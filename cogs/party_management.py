import discord
from discord.ext import commands
import database
import asyncio

class PartyManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="party", aliases=["grupo"], help="Gerencia seu grupo de aventureiros.", invoke_without_command=True)
    async def party(self, ctx):
        """Mostra o status do grupo atual ou a ajuda do comando."""
        user_id = ctx.author.id
        party_id = database.get_party_by_member(user_id)

        if not party_id:
            await ctx.send("Você não está em um grupo. Use `!party create` para começar ou espere um convite.")
            return

        party_details = database.get_party_details(party_id)
        if not party_details:
            await ctx.send("Ocorreu um erro ao buscar os detalhes do seu grupo.")
            return

        leader = next((m for m in party_details['members'] if m['user_id'] == party_details['leader_id']), None)
        
        embed = discord.Embed(title=f"Grupo de {leader['name'] if leader else 'Aventureiros'}", color=discord.Color.dark_purple())
        
        members_str = []
        for member in party_details['members']:
            role = "👑 Líder" if member['user_id'] == party_details['leader_id'] else "⚔️ Membro"
            members_str.append(f"**{member['name']}** (Nível {member['level']}) - {role}")

        embed.description = "\n".join(members_str)
        embed.set_footer(text=f"Total de membros: {len(party_details['members'])}/4")
        await ctx.send(embed=embed)

    @party.command(name="create", help="Cria um novo grupo.")
    async def create(self, ctx):
        user_id = ctx.author.id
        if not database.get_character(user_id):
            await ctx.send("Você precisa de um personagem para criar um grupo.")
            return

        if database.get_party_by_member(user_id):
            await ctx.send("Você já está em um grupo. Use `!party leave` para sair primeiro.")
            return

        if database.create_party(user_id):
            await ctx.send(f"🎉 Grupo criado! Você é o líder. Use `!party invite <@membro>` para convidar jogadores.")
        else:
            await ctx.send("Não foi possível criar o grupo. Verifique se você não é líder de outro grupo.")

    @party.command(name="invite", help="Convida um jogador para o seu grupo.")
    @commands.has_permissions(mention_everyone=False)
    async def invite(self, ctx, member: discord.Member):
        leader_id = ctx.author.id
        party_id = database.get_party_by_leader(leader_id)

        if not party_id:
            await ctx.send("Você não é o líder de um grupo.")
            return

        invited_id = member.id
        if not database.get_character(invited_id):
            await ctx.send(f"**{member.display_name}** não tem um personagem.")
            return

        if database.get_party_by_member(invited_id):
            await ctx.send(f"**{member.display_name}** já está em um grupo.")
            return

        self.bot.party_invitations[invited_id] = leader_id
        await ctx.send(f"✅ Convite enviado para **{member.display_name}**. Ele(a) tem 60 segundos para aceitar.")
        await member.send(f"⚔️ Você foi convidado por **{ctx.author.display_name}** para se juntar ao grupo dele(a)! Use `!party accept` ou `!party decline` em qualquer canal do servidor.")

        await asyncio.sleep(60)
        if self.bot.party_invitations.get(invited_id) == leader_id:
            del self.bot.party_invitations[invited_id]
            await ctx.send(f"O convite para **{member.display_name}** expirou.")

    @party.command(name="accept", help="Aceita um convite de grupo.")
    async def accept(self, ctx):
        user_id = ctx.author.id
        leader_id = self.bot.party_invitations.get(user_id)

        if not leader_id:
            await ctx.send("Você não tem convites pendentes.")
            return

        party_id = database.get_party_by_leader(leader_id)
        if not party_id:
            await ctx.send("O grupo para o qual você foi convidado não existe mais.")
            return

        if database.add_member_to_party(party_id, user_id):
            del self.bot.party_invitations[user_id]
            await ctx.send(f"Você se juntou ao grupo de <@{leader_id}>!")
        else:
            await ctx.send("Não foi possível entrar no grupo. Você já pode estar em outro.")

    @party.command(name="decline", help="Recusa um convite de grupo.")
    async def decline(self, ctx):
        user_id = ctx.author.id
        if user_id in self.bot.party_invitations:
            del self.bot.party_invitations[user_id]
            await ctx.send("Convite recusado.")
        else:
            await ctx.send("Você não tem convites pendentes.")

    @party.command(name="leave", help="Sai do seu grupo atual.")
    async def leave(self, ctx):
        user_id = ctx.author.id
        party_id = database.get_party_by_member(user_id)
        if not party_id:
            await ctx.send("Você não está em um grupo.")
            return

        party_details = database.get_party_details(party_id)
        if user_id == party_details['leader_id']:
            await ctx.send("Você é o líder. Use `!party disband` para dissolver o grupo.")
            return

        if database.remove_member_from_party(user_id):
            await ctx.send("Você saiu do grupo.")

    @party.command(name="kick", help="Remove um membro do grupo (somente líder).")
    async def kick(self, ctx, member: discord.Member):
        leader_id = ctx.author.id
        party_id = database.get_party_by_leader(leader_id)
        if not party_id:
            await ctx.send("Você não é o líder de um grupo.")
            return

        if database.remove_member_from_party(member.id):
            await ctx.send(f"**{member.display_name}** foi removido(a) do grupo.")

    @party.command(name="disband", help="Dissolve o grupo (somente líder).")
    async def disband(self, ctx):
        leader_id = ctx.author.id
        party_id = database.get_party_by_leader(leader_id)
        if not party_id:
            await ctx.send("Você não é o líder de um grupo.")
            return

        if database.disband_party(party_id):
            await ctx.send("O grupo foi dissolvido.")

async def setup(bot):
    await bot.add_cog(PartyManagement(bot))