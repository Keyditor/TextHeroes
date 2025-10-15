# --- Constantes do Jogo ---

RACES = ["Humano", "Elfo", "Anão", "Halfling", "Meio-Orc", "Thiefling"]
CLASSES = ["Guerreiro", "Ladino", "Feiticeiro", "Bardo", "Clérigo", "Patrulheiro"]

# Detalhes das Raças (Bônus/Ônus de Atributos)
RACE_MODIFIERS = {
    "Humano": {"strength": 1, "constitution": 1, "dexterity": 1, "intelligence": 1, "wisdom": 1, "charisma": 1},
    "Elfo": {"dexterity": 3, "intelligence": 2, "constitution": -1},
    "Anão": {"constitution": 3, "strength": 2, "dexterity": -1},
    "Halfling": {"dexterity": 3, "charisma": 2, "strength": -1},
    "Meio-Orc": {"strength": 3, "constitution": 2, "intelligence": -1},
    "Thiefling": {"intelligence": 2, "charisma": 3, "wisdom": -1},
}

# Detalhes das Classes (Atributo Chave)
CLASS_DETAILS = {
    "Guerreiro": {"key_attribute": "strength", "type": "physical"},
    "Ladino": {"key_attribute": "dexterity", "type": "physical"},
    "Feiticeiro": {"key_attribute": "intelligence", "type": "magical"},
    "Bardo": {"key_attribute": "charisma", "type": "magical"},
    "Clérigo": {"key_attribute": "wisdom", "type": "magical"},
    "Patrulheiro": {"key_attribute": "dexterity", "type": "physical"},
}

# Mapeamento para o banco de dados
ATTRIBUTE_MAP_PT_EN = {
    "força": "strength", "constituição": "constitution", "destreza": "dexterity",
    "inteligência": "intelligence", "sabedoria": "wisdom", "carisma": "charisma"
}

ATTRIBUTE_MAP_EN_PT = {v: k.capitalize() for k, v in ATTRIBUTE_MAP_PT_EN.items()}

TOTAL_ATTRIBUTE_POINTS = 24
MIN_ATTRIBUTE_VALUE = 8
MAX_ATTRIBUTE_VALUE = 15

XP_PER_LEVEL_MULTIPLIER = 100