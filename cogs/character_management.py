import discord
from discord.ext import commands
import asyncio
import database
from game_constants import *

class CharacterManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _calculate_hp_mp(self, constitution, intelligence, char_class):
        """Calcula HP e MP baseados nos atributos e classe."""
        base_hp = 50
        base_mp = 20
        hp = base_hp + (constitution * 5)
        if char_class in ["Feiticeiro", "Bardo"]:
            mp = base_mp + (intelligence * 3)
        else:
            mp = base_mp + (intelligence * 2)
        return hp, mp

    @commands.command(name="newchar", help="Cria um novo personagem para o RPG.")
    async def new_character(self, ctx):
        user_id = ctx.author.id
        guild_id = ctx.guild.id

        if database.get_character(user_id):
            await ctx.send(f"Você já possui um personagem. Use `!reset` para recomeçar.")
            return

        await ctx.send(f"Bem-vindo(a) à jornada, {ctx.author.mention}! Vamos criar seu personagem.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            await ctx.send("Qual o nome do seu personagem?")
            name_msg = await self.bot.wait_for("message", check=check, timeout=60.0)
            char_name = name_msg.content

            races_str = ", ".join(RACES)
            await ctx.send(f"Escolha sua raça: {races_str}")
            race_msg = await self.bot.wait_for("message", check=lambda m: check(m) and m.content.capitalize() in RACES, timeout=60.0)
            char_race = race_msg.content.capitalize()

            class_descriptions = "\n".join([f"**{c}**: {d['key_attribute'].capitalize()}" for c, d in CLASS_DETAILS.items()])
            await ctx.send(f"Escolha sua classe: {', '.join(CLASSES)}\n{class_descriptions}")
            class_msg = await self.bot.wait_for("message", check=lambda m: check(m) and m.content.capitalize() in CLASSES, timeout=60.0)
            char_class = class_msg.content.capitalize()

            attributes = {attr.capitalize(): MIN_ATTRIBUTE_VALUE for attr in ATTRIBUTE_MAP_PT_EN.keys()}
            remaining_points = TOTAL_ATTRIBUTE_POINTS
            racial_bonus = RACE_MODIFIERS[char_race]
            bonus_str = ", ".join([f"{attr.capitalize()} {mod:+}" for attr, mod in racial_bonus.items() if mod != 0])

            await ctx.send(f"Agora, distribua **{TOTAL_ATTRIBUTE_POINTS}** pontos entre seus atributos (base {MIN_ATTRIBUTE_VALUE}, máx {MAX_ATTRIBUTE_VALUE}).\nBônus racial ({char_race}): **{bonus_str}**.\nDigite o atributo e o valor. Ex: `Força 15`")

            while remaining_points > 0:
                await ctx.send(f"Pontos restantes: **{remaining_points}**. Atributos: `{attributes}`.\nQual atributo você quer alterar? (Ex: `Força 14`)")
                attr_input_msg = await self.bot.wait_for("message", check=check, timeout=120.0)
                parts = attr_input_msg.content.split()
                if len(parts) != 2:
                    await ctx.send("Formato inválido. Use `Atributo Valor`.")
                    continue
                
                attr_name_input, value_str = parts
                attr_name = attr_name_input.capitalize()
                
                if attr_name not in attributes:
                    await ctx.send(f"Atributo '{attr_name}' inválido.")
                    continue

                value = int(value_str)
                if not (MIN_ATTRIBUTE_VALUE <= value <= MAX_ATTRIBUTE_VALUE):
                    await ctx.send(f"Valor inválido. O atributo deve estar entre {MIN_ATTRIBUTE_VALUE} e {MAX_ATTRIBUTE_VALUE}.")
                    continue

                attributes[attr_name] = value
                points_spent = sum(v - MIN_ATTRIBUTE_VALUE for v in attributes.values())
                remaining_points = TOTAL_ATTRIBUTE_POINTS - points_spent

            if remaining_points != 0:
                await ctx.send("Você não usou todos os pontos. Criação cancelada. Comece novamente.")
                return

            final_attributes = {attr_en: attributes[attr_pt.capitalize()] + racial_bonus.get(attr_en, 0) for attr_pt, attr_en in ATTRIBUTE_MAP_PT_EN.items()}
            hp, mp = self._calculate_hp_mp(final_attributes["constitution"], final_attributes["intelligence"], char_class)

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            private_channel = await ctx.guild.create_text_channel(f'rpg-{char_name.lower().replace(" ", "-")}', overwrites=overwrites)
            
            success = database.create_character(user_id, guild_id, private_channel.id, char_name, char_race, char_class, **final_attributes, hp=hp, mp=mp)

            if success:
                potion_item = database.get_item_by_name("Poção de Cura Pequena")
                if potion_item:
                    database.add_item_to_inventory(user_id, potion_item['id'], 20)
                
                await ctx.send(f"Parabéns, {char_name} foi criado(a) com sucesso! Seu canal de aventura é: {private_channel.mention}")
                general_channel = discord.utils.get(ctx.guild.text_channels, name=GENERAL_CHANNEL_NAME)
                if general_channel:
                    await general_channel.send(f"🎉 Um novo aventureiro(a) se juntou à jornada! **{char_name}** ({char_race} {char_class}) embarca em sua aventura!")
            else:
                await ctx.send("Ocorreu um erro ao salvar seu personagem.")

        except (asyncio.TimeoutError, ValueError):
            await ctx.send("Tempo esgotado ou entrada inválida. Por favor, comece novamente com `!newchar`.")

    @commands.command(name="char", aliases=["ficha"], help="Exibe a ficha do seu personagem ou atualiza a imagem.")
    async def character_sheet(self, ctx, subcommand: str = None, *, url: str = None):
        user_id = ctx.author.id
        character = database.get_character(user_id)
        if not character:
            await ctx.send("Você não tem um personagem. Use `!newchar` para criar um.")
            return

        if subcommand == "img":
            if not url:
                await ctx.send("Por favor, forneça a URL da imagem. Ex: `!char img <url-da-imagem>`")
                return
            if database.update_character_image(user_id, url):
                await ctx.send(f"Imagem do personagem atualizada com sucesso!")
            else:
                await ctx.send("Não foi possível atualizar a imagem.")
            return

        equipped_items, bonuses = database.get_equipped_items(user_id)
        
        embed = discord.Embed(title=f"Ficha de Personagem: {character['name']}", description=f"**Raça:** {character['race']} | **Classe:** {character['class']}", color=discord.Color.blue())
        embed.add_field(name="Level", value=character['level'], inline=True)
        embed.add_field(name="XP", value=f"{character['experience']} / {character['level'] * XP_PER_LEVEL_MULTIPLIER}", inline=True)
        embed.add_field(name="💰 Gold", value=character['gold'], inline=True)
        embed.add_field(name="HP", value=f"{character['hp']}/{character['max_hp']}", inline=True)
        embed.add_field(name="MP", value=f"{character['mp']}/{character['max_mp']}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.add_field(name="Força", value=f"{character['strength']}", inline=True)
        embed.add_field(name="Constituição", value=character['constitution'], inline=True)
        embed.add_field(name="Destreza", value=character['dexterity'], inline=True)
        embed.add_field(name="Inteligência", value=character['intelligence'], inline=True)
        embed.add_field(name="Sabedoria", value=character['wisdom'], inline=True)
        embed.add_field(name="Carisma", value=character['charisma'], inline=True)

        embed.add_field(name="\u200b", value="--- **Bônus de Equipamento** ---", inline=False)
        embed.add_field(name="⚔️ Ataque", value=f"+{bonuses['attack']}", inline=True)
        embed.add_field(name="🛡️ Defesa", value=f"+{bonuses['defense']}", inline=True)

        embed.add_field(name="\u200b", value="--- **Equipamento** ---", inline=False)
        embed.add_field(name="Mão Direita", value=equipped_items.get('right_hand_id', 'Vazio'), inline=True)
        embed.add_field(name="Mão Esquerda", value=equipped_items.get('left_hand_id', 'Vazio'), inline=True)
        embed.add_field(name="Capacete", value=equipped_items.get('helmet_id', 'Vazio'), inline=True)
        embed.add_field(name="Peitoral", value=equipped_items.get('chest_id', 'Vazio'), inline=True)
        embed.add_field(name="Pernas", value=equipped_items.get('legs_id', 'Vazio'), inline=True)
        embed.add_field(name="Anel", value=equipped_items.get('ring_id', 'Vazio'), inline=True)

        if character['image_url']:
            embed.set_thumbnail(url=f"{character['image_url']}?t={int(asyncio.get_event_loop().time())}")

        embed.set_footer(text=f"ID do Jogador: {character['user_id']}")
        await ctx.send(embed=embed)

    @commands.command(name="skills", aliases=["habilidades"], help="Mostra as habilidades disponíveis para sua classe e nível.")
    async def show_skills(self, ctx):
        user_id = ctx.author.id
        character = database.get_character(user_id)
        if not character:
            await ctx.send("Você não tem um personagem.")
            return

        skills = database.get_character_skills(character['class'], character['level'])
        if not skills:
            await ctx.send("Você ainda não aprendeu nenhuma habilidade.")
            return

        embed = discord.Embed(title=f"Habilidades de {character['name']} ({character['class']})", color=discord.Color.purple())
        for skill in skills:
            scaling_stat_value = character.get(skill['scaling_stat'], 0)
            total_effect_value = round(skill['base_value'] + (scaling_stat_value * skill['scaling_factor']))
            scaling_stat_pt = ATTRIBUTE_MAP_EN_PT.get(skill['scaling_stat'], "N/A")
            field_value = f"**Custo:** {skill['mp_cost']} MP | **Poder:** {total_effect_value} (Escala com **{scaling_stat_pt}**)\n*{skill['description']}*"
            embed.add_field(name=f"**{skill['name']}** (Nível {skill['min_level']})", value=field_value, inline=False)
        embed.set_footer(text="O poder das habilidades aumenta com seus atributos.")
        await ctx.send(embed=embed)

    @commands.command(name="reset", help="Apaga seu personagem para recomeçar do zero, mantendo o nome.")
    async def reset_character(self, ctx):
        user_id = ctx.author.id
        character = database.get_character(user_id)
        if not character:
            await ctx.send("Você não tem um personagem para resetar.")
            return

        char_name = character['name']
        guild_id = character['guild_id']

        embed = discord.Embed(title="⚠️ ATENÇÃO: Reset de Personagem ⚠️", description=f"Você está prestes a resetar **{char_name}**. **TODA** a sua progressão será **PERMANENTEMENTE APAGADA**.\n\nPara confirmar, digite `resetar meu personagem`.", color=discord.Color.red())
        await ctx.author.send(embed=embed)
        await ctx.send("Enviei uma mensagem de confirmação no seu privado.")

        def check(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel) and m.content.lower() == "resetar meu personagem"

        try:
            await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.author.send("Reset cancelado. Nenhuma alteração foi feita.")
            return

        await ctx.author.send(f"Iniciando o reset para **{char_name}**...")
        
        if character.get('channel_id'):
            old_channel = self.bot.get_channel(character['channel_id'])
            if old_channel:
                try:
                    await old_channel.delete(reason=f"Reset do personagem {char_name}")
                except discord.Forbidden:
                    await ctx.author.send("Não foi possível apagar seu canal antigo. Peça a um administrador para removê-lo.")

        if not database.delete_character_full(user_id):
            await ctx.author.send("Ocorreu um erro ao apagar os dados antigos. Processo abortado.")
            return

        await ctx.author.send("Dados antigos removidos. Agora, vamos recriar seu personagem (o nome será mantido).")
        await asyncio.sleep(2)

        # Re-creation process in DMs
        dm_check = lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel)
        try:
            races_str = ", ".join(RACES)
            await ctx.author.send(f"Escolha sua nova raça: {races_str}")
            race_msg = await self.bot.wait_for("message", check=lambda m: dm_check(m) and m.content.capitalize() in RACES, timeout=60.0)
            char_race = race_msg.content.capitalize()

            classes_str = ", ".join(CLASSES)
            await ctx.author.send(f"Escolha sua nova classe: {classes_str}")
            class_msg = await self.bot.wait_for("message", check=lambda m: dm_check(m) and m.content.capitalize() in CLASSES, timeout=60.0)
            char_class = class_msg.content.capitalize()

            attributes = {attr.capitalize(): MIN_ATTRIBUTE_VALUE for attr in ATTRIBUTE_MAP_PT_EN.keys()}
            remaining_points = TOTAL_ATTRIBUTE_POINTS
            racial_bonus = RACE_MODIFIERS[char_race]

            await ctx.author.send(f"Distribua **{TOTAL_ATTRIBUTE_POINTS}** pontos de atributo (base {MIN_ATTRIBUTE_VALUE}, máx {MAX_ATTRIBUTE_VALUE}).\nEx: `Força 15`")

            while remaining_points > 0:
                await ctx.author.send(f"Pontos restantes: **{remaining_points}**. Atributos: `{attributes}`.")
                attr_input_msg = await self.bot.wait_for("message", check=dm_check, timeout=120.0)
                parts = attr_input_msg.content.split()
                if len(parts) != 2: continue
                
                attr_name, value_str = parts[0].capitalize(), parts[1]
                if attr_name not in attributes or not value_str.isdigit(): continue

                value = int(value_str)
                if not (MIN_ATTRIBUTE_VALUE <= value <= MAX_ATTRIBUTE_VALUE): continue

                attributes[attr_name] = value
                points_spent = sum(v - MIN_ATTRIBUTE_VALUE for v in attributes.values())
                remaining_points = TOTAL_ATTRIBUTE_POINTS - points_spent

            final_attributes = {attr_en: attributes[attr_pt.capitalize()] + racial_bonus.get(attr_en, 0) for attr_pt, attr_en in ATTRIBUTE_MAP_PT_EN.items()}
            hp, mp = self._calculate_hp_mp(final_attributes["constitution"], final_attributes["intelligence"], char_class)

            guild = self.bot.get_guild(guild_id)
            if not guild:
                await ctx.author.send("Não foi possível encontrar o servidor original. Processo falhou.")
                return
                
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            private_channel = await guild.create_text_channel(f'rpg-{char_name.lower().replace(" ", "-")}', overwrites=overwrites)

            success = database.create_character(user_id, guild_id, private_channel.id, char_name, char_race, char_class, **final_attributes, hp=hp, mp=mp)

            if success:
                potion_item = database.get_item_by_name("Poção de Cura Pequena")
                if potion_item:
                    database.add_item_to_inventory(user_id, potion_item['id'], 20)
                
                await ctx.author.send(f"Parabéns, **{char_name}** foi recriado com sucesso! Seu novo canal é {private_channel.mention}")
                general_channel = discord.utils.get(guild.text_channels, name=GENERAL_CHANNEL_NAME)
                if general_channel:
                    await general_channel.send(f"🔄 O aventureiro(a) **{char_name}** decidiu recomeçar sua jornada, renascendo como um(a) {char_race} {char_class}!")
            else:
                await ctx.author.send("Ocorreu um erro ao salvar seu novo personagem. Use `!newchar`.")

        except (asyncio.TimeoutError, ValueError):
            await ctx.author.send("Tempo esgotado ou entrada inválida. Processo de reset falhou. Use `!newchar` para criar um novo personagem.")

    @commands.command(name="migrate", help="Move seu personagem para o servidor atual.")
    async def migrate(self, ctx):
        user_id = ctx.author.id
        destination_guild = ctx.guild
        character = database.get_character(user_id)

        if not character:
            await ctx.send("Você não tem um personagem para migrar.")
            return

        if character['guild_id'] == destination_guild.id:
            await ctx.send("Seu personagem já está neste servidor!")
            return

        embed = discord.Embed(title="⚠️ Confirmação de Migração ⚠️", description=f"Você está prestes a migrar **{character['name']}** para o servidor **'{destination_guild.name}'**.\nSeu canal privado atual será apagado e um novo será criado aqui.\n\nPara confirmar, digite `migrar meu personagem`.", color=discord.Color.orange())
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "migrar meu personagem"

        try:
            await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Migração cancelada.")
            return

        await ctx.send(f"Iniciando a migração para **'{destination_guild.name}'**...")

        if character.get('channel_id'):
            old_channel = self.bot.get_channel(character['channel_id'])
            if old_channel:
                try:
                    await old_channel.delete(reason=f"Migração do personagem {character['name']}")
                except discord.Forbidden:
                    await ctx.send("Não foi possível apagar seu canal antigo. A migração continuará, mas peça a um administrador para removê-lo manualmente.")

        overwrites = {
            destination_guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            destination_guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        try:
            private_channel = await destination_guild.create_text_channel(f'rpg-{character["name"].lower().replace(" ", "-")}', overwrites=overwrites)
        except discord.Forbidden:
            await ctx.send("Não consegui criar seu novo canal privado aqui. A migração falhou.")
            return

        if database.update_character_guild(user_id, destination_guild.id, private_channel.id):
            await ctx.send(f"✅ Migração concluída! Seu personagem **{character['name']}** agora pertence a **'{destination_guild.name}'**.")
            await private_channel.send(f"Bem-vindo(a) ao seu novo lar, {ctx.author.mention}! Sua aventura continua aqui.")
            general_channel = discord.utils.get(destination_guild.text_channels, name=GENERAL_CHANNEL_NAME)
            if general_channel:
                await general_channel.send(f"👋 Um(a) aventureiro(a) experiente chegou! **{character['name']}** migrou para este servidor!")
        else:
            await ctx.send("Ocorreu um erro ao atualizar os dados. A migração falhou.")

async def setup(bot):
    await bot.add_cog(CharacterManagement(bot))