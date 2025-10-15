# Guia de Comandos - TextHeroes

Aqui você encontrará uma lista completa de todos os comandos disponíveis no bot TextHeroes.

> **Dica**: Use `!help <comando>` para obter detalhes sobre um comando específico diretamente no Discord.

---

### Personagem

*   `!newchar`
    *   **Função**: Inicia o processo guiado de criação de um novo personagem.
*   `!char`
    *   **Função**: Mostra a ficha do seu personagem, incluindo atributos e equipamentos.
    *   **Subcomando**: `!char img <url>` - Define uma imagem para seu personagem.
*   `!skills`
    *   **Função**: Lista todas as habilidades que seu personagem aprendeu e pode usar em batalha.
*   `!reset`
    *   **Função**: Apaga completamente seu personagem atual para que você possa recomeçar do zero.
*   `!migrate`
    *   **Função**: Move seu personagem para o servidor atual onde o comando é executado.

---

### Ação

*   `!hunt [nome do inimigo]`
    *   **Função**: Inicia uma batalha manual. Se um nome de inimigo for fornecido, tenta caçar aquele inimigo específico (requer nível superior ao do monstro).
*   `!autohunt [nome do inimigo]`
    *   **Função**: Inicia uma batalha automática para farm. Também suporta caça direcionada.
*   `!use [qtd] <item>`
    *   **Função**: Usa um item consumível do seu inventário.
*   `!pvp`
    *   **Função**: Gerencia duelos entre jogadores.
    *   **Subcomando**: `!pvp challenge [ranked] <nome>` - Desafia outro jogador para um duelo.
    *   **Subcomando**: `!pvp accept` - Aceita um desafio de duelo pendente.
    *   **Subcomando**: `!pvp decline` - Recusa um desafio de duelo pendente.

---

### Equipamento

*   `!inventory` ou `!inv`
    *   **Função**: Mostra todos os itens no seu inventário.
*   `!equip <ID ou nome do item>`
    *   **Função**: Equipa um item do seu inventário.
*   `!unequip <slot>`
    *   **Função**: Desequipa um item de um slot específico (ex: `!unequip capacete`).
*   `!enhance <nome do item>`
    *   **Função**: Tenta aprimorar um equipamento, consumindo 2 itens base e uma gema.

---

### Interação

*   `!shop`
    *   **Função**: Abre a interface da loja do jogo.
    *   **Subcomando**: `!shop buy [qtd] <item>` - Compra um item da loja.
    *   **Subcomando**: `!shop sell [qtd] <item>` - Vende um item do seu inventário para a loja.
*   `!market`
    *   **Função**: Abre a interface do mercado de jogadores.
    *   **Subcomando**: `!market sell <preço> [qtd] <item>` - Anuncia um item para venda.
    *   **Subcomando**: `!market buy <ID> [qtd]` - Compra um item de um anúncio.
    *   **Subcomando**: `!market remove <ID>` - Remove um de seus anúncios.
    *   **Subcomando**: `!market search <item>` - Pesquisa por um item específico no mercado.
*   `!job`
    *   **Função**: Gerencia sua profissão para ganhar ouro.
    *   **Subcomando**: `!job list` - Mostra as profissões disponíveis.
    *   **Subcomando**: `!job status` - Mostra sua ficha de profissão e ganhos pendentes.
    *   **Subcomando**: `!job select <ID>` - Escolhe uma nova profissão.
    *   **Subcomando**: `!job quit` - Abandona sua profissão atual.
*   `!work`
    *   **Função**: "Bate o ponto" no seu trabalho para acumular horas e continuar ganhando ouro.
*   `!payday`
    *   **Função**: Coleta seu salário acumulado. Pode ser usado uma vez por dia.

---

### Utilidade

*   `!quest`
    *   **Função**: Gerencia suas missões.
    *   **Subcomando**: `!quest list` - Mostra as missões diárias e semanais disponíveis.
    *   **Subcomando**: `!quest myquests` - Mostra suas missões ativas e o progresso.
    *   **Subcomando**: `!quest accept <ID>` - Aceita uma missão do quadro.
    *   **Subcomando**: `!quest complete <ID>` - Entrega uma missão finalizada para receber as recompensas.
*   `!bestiary`
    *   **Função**: Mostra os inimigos que você pode encontrar em caçadas aleatórias e os que pode caçar diretamente.
*   `!leaderboard [level/pvp]`
    *   **Função**: Mostra os rankings do servidor por nível ou por vitórias em PvP.
*   `!gm`
    *   **Função**: Mostra os créditos do criador do bot.