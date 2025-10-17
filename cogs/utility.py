import discord
from discord.ext import commands
import database
from config import OWNER_ID

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Remove o comando de ajuda padrão para substituí-lo
        self.bot.remove_command('help')

    @commands.command(name="help", aliases=["ajuda"], help="Mostra esta mensagem de ajuda.")
    async def custom_help(self, ctx, *, command_name: str = None):
        if command_name:
            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(title=f"Ajuda para: `!{command.name}`", description=command.help, color=discord.Color.green())
                usage = f"!{command.name} {command.signature}"
                embed.add_field(name="Uso", value=f"`{usage}`", inline=False)
                if command.aliases:
                    embed.add_field(name="Alternativas", value=", ".join([f"`!{a}`" for a in command.aliases]), inline=False)
                if isinstance(command, commands.Group):
                    subcommands_desc = "\n".join([f"`!{command.name} {c.name}` - {c.help}" for c in command.commands])
                    embed.add_field(name="Subcomandos", value=subcommands_desc, inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Comando `{command_name}` não encontrado.")
        else:
            embed = discord.Embed(title="📜 Guia de Comandos do RPG 📜", description="Aqui estão os comandos que você pode usar:", color=discord.Color.blurple())
            
            categories = {
                "Personagem": ["newchar", "char", "attribute", "skills", "reset", "migrate"],
                "Ação": ["hunt", "autohunt", "use"],
                "Equipamento": ["inventory", "equip", "unequip", "enhance"],
                "Interação": ["shop", "market", "job", "work", "payday"],
                "Grupo & Aventura": ["party", "dungeon", "pvp"],
                "Utilidade": ["quest", "bestiary", "leaderboard", "gm", "help"]
            }
            for category, cmd_list in categories.items():
                # Filtra comandos que podem não existir ou não foram carregados
                valid_cmds = [self.bot.get_command(c) for c in cmd_list if self.bot.get_command(c)]
                if not valid_cmds: continue
                
                cmd_descriptions = "\n".join([f"`!{cmd.name}` - {cmd.help}" for cmd in valid_cmds])
                embed.add_field(name=f"**--- {category} ---**", value=cmd_descriptions, inline=False)
            
            embed.set_footer(text="Use !help <comando> para ver detalhes de um comando específico.")
            await ctx.send(embed=embed)

    @commands.command(name="gm", help="Mostra os créditos do criador do bot.")
    async def gm_command(self, ctx):
        embed = discord.Embed(
            title="Créditos do TextHeroes",
            description=f"Este bot foi desenvolvido com ❤️ por <@{OWNER_ID}>.",
            color=discord.Color.from_rgb(114, 137, 218)
        )
        embed.add_field(name="GitHub", value="https://github.com/Keyditor/TextHeroes-RPG-BOT")
        embed.set_footer(text="Sinta-se livre para usar este código como base para seus próprios projetos!")
        await ctx.send(embed=embed)

        try:
            owner = await self.bot.fetch_user(OWNER_ID)
            if owner:
                await owner.send(f"ℹ️ O comando `!gm` foi usado no servidor **'{ctx.guild.name}'** pelo usuário **{ctx.author.name}**.")
        except Exception as e:
            print(f"Não foi possível enviar a notificação para o dono do bot: {e}")

    @commands.command(name="leaderboard", aliases=["ranking", "top"], help="Mostra os rankings do servidor.")
    async def leaderboard(self, ctx, ranking_type: str = 'level'):
        if ranking_type.lower() not in ['level', 'pvp']:
            await ctx.send("Tipo de ranking inválido. Use `level` ou `pvp`.")
            return

        if ranking_type.lower() == 'level':
            data = database.get_leaderboard('level')
            embed = discord.Embed(title="🏆 Placar de Líderes - Nível 🏆", description="Os aventureiros mais experientes.", color=discord.Color.gold())
            for i, player in enumerate(data):
                embed.add_field(name=f"#{i+1} - {player['name']}", value=f"**Nível:** {player['level']} | **XP:** {player['experience']}", inline=False)
        
        elif ranking_type.lower() == 'pvp':
            data = database.get_leaderboard('pvp')
            embed = discord.Embed(title="⚔️ Placar de Líderes - PvP Ranqueado ⚔️", description="Os duelistas mais temidos.", color=discord.Color.red())
            for i, player in enumerate(data):
                score = player.get('score', 0)
                embed.add_field(name=f"#{i+1} - {player['name']}", value=f"**Score:** {score} | **Vitórias:** {player['pvp_wins']} | **Derrotas:** {player['pvp_losses']}", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="debug", help="Ativa ou desativa o modo de debug para o console.")
    @commands.is_owner()
    async def debug_mode(self, ctx):
        self.bot.debug_mode = not self.bot.debug_mode
        status = "ATIVADO" if self.bot.debug_mode else "DESATIVADO"
        await ctx.send(f"🔧 Modo de Debug foi **{status}**.")

async def setup(bot):
    await bot.add_cog(Utility(bot))