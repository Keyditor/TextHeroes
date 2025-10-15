import sqlite3
from contextlib import contextmanager

DATABASE_NAME = "rpg_data.db"

def connect_db():
    """Conecta ao banco de dados e retorna o objeto de conexão."""
    return sqlite3.connect(DATABASE_NAME)

@contextmanager
def db_cursor():
    """Um gerenciador de contexto para simplificar as operações de banco de dados."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        conn.commit()
        conn.close()

def populate_initial_data(cursor):
    """Verifica e cria inimigos e itens básicos se eles não existirem no banco de dados."""
    # Inimigos
    # name, min_level, max_level, hp, attack, defense, xp_reward, gold_reward, image_url
    enemies_to_add = [
        ('Goblin', 1, 3, 30, 8, 5, 10, 10, 'https://i.imgur.com/wI411wg.png'),
        ('Lobo', 1, 4, 45, 10, 6, 15, 10, 'https://i.imgur.com/TqBqS2Q.png'),
        ('Orc Batedor', 3, 5, 60, 12, 8, 25, 15, 'https://i.imgur.com/s4GAS25.png'),
        ('Esqueleto', 2, 6, 50, 11, 7, 20, 12, 'https://i.imgur.com/a2J3i2a.png'),
        # --- Novos Inimigos (Nível 4-100) ---
        # Nível 4-10
        ('Hobgoblin', 4, 7, 70, 15, 10, 35, 20, 'https://i.imgur.com/U4a322b.png'),
        ('Aranha Gigante', 5, 8, 80, 16, 11, 40, 22, 'https://i.imgur.com/v2h4367.png'),
        ('Bandido', 6, 9, 95, 18, 12, 50, 28, 'https://i.imgur.com/u0L3d2D.png'),
        ('Gnoll', 7, 10, 110, 20, 14, 60, 35, 'https://i.imgur.com/aO4YJbJ.png'),
        ('Ogro Jovem', 8, 11, 150, 25, 15, 80, 45, 'https://i.imgur.com/v8GS8y8.png'),
        # Nível 11-20
        ('Troll', 11, 15, 220, 30, 18, 120, 60, 'https://i.imgur.com/O40a3ja.png'),
        ('Harpia', 13, 17, 180, 35, 16, 140, 70, 'https://i.imgur.com/N3b5xpn.png'),
        ('Minotauro', 15, 20, 300, 40, 22, 180, 90, 'https://i.imgur.com/C1fb33g.png'),
        ('Manticora', 17, 22, 280, 45, 20, 220, 110, 'https://i.imgur.com/eWj3vE4.png'),
        ('Basilisco', 19, 24, 350, 50, 28, 270, 130, 'https://i.imgur.com/z1IARq6.png'),
        # Nível 21-30
        ('Elemental Menor', 21, 26, 320, 55, 30, 300, 150, 'https://i.imgur.com/0V8A12E.png'),
        ('Guerreiro Morto-Vivo', 23, 28, 400, 60, 35, 350, 170, 'https://i.imgur.com/y5J8IZh.png'),
        ('Wyvern', 25, 30, 450, 68, 32, 420, 200, 'https://i.imgur.com/Q4lCg11.png'),
        ('Ciclope', 27, 33, 550, 75, 40, 500, 240, 'https://i.imgur.com/M8G9zEE.png'),
        ('Golem de Pedra', 29, 35, 600, 65, 55, 550, 260, 'https://i.imgur.com/pDRa2s0.png'),
        # Nível 31-40
        ('Gigante do Gelo', 31, 37, 700, 85, 45, 650, 300, 'https://i.imgur.com/j1v2OVo.png'),
        ('Quimera', 34, 40, 800, 95, 50, 780, 350, 'https://i.imgur.com/Y533t0Q.png'),
        ('Beholder Jovem', 36, 42, 750, 105, 55, 900, 400, 'https://i.imgur.com/JdY26iU.png'),
        ('Sacerdote das Sombras', 38, 45, 650, 120, 48, 1000, 450, 'https://i.imgur.com/Bw27pYy.png'),
        ('Dragão Verde Jovem', 40, 48, 1200, 130, 65, 1500, 600, 'https://i.imgur.com/sZ5rD6I.png'),
        # Nível 41-50
        ('Elemental Maior', 41, 47, 900, 140, 70, 1300, 550, 'https://i.imgur.com/9dYf0yV.png'),
        ('Hidra', 44, 50, 1500, 150, 75, 1800, 700, 'https://i.imgur.com/TqfMh0N.png'),
        ('Cavaleiro da Morte', 46, 53, 1300, 165, 85, 2200, 850, 'https://i.imgur.com/e5f2s9f.png'),
        ('Gigante de Fogo', 48, 55, 1800, 180, 80, 2500, 950, 'https://i.imgur.com/I1N50yC.png'),
        ('Lich Aprendiz', 50, 58, 1500, 200, 90, 3000, 1200, 'https://i.imgur.com/Z02p9vO.png'),
        # Nível 51-60
        ('Dragão Azul Adulto', 52, 60, 2500, 220, 110, 3500, 1500, 'https://i.imgur.com/i3vE5yb.png'),
        ('Kraken Menor', 55, 63, 3000, 210, 130, 4000, 1800, 'https://i.imgur.com/rV2i27a.png'),
        ('Vampiro Lorde', 58, 66, 2200, 250, 120, 4800, 2200, 'https://i.imgur.com/8vD6x8B.png'),
        ('Golem de Adamantina', 60, 68, 4000, 230, 180, 5500, 2500, 'https://i.imgur.com/S2A21sA.png'),
        # Nível 61-70
        ('Dragão Vermelho Adulto', 62, 70, 4500, 280, 150, 6500, 3000, 'https://i.imgur.com/x1Y13A0.png'),
        ('Anjo Caído', 65, 73, 3800, 310, 140, 7500, 3500, 'https://i.imgur.com/C9a1s3v.png'),
        ('Arquimago Corrompido', 68, 76, 3500, 350, 130, 8800, 4000, 'https://i.imgur.com/m0xS3Y1.png'),
        # Nível 71-80
        ('Beholder Ancião', 72, 80, 5000, 400, 180, 10000, 5000, 'https://i.imgur.com/2h255sC.png'),
        ('Lich', 75, 83, 4800, 450, 170, 12000, 6000, 'https://i.imgur.com/yV1s9a4.png'),
        ('Dragão Negro Ancião', 78, 86, 7000, 480, 220, 15000, 7500, 'https://i.imgur.com/A03bJ75.png'),
        # Nível 81-90
        ('Avatar da Morte', 82, 90, 8000, 550, 250, 20000, 10000, 'https://i.imgur.com/D4s2G3z.png'),
        ('Titã', 85, 93, 12000, 600, 300, 25000, 12000, 'https://i.imgur.com/O0f4s4P.png'),
        ('Dragão de Mithril', 88, 96, 10000, 650, 350, 30000, 15000, 'https://i.imgur.com/c6o5x1A.png'),
        # Nível 91-100
        ('Lorde Demônio', 92, 98, 15000, 750, 400, 40000, 20000, 'https://i.imgur.com/I0b5c1M.png'),
        ('Arcanjo Vingativo', 95, 100, 13000, 850, 380, 50000, 25000, 'https://i.imgur.com/Z7g1p1J.png'),
        ('Tarrasque', 100, 100, 25000, 900, 500, 75000, 35000, 'https://i.imgur.com/sC3a3fT.png'),
        ('Deus Antigo Adormecido', 100, 100, 20000, 1200, 450, 100000, 50000, 'https://i.imgur.com/Gv1s5sW.png'),
    ]
    for enemy_data in enemies_to_add:
        cursor.execute("SELECT COUNT(*) FROM enemies WHERE name = ?", (enemy_data[0],))
        if cursor.fetchone()[0] == 0:
            print(f"Creating missing enemy: {enemy_data[0]}")
            cursor.execute(
                "INSERT INTO enemies (name, min_level, max_level, hp, attack, defense, xp_reward, gold_reward, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                enemy_data
            )

    # Itens de Loot
    loot_to_add = [
        # name, description, item_type, rarity, min_level_drop, effect_type, effect_value, value, equip_slot, attack_bonus, defense_bonus
        ('Poção de Cura Pequena', 'Restaura 25 HP.', 'potion', 'common', 1, 'HEAL_HP', 25, 10, None, 0, 0, None),
        ('Poção de Cura Média', 'Restaura 75 HP.', 'potion', 'uncommon', 5, 'HEAL_HP', 75, 50, None, 0, 0, None),
        ('Poção de Mana Pequena', 'Restaura 20 MP.', 'potion', 'common', 2, 'HEAL_MP', 20, 15, None, 0, 0, None),
        ('Fruto Dourado', 'Aumenta permanentemente o HP máximo em 5.', 'potion', 'rare', 8, 'INCREASE_MAX_HP', 5, 500, None, 0, 0, None),
        ('Tomo do Conhecimento', 'Concede 50 de experiência.', 'potion', 'uncommon', 4, 'GAIN_XP', 50, 100, None, 0, 0, None),
        ('Elixir da Rapidez', 'Aumenta permanentemente a Destreza em 1.', 'potion', 'epic', 10, 'INCREASE_DEXTERITY', 1, 1000, None, 0, 0, None),

        ('Adaga Enferrujada', 'Uma adaga simples.', 'weapon', 'common', 1, None, None, 5, 'right_hand', 2, 0, None),
        ('Adaga Envenenada', 'Uma adaga com uma lâmina coberta de veneno que tem 25% de chance de envenenar o alvo em ataques.', 'weapon', 'rare', 6, 'POISON_ON_HIT', 25, 220, 'right_hand', 7, 0, 3),
        ('Machado de Guerra Orc', 'Bruto e pesado, favorece a força sobre a defesa.', 'weapon', 'uncommon', 4, None, None, 40, 'right_hand', 8, -2, None),
        ('Arco Élfico', 'Leve e preciso.', 'weapon', 'uncommon', 3, None, None, 55, 'right_hand', 6, 0, None),
        ('Cajado do Aprendiz', 'Focado em canalizar poder mágico.', 'weapon', 'common', 1, 'SCALE_WITH_INTELLIGENCE', None, 20, 'right_hand', 3, 1, None),
        ('Martelo de Guerra Anão', 'Uma arma robusta que também oferece boa proteção.', 'weapon', 'rare', 6, None, None, 150, 'right_hand', 10, 2, None),

        ('Pele de Lobo', 'Pode ser útil para artesanato.', 'material', 'common', 1, None, None, 3, None, 0, 0, None),
        ('Espada Curta de Ferro', 'Uma espada confiável.', 'weapon', 'uncommon', 3, None, None, 20, 'right_hand', 5, 0, None),

        ('Peitoral de Couro', 'Oferece proteção básica.', 'armor', 'common', 2, None, None, 25, 'chest', 0, 3, None),
        ('Elmo de Ferro', 'Proteção sólida para a cabeça.', 'armor', 'common', 3, None, None, 30, 'helmet', 0, 2, None),
        ('Calças de Malha', 'Flexíveis e resistentes.', 'armor', 'uncommon', 4, None, None, 45, 'legs', 0, 4, None),
        ('Peitoral de Aço', 'Excelente proteção, mas pesado.', 'armor', 'rare', 7, None, None, 200, 'chest', -1, 10, None),
        ('Botas de Couro Leve', 'Aumentam a agilidade do usuário.', 'armor', 'common', 2, None, None, 20, 'legs', 0, 1, None),

        ('Anel do Vampiro', 'Cura o usuário em 25% do dano causado por ataques.', 'armor', 'rare', 5, 'LIFESTEAL_PERCENT', 25, 250, 'ring', 0, 0, None),
        ('Anel da Avareza', 'Aumenta o ouro ganho em batalhas em 15%.', 'armor', 'uncommon', 3, 'GOLD_BONUS_PERCENT', 15, 150, 'ring', 0, 0, None),
        ('Anel do Sábio', 'Aumenta a experiência ganha em 10%.', 'armor', 'uncommon', 3, 'XP_BONUS_PERCENT', 10, 150, 'ring', 0, 0, None),
        ('Anel da Precisão', 'Aumenta a chance de causar dano crítico.', 'armor', 'rare', 6, 'CRIT_CHANCE_PERCENT', 10, 300, 'ring', 0, 0, None),
        ('Anel da Regeneração', 'Regenera uma pequena quantidade de MP a cada turno.', 'armor', 'epic', 10, 'MP_REGEN_FLAT', 2, 500, 'ring', 0, 0, None),

        ('Gema de Arma', 'Uma gema necessária para aprimorar armas.', 'material', 'rare', 10, None, None, 1000, None, 0, 0, None),
        ('Gema de Armadura', 'Uma gema necessária para aprimorar armaduras.', 'material', 'rare', 10, None, None, 1000, None, 0, 0, None),
        ('Gema de Acessório', 'Uma gema rara usada para aprimorar anéis e outros acessórios.', 'material', 'epic', 20, None, None, 2500, None, 0, 0, None),
    ]
    for item_data in loot_to_add:
        cursor.execute("SELECT COUNT(*) FROM loot_table WHERE name = ?", (item_data[0],))
        if cursor.fetchone()[0] == 0:
            print(f"Creating missing item: {item_data[0]}")
            cursor.execute(
                "INSERT INTO loot_table (name, description, item_type, rarity, min_level_drop, effect_type, effect_value, value, equip_slot, attack_bonus, defense_bonus, effect_duration) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                item_data
            )
    
    # Habilidades (Skills)
    # name, description, class_restriction, mp_cost, effect_type, base_value, scaling_stat, scaling_factor, min_level
    skills_to_add = [
        # Guerreiro
        ('Golpe Poderoso', 'Um ataque devastador que consome energia.', 'Guerreiro', 10, 'DAMAGE', 15, 'strength', 1.2, 1, None),
        ('Grito de Guerra', 'Aumenta seu ataque no próximo turno.', 'Guerreiro', 15, 'BUFF_ATTACK', 5, 'strength', 0.5, 5, 1),
        # Ladino
        ('Ataque Furtivo', 'Um ataque rápido e preciso que ignora parte da defesa inimiga.', 'Ladino', 12, 'DAMAGE_PIERCING', 10, 'dexterity', 1.3, 1, None),
        ('Lançar Adaga Envenenada', 'Causa dano e envenena o alvo por 3 turnos.', 'Ladino', 18, 'DAMAGE_AND_POISON', 10, 'dexterity', 1.0, 6, 3),
        # Feiticeiro
        ('Bola de Fogo', 'Lança uma bola de fogo que causa dano mágico.', 'Feiticeiro', 15, 'DAMAGE', 20, 'intelligence', 1.5, 1, None),
        ('Barreira de Gelo', 'Cria uma barreira que aumenta sua defesa no próximo turno.', 'Feiticeiro', 10, 'BUFF_DEFENSE', 10, 'intelligence', 0.3, 4, 1),
        # Bardo
        ('Canção Revigorante', 'Uma melodia que cura uma pequena quantidade de vida.', 'Bardo', 20, 'HEAL', 25, 'charisma', 1.0, 1, None),
        ('Balada Desmoralizante', 'Confunde o inimigo, reduzindo sua defesa no próximo turno.', 'Bardo', 15, 'DEBUFF_DEFENSE', 5, 'charisma', 0.5, 5, 1),
        # Clérigo
        ('Luz Sagrada', 'Causa dano radiante em um inimigo.', 'Clérigo', 15, 'DAMAGE', 18, 'wisdom', 1.4, 1, None),
        ('Bênção Divina', 'Cura um aliado (ou a si mesmo) com poder divino.', 'Clérigo', 25, 'HEAL', 30, 'wisdom', 1.2, 3, None),
        # Patrulheiro
        ('Tiro Preciso', 'Um disparo certeiro que causa dano aumentado.', 'Patrulheiro', 12, 'DAMAGE', 15, 'dexterity', 1.4, 1, None),
        ('Armadilha de Caçador', 'Prende o inimigo, reduzindo sua defesa temporariamente.', 'Patrulheiro', 15, 'DEBUFF_DEFENSE', 8, 'dexterity', 0.4, 5, 2),
    ]
    for skill_data in skills_to_add:
        cursor.execute("SELECT COUNT(*) FROM skills WHERE name = ?", (skill_data[0],))
        if cursor.fetchone()[0] == 0:
            print(f"Creating missing skill: {skill_data[0]}")
            cursor.execute(
                "INSERT INTO skills (name, description, class_restriction, mp_cost, effect_type, base_value, scaling_stat, scaling_factor, min_level, effect_duration) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                skill_data
            )

    # Missões (Quests)
    # name, description, type ('daily', 'weekly'), objective_type ('kill'), objective_target, objective_quantity, xp_reward, gold_reward, item_reward_id, item_reward_quantity
    quests_to_add = [
        ('Caça aos Goblins', 'Elimine 5 Goblins da floresta.', 'daily', 'kill', 'Goblin', 5, 50, 25, None, None),
        ('Extermínio de Lobos', 'Cace 10 Lobos que ameaçam os viajantes.', 'daily', 'kill', 'Lobo', 10, 80, 40, None, None),
        ('A Ameaça Orc', 'Derrote 15 Orcs Batedores para proteger a vila.', 'weekly', 'kill', 'Orc Batedor', 15, 250, 150, 1, 1), # Recompensa: Poção de Cura Pequena
        ('Limpeza de Cripta', 'Destrua 20 Esqueletos em uma cripta antiga.', 'weekly', 'kill', 'Esqueleto', 20, 300, 200, 2, 1), # Recompensa: Poção de Cura Média
    ]
    for quest_data in quests_to_add:
        cursor.execute("SELECT COUNT(*) FROM quests WHERE name = ?", (quest_data[0],))
        if cursor.fetchone()[0] == 0:
            print(f"Creating missing quest: {quest_data[0]}")
            cursor.execute("INSERT INTO quests (name, description, type, objective_type, objective_target, objective_quantity, xp_reward, gold_reward, item_reward_id, item_reward_quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", quest_data)

    # Profissões (Jobs)
    jobs_to_add = [
        (1, 'Ajudante de Fazendeiro', 'Trabalho simples na fazenda local.', 1, 10),
        (2, 'Garimpeiro Aprendiz', 'Busca por minérios nas minas abandonadas.', 10, 25),
        (3, 'Guarda da Cidade', 'Patrulha os muros da cidade, mantendo a ordem.', 20, 50),
        (4, 'Assistente de Alquimista', 'Ajuda a coletar ingredientes e preparar poções.', 30, 80),
        (5, 'Caçador de Recompensas', 'Rastreia e captura criminosos para o reino.', 50, 150),
    ]
    for job_data in jobs_to_add:
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE id = ?", (job_data[0],))
        if cursor.fetchone()[0] == 0:
            print(f"Creating missing job: {job_data[1]}")
            cursor.execute("INSERT INTO jobs (id, name, description, level_req, gold_per_hour) VALUES (?, ?, ?, ?, ?)", job_data)

def migrate_db():
    """Verifica e aplica migrações pendentes no banco de dados para atualizar a estrutura."""
    print("Checking for database migrations...")
    with db_cursor() as cursor:
        # --- Migração 1: Adicionar colunas se não existirem ---
        tables_to_check = {
            "characters": [
                ("gold", "INTEGER NOT NULL DEFAULT 0"),
                ("pvp_wins", "INTEGER NOT NULL DEFAULT 0"),
                ("pvp_losses", "INTEGER NOT NULL DEFAULT 0"),
                ("current_job_id", "INTEGER", "FOREIGN KEY (current_job_id) REFERENCES jobs(id)"),
                ("job_started_at", "TIMESTAMP"),
                ("last_payday", "TIMESTAMP"),
                ("last_job_change", "TIMESTAMP"),
                ("last_work_check_in", "TIMESTAMP"),
            ],
            "enemies": [
                ("gold_reward", "INTEGER NOT NULL DEFAULT 10"),
                ("image_url", "TEXT")
            ],
            "loot_table": [
                ("effect_type", "TEXT"),
                ("effect_value", "INTEGER"),
                ("value", "INTEGER NOT NULL DEFAULT 0"),
                ("equip_slot", "TEXT"),
                ("attack_bonus", "INTEGER NOT NULL DEFAULT 0"),
                ("defense_bonus", "INTEGER NOT NULL DEFAULT 0"),
                ("effect_duration", "INTEGER"),
            ],
            "inventory": [
                ("unique_id", "TEXT"), # Adicionado para rastrear itens individualmente
            ],
            "skills": [
                ("effect_duration", "INTEGER"),
            ]
        }

        for table, columns in tables_to_check.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = [row[1] for row in cursor.fetchall()]
            for column_def in columns:
                col_name, col_type = column_def[0], column_def[1]
                if col_name not in existing_columns:
                    print(f"Applying migration: Adding column '{col_name}' to table '{table}'...")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}") # A FK não é adicionada via ALTER TABLE simples em SQLite

        # --- Migração 2: Garantir que cada personagem tenha uma entrada de equipamento ---
        cursor.execute("SELECT user_id FROM characters")
        all_character_ids = [row[0] for row in cursor.fetchall()]
        
        if all_character_ids:
            cursor.execute("SELECT character_user_id FROM equipment")
            equipped_character_ids = [row[0] for row in cursor.fetchall()]
            
            missing_equipment_entries = set(all_character_ids) - set(equipped_character_ids)
            
            if missing_equipment_entries:
                print(f"Applying migration: Creating equipment entries for {len(missing_equipment_entries)} characters...")
                for user_id in missing_equipment_entries:
                    try:
                        cursor.execute("INSERT INTO equipment (character_user_id) VALUES (?)", (user_id,))
                    except sqlite3.IntegrityError:
                        # Caso a entrada já exista (corrida de condição), ignora o erro.
                        pass

    print("Database migrations checked.")

def init_db():
    """Inicializa o banco de dados, criando as tabelas necessárias."""
    with db_cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            user_id INTEGER PRIMARY KEY,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER,
            name TEXT NOT NULL,
            race TEXT NOT NULL,
            class TEXT NOT NULL,
            strength INTEGER NOT NULL,
            constitution INTEGER NOT NULL,
            dexterity INTEGER NOT NULL,
            intelligence INTEGER NOT NULL,
            wisdom INTEGER NOT NULL,
            charisma INTEGER NOT NULL,
            hp INTEGER NOT NULL,
            max_hp INTEGER NOT NULL,
            mp INTEGER NOT NULL,
            max_mp INTEGER NOT NULL,
            image_url TEXT,
            level INTEGER NOT NULL DEFAULT 1,
            experience INTEGER NOT NULL DEFAULT 0,
            gold INTEGER NOT NULL DEFAULT 0,
            pvp_wins INTEGER NOT NULL DEFAULT 0,
            pvp_losses INTEGER NOT NULL DEFAULT 0,
            current_job_id INTEGER,
            job_started_at TIMESTAMP,
            last_payday TIMESTAMP,
            last_job_change TIMESTAMP,
            last_work_check_in TIMESTAMP,
            FOREIGN KEY (current_job_id) REFERENCES jobs(id)
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS enemies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            min_level INTEGER NOT NULL,
            max_level INTEGER NOT NULL,
            hp INTEGER NOT NULL,
            attack INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            xp_reward INTEGER NOT NULL,
            gold_reward INTEGER NOT NULL DEFAULT 10,
            image_url TEXT
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS loot_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            item_type TEXT NOT NULL,
            rarity TEXT NOT NULL,
            min_level_drop INTEGER NOT NULL DEFAULT 1,
            effect_type TEXT,
            effect_value INTEGER,
            value INTEGER NOT NULL DEFAULT 0,
            equip_slot TEXT,
            attack_bonus INTEGER NOT NULL DEFAULT 0,
            defense_bonus INTEGER NOT NULL DEFAULT 0,
            effect_duration INTEGER
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL, -- O tipo de item (da loot_table)
            quantity INTEGER NOT NULL DEFAULT 1, -- Para itens empilháveis
            enhancement_level INTEGER NOT NULL DEFAULT 0,
            unique_id TEXT, -- UUID para itens únicos como equipamentos
            FOREIGN KEY (character_user_id) REFERENCES characters (user_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES loot_table (id)
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            character_user_id INTEGER PRIMARY KEY,
            helmet_id INTEGER,
            chest_id INTEGER,
            legs_id INTEGER,
            right_hand_id INTEGER,
            left_hand_id INTEGER,
            ring_id INTEGER,
            FOREIGN KEY (character_user_id) REFERENCES characters (user_id) ON DELETE CASCADE,
            FOREIGN KEY (helmet_id) REFERENCES inventory (id),
            FOREIGN KEY (chest_id) REFERENCES inventory (id),
            FOREIGN KEY (legs_id) REFERENCES inventory (id),
            FOREIGN KEY (right_hand_id) REFERENCES inventory (id),
            FOREIGN KEY (left_hand_id) REFERENCES inventory (id),
            FOREIGN KEY (ring_id) REFERENCES inventory (id)
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            class_restriction TEXT NOT NULL,
            mp_cost INTEGER NOT NULL,
            effect_type TEXT NOT NULL,
            base_value INTEGER NOT NULL,
            scaling_stat TEXT,
            scaling_factor REAL,
            min_level INTEGER NOT NULL DEFAULT 1,
            effect_duration INTEGER
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            enhancement_level INTEGER NOT NULL DEFAULT 0,
            listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES characters (user_id),
            FOREIGN KEY (item_id) REFERENCES loot_table (id)
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            type TEXT NOT NULL, -- 'daily' or 'weekly'
            objective_type TEXT NOT NULL, -- 'kill', 'collect', etc.
            objective_target TEXT NOT NULL,
            objective_quantity INTEGER NOT NULL,
            xp_reward INTEGER NOT NULL,
            gold_reward INTEGER NOT NULL,
            item_reward_id INTEGER,
            item_reward_quantity INTEGER,
            FOREIGN KEY (item_reward_id) REFERENCES loot_table (id)
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_user_id INTEGER NOT NULL,
            quest_id INTEGER NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (character_user_id) REFERENCES characters (user_id) ON DELETE CASCADE,
            FOREIGN KEY (quest_id) REFERENCES quests (id)
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS guilds (
            guild_id INTEGER PRIMARY KEY,
            guild_name TEXT NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            level_req INTEGER NOT NULL,
            gold_per_hour INTEGER NOT NULL
        )
    """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_jobs_progress (
            character_user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            hours_worked INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (character_user_id, job_id),
            FOREIGN KEY (character_user_id) REFERENCES characters(user_id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)



    # Executa as migrações ANTES de popular os dados
    migrate_db() 

    with db_cursor() as cursor:
        populate_initial_data(cursor)

    print(f"Database '{DATABASE_NAME}' initialized.")

def delete_character_full(user_id):
    """
    Deleta um personagem e todos os seus dados associados (inventário, equipamento, quests).
    A exclusão da tabela 'characters' aciona o ON DELETE CASCADE para 'player_quests'.
    """
    with db_cursor() as cursor:
        # Remove explicitamente para garantir a limpeza completa
        cursor.execute("DELETE FROM inventory WHERE character_user_id = ?", (user_id,))
        cursor.execute("DELETE FROM equipment WHERE character_user_id = ?", (user_id,))
        cursor.execute("DELETE FROM characters WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0

def create_character(user_id, guild_id, channel_id, name, race, char_class,
                     strength, constitution, dexterity, intelligence, wisdom,
                     charisma, hp, mp, image_url=None):
    """Cria um novo personagem no banco de dados."""
    with db_cursor() as cursor:
        try:
            cursor.execute("""
                INSERT INTO characters (user_id, guild_id, channel_id, name, race, class, 
                                        strength, constitution, dexterity, intelligence, wisdom, charisma,
                                        hp, max_hp, mp, max_mp, image_url, level, experience, gold)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 150)
            """, (user_id, guild_id, channel_id, name, race, char_class,
                  strength, constitution, dexterity, intelligence, wisdom, charisma,
                  hp, hp, mp, mp, image_url))
            cursor.execute("INSERT INTO equipment (character_user_id) VALUES (?)", (user_id,))
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Character with user_id {user_id} already exists.")
            return False

def get_character(user_id):
    """Retorna os dados de um personagem pelo user_id."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM characters WHERE user_id = ?", (user_id,))
        character_data = cursor.fetchone()
        if character_data:
            # Retorna um dicionário para facilitar o acesso aos dados
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, character_data))
    return None

def get_character_by_name(name):
    """Retorna os dados de um personagem pelo nome (case-insensitive)."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM characters WHERE name LIKE ?", (name,))
        character_data = cursor.fetchone()
        if character_data:
            # Retorna um dicionário para facilitar o acesso aos dados
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, character_data))
    return None

