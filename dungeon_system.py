import discord
import asyncio
import random
import database

class DungeonRun:
    def __init__(self, bot_instance, party_members_chars, dungeon_info, mode='solo'):
        self.bot = bot_instance
        self.party_members = party_members_chars
        self.dungeon = dungeon_info
        self.mode = mode
        self.leader_id = self.party_members[0]['user_id'] # O primeiro da lista é o líder

        # Dicionário para armazenar o estado volátil de cada jogador
        self.players_state = {}
        for player in self.party_members:
            user_id = player['user_id']
            _, bonuses = database.get_equipped_items(user_id)
            self.players_state[user_id] = {
                'original': player,
                'hp': player['max_hp'],
                'mp': player['max_mp'],
                'bonuses': bonuses,
                'is_alive': True
            }
        
        self.current_stage = 1
        self.total_stages = 4
        self.is_complete = False
        self.log = [f"O grupo adentra **{dungeon_info['name']}**..."]
        self.total_xp_reward = 0
        self.total_gold_reward = 0

    def get_stage_description(self):
        """Retorna a descrição do estágio atual."""
        descriptions = {
            1: "Primeira Horda de Inimigos",
            2: "Área de Descanso",
            3: "Segunda Horda de Inimigos",
            4: "O Chefe da Masmorra"
        }
        return descriptions.get(self.current_stage, "Estágio Desconhecido")

    def generate_enemies_for_stage(self):
        """Gera inimigos para um estágio de combate."""
        if self.mode == 'solo':
            num_enemies = random.randint(2, 3)
        else:
            # Escala com o tamanho do grupo
            num_enemies = random.randint(len(self.party_members), len(self.party_members) + 2)
        enemy_list = []
        
        # Define os inimigos com base no tema da masmorra
        themes = {
            'Caverna dos Goblins': ['Goblin', 'Hobgoblin'],
            'Cripta Assombrada': ['Esqueleto', 'Guerreiro Morto-Vivo']
        }
        possible_enemies = themes.get(self.dungeon['name'], ['Goblin'])

        for i in range(num_enemies):
            enemy_name = random.choice(possible_enemies)
            enemy_data = database.get_enemy_by_name(enemy_name)
            if enemy_data:
                # Cria uma cópia para não modificar o original
                instance = dict(enemy_data)
                instance['current_hp'] = instance['hp']
                instance['id_in_battle'] = i + 1
                enemy_list.append(instance)
        return enemy_list

    async def run(self, ctx):
        """Loop principal para a masmorra."""
        channel = ctx.channel

        while self.current_stage <= self.total_stages and any(p['is_alive'] for p in self.players_state.values()):
            stage_embed = discord.Embed(
                title=f"Masmorra: {self.dungeon['name']}",
                description=f"**Estágio {self.current_stage}/{self.total_stages}: {self.get_stage_description()}**",
                color=discord.Color.dark_magenta()
            )
            await channel.send(embed=stage_embed)
            await asyncio.sleep(2)

            # Lógica de cada estágio
            if self.current_stage in [1, 3]: # Estágios de combate
                enemies = self.generate_enemies_for_stage()
                combat_won = await self.run_combat_stage(channel, enemies)
                if not combat_won:
                    self.log.append("O grupo foi derrotado e a jornada termina.")
                    await channel.send("Seu grupo foi derrotado... A masmorra consumiu vocês.")
                    break
            
            elif self.current_stage == 2: # Estágio de descanso
                await self.run_rest_stage(channel)

            elif self.current_stage == 4: # Estágio do Chefe
                boss_data = database.get_boss_by_id(self.dungeon['boss_id'])
                boss_data['current_hp'] = boss_data['hp']
                boss_data['id_in_battle'] = 'Chefe'
                combat_won = await self.run_combat_stage(channel, [boss_data])
                if combat_won:
                    self.is_complete = True
                else:
                    self.log.append("O grupo foi derrotado pelo chefe.")
                    await channel.send("Vocês foram derrotados pelo guardião final...")
                    break

            self.current_stage += 1
            if self.current_stage <= self.total_stages:
                await channel.send("Você avança para a próxima área...")
                await asyncio.sleep(3)

        # Final da masmorra
        await self.end_dungeon(channel)

    async def run_combat_stage(self, channel, enemies):
        """Executa um estágio de combate contra um grupo de inimigos."""
        self.log.append(f"Encontrou {len(enemies)} inimigos: {', '.join([e['name'] for e in enemies])}")
        
        # Ordem de turno: todos os jogadores, depois todos os inimigos
        turn_order = [p for p in self.party_members if self.players_state[p['user_id']]['is_alive']]
        turn = 1

        while any(p['is_alive'] for p in self.players_state.values()) and any(e['current_hp'] > 0 for e in enemies):
            # --- Turno dos Jogadores ---
            for player_char in turn_order:
                player_id = player_char['user_id']
                player_state = self.players_state[player_id]
                if not player_state['is_alive']: continue

                enemies_alive = [e for e in enemies if e['current_hp'] > 0]
                if not enemies_alive: break

                embed = discord.Embed(title=f"Combate - Turno {turn}", description=f"É a vez de **{player_char['name']}**!", color=discord.Color.blue())
                
                party_status_str = ""
                for p_id, p_state in self.players_state.items():
                    status_icon = "❤️" if p_state['is_alive'] else "☠️"
                    party_status_str += f"{status_icon} **{p_state['original']['name']}**: {p_state['hp']}/{p_state['original']['max_hp']} HP\n"
                embed.add_field(name="Status do Grupo", value=party_status_str, inline=False)
                
                enemy_status_str = ""
                for e in enemies_alive:
                    enemy_status_str += f"`{e['id_in_battle']}`: **{e['name']}** - ❤️ HP: {e['current_hp']}\n"
                embed.add_field(name="Inimigos", value=enemy_status_str, inline=False)
                embed.set_footer(text=f"Ação de {player_char['name']}? `atacar <ID>`, `habilidade`, `item`")
                await channel.send(embed=embed)

                try:
                    action_msg = await self.bot.wait_for("message", check=lambda m: m.author.id == player_id and m.channel == channel, timeout=60.0)
                    action_parts = action_msg.content.lower().split()
                    action = action_parts[0]

                    if action == "atacar" and len(action_parts) > 1:
                        target_id_str = action_parts[1]
                        target_id = int(target_id_str) if target_id_str != 'chefe' else 'Chefe'
                        target_enemy = next((e for e in enemies_alive if e['id_in_battle'] == target_id), None)
                        if not target_enemy:
                            await channel.send("Alvo inválido.")
                            continue

                        player_attack = player_state['original']['strength'] + player_state['bonuses']['attack']
                        damage = max(0, round(player_attack * random.uniform(0.8, 1.2)) - target_enemy['defense'])
                        target_enemy['current_hp'] -= damage
                        self.log.append(f"{player_char['name']} ataca {target_enemy['name']} e causa {damage} de dano.")
                        await channel.send(f"⚔️ **{player_char['name']}** ataca **{target_enemy['name']}** e causa **{damage}** de dano!")
                        if target_enemy['current_hp'] <= 0:
                            await channel.send(f"☠️ **{target_enemy['name']}** foi derrotado!")
                            self.total_xp_reward += target_enemy['xp_reward']
                            self.total_gold_reward += target_enemy['gold_reward']
                    else:
                        await channel.send(f"Ação inválida para **{player_char['name']}**. Turno perdido. (Ações: `atacar <ID>`)")

                except (asyncio.TimeoutError, ValueError):
                    await channel.send(f"**{player_char['name']}** demorou para agir e perdeu o turno.")

            # --- Turno dos Inimigos ---
            enemies_alive = [e for e in enemies if e['current_hp'] > 0]
            if not enemies_alive: break

            await asyncio.sleep(1)
            players_alive = [p_id for p_id, p_state in self.players_state.items() if p_state['is_alive']]
            if not players_alive: break

            for enemy in enemies_alive:
                target_player_id = random.choice(players_alive)
                target_state = self.players_state[target_player_id]
                
                player_defense = target_state['original']['constitution'] + target_state['bonuses']['defense']
                damage = max(0, round(enemy['attack'] * random.uniform(0.8, 1.2)) - player_defense)
                target_state['hp'] -= damage
                self.log.append(f"{enemy['name']} ataca {target_state['original']['name']} e causa {damage} de dano.")
                await channel.send(f"💥 **{enemy['name']}** ataca **{target_state['original']['name']}** e causa **{damage}** de dano!")

                if target_state['hp'] <= 0:
                    target_state['is_alive'] = False
                    players_alive.remove(target_player_id)
                    await channel.send(f"☠️ **{target_state['original']['name']}** foi derrotado!")
                    if not players_alive: break
            
            turn += 1

        return any(p['is_alive'] for p in self.players_state.values())

    async def run_rest_stage(self, channel):
        """Executa um estágio de descanso, permitindo o uso de itens."""
        self.log.append("O grupo encontra uma área segura para descansar.")
        
        embed = discord.Embed(title="Área de Descanso", description="Você encontrou um local seguro. É uma boa hora para usar poções e se preparar para o que vem a seguir.", color=discord.Color.green())
        
        party_status_str = ""
        for p_id, p_state in self.players_state.items():
            status_icon = "❤️" if p_state['is_alive'] else "☠️"
            party_status_str += f"{status_icon} **{p_state['original']['name']}**: {p_state['hp']}/{p_state['original']['max_hp']} HP | {p_state['mp']}/{p_state['original']['max_mp']} MP\n"
        embed.add_field(name="Status do Grupo", value=party_status_str, inline=False)
        embed.set_footer(text="Qualquer um pode usar `!use <item>`. Apenas o líder pode digitar `continuar`.")
        
        msg = await channel.send(embed=embed)

        def check(m):
            is_member = m.author.id in self.players_state
            is_leader_action = m.author.id == self.leader_id and m.content.lower() == 'continuar'
            is_member_action = m.content.lower().startswith('!use')
            return m.channel == channel and is_member and (is_leader_action or is_member_action)

        while True:
            try:
                action_msg = await self.bot.wait_for("message", check=check, timeout=120.0)
                
                if action_msg.content.lower() == 'continuar':
                    self.log.append("Após um breve descanso, o grupo segue em frente.")
                    break
                
                # Simula o comando !use, mas aplicando ao estado da masmorra
                if action_msg.content.lower().startswith('!use'):
                    user_id = action_msg.author.id
                    player_state = self.players_state[user_id]
                    if not player_state['is_alive']:
                        await channel.send("Jogadores derrotados não podem usar itens.")
                        continue

                    parts = action_msg.content.split()
                    item_name = " ".join(parts[1:])
                    
                    # Busca o item no inventário real do jogador
                    inventory = database.get_inventory(user_id)
                    item_to_use_data = next((item for item in inventory if item_name.lower() in item[3].lower()), None)

                    if not item_to_use_data or item_to_use_data[5] != 'potion':
                        await channel.send("Item não encontrado ou não é uma poção.")
                        continue

                    item_id, _, _, name, _, _, effect_type, effect_value, _, _ = item_to_use_data

                    # Remove o item do inventário real
                    if not database.remove_item_from_inventory(user_id, item_id, 1):
                        await channel.send("Falha ao usar o item.")
                        continue

                    # Aplica o efeito no estado da masmorra
                    if effect_type == 'HEAL_HP':
                        healed = min(player_state['original']['max_hp'] - player_state['hp'], effect_value)
                        player_state['hp'] += healed
                        await channel.send(f"**{player_state['original']['name']}** usou **{name}** e recuperou **{healed}** de HP. HP atual: {player_state['hp']}")
                    elif effect_type == 'HEAL_MP':
                        healed = min(player_state['original']['max_mp'] - player_state['mp'], effect_value)
                        player_state['mp'] += healed
                        await channel.send(f"**{player_state['original']['name']}** usou **{name}** e recuperou **{healed}** de MP. MP atual: {player_state['mp']}")
                    else:
                        await channel.send(f"**{name}** não tem efeito em um descanso.")
                        # Devolve o item, pois não teve efeito útil
                        database.add_item_to_inventory(user_id, item_id, 1)

            except asyncio.TimeoutError:
                await channel.send("O líder demorou para agir e o grupo continuou automaticamente.")
                break

    async def end_dungeon(self, channel):
        if self.is_complete:
            boss = database.get_boss_by_id(self.dungeon['boss_id'])
            self.total_xp_reward += boss['xp_reward']
            self.total_gold_reward += boss['gold_reward']

            # Aplica bônus de modo solo
            if self.mode == 'solo':
                xp_reward_final = self.total_xp_reward * 4
                gold_reward_final = self.total_gold_reward * 4
            else:
                xp_reward_final = self.total_xp_reward
                gold_reward_final = self.total_gold_reward

            final_embed = discord.Embed(title=f"🎉 Masmorra Concluída: {self.dungeon['name']} 🎉", color=discord.Color.gold())
            final_embed.description = f"O grupo superou todos os desafios e derrotou o chefe final!"
            final_embed.add_field(name="Recompensa por Sobrevivente", value=f"✨ **{xp_reward_final}** XP\n💰 **{gold_reward_final}** Ouro")
            
            # Lógica de Loot do Chefe
            boss_loot_pool = database.get_boss_loot(self.dungeon['boss_id'])
            if boss_loot_pool:
                dropped_item = random.choice(boss_loot_pool)
                surviving_players = [p_state for p_state in self.players_state.values() if p_state['is_alive']]
                
                if surviving_players:
                    # Sorteia um jogador para receber o item
                    lucky_player_state = random.choice(surviving_players)
                    lucky_player_id = lucky_player_state['original']['user_id']
                    lucky_player_name = lucky_player_state['original']['name']

                    database.add_item_to_inventory(lucky_player_id, dropped_item['id'], 1)
                    
                    loot_message = f"🎁 O chefe dropou **{dropped_item['name']}**!\nO item foi para **{lucky_player_name}**."
                    final_embed.add_field(name="Loot do Chefe", value=loot_message, inline=False)
            else:
                final_embed.add_field(name="Loot do Chefe", value="Nenhum loot especial encontrado.", inline=False)

            await channel.send(embed=final_embed)

            # Atualiza cada personagem sobrevivente no banco de dados
            for user_id, p_state in self.players_state.items():
                if p_state['is_alive']:
                    current_char = p_state['original']
                    updates = {
                        'experience': current_char['experience'] + xp_reward_final,
                        'gold': current_char['gold'] + gold_reward_final,
                        'hp': p_state['hp'], # Salva o HP restante
                        'mp': p_state['mp'], # Salva o MP restante
                    }
                    database.update_character_stats(user_id, updates)

        else:
            # O jogador perdeu
            final_embed = discord.Embed(title="☠️ Fim da Linha ☠️", description="A masmorra provou ser demais para o grupo. Vocês desmaiam e acordam na entrada, com suas forças parcialmente recuperadas.", color=discord.Color.dark_gray())
            await channel.send(embed=final_embed)
            
            # Penalidade para todos os membros: recupera apenas metade da vida
            for user_id, p_state in self.players_state.items():
                database.update_character_stats(user_id, {'hp': p_state['original']['max_hp'] // 2})

        # Limpa a instância da masmorra ativa
        for user_id in self.players_state.keys():
            if user_id in self.bot.active_dungeons:
                del self.bot.active_dungeons[user_id]