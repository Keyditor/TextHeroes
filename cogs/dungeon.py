import discord
from discord.ext import commands
import database
from dungeon_system import DungeonRun
import asyncio
import uuid

class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.PARTY_SIZE = 4 # Tamanho padrão do grupo para masmorras
        self.MATCH_TIMEOUT = 60 # Segundos para aceitar uma partida

    @commands.group(name="dungeon", aliases=["dg"], help="Acessa as masmorras do jogo.", invoke_without_command=True)
    async def dungeon(self, ctx):
        await self.dungeon_list(ctx)

    @dungeon.command(name="list", help="Lista as masmorras disponíveis.")
    async def dungeon_list(self, ctx):
        player = database.get_character(ctx.author.id)
        if not player:
            await ctx.send("Você precisa de um personagem para ver as masmorras.")
            return

        dungeons = database.get_all_dungeons()
        embed = discord.Embed(title="🚪 Portais de Masmorra 🚪", description="Escolha seu desafio. Use `!dungeon <modo> <nome>`.", color=discord.Color.dark_red())

        for dg in dungeons:
            unlocked = "✅" if player['level'] >= dg['level_req'] else "🔒"
            embed.add_field(
                name=f"{unlocked} {dg['name']} (Nível {dg['level_req']}+)",
                value=f"*{dg['description']}*",
                inline=False
            )
        
        embed.set_footer(text="Modos: solo, party, queue")
        await ctx.send(embed=embed)

    @dungeon.command(name="solo", help="Entra em uma masmorra sozinho (recompensas x4).")
    async def solo(self, ctx, *, dungeon_name: str):
        user_id = ctx.author.id
        if user_id in self.bot.active_dungeons or user_id in self.bot.active_pve_battles or user_id in self.bot.active_pvp_battles:
            await ctx.send("Você já está em uma aventura (batalha ou masmorra). Termine-a antes de começar outra.")
            return

        player = database.get_character(ctx.author.id)
        if not player:
            await ctx.send("Você precisa de um personagem.")
            return

        dungeon = database.get_dungeon_by_name(dungeon_name)
        if not dungeon:
            await ctx.send("Masmorra não encontrada.")
            return

        if player['level'] < dungeon['level_req']:
            await ctx.send(f"Você não tem o nível necessário ({dungeon['level_req']}) para entrar em **{dungeon['name']}**.")
            return

        await ctx.send(f"Preparando para entrar em **{dungeon['name']}** sozinho... Sua aventura acontecerá neste canal.")
        
        # Cria e inicia a instância da masmorra
        dungeon_run = DungeonRun(self.bot, [player], dungeon, mode='solo')
        self.bot.active_dungeons[user_id] = dungeon_run
        await dungeon_run.run(ctx)

    @dungeon.command(name="party", help="Entra em uma masmorra com seu grupo.")
    async def party_start(self, ctx, *, dungeon_name: str):
        leader_id = ctx.author.id
        party_id = database.get_party_by_leader(leader_id)

        if not party_id:
            await ctx.send("Apenas o líder do grupo pode iniciar uma masmorra. Use `!party create` para formar um grupo.")
            return

        party_details = database.get_party_details(party_id)
        if not party_details:
            await ctx.send("Não foi possível encontrar os detalhes do seu grupo.")
            return

        dungeon = database.get_dungeon_by_name(dungeon_name)
        if not dungeon:
            await ctx.send(f"Masmorra '{dungeon_name}' não encontrada.")
            return

        # Verifica os requisitos e status de todos os membros
        party_members_chars = []
        for member_info in party_details['members']:
            member_id = member_info['user_id']
            member_char = database.get_character(member_id)
            
            if member_char['level'] < dungeon['level_req']:
                await ctx.send(f"O membro **{member_char['name']}** não tem o nível necessário ({dungeon['level_req']}).")
                return
            
            if member_id in self.bot.active_dungeons or member_id in self.bot.active_pve_battles or member_id in self.bot.active_pvp_battles:
                await ctx.send(f"O membro **{member_char['name']}** já está em uma aventura.")
                return
            
            party_members_chars.append(member_char)

        await ctx.send(f"O grupo se prepara para adentrar **{dungeon['name']}**! A aventura acontecerá neste canal.")

        # Cria e inicia a instância da masmorra para o grupo
        dungeon_run = DungeonRun(self.bot, party_members_chars, dungeon, mode='party')
        for member_char in party_members_chars:
            self.bot.active_dungeons[member_char['user_id']] = dungeon_run
        await dungeon_run.run(ctx)

    @dungeon.command(name="queue", help="Entra na fila para uma masmorra.")
    async def queue(self, ctx, *, dungeon_name: str):
        user_id = ctx.author.id
        if user_id in self.bot.active_dungeons or user_id in self.bot.active_pve_battles or user_id in self.bot.active_pvp_battles:
            await ctx.send("Você já está em uma aventura. Não pode entrar na fila.")
            return

        player = database.get_character(user_id)
        if not player:
            await ctx.send("Você precisa de um personagem para entrar na fila.")
            return

        dungeon = database.get_dungeon_by_name(dungeon_name)
        if not dungeon:
            await ctx.send(f"Masmorra '{dungeon_name}' não encontrada.")
            return

        if player['level'] < dungeon['level_req']:
            await ctx.send(f"Você não tem o nível necessário ({dungeon['level_req']}) para esta masmorra.")
            return

        # Verifica se o jogador já está em alguma fila
        for queue_list in self.bot.dungeon_queues.values():
            if user_id in queue_list:
                await ctx.send("Você já está em uma fila. Use `!dungeon leavequeue` para sair.")
                return

        dungeon_name_key = dungeon['name']
        if dungeon_name_key not in self.bot.dungeon_queues:
            self.bot.dungeon_queues[dungeon_name_key] = []

        self.bot.dungeon_queues[dungeon_name_key].append(user_id)
        queue_position = len(self.bot.dungeon_queues[dungeon_name_key])
        
        await ctx.send(f"✅ Você entrou na fila para **{dungeon_name_key}**. Posição: {queue_position}/{self.PARTY_SIZE}.")

        # Verifica se a fila está cheia para iniciar o "pronto-check"
        if len(self.bot.dungeon_queues[dungeon_name_key]) >= self.PARTY_SIZE:
            await self._trigger_match_prompt(ctx, dungeon_name_key)

    @dungeon.command(name="leavequeue", help="Sai da fila de masmorra em que você está.")
    async def leavequeue(self, ctx):
        user_id = ctx.author.id
        
        queue_found_for_dungeon = None
        for dungeon_name, queue_list in self.bot.dungeon_queues.items():
            if user_id in queue_list:
                queue_found_for_dungeon = dungeon_name
                break

        if not queue_found_for_dungeon:
            await ctx.send("Você não está em nenhuma fila no momento.")
            return

        self.bot.dungeon_queues[queue_found_for_dungeon].remove(user_id)
        if not self.bot.dungeon_queues[queue_found_for_dungeon]: # Limpa a chave se a fila ficar vazia
            del self.bot.dungeon_queues[queue_found_for_dungeon]

        await ctx.send(f"Você saiu da fila para **{queue_found_for_dungeon}**.")

    async def _trigger_match_prompt(self, ctx, dungeon_name):
        """Inicia o processo de confirmação de partida."""
        queue = self.bot.dungeon_queues[dungeon_name]
        players_to_match = queue[:self.PARTY_SIZE]
        self.bot.dungeon_queues[dungeon_name] = queue[self.PARTY_SIZE:] # Remove os jogadores da fila

        match_id = str(uuid.uuid4())
        self.bot.dungeon_match_prompts[match_id] = {
            'dungeon_name': dungeon_name,
            'players': {player_id: 'pending' for player_id in players_to_match},
            'channel_id': ctx.channel.id
        }

        mentions = " ".join([f"<@{pid}>" for pid in players_to_match])
        await ctx.send(f"⚔️ **Partida encontrada para {dungeon_name}!** ⚔️\n{mentions}\nTodos os jogadores têm **{self.MATCH_TIMEOUT} segundos** para digitar `!dungeon accept` para confirmar.")

        await asyncio.sleep(self.MATCH_TIMEOUT)

        # Verifica o resultado após o timeout
        if match_id in self.bot.dungeon_match_prompts:
            match_info = self.bot.dungeon_match_prompts[match_id]
            pending_players = [pid for pid, status in match_info['players'].items() if status == 'pending']
            accepted_players = [pid for pid, status in match_info['players'].items() if status == 'accepted']

            if pending_players:
                await ctx.send(f"A partida para **{dungeon_name}** foi cancelada porque alguns jogadores não aceitaram a tempo.")
                # Devolve os jogadores que aceitaram para o início da fila
                self.bot.dungeon_queues[dungeon_name] = accepted_players + self.bot.dungeon_queues.get(dungeon_name, [])
                if accepted_players:
                    await ctx.send("Jogadores que aceitaram foram colocados de volta no início da fila.")
            
            del self.bot.dungeon_match_prompts[match_id]

    @dungeon.command(name="accept", help="Aceita uma partida de masmorra encontrada.")
    async def accept(self, ctx):
        user_id = ctx.author.id
        match_id_found = None
        for match_id, match_info in self.bot.dungeon_match_prompts.items():
            if user_id in match_info['players']:
                match_id_found = match_id
                break

        if not match_id_found:
            await ctx.send("Você não tem uma partida pendente para aceitar.")
            return

        match = self.bot.dungeon_match_prompts[match_id_found]
        match['players'][user_id] = 'accepted'
        await ctx.send(f"✅ **{ctx.author.display_name}** aceitou a partida!")

        # Verifica se todos aceitaram
        if all(status == 'accepted' for status in match['players'].values()):
            dungeon_name = match['dungeon_name']
            player_ids = list(match['players'].keys())
            
            await ctx.send(f"🎉 Todos aceitaram! Iniciando a masmorra **{dungeon_name}**...")
            
            party_members_chars = [database.get_character(pid) for pid in player_ids]
            dungeon_info = database.get_dungeon_by_name(dungeon_name)

            dungeon_run = DungeonRun(self.bot, party_members_chars, dungeon_info, mode='party')
            for member_char in party_members_chars:
                self.bot.active_dungeons[member_char['user_id']] = dungeon_run
            
            # Limpa o prompt
            del self.bot.dungeon_match_prompts[match_id_found]

            await dungeon_run.run(ctx)


async def setup(bot):
    await bot.add_cog(Dungeon(bot))