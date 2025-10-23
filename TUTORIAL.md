# 🎮 Tutorial Text Heroes - Como Jogar

Bem-vindo ao **Text Heroes**! Este é um RPG de texto completo no Discord onde você pode criar personagens, lutar contra monstros, coletar itens e viver aventuras épicas. Este tutorial irá te guiar através de todas as mecânicas do jogo.

## 📋 Índice
1. [Primeiros Passos](#primeiros-passos)
2. [Criação de Personagem](#criação-de-personagem)
3. [Sistema de Atributos](#sistema-de-atributos)
4. [Combate e Batalhas](#combate-e-batalhas)
5. [Sistema de Itens](#sistema-de-itens)
6. [Economia](#economia)
7. [Missões](#missões)
8. [Profissões](#profissões)
9. [Grupos e Masmorras](#grupos-e-masmorras)
10. [PvP](#pvp)
11. [Dicas e Estratégias](#dicas-e-estratégias)

---

## 🚀 Primeiros Passos

### Criando seu Primeiro Personagem

Para começar sua aventura, você precisa criar um personagem:

```
!newchar
```

O bot irá te guiar através de um processo interativo onde você escolherá:
- **Nome** do seu personagem
- **Raça** (Humano, Elfo, Anão, Halfling, Meio-Orc, Thiefling)
- **Classe** (Guerreiro, Ladino, Feiticeiro, Bardo, Clérigo, Patrulheiro)
- **Distribuição de Atributos** (24 pontos para distribuir)

### Visualizando sua Ficha

Para ver sua ficha completa:
```
!char
```

Este comando mostra:
- Nível, XP e Gold
- Pontos de atributo disponíveis
- HP e MP atuais
- Todos os seus atributos
- Equipamentos equipados
- Bônus especiais

---

## 🎯 Criação de Personagem

### Raças e Seus Bônus

Cada raça oferece bônus únicos aos seus atributos:

| Raça | Bônus | Descrição |
|------|-------|-----------|
| **Humano** | +1 em todos os atributos | Versátil e equilibrado |
| **Elfo** | +3 Destreza, +2 Inteligência, -1 Constituição | Ágil e inteligente |
| **Anão** | +3 Constituição, +2 Força, -1 Destreza | Resistente e forte |
| **Halfling** | +3 Destreza, +2 Carisma, -1 Força | Ágil e carismático |
| **Meio-Orc** | +3 Força, +2 Constituição, -1 Inteligência | Forte e resistente |
| **Thiefling** | +2 Inteligência, +3 Carisma, -1 Sabedoria | Inteligente e carismático |

### Classes e Atributos Chave

Cada classe tem um atributo principal que afeta suas habilidades:

| Classe | Atributo Chave | Tipo |
|--------|----------------|------|
| **Guerreiro** | Força | Físico |
| **Ladino** | Destreza | Físico |
| **Feiticeiro** | Inteligência | Mágico |
| **Bardo** | Carisma | Mágico |
| **Clérigo** | Sabedoria | Mágico |
| **Patrulheiro** | Destreza | Físico |

### Distribuição de Atributos

Você recebe **24 pontos** para distribuir entre 6 atributos:
- **Força**: Ataque físico e dano corpo a corpo
- **Constituição**: HP máximo e resistência
- **Destreza**: Velocidade e precisão
- **Inteligência**: MP máximo e magias
- **Sabedoria**: Percepção e magias divinas
- **Carisma**: Influência e magias de encantamento

**Valores**: Mínimo 8, Máximo 15 (antes dos bônus raciais)

---

## ⚔️ Combate e Batalhas

### Tipos de Batalha

#### Caça Manual (`!hunt`)
- Batalha por turnos com controle total
- Escolha entre: Atacar, Defender, Usar Habilidade, Usar Item
- Ideal para estratégia e aprendizado

#### Caça Automática (`!autohunt`)
- Batalha automática para farm
- O bot escolhe as melhores ações
- Perfeito para ganhar XP e itens passivamente

#### Caça Direcionada
```
!hunt [nome do inimigo]
!autohunt [nome do inimigo]
```
- Caça um inimigo específico
- Requer nível superior ao do monstro
- Maior controle sobre recompensas

### Sistema de Combate

#### Ações Disponíveis
1. **Atacar**: Ataque básico com sua arma
2. **Defender**: Reduz dano recebido no próximo turno
3. **Habilidade**: Usa uma habilidade especial (custa MP)
4. **Item**: Usa um item consumível

#### Cálculo de Dano
- **Dano = (Ataque + Bônus de Arma) - (Defesa do Inimigo)**
- **Crítico**: 10% de chance (pode ser aumentado com equipamentos)
- **Defender**: Reduz 50% do dano recebido

#### Inimigos Elite
- **10% de chance** de encontrar um inimigo Elite
- **+75%** em HP, Ataque e Defesa
- **+100%** em XP e Gold
- Aparecem com ⭐ **ELITE** no nome

### Consultando o Bestiário

```
!bestiary
```
Mostra todos os inimigos disponíveis para seu nível:
- **Encontros Aleatórios**: Inimigos que podem aparecer em `!hunt`
- **Caça Direcionada**: Inimigos que você pode caçar especificamente

---

## 🎒 Sistema de Itens

### Tipos de Itens

#### Equipamentos
- **Armas** (Mão Direita): Aumentam ataque
- **Escudos** (Mão Esquerda): Aumentam defesa
- **Armaduras**: Capacete, Peitoral, Pernas
- **Acessórios**: Anéis com efeitos especiais

#### Consumíveis
- **Poções**: Restauram HP ou MP
- **Materiais**: Usados para aprimoramento

### Gerenciando seu Inventário

#### Visualizar Inventário
```
!inventory
!inv
```

#### Organizar Inventário
```
!inv clean
```
Unifica itens empilháveis automaticamente.

### Equipando Itens

#### Equipar
```
!equip [ID ou nome do item]
```

#### Desequipar
```
!unequip [slot]
```
Slots: `capacete`, `peitoral`, `pernas`, `anel`, etc.

### Aprimoramento de Equipamentos

```
!enhance [nome do item]
```
- Consome **2 itens base** + **1 gema**
- Melhora o item em +1 (até +13)
- Aumenta bônus de ataque/defesa

### Usando Itens

```
!use [quantidade] [nome do item]
```
Exemplo: `!use 3 Poção de Cura Pequena`

---

## 💰 Economia

### Loja do Jogo

#### Acessar Loja
```
!shop
```

#### Comprar Itens
```
!shop buy [quantidade] [nome do item]
```

#### Vender Itens
```
!shop sell [quantidade] [nome do item]
```

### Mercado de Jogadores

#### Acessar Mercado
```
!market
```

#### Vender para Outros Jogadores
```
!market sell [preço] [quantidade] [nome do item]
```

#### Comprar de Outros Jogadores
```
!market buy [ID do anúncio] [quantidade]
```

#### Pesquisar Itens
```
!market search [nome do item]
```

#### Gerenciar Anúncios
```
!market remove [ID do anúncio]
```

---

## 📜 Missões

### Tipos de Missões

#### Missões Diárias
- Reiniciam a cada 24 horas
- Recompensas menores
- Focadas em combate

#### Missões Semanais
- Reiniciam a cada 7 dias
- Recompensas maiores
- Objetivos mais complexos

### Gerenciando Missões

#### Ver Missões Disponíveis
```
!quest list
```

#### Ver Suas Missões Ativas
```
!quest myquests
```

#### Aceitar Missão
```
!quest accept [ID da missão]
```

#### Entregar Missão
```
!quest complete [ID da missão]
```

### Tipos de Objetivos
- **Eliminar**: Mate X inimigos específicos
- Mais tipos podem ser adicionados no futuro

---

## 💼 Profissões

### Sistema de Trabalho

Escolha uma profissão para ganhar ouro passivamente:

#### Ver Profissões Disponíveis
```
!job list
```

#### Escolher Profissão
```
!job select [ID da profissão]
```

#### Ver Status da Profissão
```
!job status
```

#### Trabalhar
```
!work
```
"Bata o ponto" para acumular horas trabalhadas.

#### Receber Salário
```
!payday
```
Coleta seu salário acumulado (uma vez por dia).

#### Abandonar Profissão
```
!job quit
```

### Como Funciona
1. Escolha uma profissão adequada ao seu nível
2. Use `!work` regularmente para acumular horas
3. Use `!payday` uma vez por dia para receber ouro
4. Quanto maior o nível, melhores profissões disponíveis

---

## 👥 Grupos e Masmorras

### Sistema de Grupos

#### Criar Grupo
```
!party create
```

#### Convidar Membro
```
!party invite [@membro]
```

#### Aceitar Convite
```
!party accept
```

#### Recusar Convite
```
!party decline
```

#### Sair do Grupo
```
!party leave
```

#### Remover Membro (Líder)
```
!party kick [@membro]
```

#### Dissolver Grupo (Líder)
```
!party disband
```

### Masmorras

#### Ver Masmorras Disponíveis
```
!dungeon list
```

#### Entrar Sozinho
```
!dungeon solo [nome da masmorra]
```
- Recompensas aumentadas
- Maior desafio

#### Entrar com Grupo
```
!dungeon party [nome da masmorra]
```
- Apenas o líder pode iniciar
- Recompensas divididas entre o grupo

#### Fila Aleatória
```
!dungeon queue [nome da masmorra]
```
- Encontra outros jogadores automaticamente
- Use `!dungeon accept` quando encontrar partida
- Use `!dungeon leavequeue` para sair da fila

### Estrutura das Masmorras
1. **Múltiplas batalhas** contra inimigos
2. **Chefe final** com recompensas especiais
3. **Recompensas** baseadas na dificuldade
4. **Itens únicos** que só dropam em masmorras

---

## ⚔️ PvP (Player vs Player)

### Desafios

#### Desafiar Jogador
```
!pvp challenge [ranked] [nome do jogador]
```
- **Ranked**: Conta para ranking
- **Casual**: Apenas diversão

#### Aceitar Desafio
```
!pvp accept
```

#### Recusar Desafio
```
!pvp decline
```

### Sistema de Ranking
- Vitórias em PvP ranked contam para o ranking
- Use `!leaderboard pvp` para ver os melhores duelistas
- Recompensas especiais para os top players

---

## 🏆 Rankings e Progressão

### Ver Rankings

#### Ranking por Nível
```
!leaderboard level
```

#### Ranking PvP
```
!leaderboard pvp
```

### Sistema de Níveis

#### Ganhando XP
- **Derrotar inimigos** em batalhas
- **Completar missões**
- **Explorar masmorras**

#### Subindo de Nível
- **XP necessário** = Nível × 100
- **Pontos de atributo** ganhos ao subir
- **HP e MP** aumentam automaticamente

#### Distribuindo Pontos
```
!attribute [atributo] [quantidade]
```
Exemplo: `!attribute força 2`

---

## 💡 Dicas e Estratégias

### Para Iniciantes

1. **Comece com `!hunt`** para aprender o combate
2. **Complete missões diárias** para XP e gold
3. **Equipe-se bem** antes de tentar masmorras
4. **Use `!autohunt`** para farm quando estiver offline

### Otimização de Build

#### Classes Físicas (Guerreiro, Ladino, Patrulheiro)
- **Foque em Força/Destreza**
- **Constituição** para sobrevivência
- **Equipamentos** com bônus de ataque

#### Classes Mágicas (Feiticeiro, Bardo, Clérigo)
- **Foque no atributo chave** da classe
- **Inteligência** para MP
- **Equipamentos** com efeitos especiais

### Farm Eficiente

1. **Use `!autohunt`** com inimigos do seu nível
2. **Complete missões** regularmente
3. **Venda itens** desnecessários na loja
4. **Participe de masmorras** para itens raros

### Gerenciamento de Recursos

#### Gold
- **Venda itens** que não usa
- **Trabalhe** com profissões
- **Complete missões** diárias

#### Inventário
- **Use `!inv clean`** regularmente
- **Venda materiais** em excesso
- **Mantenha poções** para emergências

### Trabalho em Equipe

#### Grupos
- **Forme grupos** com jogadores de níveis similares
- **Coordene builds** complementares
- **Compartilhe recursos** quando necessário

#### Masmorras
- **Planeje** antes de entrar
- **Comunique** estratégias
- **Divida** recompensas justamente

---

## 🎯 Comandos Essenciais

### Comandos Básicos
- `!newchar` - Criar personagem
- `!char` - Ver ficha
- `!hunt` - Batalha manual
- `!autohunt` - Batalha automática

### Comandos de Progressão
- `!attribute` - Distribuir pontos
- `!skills` - Ver habilidades
- `!quest` - Gerenciar missões

### Comandos de Itens
- `!inventory` - Ver inventário
- `!equip` - Equipar item
- `!use` - Usar item

### Comandos Sociais
- `!party` - Gerenciar grupo
- `!dungeon` - Entrar em masmorra
- `!pvp` - Duelar jogadores

### Comandos de Economia
- `!shop` - Acessar loja
- `!market` - Mercado de jogadores
- `!job` - Sistema de profissões

---

## 🆘 Ajuda e Suporte

### Comandos de Ajuda
- `!help` - Lista todos os comandos
- `!help [comando]` - Ajuda específica
- `!gm` - Créditos do criador

### Reset e Migração
- `!reset` - Apagar personagem (cuidado!)
- `!migrate` - Mover personagem para outro servidor

### Problemas Comuns

#### "Você não tem um personagem"
- Use `!newchar` para criar um

#### "Você já está em uma batalha"
- Complete a batalha atual primeiro

#### "Canal privado não encontrado"
- Contate um administrador

---

## 🎉 Conclusão

Agora você está pronto para embarcar em sua aventura no **Text Heroes**! Lembre-se:

- **Explore** diferentes builds e estratégias
- **Interaja** com outros jogadores
- **Complete missões** regularmente
- **Divirta-se** e seja criativo!

Boa sorte, aventureiro! Que sua jornada seja épica! ⚔️✨

---

*Para mais informações sobre comandos específicos, use `!help [comando]` no Discord.*