def update_character_image(user_id, image_url):
    """Atualiza a URL da imagem de um personagem."""
    with db_cursor() as cursor:
        cursor.execute("UPDATE characters SET image_url = ? WHERE user_id = ?", (image_url, user_id))
        return cursor.rowcount > 0

def update_character_channel(user_id, channel_id):
    """Atualiza o ID do canal privado do personagem."""
    with db_cursor() as cursor:
        cursor.execute("UPDATE characters SET channel_id = ? WHERE user_id = ?", (channel_id, user_id))
        return cursor.rowcount > 0

def update_character_guild(user_id, new_guild_id, new_channel_id):
    """Atualiza o guild_id e channel_id de um personagem durante a migração."""
    with db_cursor() as cursor:
        cursor.execute("UPDATE characters SET guild_id = ?, channel_id = ? WHERE user_id = ?", (new_guild_id, new_channel_id, user_id))
        return cursor.rowcount > 0


def update_character_stats(user_id, updates):
    """Atualiza múltiplos status de um personagem (level, xp, atributos)."""
    with db_cursor() as cursor:
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(user_id)
        
        query = f"UPDATE characters SET {set_clause} WHERE user_id = ?" # nosec
        
        cursor.execute(query, tuple(values))
        return cursor.rowcount > 0

def get_random_enemy(player_level):
    """Busca um inimigo aleatório apropriado para o nível do jogador."""
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM enemies WHERE min_level <= ? AND max_level >= ? ORDER BY RANDOM() LIMIT 1",
            (player_level, player_level)
        )
        enemy_data = cursor.fetchone()
        if enemy_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, enemy_data))
    return None

