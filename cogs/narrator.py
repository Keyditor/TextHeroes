import discord
from discord.ext import commands
import database
from narrator_system import NarrativeSession

class Narrator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="narrate", aliases=["adventure", "aventura"], help="Inicia uma aventura narrada por uma IA.")
    async def narrate(self, ctx):
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player:
            await ctx.send("Você precisa de um personagem para iniciar uma aventura! Use `!newchar`.")
            return

        if ctx.channel.id != player.get('channel_id'):
            private_channel = self.bot.get_channel(player['channel_id'])
            if private_channel:
                await ctx.send(f"As aventuras acontecem no seu canal privado! Vá para {private_channel.mention} e use o comando lá.")
            else:
                await ctx.send("Não encontrei seu canal privado. A aventura não pode começar.")
            return

        if user_id in self.bot.active_pve_battles or user_id in self.bot.active_pvp_battles or user_id in self.bot.active_dungeons or user_id in self.bot.narrative_sessions:
            await ctx.send("Você já está em outra atividade (batalha, masmorra ou outra aventura). Conclua-a antes de iniciar uma nova.")
            return

        session = NarrativeSession(self.bot, player)
        self.bot.narrative_sessions[user_id] = session
        
        await ctx.send("A névoa da aventura se forma ao seu redor... Um Mestre invisível começa a narrar sua jornada. Responda com suas ações em texto simples (sem o `!`).")
        
        try:
            await session.run(ctx)
        except Exception as e:
            print(f"Erro durante a sessão de narração para {user_id}: {e}")
        finally: # Garante que a sessão seja sempre removida
            # Garante que a sessão seja removida ao final, seja por conclusão ou erro
            if user_id in self.bot.narrative_sessions:
                del self.bot.narrative_sessions[user_id]

async def setup(bot):
    await bot.add_cog(Narrator(bot))
