# Guia de Comandos - TextHeroes

Aqui você encontrará uma lista completa de todos os comandos disponíveis no bot TextHeroes.

> **Dica**: Use `!help <comando>` para obter detalhes sobre um comando específico diretamente no Discord.

---

### Personagem

*   `!newchar`
    *   **Função**: Inicia o processo guiado de criação de um novo personagem.
*   `!char`
    *   **Função**: Mostra a ficha básica do seu personagem, incluindo atributos e equipamentos.
    *   **Subcomando**: `!char detail` - Mostra uma ficha detalhada com os cálculos de bônus.
    *   **Subcomando**: `!char img <url>` - Define uma imagem para seu personagem.
*   `!skills`
    *   **Função**: Lista todas as habilidades que seu personagem aprendeu e pode usar em batalha.
*   `!quest`
    *   **Função**: Gerencia suas missões.
    *   **Subcomando**: `!quest list` - Mostra as missões diárias e semanais disponíveis.
    *   **Subcomando**: `!quest myquests` - Mostra suas missões ativas e o progresso.
    *   **Subcomando**: `!quest accept <ID>` - Aceita uma missão do quadro.
    *   **Subcomando**: `!quest complete <ID>` - Entrega uma missão finalizada para receber as recompensas.
*   `!bestiary`
    *   **Função**: Mostra os inimigos que você pode encontrar em caçadas aleatórias e os que pode caçar diretamente.
*   `!market`
    *   **Função**: Abre a interface do mercado de jogadores.
    *   **Subcomando**: `!market sell <preço> [qtd] <item>` - Anuncia um item para venda.
    *   **Subcomando**: `!market buy <ID> [qtd]` - Compra um item de um anúncio.
    *   **Subcomando**: `!market remove <ID>` - Remove um de seus anúncios.
    *   **Subcomando**: `!market search <item>` - Pesquisa por um item específico no mercado.
*   `!reset`
    *   **Função**: Apaga completamente seu personagem atual para que você possa recomeçar do zero.

---

### Ação

*   `!hunt [nome do inimigo]`
    *   **Função**: Inicia uma batalha manual. Se um nome de inimigo for fornecido, tenta caçar aquele inimigo específico (requer nível superior ao do monstro).
*   `!autohunt [nome do inimigo]`
    *   **Função**: Inicia uma batalha automática para farm. Também suporta caça direcionada.
*   `!use [qtd] <item>`
    *   **Função**: Usa um item consumível do seu inventário.
*   `!shop`
    *   **Função**: Abre a interface da loja do jogo.
    *   **Subcomando**: `!shop buy [qtd] <item>` - Compra um item da loja.
    *   **Subcomando**: `!shop sell [qtd] <item>` - Vende um item do seu inventário para a loja.

---

### Equipamento

*   `!inventory` ou `!inv`
    *   **Função**: Mostra todos os itens no seu inventário.
*   `!equip <ID do item>`
    *   **Função**: Equipa um item do seu inventário. Use o ID que aparece no `!inventory`.
*   `!unequip <slot>`
    *   **Função**: Desequipa um item de um slot específico (ex: `!unequip capacete`).
*   `!enhance <nome do item>`
    *   **Função**: Tenta aprimorar um equipamento, consumindo 2 itens base e uma gema.