def get_random_loot(enemy_level):
    """Sorteia um item de loot aleatório."""
    with db_cursor() as cursor:
        # Lógica simples de drop: 30% de chance de dropar algo
        cursor.execute(
            "SELECT * FROM loot_table WHERE min_level_drop <= ? ORDER BY RANDOM() LIMIT 1",
            (enemy_level,)
        )
        loot_data = cursor.fetchone()
        if loot_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, loot_data))
    return None

def get_enemies_for_level(player_level):
    """Busca todos os inimigos para o nível do jogador."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM enemies WHERE min_level <= ? AND max_level >= ? ORDER BY min_level", (player_level, player_level))
        enemy_data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, enemy)) for enemy in enemy_data]

def get_all_huntable_enemies(player_level):
    """Busca todos os inimigos que o jogador pode caçar especificamente (nível > max_level)."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM enemies WHERE max_level < ? ORDER BY min_level", (player_level,))
        enemy_data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, enemy)) for enemy in enemy_data]

def _add_item_to_inventory(cursor, user_id, item_id, quantity=1, enhancement_level=0):
    """Lógica interna para adicionar um item, reutilizando um cursor existente."""
    item_info = get_item_by_id(item_id)
    is_stackable = item_info['item_type'] in ['potion', 'material']

    if is_stackable and enhancement_level == 0:
        cursor.execute("SELECT id, quantity FROM inventory WHERE character_user_id = ? AND item_id = ? AND enhancement_level = 0", (user_id, item_id))
        existing_item = cursor.fetchone()
        if existing_item:
            new_quantity = existing_item[1] + quantity
            cursor.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_quantity, existing_item[0]))
            return

    # Para itens não empilháveis, aprimorados, ou o primeiro de um stack
    for _ in range(quantity):
        cursor.execute(
            "INSERT INTO inventory (character_user_id, item_id, quantity, enhancement_level) VALUES (?, ?, 1, ?)",
            (user_id, item_id, enhancement_level)
        )

