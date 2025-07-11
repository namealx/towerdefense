import pygame
import numpy as np
import math
import os
from scipy.io import wavfile

# --- Инициализация Pygame ---
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

# --- Основные настройки ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# --- Настройки UI ---
RIGHT_PANEL_WIDTH = 240
GAME_AREA_WIDTH = SCREEN_WIDTH - RIGHT_PANEL_WIDTH

# --- Цвета ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
RED = (220, 20, 60)
GREEN = (50, 205, 50)
BLUE = (65, 105, 225)
YELLOW = (255, 215, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 140, 0)
DARK_GREEN = (0, 100, 0)
SLATE_GREY = (112, 128, 144)
INDIGO = (75, 0, 130)
BROWN = (139, 69, 19)

# Цвета для графики
BG_COLOR_1 = (27, 68, 41)
BG_COLOR_2 = (87, 65, 47)
PATH_COLOR = (119, 101, 89)
PANEL_COLOR = (40, 40, 50)
BUTTON_LOCKED_COLOR = (112, 128, 144)
UPGRADE_BAR_COLOR = (218, 165, 32)  # Золотой цвет для полосок улучшений

# --- Настройки прокачки ---
UPGRADE_LEVEL_COSTS = [0.8, 1.0, 1.2]
UPGRADE_BONUS = 0.4
SELL_RATIO = 0.7
MAX_UPGRADE_LEVEL = 3

# --- Шрифты ---
try:
    FONT_MAIN = pygame.font.Font("assets/fonts/main_font.ttf", 40)
    FONT_SMALL = pygame.font.Font("assets/fonts/small_font.ttf", 28)
    FONT_TINY = pygame.font.Font("assets/fonts/tiny_font.ttf", 22)
except FileNotFoundError as e:
    print(f"Error loading fonts: {e}")
    FONT_MAIN = pygame.font.SysFont("arial", 40)
    FONT_SMALL = pygame.font.SysFont("arial", 28)
    FONT_TINY = pygame.font.SysFont("arial", 22)

# --- Генерация звуков ---
def generate_sound(frequency=440, duration=0.1, volume=0.1, decay=True):
    try:
        sample_rate = pygame.mixer.get_init()[0]
        n_samples = int(round(duration * sample_rate))
        buf = np.zeros((n_samples, 2), dtype=np.int16)
        max_sample = 2**(15) - 1
        amplitude = max_sample * volume
        arr = np.arange(n_samples)
        waveform = np.sin(2 * np.pi * frequency * arr / sample_rate)
        if decay:
            decay_rate = -5.0 / n_samples
            decay_arr = np.exp(decay_rate * arr)
            waveform *= decay_arr
        buf[:, 0] = (waveform * amplitude).astype(np.int16)
        buf[:, 1] = (waveform * amplitude).astype(np.int16)
        return pygame.sndarray.make_sound(buf)
    except (ImportError, pygame.error):
        return None

# Звуки с различными параметрами для разных событий
SHOOT_SOUND = generate_sound(frequency=880, duration=0.05, volume=0.1)  # Короткий высокий звук для выстрела
HIT_SOUND = generate_sound(frequency=220, duration=0.08, volume=0.2)  # Низкий звук для попадания
PLACE_TOWER_SOUND = generate_sound(frequency=660, duration=0.1, volume=0.1)  # Средний звук для размещения башни
UPGRADE_SOUND = generate_sound(frequency=1200, duration=0.1, volume=0.15)  # Высокий звук для улучшения
SELL_SOUND = generate_sound(frequency=440, duration=0.15, volume=0.15, decay=False)  # Постоянный звук для продажи

# Фоновая музыка (если файл отсутствует, используем резервный вариант)
BACKGROUND_MUSIC = None
try:
    pygame.mixer.music.load("assets/sounds/background_music.mp3")
    BACKGROUND_MUSIC = True
except pygame.error:
    print("Warning: Failed to load background_music.mp3, using generated fallback.")
    try:
        # Генерируем простую фоновую музыку как резерв
        sample_rate = pygame.mixer.get_init()[0]
        duration = 60  # 1 минута
        n_samples = int(round(duration * sample_rate))
        buf = np.zeros((n_samples, 2), dtype=np.int16)
        max_sample = 2**(15) - 1
        amplitude = max_sample * 0.05
        arr = np.arange(n_samples)
        waveform = np.sin(2 * np.pi * 220 * arr / sample_rate) + 0.5 * np.sin(2 * np.pi * 440 * arr / sample_rate)
        decay_rate = -0.001 / n_samples
        decay_arr = np.exp(decay_rate * arr)
        waveform *= decay_arr
        buf[:, 0] = (waveform * amplitude).astype(np.int16)
        buf[:, 1] = (waveform * amplitude).astype(np.int16)
        # Сохраняем в временный WAV-файл с помощью scipy
        temp_wav = "temp_background_music.wav"
        wavfile.write(temp_wav, sample_rate, buf)
        pygame.mixer.music.load(temp_wav)
        BACKGROUND_MUSIC = True
    except (ImportError, pygame.error, OSError):
        BACKGROUND_MUSIC = None

