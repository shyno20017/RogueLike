# Constant Variables
CELL_WIDTH = 32
CELL_HEIGHT = 32

CELL_SIZE = (CELL_WIDTH, CELL_HEIGHT)

GAME_FPS = 60

# Map Constants
MAP_WIDTH = 20
MAP_HEIGHT = 20

# Game size
GAME_WIDTH = MAP_WIDTH * CELL_WIDTH
GAME_HEIGHT = MAP_HEIGHT * CELL_HEIGHT
WINDOW_SIZE = (GAME_WIDTH, GAME_HEIGHT)

# Color definitions
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (100, 100, 100)
COLOR_RED = (255, 0, 0)
COLOR_L_RED = (255, 100, 100)
COLOR_GREEN = (0, 255, 0)
COLOR_L_GREEN = (100, 255, 100)
COLOR_D_GREEN = (0, 200, 0)

# Game Colors
COLOR_DEFAULT_BG = COLOR_GREY

# Sprites
# Sprites from DawnLike tileset
# (https://imgur.com/a/TECi6)
# (https://opengameart.org/content/dawnlike-16x16-universal-rogue-like-tileset-v181)
# Thanks to DawnBringer for the graphics

# FOV Settings
FOV_ALGO = 0 # libtcod.FOV_BASIC
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# Message Settings
NUM_MESSAGES = 4
PIXELS_UNDER_MESSAGES = 2

# Cursor Settings
USE_CURSOR = False
CURSOR_SIZE = (26, 26)