def add_item_to_inventory(user_id, item_id, quantity=1, enhancement_level=0):
    """Adiciona um item (ou aumenta a quantidade) ao inventário do jogador."""
    with db_cursor() as cursor:
        _add_item_to_inventory(cursor, user_id, item_id, quantity, enhancement_level)

def _remove_item_from_inventory(cursor, user_id, item_id, quantity=1, enhancement_level=0):
    """Lógica interna para remover um item, reutilizando um cursor existente."""
    item_info = get_item_by_id(item_id)
    is_stackable = item_info['item_type'] in ['potion', 'material']

    if is_stackable and enhancement_level == 0:
        cursor.execute("SELECT id, quantity FROM inventory WHERE character_user_id = ? AND item_id = ? AND enhancement_level = 0", (user_id, item_id))
        item = cursor.fetchone()
        if not item or item[1] < quantity: return False
        if item[1] > quantity:
            cursor.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (item[1] - quantity, item[0]))
        else:
            cursor.execute("DELETE FROM inventory WHERE id = ?", (item[0],))
    else: # Itens não empilháveis ou aprimorados
        cursor.execute("SELECT id FROM inventory WHERE character_user_id = ? AND item_id = ? AND enhancement_level = ? LIMIT ?", (user_id, item_id, enhancement_level, quantity))
        items_to_delete = cursor.fetchall()
        if len(items_to_delete) < quantity: return False
        for item_tuple in items_to_delete:
            cursor.execute("DELETE FROM inventory WHERE id = ?", (item_tuple[0],))
    return True