# --- Функция для загрузки и масштабирования изображений ---
def load_images():
    global ENEMY_IMAGES, TOWER_IMAGES, PROJECTILE_IMAGES, UI_IMAGES
    # Заглушка для отсутствующих изображений
    placeholder_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
    placeholder_surface.fill((255, 0, 0, 128))  # Полупрозрачный красный квадрат

    def load_image(paths, size):
        for path in paths:
            if os.path.exists(path):
                try:
                    image = pygame.image.load(path)
                    # Переконвертируем изображение для устранения проблем с цветовым профилем
                    image = image.convert_alpha()
                    return pygame.transform.scale(image, size)
                except pygame.error as e:
                    print(f"Error loading image {path}: {e}")
        print(f"Error: None of the paths exist or are invalid for {paths}")
        return placeholder_surface

    ENEMY_IMAGES = {
        "goblin": load_image(["assets/images/enemies/goblin.png", "assets/images/goblin.png"], (25, 25)),
        "orc": load_image(["assets/images/enemies/orc.png", "assets/images/orc.png"], (35, 35)),
        "knight": load_image(["assets/images/enemies/knight.png", "assets/images/knight.png"], (30, 30)),
        "rogue": load_image(["assets/images/enemies/rogue.png", "assets/images/rogue.png"], (20, 20)),
        "slime": load_image(["assets/images/enemies/slime.png", "assets/images/slime.png"], (30, 20)),
        "small_slime": load_image(["assets/images/enemies/small_slime.png", "assets/images/small_slime.png"], (15, 10))
    }

    TOWER_IMAGES = {
        "archer": load_image(["assets/images/towers/archer.png", "assets/images/archer.png"], (70, 70)),
        "cannon": load_image(["assets/images/towers/cannon.png", "assets/images/cannon.png"], (70, 70)),
        "mage": load_image(["assets/images/towers/mage.png", "assets/images/mage.png"], (70, 70))
    }

    PROJECTILE_IMAGES = {
        "arrow": load_image(["assets/images/projectiles/arrow.png", "assets/images/projectile_arrow.png", "assets/images/arrow.png"], (25, 5)),
        "cannonball": load_image(["assets/images/projectiles/cannonball.png", "assets/images/projectile_cannonball.png", "assets/images/cannonball.png"], (17, 17)),
        "magic_bolt": load_image(["assets/images/projectiles/magic_bolt.png", "assets/images/projectile_magic_bolt.png", "assets/images/magic_bolt.png"], (12, 12))
    }

    UI_IMAGES = {
        "heart": load_image(["assets/images/ui/heart.png", "assets/images/heart.png"], (30, 30)),
        "coin": load_image(["assets/images/ui/coin.png", "assets/images/coin.png"], (30, 30)),
        "star": load_image(["assets/images/ui/star.png", "assets/images/star.png"], (25, 25)),
        "star_empty": load_image(["assets/images/ui/star_empty.png", "assets/images/empty.png"], (25, 25)),
        "settings_gear": load_image(["assets/images/ui/settings_gear.png", "assets/images/gear.png"], (40, 40))
    }

# Инициализация словарей как пустых до вызова load_images
ENEMY_IMAGES = {}
TOWER_IMAGES = {}
PROJECTILE_IMAGES = {}
UI_IMAGES = {}

# --- Данные о юнитах ---
ENEMY_DATA = {
    "goblin": {"health": 100, "speed": 2.0, "reward": 10, "image": None},
    "orc": {"health": 250, "speed": 1.5, "reward": 25, "image": None},
    "knight": {"health": 600, "speed": 1.0, "reward": 50, "image": None},
    "rogue": {"health": 80, "speed": 3.5, "reward": 20, "image": None, "steals_gold": 50},
    "slime": {"health": 150, "speed": 1.8, "reward": 20, "image": None, "spawns_on_death": ("small_slime", 2)},
    "small_slime": {"health": 50, "speed": 2.5, "reward": 5, "image": None}
}

