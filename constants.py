import pygame

DIFFICULTIES = {
    "Beginner": {"cols": 9, "rows": 9, "mines": 10},
    "Intermediate": {"cols": 16, "rows": 16, "mines": 40},
    "Expert": {"cols": 30, "rows": 16, "mines": 99},
    "Custom": {"cols": 20, "rows": 20, "mines": 60}
}

DEFAULT_DIFFICULTY = "Intermediate"

MIN_CUSTOM_COLS = 5
MAX_CUSTOM_COLS = 50
MIN_CUSTOM_ROWS = 5
MAX_CUSTOM_ROWS = 30

CELL_SIZE = 30
TOP_BAR_HEIGHT = 80
MIN_WIDTH = 550
TEXT_COLOR = (0, 0, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

THEMES = {
    "Grey": {
        "bg": (192, 192, 192),
        "grid": (128, 128, 128),
        "hidden": (192, 192, 192),
        "revealed": (220, 220, 220),
        "hover": (205, 205, 205),
        "highlight": (255, 255, 255),
        "shadow": (128, 128, 128),
    },
    "Red": {
        "bg": (200, 150, 150),
        "grid": (150, 80, 80),
        "hidden": (220, 170, 170),
        "revealed": (240, 200, 200),
        "hover": (230, 185, 185),
        "highlight": (255, 220, 220),
        "shadow": (170, 100, 100),
    },
    "Blue": {
        "bg": (150, 170, 210),
        "grid": (80, 100, 150),
        "hidden": (170, 190, 230),
        "revealed": (200, 220, 245),
        "hover": (185, 205, 240),
        "highlight": (220, 240, 255),
        "shadow": (100, 130, 180),
    },
    "Green": {
        "bg": (150, 190, 150),
        "grid": (80, 130, 80),
        "hidden": (170, 210, 170),
        "revealed": (200, 230, 200),
        "hover": (185, 220, 185),
        "highlight": (220, 245, 220),
        "shadow": (100, 150, 100),
    },
    "Pink": {
        "bg": (210, 160, 210),
        "grid": (160, 90, 160),
        "hidden": (230, 180, 230),
        "revealed": (245, 210, 245),
        "hover": (240, 195, 240),
        "highlight": (255, 230, 255),
        "shadow": (180, 120, 180),
    },
    "Yellow": {
        "bg": (210, 210, 150),
        "grid": (160, 160, 80),
        "hidden": (230, 230, 170),
        "revealed": (245, 245, 200),
        "hover": (240, 240, 185),
        "highlight": (255, 255, 220),
        "shadow": (180, 180, 100),
    },
    "Orange": {
        "bg": (210, 180, 140),
        "grid": (170, 120, 60),
        "hidden": (230, 200, 160),
        "revealed": (250, 220, 190),
        "hover": (240, 210, 175),
        "highlight": (255, 240, 220),
        "shadow": (190, 140, 80),
    },
    "Purple": {
        "bg": (180, 160, 210),
        "grid": (120, 90, 160),
        "hidden": (200, 180, 230),
        "revealed": (220, 210, 245),
        "hover": (210, 195, 240),
        "highlight": (240, 230, 255),
        "shadow": (140, 120, 180),
    }
}

NUM_COLORS = {
    1: (0, 0, 255),
    2: (0, 128, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    7: (0, 0, 0),
    8: (128, 128, 128)
}

FPS = 60
