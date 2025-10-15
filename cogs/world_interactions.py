import discord
from discord.ext import commands
from datetime import datetime, timedelta
import database

# As classes de View precisam ser movidas para cá também
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

class MarketView(discord.ui.View):
    def __init__(self, author_id, search_term=None):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.current_page = 1
        self.search_term = search_term
        self.total_pages = 0

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
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

class WorldInteractions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="work", aliases=["trabalhar"], help="Bate o ponto no seu trabalho para acumular horas.")
    async def work(self, ctx):
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player or not player.get('current_job_id'):
            await ctx.send("Você precisa de um emprego para poder trabalhar. Use `!job list`.")
            return

        last_check_in_str = player.get('last_work_check_in')
        if not last_check_in_str:
            database.update_character_stats(user_id, {'last_work_check_in': datetime.now().isoformat()})
            await ctx.send("Seu ponto foi registrado pela primeira vez. Use `!work` novamente em breve para acumular horas.")
            return

        last_check_in = datetime.fromisoformat(last_check_in_str)
        time_since_check_in = datetime.now() - last_check_in
        
        hours_to_credit = min(time_since_check_in.total_seconds() / 3600, 3)

        if hours_to_credit < (1/60):
            await ctx.send("Você acabou de bater o ponto. Volte mais tarde para acumular mais tempo.")
            return

        database.update_player_job_progress(user_id, player['current_job_id'], hours_to_credit)
        database.update_character_stats(user_id, {'last_work_check_in': datetime.now().isoformat()})

        await ctx.send(f"✅ Ponto batido! Você acumulou mais **{hours_to_credit:.2f}** horas de trabalho. Continue usando `!work` a cada 3 horas para não perder o progresso.")

    @commands.group(name="job", aliases=["emprego", "profissao"], help="Gerencia sua profissão para ganhar ouro passivamente.", invoke_without_command=True)
    async def job(self, ctx):
        await self.job_status(ctx)

    @job.command(name="list", help="Lista todos os empregos disponíveis.")
    async def job_list(self, ctx):
        jobs = database.get_all_jobs()
        player = database.get_character(ctx.author.id)

        embed = discord.Embed(title="🏢 Empregos Disponíveis 🏢", description="Escolha uma profissão para ganhar ouro enquanto estiver offline.", color=discord.Color.dark_blue())
        
        for j in jobs:
            unlocked = "✅" if player and player['level'] >= j['level_req'] else "🔒"
            embed.add_field(
                name=f"{unlocked} ID: `{j['id']}` - {j['name']} (Nível {j['level_req']}+)",
                value=f"*{j['description']}*\n**Salário:** {j['gold_per_hour']} Ouro/hora",
                inline=False
            )
        embed.set_footer(text="Use `!job select <ID>` para começar a trabalhar.")
        await ctx.send(embed=embed)

    @job.command(name="status", help="Mostra seu status de emprego atual.")
    async def job_status(self, ctx):
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player:
            await ctx.send("Você precisa de um personagem para ter um emprego.")
            return

        if not player.get('current_job_id'):
            await ctx.send("Você está desempregado. Use `!job list` para ver as vagas.")
            return

        job_info = database.get_job_by_id(player['current_job_id'])
        
        accumulated_hours = database.get_player_job_progress(user_id, job_info['id'])
        pending_payment = int(accumulated_hours * job_info['gold_per_hour'])

        embed = discord.Embed(title=f"💼 Status de Emprego - {player['name']} 💼", color=discord.Color.green())
        embed.add_field(name="Profissão Atual", value=job_info['name'], inline=False)
        embed.add_field(name="Horas Acumuladas", value=f"⏳ {accumulated_hours:.2f} horas", inline=True)
        embed.add_field(name="Pagamento Pendente", value=f"💰 **{pending_payment}** Ouro", inline=True)
        embed.set_footer(text="Use `!work` a cada 3h para acumular horas e `!payday` para coletar seu pagamento (uma vez por dia).")
        await ctx.send(embed=embed)

    @job.command(name="select", help="Escolhe um novo emprego. Uso: !job select <ID>")
    async def job_select(self, ctx, job_id: int):
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player:
            await ctx.send("Você precisa de um personagem para conseguir um emprego.")
            return

        if player.get('last_job_change'):
            last_change = datetime.fromisoformat(player['last_job_change'])
            if datetime.now() < last_change + timedelta(days=1):
                await ctx.send(f"Você só pode trocar de emprego uma vez por dia. Tente novamente após {last_change + timedelta(days=1):%d/%m/%Y às %H:%M}.")
                return

        job_to_select = database.get_job_by_id(job_id)
        if not job_to_select:
            await ctx.send("ID de emprego inválido.")
            return

        if player['level'] < job_to_select['level_req']:
            await ctx.send(f"Você não tem o nível necessário para este emprego. Requer nível {job_to_select['level_req']}.")
            return

        if player.get('current_job_id'):
            await self.job_quit(ctx, from_select=True)

        if database.set_player_job(user_id, job_id):
            await ctx.send(f"Parabéns! Você foi contratado como **{job_to_select['name']}**. Seu turno começa agora! Use `!work` para bater o ponto.")
        else:
            await ctx.send("Ocorreu um erro ao tentar conseguir o emprego.")

    @job.command(name="quit", help="Abandona seu emprego atual.")
    async def job_quit(self, ctx, from_select: bool = False):
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player or not player.get('current_job_id'):
            if not from_select: await ctx.send("Você não tem um emprego para abandonar.")
            return

        await self.payday(ctx, from_quit=True)

        job_info = database.get_job_by_id(player['current_job_id'])
        database.reset_player_job_progress(user_id, player['current_job_id'])
        database.set_player_job(user_id, None)
        if not from_select:
            await ctx.send(f"Você abandonou seu posto de **{job_info['name']}**.")

    @commands.command(name="payday", help="Coleta seu salário. Disponível uma vez por dia.")
    async def payday(self, ctx, from_quit: bool = False):
        user_id = ctx.author.id
        player = database.get_character(user_id)
        if not player or not player.get('current_job_id'):
            await ctx.send("Você precisa de um emprego para receber um salário.")
            return

        if not from_quit and player.get('last_payday'):
            last_payment = datetime.fromisoformat(player['last_payday'])
            if datetime.now() < last_payment + timedelta(days=1):
                await ctx.send(f"Você já coletou seu pagamento hoje. Próximo pagamento disponível após {last_payment + timedelta(days=1):%d/%m/%Y às %H:%M}.")
                return

        job_info = database.get_job_by_id(player['current_job_id'])

        last_check_in = datetime.fromisoformat(player['last_work_check_in'])
        time_since_check_in = datetime.now() - last_check_in
        final_hours_to_credit = min(time_since_check_in.total_seconds() / 3600, 3)
        database.update_player_job_progress(user_id, player['current_job_id'], final_hours_to_credit)

        accumulated_hours = database.get_player_job_progress(user_id, player['current_job_id'])
        payment = int(accumulated_hours * job_info['gold_per_hour'])

        if payment <= 0:
            await ctx.send("Você não acumulou horas suficientes para receber um pagamento. Use `!work` para trabalhar.")
            return

        database.update_character_stats(user_id, {'gold': player['gold'] + payment, 'last_payday': datetime.now().isoformat(), 'last_work_check_in': datetime.now().isoformat()})
        database.reset_player_job_progress(user_id, player['current_job_id'])

        await ctx.send(f"💰 **DIA DE PAGAMENTO!** 💰\nVocê recebeu **{payment}** de ouro por **{accumulated_hours:.2f}** horas de trabalho acumuladas!")

    @commands.group(name="shop", help="Abre a loja para comprar ou vender itens.", invoke_without_command=True)
    async def shop(self, ctx):
        user_id = ctx.author.id
        if not database.get_character(user_id):
            await ctx.send("Você precisa de um personagem para acessar a loja.")
            return

        view = ShopView(user_id)
        embed = await view.format_shop_embed()
        await ctx.send(embed=embed, view=view)

    @shop.command(name="buy", help="Compra um item da loja.")
    async def shop_buy(self, ctx, *args):
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
    async def shop_sell(self, ctx, *args):
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
        item_to_sell_data = next((item for item in inventory if item_name.lower() in item[3].lower()), None)
        
        if not item_to_sell_data:
            await ctx.send(f"Você não possui o item '{item_name}' para vender.")
            return

        inv_id, item_id, inv_quantity, name, _, _, _, _, _, enhancement_level = item_to_sell_data
        item_details = database.get_item_by_id(item_id)

        if inv_quantity < quantity:
            await ctx.send(f"Você não tem itens suficientes para vender. Você possui apenas {inv_quantity}x **{name}**.")
            return

        unit_sell_price = round(item_details['value'] * 0.7)
        unit_sell_price += round(item_details['value'] * 1.75 * enhancement_level)

        if unit_sell_price <= 0:
            await ctx.send(f"O item **{name}** não tem valor de venda.")
            return

        total_gain = unit_sell_price * quantity

        if database.remove_item_from_inventory(user_id, item_id, quantity, enhancement_level=enhancement_level):
            database.update_character_stats(user_id, {"gold": character['gold'] + total_gain})
            await ctx.send(f"Você vendeu {quantity}x **{name}** por {total_gain} de ouro!")
        else:
            await ctx.send("Erro ao vender o item.")

    @commands.group(name="market", aliases=["mercado"], help="Acessa o mercado de jogadores.", invoke_without_command=True)
    async def market(self, ctx):
        view = MarketView(ctx.author.id)
        embed = await view.format_market_embed()
        await ctx.send(embed=embed, view=view)

    @market.command(name="sell", help="Anuncia um item no mercado. Uso: !market sell <preço> [quantidade] <nome do item>")
    async def market_sell(self, ctx, price: int, *args):
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

        inventory = database.get_inventory(user_id)
        item_to_sell_data = next((item for item in inventory if item_name.lower() in item[3].lower()), None)

        if not item_to_sell_data:
            await ctx.send(f"Você não possui o item '{item_name}'.")
            return

        inv_id, item_id, inv_quantity, name, _, _, _, _, _, enhancement_level = item_to_sell_data

        if inv_quantity < quantity:
            await ctx.send(f"Você tem apenas {inv_quantity}x de {name} para vender.")
            return

        if database.remove_item_from_inventory(user_id, item_id, quantity, enhancement_level):
            listing_id = database.create_market_listing(user_id, item_id, quantity, price, enhancement_level)
            display_name = f"{name} +{enhancement_level}" if enhancement_level > 0 else name
            await ctx.send(f"✅ Você anunciou **{quantity}x {display_name}** no mercado por **{price}** ouro cada. (ID do Anúncio: `{listing_id}`)")
        else:
            await ctx.send("Erro ao remover o item do inventário para venda.")

    @market.command(name="buy", help="Compra um item do mercado. Uso: !market buy <ID do anúncio> [quantidade]")
    async def market_buy(self, ctx, listing_id: int, quantity: int = 1):
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

        seller = database.get_character(listing['seller_id'])
        database.update_character_stats(listing['seller_id'], {'gold': seller['gold'] + total_cost})
        database.update_character_stats(user_id, {'gold': buyer['gold'] - total_cost})
        database.add_item_to_inventory(user_id, listing['item_id'], quantity, listing['enhancement_level'])
        
        if quantity == listing['quantity']:
            database.remove_market_listing(listing_id)
        else:
            database.remove_market_listing(listing_id)
            database.create_market_listing(listing['seller_id'], listing['item_id'], listing['quantity'] - quantity, listing['price'], listing['enhancement_level'])

        item_info = database.get_item_by_id(listing['item_id'])
        await ctx.send(f"🛍️ Você comprou **{quantity}x {item_info['name']}** por **{total_cost}** ouro!")

    @market.command(name="remove", help="Remove um de seus anúncios do mercado. Uso: !market remove <ID do anúncio>")
    async def market_remove(self, ctx, listing_id: int):
        user_id = ctx.author.id
        listing = database.get_market_listing_by_id(listing_id)

        if not listing or listing['seller_id'] != user_id:
            await ctx.send("Anúncio não encontrado ou você não é o vendedor.")
            return

        database.add_item_to_inventory(user_id, listing['item_id'], listing['quantity'], listing['enhancement_level'])
        database.remove_market_listing(listing_id)

        item_info = database.get_item_by_id(listing['item_id'])
        await ctx.send(f"Anúncio de **{listing['quantity']}x {item_info['name']}** removido. O item voltou para seu inventário.")

    @market.command(name="search", help="Pesquisa por um item no mercado. Uso: !market search <nome do item>")
    async def market_search(self, ctx, *, item_name: str):
        view = MarketView(ctx.author.id, search_term=item_name)
        embed = await view.format_market_embed()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(WorldInteractions(bot))