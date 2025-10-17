import discord
from discord.ext import commands
import random
import database
from battle_system import PVEBattle

class Gameplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def start_pve_battle(self, ctx, is_autohunt, enemy_name=None):
        """Função unificada para iniciar batalhas PVE (hunt e autohunt)."""
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player:
            await ctx.send(f"Você precisa de um personagem para caçar! Use `!newchar`.")
            return

        if ctx.channel.id != player.get('channel_id'):
            private_channel = self.bot.get_channel(player['channel_id'])
            if private_channel:
                await ctx.send(f"As batalhas acontecem no seu canal privado! Vá para {private_channel.mention} e use o comando lá.")
            else:
                await ctx.send("Não encontrei seu canal privado. Tente usar o comando lá ou contate um administrador.")
            return

        if user_id in self.bot.active_pve_battles or user_id in self.bot.active_pvp_battles:
            await ctx.send("Você já está em uma batalha! Conclua-a antes de iniciar outra.")
            return

        is_elite = random.random() < 0.1
        enemy = None
        if enemy_name:
            enemy = database.get_enemy_by_name(enemy_name)
            if enemy and player['level'] <= enemy['max_level']:
                await ctx.send(f"Você ainda não superou o poder de **{enemy['name']}**. Para caçá-lo diretamente, seu nível deve ser maior que {enemy['max_level']}.")
                return
        else:
            enemy = database.get_random_enemy(player['level'])

        if not enemy:
            await ctx.send(f"Inimigo '{enemy_name}' não encontrado." if enemy_name else "Nenhum inimigo encontrado para o seu nível.")
            return

        original_enemy_name = enemy['name']

        if is_elite and not enemy_name:
            enemy['name'] = f"⭐ **ELITE** {enemy['name']}"
            enemy['hp'] = round(enemy['hp'] * 1.75)
            enemy['attack'] = round(enemy['attack'] * 1.75)
            enemy['defense'] = round(enemy['defense'] * 1.75)
            enemy['xp_reward'] = round(enemy['xp_reward'] * 2)
            enemy['gold_reward'] = round(enemy['gold_reward'] * 2)

        battle = PVEBattle(self.bot, player, enemy, original_enemy_name, is_autohunt, is_elite, self.bot.active_pve_battles)
        self.bot.active_pve_battles[user_id] = battle

        await battle.send_versus_embed(ctx)

        if is_autohunt:
            await battle.run_autohunt_loop(ctx)
        else:
            await battle.run_manual_loop(ctx)

    @commands.command(name="hunt", aliases=["battle", "explorar"], help="Inicia uma batalha com um inimigo aleatório.")
    async def hunt(self, ctx, *, enemy_name: str = None):
        await self.start_pve_battle(ctx, is_autohunt=False, enemy_name=enemy_name)

    @commands.command(name="autohunt", aliases=["afk"], help="Inicia uma batalha automática para farm de XP e itens.")
    async def autohunt(self, ctx, *, enemy_name: str = None):
        await self.start_pve_battle(ctx, is_autohunt=True, enemy_name=enemy_name)

    @commands.command(name="bestiary", aliases=["inimigos", "monstros"], help="Lista os inimigos que você pode encontrar.")
    async def bestiary(self, ctx):
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player:
            await ctx.send("Você precisa de um personagem para consultar o bestiário.")
            return

        embed = discord.Embed(title="📖 Bestiário 📖", description=f"Informações sobre as criaturas para seu nível ({player['level']}).", color=discord.Color.dark_red())

        random_enemies = database.get_enemies_for_level(player['level'])
        if random_enemies:
            random_desc = "\n".join([f"**{e['name']}** (Nível {e['min_level']}-{e['max_level']})" for e in random_enemies])
            embed.add_field(name="--- Encontros Aleatórios no seu Nível ---", value=random_desc, inline=False)

        huntable_enemies = database.get_all_huntable_enemies(player['level'])
        if huntable_enemies:
            huntable_desc = ", ".join([f"`{e['name']}`" for e in huntable_enemies])
            embed.add_field(name="--- Caça Direcionada Disponível ---", value=f"Você pode usar `!hunt <nome>` para caçar: {huntable_desc}", inline=False)

        embed.set_footer(text="Novas criaturas podem ser descobertas ao subir de nível.")
        await ctx.send(embed=embed)

    @commands.group(name="quest", aliases=["missao"], help="Gerencia suas missões.", invoke_without_command=True)
    async def quest(self, ctx):
        await self.bot.get_command('help').callback(ctx, command_name="quest")

    @quest.command(name="list", help="Lista as missões diárias e semanais disponíveis.")
    async def quest_list(self, ctx):
        user_id = ctx.author.id
        if not database.get_character(user_id):
            await ctx.send("Você precisa de um personagem para ver as missões.")
            return

        daily_quests = database.get_available_quests(user_id, 'daily')
        weekly_quests = database.get_available_quests(user_id, 'weekly')

        embed = discord.Embed(title="📜 Quadro de Missões 📜", description="Use `!quest accept <ID>` para aceitar uma missão.", color=discord.Color.dark_green())
        
        daily_desc = "\n".join([f"**ID {q['id']}**: {q['name']} - *{q['description']}*" for q in daily_quests]) if daily_quests else "Nenhuma missão diária nova."
        embed.add_field(name="--- Missões Diárias ---", value=daily_desc, inline=False)

        weekly_desc = "\n".join([f"**ID {q['id']}**: {q['name']} - *{q['description']}*" for q in weekly_quests]) if weekly_quests else "Nenhuma missão semanal nova."
        embed.add_field(name="--- Missões Semanais ---", value=weekly_desc, inline=False)

        embed.set_footer(text="Missões diárias e semanais são reiniciadas periodicamente.")
        await ctx.send(embed=embed)

    @quest.command(name="myquests", aliases=["ativas"], help="Mostra suas missões ativas e seu progresso.")
    async def my_quests(self, ctx):
        user_id = ctx.author.id
        if not database.get_character(user_id):
            await ctx.send("Você precisa de um personagem para ter missões.")
            return

        active_quests = database.get_player_active_quests(user_id)
        if not active_quests:
            await ctx.send("Você não tem nenhuma missão ativa. Use `!quest list` para ver as disponíveis.")
            return

        embed = discord.Embed(title="📖 Diário de Missões 📖", description="Seu progresso nas missões atuais.", color=discord.Color.orange())
        for q in active_quests:
            status = "✅" if q['progress'] >= q['objective_quantity'] else "⏳"
            embed.add_field(
                name=f"{status} {q['name']} (ID: {q['id']})",
                value=f"*{q['description']}*\n**Progresso:** {q['progress']} / {q['objective_quantity']} {q['objective_target']}s",
                inline=False
            )
        embed.set_footer(text="Use `!quest complete <ID>` para entregar uma missão completa.")
        await ctx.send(embed=embed)

    @quest.command(name="accept", help="Aceita uma missão do quadro.")
    async def accept_quest(self, ctx, quest_id: int):
        user_id = ctx.author.id
        if not database.get_character(user_id):
            await ctx.send("Você precisa de um personagem para aceitar missões.")
            return

        quest_to_accept = database.get_quest_by_id(quest_id)
        if not quest_to_accept:
            await ctx.send("ID de missão inválido.")
            return

        if database.accept_quest(user_id, quest_id):
            await ctx.send(f"Missão **'{quest_to_accept['name']}'** aceita! Veja seu progresso com `!quest myquests`.")
        else:
            await ctx.send("Não foi possível aceitar a missão. Você já pode tê-la aceitado ou ocorreu um erro.")

    @quest.command(name="complete", help="Completa uma missão e recebe as recompensas.")
    async def complete_quest(self, ctx, quest_id: int):
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player:
            await ctx.send("Você precisa de um personagem para completar missões.")
            return

        active_quests = database.get_player_active_quests(user_id)
        quest_to_complete = next((q for q in active_quests if q['id'] == quest_id), None)

        if not quest_to_complete:
            await ctx.send("Você não tem essa missão ativa ou o ID é inválido.")
            return

        if quest_to_complete['progress'] < quest_to_complete['objective_quantity']:
            await ctx.send("Você ainda não completou os objetivos desta missão!")
            return
        
        quest_info = database.get_quest_by_id(quest_id)
        _, bonuses = database.get_equipped_items(user_id)

        base_xp_reward = quest_info['xp_reward']
        base_gold_reward = quest_info['gold_reward']

        xp_bonus_percent = bonuses.get("special", {}).get("XP_BONUS_PERCENT", 0)
        gold_bonus_percent = bonuses.get("special", {}).get("GOLD_BONUS_PERCENT", 0)

        bonus_xp = round(base_xp_reward * (xp_bonus_percent / 100))
        bonus_gold = round(base_gold_reward * (gold_bonus_percent / 100))

        final_xp_reward = base_xp_reward + bonus_xp
        final_gold_reward = base_gold_reward + bonus_gold

        updates = {
            'experience': player['experience'] + final_xp_reward,
            'gold': player['gold'] + final_gold_reward
        }

        reward_message = f"🎉 Missão **'{quest_info['name']}'** completa!\n"
        reward_message += f"Você recebeu **{base_xp_reward}** XP{' (+'+str(bonus_xp)+')' if bonus_xp > 0 else ''} e **{base_gold_reward}** Ouro{' (+'+str(bonus_gold)+')' if bonus_gold > 0 else ''}!"

        if quest_info.get('item_reward_id') and quest_info.get('item_reward_quantity'):
            item_id = quest_info['item_reward_id']
            item_quantity = quest_info['item_reward_quantity']
            database.add_item_to_inventory(user_id, item_id, item_quantity)
            reward_item = database.get_item_by_id(item_id)
            if reward_item:
                reward_message += f"\nE também recebeu **{item_quantity}x {reward_item['name']}**!"

        database.update_character_stats(user_id, updates)
        database.complete_quest(user_id, quest_id)

        await ctx.send(reward_message)

async def setup(bot):
    await bot.add_cog(Gameplay(bot))