TOWER_DATA = {
    "archer": {"cost": 100, "range": 200, "damage": 40, "fire_rate": 1000, "projectile": "arrow", "image": None},
    "cannon": {"cost": 250, "range": 150, "damage": 100, "fire_rate": 2000, "projectile": "cannonball", "image": None},
    "mage": {"cost": 175, "range": 180, "damage": 20, "fire_rate": 1500, "projectile": "magic_bolt", "image": None, "slow_effect": (0.5, 2000)}
}

PROJECTILE_DATA = {
    "arrow": {"speed": 10, "image": None},
    "cannonball": {"speed": 7, "image": None},
    "magic_bolt": {"speed": 8, "image": None}
}

# --- Обновление данных о юнитах после загрузки изображений ---
def update_unit_data():
    for key in ENEMY_DATA:
        ENEMY_DATA[key]["image"] = ENEMY_IMAGES.get(key, None)
    for key in TOWER_DATA:
        TOWER_DATA[key]["image"] = TOWER_IMAGES.get(key, None)
    for key in PROJECTILE_DATA:
        PROJECTILE_DATA[key]["image"] = PROJECTILE_IMAGES.get(key, None)

LEVELS_CONFIG = {
    1: {"bg_color": BG_COLOR_1, "path": [(0, 300), (200, 300), (200, 150), (450, 150), (450, 450), (800, 450), (800, 250), (950, 250), (950, 600), (GAME_AREA_WIDTH + 50, 600)], "waves": [{"goblin": 10}, {"goblin": 15, "rogue": 5}, {"goblin": 20, "orc": 2}, {"goblin": 15, "orc": 5},{"goblin": 10, "orc": 10}, {"goblin": 25, "orc": 8, "rogue": 10}, {"goblin": 0, "orc": 15}]},
    2: {"bg_color": BG_COLOR_2, "path": [(0, 100), (400, 100), (400, 300), (100, 300), (100, 500), (600, 500), (600, 200), (900, 200), (900, 600), (GAME_AREA_WIDTH + 50, 600)], "waves": [{"goblin": 15, "orc": 2}, {"goblin": 20, "rogue": 8}, {"goblin": 25, "orc": 8}, {"goblin": 15, "orc": 12, "slime": 5}, {"goblin": 10, "orc": 15}, {"knight": 5, "orc": 10}, {"goblin": 10, "orc": 20}, {"rogue": 20, "orc": 25}]},
    3: {"bg_color": BG_COLOR_1, "path": [(120, 0), (120, 400), (400, 400), (400, 150), (700, 150), (700, 550), (900, 550), (900, 300), (GAME_AREA_WIDTH + 50, 300)], "waves": [{"goblin": 20, "orc": 5}, {"rogue": 15, "goblin": 10}, {"knight": 5, "orc": 5}, {"slime": 10}, {"goblin": 30, "orc": 10}, {"knight": 8, "rogue": 15}, {"slime": 15, "orc": 15}, {"knight": 10, "orc": 20}, {"goblin": 50, "rogue": 30}]},
    4: {"bg_color": BG_COLOR_2, "path": [(0, 360), (1000, 360), (1000, 100), (100, 100), (100, 600), (900, 600), (900, 200), (GAME_AREA_WIDTH + 50, 200)], "waves": [{"orc": 20, "knight": 5}, {"slime": 15, "rogue": 20}, {"goblin": 40, "orc": 15}, {"knight": 15, "slime": 10}, {"rogue": 40, "orc": 20}, {"goblin": 50, "knight": 10}, {"slime": 25, "orc": 25}, {"knight": 20, "rogue": 30}, {"goblin": 100}, {"orc": 50, "knight": 25}]},
    5: {"bg_color": BG_COLOR_1, "path": [(0, 100), (200, 100), (200, 500), (400, 500), (400, 200), (600, 200), (600, 600), (800, 600), (800, 100), (950, 100), (950, 400), (GAME_AREA_WIDTH + 50, 400)], "waves": [{"knight": 10, "slime": 10}, {"goblin": 50, "rogue": 20}, {"orc": 30, "knight": 15}, {"slime": 20, "rogue": 30}, {"goblin": 70, "orc": 20}, {"knight": 25, "rogue": 25}, {"slime": 30, "orc": 30}, {"goblin": 80, "knight": 15}, {"orc": 50, "rogue": 40}, {"slime": 40, "knight": 20}, {"goblin": 100, "orc": 50, "knight": 30, "rogue": 50, "slime": 25}]}
}