def remove_item_from_inventory(user_id, item_id, quantity=1, enhancement_level=0):
    """Remove uma quantidade de um item do inventário. Retorna True se bem-sucedido."""
    with db_cursor() as cursor:
        return _remove_item_from_inventory(cursor, user_id, item_id, quantity, enhancement_level)
 
def get_inventory(user_id):
    """Retorna o inventário de um jogador."""
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT i.id as inventory_id, l.id as item_id, i.quantity, l.name, l.description, l.item_type, l.effect_type, l.effect_value, l.equip_slot, i.enhancement_level 
            FROM inventory i
            JOIN loot_table l ON i.item_id = l.id
            WHERE i.character_user_id = ?
        """, (user_id,))
        return cursor.fetchall()

def get_item_by_name(item_name):
    """Busca um item na loot_table pelo nome."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM loot_table WHERE name LIKE ?", (f'%{item_name}%',))
        item_data = cursor.fetchone()
        if item_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, item_data))
    return None

def get_item_by_id(item_id):
    """Busca um item na loot_table pelo ID."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM loot_table WHERE id = ?", (item_id,))
        item_data = cursor.fetchone()
        if item_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, item_data))
    return None

def get_shop_items(category=None, page=1, per_page=5):
    """Retorna itens da loja com filtro de categoria e paginação."""
    with db_cursor() as cursor:
        query = "SELECT * FROM loot_table WHERE value > 0"
        params = []
        if category and category != 'all':
            query += " AND item_type = ?"
            params.append(category)
        
        offset = (page - 1) * per_page
        query += " ORDER BY item_type, name LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        cursor.execute(query, tuple(params))
        items_data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, item)) for item in items_data]

def count_shop_items(category=None):
    """Conta o número total de itens na loja, com filtro de categoria opcional."""
    with db_cursor() as cursor:
        query = "SELECT COUNT(*) FROM loot_table WHERE value > 0"
        params = []
        if category and category != 'all':
            query += " AND item_type = ?"
            params.append(category)
        
        cursor.execute(query, tuple(params))
        count = cursor.fetchone()[0]
        return count

def get_equipped_items(user_id):
    """Retorna os itens equipados por um jogador e seus bônus totais."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM equipment WHERE character_user_id = ?", (user_id,))
        equipped_data = cursor.fetchone()
        if not equipped_data:
            return {}, {"attack": 0, "defense": 0}

        columns = [description[0] for description in cursor.description]
        equipped_dict = dict(zip(columns, equipped_data))

        total_attack_bonus = 0
        total_defense_bonus = 0
        equipped_item_details = {}

        # Busca por bônus especiais
        special_bonuses = {}
        duration_bonuses = {}

        for slot, inventory_id in equipped_dict.items():
            if inventory_id and slot != 'character_user_id':
                # Pega os detalhes do item e seu aprimoramento
                cursor.execute("""
                    SELECT l.name, l.attack_bonus, l.defense_bonus, l.effect_type, l.effect_value, l.effect_duration, i.enhancement_level
                    FROM inventory i
                    JOIN loot_table l ON i.item_id = l.id
                    WHERE i.id = ?
                """, (inventory_id,))
                item_details = cursor.fetchone()
                if item_details:
                    name, attack, defense, effect_type, effect_value, effect_duration, enhancement = item_details
                    
                    # Calcula o bônus do aprimoramento (15% por nível)
                    final_attack = round(attack * (1 + 0.15 * enhancement))
                    final_defense = round(defense * (1 + 0.15 * enhancement))

                    equipped_item_details[slot] = f"{name} +{enhancement}" if enhancement > 0 else name
                    total_attack_bonus += final_attack
                    total_defense_bonus += final_defense

                    if effect_type:
                        special_bonuses[effect_type] = effect_value
                        if effect_duration:
                            duration_bonuses[effect_type] = effect_duration
            else:
                equipped_item_details[slot] = "Vazio"
        
        bonuses = {
            "attack": total_attack_bonus, 
            "defense": total_defense_bonus,
            "special": special_bonuses,
            "duration": duration_bonuses
        }

        return equipped_item_details, bonuses

