# Guia de Expansão - TextHeroes

Este guia detalha como adicionar novo conteúdo (inimigos, itens, habilidades e missões) ao bot TextHeroes diretamente no banco de dados `rpg_data.db`.

**Ferramenta Recomendada**: DB Browser for SQLite - Um editor visual gratuito e de código aberto para bancos de dados SQLite.

---

## 1. Tabela `enemies` (Inimigos)

Esta tabela armazena todos os monstros que os jogadores podem encontrar.

| Coluna | Tipo | Descrição Detalhada | Exemplo |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | **(Automático)** ID único do inimigo. Não precisa ser preenchido. | `1` |
| `name` | `TEXT` | O nome do inimigo, que será exibido no jogo. | `Lobo Cinzento` |
| `min_level` | `INTEGER` | O nível **mínimo** que um jogador precisa ter para encontrar este inimigo em uma caçada aleatória (`!hunt`). | `5` |
| `max_level` | `INTEGER` | O nível **máximo** que um jogador pode ter para encontrar este inimigo em uma caçada aleatória. | `10` |
| `hp` | `INTEGER` | A quantidade de pontos de vida (HP) do inimigo. | `80` |
| `attack` | `INTEGER` | O poder de ataque base do inimigo. | `15` |
| `defense` | `INTEGER` | A defesa base do inimigo, que reduz o dano recebido. | `8` |
| `xp_reward` | `INTEGER` | A quantidade de experiência (XP) que o jogador ganha ao derrotá-lo. | `45` |
| `gold_reward` | `INTEGER` | A quantidade de ouro que o jogador ganha ao derrotá-lo. | `25` |
| `image_url` | `TEXT` | URL de uma imagem para o inimigo. Será exibida na ficha de batalha. | `https://i.imgur.com/TqBqS2Q.png` |

---

## 2. Tabela `loot_table` (Itens)

Esta é a tabela mestre para todos os itens do jogo.

| Coluna | Tipo | Descrição Detalhada | Exemplo |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | **(Automático)** ID único do item. | `1` |
| `name` | `TEXT` | Nome do item. | `Espada Longa de Aço` |
| `description`| `TEXT` | Descrição curta exibida no inventário e na loja. | `Uma espada bem balanceada.` |
| `item_type` | `TEXT` | Categoria do item. **Valores possíveis**: `weapon`, `armor`, `potion`, `material`. | `weapon` |
| `rarity` | `TEXT` | Raridade do item (atualmente para fins de organização). **Valores**: `common`, `uncommon`, `rare`, `epic`. | `uncommon` |
| `min_level_drop`| `INTEGER` | Nível mínimo que um inimigo precisa ter para que este item possa ser dropado. | `5` |
| `effect_type`| `TEXT` | Efeito especial do item. Deixe `NULL` se não houver. **Valores possíveis**: `HEAL_HP`, `HEAL_MP`, `INCREASE_MAX_HP`, `GAIN_XP`, `INCREASE_DEXTERITY`, `LIFESTEAL_PERCENT`, `GOLD_BONUS_PERCENT`, `XP_BONUS_PERCENT`, `CRIT_CHANCE_PERCENT`, `MP_REGEN_FLAT`, `POISON_ON_HIT`, `SCALE_WITH_INTELLIGENCE`. | `LIFESTEAL_PERCENT` |
| `effect_value`| `INTEGER` | O valor numérico do efeito. Ex: `25` para 25 de cura ou 25%. | `10` |
| `value` | `INTEGER` | O preço base do item em ouro. Se for `0`, não aparecerá na loja. | `150` |
| `equip_slot` | `TEXT` | Slot de equipamento. Deixe `NULL` se não for equipável. **Valores**: `right_hand`, `left_hand`, `helmet`, `chest`, `legs`, `ring`. | `right_hand` |
| `attack_bonus`| `INTEGER` | Bônus de ataque que o item concede. | `8` |
| `defense_bonus`| `INTEGER` | Bônus de defesa que o item concede. | `2` |
| `effect_duration`| `INTEGER` | Para efeitos de status (como `POISON_ON_HIT`), define a duração em turnos. | `3` |

---

## 3. Tabela `skills` (Habilidades)

Esta tabela define as habilidades que as classes podem usar.

| Coluna | Tipo | Descrição Detalhada | Exemplo |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | **(Automático)** ID único da habilidade. | `1` |
| `name` | `TEXT` | Nome da habilidade. | `Golpe Flamejante` |
| `description`| `TEXT` | Descrição curta da habilidade. | `Um ataque que causa dano de fogo.` |
| `class_restriction`| `TEXT` | A classe que pode usar esta habilidade. **Deve corresponder exatamente** a uma das classes definidas no jogo (ex: `Guerreiro`, `Feiticeiro`). | `Guerreiro` |
| `mp_cost` | `INTEGER` | Custo em Mana (MP) para usar a habilidade. | `15` |
| `effect_type`| `TEXT` | O que a habilidade faz. **Valores possíveis**: `DAMAGE`, `DAMAGE_PIERCING`, `DAMAGE_AND_POISON`, `HEAL`, `BUFF_ATTACK`, `BUFF_DEFENSE`, `DEBUFF_DEFENSE`. | `DAMAGE` |
| `base_value` | `INTEGER` | O valor base do efeito (dano, cura, etc.). | `20` |
| `scaling_stat`| `TEXT` | O atributo que aumenta o poder da habilidade. **Valores**: `strength`, `dexterity`, `intelligence`, `wisdom`, `charisma`. | `strength` |
| `scaling_factor`| `REAL` | O multiplicador do atributo de escala. `Poder Final = base_value + (atributo * scaling_factor)`. | `1.2` |
| `min_level` | `INTEGER` | O nível mínimo que o personagem precisa ter para aprender e usar esta habilidade. | `5` |
| `effect_duration`| `INTEGER` | Para buffs/debuffs, define a duração em turnos. | `2` |

---

## 4. Tabela `quests` (Missões)

Esta tabela contém todas as missões disponíveis no jogo.

| Coluna | Tipo | Descrição Detalhada | Exemplo |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | **(Automático)** ID único da missão. | `1` |
| `name` | `TEXT` | Nome da missão. | `A Praga dos Ratos` |
| `description`| `TEXT` | Descrição curta da missão. | `Elimine 10 Aranhas Gigantes da caverna local.` |
| `type` | `TEXT` | O tipo de missão, que define a frequência de reinicialização. **Valores**: `daily`, `weekly`. | `daily` |
| `objective_type`| `TEXT` | O tipo de objetivo. Atualmente, apenas `kill` (matar) é suportado. | `kill` |
| `objective_target`| `TEXT` | O nome do alvo do objetivo. **Deve corresponder exatamente** ao nome de um inimigo na tabela `enemies`. | `Aranha Gigante` |
| `objective_quantity`| `INTEGER` | A quantidade de alvos a serem completados. | `10` |
| `xp_reward` | `INTEGER` | A quantidade de experiência (XP) recebida ao completar a missão. | `150` |
| `gold_reward`| `INTEGER` | A quantidade de ouro recebida ao completar a missão. | `100` |
| `item_reward_id`| `INTEGER` | O `id` de um item da `loot_table` a ser dado como recompensa. Deixe `NULL` se não houver. | `2` |
| `item_reward_quantity`| `INTEGER` | A quantidade do item de recompensa a ser dado. | `3` |

