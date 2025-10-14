import discord
from discord.ext import commands
import asyncio

import random
from config import DISCORD_BOT_TOKEN, GENERAL_CHANNEL_NAME, OWNER_ID
import database

# --- Configurações do Bot ---

# Intents são permissões que seu bot precisa para acessar certos eventos do Discord.
# Para criar canais e interagir com membros, precisamos de algumas.
intents = discord.Intents.default()
intents.reactions = True
intents.message_content = True  # Necessário para ler o conteúdo das mensagens
intents.members = True          # Necessário para gerenciar membros e permissões de canal

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Gerenciamento de Estado Global ---
pvp_invitations = {} # Armazena convites de duelo {desafiado_id: desafiante_id}
active_pvp_battles = {} # Armazena batalhas ativas {user_id: battle_instance}
DEBUG_MODE = False # Controla a exibição de logs de cálculo no console

# --- Constantes do Jogo ---

RACES = ["Humano", "Elfo", "Anão", "Halfling", "Meio-Orc", "Thiefling"]
CLASSES = ["Guerreiro", "Ladino", "Feiticeiro", "Bardo", "Clérigo", "Patrulheiro"]

# Detalhes das Raças (Bônus/Ônus de Atributos)
RACE_MODIFIERS = {
    "Humano": {"strength": 1, "constitution": 1, "dexterity": 1, "intelligence": 1, "wisdom": 1, "charisma": 1},
    "Elfo": {"dexterity": 3, "intelligence": 2, "constitution": -1},
    "Anão": {"constitution": 3, "strength": 2, "dexterity": -1},
    "Halfling": {"dexterity": 3, "charisma": 2, "strength": -1},
    "Meio-Orc": {"strength": 3, "constitution": 2, "intelligence": -1},
    "Thiefling": {"intelligence": 2, "charisma": 3, "wisdom": -1},
}

# Detalhes das Classes (Atributo Chave)
CLASS_DETAILS = {
    "Guerreiro": {"key_attribute": "strength", "type": "physical"},
    "Ladino": {"key_attribute": "dexterity", "type": "physical"},
    "Feiticeiro": {"key_attribute": "intelligence", "type": "magical"},
    "Bardo": {"key_attribute": "charisma", "type": "magical"},
    "Clérigo": {"key_attribute": "wisdom", "type": "magical"},
    "Patrulheiro": {"key_attribute": "dexterity", "type": "physical"},
}

# Mapeamento para o banco de dados
ATTRIBUTE_MAP_PT_EN = {
    "força": "strength", "constituição": "constitution", "destreza": "dexterity",
    "inteligência": "intelligence", "sabedoria": "wisdom", "carisma": "charisma"
}

ATTRIBUTE_MAP_EN_PT = {v: k.capitalize() for k, v in ATTRIBUTE_MAP_PT_EN.items()}


# Pontos para distribuição de atributos (ex: 75 pontos para distribuir entre 6 atributos)
# D&D 5e geralmente usa um array fixo (15, 14, 13, 12, 10, 8) ou point buy.
# Para simplificar, vamos usar um sistema de "point buy" onde o jogador distribui um total de pontos.
TOTAL_ATTRIBUTE_POINTS = 24 # Pontos para distribuir acima do valor mínimo de 8.
MIN_ATTRIBUTE_VALUE = 8
MAX_ATTRIBUTE_VALUE = 15

# --- Constantes de Progressão ---
XP_PER_LEVEL_MULTIPLIER = 100


# --- Funções Auxiliares ---

def calculate_hp_mp(constitution, intelligence, char_class):
    """Calcula HP e MP baseados nos atributos e classe."""
    # Simplificação: HP base + (CON * 5), MP base + (INT ou CHA * 3)
    # Em um RPG real, isso seria mais complexo e dependeria do nível.
    base_hp = 50
    base_mp = 20

    hp = base_hp + (constitution * 5)

    if char_class in ["Feiticeiro", "Bardo"]: # Classes que usam Carisma para magia
        mp = base_mp + (intelligence * 3) # Ou Carisma, dependendo da sua regra
    else: # Outras classes podem ter menos MP ou usar Inteligência
        mp = base_mp + (intelligence * 2)

    return hp, mp

async def get_general_channel(guild):
    """Encontra o canal #geral no servidor."""
    for channel in guild.text_channels:
        if channel.name == GENERAL_CHANNEL_NAME:
            return channel
    return None

# --- Eventos do Bot ---

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