def equip_item(user_id, inventory_id, slot):
    """Equipa um item em um slot específico, desequipando o anterior se houver."""
    with db_cursor() as cursor:
        # Primeiro, verifica se há um item no slot e o devolve ao inventário
        # Esta lógica foi simplificada, pois o item desequipado já está no inventário.
        # Apenas precisamos limpar o slot.

        # Agora, equipa o novo item
        try:
            cursor.execute(f"UPDATE equipment SET {slot} = ? WHERE character_user_id = ?", (inventory_id, user_id))
        except sqlite3.Error as e:
            print(f"Erro ao equipar item: {e}")
            return False
    return True

def unequip_item(user_id, slot):
    """Desequipa um item e o devolve ao inventário."""
    # O item nunca sai do inventário, apenas o slot de equipamento é limpo.
    with db_cursor() as cursor:
        # A query usa f-string de forma segura, pois 'slot' é validado no comando.
        cursor.execute(f"UPDATE equipment SET {slot} = NULL WHERE character_user_id = ?", (user_id,)) # nosec
        return cursor.rowcount > 0

def get_character_skills(class_name, level):
    """Retorna as habilidades disponíveis para uma classe e nível."""
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM skills WHERE class_restriction = ? AND min_level <= ?",
            (class_name, level)
        )
        skills_data = cursor.fetchall()
        if skills_data:
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, skill)) for skill in skills_data]
    return []

