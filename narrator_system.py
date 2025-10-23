# e:\PYPROJECTS\RPG-DISCORD\narrator_system.py
import discord
import json
import asyncio
import re
from openai import AsyncOpenAI

import database
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
from battle_system import PVEBattle

# Inicializa o cliente da OpenAI
# Certifique-se de que a variável de ambiente ou a chave em config.py está definida
client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

class NarrativeSession:
    def __init__(self, bot_instance, player_char):
        self.bot = bot_instance
        self.player = player_char
        self.user_id = player_char['user_id']
        self.is_complete = False
        self.pending_enemy = None
        self.history = database.get_narrative_history(self.user_id)

        if not self.history:
            self.history = []
            self._initialize_prompt()
        else:
            # Verifica se há um resultado de batalha recente não processado
            last_battle_result = self.bot.last_battle_results.pop(self.user_id, None)
            
            continue_prompt = f"A aventura de {self.player['name']} continua."
            
            if last_battle_result:
                # Adiciona o evento recente ao contexto da IA
                continue_prompt += f" Evento recente importante: {last_battle_result}. Leve isso em consideração ao iniciar a narração."
            
            continue_prompt += " Lembre-se de tudo que aconteceu antes e prossiga a jornada."

            self.history.append({"role": "system", "content": continue_prompt})

    def _initialize_prompt(self):
        """Define o comportamento inicial do Mestre de Jogo (IA)."""
        system_prompt = f"""
        Você é o Mestre de Jogo do 'TextHeroes', um RPG de texto no Discord.
        Seu papel é criar e narrar uma aventura curta e única para o jogador.

        Jogador:
        - Nome: {self.player['name']}
        - Raça: {self.player['race']}
        - Classe: {self.player['class']}
        - Nível: {self.player['level']}

        Regras de Interação:
        1.  Comece a aventura com uma introdução cativante.
        2.  Descreva cenários e termine sempre perguntando ao jogador: "O que você faz?".
        3.  Mantenha as respostas curtas e diretas (2-3 parágrafos).
        4.  Para acionar eventos no jogo, use as seguintes tags ESPECIAIS no final da sua resposta:
            - `[BATTLE:NomeDoInimigo]` para iniciar um combate. Use inimigos que existem no jogo, como 'Goblin', 'Lobo', 'Esqueleto'.
            - `[REWARD:XP=valor,GOLD=valor]` para dar recompensas. Ex: `[REWARD:XP=50,GOLD=25]`.
            - `[CREATE_ITEM:name="Nome",description="Desc.",type="weapon/armor",slot="right_hand/chest",attack=5,defense=1,rarity="unique"]` para criar um item único. Pondere o poder do item com base nos feitos do jogador. Itens criados devem ter `rarity="unique"`.
            - `[END]` para terminar a aventura de forma conclusiva.

        Exemplo de resposta:
        "Você encontra uma clareira com uma fogueira apagada. Há pegadas de goblin por toda parte. Um som de galho quebrando vem da floresta à sua direita. O que você faz?
        [BATTLE:Goblin]". Após esta tag, o jogador decidirá quando atacar.

        Comece a aventura agora.
        """
        self.history.append({"role": "system", "content": system_prompt})

    async def _summarize_history(self):
        """Resume o histórico se ele ficar muito longo para economizar tokens."""
        # Um resumo é acionado quando o histórico tem mais de 10 trocas (20 mensagens)
        if len(self.history) > 20:
            print(f"Resumindo histórico para o jogador {self.user_id}...")
            summary_prompt = "Resuma a conversa a seguir em um parágrafo conciso, capturando os eventos e decisões mais importantes do jogador. Este resumo será usado como memória para continuar a aventura."
            
            # Pega o histórico antigo, excluindo a última interação do sistema
            history_to_summarize = self.history[:-1]

            try:
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": summary_prompt},
                        {"role": "user", "content": json.dumps(history_to_summarize)}
                    ],
                    temperature=0.3
                )
                summary = response.choices[0].message.content
                # Substitui o histórico antigo pelo prompt inicial + resumo
                self._initialize_prompt() # Recria o prompt do sistema
                self.history.append({"role": "system", "content": f"Memória da aventura até agora: {summary}"})
                print(f"Histórico para {self.user_id} resumido com sucesso.")
            except Exception as e:
                print(f"Falha ao resumir o histórico: {e}")

    async def get_ai_response(self, custom_prompt=None):
        """Envia o histórico para a API da OpenAI e obtém a próxima narração."""
        messages_to_send = self.history
        if custom_prompt:
            # Cria uma cópia para não modificar o histórico original da sessão
            messages_to_send = self.history + [{"role": "system", "content": custom_prompt}]

        try:
            response = await client.chat.completions.create(
                model=OPENAI_MODEL, # Usa o modelo do arquivo de configuração
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=400
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Erro na API da OpenAI: {e}")
            return "O Mestre parece confuso e não consegue continuar a história. A aventura termina abruptamente. [END]"

    async def get_action_tags_for_narration(self, narration):
        """Pede à IA para gerar apenas as tags de ação com base na narração fornecida."""
        tag_prompt = f"""
        Baseado na seguinte narração que você acabou de criar:
        ---
        {narration}
        ---
        Gere APENAS as tags de ação apropriadas (como [BATTLE:...], [CREATE_ITEM:...], [REWARD:...], [END]).
        Se nenhuma ação especial for necessária, não retorne nada.
        Lembre-se da estrutura da tag de criação de item: `[CREATE_ITEM:name="...",description="...",type="...",slot="...",attack=...,defense=...,rarity="unique"]`.
        """
        try:
            # Chamada de API mais leve, sem o histórico completo, para focar na geração da tag.
            response = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "system", "content": tag_prompt}],
                temperature=0.2, # Menos criatividade, mais precisão na formatação da tag
                max_tokens=200 # 200 tokens é mais que suficiente para uma tag complexa.
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Erro ao gerar tags de ação: {e}")
            return "" # Retorna vazio em caso de erro

    def parse_actions(self, text):
        """Extrai ações especiais (tags) e o texto da narração."""
        narration = re.sub(r'\[.*?\]', '', text).strip()
        actions = re.findall(r'\[(.*?)\]', text)
        return narration, actions

    async def handle_action(self, action_str, ctx):
        """Processa uma ação extraída da resposta da IA."""
        action_type, _, params = action_str.partition(':')
        
        if action_type.upper() == 'BATTLE':
            enemy_name = params
            enemy = database.get_enemy_by_name(enemy_name)
            if not enemy:
                await ctx.send(f"(O Mestre tentou invocar um '{enemy_name}', mas a criatura não existe neste mundo. A aventura continua...)")
                return True
            
            self.pending_enemy = enemy
            await ctx.send(f"⚔️ **Ameaça iminente!** Um **{enemy['name']}** está à sua frente. Você pode `atacar` para iniciar o combate ou descrever outra ação.")
            return True # Continua o loop, aguardando a ação do jogador

        elif action_type.upper() == 'REWARD':
            updates = {}
            xp_reward = re.search(r'XP=(\d+)', params, re.IGNORECASE)
            gold_reward = re.search(r'GOLD=(\d+)', params, re.IGNORECASE)
            
            reward_msgs = []
            if xp_reward:
                xp = int(xp_reward.group(1))
                updates['experience'] = self.player['experience'] + xp
                reward_msgs.append(f"✨ **{xp}** XP")
            if gold_reward:
                gold = int(gold_reward.group(1))
                updates['gold'] = self.player['gold'] + gold
                reward_msgs.append(f"💰 **{gold}** Ouro")

            if updates:
                database.update_character_stats(self.player['user_id'], updates)
                self.player = database.get_character(self.user_id) # Atualiza o estado do jogador
                await ctx.send(f"🎁 **Recompensa recebida:** {', '.join(reward_msgs)}!")
        
        elif action_type.upper() == 'CREATE_ITEM':
            try:
                # Analisa os parâmetros como um dicionário
                item_params = dict(re.findall(r'(\w+)="([^"]*)"', params))
                
                # Converte valores numéricos
                for key in ['attack', 'defense']:
                    if key in item_params:
                        item_params[key] = int(item_params[key])
                
                # Renomeia chaves para corresponder ao banco de dados
                if 'attack' in item_params: item_params['attack_bonus'] = item_params.pop('attack')
                if 'defense' in item_params: item_params['defense_bonus'] = item_params.pop('defense')
                if 'slot' in item_params: item_params['equip_slot'] = item_params.pop('slot')
                if 'type' in item_params: item_params['item_type'] = item_params.pop('type')

                item_id = database.create_loot_item(item_params)
                if item_id:
                    database.add_item_to_inventory(self.user_id, item_id, 1)
                    await ctx.send(f"✨ **Artefato Conquistado!** ✨\nVocê obteve **{item_params['name']}** e o guardou em seu inventário.")
                else:
                    await ctx.send("(O Mestre tentou forjar um item, mas a magia falhou.)")

            except Exception as e:
                print(f"Erro ao processar a tag CREATE_ITEM: {e} | Parâmetros: {params}")
                await ctx.send("(A energia da criação se dissipa de forma instável. O item não pôde ser formado.)")

        elif action_type.upper() == 'END':
            self.is_complete = True
            await ctx.send("A aventura chegou ao fim.")
            return False

        return True # Continua o loop

    async def run(self, ctx):
        """Loop principal da sessão de narração."""
        # Garante que a sessão seja salva no final
        try:
            await self._run_loop(ctx)
        finally:
            await self._summarize_history()
            database.save_narrative_history(self.user_id, self.history)
            print(f"Histórico de narração para {self.user_id} foi salvo.")

    async def _run_loop(self, ctx):
        # Primeira mensagem da IA
        ai_message = await self.get_ai_response()
        self.history.append({"role": "assistant", "content": ai_message})
        narration, actions = self.parse_actions(ai_message)
        
        if narration:
            await ctx.send(narration)

        for action in actions:
            if not await self.handle_action(action, ctx):
                return # Termina a sessão se a ação indicar

        while not self.is_complete:
            try:
                player_msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == self.user_id and m.channel == ctx.channel and not m.content.startswith('!'),
                    timeout=300.0 # 5 minutos para responder
                )

                # Verifica se o jogador quer iniciar um combate pendente
                if self.pending_enemy and player_msg.content.lower().strip() == 'atacar':
                    await ctx.send(f"**Você avança para o ataque!** A narração é interrompida por um combate!")
                    battle = PVEBattle(self.bot, self.player, self.pending_enemy, self.pending_enemy['name'], is_autohunt=False, is_elite=False, battle_manager=self.bot.active_pve_battles)
                    self.bot.active_pve_battles[self.user_id] = battle
                    await battle.run_manual_loop(ctx)
                    # A aventura termina após a batalha para simplificar
                    self.is_complete = True
                    break

                self.pending_enemy = None # Qualquer outra ação cancela o combate iminente
                self.history.append({"role": "user", "content": player_msg.content})

                async with ctx.typing():
                    # Etapa 1: Gerar a narração
                    narration_only = await self.get_ai_response()
                    
                    # Etapa 2: Gerar as tags com base na narração
                    tags_only = await self.get_action_tags_for_narration(narration_only)
                
                # Combina a narração e as tags para manter o histórico consistente
                full_ai_response = f"{narration_only.strip()} {tags_only.strip()}"
                self.history.append({"role": "assistant", "content": full_ai_response})
                narration, actions = self.parse_actions(full_ai_response)

                if narration:
                    await ctx.send(narration)
                
                should_continue = True
                for action in actions:
                    if not await self.handle_action(action, ctx):
                        should_continue = False
                        break
                if not should_continue:
                    break

            except asyncio.TimeoutError:
                await ctx.send("O Mestre se cansa de esperar e a névoa da aventura se dissipa. A sessão terminou.")
                self.is_complete = True
