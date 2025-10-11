# TextHeroes ⚔️

Bem-vindo ao **TextHeroes**! Um bot de RPG de texto completo e de código aberto para Discord, projetado para ser uma base robusta para suas próprias aventuras. Crie personagens, lute contra monstros, colete itens, negocie com outros jogadores e muito mais!

Este projeto foi criado com a intenção de ser um ponto de partida para desenvolvedores e entusiastas de RPG que desejam criar sua própria experiência de jogo no Discord.

## Funcionalidades

*   **Criação de Personagem**: Sistema completo com raças, classes e distribuição de atributos.
*   **Combate Tático**: Batalhas por turnos com opções de ataque, defesa, habilidades e uso de itens.
*   **Progressão**: Ganho de XP, sistema de níveis e distribuição de pontos de atributo.
*   **Inimigos Variados**: Um bestiário com mais de 45 inimigos, incluindo monstros de **Elite** com recompensas maiores.
*   **Sistema de Itens**: Diversos tipos de itens, incluindo armas, armaduras, consumíveis e materiais.
*   **Aprimoramento de Equipamentos**: Melhore seus equipamentos até +13 usando gemas especiais.
*   **Economia**: Lojas para compra/venda e um mercado completo entre jogadores.
*   **Missões**: Sistema de quests diárias e semanais com recompensas variadas.

## Expansão de Conteúdo

Os itens, inimigos, quests e habilidades podem ser adicionados inserindo novas linhas no banco de dados `rpg_data.db`. Para fazer isso, você pode utilizar um editor de banco de dados SQLite.

Siga o [**Guia de Expansão**](https://github.com/Keyditor/TextHeroes/blob/main/EXPANSION.md) caso tenha duvidas.

## Configuração

Para rodar o TextHeroes no seu próprio servidor, siga estes passos:

1.  **Clone o Repositório**
    ```bash
    git clone https://github.com/Keyditor/TextHeroes-RPG-BOT.git
    cd TextHeroes-RPG-BOT
    ```

2.  **Instale as Dependências**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Crie o Arquivo de Configuração**

    Crie um arquivo chamado `config.py` na raiz do projeto e adicione as seguintes linhas, substituindo os valores conforme necessário:

    ```python
    # Substitua pelo token do seu bot, obtido no Portal de Desenvolvedores do Discord.
    DISCORD_BOT_TOKEN = "SEU_TOKEN_AQUI"
    
    # Nome do canal de texto onde os anúncios globais (como criação de personagem) serão feitos.
    GENERAL_CHANNEL_NAME = "geral"
    ```

4.  **Execute o Bot**
    ```bash
    python main.py
    ```

## Comandos do Jogo

Para uma lista completa de todos os comandos disponíveis e como usá-los, por favor, consulte nosso **Guia de Comandos**.

## Licença e Créditos

Este projeto é de código aberto e pode ser livremente utilizado como base para outros bots de RPG. A única condição é a manutenção do comando `!gm`, que atribui os devidos créditos ao criador original.

*   **Criador**: @Keyditor
*   **Repositório**: TextHeroes no GitHub