def get_available_quests(user_id, quest_type):
    """Retorna missões disponíveis (diárias/semanais) que o jogador ainda não aceitou."""
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM quests q
            WHERE q.type = ? AND NOT EXISTS (
                SELECT 1 FROM player_quests pq 
                WHERE pq.character_user_id = ? AND pq.quest_id = q.id
            )
        """, (quest_type, user_id))
        quests_data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, quest)) for quest in quests_data]

def get_player_active_quests(user_id):
    """Retorna as missões ativas de um jogador com seu progresso."""
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT q.id, q.name, q.description, pq.progress, q.objective_quantity, q.objective_target
            FROM player_quests pq
            JOIN quests q ON pq.quest_id = q.id
            WHERE pq.character_user_id = ?
        """, (user_id,))
        quests_data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, quest)) for quest in quests_data]

def get_quest_by_id(quest_id):
    """Busca uma missão pelo seu ID."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM quests WHERE id = ?", (quest_id,))
        quest_data = cursor.fetchone()
        if quest_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, quest_data))
    return None

def accept_quest(user_id, quest_id):
    """Associa uma missão a um jogador."""
    with db_cursor() as cursor:
        cursor.execute("INSERT INTO player_quests (character_user_id, quest_id) VALUES (?, ?)", (user_id, quest_id))
        return cursor.rowcount > 0

def update_quest_progress(user_id, objective_type, target_name):
    """Atualiza o progresso de uma missão ativa."""
    with db_cursor() as cursor:
        # Encontra a missão ativa correspondente
        cursor.execute("""
            UPDATE player_quests 
            SET progress = progress + 1
            WHERE character_user_id = ? AND quest_id IN (
                SELECT id FROM quests WHERE objective_type = ? AND objective_target = ?
            )
        """, (user_id, objective_type, target_name))

def complete_quest(user_id, quest_id):
    """Remove uma missão da lista de ativas do jogador."""
    with db_cursor() as cursor:
        cursor.execute("DELETE FROM player_quests WHERE character_user_id = ? AND quest_id = ?", (user_id, quest_id))
        return cursor.rowcount > 0

def register_guild(guild_id, guild_name):
    """Registra um novo servidor ou atualiza o nome de um existente."""
    with db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO guilds (guild_id, guild_name) VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET guild_name = excluded.guild_name
        """, (guild_id, guild_name))
        return cursor.rowcount > 0

