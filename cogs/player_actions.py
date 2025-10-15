import discord
from discord.ext import commands
import database

class PlayerActions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="inventory", aliases=["inv"], help="Mostra os itens no seu inventário.")
    async def inventory(self, ctx):
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

    @commands.command(name="use", help="Usa um item consumível do seu inventário.")
    async def use_item(self, ctx, *args):
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

    @commands.command(name="enhance", aliases=["aprimorar"], help="Aprimora um equipamento.")
    async def enhance(self, ctx, *, item_name: str):
        user_id = ctx.author.id
        if not database.get_character(user_id):
            await ctx.send("Você precisa de um personagem para aprimorar itens.")
            return

        inventory = database.get_inventory(user_id)
        item_to_enhance_data = None
        for item_data in inventory:
            if item_name.lower() in item_data[3].lower() and item_data[9] == 0:
                item_to_enhance_data = item_data
                break
        
        if not item_to_enhance_data:
            await ctx.send(f"Item '{item_name}' não encontrado no seu inventário ou não é um item base (+0).")
            return

        inv_id, item_id, quantity, name, _, item_type, _, _, equip_slot, enhancement_level = item_to_enhance_data

        if item_type not in ['weapon', 'armor']:
            await ctx.send(f"**{name}** não é um item aprimorável.")
            return

        if enhancement_level >= 13:
            await ctx.send(f"**{name} +{enhancement_level}** já está no nível máximo de aprimoramento.")
            return

        if quantity < 2:
            await ctx.send(f"Você precisa de pelo menos 2x **{name} +{enhancement_level}** para tentar o aprimoramento.")
            return

        if item_type == 'weapon':
            gem_name = "Gema de Arma"
        elif item_type == 'armor' and equip_slot == 'ring':
            gem_name = "Gema de Acessório"
        else:
            gem_name = "Gema de Armadura"

        gem_item = database.get_item_by_name(gem_name)
        if not gem_item:
            await ctx.send(f"Erro de sistema: {gem_name} não encontrada na base de dados.")
            return

        gem_in_inventory = next((item for item in inventory if item[1] == gem_item['id']), None)
        if not gem_in_inventory:
            await ctx.send(f"Você não possui a **{gem_name}** necessária para o aprimoramento.")
            return

        database.remove_item_from_inventory(user_id, item_id, 2, enhancement_level=0)
        database.remove_item_from_inventory(user_id, gem_item['id'], 1)
        database.add_item_to_inventory(user_id, item_id, 1, enhancement_level + 1)

        new_name = f"{name} +{enhancement_level + 1}"
        await ctx.send(f"✨ **SUCESSO!** ✨\nVocê aprimorou seu equipamento e criou uma **{new_name}**!")

    @commands.command(name="equip", help="Equipa um item do seu inventário.")
    async def equip(self, ctx, *, item_name: str):
        user_id = ctx.author.id
        if not database.get_character(user_id):
            await ctx.send("Você precisa de um personagem para equipar itens.")
            return

        inventory = database.get_inventory(user_id)
        
        try:
            inv_id_to_equip = int(item_name)
            item_to_equip_data = next((item for item in inventory if item[0] == inv_id_to_equip), None)
        except ValueError:
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

    @commands.command(name="unequip", help="Desequipa um item.")
    async def unequip(self, ctx, *, slot_name: str):
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

        # A função unequip do DB agora não adiciona de volta, apenas limpa o slot.
        # A lógica de "devolver" foi removida pois o item nunca sai do inventário.
        if database.unequip_item(user_id, db_slot):
            await ctx.send(f"Você desequipou **{item_name}**. O item permanece em seu inventário.")
        else:
            await ctx.send("Ocorreu um erro ao desequipar o item.")

async def setup(bot):
    await bot.add_cog(PlayerActions(bot))