@bot.event
async def on_command_error(ctx, error):
    """Tratamento de erros para comandos."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Faltando argumento(s) para o comando. Uso correto: `{ctx.command.usage}`")
    elif not isinstance(error, commands.CommandNotFound): # Ignora erros de comando não encontrado
        print(f"Erro no comando {ctx.command}: {error}")
        await ctx.send(f"Ocorreu um erro ao executar o comando: `{error}`")

# --- Comandos do Bot ---

@bot.command(name="newchar", help="Cria um novo personagem para o RPG.")
async def new_character(ctx):
    """
    Comando para iniciar o processo de criação de personagem.
    Guia o usuário através da seleção de raça, classe e distribuição de atributos.
    """
    user_id = ctx.author.id
    guild_id = ctx.guild.id

    # 1. Verificar se o usuário já tem um personagem
    existing_char = database.get_character(user_id)
    if existing_char:
        await ctx.send(f"Você já possui um personagem chamado '{existing_char['name']}'. "
                              "Se deseja criar um novo, você precisará deletar o atual primeiro.")
        return

    await ctx.send(f"Bem-vindo(a) à jornada, {ctx.author.mention}! Vamos criar seu personagem. "
                          "Por favor, responda às perguntas a seguir neste canal.")

    # 2. Nome do Personagem
    await ctx.send("Qual o nome do seu personagem?")
    try:
        name_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        char_name = name_msg.content
    except asyncio.TimeoutError:
        await ctx.send("Tempo esgotado. Por favor, comece novamente com `!newchar`.")
        return

    # 3. Seleção de Raça
    races_str = ", ".join(RACES)
    await ctx.send(f"Escolha sua raça: {races_str}")
    try:
        race_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in RACES, timeout=60.0)
        char_race = race_msg.content
    except asyncio.TimeoutError:
        await ctx.send("Tempo esgotado ou raça inválida. Por favor, comece novamente com `!newchar`.")
        return

    # 4. Seleção de Classe
    class_descriptions = {
        "Guerreiro": "Mestre do combate corpo a corpo, usa Força.",
        "Ladino": "Ágil e mortal, usa Destreza para ataques precisos.",
        "Feiticeiro": "Manipulador de energias arcanas, usa Inteligência.",
        "Bardo": "Inspira aliados e amaldiçoa inimigos com seu Carisma.",
        "Clérigo": "Devoto de uma divindade, usa Sabedoria para milagres.",
        "Patrulheiro": "Perito em sobrevivência e combate à distância, usa Destreza."
    }
    classes_str = ", ".join(CLASSES)
    await ctx.send(f"Escolha sua classe: {classes_str}\n" + "\n".join([f"**{c}**: {d}" for c, d in class_descriptions.items()]))
    try:
        class_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in CLASSES, timeout=60.0)
        char_class = class_msg.content
    except asyncio.TimeoutError:
        await ctx.send("Tempo esgotado ou classe inválida. Por favor, comece novamente com `!newchar`.")
        return

    # 5. Distribuição de Atributos
    attributes = {attr.capitalize(): MIN_ATTRIBUTE_VALUE for attr in ATTRIBUTE_MAP_PT_EN.keys()}
    remaining_points = TOTAL_ATTRIBUTE_POINTS

    # Mostra os bônus da raça escolhida
    racial_bonus = RACE_MODIFIERS[char_race]
    bonus_str = ", ".join([f"{attr.capitalize()} {mod:+}" for attr, mod in racial_bonus.items() if mod != 0])

    await ctx.send(f"Agora, vamos distribuir seus atributos. Todos começam em **{MIN_ATTRIBUTE_VALUE}** e você tem **{TOTAL_ATTRIBUTE_POINTS}** pontos para aumentá-los. "
                          f"O valor máximo de um atributo (antes do bônus racial) é **{MAX_ATTRIBUTE_VALUE}**. "
                          f"Sua raça ({char_race}) concede os seguintes bônus: **{bonus_str}**.\nDigite o atributo e o valor. Ex: `Força 15`")

    while remaining_points > 0:
        await ctx.send(f"Pontos restantes: **{remaining_points}**. Atributos atuais: `{attributes}`. "
                              f"Qual atributo você quer alterar? (Ex: `Força 14`)")
        try:
            attr_input_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=120.0)
            parts = attr_input_msg.content.split()
            if len(parts) != 2:
                await ctx.send("Formato inválido. Use `Atributo Valor`, por exemplo: `Força 12`.")
                continue
            
            attr_name_input, value_str = parts
            attr_name = attr_name_input.capitalize()
            
            if attr_name not in attributes:
                await ctx.send(f"Atributo '{attr_name}' inválido. Os atributos são: {list(attributes.keys())}.")
                continue

            value = int(value_str)
            if not (MIN_ATTRIBUTE_VALUE <= value <= MAX_ATTRIBUTE_VALUE):
                await ctx.send(f"Valor inválido. O atributo deve estar entre {MIN_ATTRIBUTE_VALUE} e {MAX_ATTRIBUTE_VALUE}.")
                continue

            attributes[attr_name] = value
            # Recalcula os pontos restantes com base no total gasto
            points_spent = sum(v - MIN_ATTRIBUTE_VALUE for v in attributes.values())
            remaining_points = TOTAL_ATTRIBUTE_POINTS - points_spent

        except (ValueError, asyncio.TimeoutError):
            await ctx.send("Entrada inválida ou tempo esgotado. Por favor, comece novamente com `!newchar`.")
            return

    if remaining_points != 0:
        await ctx.send(f"Você terminou de distribuir os pontos, mas sobraram {remaining_points} pontos. "
                              "Por favor, redistribua para que todos os pontos sejam usados ou comece novamente.")
        # Forcing a restart for simplicity, in a real game you might allow re-distribution
        await ctx.send("Criação de personagem cancelada. Por favor, comece novamente com `!newchar`.")
        return

    # 6. Aplicar modificadores raciais
    final_attributes = {}
    for attr_pt, attr_en in ATTRIBUTE_MAP_PT_EN.items():
        base_value = attributes[attr_pt.capitalize()]
        modifier = racial_bonus.get(attr_en, 0)
        final_attributes[attr_en] = base_value + modifier

    # 6. Calcular HP e MP
    hp, mp = calculate_hp_mp(final_attributes["constitution"], final_attributes["intelligence"], char_class)

    # 7. Criar canal privado
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False), # Ninguém vê
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True), # Jogador vê e escreve
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True) # Bot vê e escreve
    }
    try:
        private_channel = await ctx.guild.create_text_channel(
            f'rpg-{char_name.lower().replace(" ", "-")}',
            category=None, # Pode definir uma categoria específica se quiser
            overwrites=overwrites,
            reason=f"Canal RPG para {char_name}"
        )
        channel_id = private_channel.id
        await private_channel.send(f"Bem-vindo(a) ao seu canal de aventura, {ctx.author.mention}! "
                                   "Aqui você poderá interagir com o bot e o mestre em particular.")
    except discord.Forbidden:
        await ctx.author.send("Não consegui criar seu canal privado. Verifique as permissões do bot no servidor.")
        channel_id = None # Se não conseguir criar, não armazena o ID

    # 8. Salvar personagem no DB
    success = database.create_character(
        user_id, guild_id, channel_id, char_name, char_race, char_class,
        final_attributes["strength"], final_attributes["constitution"], final_attributes["dexterity"],
        final_attributes["intelligence"], final_attributes["wisdom"], final_attributes["charisma"],
        hp, mp
    )

    if success:
        # Adiciona poções iniciais
        potion_item = database.get_item_by_name("Poção de Cura Pequena")
        if potion_item:
            database.add_item_to_inventory(user_id, potion_item['id'], 20)
            await ctx.send("Você recebeu **20x Poção de Cura Pequena** para iniciar sua jornada!")
        else:
            print("Aviso: 'Poção de Cura Pequena' não encontrada no banco de dados. Poções iniciais não foram adicionadas.")

        await ctx.send(f"Parabéns, {char_name} foi criado(a) com sucesso! "
                              f"Seu HP inicial é {hp} e MP é {mp}.")
        if channel_id:
            await ctx.send(f"Seu canal de aventura é: {private_channel.mention}")

        # 9. Aviso no chat #geral
        general_channel = await get_general_channel(ctx.guild)
        if general_channel:
            await general_channel.send(f"🎉 Um novo aventureiro(a) se juntou à jornada! "
                                       f"**{char_name}** ({char_race} {char_class}) embarca em sua aventura!")
        else:
            print(f"Canal '{GENERAL_CHANNEL_NAME}' não encontrado no servidor.")
            # This message is sent to the user, not the general channel.
            # It's a fallback in case the general channel is not found.
            await ctx.send(f"Não consegui encontrar o canal '{GENERAL_CHANNEL_NAME}' para fazer o anúncio.")
    else:
        await ctx.send("Ocorreu um erro ao salvar seu personagem. Por favor, tente novamente.")

@bot.command(name="char", aliases=["ficha"], help="Exibe a ficha do seu personagem ou atualiza a imagem.")
async def character_sheet(ctx, subcommand=None, *args):
    user_id = ctx.author.id
    character = database.get_character(user_id)

    if not character:
        await ctx.send("Você não tem um personagem criado. Use `!newchar` para começar sua aventura!")
        return

    if subcommand == "img":
        if not args:
            await ctx.send("Por favor, forneça a URL da imagem. Ex: `!char img <url-da-imagem>`")
            return
        image_url = args[0]
        if database.update_character_image(user_id, image_url):
            await ctx.send(f"Imagem do personagem atualizada com sucesso para: {image_url}")
        else:
            await ctx.send("Não foi possível atualizar a imagem do personagem.")
        return

    if subcommand == "detail":
        # Exibir ficha detalhada
        equipped_items, bonuses = database.get_equipped_items(user_id)

        embed = discord.Embed(
            title=f"Ficha Detalhada: {character['name']}",
            description="Análise completa dos seus atributos e bônus.",
            color=discord.Color.dark_blue()
        )

        # Atributos
        racial_mods = RACE_MODIFIERS.get(character['race'], {})
        for attr_en, attr_pt in ATTRIBUTE_MAP_EN_PT.items():
            base_value = character[attr_en] - racial_mods.get(attr_en, 0)
            racial_bonus = racial_mods.get(attr_en, 0)
            item_bonus = bonuses['attack'] if attr_en == 'strength' else 0 # Simplificação, só força ganha bônus de item por enquanto
            total_value = character[attr_en] + item_bonus
            
            details = f"`{total_value} = {base_value} (Base) + {racial_bonus} (Raça) + {item_bonus} (Itens)`"
            embed.add_field(name=f"**{attr_pt}**", value=details, inline=False)

        # HP e MP
        embed.add_field(name="\u200b", value="--- **Recursos** ---", inline=False)
        embed.add_field(name="❤️ HP Máximo", value=f"`{character['max_hp']}` (Baseado em Constituição e Nível)", inline=False)
        embed.add_field(name="💙 MP Máximo", value=f"`{character['max_mp']}` (Baseado em Inteligência e Nível)", inline=False)

        # Ataque e Defesa
        embed.add_field(name="\u200b", value="--- **Combate** ---", inline=False)
        class_info = CLASS_DETAILS.get(character['class'], {})
        key_attr_name = class_info.get('key_attribute', 'strength')
        key_attr_value = character[key_attr_name]
        attack_bonus_items = bonuses['attack']
        total_attack = key_attr_value + attack_bonus_items
        embed.add_field(name="⚔️ Ataque Total", value=f"`{total_attack} = {key_attr_value} ({ATTRIBUTE_MAP_EN_PT[key_attr_name]}) + {attack_bonus_items} (Itens)`", inline=False)
        
        embed.add_field(name="🛡️ Defesa Total", value=f"`{bonuses['defense']}` (Vinda de Itens)", inline=False)

        await ctx.send(embed=embed)
        return

    # Exibir ficha do personagem
    equipped_items, bonuses = database.get_equipped_items(user_id)
    total_strength = character['strength'] + bonuses['attack']
    total_defense = character['constitution'] + bonuses['defense'] # Simplificado

    embed = discord.Embed(
        title=f"Ficha de Personagem: {character['name']}",
        description=f"**Raça:** {character['race']} | **Classe:** {character['class']}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Level", value=character['level'], inline=True)
    embed.add_field(name="XP", value=f"{character['experience']} / {character['level'] * XP_PER_LEVEL_MULTIPLIER}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=False) # Quebra de linha
    embed.add_field(name="💰 Gold", value=character['gold'], inline=True)

    embed.add_field(name="HP", value=f"{character['hp']}/{character['max_hp']}", inline=True)
    embed.add_field(name="MP", value=f"{character['mp']}/{character['max_mp']}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=False) # Quebra de linha

    embed.add_field(name="Força", value=f"{total_strength} ({character['strength']}+{bonuses['attack']})", inline=True)
    embed.add_field(name="Constituição", value=character['constitution'], inline=True) # Defesa é separada
    embed.add_field(name="Destreza", value=character['dexterity'], inline=True)
    embed.add_field(name="Inteligência", value=character['intelligence'], inline=True)
    embed.add_field(name="Sabedoria", value=character['wisdom'], inline=True)
    embed.add_field(name="Carisma", value=character['charisma'], inline=True)

    # Equipamentos
    embed.add_field(name="\u200b", value="--- **Equipamento** ---", inline=False)
    embed.add_field(name="Mão Direita", value=equipped_items.get('right_hand_id', 'Vazio'), inline=True)
    embed.add_field(name="Mão Esquerda", value=equipped_items.get('left_hand_id', 'Vazio'), inline=True)
    embed.add_field(name="Capacete", value=equipped_items.get('helmet_id', 'Vazio'), inline=True)
    embed.add_field(name="Peitoral", value=equipped_items.get('chest_id', 'Vazio'), inline=True)
    embed.add_field(name="Pernas", value=equipped_items.get('legs_id', 'Vazio'), inline=True)
    embed.add_field(name="Anel", value=equipped_items.get('ring_id', 'Vazio'), inline=True)

    if character['image_url']:
        # Adiciona um timestamp à URL para evitar o cache do Discord
        embed.set_thumbnail(url=f"{character['image_url']}?t={int(asyncio.get_event_loop().time())}")
    else:
        embed.set_thumbnail(url=character['image_url'])

    embed.set_footer(text=f"ID do Jogador: {character['user_id']}")
    await ctx.send(embed=embed)

@bot.command(name="hunt", aliases=["battle", "explorar"], help="Inicia uma batalha com um inimigo aleatório.")
async def hunt(ctx, *, enemy_name: str = None):
    user_id = ctx.author.id
    player = database.get_character(user_id)

    if not player:
        await ctx.send("Você precisa de um personagem para caçar! Use `!newchar`.")
        return

    # Garante que a batalha ocorra no canal privado do jogador
    if ctx.channel.id != player['channel_id']:
        private_channel = bot.get_channel(player['channel_id'])
        await ctx.send(f"As batalhas acontecem no seu canal privado! Vá para {private_channel.mention} e use o comando `!hunt` lá.")
        return

    # --- Lógica de Inimigo Elite ---
    is_elite = random.random() < 0.1 # 10% de chance de ser Elite
    elite_prefix = ""

    if enemy_name:
        enemy = database.get_enemy_by_name(enemy_name)
        if enemy and player['level'] <= enemy['max_level']:
            await ctx.send(f"Você ainda não superou o poder de **{enemy['name']}**. Para caçá-lo diretamente, seu nível deve ser maior que {enemy['max_level']}.")
            return
    else:
        enemy = database.get_random_enemy(player['level'])

    if not enemy:
        if enemy_name:
            await ctx.send(f"Inimigo '{enemy_name}' não encontrado.")
        else:
            await ctx.send("Nenhum inimigo encontrado para o seu nível. O mundo parece seguro... por enquanto.")
        return

    original_enemy_name = enemy['name'] # Salva o nome original para a quest

    if is_elite and not enemy_name: # Elites só aparecem em caçadas aleatórias
        elite_prefix = "⭐ **ELITE** "
        enemy['name'] = f"{elite_prefix}{enemy['name']}"
        enemy['hp'] = round(enemy['hp'] * 1.75)
        enemy['attack'] = round(enemy['attack'] * 1.75)
        enemy['defense'] = round(enemy['defense'] * 1.75)
        enemy['xp_reward'] = round(enemy['xp_reward'] * 2)
        enemy['gold_reward'] = round(enemy['gold_reward'] * 2)

    player_hp = player['hp']
    enemy_hp = enemy['hp']

    # Pega os bônus de equipamento
    _, player_bonuses = database.get_equipped_items(user_id)
    
    # --- Criação da Ficha de Versus ---
    versus_embed = discord.Embed(
        title=f"⚔️ BATALHA IMINENTE ⚔️",
        description=f"🌲 Você encontra um {enemy['name']}! Prepare-se! 🌲",
        color=discord.Color.red()
    )
    # Stats do Jogador
    player_total_attack = player['strength'] + player_bonuses['attack']
    player_total_defense = player['constitution'] + player_bonuses['defense']
    versus_embed.add_field(name=f"__**{player['name']}**__ (Lvl {player['level']})", value=f"❤️ HP: {player_hp}\n⚔️ Atq: {player_total_attack}\n🛡️ Def: {player_total_defense}", inline=True)
    # Stats do Inimigo
    versus_embed.add_field(name=f"__**{enemy['name'].replace('⭐ **ELITE** ', '')}**__ (Lvl {enemy['min_level']}-{enemy['max_level']})", value=f"❤️ HP: {enemy_hp}\n⚔️ Atq: {enemy['attack']}\n🛡️ Def: {enemy['defense']}", inline=True)
    if player.get('image_url'):
        versus_embed.set_author(name=player['name'], icon_url=player['image_url'])
    if enemy.get('image_url'):
        versus_embed.set_thumbnail(url=enemy['image_url'])
    
    await ctx.send(embed=versus_embed)

    # Loop de batalha
    player_buffs = {}
    enemy_debuffs = {}
    enemy_status_effects = {} # Para efeitos como veneno

    while player_hp > 0 and enemy_hp > 0:
        # Turno do Jogador
        embed = discord.Embed(title="Seu Turno!", description="Escolha sua ação: `atacar`, `defender`, `habilidade`, `usar item`, `fugir`", color=discord.Color.green())
        embed.add_field(name=f"{player['name']} HP", value=f"{player_hp}/{player['max_hp']}", inline=True)
        embed.add_field(name=f"{player['name']} MP", value=f"{player['mp']}/{player['max_mp']}", inline=True)
        embed.add_field(name=f"{enemy['name']} HP", value=f"{enemy_hp}/{enemy['hp']}", inline=True)
        await ctx.send(embed=embed)

        try:
            action_msg = await bot.wait_for(
                "message",
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["atacar", "defender", "habilidade", "skill", "usar item", "fugir"],
                timeout=30.0
            )
            action = action_msg.content.lower()
            if action == "skill": action = "habilidade" # Alias
        except asyncio.TimeoutError:
            await ctx.send("Você demorou demais para agir! O inimigo ataca!")
            action = "passar" # Ação padrão se o tempo esgotar


        player_defending = False
        if action == "atacar":
            # Dano = (Força do Atacante * Modificador Aleatório) - Defesa do Alvo
            special_bonuses = player_bonuses.get("special", {})
            
            # Usa o atributo chave da classe para ataques físicos
            class_info = CLASS_DETAILS.get(player['class'])
            base_attack_stat_name = 'strength' # Padrão
            if class_info and class_info['type'] == 'physical':
                base_attack_stat_name = class_info['key_attribute']

            base_attack_stat = player[base_attack_stat_name]
            player_total_attack = base_attack_stat + player_bonuses['attack']
            player_damage = max(0, round(player_total_attack * random.uniform(0.8, 1.2)) - enemy['defense'])
            enemy_hp -= player_damage
            await ctx.send(f"⚔️ Você ataca o {enemy['name']} e causa **{player_damage}** de dano!")

            # Lógica de Lifesteal
            lifesteal_percent = special_bonuses.get("LIFESTEAL_PERCENT")
            if lifesteal_percent and player_damage > 0:
                life_drained = round(player_damage * (lifesteal_percent / 100))
                player_hp = min(player['max_hp'], player_hp + life_drained)
                await ctx.send(f"🩸 Você drena **{life_drained}** de vida do inimigo! (HP: {player_hp})")
            
            # Lógica de Veneno ao atacar
            poison_chance = special_bonuses.get("POISON_ON_HIT")
            if poison_chance and random.random() < (poison_chance / 100):
                # O dano do veneno pode ser uma fração do ataque do jogador
                poison_damage = round((player['dexterity'] + player_bonuses['attack']) * 0.25) 
                # A duração vem do item
                poison_duration = player_bonuses.get("duration", {}).get("POISON_ON_HIT", 3)
                enemy_status_effects['poison'] = {'damage': poison_damage, 'duration': poison_duration}
                await ctx.send(f"🐍 Sua arma envenenou o {enemy['name']}!")
        elif action == "defender":
            player_defending = True
            await ctx.send("🛡️ Você se prepara para o próximo ataque, aumentando sua defesa!")
        elif action == "habilidade":
            skills = database.get_character_skills(player['class'], player['level'])
            if not skills:
                await ctx.send("Você ainda não aprendeu nenhuma habilidade! Você perde seu turno.")
                action = "passar"
            else:
                skill_list_str = "\n".join([f"`{idx+1}`: **{s['name']}** (Custo: {s['mp_cost']} MP) - {s['description']}" for idx, s in enumerate(skills)])
                await ctx.send(f"Qual habilidade você quer usar?\n{skill_list_str}\nDigite o número da habilidade ou `cancelar`.")

                try:
                    skill_choice_msg = await bot.wait_for(
                        "message",
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                        timeout=30.0
                    )
                    if skill_choice_msg.content.lower() == 'cancelar':
                        await ctx.send("Uso de habilidade cancelado. Você perde seu turno.")
                        action = "passar"
                    else:
                        choice_idx = int(skill_choice_msg.content) - 1
                        if 0 <= choice_idx < len(skills):
                            skill = skills[choice_idx]
                            if player['mp'] < skill['mp_cost']:
                                await ctx.send(f"Você não tem MP suficiente para usar **{skill['name']}**! Você perde seu turno.")
                                action = "passar"
                            else:
                                # Deduz MP e aplica o efeito
                                player['mp'] -= skill['mp_cost']
                                database.update_character_stats(user_id, {'mp': player['mp']})
                                await ctx.send(f"Você usou **{skill['name']}**!")

                                # Lógica de Efeitos
                                scaling_stat_value = player.get(skill['scaling_stat'], 0)
                                total_effect_value = round(skill['base_value'] + (scaling_stat_value * skill['scaling_factor']))

                                if skill['effect_type'] == 'DAMAGE':
                                    skill_damage = max(0, total_effect_value - enemy['defense'])
                                    enemy_hp -= skill_damage
                                    await ctx.send(f"✨ A habilidade causa **{skill_damage}** de dano ao {enemy['name']}!")
                                
                                elif skill['effect_type'] == 'DAMAGE_PIERCING':
                                    # Ignora metade da defesa do inimigo
                                    skill_damage = max(0, total_effect_value - (enemy['defense'] // 2))
                                    enemy_hp -= skill_damage
                                    await ctx.send(f"🎯 O ataque perfurante causa **{skill_damage}** de dano ao {enemy['name']}!")
                                
                                elif skill['effect_type'] == 'DAMAGE_AND_POISON':
                                    # Dano inicial
                                    skill_damage = max(0, total_effect_value - enemy['defense'])
                                    enemy_hp -= skill_damage
                                    await ctx.send(f"✨ A habilidade causa **{skill_damage}** de dano direto...")
                                    # Aplica veneno
                                    enemy_status_effects['poison'] = {'damage': round(total_effect_value * 0.5), 'duration': skill['effect_duration']}
                                    await ctx.send(f"🐍 ...e envenena o {enemy['name']} por {skill['effect_duration']} turnos!")

                                elif skill['effect_type'] == 'HEAL':
                                    player_hp = min(player['max_hp'], player_hp + total_effect_value)
                                    await ctx.send(f"💖 Você se cura em **{total_effect_value}** de HP! HP atual: {player_hp}")

                                elif skill['effect_type'] == 'BUFF_ATTACK':
                                    player_buffs['attack'] = total_effect_value
                                    await ctx.send(f"💪 Sua fúria aumenta seu ataque em **{total_effect_value}** no próximo turno!")

                                elif skill['effect_type'] == 'BUFF_DEFENSE':
                                    player_buffs['defense'] = total_effect_value
                                    await ctx.send(f"🛡️ Uma barreira mágica aumenta sua defesa em **{total_effect_value}** no próximo turno!")

                                elif skill['effect_type'] == 'DEBUFF_DEFENSE':
                                    enemy_debuffs['defense'] = total_effect_value
                                    await ctx.send(f"📉 A defesa do inimigo foi reduzida em **{total_effect_value}** no próximo turno!")

                        else:
                            await ctx.send("Escolha inválida. Você perde seu turno.")
                            action = "passar"
                except (asyncio.TimeoutError, ValueError):
                    await ctx.send("Tempo esgotado ou escolha inválida. Você perde seu turno.")
                    action = "passar"

        elif action == "usar item":
            inventory = database.get_inventory(user_id)
            consumables = [item for item in inventory if item[4] == 'potion'] # item[4] é item_type

            if not consumables:
                await ctx.send("Você não tem itens consumíveis para usar! Você perde seu turno.")
                action = "passar" # Pula o turno
            else:
                item_list_str = "\n".join([f"`{idx+1}`: {item[2]}" for idx, item in enumerate(consumables)])
                await ctx.send(f"Qual item você quer usar?\n{item_list_str}\nDigite o número do item ou `cancelar`.")
                
                try:
                    item_choice_msg = await bot.wait_for(
                        "message",
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                        timeout=30.0
                    )
                    if item_choice_msg.content.lower() == 'cancelar':
                        await ctx.send("Uso de item cancelado. Você perde seu turno.")
                        action = "passar"
                    else:
                        choice_idx = int(item_choice_msg.content) - 1
                        if 0 <= choice_idx < len(consumables):
                            item_to_use = consumables[choice_idx]
                            item_id, _, item_name, _, _, effect_type, effect_value, _ = item_to_use

                            if effect_type == 'HEAL_HP':
                                player_hp = min(player['max_hp'], player_hp + effect_value)
                                await ctx.send(f"Você usou **{item_name}** e recuperou **{effect_value}** de HP! HP atual: {player_hp}")
                                database.remove_item_from_inventory(user_id, item_id, 1)
                            else:
                                await ctx.send(f"O item **{item_name}** não pode ser usado em batalha. Você perde seu turno.")
                                action = "passar"
                        else:
                            await ctx.send("Escolha inválida. Você perde seu turno.")
                            action = "passar"
                except (asyncio.TimeoutError, ValueError):
                    await ctx.send("Tempo esgotado ou escolha inválida. Você perde seu turno.")
                    action = "passar"
            
            if action == "passar": # Se o uso do item falhou, o inimigo ainda ataca
                pass
        elif action == "fugir":
            # Chance de fuga baseada na Destreza
            flee_chance = player['dexterity'] / 20 # Ex: 15 DEX = 75% de chance
            if random.random() < flee_chance:
                await ctx.send("🏃 Você conseguiu fugir da batalha!")
                return # Encerra a função de caça
            else:
                await ctx.send("A tentativa de fuga falhou! Você perde seu turno.")

        if enemy_hp <= 0:
            break # Inimigo derrotado, sai do loop

        # Processar efeitos de status no inimigo (ex: veneno)
        if 'poison' in enemy_status_effects:
            poison = enemy_status_effects['poison']
            poison_damage = poison['damage']
            enemy_hp -= poison_damage
            poison['duration'] -= 1
            await ctx.send(f"🤢 O {enemy['name']} sofre **{poison_damage}** de dano de veneno. (Duração: {poison['duration']} turnos)")
            if poison['duration'] <= 0:
                del enemy_status_effects['poison']
                await ctx.send(f"O veneno no {enemy['name']} se dissipou.")
        
        if enemy_hp <= 0:
            break # Inimigo derrotado pelo veneno


        # Turno do Inimigo
        await asyncio.sleep(1) # Pausa para dar ritmo
        
        # Aplica buffs e debuffs
        final_player_attack = player_bonuses['attack'] + player_buffs.get('attack', 0)
        final_player_defense = player_bonuses['defense'] + player_buffs.get('defense', 0)
        final_enemy_defense = enemy['defense'] - enemy_debuffs.get('defense', 0)

        player_total_defense = final_player_defense + (player['dexterity'] // 4) # Bônus de equipamento + destreza
        if player_defending:
            player_total_defense += player['dexterity'] // 2 # Bônus maior ao defender

        enemy_damage = max(0, round(enemy['attack'] * random.uniform(0.8, 1.2)) - player_total_defense) # Inimigo não se beneficia de buffs de ataque por enquanto
        player_hp -= enemy_damage
        await ctx.send(f"💥 O {enemy['name']} ataca e causa **{enemy_damage}** de dano em você!")

        # Resetar buffs/debuffs de um turno no final do turno completo
        player_buffs = {}
        enemy_debuffs = {}

    # Fim da batalha
    await asyncio.sleep(1)
    if player_hp <= 0:
        await ctx.send(f"☠️ Você foi derrotado pelo {enemy['name']}... Sua jornada termina aqui (por enquanto).")
        # Penalidade: restaurar HP para 1, sem ganhar XP.
        database.update_character_stats(user_id, {"hp": 1})
    else:
        await ctx.send(f"🏆 **VITÓRIA!** Você derrotou o {enemy['name']}! 🏆")

        # Ganho de XP
        new_experience = player['experience'] + enemy['xp_reward']
        new_gold = player['gold'] + enemy['gold_reward']
        xp_to_next_level = player['level'] * XP_PER_LEVEL_MULTIPLIER

        # Aplica bônus de anéis
        special_bonuses = player_bonuses.get("special", {})

        await ctx.send(f"Você ganhou **{enemy['xp_reward']}** de experiência e **{enemy['gold_reward']}** moedas de ouro!")

        updates = {"experience": new_experience, "hp": player_hp, "gold": new_gold} # Salva o HP atual e ouro

        # Lógica de Level Up
        if new_experience >= xp_to_next_level:
            updates['level'] = player['level'] + 1
            updates['experience'] = new_experience - xp_to_next_level
            
            await ctx.send(f"🎉 **LEVEL UP!** Você alcançou o nível **{updates['level']}**! 🎉")

            attr_map = {"força": "strength", "constituição": "constitution", "destreza": "dexterity", "inteligência": "intelligence", "sabedoria": "wisdom", "carisma": "charisma"}
            
            if updates['level'] % 5 == 0:
                # A cada 5 níveis, o jogador distribui 4 pontos
                points_to_distribute = 4
                await ctx.send(f"Você tem **{points_to_distribute}** pontos para distribuir entre seus atributos: `força`, `constituição`, `destreza`, `inteligência`, `sabedoria`, `carisma`.")
                
                for i in range(points_to_distribute):
                    await ctx.send(f"Ponto {i+1}/{points_to_distribute}: Qual atributo você quer aumentar?")
                    try:
                        attr_choice_msg = await bot.wait_for(
                            "message",
                            check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in attr_map.keys(),
                            timeout=60.0
                        )
                        attr_to_increase = attr_choice_msg.content.lower()
                        db_attr = attr_map[attr_to_increase]
                        
                        # Aumenta o atributo no dicionário de updates
                        current_value = updates.get(db_attr, player[db_attr])
                        updates[db_attr] = current_value + 1
                        await ctx.send(f"Seu atributo **{attr_to_increase.capitalize()}** aumentou para **{updates[db_attr]}**!")

                    except asyncio.TimeoutError:
                        await ctx.send("Tempo esgotado. O ponto de atributo foi perdido.")

            # Aumenta HP/MP máximo no level up
            # Usa 'updates.get' para pegar o valor atualizado de constituição, se foi alterado
            new_constitution = updates.get('constitution', player['constitution'])
            new_intelligence = updates.get('intelligence', player['intelligence'])
            updates['max_hp'] = player['max_hp'] + 10 + (new_constitution // 4)
            updates['max_mp'] = player['max_mp'] + 5 + (new_intelligence // 4)
            updates['hp'] = updates['max_hp'] # Restaura HP e MP no level up
            updates['mp'] = updates['max_mp']

        database.update_character_stats(user_id, updates)

        # Lógica de Loot
        loot_rolls = 2 if is_elite else 1 # 2 rolagens de loot para Elites
        loot_chance = 0.3 # 30% de chance por rolagem
        
        for _ in range(loot_rolls):
            if random.random() > loot_chance:
                continue

            loot_item = database.get_random_loot(player['level'])
            if loot_item:
                database.add_item_to_inventory(user_id, loot_item['id'])
                await ctx.send(f"🎁 Você encontrou um item: **{loot_item['name']}**! Ele foi adicionado ao seu inventário (`!inventory`).")

@bot.command(name="inventory", aliases=["inv"], help="Mostra os itens no seu inventário.")
async def inventory(ctx):
    user_id = ctx.author.id
    character = database.get_character(user_id)
    if not character:
        await ctx.send("Você não tem um personagem. Use `!newchar` para criar um.")
        return

    items = database.get_inventory(user_id)

    if not items:
        await ctx.send("Seu inventário está vazio.")
        return

    embed = discord.Embed(
        title=f"Inventário de {character['name']}",
        color=discord.Color.dark_gold()
    )

    for item in items:
        inv_id, item_id, quantity, name, description, item_type, _, _, _, enhancement = item
        display_name = f"ID: `{inv_id}` | {name} +{enhancement}" if enhancement > 0 else f"ID: `{inv_id}` | {name}"
        embed.add_field(name=f"{display_name} (x{quantity})", value=description, inline=False)

    await ctx.send(embed=embed)

@bot.command(name="use", help="Usa um item consumível do seu inventário.")
async def use_item(ctx, *args):
    user_id = ctx.author.id
    character = database.get_character(user_id)
    if not character:
        await ctx.send("Você não tem um personagem.")
        return

    if not args:
        await ctx.send("Uso: `!use [quantidade] <nome do item>`")
        return

    quantity = 1
    if args[0].isdigit():
        quantity = int(args[0])
        item_name = " ".join(args[1:])
    else:
        item_name = " ".join(args)

    if quantity <= 0:
        await ctx.send("A quantidade deve ser um número positivo.")
        return

    inventory = database.get_inventory(user_id)
    item_to_use = None
    for item in inventory:
        # item: (inv_id, item_id, quantity, name, ...)
        if item_name.lower() in item[3].lower():
            item_to_use = item
            break

    if not item_to_use:
        await ctx.send(f"Item '{item_name}' não encontrado no seu inventário.")
        return
    
    inv_id, item_id, inv_quantity, name, _, item_type, effect_type, effect_value, _, _ = item_to_use

    if inv_quantity < quantity:
        await ctx.send(f"Você não tem itens suficientes. Você possui apenas {inv_quantity}x **{name}**.")
        return

    if item_type != 'potion':
        await ctx.send(f"**{name}** não é um item consumível.")
        return

    updates = {}
    items_used = 0
    total_effect = 0

    if effect_type == 'HEAL_HP':
        if character['hp'] >= character['max_hp']:
            await ctx.send("Sua vida já está cheia!")
            return
        
        for i in range(quantity):
            if character['hp'] >= character['max_hp']:
                break
            character['hp'] = min(character['max_hp'], character['hp'] + effect_value)
            items_used += 1
        
        updates['hp'] = character['hp']
        database.remove_item_from_inventory(user_id, item_id, items_used)
        database.update_character_stats(user_id, updates)
        await ctx.send(f"Você usou {items_used}x **{name}**. HP atual: {character['hp']}/{character['max_hp']}")

    elif effect_type == 'HEAL_MP':
        if character['mp'] >= character['max_mp']:
            await ctx.send("Sua mana já está cheia!")
            return

        for i in range(quantity):
            if character['mp'] >= character['max_mp']:
                break
            character['mp'] = min(character['max_mp'], character['mp'] + effect_value)
            items_used += 1

        updates['mp'] = character['mp']
        database.remove_item_from_inventory(user_id, item_id, items_used)
        database.update_character_stats(user_id, updates)
        await ctx.send(f"Você usou {items_used}x **{name}**. MP atual: {character['mp']}/{character['max_mp']}")

    elif effect_type == 'INCREASE_MAX_HP':
        total_effect = effect_value * quantity
        updates['max_hp'] = character['max_hp'] + total_effect
        database.remove_item_from_inventory(user_id, item_id, quantity)
        database.update_character_stats(user_id, updates)
        await ctx.send(f"Você usou {quantity}x **{name}** e seu HP máximo aumentou em **{total_effect}**! Novo HP Máximo: **{updates['max_hp']}**!")

    elif effect_type == 'GAIN_XP':
        total_effect = effect_value * quantity
        updates['experience'] = character['experience'] + total_effect
        database.remove_item_from_inventory(user_id, item_id, quantity)
        database.update_character_stats(user_id, updates)
        await ctx.send(f"Você usou {quantity}x **{name}** e ganhou **{total_effect}** de experiência!")

    elif effect_type == 'INCREASE_DEXTERITY':
        total_effect = effect_value * quantity
        updates['dexterity'] = character['dexterity'] + total_effect
        database.remove_item_from_inventory(user_id, item_id, quantity)
        database.update_character_stats(user_id, updates)
        await ctx.send(f"Você usou {quantity}x **{name}** e sua Destreza aumentou permanentemente em **{total_effect}**! Nova Destreza: **{updates['dexterity']}**!")

    else:
        await ctx.send(f"O item **{name}** não tem um efeito utilizável no momento.")


class ShopView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.current_page = 1
        self.current_category = "all"
        self.total_pages = 0
        self.update_options()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Você não pode controlar esta loja.", ephemeral=True)
            return False
        return True

    def update_options(self):
        # Atualiza o estado dos botões de paginação
        self.children[0].disabled = self.current_page == 1
        self.children[1].disabled = self.current_page == self.total_pages

    async def format_shop_embed(self):
        item_count = database.count_shop_items(self.current_category)
        self.total_pages = (item_count - 1) // 5 + 1
        if self.total_pages == 0: self.total_pages = 1

        items = database.get_shop_items(self.current_category, self.current_page, per_page=5)
        
        embed = discord.Embed(title=f"🛒 Loja - Categoria: {self.current_category.capitalize()} 🛒", color=discord.Color.gold())
        embed.set_footer(text=f"Página {self.current_page} de {self.total_pages}")

        if not items:
            embed.description = "Nenhum item encontrado nesta categoria."
        else:
            for item in items:
                embed.add_field(name=f"{item['name']} - {item['value']} Ouro", value=item['description'], inline=False)
        
        self.update_options()
        return embed

    @discord.ui.button(label="◀ Anterior", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 1:
            self.current_page -= 1
        embed = await self.format_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Próxima ▶", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages:
            self.current_page += 1
        embed = await self.format_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="Escolha uma categoria...",
        options=[
            discord.SelectOption(label="Todas", value="all"),
            discord.SelectOption(label="Armas", value="weapon"),
            discord.SelectOption(label="Armaduras", value="armor"),
            discord.SelectOption(label="Poções", value="potion"),
            discord.SelectOption(label="Materiais", value="material"),
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.current_category = select.values[0]
        self.current_page = 1
        embed = await self.format_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

@bot.group(name="shop", help="Abre a loja para comprar ou vender itens.", invoke_without_command=True)
async def shop(ctx):
    user_id = ctx.author.id
    character = database.get_character(user_id)
    if not character:
        await ctx.send("Você precisa de um personagem para acessar a loja.")
        return

    view = ShopView(user_id)
    embed = await view.format_shop_embed()
    await ctx.send(embed=embed, view=view)

@shop.command(name="buy", help="Compra um item da loja.")
async def shop_buy(ctx, *args):
    user_id = ctx.author.id
    character = database.get_character(user_id)
    if not character:
        await ctx.send("Você precisa de um personagem para comprar itens.")
        return

    if not args:
        await ctx.send("Uso: `!shop buy [quantidade] <nome do item>`")
        return

    quantity = 1
    if args[0].isdigit():
        quantity = int(args[0])
        item_name = " ".join(args[1:])
    else:
        item_name = " ".join(args)
    
    item_to_buy = database.get_item_by_name(item_name)
    if not item_to_buy or item_to_buy['value'] <= 0:
        await ctx.send(f"O item '{item_name}' não está à venda.")
        return

    total_cost = item_to_buy['value'] * quantity
    if character['gold'] < total_cost:
        await ctx.send(f"Você não tem ouro suficiente! {quantity}x **{item_to_buy['name']}** custa {total_cost} de ouro. Você tem {character['gold']}.")
        return

    database.update_character_stats(user_id, {"gold": character['gold'] - total_cost})
    database.add_item_to_inventory(user_id, item_to_buy['id'], quantity)
    await ctx.send(f"Você comprou {quantity}x **{item_to_buy['name']}** por {total_cost} de ouro!")

@shop.command(name="sell", help="Vende um item do seu inventário.")
async def shop_sell(ctx, *args):
    user_id = ctx.author.id
    character = database.get_character(user_id)
    if not character:
        await ctx.send("Você precisa de um personagem para vender itens.")
        return

    if not args:
        await ctx.send("Uso: `!shop sell [quantidade] <nome do item>`")
        return

    quantity = 1
    if args[0].isdigit():
        quantity = int(args[0])
        item_name = " ".join(args[1:])
    else:
        item_name = " ".join(args)

    inventory = database.get_inventory(user_id)
    item_to_sell = None
    inv_item_data = None
    for item_data in inventory:
        # item_data[3] é o nome do item
        if item_name.lower() in item_data[3].lower():
            item_to_sell = database.get_item_by_name(item_data[3])
            inv_item_data = item_data
            break
    
    if not item_to_sell:
        await ctx.send(f"Você não possui o item '{item_name}' para vender.")
        return

    # inv_item_data: (inv_id, item_id, quantity, name, ..., enhancement_level)
    inv_quantity = inv_item_data[2] 
    enhancement_level = inv_item_data[9]

    if inv_quantity < quantity:
        await ctx.send(f"Você não tem itens suficientes para vender. Você possui apenas {inv_quantity}x **{item_to_sell['name']}**.")
        return

    unit_sell_price = round(item_to_sell['value'] * 0.7) # Vende por 70% do valor
    # Preço de venda aumenta em 175% do valor BASE por nível de aprimoramento
    unit_sell_price += round(item_to_sell['value'] * 1.75 * enhancement_level)

    if unit_sell_price <= 0:
        await ctx.send(f"O item **{item_to_sell['name']}** não tem valor de venda.")
        return

    total_gain = unit_sell_price * quantity

    if database.remove_item_from_inventory(user_id, item_to_sell['id'], quantity):
        database.update_character_stats(user_id, {"gold": character['gold'] + total_gain})
        await ctx.send(f"Você vendeu {quantity}x **{item_to_sell['name']}** por {total_gain} de ouro!")
    else:
        await ctx.send("Erro ao vender o item.") # Não deveria acontecer se a lógica estiver correta

class MarketView(discord.ui.View):
    def __init__(self, author_id, search_term=None):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.current_page = 1
        self.search_term = search_term
        self.total_pages = 0

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Permite que qualquer um navegue, mas apenas o autor original pode fechar (se implementado)
        return True

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 1
        self.children[1].disabled = self.current_page >= self.total_pages

    async def format_market_embed(self):
        item_count = database.count_market_listings(self.search_term)
        self.total_pages = (item_count - 1) // 10 + 1
        if self.total_pages == 0: self.total_pages = 1

        listings = database.get_market_listings(self.current_page, 10, self.search_term)
        
        title = "🛒 Mercado de Jogadores 🛒"
        if self.search_term:
            title += f" - Buscando por: '{self.search_term}'"

        embed = discord.Embed(title=title, color=discord.Color.dark_teal())
        embed.set_footer(text=f"Página {self.current_page} de {self.total_pages}")

        if not listings:
            embed.description = "Nenhum item encontrado no mercado."
        else:
            description = "Use `!market buy <ID>` para comprar.\n\n"
            for listing in listings:
                listing_id, quantity, price, enhancement, item_name, seller_name = listing
                display_name = f"{item_name} +{enhancement}" if enhancement > 0 else item_name
                description += f"**ID:** `{listing_id}` | **Item:** {display_name} (x{quantity})\n"
                description += f"**Preço:** {price} Ouro/un. | **Vendedor:** {seller_name}\n"
                description += "------------------------------------\n"
            embed.description = description
        
        self.update_buttons()
        return embed

    @discord.ui.button(label="◀ Anterior", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 1:
            self.current_page -= 1
        embed = await self.format_market_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Próxima ▶", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages:
            self.current_page += 1
        embed = await self.format_market_embed()
        await interaction.response.edit_message(embed=embed, view=self)

@bot.group(name="market", aliases=["mercado"], help="Acessa o mercado de jogadores.", invoke_without_command=True)
async def market(ctx):
    view = MarketView(ctx.author.id)
    embed = await view.format_market_embed()
    await ctx.send(embed=embed, view=view)

@market.command(name="sell", help="Anuncia um item no mercado. Uso: !market sell <preço> [quantidade] <nome do item>")
async def market_sell(ctx, price: int, *args):
    user_id = ctx.author.id
    if not database.get_character(user_id):
        await ctx.send("Você precisa de um personagem para vender itens.")
        return

    if not args:
        await ctx.send("Uso: `!market sell <preço> [quantidade] <nome do item>`")
        return

    quantity = 1
    if args[0].isdigit():
        quantity = int(args[0])
        item_name = " ".join(args[1:])
    else:
        item_name = " ".join(args)

    # Encontra o item no inventário
    inventory = database.get_inventory(user_id)
    item_to_sell_data = next((item for item in inventory if item_name.lower() in item[2].lower()), None)

    if not item_to_sell_data:
        await ctx.send(f"Você não possui o item '{item_name}'.")
        return

    item_id, inv_quantity, name, _, _, _, _, _, enhancement_level = item_to_sell_data

    if inv_quantity < quantity:
        await ctx.send(f"Você tem apenas {inv_quantity}x de {name} para vender.")
        return

    # Remove o item do inventário do vendedor
    database.remove_item_from_inventory(user_id, item_id, quantity)
    # Cria o anúncio no mercado
    listing_id = database.create_market_listing(user_id, item_id, quantity, price, enhancement_level)

    display_name = f"{name} +{enhancement_level}" if enhancement_level > 0 else name
    await ctx.send(f"✅ Você anunciou **{quantity}x {display_name}** no mercado por **{price}** ouro cada. (ID do Anúncio: `{listing_id}`)")

@market.command(name="buy", help="Compra um item do mercado. Uso: !market buy <ID do anúncio> [quantidade]")
async def market_buy(ctx, listing_id: int, quantity: int = 1):
    user_id = ctx.author.id
    buyer = database.get_character(user_id)
    if not buyer:
        await ctx.send("Você precisa de um personagem para comprar itens.")
        return

    listing = database.get_market_listing_by_id(listing_id)
    if not listing:
        await ctx.send("Anúncio não encontrado.")
        return

    if listing['seller_id'] == user_id:
        await ctx.send("Você não pode comprar seus próprios itens.")
        return

    if quantity > listing['quantity']:
        await ctx.send(f"Este anúncio tem apenas {listing['quantity']} unidade(s) disponível(is).")
        return

    total_cost = listing['price'] * quantity
    if buyer['gold'] < total_cost:
        await ctx.send(f"Você não tem ouro suficiente. Custo total: {total_cost} ouro.")
        return

    # Transação
    # Paga o vendedor
    seller = database.get_character(listing['seller_id'])
    database.update_character_stats(listing['seller_id'], {'gold': seller['gold'] + total_cost})
    # Deduz do comprador
    database.update_character_stats(user_id, {'gold': buyer['gold'] - total_cost})
    # Adiciona item ao comprador
    database.add_item_to_inventory(user_id, listing['item_id'], quantity) # Aprimoramento precisa ser tratado
    # Atualiza o anúncio
    if quantity == listing['quantity']:
        database.remove_market_listing(listing_id)
    else:
        # Esta parte requer uma função de update no DB, por simplicidade vamos remover e recriar
        database.remove_market_listing(listing_id)
        database.create_market_listing(listing['seller_id'], listing['item_id'], listing['quantity'] - quantity, listing['price'], listing['enhancement_level'])

    item_info = database.get_item_by_id(listing['item_id'])
    await ctx.send(f"🛍️ Você comprou **{quantity}x {item_info['name']}** por **{total_cost}** ouro!")

@market.command(name="remove", help="Remove um de seus anúncios do mercado. Uso: !market remove <ID do anúncio>")
async def market_remove(ctx, listing_id: int):
    user_id = ctx.author.id
    listing = database.get_market_listing_by_id(listing_id)

    if not listing or listing['seller_id'] != user_id:
        await ctx.send("Anúncio não encontrado ou você não é o vendedor.")
        return

    # Devolve o item e remove o anúncio
    database.add_item_to_inventory(user_id, listing['item_id'], listing['quantity'])
    database.remove_market_listing(listing_id)

    item_info = database.get_item_by_id(listing['item_id'])
    await ctx.send(f"Anúncio de **{listing['quantity']}x {item_info['name']}** removido. O item voltou para seu inventário.")

@market.command(name="search", help="Pesquisa por um item no mercado. Uso: !market search <nome do item>")
async def market_search(ctx, *, item_name: str):
    view = MarketView(ctx.author.id, search_term=item_name)
    embed = await view.format_market_embed()
    await ctx.send(embed=embed, view=view)

@bot.command(name="enhance", aliases=["aprimorar"], help="Aprimora um equipamento.")
async def enhance(ctx, *, item_name: str):
    user_id = ctx.author.id
    if not database.get_character(user_id):
        await ctx.send("Você precisa de um personagem para aprimorar itens.")
        return

    # 1. Encontrar o item no inventário
    inventory = database.get_inventory(user_id)
    item_to_enhance_data = None
    for item_data in inventory:
        # item_data: (inv_id, item_id, quantity, name, ..., enhancement_level)
        if item_name.lower() in item_data[3].lower() and item_data[9] == 0: # Apenas aprimora itens +0
            item_to_enhance_data = item_data
            break
    
    if not item_to_enhance_data:
        await ctx.send(f"Item '{item_name}' não encontrado no seu inventário.")
        return

    inv_id, item_id, quantity, name, _, item_type, _, _, equip_slot, enhancement_level = item_to_enhance_data

    # 2. Verificar se o item é aprimorável
    if item_type not in ['weapon', 'armor']:
        await ctx.send(f"**{name}** não é um item aprimorável.")
        return

    # 3. Verificar nível máximo de aprimoramento
    if enhancement_level >= 13:
        await ctx.send(f"**{name} +{enhancement_level}** já está no nível máximo de aprimoramento.")
        return

    # 4. Verificar se tem itens suficientes (precisa de 2)
    if quantity < 2:
        await ctx.send(f"Você precisa de pelo menos 2x **{name} +{enhancement_level}** para tentar o aprimoramento.")
        return

    # 5. Verificar se tem a gema necessária
    if item_type == 'weapon':
        gem_name = "Gema de Arma"
    elif item_type == 'armor' and equip_slot == 'ring':
        gem_name = "Gema de Acessório"
    else: # Outras armaduras
        gem_name = "Gema de Armadura"

    gem_item = database.get_item_by_name(gem_name)
    if not gem_item:
        await ctx.send(f"Erro de sistema: {gem_name} não encontrada na base de dados.")
        return

    gem_in_inventory = next((item for item in inventory if item[0] == gem_item['id']), None)
    if not gem_in_inventory:
        await ctx.send(f"Você não possui a **{gem_name}** necessária para o aprimoramento.")
        return

    # 6. Processar o aprimoramento
    # Consome 2 itens base e 1 gema
    database.remove_item_from_inventory(user_id, item_id, 2, enhancement_level=0)
    database.remove_item_from_inventory(user_id, gem_item['id'], 1)

    # Adiciona o novo item aprimorado
    database.add_item_to_inventory(user_id, item_id, 1, enhancement_level + 1)

    new_name = f"{name} +{enhancement_level + 1}"
    await ctx.send(f"✨ **SUCESSO!** ✨\nVocê aprimorou seu equipamento e criou uma **{new_name}**!")


@bot.command(name="equip", help="Equipa um item do seu inventário.")
async def equip(ctx, *, item_name: str):
    user_id = ctx.author.id
    if not database.get_character(user_id):
        await ctx.send("Você precisa de um personagem para equipar itens.")
        return

    inventory = database.get_inventory(user_id)
    
    # Tenta encontrar pelo ID do inventário primeiro
    try:
        inv_id_to_equip = int(item_name)
        item_to_equip_data = next((item for item in inventory if item[0] == inv_id_to_equip), None)
    except ValueError:
        # Se não for um número, busca pelo nome
        item_to_equip_data = next((item for item in inventory if item_name.lower() in item[3].lower()), None)

    if not item_to_equip_data:
        await ctx.send(f"Item '{item_name}' não encontrado no seu inventário. Tente usar o ID do item (`!inv`).")
        return

    inventory_id, item_id, _, name, _, _, _, _, _, _ = item_to_equip_data
    item_details = database.get_item_by_id(item_id)

    if not item_details.get('equip_slot'):
        await ctx.send(f"O item **{name}** não é equipável.")
        return

    db_slot = item_details['equip_slot'] + "_id"
    
    if database.equip_item(user_id, inventory_id, db_slot):
        await ctx.send(f"Você equipou **{name}**.")
    else:
        await ctx.send("Ocorreu um erro ao equipar o item.")

@bot.command(name="unequip", help="Desequipa um item.")
async def unequip(ctx, *, slot_name: str):
    user_id = ctx.author.id
    if not database.get_character(user_id):
        await ctx.send("Você precisa de um personagem para desequipar itens.")
        return

    slot_map = {
        "capacete": "helmet_id", "peitoral": "chest_id", "pernas": "legs_id",
        "mão direita": "right_hand_id", "mao direita": "right_hand_id",
        "mão esquerda": "left_hand_id", "mao esquerda": "left_hand_id",
        "anel": "ring_id"
    }
    db_slot = slot_map.get(slot_name.lower())

    if not db_slot:
        await ctx.send(f"Slot '{slot_name}' inválido. Slots disponíveis: Capacete, Peitoral, Pernas, Mão Direita, Mão Esquerda, Anel.")
        return

    equipped_items, _ = database.get_equipped_items(user_id)
    item_name = equipped_items.get(db_slot)

    if not item_name or item_name == "Vazio":
        await ctx.send(f"Você não tem nenhum item equipado no slot de {slot_name}.")
        return

    if database.unequip_item(user_id, db_slot):
        await ctx.send(f"Você desequipou **{item_name}**. O item voltou para o seu inventário.")
    else:
        await ctx.send("Ocorreu um erro ao desequipar o item.")

@bot.command(name="skills", aliases=["habilidades"], help="Mostra as habilidades disponíveis para sua classe e nível.")
async def show_skills(ctx):
    user_id = ctx.author.id
    character = database.get_character(user_id)
    if not character:
        await ctx.send("Você não tem um personagem. Use `!newchar` para criar um.")
        return

    skills = database.get_character_skills(character['class'], character['level'])

    if not skills:
        await ctx.send("Você ainda não aprendeu nenhuma habilidade.")
        return

    embed = discord.Embed(
        title=f"Habilidades de {character['name']} ({character['class']})",
        description="Estas são as habilidades que você pode usar em batalha.",
        color=discord.Color.purple()
    )

    for skill in skills:
        # Calcula o poder atual da habilidade para exibição
        scaling_stat_value = character.get(skill['scaling_stat'], 0)
        total_effect_value = round(skill['base_value'] + (scaling_stat_value * skill['scaling_factor']))

        scaling_stat_pt = ATTRIBUTE_MAP_EN_PT.get(skill['scaling_stat'], "N/A")

        field_value = (
            f"**Custo:** {skill['mp_cost']} MP | **Poder:** {total_effect_value} (Escala com **{scaling_stat_pt}**)\n"
            f"*{skill['description']}*"
        )
        embed.add_field(name=f"**{skill['name']}** (Requer Nível {skill['min_level']})", value=field_value, inline=False)

    embed.set_footer(text="O poder das habilidades aumenta com seus atributos.")
    await ctx.send(embed=embed)

@bot.command(name="autohunt", aliases=["afk"], help="Inicia uma batalha automática para farm de XP e itens.")
async def autohunt(ctx, *, enemy_name: str = None):
    user_id = ctx.author.id
    player = database.get_character(user_id)

    if not player:
        await ctx.send("Você precisa de um personagem para caçar! Use `!newchar`.")
        return

    if ctx.channel.id != player['channel_id']:
        private_channel = bot.get_channel(player['channel_id'])
        await ctx.send(f"As batalhas acontecem no seu canal privado! Vá para {private_channel.mention} e use o comando `!autohunt` lá.")
        return

    # --- Lógica de Inimigo Elite ---
    is_elite = random.random() < 0.1 # 10% de chance de ser Elite
    elite_prefix = ""

    if enemy_name:
        enemy = database.get_enemy_by_name(enemy_name)
        if enemy and player['level'] <= enemy['max_level']:
            await ctx.send(f"Você ainda não superou o poder de **{enemy['name']}**. Para caçá-lo diretamente, seu nível deve ser maior que {enemy['max_level']}.")
            return
    else:
        enemy = database.get_random_enemy(player['level'])

    if not enemy:
        if enemy_name:
            await ctx.send(f"Inimigo '{enemy_name}' não encontrado.")
        else:
            await ctx.send("Nenhum inimigo encontrado para o seu nível. O mundo parece seguro... por enquanto.")
        return

    original_enemy_name = enemy['name'] # Salva o nome original para a quest

    if is_elite and not enemy_name: # Elites só aparecem em caçadas aleatórias
        elite_prefix = "⭐ **ELITE** "
        enemy['name'] = f"{elite_prefix}{enemy['name']}"
        enemy['hp'] = round(enemy['hp'] * 1.75)
        enemy['attack'] = round(enemy['attack'] * 1.75)
        enemy['defense'] = round(enemy['defense'] * 1.75)
        enemy['xp_reward'] = round(enemy['xp_reward'] * 2)
        enemy['gold_reward'] = round(enemy['gold_reward'] * 2)

    player_hp = player['hp']
    enemy_hp = enemy['hp']
    _, player_bonuses = database.get_equipped_items(user_id)

    # --- Criação da Ficha de Versus ---
    versus_embed = discord.Embed(
        title=f"⚔️ CAÇADA AUTOMÁTICA ⚔️",
        description=f"🌲 Iniciando caçada contra um {enemy['name']}! 🌲",
        color=discord.Color.dark_orange()
    )
    # Stats do Jogador
    player_total_attack = player['strength'] + player_bonuses['attack']
    player_total_defense = player['constitution'] + player_bonuses['defense']
    versus_embed.add_field(name=f"__**{player['name']}**__ (Lvl {player['level']})", value=f"❤️ HP: {player_hp}\n⚔️ Atq: {player_total_attack}\n🛡️ Def: {player_total_defense}", inline=True)
    # Stats do Inimigo
    versus_embed.add_field(name=f"__**{enemy['name'].replace('⭐ **ELITE** ', '')}**__ (Lvl {enemy['min_level']}-{enemy['max_level']})", value=f"❤️ HP: {enemy_hp}\n⚔️ Atq: {enemy['attack']}\n🛡️ Def: {enemy['defense']}", inline=True)
    if player.get('image_url'):
        versus_embed.set_author(name=player['name'], icon_url=player['image_url'])
    if enemy.get('image_url'):
        versus_embed.set_thumbnail(url=enemy['image_url'])
    
    await ctx.send(embed=versus_embed)

    battle_log = []
    turn = 1

    # Loop de batalha automático
    while player_hp > 0 and enemy_hp > 0:
        # Turno do Jogador (sempre ataca)
        special_bonuses = player_bonuses.get("special", {})

        # Usa o atributo chave da classe para ataques físicos
        class_info = CLASS_DETAILS.get(player['class'])
        base_attack_stat_name = 'strength' # Padrão
        if class_info and class_info['type'] == 'physical':
            base_attack_stat_name = class_info['key_attribute']

        base_attack_stat = player[base_attack_stat_name]
        player_total_attack = base_attack_stat + player_bonuses['attack']
        player_damage = max(0, round(player_total_attack * random.uniform(0.8, 1.2)) - enemy['defense'])
        enemy_hp -= player_damage
        battle_log.append(f"Turno {turn}: ⚔️ Você ataca o {enemy['name']} e causa **{player_damage}** de dano. (Inimigo HP: {max(0, enemy_hp)})")

        # Lógica de Lifesteal
        lifesteal_percent = special_bonuses.get("LIFESTEAL_PERCENT")
        if lifesteal_percent and player_damage > 0:
            life_drained = round(player_damage * (lifesteal_percent / 100))
            player_hp = min(player['max_hp'], player_hp + life_drained)
            battle_log.append(f"Turno {turn}: 🩸 Você drena **{life_drained}** de vida do inimigo! (Seu HP: {max(0, player_hp)})")

        if enemy_hp <= 0:
            break

        # Turno do Inimigo
        player_total_defense = player_bonuses['defense'] + (player['dexterity'] // 4)
        enemy_damage = max(0, round(enemy['attack'] * random.uniform(0.8, 1.2)) - player_total_defense)
        player_hp -= enemy_damage
        battle_log.append(f"Turno {turn}: 💥 O {enemy['name']} ataca e causa **{enemy_damage}** de dano. (Seu HP: {max(0, player_hp)})")
        turn += 1

    # Envia o log da batalha
    log_message = "\n".join(battle_log)
    embed = discord.Embed(title=f"Resumo da Batalha: {player['name']} vs {enemy['name']}", description=log_message, color=discord.Color.orange())
    await ctx.send(embed=embed)
    await asyncio.sleep(1)

    # Fim da batalha
    if player_hp <= 0:
        await ctx.send(f"☠️ **DERROTA!** Você foi derrotado pelo {enemy['name']}.")
        database.update_character_stats(user_id, {"hp": 1})
    else:
        result_embed = discord.Embed(title="🏆 **VITÓRIA!** 🏆", description=f"Você derrotou o {enemy['name']}!", color=discord.Color.green())

        # Ganho de XP e Moedas
        new_experience = player['experience'] + enemy['xp_reward']
        new_gold = player['gold'] + enemy['gold_reward']
        xp_to_next_level = player['level'] * XP_PER_LEVEL_MULTIPLIER
        
        result_embed.add_field(name="Recompensas", value=f"**{enemy['xp_reward']}** de XP\n**{enemy['gold_reward']}** de Ouro", inline=False)

        updates = {"experience": new_experience, "hp": player_hp, "gold": new_gold}

        # Lógica de Level Up (simplificada para auto-hunt)
        if new_experience >= xp_to_next_level:
            updates['level'] = player['level'] + 1
            updates['experience'] = new_experience - xp_to_next_level

            level_up_msg = f"🎉 **LEVEL UP!** Você alcançou o nível **{updates['level']}**!\n"
            if updates['level'] % 5 == 0:
                level_up_msg += "Você ganhou pontos de atributo para distribuir! Use o comando `!hunt` para subir de nível e distribuí-los."

            # Aumenta HP/MP máximo no level up
            new_constitution = updates.get('constitution', player['constitution'])
            new_intelligence = updates.get('intelligence', player['intelligence'])
            updates['max_hp'] = player['max_hp'] + 10 + (new_constitution // 4)
            updates['max_mp'] = player['max_mp'] + 5 + (new_intelligence // 4)
            updates['hp'] = updates['max_hp'] # Restaura HP e MP no level up
            updates['mp'] = updates['max_mp']

            result_embed.add_field(name="Level Up!", value=level_up_msg + "\nSeus HP e MP foram restaurados e aumentados!", inline=False)

        database.update_character_stats(user_id, updates)

        # Lógica de Loot
        loot_rolls = 2 if is_elite else 1 # 2 rolagens de loot para Elites
        loot_chance = 0.3 # 30% de chance por rolagem
        loot_message = "Nenhum item encontrado."
        
        for i in range(loot_rolls):
            if random.random() > loot_chance:
                continue
            loot_item = database.get_random_loot(player['level'])
            if loot_item:
                database.add_item_to_inventory(user_id, loot_item['id'])
                loot_message = f"🎁 Você encontrou: **{loot_item['name']}**!" if i == 0 else loot_message + f"\n🎁 E também: **{loot_item['name']}**!"

        result_embed.add_field(name="Loot", value=loot_message, inline=False)
        
        # Recupera os dados atualizados para mostrar no rodapé
        updated_player = database.get_character(user_id)
        result_embed.set_footer(text=f"HP Final: {player_hp}/{updated_player['max_hp']} | XP: {updated_player['experience']}/{updated_player['level'] * XP_PER_LEVEL_MULTIPLIER}")

        await ctx.send(embed=result_embed)

        # Atualiza o progresso da missão, se houver
        database.update_quest_progress(user_id, 'kill', original_enemy_name)

# --- Comandos de Ajuda ---
bot.remove_command('help') # Remove o comando de ajuda padrão

@bot.command(name="help", aliases=["ajuda"], help="Mostra esta mensagem de ajuda.")
async def custom_help(ctx, *, command_name: str = None):
    if command_name:
        command = bot.get_command(command_name)
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
            "Personagem": ["newchar", "char", "skills", "quest", "bestiary", "reset"],
            "Ação": ["hunt", "autohunt", "use", "pvp"],
            "Interação": ["shop", "market"],
            "Equipamento": ["inventory", "equip", "unequip", "enhance"],
            "Outros": ["gm", "leaderboard"]
        }
        for category, cmd_list in categories.items():
            cmd_descriptions = "\n".join([f"`!{bot.get_command(c).name}` - {bot.get_command(c).help}" for c in cmd_list if bot.get_command(c)])
            embed.add_field(name=f"**--- {category} ---**", value=cmd_descriptions, inline=False)
        embed.set_footer(text="Use !help <comando> para ver detalhes de um comando específico.")
        embed.add_field(name="**--- Outros ---**", value="`!gm` - Mostra os créditos do criador do bot.", inline=False)
        await ctx.send(embed=embed)

@bot.command(name="bestiary", aliases=["inimigos", "monstros"], help="Lista os inimigos que você pode encontrar.")
async def bestiary(ctx):
    user_id = ctx.author.id
    player = database.get_character(user_id)
    if not player:
        await ctx.send("Você precisa de um personagem para consultar o bestiário.")
        return

    embed = discord.Embed(title="📖 Bestiário 📖", description=f"Informações sobre as criaturas para seu nível ({player['level']}).", color=discord.Color.dark_red())

    # Inimigos de encontro aleatório
    random_enemies = database.get_enemies_for_level(player['level'])
    if random_enemies:
        random_desc = "\n".join([f"**{e['name']}** (Nível {e['min_level']}-{e['max_level']})" for e in random_enemies])
        embed.add_field(name="--- Encontros Aleatórios no seu Nível ---", value=random_desc, inline=False)

    # Inimigos que podem ser caçados especificamente
    huntable_enemies = database.get_all_huntable_enemies(player['level'])
    if huntable_enemies:
        huntable_desc = ", ".join([f"`{e['name']}`" for e in huntable_enemies])
        embed.add_field(name="--- Caça Direcionada Disponível ---", value=f"Você pode usar `!hunt <nome>` ou `!autohunt <nome>` para caçar: {huntable_desc}", inline=False)

    embed.set_footer(text="Novas criaturas podem ser descobertas ao subir de nível.")
    await ctx.send(embed=embed)

# --- Comandos de Missão (Quest) ---
@bot.group(name="quest", aliases=["missao"], help="Gerencia suas missões.", invoke_without_command=True)
async def quest(ctx):
    await custom_help(ctx, command_name="quest")

@quest.command(name="list", help="Lista as missões diárias e semanais disponíveis.")
async def quest_list(ctx):
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
async def my_quests(ctx):
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
async def accept_quest(ctx, quest_id: int):
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
async def complete_quest(ctx, quest_id: int):
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
    
    # Lógica de recompensa
    quest_info = database.get_quest_by_id(quest_id)
    updates = {
        'experience': player['experience'] + quest_info['xp_reward'],
        'gold': player['gold'] + quest_info['gold_reward']
    }

    reward_message = f"🎉 Missão **'{quest_info['name']}'** completa!\n"
    reward_message += f"Você recebeu **{quest_info['xp_reward']}** XP e **{quest_info['gold_reward']}** Ouro!"

    # Verifica e adiciona recompensa de item
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

@bot.command(name="reset", help="Apaga seu personagem para recomeçar do zero, mantendo o nome.")
async def reset_character(ctx):
    user_id = ctx.author.id
    character = database.get_character(user_id)

    if not character:
        await ctx.send("Você não tem um personagem para resetar. Use `!newchar` para criar um.")
        return

    char_name = character['name']
    guild_id = character['guild_id']

    # --- Passo de Confirmação ---
    embed = discord.Embed(
        title="⚠️ ATENÇÃO: Reset de Personagem ⚠️",
        description=(
            f"Você está prestes a resetar **{char_name}**.\n"
            "**TODA** a sua progressão (nível, ouro, itens, missões) será **PERMANENTEMENTE APAGADA**.\n"
            "Seu personagem voltará ao nível 1 e você precisará escolher raça e classe novamente.\n\n"
            "Para confirmar, digite `resetar meu personagem`."
        ),
        color=discord.Color.red()
    )
    await ctx.author.send(embed=embed) # Send confirmation to DMs to be safe

    try:
        confirm_msg = await bot.wait_for(
            "message",
            check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel) and m.content.lower() == "resetar meu personagem",
            timeout=30.0
        )
    except asyncio.TimeoutError:
        await ctx.author.send("Reset cancelado. Nenhuma alteração foi feita.")
        return

    # --- Processo de Reset ---
    await ctx.author.send(f"Iniciando o reset para **{char_name}**...")
    
    # Deletar canal antigo
    if character.get('channel_id'):
        old_channel = bot.get_channel(character['channel_id'])
        if old_channel:
            try:
                await old_channel.delete(reason=f"Reset do personagem {char_name}")
            except discord.Forbidden:
                await ctx.author.send("Não foi possível apagar seu canal antigo. Por favor, peça a um administrador para removê-lo.")

    # Deletar dados do personagem
    if not database.delete_character_full(user_id):
        await ctx.author.send("Ocorreu um erro ao apagar os dados antigos do seu personagem. O processo foi abortado.")
        return

    await ctx.author.send("Dados antigos removidos. Agora, vamos recriar seu personagem. O nome será mantido.")
    await asyncio.sleep(2)

    # --- Processo de Recriação (similar ao !newchar, mas sem pedir o nome) ---
    # A comunicação agora é via DM (ctx.author)
    
    # 1. Seleção de Raça
    races_str = ", ".join(RACES)
    await ctx.author.send(f"Escolha sua nova raça: {races_str}")
    try:
        race_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel) and m.content in RACES, timeout=60.0)
        char_race = race_msg.content
    except asyncio.TimeoutError:
        await ctx.author.send("Tempo esgotado. Processo de reset falhou. Use `!newchar` para criar um novo personagem.")
        return

    # 2. Seleção de Classe
    classes_str = ", ".join(CLASSES)
    await ctx.author.send(f"Escolha sua nova classe: {classes_str}")
    try:
        class_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel) and m.content in CLASSES, timeout=60.0)
        char_class = class_msg.content
    except asyncio.TimeoutError:
        await ctx.author.send("Tempo esgotado. Processo de reset falhou. Use `!newchar` para criar um novo personagem.")
        return

    # 3. Distribuição de Atributos
    attributes = {attr.capitalize(): MIN_ATTRIBUTE_VALUE for attr in ATTRIBUTE_MAP_PT_EN.keys()}
    remaining_points = TOTAL_ATTRIBUTE_POINTS

    racial_bonus = RACE_MODIFIERS[char_race]
    bonus_str = ", ".join([f"{attr.capitalize()} {mod:+}" for attr, mod in racial_bonus.items() if mod != 0])

    await ctx.author.send(f"Agora, vamos distribuir seus atributos. Todos começam em **{MIN_ATTRIBUTE_VALUE}** e você tem **{TOTAL_ATTRIBUTE_POINTS}** pontos para aumentá-los. "
                          f"O valor máximo de um atributo (antes do bônus racial) é **{MAX_ATTRIBUTE_VALUE}**. "
                          f"Sua raça ({char_race}) concede os seguintes bônus: **{bonus_str}**.\nDigite o atributo e o valor. Ex: `Força 15`")

    while remaining_points > 0:
        await ctx.author.send(f"Pontos restantes: **{remaining_points}**. Atributos atuais: `{attributes}`. "
                              f"Qual atributo você quer alterar? (Ex: `Força 14`)")
        try:
            attr_input_msg = await bot.wait_for("message", check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel), timeout=120.0)
            parts = attr_input_msg.content.split()
            if len(parts) != 2:
                await ctx.author.send("Formato inválido. Use `Atributo Valor`, por exemplo: `Força 12`.")
                continue
            
            attr_name_input, value_str = parts
            attr_name = attr_name_input.capitalize()
            
            if attr_name not in attributes:
                await ctx.author.send(f"Atributo '{attr_name}' inválido. Os atributos são: {list(attributes.keys())}.")
                continue

            value = int(value_str)
            if not (MIN_ATTRIBUTE_VALUE <= value <= MAX_ATTRIBUTE_VALUE):
                await ctx.author.send(f"Valor inválido. O atributo deve estar entre {MIN_ATTRIBUTE_VALUE} e {MAX_ATTRIBUTE_VALUE}.")
                continue

            attributes[attr_name] = value
            points_spent = sum(v - MIN_ATTRIBUTE_VALUE for v in attributes.values())
            remaining_points = TOTAL_ATTRIBUTE_POINTS - points_spent

        except (ValueError, asyncio.TimeoutError):
            await ctx.author.send("Entrada inválida ou tempo esgotado. Por favor, comece novamente com `!newchar`.")
            return

    # Aplicar modificadores raciais
    final_attributes = {}
    for attr_pt, attr_en in ATTRIBUTE_MAP_PT_EN.items():
        base_value = attributes[attr_pt.capitalize()]
        modifier = racial_bonus.get(attr_en, 0)
        final_attributes[attr_en] = base_value + modifier

    hp, mp = calculate_hp_mp(final_attributes["constitution"], final_attributes["intelligence"], char_class)

    # 4. Criar novo canal privado
    guild = bot.get_guild(guild_id)
    if not guild:
        await ctx.author.send("Não foi possível encontrar o servidor original. O processo de reset falhou.")
        return
        
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    try:
        private_channel = await guild.create_text_channel(
            f'rpg-{char_name.lower().replace(" ", "-")}',
            overwrites=overwrites,
            reason=f"Canal RPG recriado para {char_name}"
        )
        channel_id = private_channel.id
    except discord.Forbidden:
        await ctx.author.send("Não consegui criar seu novo canal privado. Verifique as permissões do bot no servidor.")
        channel_id = None

    # 5. Salvar personagem no DB
    success = database.create_character(
        user_id, guild_id, channel_id, char_name, char_race, char_class,
        final_attributes["strength"], final_attributes["constitution"], final_attributes["dexterity"],
        final_attributes["intelligence"], final_attributes["wisdom"], final_attributes["charisma"],
        hp, mp
    )

    if success:
        # Adiciona poções iniciais
        potion_item = database.get_item_by_name("Poção de Cura Pequena")
        if potion_item:
            database.add_item_to_inventory(user_id, potion_item['id'], 20)
            await ctx.author.send("Você recebeu **20x Poção de Cura Pequena** para iniciar sua jornada!")
        else:
            print("Aviso: 'Poção de Cura Pequena' não encontrada no banco de dados. Poções iniciais não foram adicionadas.")

        await ctx.author.send(f"Parabéns, **{char_name}** foi resetado e recriado com sucesso!")
        if channel_id:
            await private_channel.send(f"Bem-vindo de volta à sua jornada, {ctx.author.mention}! Este é seu novo canal de aventura.")
            await ctx.author.send(f"Seu novo canal de aventura é: {private_channel.mention}")

        # 6. Aviso no chat #geral
        general_channel = await get_general_channel(guild)
        if general_channel:
            await general_channel.send(f"🔄 O aventureiro(a) **{char_name}** decidiu recomeçar sua jornada, renascendo como um(a) {char_race} {char_class}!")
    else:
        await ctx.author.send("Ocorreu um erro ao salvar seu novo personagem. Por favor, tente usar `!newchar`.")

@bot.command(name="migrate", help="Move seu personagem para o servidor atual. Deve ser usado no servidor de destino.")
async def migrate(ctx):
    user_id = ctx.author.id
    destination_guild = ctx.guild
    destination_guild_id = destination_guild.id

    character = database.get_character(user_id)

    if not character:
        await ctx.send("Você não tem um personagem para migrar.")
        return

    if character['guild_id'] == destination_guild.id:
        await ctx.send("Seu personagem já está neste servidor!")
        return

    # --- Passo de Confirmação ---
    embed = discord.Embed(
        title="⚠️ Confirmação de Migração ⚠️",
        description=(
            f"Você está prestes a migrar **{character['name']}** para o servidor **'{destination_guild.name}'**.\n"
            "Seu canal privado atual será apagado e um novo será criado no servidor de destino.\n\n"
            "Para confirmar, digite `migrar meu personagem`."
        ),
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

    try:
        confirm_msg = await bot.wait_for(
            "message",
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "migrar meu personagem",
            timeout=30.0
        )
    except asyncio.TimeoutError:
        await ctx.send("Migração cancelada. Nenhuma alteração foi feita.")
        return

    # --- Processo de Migração ---
    await ctx.send(f"Iniciando a migração para **'{destination_guild.name}'**...")

    # 1. Deletar canal antigo
    if character.get('channel_id'):
        old_channel = bot.get_channel(character['channel_id'])
        if old_channel:
            try:
                await old_channel.delete(reason=f"Migração do personagem {character['name']}")
            except discord.Forbidden:
                await ctx.send("Não foi possível apagar seu canal antigo. A migração continuará, mas peça a um administrador para remover o canal manualmente.")

    # 2. Criar novo canal privado no servidor de destino
    overwrites = {
        destination_guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        destination_guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    try:
        private_channel = await destination_guild.create_text_channel(
            f'rpg-{character["name"].lower().replace(" ", "-")}',
            overwrites=overwrites,
            reason=f"Canal RPG migrado para {character['name']}"
        )
        new_channel_id = private_channel.id
    except discord.Forbidden:
        await ctx.send("Não consegui criar seu novo canal privado no servidor de destino. A migração falhou. Verifique as permissões do bot lá.")
        return

    # 3. Atualizar o banco de dados
    if database.update_character_guild(user_id, destination_guild_id, new_channel_id):
        await ctx.send(f"✅ Migração concluída com sucesso! Seu personagem **{character['name']}** agora pertence ao servidor **'{destination_guild.name}'**.")
        await private_channel.send(f"Bem-vindo(a) ao seu novo lar, {ctx.author.mention}! Sua aventura continua aqui.")

        # 4. Aviso no chat #geral do novo servidor
        general_channel = await get_general_channel(destination_guild)
        if general_channel:
            await general_channel.send(f"👋 Um(a) aventureiro(a) experiente chegou! **{character['name']}** migrou para este servidor para continuar sua jornada!")
    else:
        await ctx.send("Ocorreu um erro ao atualizar os dados do seu personagem no banco de dados. A migração falhou.")

@bot.command(name="gm", help="Mostra os créditos do criador do bot.")
async def gm_command(ctx):
    embed = discord.Embed(
        title="Créditos do TextHeroes",
        description=f"Este bot foi desenvolvido com ❤️ por <@{OWNER_ID}>.",
        color=discord.Color.from_rgb(114, 137, 218) # Discord Blurple
    )
    embed.add_field(name="GitHub", value="https://github.com/Keyditor/TextHeroes-RPG-BOT")
    embed.set_footer(text="Sinta-se livre para usar este código como base para seus próprios projetos!")
    await ctx.send(embed=embed)

    # Envia uma notificação para o dono do bot
    try:
        owner = await bot.fetch_user(OWNER_ID)
        if owner:
            await owner.send(f"ℹ️ O comando `!gm` foi usado no servidor **'{ctx.guild.name}'** pelo usuário **{ctx.author.name}** (`{ctx.author.id}`).")
    except Exception as e:
        print(f"Não foi possível enviar a notificação para o dono do bot: {e}")

@bot.command(name="debug", help="Ativa ou desativa o modo de debug para o console.")
@commands.is_owner() # Apenas o dono do bot (definido na inicialização) pode usar
async def debug_mode(ctx):
    global DEBUG_MODE
    DEBUG_MODE = not DEBUG_MODE
    status = "ATIVADO" if DEBUG_MODE else "DESATIVADO"
    await ctx.send(f"🔧 Modo de Debug foi **{status}**.")

@debug_mode.error
async def debug_mode_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.send("Apenas o proprietário do bot pode usar este comando.")

# --- Sistema de PvP ---

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

@bot.group(name="pvp", help="Inicia ou gerencia um duelo PvP.", invoke_without_command=True)
async def pvp(ctx):
    await custom_help(ctx, command_name="pvp")

@pvp.command(name="challenge", help="Desafia outro jogador. Uso: !pvp challenge [ranked] <nome>")
async def pvp_challenge(ctx, *args):
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

    if target_id in pvp_invitations.values() or challenger_id in pvp_invitations:
        await ctx.send("Um de vocês já tem um desafio pendente.")
        return

    if target_id in active_pvp_battles or challenger_id in active_pvp_battles:
        await ctx.send("Um de vocês já está em uma batalha.")
        return

    pvp_invitations[target_id] = challenger_id
    pvp_invitations[f"{target_id}_ranked"] = is_ranked # Armazena se é ranqueada
    
    await ctx.send(f"⚔️ Desafio {'Ranqueado ' if is_ranked else ''}enviado para **{target_char['name']}**! Ele(a) tem 60 segundos para aceitar.")

    # Envia o convite para o canal privado do jogador desafiado
    target_channel = bot.get_channel(target_char['channel_id'])
    if target_channel:
        await target_channel.send(f"⚔️ <@{target_id}>, você foi desafiado para um duelo {'Ranqueado ' if is_ranked else ''}por **{challenger_char['name']}**! "
                                  f"Use `!pvp accept {challenger_char['name']}` ou `!pvp decline {challenger_char['name']}` neste canal.")
    else:
        # Fallback para DM caso o canal não seja encontrado
        target_user = await bot.fetch_user(target_id)
        await target_user.send(f"⚔️ Você foi desafiado para um duelo por **{challenger_char['name']}**! "
                               f"Use `!pvp accept {challenger_char['name']}` ou `!pvp decline {challenger_char['name']}` no seu canal de RPG.")

    await asyncio.sleep(60)
    if pvp_invitations.get(target_id) == challenger_id:
        del pvp_invitations[target_id]
        if f"{target_id}_ranked" in pvp_invitations: del pvp_invitations[f"{target_id}_ranked"]
        await ctx.send(f"O desafio para **{target_char['name']}** expirou.")

@pvp.command(name="accept", help="Aceita um desafio de duelo.")
async def pvp_accept(ctx, *, challenger_name: str):
    challenged_id = ctx.author.id
    challenger_char = database.get_character_by_name(challenger_name)
    if not challenger_char:
        await ctx.send(f"Personagem '{challenger_name}' não encontrado.")
        return

    challenger_id = challenger_char['user_id']

    if pvp_invitations.get(challenged_id) != challenger_id:
        await ctx.send("Você não tem um desafio pendente deste jogador.")
        return

    is_ranked = pvp_invitations.get(f"{challenged_id}_ranked", False)
    del pvp_invitations[challenged_id]
    if f"{challenged_id}_ranked" in pvp_invitations: del pvp_invitations[f"{challenged_id}_ranked"]

    challenged_char = database.get_character(challenged_id)

    # Inicia a batalha
    battle = PVPBattle(challenger_char, challenged_char, ranked=is_ranked)
    active_pvp_battles[challenger_id] = battle
    active_pvp_battles[challenged_id] = battle

    challenger_channel = bot.get_channel(challenger_char['channel_id'])
    challenged_channel = bot.get_channel(challenged_char['channel_id'])

    await challenger_channel.send(f"**{challenged_char['name']}** aceitou seu desafio! A batalha {'Ranqueada ' if is_ranked else ''}vai começar!")
    await challenged_channel.send(f"Você aceitou o desafio de **{challenger_char['name']}**! A batalha {'Ranqueada ' if is_ranked else ''}vai começar!")

    # Inicia o loop da batalha
    await run_pvp_battle(battle)

def _process_effects(battle, player_id):
    """Processa efeitos de status (como veneno) no início do turno do jogador."""
    log_entries = []
    effects = battle.p1_effects if player_id == battle.p1['user_id'] else battle.p2_effects
    
    # Dano de Veneno
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

async def run_pvp_battle(battle):
    p1_channel = bot.get_channel(battle.p1['channel_id'])
    p2_channel = bot.get_channel(battle.p2['channel_id'])

    while battle.p1_hp > 0 and battle.p2_hp > 0:
        current_player_id = battle.turn
        current_player_char = battle.p1 if current_player_id == battle.p1['user_id'] else battle.p2
        current_player_channel = p1_channel if current_player_id == battle.p1['user_id'] else p2_channel
        
        opponent_char = battle.p2 if current_player_id == battle.p1['user_id'] else battle.p1
        opponent_channel = p2_channel if current_player_id == battle.p1['user_id'] else p1_channel

        # Processar efeitos de status no início do turno
        effect_logs = _process_effects(battle, current_player_id)
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
            action_msg = await bot.wait_for(
                "message",
                check=lambda m: m.author.id == current_player_id and m.channel == current_player_channel and m.content.lower() in ["atacar", "habilidade", "skill", "fugir"],
                timeout=60.0
            )
            action = action_msg.content.lower()

            # Lógica da ação (simplificada, pode ser expandida com a lógica do !hunt)
            if action == "atacar":
                attacker_bonuses = battle.p1_bonuses if current_player_id == battle.p1['user_id'] else battle.p2_bonuses
                defender_bonuses = battle.p2_bonuses if current_player_id == battle.p1['user_id'] else battle.p1_bonuses
                
                attacker_effects = battle.p1_effects if current_player_id == battle.p1['user_id'] else battle.p2_effects
                defender_effects = battle.p2_effects if current_player_id == battle.p1['user_id'] else battle.p1_effects

                # Aplica buffs/debuffs
                attack_buff = attacker_effects.get('buff_attack', {}).get('value', 0)
                defense_debuff = defender_effects.get('debuff_defense', {}).get('value', 0)
                defense_buff = defender_effects.get('buff_defense', {}).get('value', 0)

                attack_stat = current_player_char['strength'] + attacker_bonuses['attack'] + attack_buff
                defense_stat = opponent_char['constitution'] + defender_bonuses['defense'] + defense_buff - defense_debuff

                if DEBUG_MODE:
                    print("\n--- CÁLCULO DE DANO (ATAQUE NORMAL) ---")
                    print(f"Atacante: {current_player_char['name']} | Defensor: {opponent_char['name']}")
                    print(f"Ataque Total: {attack_stat} = {current_player_char['strength']}(base) + {attacker_bonuses['attack']}(itens) + {attack_buff}(buff)")
                    print(f"Defesa Total: {defense_stat} = {opponent_char['constitution']}(base) + {defender_bonuses['defense']}(itens) + {defense_buff}(buff) - {defense_debuff}(debuff)")

                damage = max(0, round(attack_stat * random.uniform(0.9, 1.1)) - defense_stat)
                
                if current_player_id == battle.p1['user_id']:
                    battle.p2_hp -= damage
                else:
                    battle.p1_hp -= damage
                
                if DEBUG_MODE:
                    print(f"Dano Final: {damage}")

                log_entry = f"**Turno {battle.turn_count}**: ⚔️ **{current_player_char['name']}** ataca **{opponent_char['name']}** e causa **{damage}** de dano!"
                battle.log.append(log_entry)

            elif action == "habilidade" or action == "skill":
                skills = database.get_character_skills(current_player_char['class'], current_player_char['level'])
                if not skills:
                    battle.log.append(f"**Turno {battle.turn_count}**: ❓ **{current_player_char['name']}** tentou usar uma habilidade, mas não conhece nenhuma e perdeu o turno.")
                else:
                    skill_list_str = "\n".join([f"`{idx+1}`: **{s['name']}** (Custo: {s['mp_cost']} MP)" for idx, s in enumerate(skills)])
                    await current_player_channel.send(f"Qual habilidade você quer usar?\n{skill_list_str}\nDigite o número da habilidade ou `cancelar`.")
                    
                    try:
                        skill_choice_msg = await bot.wait_for(
                            "message",
                            check=lambda m: m.author.id == current_player_id and m.channel == current_player_channel,
                            timeout=30.0
                        )
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
                                    # Deduz MP
                                    if current_player_id == battle.p1['user_id']: battle.p1_mp -= skill['mp_cost']
                                    else: battle.p2_mp -= skill['mp_cost']

                                    # Lógica de Efeitos
                                    scaling_stat_value = current_player_char.get(skill['scaling_stat'], 0)
                                    total_effect_value = round(skill['base_value'] + (scaling_stat_value * skill['scaling_factor']))

                                    if skill['effect_type'] == 'DAMAGE':
                                        defender_bonuses = battle.p2_bonuses if current_player_id == battle.p1['user_id'] else battle.p1_bonuses
                                        defense_stat = opponent_char['constitution'] + defender_bonuses['defense']
                                        if DEBUG_MODE:
                                            print("\n--- CÁLCULO DE DANO (SKILL DAMAGE) ---")
                                            print(f"Poder da Skill: {total_effect_value} | Defesa do Alvo: {defense_stat}")
                                        skill_damage = max(0, total_effect_value - defense_stat)
                                        
                                        if current_player_id == battle.p1['user_id']: battle.p2_hp -= skill_damage
                                        else: battle.p1_hp -= skill_damage

                                        if DEBUG_MODE: print(f"Dano Final da Skill: {skill_damage}")
                                        battle.log.append(f"**Turno {battle.turn_count}**: ✨ **{current_player_char['name']}** usa **{skill['name']}** e causa **{skill_damage}** de dano em **{opponent_char['name']}**!")

                                    elif skill['effect_type'] == 'DAMAGE_PIERCING':
                                        defender_bonuses = battle.p2_bonuses if current_player_id == battle.p1['user_id'] else battle.p1_bonuses
                                        # O poder da skill é o dano, e a penetração é calculada separadamente
                                        penetration_value = round(skill['base_value'] + ((current_player_char.get(skill['scaling_stat'], 0)*0.25) * skill['scaling_factor']))
                                        total_defense = opponent_char['constitution'] + defender_bonuses['defense']
                                        final_defense = max(0, total_defense - penetration_value)
                                        if DEBUG_MODE:
                                            print("\n--- CÁLCULO DE DANO (SKILL PIERCING) ---")
                                            print(f"Poder da Skill: {total_effect_value} | Defesa Original: {total_defense} | Penetração: {penetration_value} | Defesa Final: {final_defense}")
                                        skill_damage = max(0, total_effect_value - final_defense)

                                        if current_player_id == battle.p1['user_id']: battle.p2_hp -= skill_damage
                                        else: battle.p1_hp -= skill_damage

                                        battle.log.append(f"**Turno {battle.turn_count}**: ✨ **{current_player_char['name']}** usa **{skill['name']}** e causa **{skill_damage}** de dano em **{opponent_char['name']}**!")
                                    
                                    elif skill['effect_type'] == 'HEAL':
                                        if current_player_id == battle.p1['user_id']:
                                            battle.p1_hp = min(battle.p1['max_hp'], battle.p1_hp + total_effect_value)
                                        else:
                                            battle.p2_hp = min(battle.p2['max_hp'], battle.p2_hp + total_effect_value)
                                        battle.log.append(f"**Turno {battle.turn_count}**: 💖 **{current_player_char['name']}** usa **{skill['name']}** e se cura em **{total_effect_value}** de HP!")

                                    elif skill['effect_type'] == 'DAMAGE_AND_POISON':
                                        defender_bonuses = battle.p2_bonuses if current_player_id == battle.p1['user_id'] else battle.p1_bonuses
                                        defense_stat = opponent_char['constitution'] + defender_bonuses['defense']
                                        skill_damage = max(0, total_effect_value - defense_stat)
                                        
                                        if current_player_id == battle.p1['user_id']: battle.p2_hp -= skill_damage
                                        else: battle.p1_hp -= skill_damage
                                        battle.log.append(f"**Turno {battle.turn_count}**: ✨ **{current_player_char['name']}** usa **{skill['name']}** e causa **{skill_damage}** de dano direto...")

                                        # Aplica veneno
                                        opponent_effects = battle.p2_effects if current_player_id == battle.p1['user_id'] else battle.p1_effects
                                        opponent_effects['poison'] = {'damage': round(total_effect_value * 0.5), 'duration': skill['effect_duration']}
                                        battle.log.append(f"**Turno {battle.turn_count}**: 🐍 ...e envenena **{opponent_char['name']}** por {skill['effect_duration']} turnos!")

                                    elif skill['effect_type'] == 'BUFF_ATTACK':
                                        attacker_effects = battle.p1_effects if current_player_id == battle.p1['user_id'] else battle.p2_effects
                                        attacker_effects['buff_attack'] = {'value': total_effect_value, 'duration': skill['effect_duration']}
                                        battle.log.append(f"**Turno {battle.turn_count}**: 💪 **{current_player_char['name']}** usa **{skill['name']}** e aumenta seu ataque por {skill['effect_duration']} turnos!")

                                    elif skill['effect_type'] == 'BUFF_DEFENSE':
                                        attacker_effects = battle.p1_effects if current_player_id == battle.p1['user_id'] else battle.p2_effects
                                        attacker_effects['buff_defense'] = {'value': total_effect_value, 'duration': skill['effect_duration']}
                                        battle.log.append(f"**Turno {battle.turn_count}**: 🛡️ **{current_player_char['name']}** usa **{skill['name']}** e aumenta sua defesa por {skill['effect_duration']} turnos!")

                                    elif skill['effect_type'] == 'DEBUFF_DEFENSE':
                                        opponent_effects = battle.p2_effects if current_player_id == battle.p1['user_id'] else battle.p1_effects
                                        opponent_effects['debuff_defense'] = {'value': total_effect_value, 'duration': skill['effect_duration']}
                                        battle.log.append(f"**Turno {battle.turn_count}**: 📉 **{current_player_char['name']}** usa **{skill['name']}** e reduz a defesa de **{opponent_char['name']}** por {skill['effect_duration']} turnos!")

                                    else:
                                        battle.log.append(f"**Turno {battle.turn_count}**: 🌀 **{current_player_char['name']}** usa **{skill['name']}**, mas o efeito ainda não foi implementado em PvP.")

                            else:
                                battle.log.append(f"**Turno {battle.turn_count}**: ❓ **{current_player_char['name']}** fez uma escolha inválida e perdeu o turno.")

                    except (asyncio.TimeoutError, ValueError):
                        battle.log.append(f"**Turno {battle.turn_count}**: ⏳ **{current_player_char['name']}** demorou para escolher uma habilidade e perdeu o turno.")

            elif action == "fugir":
                log_entry = f"**Turno {battle.turn_count}**: 🏳️ **{current_player_char['name']}** fugiu do duelo!"
                battle.log.append(log_entry)
                if current_player_id == battle.p1['user_id']: battle.p1_hp = 0
                else: battle.p2_hp = 0

            # Enviar log para ambos os jogadores
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

    # Atualiza stats de PvP se for ranqueada
    if battle.ranked:
        winner_stats = database.get_character(winner['user_id'])
        loser_stats = database.get_character(loser['user_id'])
        database.update_character_stats(winner['user_id'], {'pvp_wins': winner_stats['pvp_wins'] + 1})
        database.update_character_stats(loser['user_id'], {'pvp_losses': loser_stats['pvp_losses'] + 1})
        await p1_channel.send("As estatísticas ranqueadas foram atualizadas.")
        await p2_channel.send("As estatísticas ranqueadas foram atualizadas.")

    # Cura ambos os jogadores
    database.update_character_stats(battle.p1['user_id'], {'hp': battle.p1['max_hp'], 'mp': battle.p1['max_mp']})
    database.update_character_stats(battle.p2['user_id'], {'hp': battle.p2['max_hp'], 'mp': battle.p2['max_mp']})

    # Limpa o estado da batalha
    del active_pvp_battles[battle.p1['user_id']]
    del active_pvp_battles[battle.p2['user_id']]

@bot.command(name="leaderboard", aliases=["ranking", "top"], help="Mostra os rankings do servidor.")
async def leaderboard(ctx, ranking_type: str = 'level'):
    if ranking_type.lower() not in ['level', 'pvp']:
        await ctx.send("Tipo de ranking inválido. Use `level` ou `pvp`.")
        return

    if ranking_type.lower() == 'level':
        data = database.get_leaderboard('level')
        embed = discord.Embed(title="🏆 Placar de Líderes - Nível 🏆", description="Os aventureiros mais experientes do servidor.", color=discord.Color.gold())
        for i, player in enumerate(data):
            embed.add_field(name=f"#{i+1} - {player['name']}", value=f"**Nível:** {player['level']} | **XP:** {player['experience']}", inline=False)
    
    elif ranking_type.lower() == 'pvp':
        data = database.get_leaderboard('pvp')
        embed = discord.Embed(title="⚔️ Placar de Líderes - PvP Ranqueado ⚔️", description="Os duelistas mais temidos do servidor.", color=discord.Color.red())
        for i, player in enumerate(data):
            score = player.get('score', 0)
            embed.add_field(
                name=f"#{i+1} - {player['name']}", 
                value=f"**Score:** {score} | **Vitórias:** {player['pvp_wins']} | **Derrotas:** {player['pvp_losses']}", 
                inline=False
            )

    await ctx.send(embed=embed)

# --- Executar o Bot ---

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)