def unregister_guild(guild_id):
    """Remove um servidor do banco de dados."""
    with db_cursor() as cursor:
        cursor.execute("DELETE FROM guilds WHERE guild_id = ?", (guild_id,))
        return cursor.rowcount > 0

def get_all_guilds():
    """Retorna todos os servidores registrados."""
    with db_cursor() as cursor:
        cursor.execute("SELECT guild_id, guild_name FROM guilds")
        return cursor.fetchall()

# --- Funções de Profissão (Jobs) ---

def get_all_jobs():
    """Retorna todas as profissões disponíveis."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM jobs ORDER BY level_req")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_job_by_id(job_id):
    """Retorna os detalhes de uma profissão pelo ID."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
    return None

def set_player_job(user_id, job_id):
    """Define o emprego de um jogador e atualiza os timestamps."""
    with db_cursor() as cursor:
        if job_id:
            # Começando um novo emprego
            cursor.execute("UPDATE characters SET current_job_id = ?, job_started_at = CURRENT_TIMESTAMP, last_job_change = CURRENT_TIMESTAMP, last_work_check_in = CURRENT_TIMESTAMP WHERE user_id = ?", (job_id, user_id))
        else:
            # Saindo do emprego
            cursor.execute("UPDATE characters SET current_job_id = NULL, job_started_at = NULL WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0

def get_player_job_progress(user_id, job_id):
    """Retorna as horas trabalhadas de um jogador em um emprego específico."""
    with db_cursor() as cursor:
        cursor.execute("SELECT hours_worked FROM player_jobs_progress WHERE character_user_id = ? AND job_id = ?", (user_id, job_id))
        result = cursor.fetchone()
        return result[0] if result else 0

def update_player_job_progress(user_id, job_id, hours_to_add):
    """Adiciona horas ao progresso de um emprego do jogador."""
    with db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO player_jobs_progress (character_user_id, job_id, hours_worked) VALUES (?, ?, ?)
            ON CONFLICT(character_user_id, job_id) DO UPDATE SET hours_worked = hours_worked + excluded.hours_worked
        """, (user_id, job_id, hours_to_add))
        return cursor.rowcount > 0

def reset_player_job_progress(user_id, job_id):
    """Reseta as horas trabalhadas de um jogador para um emprego específico (usado após o payday)."""
    with db_cursor() as cursor:
        cursor.execute("""
            UPDATE player_jobs_progress SET hours_worked = 0
            WHERE character_user_id = ? AND job_id = ?
        """, (user_id, job_id))
        return cursor.rowcount > 0

# --- Funções do Mercado ---

def get_market_listings(page=1, per_page=10, search_term=None):
    """Busca anúncios no mercado com paginação e pesquisa."""
    with db_cursor() as cursor:
        query = """
            SELECT m.id, m.quantity, m.price, m.enhancement_level, l.name, c.name as seller_name
            FROM market_listings m
            JOIN loot_table l ON m.item_id = l.id
            JOIN characters c ON m.seller_id = c.user_id
        """
        params = []
        if search_term:
            query += " WHERE l.name LIKE ?"
            params.append(f"%{search_term}%")
        
        offset = (page - 1) * per_page
        query += " ORDER BY m.listed_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        cursor.execute(query, tuple(params))
        return cursor.fetchall()

def count_market_listings(search_term=None):
    """Conta o total de anúncios no mercado."""
    with db_cursor() as cursor:
        query = "SELECT COUNT(*) FROM market_listings"
        params = []
        if search_term:
            query += " m JOIN loot_table l ON m.item_id = l.id WHERE l.name LIKE ?"
            params.append(f"%{search_term}%")
        
        cursor.execute(query, tuple(params))
        return cursor.fetchone()[0]

def get_market_listing_by_id(listing_id):
    """Busca um anúncio específico pelo ID."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM market_listings WHERE id = ?", (listing_id,))
        listing_data = cursor.fetchone()
        if listing_data:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, listing_data))
    return None

def create_market_listing(seller_id, item_id, quantity, price, enhancement_level):
    """Cria um novo anúncio no mercado."""
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO market_listings (seller_id, item_id, quantity, price, enhancement_level) VALUES (?, ?, ?, ?, ?)",
            (seller_id, item_id, quantity, price, enhancement_level)
        )
        return cursor.lastrowid

def remove_market_listing(listing_id):
    """Remove um anúncio do mercado."""
    with db_cursor() as cursor:
        cursor.execute("DELETE FROM market_listings WHERE id = ?", (listing_id,))
        return cursor.rowcount > 0

def get_leaderboard(sort_by='level', limit=10):
    """Busca dados para o placar de líderes."""
    with db_cursor() as cursor:
        if sort_by == 'level':
            query = "SELECT name, level, experience FROM characters ORDER BY level DESC, experience DESC LIMIT ?"
        elif sort_by == 'pvp':
            # Calcula o score como (vitórias - derrotas)
            query = "SELECT name, pvp_wins, pvp_losses, (pvp_wins - pvp_losses) as score FROM characters ORDER BY score DESC, pvp_wins DESC LIMIT ?"
        else:
            return []
        
        cursor.execute(query, (limit,))
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


if __name__ == "__main__":
    # Exemplo de uso e inicialização do DB
    init_db()
    # Você pode adicionar mais testes aqui para create_character, get_character, etc.
    # print(get_character(123))