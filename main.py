import discord
from discord.ext import commands
import os
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

bot = commands.Bot(command_prefix="!", intents=intents)

# Importa após a criação do bot para evitar importação circular
from battle_system import PVEBattle, PVPBattle

# --- Gerenciamento de Estado Global ---
bot.pvp_invitations = {} # Armazena convites de duelo {desafiado_id: desafiante_id}
bot.active_pvp_battles = {} # Armazena batalhas ativas {user_id: battle_instance}
bot.active_pve_battles = {} # Armazena batalhas PVE ativas {user_id: battle_instance}
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
    asyncio.run(bot.run(DISCORD_BOT_TOKEN))