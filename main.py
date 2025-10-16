import discord
from discord.ext import commands, tasks
import os, sys
import asyncio

from datetime import datetime, timedelta
import random
from config import DISCORD_BOT_TOKEN, GENERAL_CHANNEL_NAME, OWNER_ID
import database
from game_constants import *


# --- Configurações do Bot ---

# Intents são permissões que seu bot precisa para acessar certos eventos do Discord.
# Para criar canais e interagir com membros, precisamos de algumas.
intents = discord.Intents.default()
intents.reactions = True
intents.message_content = True  # Necessário para ler o conteúdo das mensagens
intents.members = True          # Necessário para gerenciar membros e permissões de canal
intents.guilds = True           # Necessário para a tarefa de reset de missões

# Adiciona um prefixo dinâmico para evitar conflitos
bot = commands.Bot(command_prefix="!", intents=intents)

# Importa após a criação do bot para evitar importação circular
from battle_system import PVEBattle, PVPBattle

# --- Gerenciamento de Estado Global ---
bot.pvp_invitations = {} # Armazena convites de duelo {desafiado_id: desafiante_id}
bot.party_invitations = {} # Armazena convites de grupo {convidado_id: lider_id}
bot.active_pvp_battles = {} # Armazena batalhas ativas {user_id: battle_instance}
bot.active_pve_battles = {} # Armazena batalhas PVE ativas {user_id: battle_instance}
bot.active_dungeons = {} # Armazena masmorras ativas {user_id: dungeon_instance}
bot.dungeon_queues = {} # Armazena as filas para masmorras {dungeon_name: [user_id]}
bot.dungeon_match_prompts = {} # Armazena os "pronto-check" {match_id: {players: {user_id: status}}}
bot.debug_mode = False # Controla a exibição de logs de cálculo no console

async def get_general_channel(guild):
    """Encontra o canal #geral no servidor."""
    for channel in guild.text_channels:
        if channel.name == GENERAL_CHANNEL_NAME:
            return channel
    return None

# --- Eventos do Bot ---

def sync_guilds():
    """Sincroniza a lista de servidores do bot com o banco de dados."""
    print("Sincronizando servidores com o banco de dados...")
    for guild in bot.guilds:
        database.register_guild(guild.id, guild.name)
    print(f"Sincronização concluída. O bot está em {len(bot.guilds)} servidor(es).")

@bot.event
async def on_ready():
    """Evento disparado quando o bot está online."""
    print(f'Bot conectado como {bot.user.name} (ID: {bot.user.id})')
    print('------')

    # Verificação de autenticidade do criador
    try:
        owner = await bot.fetch_user(OWNER_ID)
        # O nome de usuário no Discord (sem o #) é único e não diferencia maiúsculas/minúsculas na verificação.
        if owner.name.lower() != "keyditor":
            print("="*50)
            print("ERRO DE AUTENTICAÇÃO: O ID do proprietário não corresponde a 'Keyditor'.")
            print("Por favor, mantenha os créditos ao criador original conforme a licença.")
            print("O bot não será inicializado.")
            print("="*50)
            await bot.close()
            return
    except discord.NotFound:
        print("="*50)
        print(f"ERRO: O ID do proprietário ({OWNER_ID}) definido em config.py não foi encontrado.")
        print("O bot não será inicializado.")
        print("="*50)
        await bot.close()
        return

    database.init_db() # Garante que o DB está inicializado ao iniciar o bot
    sync_guilds() # Sincroniza os servidores ao iniciar
    await load_cogs() # Carrega todos os cogs
    quest_reset_task.start() # Inicia a tarefa de reset de missões

async def load_cogs():
    """Carrega todos os cogs da pasta /cogs."""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Cog '{filename[:-3]}' carregado.")

@bot.event
async def on_guild_join(guild):
    """Evento disparado quando o bot entra em um novo servidor."""
    print(f"Bot adicionado ao servidor: {guild.name} (ID: {guild.id})")
    database.register_guild(guild.id, guild.name)

@bot.event
async def on_guild_remove(guild):
    """Evento disparado quando o bot é removido de um servidor."""
    print(f"Bot removido do servidor: {guild.name} (ID: {guild.id})")
    database.unregister_guild(guild.id)

# --- Tarefas em Segundo Plano (Tasks) ---

@tasks.loop(hours=1)
async def quest_reset_task():
    """Verifica e reinicia as missões diárias e semanais."""
    now = datetime.utcnow()
    today_str = now.strftime('%Y-%m-%d')
    
    # --- Reset Diário ---
    last_daily_reset_str = database.get_server_state('last_daily_reset')
    if last_daily_reset_str < today_str:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando reset de missões diárias...")
        database.reset_player_quests_by_type('daily')
        database.set_server_state('last_daily_reset', today_str)
        print("Reset de missões diárias concluído.")
        
        # Notifica o canal geral de cada servidor
        for guild in bot.guilds:
            general_channel = await get_general_channel(guild)
            if general_channel:
                try:
                    await general_channel.send("☀️ **Novas missões diárias estão disponíveis!** Use `!quest list` para vê-las.")
                except discord.Forbidden:
                    print(f"Não foi possível enviar a mensagem de reset no servidor '{guild.name}'.")

    # --- Reset Semanal (Toda Segunda-feira) ---
    last_weekly_reset_str = database.get_server_state('last_weekly_reset')
    last_weekly_reset_date = datetime.strptime(last_weekly_reset_str, '%Y-%m-%d')
    
    # Se hoje é segunda (weekday==0) e o último reset foi antes desta semana
    if now.weekday() == 0 and (now - last_weekly_reset_date).days >= 7:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando reset de missões semanais...")
        database.reset_player_quests_by_type('weekly')
        database.set_server_state('last_weekly_reset', today_str)
        print("Reset de missões semanais concluído.")
        # Você pode adicionar uma notificação para o reset semanal aqui também se desejar.



@bot.event
async def on_command_error(ctx, error):
    """Tratamento de erros para comandos."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Faltando argumento(s) para o comando. Uso correto: `{ctx.command.usage}`")
    elif not isinstance(error, commands.CommandNotFound): # Ignora erros de comando não encontrado
        print(f"Erro no comando {ctx.command}: {error}")
        await ctx.send(f"Ocorreu um erro ao executar o comando: `{error}`")

# --- Executar o Bot ---

if __name__ == "__main__":
    try:
        asyncio.run(bot.run(DISCORD_BOT_TOKEN))
    except discord.errors.LoginFailure:
        print("ERRO: Token do bot inválido. Verifique o arquivo 'config.py'.")