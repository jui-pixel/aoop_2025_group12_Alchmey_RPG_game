# src/config.py
from enum import Enum

class DungeonConfig(Enum):
    ROOM_WIDTH = 150  # 單個房間的最大寬度（瓦片數，控制房間的最大尺寸）
    ROOM_HEIGHT = 150 # 單個房間的最大高度（瓦片數，控制房間的最大尺寸）
    GRID_WIDTH = 150  # 地牢網格的寬度（瓦片數，定義地牢的總寬度）
    GRID_HEIGHT = 150  # 地牢網格的高度（瓦片數，定義地牢的總高度）
    MIN_ROOM_SIZE = 15  # 房間的最小尺寸（寬度和高度，確保房間不會太小）
    TILE_SIZE = 32  # 每個瓦片的像素大小
    ROOM_GAP = 2  # 房間之間的最小間距（瓦片數，防止房間互相重疊）
    BIAS_RATIO = 0.6  # 房間大小偏向比例（控制房間大小的隨機性）
    BIAS_STRENGTH = 0.3  # 偏向強度（控制房間位置的隨機偏移）
    MIN_BRIDGE_WIDTH = 2  # 走廊（橋接）的最小寬度（瓦片數，確保走廊不會太窄）
    MAX_BRIDGE_WIDTH = 4  # 走廊（橋接）的最大寬度（瓦片數，控制走廊的最大寬度）
    MAX_SPLIT_DEPTH = 15  # BSP 分割的最大深度（控制生成房間的數量，深度越大房間越多）
    EXTRA_BRIDGE_RATIO = 0.2  # 額外走廊的比例（增加連通性，生成更多非必要走廊）
    MOMSTER_ROOM_RATIO = 0.3  # 怪物房間的比例（控制怪物房間的數量，增加遊戲挑戰性）
    TRAP_ROOM_RATIO = 0.2  # 陷阱房間的比例（控制陷阱房間的數量，增加遊戲危險性）
    REWARD_ROOM_RATIO = 0.2  # 獎勵房間的比例（控制獎勵房間的數量，增加遊戲獎勵）
FPS = 60
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 750
TILE_SIZE = 32
MAX_WEAPONS_DEFAULT = 4

# 顏色定義
# ====== 基本顏色 ======
BLACK       = (0, 0, 0)             # ⬛ 黑色
WHITE       = (255, 255, 255)       # ⬜ 白色
GRAY        = (128, 128, 128)       # ◼ 灰色
LIGHT_GRAY  = (200, 200, 200)       # ◽ 淺灰
DARK_GRAY   = (50, 50, 50)          # ◾ 深灰

# ====== 紅色系 ======
RED         = (255, 0, 0)           # 🟥 紅
DARK_RED    = (139, 0, 0)           # 🟥 暗紅
PINK        = (255, 182, 193)       # 🌸 粉紅
LIGHT_PINK  = (255, 192, 203)       # 🎀 淡粉紅

# ====== 橙黃色系 ======
ORANGE      = (255, 165, 0)         # 🟧 橙
GOLD        = (255, 215, 0)         # 🟨 金黃色
YELLOW      = (255, 255, 0)         # 🟨 黃色
LIGHT_YELLOW= (255, 255, 224)       # 🌕 淡黃

# ====== 綠色系 ======
GREEN       = (0, 255, 0)           # 🟩 綠色
DARK_GREEN  = (0, 100, 0)           # 🌲 暗綠
LIME        = (50, 205, 50)         # 💚 青綠
OLIVE       = (128, 128, 0)         # 🫒 橄欖綠

# ====== 藍色系 ======
BLUE        = (0, 0, 255)           # 🟦 藍色
NAVY        = (0, 0, 128)           # ⚓ 海軍藍
SKY_BLUE    = (135, 206, 235)       # 🌤 天藍
LIGHT_BLUE  = (173, 216, 230)       # 🧊 淺藍

# ====== 紫色系 ======
PURPLE      = (128, 0, 128)         # 🟪 紫色
VIOLET      = (238, 130, 238)       # 💜 紫羅蘭
INDIGO      = (75, 0, 130)          # 🟪 靛色

# ====== 棕色系 ======
BROWN       = (139, 69, 19)         # 🟫 棕色
TAN         = (210, 180, 140)       # 🏜 沙棕
BEIGE       = (245, 245, 220)       # 🏠 米色

# ====== 透明色（適用於支援 alpha 的情境） ======
TRANSPARENT = (0, 0, 0, 0)          # 透明（RGBA）

# ====== 遊戲特定顏色 ======
ROOM_FLOOR_COLOR = GRAY  # 房間地板
BORDER_WALL_COLOR = RED     # 邊界牆
BRIDGE_FLOOR_COLOR = LIGHT_GRAY  # 橋樑地板
END_ROOM_FLOOR_COLAR = BLUE     # 最終房間地板
END_ROOM_PROTAL_COLOR = PURPLE    # 最終房間傳送門
OUTSIDE_COLOR = BLACK           # 外部區域
