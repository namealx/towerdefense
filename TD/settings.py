import pygame
import numpy as np
import math
import os
from scipy.io import wavfile

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

RIGHT_PANEL_WIDTH = 240
GAME_AREA_WIDTH = SCREEN_WIDTH - RIGHT_PANEL_WIDTH

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

BG_COLOR_1 = (124, 153, 2)
BG_COLOR_2 = (197, 146, 70)
BG_COLOR_3 = (109, 93, 105)
BG_COLOR_4 = (239, 239, 239)
BG_COLOR_5 = (107, 101, 108)
PATH_COLOR = (119, 101, 89)
PANEL_COLOR = (40, 40, 50)
BUTTON_LOCKED_COLOR = (112, 128, 144)
UPGRADE_BAR_COLOR = (218, 165, 32)

UPGRADE_LEVEL_COSTS = [0.8, 1.0, 1.2]
UPGRADE_BONUS = 0.4
SELL_RATIO = 0.7
MAX_UPGRADE_LEVEL = 3

FONT_MAIN = pygame.font.SysFont("arial", 40)
FONT_SMALL = pygame.font.SysFont("arial", 28)
FONT_TINY = pygame.font.SysFont("arial", 22)

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

SHOOT_SOUND = generate_sound(frequency=880, duration=0.05, volume=0.1)
HIT_SOUND = generate_sound(frequency=220, duration=0.08, volume=0.2)
PLACE_TOWER_SOUND = generate_sound(frequency=660, duration=0.1, volume=0.1)
UPGRADE_SOUND = generate_sound(frequency=1200, duration=0.1, volume=0.15)
SELL_SOUND = generate_sound(frequency=440, duration=0.15, volume=0.15, decay=False)

BACKGROUND_MUSIC = True
try:
    pygame.mixer.music.load("assets/sounds/background_music.mp3")
except pygame.error:
    try:
        sample_rate = pygame.mixer.get_init()[0]
        duration = 60
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
        temp_wav = "temp_background_music.wav"
        wavfile.write(temp_wav, sample_rate, buf)
        pygame.mixer.music.load(temp_wav)
    except (ImportError, pygame.error, OSError):
        BACKGROUND_MUSIC = False

