import discord
import asyncio
import random
import database
from game_constants import CLASS_DETAILS, XP_PER_LEVEL_MULTIPLIER, ATTRIBUTE_MAP_EN_PT


class PVEBattle:
    def __init__(self, bot_instance, player_char, enemy_char, original_enemy_name, is_autohunt, is_elite, battle_manager):
        self.bot = bot_instance
        self.player = player_char
        self.enemy = enemy_char
        self.original_enemy_name = original_enemy_name
        self.is_autohunt = is_autohunt
        self.is_elite = is_elite

        self.battle_manager = battle_manager
        self.player_hp = player_char['hp']
        self.player_mp = player_char['mp']
        _, self.player_bonuses = database.get_equipped_items(player_char['user_id'])
        
        self.enemy_hp = enemy_char['hp']

        self.player_buffs = {}
        self.enemy_debuffs = {}
        self.enemy_status_effects = {}
        self.player_defending = False
        
        self.log = []
        self.turn = 1
        self.winner = None

    async def send_versus_embed(self, ctx):
        """Envia a ficha inicial da batalha."""
        title = "⚔️ CAÇADA AUTOMÁTICA ⚔️" if self.is_autohunt else "⚔️ BATALHA IMINENTE ⚔️"
        color = discord.Color.dark_orange() if self.is_autohunt else discord.Color.red()

        embed = discord.Embed(
            title=title,
            description=f"🌲 Você encontra um {self.enemy['name']}! Prepare-se! 🌲",
            color=color
        )
        
        player_total_attack = self.player['strength'] + self.player_bonuses['attack']
        player_total_defense = self.player['constitution'] + self.player_bonuses['defense']
        
        embed.add_field(name=f"__**{self.player['name']}**__ (Lvl {self.player['level']})", value=f"❤️ HP: {self.player_hp}\n⚔️ Atq: {player_total_attack}\n🛡️ Def: {player_total_defense}", inline=True)
        embed.add_field(name=f"__**{self.enemy['name'].replace('⭐ **ELITE** ', '')}**__ (Lvl {self.enemy['min_level']}-{self.enemy['max_level']})", value=f"❤️ HP: {self.enemy_hp}\n⚔️ Atq: {self.enemy['attack']}\n🛡️ Def: {self.enemy['defense']}", inline=True)
        
        if self.player.get('image_url'):
            embed.set_author(name=self.player['name'], icon_url=self.player['image_url'])
        if self.enemy.get('image_url'):
            embed.set_thumbnail(url=self.enemy['image_url'])
        
        await ctx.send(embed=embed)

    async def _handle_player_action(self, ctx, action):
        """Processa a ação do jogador e retorna as mensagens de log."""
        log_entries = []
        self.player_defending = False

        if action == "atacar":
            class_info = CLASS_DETAILS.get(self.player['class'])
            base_attack_stat_name = class_info.get('key_attribute', 'strength') if class_info['type'] == 'physical' else 'strength'
            
            base_attack_stat = self.player[base_attack_stat_name]
            player_total_attack = base_attack_stat + self.player_bonuses['attack']
            player_damage = max(0, round(player_total_attack * random.uniform(0.8, 1.2)) - self.enemy['defense'])
            self.enemy_hp -= player_damage
            log_entries.append(f"⚔️ Você ataca o {self.enemy['name']} e causa **{player_damage}** de dano!")

            # Lógica de Lifesteal
            lifesteal_percent = self.player_bonuses.get("special", {}).get("LIFESTEAL_PERCENT")
            if lifesteal_percent and player_damage > 0:
                life_drained = round(player_damage * (lifesteal_percent / 100))
                self.player_hp = min(self.player['max_hp'], self.player_hp + life_drained)
                log_entries.append(f"🩸 Você drena **{life_drained}** de vida do inimigo! (HP: {self.player_hp})")

        elif action == "defender":
            self.player_defending = True
            log_entries.append("🛡️ Você se prepara para o próximo ataque, aumentando sua defesa!")

        elif action == "fugir":
            flee_chance = self.player['dexterity'] / 20
            if random.random() < flee_chance:
                log_entries.append("🏃 Você conseguiu fugir da batalha!")
                self.winner = 'fled'
            else:
                log_entries.append("A tentativa de fuga falhou! Você perde seu turno.")
        
        elif action == "habilidade" or action == "skill":
            log_entries = await self._use_skill(ctx)

        elif action == "usar item":
            log_entries = await self._use_item(ctx)

        return log_entries

    async def _use_skill(self, ctx):
        """Lógica para o jogador usar uma habilidade."""
        skills = database.get_character_skills(self.player['class'], self.player['level'])
        if not skills:
            return ["Você ainda não aprendeu nenhuma habilidade! Você perde seu turno."]

        skill_list_str = "\n".join([f"`{idx+1}`: **{s['name']}** (Custo: {s['mp_cost']} MP) - {s['description']}" for idx, s in enumerate(skills)])
        await ctx.send(f"Qual habilidade você quer usar?\n{skill_list_str}\nDigite o número da habilidade ou `cancelar`.")

        try:
            skill_choice_msg = await self.bot.wait_for(
                "message",
                check=lambda m: m.author.id == self.player['user_id'] and m.channel == ctx.channel,
                timeout=30.0
            )
            if skill_choice_msg.content.lower() == 'cancelar':
                return ["Uso de habilidade cancelado. Você perde seu turno."]
            
            choice_idx = int(skill_choice_msg.content) - 1
            if not (0 <= choice_idx < len(skills)):
                return ["Escolha inválida. Você perde seu turno."]

            skill = skills[choice_idx]
            if self.player_mp < skill['mp_cost']:
                return [f"Você não tem MP suficiente para usar **{skill['name']}**! Você perde seu turno."]

            # Deduz MP e aplica o efeito
            self.player_mp -= skill['mp_cost']
            database.update_character_stats(self.player['user_id'], {'mp': self.player_mp})
            
            log_entries = [f"Você usou **{skill['name']}**!"]
            scaling_stat_value = self.player.get(skill['scaling_stat'], 0)
            total_effect_value = round(skill['base_value'] + (scaling_stat_value * skill['scaling_factor']))

            if skill['effect_type'] == 'DAMAGE':
                skill_damage = max(0, total_effect_value - self.enemy['defense'])
                self.enemy_hp -= skill_damage
                log_entries.append(f"✨ A habilidade causa **{skill_damage}** de dano ao {self.enemy['name']}!")
            
            elif skill['effect_type'] == 'DAMAGE_PIERCING':
                skill_damage = max(0, total_effect_value - (self.enemy['defense'] // 2))
                self.enemy_hp -= skill_damage
                log_entries.append(f"🎯 O ataque perfurante causa **{skill_damage}** de dano ao {self.enemy['name']}!")
            
            elif skill['effect_type'] == 'DAMAGE_AND_POISON':
                skill_damage = max(0, total_effect_value - self.enemy['defense'])
                self.enemy_hp -= skill_damage
                log_entries.append(f"✨ A habilidade causa **{skill_damage}** de dano direto...")
                self.enemy_status_effects['poison'] = {'damage': round(total_effect_value * 0.5), 'duration': skill['effect_duration']}
                log_entries.append(f"🐍 ...e envenena o {self.enemy['name']} por {skill['effect_duration']} turnos!")

            elif skill['effect_type'] == 'HEAL':
                healed_amount = min(self.player['max_hp'] - self.player_hp, total_effect_value)
                self.player_hp += healed_amount
                log_entries.append(f"💖 Você se cura em **{healed_amount}** de HP! HP atual: {self.player_hp}")

            elif skill['effect_type'] == 'BUFF_ATTACK':
                self.player_buffs['attack'] = {'value': total_effect_value, 'duration': skill['effect_duration']}
                log_entries.append(f"💪 Sua fúria aumenta seu ataque em **{total_effect_value}** por {skill['effect_duration']} turnos!")

            elif skill['effect_type'] == 'BUFF_DEFENSE':
                self.player_buffs['defense'] = {'value': total_effect_value, 'duration': skill['effect_duration']}
                log_entries.append(f"🛡️ Uma barreira mágica aumenta sua defesa em **{total_effect_value}** por {skill['effect_duration']} turnos!")

            elif skill['effect_type'] == 'DEBUFF_DEFENSE':
                self.enemy_debuffs['defense'] = {'value': total_effect_value, 'duration': skill['effect_duration']}
                log_entries.append(f"📉 A defesa do inimigo foi reduzida em **{total_effect_value}** por {skill['effect_duration']} turnos!")

            return log_entries

        except (asyncio.TimeoutError, ValueError):
            return ["Tempo esgotado ou escolha inválida. Você perde seu turno."]

    async def _use_item(self, ctx):
        """Lógica para o jogador usar um item."""
        inventory = database.get_inventory(self.player['user_id'])
        consumables = [item for item in inventory if item[5] == 'potion'] # item[5] é item_type

        if not consumables:
            return ["Você não tem itens consumíveis para usar! Você perde seu turno."]

        item_list_str = "\n".join([f"`{idx+1}`: {item[3]} (x{item[2]})" for idx, item in enumerate(consumables)])
        await ctx.send(f"Qual item você quer usar?\n{item_list_str}\nDigite o número do item ou `cancelar`.")
        
        try:
            item_choice_msg = await self.bot.wait_for(
                "message",
                check=lambda m: m.author.id == self.player['user_id'] and m.channel == ctx.channel,
                timeout=30.0
            )
            if item_choice_msg.content.lower() == 'cancelar':
                return ["Uso de item cancelado. Você perde seu turno."]
            
            choice_idx = int(item_choice_msg.content) - 1
            if not (0 <= choice_idx < len(consumables)):
                return ["Escolha inválida. Você perde seu turno."]

            item_to_use = consumables[choice_idx]
            inv_id, item_id, _, name, _, _, effect_type, effect_value, _, _ = item_to_use

            if effect_type == 'HEAL_HP':
                healed_amount = min(self.player['max_hp'] - self.player_hp, effect_value)
                self.player_hp += healed_amount
                database.remove_item_from_inventory(self.player['user_id'], item_id, 1)
                return [f"Você usou **{name}** e recuperou **{healed_amount}** de HP! HP atual: {self.player_hp}"]
            elif effect_type == 'HEAL_MP':
                healed_amount = min(self.player['max_mp'] - self.player_mp, effect_value)
                self.player_mp += healed_amount
                database.remove_item_from_inventory(self.player['user_id'], item_id, 1)
                return [f"Você usou **{name}** e recuperou **{healed_amount}** de MP! MP atual: {self.player_mp}"]
            else:
                return [f"O item **{name}** não pode ser usado em batalha. Você perde seu turno."]

        except (asyncio.TimeoutError, ValueError):
            return ["Tempo esgotado ou escolha inválida. Você perde seu turno."]

    def _process_enemy_turn(self):
        """Processa o turno do inimigo e retorna as mensagens de log."""
        log_entries = []
        
        # Processar buffs/debuffs
        defense_buff = self.player_buffs.get('defense', {}).get('value', 0)
        player_total_defense = self.player_bonuses['defense'] + (self.player['dexterity'] // 4) + defense_buff
        if self.player_defending:
            player_total_defense += self.player['dexterity'] // 2

        enemy_damage = max(0, round(self.enemy['attack'] * random.uniform(0.8, 1.2)) - player_total_defense)
        self.player_hp -= enemy_damage
        log_entries.append(f"💥 O {self.enemy['name']} ataca e causa **{enemy_damage}** de dano em você!")

        return log_entries

    def _process_status_effects(self):
        """Processa efeitos de status no início do turno (ex: veneno no inimigo)."""
        log_entries = []
        if 'poison' in self.enemy_status_effects:
            poison = self.enemy_status_effects['poison']
            poison_damage = poison['damage']
            self.enemy_hp -= poison_damage
            poison['duration'] -= 1
            log_entries.append(f"🤢 O {self.enemy['name']} sofre **{poison_damage}** de dano de veneno. (Duração: {poison['duration']} turnos)")
            if poison['duration'] <= 0:
                del self.enemy_status_effects['poison']
                log_entries.append(f"O veneno no {self.enemy['name']} se dissipou.")
        return log_entries

    def _tick_down_effects(self):
        """Reduz a duração de buffs e debuffs no final do turno."""
        for effect_dict in [self.player_buffs, self.enemy_debuffs]:
            for key in list(effect_dict.keys()):
                effect_dict[key]['duration'] -= 1
                if effect_dict[key]['duration'] <= 0:
                    del effect_dict[key]

    async def run_autohunt_loop(self, ctx):
        """Executa o loop de batalha automático."""
        battle_log = []

        while self.player_hp > 0 and self.enemy_hp > 0:
            # Turno do Jogador
            player_logs = await self._handle_player_action(ctx, "atacar")
            battle_log.extend([f"Turno {self.turn}: {log}" for log in player_logs])
            
            if self.enemy_hp <= 0: break

            # Turno do Inimigo
            enemy_logs = self._process_enemy_turn()
            battle_log.extend([f"Turno {self.turn}: {log}" for log in enemy_logs])

            self.turn += 1

        log_message = "\n".join(battle_log)
        embed = discord.Embed(title=f"Resumo da Batalha: {self.player['name']} vs {self.enemy['name']}", description=log_message, color=discord.Color.orange())
        await ctx.send(embed=embed)

        self.winner = 'player' if self.player_hp > 0 else 'enemy'
        await self._end_battle(ctx)

    async def run_manual_loop(self, ctx):
        """Executa o loop de batalha manual, aguardando input do jogador."""
        while self.winner is None:
            # Processar efeitos de status no inimigo (ex: veneno)
            status_logs = self._process_status_effects()
            if status_logs:
                await ctx.send("\n".join(status_logs))
            if self.enemy_hp <= 0:
                self.winner = 'player'
                break

            embed = discord.Embed(title=f"Seu Turno! (Turno {self.turn})", description="Escolha sua ação: `atacar`, `defender`, `habilidade`, `usar item`, `fugir`", color=discord.Color.green())
            embed.add_field(name=f"{self.player['name']} HP", value=f"{self.player_hp}/{self.player['max_hp']}", inline=True)
            embed.add_field(name=f"{self.player['name']} MP", value=f"{self.player_mp}/{self.player['max_mp']}", inline=True)
            embed.add_field(name=f"{self.enemy['name']} HP", value=f"{self.enemy_hp}/{self.enemy['hp']}", inline=True)
            await ctx.send(embed=embed)

            try:
                action_msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == self.player['user_id'] and m.channel == ctx.channel and m.content.lower() in ["atacar", "defender", "habilidade", "skill", "usar item", "fugir"],
                    timeout=60.0
                )
                action = action_msg.content.lower()
            except asyncio.TimeoutError:
                await ctx.send("Você demorou demais para agir! O inimigo ataca!")
                action = "passar"

            if action != "passar":
                player_logs = await self._handle_player_action(ctx, action)
                if player_logs: await ctx.send("\n".join(player_logs))

            if self.winner is not None: break # Se o jogador fugiu
            if self.enemy_hp <= 0:
                self.winner = 'player'
                break

            # Turno do Inimigo
            await asyncio.sleep(1)
            enemy_logs = self._process_enemy_turn()
            if enemy_logs: await ctx.send("\n".join(enemy_logs))

            if self.player_hp <= 0:
                self.winner = 'enemy'
                break
            
            # Reduz a duração dos efeitos
            self._tick_down_effects()
            self.turn += 1

        await self._end_battle(ctx)

    async def _end_battle(self, ctx):
        """Finaliza a batalha, calcula recompensas e limpa o estado."""
        user_id = self.player['user_id']

        if self.winner == 'fled':
            await ctx.send("Batalha encerrada.")
        elif self.winner == 'enemy':
            await ctx.send(f"☠️ Você foi derrotado pelo {self.enemy['name']}... Sua jornada termina aqui (por enquanto).")
            database.update_character_stats(user_id, {"hp": 1})
        elif self.winner == 'player':
            result_embed = discord.Embed(title="🏆 **VITÓRIA!** 🏆", description=f"Você derrotou o {self.enemy['name']}!", color=discord.Color.green())

            # Ganho de XP e Moedas
            new_experience = self.player['experience'] + self.enemy['xp_reward']
            new_gold = self.player['gold'] + self.enemy['gold_reward']
            xp_to_next_level = self.player['level'] * XP_PER_LEVEL_MULTIPLIER
            
            result_embed.add_field(name="Recompensas", value=f"**{self.enemy['xp_reward']}** de XP\n**{self.enemy['gold_reward']}** de Ouro", inline=False)

            updates = {"experience": new_experience, "hp": self.player_hp, "mp": self.player_mp, "gold": new_gold}

            # Lógica de Level Up
            if new_experience >= xp_to_next_level:
                updates['level'] = self.player['level'] + 1
                updates['experience'] = new_experience - xp_to_next_level
                
                await ctx.send(f"🎉 **LEVEL UP!** Você alcançou o nível **{updates['level']}**! 🎉")

                # A cada 5 níveis, o jogador distribui 4 pontos
                if updates['level'] % 5 == 0 and not self.is_autohunt:
                    points_to_distribute = 4
                    await ctx.send(f"Você tem **{points_to_distribute}** pontos para distribuir entre seus atributos: `força`, `constituição`, `destreza`, `inteligência`, `sabedoria`, `carisma`.")
                    
                    for i in range(points_to_distribute):
                        await ctx.send(f"Ponto {i+1}/{points_to_distribute}: Qual atributo você quer aumentar?")
                        try:
                            attr_choice_msg = await self.bot.wait_for(
                                "message",
                                check=lambda m: m.author.id == user_id and m.channel == ctx.channel and m.content.lower() in ATTRIBUTE_MAP_EN_PT.values(),
                                timeout=60.0
                            )
                            attr_to_increase = attr_choice_msg.content.lower()
                            
                            current_value = updates.get(attr_to_increase, self.player[attr_to_increase])
                            updates[attr_to_increase] = current_value + 1
                            await ctx.send(f"Seu atributo **{attr_to_increase.capitalize()}** aumentou para **{updates[attr_to_increase]}**!")

                        except asyncio.TimeoutError:
                            await ctx.send("Tempo esgotado. O ponto de atributo foi perdido.")
                elif updates['level'] % 5 == 0 and self.is_autohunt:
                     result_embed.add_field(name="Level Up!", value="Você ganhou pontos de atributo para distribuir! Use o comando `!hunt` manual para subir de nível e distribuí-los.", inline=False)

                # Aumenta HP/MP máximo no level up
                new_constitution = updates.get('constitution', self.player['constitution'])
                new_intelligence = updates.get('intelligence', self.player['intelligence'])
                updates['max_hp'] = self.player['max_hp'] + 10 + (new_constitution // 4)
                updates['max_mp'] = self.player['max_mp'] + 5 + (new_intelligence // 4)
                updates['hp'] = updates['max_hp'] # Restaura HP e MP no level up
                updates['mp'] = updates['max_mp']

            database.update_character_stats(user_id, updates)

            # Lógica de Loot
            loot_rolls = 2 if self.is_elite else 1
            loot_chance = 0.3
            loot_found = []
            
            for _ in range(loot_rolls):
                if random.random() <= loot_chance:
                    loot_item = database.get_random_loot(self.player['level'])
                    if loot_item:
                        database.add_item_to_inventory(user_id, loot_item['id'])
                        loot_found.append(f"🎁 **{loot_item['name']}**")

            loot_message = "\n".join(loot_found) if loot_found else "Nenhum item encontrado."
            result_embed.add_field(name="Loot", value=loot_message, inline=False)
            
            updated_player = database.get_character(user_id)
            result_embed.set_footer(text=f"HP Final: {self.player_hp}/{updated_player['max_hp']} | XP: {updated_player['experience']}/{updated_player['level'] * XP_PER_LEVEL_MULTIPLIER}")

            await ctx.send(embed=result_embed)

            # Atualiza o progresso da missão
            database.update_quest_progress(user_id, 'kill', self.original_enemy_name)

        # Limpa a batalha ativa
        if self.battle_manager and user_id in self.battle_manager:
            del self.battle_manager[user_id]


class PVPBattle:
    def __init__(self, p1_char, p2_char, ranked=False):
        self.p1 = p1_char
        self.p2 = p2_char
        self.p1_hp = p1_char['max_hp']
        self.p2_hp = p2_char['max_hp']
        self.p1_mp = p1_char['max_mp']
        self.p2_mp = p2_char['max_mp']
        self.ranked = ranked
        _, self.p1_bonuses = database.get_equipped_items(p1_char['user_id'])
        _, self.p2_bonuses = database.get_equipped_items(p2_char['user_id'])
        self.turn = p1_char['user_id'] # p1 começa
        self.log = []
        self.turn_count = 1
        self.p1_effects = {} # Armazena buffs, debuffs e status
        self.p2_effects = {}

    def get_opponent_id(self, player_id):
        return self.p2['user_id'] if player_id == self.p1['user_id'] else self.p1['user_id']

    def switch_turn(self):
        self.turn = self.get_opponent_id(self.turn)
        if self.turn == self.p1['user_id']:
            self.turn_count += 1