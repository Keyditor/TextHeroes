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
*   `!attribute <atributo> <quantidade>`
    *   **Função**: Distribui os pontos de atributo que você acumulou ao subir de nível.
    *   **Exemplo**: `!attribute força 2`
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

---

### Equipamento

*   `!inventory` ou `!inv`
    *   **Função**: Mostra todos os itens no seu inventário.
    *   **Subcomando**: `!inv clean` - Organiza o inventário, unificando itens empilháveis.
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

### Grupo & Aventura

*   `!party`
    *   **Função**: Gerencia seu grupo de aventureiros.
    *   **Subcomando**: `!party create` - Cria um novo grupo e te torna o líder.
    *   **Subcomando**: `!party invite <@membro>` - Convida um jogador para o seu grupo (apenas líder).
    *   **Subcomando**: `!party accept` - Aceita um convite de grupo pendente.
    *   **Subcomando**: `!party decline` - Recusa um convite de grupo.
    *   **Subcomando**: `!party leave` - Sai do seu grupo atual.
    *   **Subcomando**: `!party kick <@membro>` - Remove um jogador do seu grupo (apenas líder).
    *   **Subcomando**: `!party disband` - Dissolve o grupo (apenas líder).
*   `!dungeon`
    *   **Função**: Gerencia as masmorras.
    *   **Subcomando**: `!dungeon list` - Lista todas as masmorras disponíveis.
    *   **Subcomando**: `!dungeon solo <nome>` - Entra em uma masmorra sozinho (recompensas aumentadas).
    *   **Subcomando**: `!dungeon party <nome>` - Entra em uma masmorra com seu grupo atual (apenas líder).
    *   **Subcomando**: `!dungeon queue <nome>` - Entra na fila para encontrar um grupo aleatório para uma masmorra.
    *   **Subcomando**: `!dungeon leavequeue` - Sai da fila de masmorra.
    *   **Subcomando**: `!dungeon accept` - Aceita uma partida encontrada pela fila.
*   `!pvp`
    *   **Função**: Gerencia duelos entre jogadores.
    *   **Subcomando**: `!pvp challenge [ranked] <nome>` - Desafia outro jogador para um duelo.
    *   **Subcomando**: `!pvp accept` - Aceita um desafio de duelo pendente.
    *   **Subcomando**: `!pvp decline` - Recusa um desafio de duelo pendente.



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