def load_images():
    global ENEMY_IMAGES, TOWER_IMAGES, PROJECTILE_IMAGES, UI_IMAGES, LEVEL_IMAGES, ROAD_IMAGES, DECORATION_IMAGES
    placeholder_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
    placeholder_surface.fill((255, 0, 0, 128))

    def load_image(paths, size):
        for path in paths:
            if os.path.exists(path):
                try:
                    image = pygame.image.load(path)
                    image = image.convert_alpha()
                    return pygame.transform.scale(image, size)
                except pygame.error:
                    pass
        return placeholder_surface

    ENEMY_IMAGES = {
        "goblin": load_image(["assets/images/enemies/goblin.png"], (25, 25)),
        "orc": load_image(["assets/images/enemies/orc.png"], (35, 35)),
        "knight": load_image(["assets/images/enemies/knight.png"], (30, 30)),
        "rogue": load_image(["assets/images/enemies/rogue.png"], (20, 20)),
        "slime": load_image(["assets/images/enemies/slime.png"], (30, 20)),
        "small_slime": load_image(["assets/images/enemies/small_slime.png"], (15, 10))
    }

    TOWER_IMAGES = {
        "archer": load_image(["assets/images/towers/archer.png"], (70, 70)),
        "cannon": load_image(["assets/images/towers/cannon.png"], (70, 70)),
        "mage": load_image(["assets/images/towers/mage.png"], (70, 70))
    }

    PROJECTILE_IMAGES = {
        "arrow": load_image(["assets/images/projectiles/arrow.png"], (25, 5)),
        "cannonball": load_image(["assets/images/projectiles/cannonball.png"], (17, 17)),
        "magic_bolt": load_image(["assets/images/projectiles/magic_bolt.png"], (12, 12))
    }

    UI_IMAGES = {
        "heart": load_image(["assets/images/ui/heart.png"], (30, 30)),
        "coin": load_image(["assets/images/ui/coin.png"], (30, 30)),
        "star": load_image(["assets/images/ui/star.png"], (25, 25)),
        "star_empty": load_image(["assets/images/ui/star_empty.png"], (25, 25)),
        "settings_gear": load_image(["assets/images/ui/settings_gear.png"], (40, 40))
    }

    LEVEL_IMAGES = {
        "level_1_background": load_image(["assets/images/backgrounds/level_1_background.png"], (GAME_AREA_WIDTH, SCREEN_HEIGHT))
    }

    ROAD_IMAGES = {
        "road_1_1": load_image(["assets/images/decorations/road_1_1.png"], (100, 100)),
        "road_1_2": load_image(["assets/images/decorations/road_1_2.png"], (100, 100)),
        "road_1_3": load_image(["assets/images/decorations/road_1_3.png"], (100, 100)),
        "road_1_4": load_image(["assets/images/decorations/road_1_4.png"], (100, 100)),
        "road_1_5": load_image(["assets/images/decorations/road_1_5.png"], (100, 100)),
        "road_1_6": load_image(["assets/images/decorations/road_1_6.png"], (100, 70)),
        "road_1_7": load_image(["assets/images/decorations/road_1_7.png"], (75, 100)),
        "road_2_1": load_image(["assets/images/decorations/road_2_1.png"], (115, 115)),
        "road_2_2": load_image(["assets/images/decorations/road_2_2.png"], (115, 115)),
        "road_2_3": load_image(["assets/images/decorations/road_2_3.png"], (115, 115)),
        "road_2_4": load_image(["assets/images/decorations/road_2_4.png"], (115, 115)),
        "road_2_5": load_image(["assets/images/decorations/road_2_5.png"], (100, 80)),
        "road_2_6": load_image(["assets/images/decorations/road_2_6.png"], (80, 100)),
        "road_2_7": load_image(["assets/images/decorations/road_2_7.png"], (230, 120)),
        "road_3_1": load_image(["assets/images/decorations/road_3_1.png"], (120, 120)),
        "road_3_2": load_image(["assets/images/decorations/road_3_2.png"], (120, 120)),
        "road_3_3": load_image(["assets/images/decorations/road_3_3.png"], (120, 120)),
        "road_3_4": load_image(["assets/images/decorations/road_3_4.png"], (120, 120)),
        "road_3_5": load_image(["assets/images/decorations/road_3_5.png"], (100, 80)),
        "road_3_6": load_image(["assets/images/decorations/road_3_6.png"], (80, 100)),
        "road_4_1": load_image(["assets/images/decorations/road_4_1.png"], (120, 120)),
        "road_4_2": load_image(["assets/images/decorations/road_4_2.png"], (120, 120)),
        "road_4_3": load_image(["assets/images/decorations/road_4_3.png"], (120, 120)),
        "road_4_4": load_image(["assets/images/decorations/road_4_4.png"], (120, 120)),
        "road_4_5": load_image(["assets/images/decorations/road_4_5.png"], (100, 80)),
        "road_4_6": load_image(["assets/images/decorations/road_4_6.png"], (80, 100)),
        "road_4_7": load_image(["assets/images/decorations/road_4_7.png"], (240, 125)),
        "road_5_1": load_image(["assets/images/decorations/road_5_1.png"], (120, 120)),
        "road_5_2": load_image(["assets/images/decorations/road_5_2.png"], (120, 120)),
        "road_5_3": load_image(["assets/images/decorations/road_5_3.png"], (120, 120)),
        "road_5_4": load_image(["assets/images/decorations/road_5_4.png"], (120, 120)),
        "road_5_5": load_image(["assets/images/decorations/road_5_5.png"], (100, 80)),
        "road_5_6": load_image(["assets/images/decorations/road_5_6.png"], (80, 100)),
        "road_5_7": load_image(["assets/images/decorations/road_5_7.png"], (240, 120)),
        "road_5_8": load_image(["assets/images/decorations/road_5_8.png"], (125, 240))

    }

    DECORATION_IMAGES = {
        "windmill_1_1": load_image(["assets/images/decorations/windmill_1_1.png"], (180, 180)),
        "house_1_1": load_image(["assets/images/decorations/house_1_1.png"], (100, 100)),
        "dec_1_1": load_image(["assets/images/decorations/dec_1_1.png"], (100, 100)),
        "dec_1_2": load_image(["assets/images/decorations/dec_1_2.png"], (35, 35)),
        "dec_1_3": load_image(["assets/images/decorations/dec_1_3.png"], (150, 150)),
        "dec_1_4": load_image(["assets/images/decorations/dec_1_4.png"], (50, 40)),
        "dec_1_5": load_image(["assets/images/decorations/dec_1_5.png"], (20, 20)),
        "dec_1_6": load_image(["assets/images/decorations/dec_1_6.png"], (50, 50)),
        "dec_1_7": load_image(["assets/images/decorations/dec_1_7.png"], (20, 20)),
        "dec_1_8": load_image(["assets/images/decorations/dec_1_8.png"], (50, 100)),
        "dec_1_9": load_image(["assets/images/decorations/dec_1_9.png"], (90, 40)),
        "dec_2_1": load_image(["assets/images/decorations/dec_2_1.png"], (100, 100)),
        "dec_2_2": load_image(["assets/images/decorations/dec_2_2.png"], (35, 35)),
        "dec_2_3": load_image(["assets/images/decorations/dec_2_3.png"], (150, 150)),
        "dec_2_4": load_image(["assets/images/decorations/dec_2_4.png"], (50, 40)),
        "dec_2_5": load_image(["assets/images/decorations/dec_2_5.png"], (20, 20)),
        "dec_2_6": load_image(["assets/images/decorations/dec_2_6.png"], (50, 50)),
        "dec_2_7": load_image(["assets/images/decorations/dec_2_7.png"], (20, 20)),
        "dec_2_8": load_image(["assets/images/decorations/dec_2_8.png"], (50, 100)),
        "dec_2_9": load_image(["assets/images/decorations/dec_2_9.png"], (90, 40)),
        "dec_2_10": load_image(["assets/images/decorations/dec_2_10.png"], (20, 20)),
        "dec_2_11": load_image(["assets/images/decorations/dec_2_11.png"], (50, 100)),
        "dec_3_1": load_image(["assets/images/decorations/dec_3_1.png"], (100, 100)),
        "dec_3_2": load_image(["assets/images/decorations/dec_3_2.png"], (35, 35)),
        "dec_3_3": load_image(["assets/images/decorations/dec_3_3.png"], (150, 150)),
        "dec_3_4": load_image(["assets/images/decorations/dec_3_4.png"], (50, 40)),
        "dec_3_5": load_image(["assets/images/decorations/dec_3_5.png"], (20, 20)),
        "dec_3_6": load_image(["assets/images/decorations/dec_3_6.png"], (50, 50)),
        "dec_3_7": load_image(["assets/images/decorations/dec_3_7.png"], (20, 20)),
        "dec_3_8": load_image(["assets/images/decorations/dec_3_8.png"], (50, 100)),
        "dec_3_9": load_image(["assets/images/decorations/dec_3_9.png"], (90, 40)),
        "dec_3_10": load_image(["assets/images/decorations/dec_3_10.png"], (20, 20)),
        "dec_3_11": load_image(["assets/images/decorations/dec_3_11.png"], (50, 100)),
        "dec_3_12": load_image(["assets/images/decorations/dec_3_12.png"], (50, 100)),
        "dec_4_1": load_image(["assets/images/decorations/dec_4_1.png"], (500, 400)),
        "dec_4_2": load_image(["assets/images/decorations/dec_4_2.png"], (35, 35)),
        "dec_4_3": load_image(["assets/images/decorations/dec_4_3.png"], (150, 150)),
        "dec_4_4": load_image(["assets/images/decorations/dec_4_4.png"], (50, 40)),
        "dec_4_5": load_image(["assets/images/decorations/dec_4_5.png"], (20, 20)),
        "dec_4_6": load_image(["assets/images/decorations/dec_4_6.png"], (50, 50)),
        "dec_5_1": load_image(["assets/images/decorations/dec_5_1.png"], (650, 230)),
        "dec_5_2": load_image(["assets/images/decorations/dec_5_2.png"], (390, 140)),
        "dec_5_3": load_image(["assets/images/decorations/dec_5_3.png"], (170, 210)),
        "dec_5_4": load_image(["assets/images/decorations/dec_5_4.png"], (50, 40)),
        "dec_5_5": load_image(["assets/images/decorations/dec_5_5.png"], (230, 250)),
        "dec_5_6": load_image(["assets/images/decorations/dec_5_6.png"], (50, 50)),
        "dec_5_7": load_image(["assets/images/decorations/dec_5_7.png"], (20, 20)),
        "dec_5_8": load_image(["assets/images/decorations/dec_5_8.png"], (50, 100)),
        "dec_5_9": load_image(["assets/images/decorations/dec_5_9.png"], (90, 40)),
        "dec_5_10": load_image(["assets/images/decorations/dec_5_10.png"], (100, 100)),
        "dec_5_11": load_image(["assets/images/decorations/dec_5_11.png"], (35, 35)),
        "dec_5_12": load_image(["assets/images/decorations/dec_5_12.png"], (150, 150)),
        "dec_5_13": load_image(["assets/images/decorations/dec_5_13.png"], (50, 40)),
        "dec_5_14": load_image(["assets/images/decorations/dec_5_14.png"], (20, 20)),
        "dec_5_15": load_image(["assets/images/decorations/dec_5_15.png"], (50, 50)),
        "dec_5_16": load_image(["assets/images/decorations/dec_5_16.png"], (20, 20)),
        "dec_5_17": load_image(["assets/images/decorations/dec_5_17.png"], (50, 100)),
        "dec_5_18": load_image(["assets/images/decorations/dec_5_18.png"], (90, 40)),
        "dec_5_19": load_image(["assets/images/decorations/dec_5_19.png"], (90, 40)),
        "river_1_1": load_image(["assets/images/decorations/river_1_1.png"], (83, 83)),
        "river_1_2": load_image(["assets/images/decorations/river_1_2.png"], (83, 83)),
        "river_1_3": load_image(["assets/images/decorations/river_1_3.png"], (83, 83)),
        "river_1_4": load_image(["assets/images/decorations/river_1_4.png"], (83, 83)),
        "river_1_5": load_image(["assets/images/decorations/river_1_5.png"], (50, 50)),
        "river_1_6": load_image(["assets/images/decorations/river_1_6.png"], (50, 50)),
        "river_3_1": load_image(["assets/images/decorations/river_3_1.png"], (83, 83)),
        "river_3_2": load_image(["assets/images/decorations/river_3_2.png"], (83, 83)),
        "river_3_3": load_image(["assets/images/decorations/river_3_3.png"], (83, 83)),
        "river_3_4": load_image(["assets/images/decorations/river_3_4.png"], (83, 83)),
        "river_3_5": load_image(["assets/images/decorations/river_3_5.png"], (50, 50)),
        "river_3_6": load_image(["assets/images/decorations/river_3_6.png"], (80, 100)),
        "bridge_1_1": load_image(["assets/images/decorations/bridge_1_1.png"], (50, 50)),
        "bridge_1_2": load_image(["assets/images/decorations/bridge_1_2.png"], (75, 50)),
        "bridge_1_3": load_image(["assets/images/decorations/bridge_1_3.png"], (50, 75)),
        "bridge_3_1": load_image(["assets/images/decorations/bridge_1_2.png"], (160, 110))
    }

