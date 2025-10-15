import discord
from discord.ext import commands
import asyncio
import random
import database
from battle_system import PVPBattle

class PVP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _process_effects(self, battle, player_id):
        """Processa efeitos de status (como veneno) no início do turno do jogador."""
        log_entries = []
        effects = battle.p1_effects if player_id == battle.p1['user_id'] else battle.p2_effects
        
        if 'poison' in effects:
            poison = effects['poison']
            poison_damage = poison['damage']
            if player_id == battle.p1['user_id']: battle.p1_hp -= poison_damage
            else: battle.p2_hp -= poison_damage
            
            log_entries.append(f"🤢 **{battle.p1['name'] if player_id == battle.p1['user_id'] else battle.p2['name']}** sofre **{poison_damage}** de dano de veneno.")
            poison['duration'] -= 1
            if poison['duration'] <= 0:
                del effects['poison']
                log_entries.append(f"O veneno se dissipou.")
        return log_entries

    async def run_pvp_battle(self, battle):
        p1_channel = self.bot.get_channel(battle.p1['channel_id'])
        p2_channel = self.bot.get_channel(battle.p2['channel_id'])

        while battle.p1_hp > 0 and battle.p2_hp > 0:
            current_player_id = battle.turn
            current_player_char = battle.p1 if current_player_id == battle.p1['user_id'] else battle.p2
            current_player_channel = p1_channel if current_player_id == battle.p1['user_id'] else p2_channel
            
            opponent_char = battle.p2 if current_player_id == battle.p1['user_id'] else battle.p1
            opponent_channel = p2_channel if current_player_id == battle.p1['user_id'] else p1_channel

            effect_logs = self._process_effects(battle, current_player_id)
            if effect_logs:
                battle.log.extend(effect_logs)
                log_embed = discord.Embed(title="Efeitos de Turno", description="\n".join(effect_logs), color=discord.Color.purple())
                await p1_channel.send(embed=log_embed)
                await p2_channel.send(embed=log_embed)
                if battle.p1_hp <= 0 or battle.p2_hp <= 0: break

            await opponent_channel.send(f"Aguardando a ação de **{current_player_char['name']}**...")

            embed = discord.Embed(title=f"Turno {battle.turn_count} - É a sua vez!", description="Escolha sua ação: `atacar`, `habilidade`, `fugir`", color=discord.Color.green())
            embed.add_field(name=f"Seu HP", value=f"{battle.p1_hp if current_player_id == battle.p1['user_id'] else battle.p2_hp}", inline=True)
            embed.add_field(name=f"HP de {opponent_char['name']}", value=f"{battle.p2_hp if current_player_id == battle.p1['user_id'] else battle.p1_hp}", inline=True)
            await current_player_channel.send(embed=embed)

            try:
                action_msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == current_player_id and m.channel == current_player_channel and m.content.lower() in ["atacar", "habilidade", "skill", "fugir"],
                    timeout=60.0
                )
                action = action_msg.content.lower()

                if action == "atacar":
                    attacker_bonuses = battle.p1_bonuses if current_player_id == battle.p1['user_id'] else battle.p2_bonuses
                    defender_bonuses = battle.p2_bonuses if current_player_id == battle.p1['user_id'] else battle.p1_bonuses
                    
                    attacker_effects = battle.p1_effects if current_player_id == battle.p1['user_id'] else battle.p2_effects
                    defender_effects = battle.p2_effects if current_player_id == battle.p1['user_id'] else battle.p1_effects

                    attack_buff = attacker_effects.get('buff_attack', {}).get('value', 0)
                    defense_debuff = defender_effects.get('debuff_defense', {}).get('value', 0)
                    defense_buff = defender_effects.get('buff_defense', {}).get('value', 0)

                    attack_stat = current_player_char['strength'] + attacker_bonuses['attack'] + attack_buff
                    defense_stat = opponent_char['constitution'] + defender_bonuses['defense'] + defense_buff - defense_debuff

                    damage = max(0, round(attack_stat * random.uniform(0.9, 1.1)) - defense_stat)
                    
                    if current_player_id == battle.p1['user_id']: battle.p2_hp -= damage
                    else: battle.p1_hp -= damage
                    
                    log_entry = f"**Turno {battle.turn_count}**: ⚔️ **{current_player_char['name']}** ataca **{opponent_char['name']}** e causa **{damage}** de dano!"
                    battle.log.append(log_entry)

                elif action in ["habilidade", "skill"]:
                    skills = database.get_character_skills(current_player_char['class'], current_player_char['level'])
                    if not skills:
                        battle.log.append(f"**Turno {battle.turn_count}**: ❓ **{current_player_char['name']}** tentou usar uma habilidade, mas não conhece nenhuma e perdeu o turno.")
                    else:
                        skill_list_str = "\n".join([f"`{idx+1}`: **{s['name']}** (Custo: {s['mp_cost']} MP)" for idx, s in enumerate(skills)])
                        await current_player_channel.send(f"Qual habilidade você quer usar?\n{skill_list_str}\nDigite o número ou `cancelar`.")
                        
                        try:
                            skill_choice_msg = await self.bot.wait_for("message", check=lambda m: m.author.id == current_player_id and m.channel == current_player_channel, timeout=30.0)
                            if skill_choice_msg.content.lower() == 'cancelar':
                                battle.log.append(f"**Turno {battle.turn_count}**: ❌ **{current_player_char['name']}** decidiu não usar uma habilidade e perdeu o turno.")
                            else:
                                choice_idx = int(skill_choice_msg.content) - 1
                                if 0 <= choice_idx < len(skills):
                                    skill = skills[choice_idx]
                                    current_mp = battle.p1_mp if current_player_id == battle.p1['user_id'] else battle.p2_mp
                                    
                                    if current_mp < skill['mp_cost']:
                                        battle.log.append(f"**Turno {battle.turn_count}**: 💧 **{current_player_char['name']}** tentou usar **{skill['name']}**, mas não tinha MP suficiente.")
                                    else:
                                        if current_player_id == battle.p1['user_id']: battle.p1_mp -= skill['mp_cost']
                                        else: battle.p2_mp -= skill['mp_cost']

                                        scaling_stat_value = current_player_char.get(skill['scaling_stat'], 0)
                                        total_effect_value = round(skill['base_value'] + (scaling_stat_value * skill['scaling_factor']))

                                        if skill['effect_type'] == 'DAMAGE':
                                            defender_bonuses = battle.p2_bonuses if current_player_id == battle.p1['user_id'] else battle.p1_bonuses
                                            defense_stat = opponent_char['constitution'] + defender_bonuses['defense']
                                            skill_damage = max(0, total_effect_value - defense_stat)
                                            
                                            if current_player_id == battle.p1['user_id']: battle.p2_hp -= skill_damage
                                            else: battle.p1_hp -= skill_damage
                                            battle.log.append(f"**Turno {battle.turn_count}**: ✨ **{current_player_char['name']}** usa **{skill['name']}** e causa **{skill_damage}** de dano em **{opponent_char['name']}**!")
                                        # Add other skill effects here...
                                        else:
                                            battle.log.append(f"**Turno {battle.turn_count}**: 🌀 **{current_player_char['name']}** usa **{skill['name']}**, mas o efeito ainda não foi implementado em PvP.")
                                else:
                                    battle.log.append(f"**Turno {battle.turn_count}**: ❓ **{current_player_char['name']}** fez uma escolha inválida e perdeu o turno.")
                        except (asyncio.TimeoutError, ValueError):
                            battle.log.append(f"**Turno {battle.turn_count}**: ⏳ **{current_player_char['name']}** demorou para escolher e perdeu o turno.")

                elif action == "fugir":
                    log_entry = f"**Turno {battle.turn_count}**: 🏳️ **{current_player_char['name']}** fugiu do duelo!"
                    battle.log.append(log_entry)
                    if current_player_id == battle.p1['user_id']: battle.p1_hp = 0
                    else: battle.p2_hp = 0

                log_embed = discord.Embed(title="Histórico da Batalha", description="\n".join(battle.log), color=discord.Color.light_grey())
                await p1_channel.send(embed=log_embed)
                await p2_channel.send(embed=log_embed)

            except asyncio.TimeoutError:
                log_entry = f"**Turno {battle.turn_count}**: ⏳ **{current_player_char['name']}** demorou demais para agir e perdeu o turno."
                battle.log.append(log_entry)
                log_embed = discord.Embed(title="Histórico da Batalha", description="\n".join(battle.log), color=discord.Color.light_grey())
                await p1_channel.send(embed=log_embed)
                await p2_channel.send(embed=log_embed)

            battle.switch_turn()

        # Fim da batalha
        winner = battle.p1 if battle.p2_hp <= 0 else battle.p2
        loser = battle.p2 if battle.p2_hp <= 0 else battle.p1
        
        final_message = f"🏆 **FIM DO DUELO {'RANQUEADO' if battle.ranked else ''}!** 🏆\nO vencedor é **{winner['name']}**!"
        await p1_channel.send(final_message)
        await p2_channel.send(final_message)

        if battle.ranked:
            winner_stats = database.get_character(winner['user_id'])
            loser_stats = database.get_character(loser['user_id'])
            database.update_character_stats(winner['user_id'], {'pvp_wins': winner_stats['pvp_wins'] + 1})
            database.update_character_stats(loser['user_id'], {'pvp_losses': loser_stats['pvp_losses'] + 1})
            await p1_channel.send("As estatísticas ranqueadas foram atualizadas.")
            await p2_channel.send("As estatísticas ranqueadas foram atualizadas.")

        database.update_character_stats(battle.p1['user_id'], {'hp': battle.p1['max_hp'], 'mp': battle.p1['max_mp']})
        database.update_character_stats(battle.p2['user_id'], {'hp': battle.p2['max_hp'], 'mp': battle.p2['max_mp']})

        del self.bot.active_pvp_battles[battle.p1['user_id']]
        del self.bot.active_pvp_battles[battle.p2['user_id']]

    @commands.group(name="pvp", help="Inicia ou gerencia um duelo PvP.", invoke_without_command=True)
    async def pvp(self, ctx):
        await self.bot.get_command('help').callback(ctx, command_name="pvp")

    @pvp.command(name="challenge", help="Desafia outro jogador. Uso: !pvp challenge [ranked] <nome>")
    async def pvp_challenge(self, ctx, *args):
        if not args:
            await ctx.send("Uso: `!pvp challenge [ranked] <nome do personagem>`")
            return

        is_ranked = args[0].lower() == 'ranked'
        target_name = " ".join(args[1:]) if is_ranked else " ".join(args)

        challenger_id = ctx.author.id
        challenger_char = database.get_character(challenger_id)
        if not challenger_char:
            await ctx.send("Você precisa de um personagem para desafiar alguém.")
            return

        target_char = database.get_character_by_name(target_name)
        if not target_char:
            await ctx.send(f"Personagem '{target_name}' não encontrado.")
            return

        target_id = target_char['user_id']
        if target_id == challenger_id:
            await ctx.send("Você não pode desafiar a si mesmo.")
            return

        if target_id in self.bot.pvp_invitations.values() or challenger_id in self.bot.pvp_invitations:
            await ctx.send("Um de vocês já tem um desafio pendente.")
            return

        if target_id in self.bot.active_pvp_battles or challenger_id in self.bot.active_pvp_battles:
            await ctx.send("Um de vocês já está em uma batalha.")
            return

        self.bot.pvp_invitations[target_id] = challenger_id
        self.bot.pvp_invitations[f"{target_id}_ranked"] = is_ranked
        
        await ctx.send(f"⚔️ Desafio {'Ranqueado ' if is_ranked else ''}enviado para **{target_char['name']}**! Ele(a) tem 60 segundos para aceitar.")

        target_channel = self.bot.get_channel(target_char['channel_id'])
        if target_channel:
            await target_channel.send(f"⚔️ <@{target_id}>, você foi desafiado para um duelo por **{challenger_char['name']}**! Use `!pvp accept {challenger_char['name']}` ou `!pvp decline`.")

        await asyncio.sleep(60)
        if self.bot.pvp_invitations.get(target_id) == challenger_id:
            del self.bot.pvp_invitations[target_id]
            if f"{target_id}_ranked" in self.bot.pvp_invitations: del self.bot.pvp_invitations[f"{target_id}_ranked"]
            await ctx.send(f"O desafio para **{target_char['name']}** expirou.")

    @pvp.command(name="accept", help="Aceita um desafio de duelo.")
    async def pvp_accept(self, ctx):
        challenged_id = ctx.author.id
        challenger_id = self.bot.pvp_invitations.get(challenged_id)

        if not challenger_id:
            await ctx.send("Você não tem um desafio pendente.")
            return

        challenger_char = database.get_character(challenger_id)
        if not challenger_char:
            await ctx.send("O desafiante não foi encontrado.")
            return

        is_ranked = self.bot.pvp_invitations.get(f"{challenged_id}_ranked", False)
        del self.bot.pvp_invitations[challenged_id]
        if f"{challenged_id}_ranked" in self.bot.pvp_invitations: del self.bot.pvp_invitations[f"{challenged_id}_ranked"]

        challenged_char = database.get_character(challenged_id)

        battle = PVPBattle(challenger_char, challenged_char, ranked=is_ranked)
        self.bot.active_pvp_battles[challenger_id] = battle
        self.bot.active_pvp_battles[challenged_id] = battle

        challenger_channel = self.bot.get_channel(challenger_char['channel_id'])
        
        if challenger_channel:
            await challenger_channel.send(f"**{challenged_char['name']}** aceitou seu desafio! A batalha vai começar!")
        await ctx.send(f"Você aceitou o desafio de **{challenger_char['name']}**! A batalha vai começar!")

        await self.run_pvp_battle(battle)

    @pvp.command(name="decline", help="Recusa um desafio de duelo.")
    async def pvp_decline(self, ctx):
        challenged_id = ctx.author.id
        challenger_id = self.bot.pvp_invitations.get(challenged_id)

        if not challenger_id:
            await ctx.send("Você não tem um desafio para recusar.")
            return

        challenger_char = database.get_character(challenger_id)
        del self.bot.pvp_invitations[challenged_id]
        if f"{challenged_id}_ranked" in self.bot.pvp_invitations: del self.bot.pvp_invitations[f"{challenged_id}_ranked"]

        await ctx.send("Você recusou o desafio.")
        if challenger_char:
            challenger_channel = self.bot.get_channel(challenger_char['channel_id'])
            if challenger_channel:
                challenged_char = database.get_character(challenged_id)
                await challenger_channel.send(f"**{challenged_char['name']}** recusou seu desafio.")

async def setup(bot):
    await bot.add_cog(PVP(bot))