ENEMY_IMAGES = {}
TOWER_IMAGES = {}
PROJECTILE_IMAGES = {}
UI_IMAGES = {}
LEVEL_IMAGES = {}
ROAD_IMAGES = {}
DECORATION_IMAGES = {}

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

def update_unit_data():
    for key in ENEMY_DATA:
        ENEMY_DATA[key]["image"] = ENEMY_IMAGES.get(key, None)
    for key in TOWER_DATA:
        TOWER_DATA[key]["image"] = TOWER_IMAGES.get(key, None)
    for key in PROJECTILE_DATA:
        PROJECTILE_DATA[key]["image"] = PROJECTILE_IMAGES.get(key, None)

LEVELS_CONFIG = {
    1: {
        "bg_color": BG_COLOR_1,
        "path": [(0, 310), (170, 310), (210, 280), (210, 150), (240, 110), (450, 110), (470, 130), (470, 420), (500, 450), (780, 450), (810, 420), (810, 280), (840, 250), (960, 250), (990, 280), (990, 570), (1020, 600), (GAME_AREA_WIDTH + 50, 600)],
        "waves": [{"goblin": 10}, {"goblin": 15, "rogue": 5}, {"goblin": 20, "orc": 2}, {"goblin": 15, "orc": 5}, {"goblin": 10, "orc": 10}, {"goblin": 25, "orc": 8, "rogue": 10}, {"goblin": 0, "orc": 15}],
        "decorations": [
            
            
            {"type": "dec_1_5", "pos": (200, 100)},
            {"type": "dec_1_5", "pos": (300, 200)},
            {"type": "dec_1_5", "pos": (630, 80)},

            {"type": "dec_1_4", "pos": (200, 330)},
            {"type": "dec_1_4", "pos": (251, 318)},
            {"type": "dec_1_4", "pos": (227, 341)},

            {"type": "dec_1_4", "pos": (710, 620)},
            {"type": "dec_1_4", "pos": (850, 470)},
            {"type": "dec_1_4", "pos": (912, 468)},
            {"type": "dec_1_4", "pos": (880, 496)},
            {"type": "house_1_1", "pos": (150, 390)},




            {"type": "dec_1_8", "pos": (20, 230)},
            {"type": "dec_1_8", "pos": (1000, 600)},
            {"type": "dec_1_9", "pos": (70, 260)},
            {"type": "dec_1_4", "pos": (600, 100)},
            {"type": "dec_1_4", "pos": (630, 113)},
            {"type": "dec_1_4", "pos": (607, 208)},
            {"type": "dec_1_7", "pos": (170, 140)},
            {"type": "dec_1_7", "pos": (300, 200)},
            {"type": "dec_1_2", "pos": (540, 690)},
            {"type": "dec_1_2", "pos": (500, 700)},
            {"type": "dec_1_2", "pos": (460, 620)},
            {"type": "dec_1_2", "pos": (450, 570)},
            {"type": "dec_1_2", "pos": (490, 565)},
            {"type": "river_1_5", "pos": (600, 695)},
            {"type": "river_1_5", "pos": (600, 646)},
            {"type": "bridge_1_2", "pos": (600, 670)},
            {"type": "river_1_1", "pos": (618, 590)},
            {"type": "river_1_6", "pos": (685, 573)},
            {"type": "river_1_6", "pos": (733, 573)},
            {"type": "river_1_6", "pos": (782, 573)},
            {"type": "river_1_2", "pos": (845, 591)},
            {"type": "river_1_3", "pos": (881, 672)},
            {"type": "river_1_2", "pos": (950, 705)},
            {"type": "bridge_1_3", "pos": (750, 570)},
            {"type": "dec_1_2", "pos": (815, 125)},
            {"type": "dec_1_2", "pos": (855, 134)},
            {"type": "dec_1_2", "pos": (750, 90)},
            {"type": "dec_1_2", "pos": (825, 60)},
            {"type": "dec_1_6", "pos": (430, 600)},
            {"type": "dec_1_6", "pos": (490, 635)},
            {"type": "dec_1_6", "pos": (510, 639)},
            {"type": "dec_1_6", "pos": (500, 665)},

            {"type": "dec_1_3", "pos": (67, 20)},

            {"type": "dec_1_3", "pos": (104, 34)},
            {"type": "dec_1_3", "pos": (189, 27)},
            {"type": "dec_1_3", "pos": (143, 49)},
            {"type": "dec_1_3", "pos": (486, -20)},
            {"type": "dec_1_3", "pos": (537, -15)},
            {"type": "dec_1_3", "pos": (678, -21)},
            {"type": "dec_1_3", "pos": (607, -4)},

            {"type": "dec_1_3", "pos": (20, 40)},

            {"type": "dec_1_3", "pos": (900, 40)},
            {"type": "dec_1_3", "pos": (1000, 25)},
            {"type": "dec_1_3", "pos": (950, 80)},
            {"type": "dec_1_3", "pos": (1030, 65)},
            {"type": "dec_1_3", "pos": (985, 95)},
            {"type": "dec_1_3", "pos": (1025, 105)},
            {"type": "dec_1_3", "pos": (70, 453)},
            {"type": "dec_1_3", "pos": (168, 465)},
            {"type": "dec_1_3", "pos": (40, 513)},
            {"type": "dec_1_3", "pos": (110, 515)},
            {"type": "dec_1_3", "pos": (178, 508)},
            {"type": "dec_1_3", "pos": (263, 520)},
            {"type": "dec_1_3", "pos": (50, 570)},
            {"type": "dec_1_3", "pos": (130, 565)},
            {"type": "dec_1_3", "pos": (175, 578)},
            {"type": "dec_1_3", "pos": (235, 574)},
            {"type": "dec_1_3", "pos": (305, 567)},
            {"type": "dec_1_3", "pos": (370, 564)},
            {"type": "dec_1_3", "pos": (20, 630)},
            {"type": "dec_1_3", "pos": (70, 635)},
            {"type": "dec_1_3", "pos": (115, 628)},
            {"type": "dec_1_3", "pos": (165, 620)},
            {"type": "dec_1_3", "pos": (205, 630)},
            {"type": "dec_1_3", "pos": (270, 634)},
            {"type": "dec_1_3", "pos": (320, 627)},
            {"type": "dec_1_3", "pos": (0, 700)},
            {"type": "dec_1_3", "pos": (50, 690)},
            {"type": "dec_1_3", "pos": (100, 685)},
            {"type": "dec_1_3", "pos": (145, 700)},
            {"type": "dec_1_3", "pos": (205, 695)},
            {"type": "dec_1_3", "pos": (260, 700)},
            {"type": "dec_1_3", "pos": (300, 710)},
            {"type": "dec_1_3", "pos": (360, 675)},
            {"type": "dec_1_3", "pos": (400, 660)},
            {"type": "dec_1_3", "pos": (445, 685)},
            {"type": "dec_1_6", "pos": (850, 95)},
            {"type": "dec_1_6", "pos": (890, 125)},
            {"type": "dec_1_6", "pos": (800, 85)},
            {"type": "dec_1_6", "pos": (940, 137)},
            {"type": "windmill_1_1", "pos": (790, 640)},
            {"type": "dec_1_4", "pos": (567, 46)},
            {"type": "dec_1_4", "pos": (532, 51)},
            {"type": "house_1_1", "pos": (700, 660)},
            {"type": "house_1_1", "pos": (550, 380)},
            {"type": "house_1_1", "pos": (50, 350)},
            {"type": "dec_1_6", "pos": (630, 350)},
            {"type": "dec_1_6", "pos": (660, 362)},
            {"type": "dec_1_7", "pos": (620, 380)},
            {"type": "dec_1_2", "pos": (650, 200)},
            {"type": "dec_1_2", "pos": (590, 350)},
            {"type": "dec_1_2", "pos": (210, 370)},
            {"type": "dec_1_2", "pos": (250, 350)},
            {"type": "dec_1_2", "pos": (280, 450)},
            {"type": "dec_1_2", "pos": (263, 421)},
            {"type": "dec_1_2", "pos": (308, 441)},

            
        ],
        "road_segments": [
            {"type": "road_1_6", "center_left": (-10, 278)},
            {"type": "road_1_6", "center_left": (65, 278)},
            {"type": "road_1_4", "center_left": (145, 245)},
            {"type": "road_1_7", "center_left": (172, 160)},
            {"type": "road_1_1", "center_left": (168, 70)},
            {"type": "road_1_6", "center_left": (252, 77)},
            {"type": "road_1_6", "center_left": (327, 77)},
            {"type": "road_1_2", "center_left": (405, 72)},
            {"type": "road_1_7", "center_left": (433, 155)},
            {"type": "road_1_7", "center_left": (433, 235)},
            {"type": "road_1_7", "center_left": (433, 305)},
            {"type": "road_1_3", "center_left": (433, 385)},
            {"type": "road_1_6", "center_left": (514, 415)},
            {"type": "road_1_6", "center_left": (589, 415)},
            {"type": "road_1_6", "center_left": (664, 415)},
            {"type": "road_1_4", "center_left": (744, 382)},
            {"type": "road_1_7", "center_left": (771, 297)},
            {"type": "road_1_1", "center_left": (767, 207)},
            {"type": "road_1_6", "center_left": (851, 216)},
            {"type": "road_1_2", "center_left": (926, 212)},
            {"type": "road_1_7", "center_left": (954, 300)},
            {"type": "road_1_7", "center_left": (954, 380)},
            {"type": "road_1_7", "center_left": (954, 460)},
            {"type": "road_1_3", "center_left": (954, 540)}
        ]
    },
    2: {
        "bg_color": BG_COLOR_2,
        "path": [(0, 235), (150, 235), (250, 195), (750, 195), (810, 245), (810, 480), (750, 540),(490, 540), (450, 480), (450, 450), (400, 400), (283, 400), (233, 435), (0,435)],
        "waves": [{"goblin": 15, "orc": 2}, {"goblin": 20, "rogue": 8}, {"goblin": 25, "orc": 8}, {"goblin": 15, "orc": 12, "slime": 5}, {"goblin": 10, "orc": 15}, {"knight": 5, "orc": 10}, {"goblin": 10, "orc": 20}, {"rogue": 20, "orc": 25}],
        "decorations": [
            {"type": "dec_1_2", "pos": (150, 150)},
            

        ],
        "road_segments": [
            {"type": "road_2_5", "center_left": (0, 200)},
            {"type": "road_2_7", "center_left": (100, 160)},
            {"type": "road_2_5", "center_left": (330, 160)},
            {"type": "road_2_5", "center_left": (430, 160)},
            {"type": "road_2_5", "center_left": (530, 160)},
            {"type": "road_2_5", "center_left": (630, 160)},
            {"type": "road_2_2", "center_left": (728, 162)},
            {"type": "road_2_6", "center_left": (767, 270)},
            {"type": "road_2_6", "center_left": (767, 368)},
            {"type": "road_2_4", "center_left": (728, 468)},
            {"type": "road_2_5", "center_left": (635, 508)},
            {"type": "road_2_5", "center_left": (535, 508)},
            {"type": "road_2_3", "center_left": (420, 472)},
            {"type": "road_2_2", "center_left": (380, 365)},
            {"type": "road_2_7", "center_left": (153, 361)},
            {"type": "road_2_5", "center_left": (53, 401)},
            {"type": "road_2_5", "center_left": (-47, 401)},


            
        ]
    },
    3: {
        "bg_color": BG_COLOR_3,
        "path": [(0, 530), (130, 530), (170, 500), (170, 470), (210, 380), (270, 380),(325, 340),(335, 330), (340,155), (385,115),(900,115), (950, 165), (950, 210), (900,270), (860,270), (800, 340), (795, 500), (840, 540), (870, 540),(940,590), (950, 720)],
        "waves": [{"goblin": 20, "orc": 5}, {"rogue": 15, "goblin": 10}, {"knight": 5, "orc": 5}, {"slime": 10}, {"goblin": 30, "orc": 10}, {"knight": 8, "rogue": 15}, {"slime": 15, "orc": 15}, {"knight": 10, "orc": 20}, {"goblin": 50, "rogue": 30}],
        "decorations": [
            {"type": "river_3_6", "pos": (660, 100)},
            {"type": "river_3_6", "pos": (660, 140)},
            {"type": "bridge_3_1", "pos": (660, 115)},
        ],
        "road_segments": [
            {"type": "road_3_5", "center_left": (0, 500)},
            {"type": "road_3_4", "center_left": (100, 458)},
            {"type": "road_3_1", "center_left": (140, 340)},
            {"type": "road_3_4", "center_left": (260, 298)},
            {"type": "road_3_6", "center_left": (300, 200)},
            {"type": "road_3_1", "center_left": (300, 82)},
            {"type": "road_3_5", "center_left": (420, 82)},
            {"type": "road_3_5", "center_left": (520, 82)},
            {"type": "road_3_5", "center_left": (670, 82)},
            {"type": "road_3_5", "center_left": (770, 82)},
            {"type": "road_3_2", "center_left": (870, 82)},
            {"type": "road_3_4", "center_left": (870, 199)},
            {"type": "road_3_1", "center_left": (750, 242)},
            {"type": "road_3_6", "center_left": (750, 360)},
            {"type": "road_3_3", "center_left": (750, 460)},
            {"type": "road_3_2", "center_left": (870, 500)},
            {"type": "road_3_6", "center_left": (910, 615)},
            {"type": "road_3_6", "center_left": (910, 715)},

            

        ]
    },
    4: {
        "bg_color": BG_COLOR_4,
        "path": [(1080, 185), (440, 185),(385,235),(385,280),(435,330),(520,360),(560,410),(560,450),(610,500),(620,505),(1080,505) ],
        "waves": [{"orc": 20, "knight": 5}, {"slime": 15, "rogue": 20}, {"goblin": 40, "orc": 15}, {"knight": 15, "slime": 10}, {"rogue": 40, "orc": 20}, {"goblin": 50, "knight": 10}, {"slime": 25, "orc": 25}, {"knight": 20, "rogue": 30}, {"goblin": 100}, {"orc": 50, "knight": 25}],
        "decorations": [
            {"type": "dec_4_1", "pos": (245, 195)},
            
        ],
        "road_segments": [
            {"type": "road_4_5", "center_left": (950, 150)},
            {"type": "road_4_5", "center_left": (850, 150)},
            {"type": "road_4_5", "center_left": (750, 150)},
            {"type": "road_4_5", "center_left": (650, 150)},
            {"type": "road_4_5", "center_left": (550, 150)},
            {"type": "road_4_5", "center_left": (450, 150)},
            {"type": "road_4_1", "center_left": (350, 150)},
            {"type": "road_4_3", "center_left": (350, 270)},
            {"type": "road_4_2", "center_left": (470, 310)},
            {"type": "road_4_3", "center_left": (510, 428)},
            {"type": "road_4_5", "center_left": (630, 470)},
            {"type": "road_4_5", "center_left": (730, 470)},
            {"type": "road_4_5", "center_left": (830, 470)},
            {"type": "road_4_5", "center_left": (930, 470)},
            {"type": "road_4_5", "center_left": (950, 470)},


            
        ]
    },
    5: {
        "bg_color": BG_COLOR_5,
        "path": [(240,720), (240,620),(215,585), (190,570), (125,550),  (85,480),(110,420),(160,400),(260,400),(310,375), (340,320),(340,220), (410, 175),(490,225),(490,350),(525,415), (570,430), (645,390), (655,320),(655,230),(690,180),(690,0)],
        "waves": [{"knight": 10, "slime": 10}, {"goblin": 50, "rogue": 20}, {"orc": 30, "knight": 15}, {"slime": 20, "rogue": 30}, {"goblin": 70, "orc": 20}, {"knight": 25, "rogue": 25}, {"slime": 30, "orc": 30}, {"goblin": 80, "knight": 15}, {"orc": 50, "rogue": 40}, {"slime": 40, "knight": 20}, {"goblin": 100, "orc": 50, "knight": 30, "rogue": 50, "slime": 25}],
        "decorations": [
            {"type": "dec_5_1", "pos": (325, 115)},
            {"type": "dec_5_5", "pos": (930, 125)},
            {"type": "dec_5_3", "pos": (960, 335)},
            {"type": "dec_5_2", "pos": (500, 650)},
            
        ],
        "road_segments": [
            {"type": "road_5_6", "center_left": (200, 630)},
            {"type": "road_5_2", "center_left": (158, 520)},
            {"type": "road_5_3", "center_left": (40, 480)},
            {"type": "road_5_1", "center_left": (40, 364)},
            {"type": "road_5_5", "center_left": (158, 363)},
            {"type": "road_5_4", "center_left": (253, 322)},
            {"type": "road_5_6", "center_left": (295, 225)},
            {"type": "road_5_1", "center_left": (295, 140)},
            {"type": "road_5_2", "center_left": (413, 140)},
            {"type": "road_5_6", "center_left": (455, 258)},
            {"type": "road_5_3", "center_left": (455, 355)},
            {"type": "road_5_4", "center_left": (573, 353)},
            {"type": "road_5_8", "center_left": (610, 120)},
            {"type": "road_5_6", "center_left": (653, 20)},
            {"type": "road_5_6", "center_left": (653, -30)},
            
        ]
    }
}