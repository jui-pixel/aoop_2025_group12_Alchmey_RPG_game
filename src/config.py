# src/config.py
from enum import Enum

ROOM_WIDTH = 20  # 單個房間的最大寬度（瓦片數，控制房間的最大尺寸）
ROOM_HEIGHT = 20 # 單個房間的最大高度（瓦片數，控制房間的最大尺寸）
GRID_WIDTH = 120  # 地牢網格的寬度（瓦片數，定義地牢的總寬度）
GRID_HEIGHT = 100  # 地牢網格的高度（瓦片數，定義地牢的總高度）
MIN_ROOM_SIZE = 15  # 房間的最小尺寸（寬度和高度，確保房間不會太小）
TILE_SIZE = 40  # 每個瓦片的像素大小
ROOM_GAP = 2  # 房間之間的最小間距（瓦片數，防止房間互相重疊）
BIAS_RATIO = 0.8  # 房間大小偏向比例（控制房間大小的隨機性）
BIAS_STRENGTH = 0.3  # 偏向強度（控制房間位置的隨機偏移）
MIN_BRIDGE_WIDTH = 2  # 走廊（橋接）的最小寬度（瓦片數，確保走廊不會太窄）
MAX_BRIDGE_WIDTH = 4  # 走廊（橋接）的最大寬度（瓦片數，控制走廊的最大寬度）
MAX_SPLIT_DEPTH = 6  # BSP 分割的最大深度（控制生成房間的數量，深度越大房間越多）
EXTRA_BRIDGE_RATIO = 0.0  # 額外走廊的比例（增加連通性，生成更多非必要走廊）
MOMSTER_ROOM_RATIO = 0.8  # 怪物房間的比例（控制怪物房間的數量，增加遊戲挑戰性）
TRAP_ROOM_RATIO = 0.1  # 陷阱房間的比例（控制陷阱房間的數量，增加遊戲危險性）
REWARD_ROOM_RATIO = 0.1  # 獎勵房間的比例（控制獎勵房間的數量，增加遊戲獎勵）
LOBBY_WIDTH = 60 # 大廳的寬度（瓦片數，確保大廳有足夠空間）
LOBBY_HEIGHT = 40 # 大廳的高度（瓦片數，確保大廳有足夠空間）

FPS = 60
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 750
MAX_WEAPONS_DEFAULT = 2
MAX_SKILLS_DEFAULT = 4
MAX_WEAPON_CHAINS_DEFAULT = 9
MAX_WEAPON_CHAIN_LENGTH_DEFAULT = 5
#
# 顏色定義
# ====== 基本顏色 ======
BLACK       = (0, 0, 0)             # ⬛ 黑色 - 用於背景或外部區域
WHITE       = (255, 255, 255)       # ⬜ 白色 - 用於文字或高亮
GRAY        = (100, 100, 100)       # ◼ 灰色 - 中性地板或裝飾
LIGHT_GRAY  = (180, 180, 180)       # ◽ 淺灰 - 走廊或次要結構
DARK_GRAY   = (40, 40, 40)          # ◾ 深灰 - 牆面或陰影
IRON_GRAY   = (98, 97, 81)          # 鐵灰 - 門

# ====== 紅色系 ======
RED       = (255, 0, 0)             # 🟥 紅色 - 怪物或危險區域
DARK_RED    = (120, 20, 20)         # 🟥 暗紅 - 危險區域或陷阱
CRIMSON     = (150, 50, 50)         # 🟥 深紅 - 怪物生成點
PALE_RED    = (200, 100, 100)       # 🌸 淡紅 - 柔和的高亮

# ====== 橙黃色系 ======
DARK_GOLD   = (180, 140, 60)        # 🟨 暗金 - 獎勵房間
GOLD        = (220, 180, 100)       # 🟨 金黃 - 獎勵生成點
AMBER       = (200, 150, 50)        # 🟧 琥珀 - 溫暖高亮

# ====== 綠色系 ======
DARK_GREEN  = (50, 80, 50)          # 🌲 暗綠 - 起始房間或自然區域
FOREST_GREEN= (70, 100, 70)         # 🌳 森林綠 - 怪物房間
LIME_GLOW   = (120, 200, 120)       # 💚 青綠 - 出生點高亮

# ====== 藍色系 ======
DARK_BLUE   = (50, 50, 100)         # 🟦 暗藍 - 終點房間
MYSTIC_BLUE = (80, 80, 150)         # 🌌 神秘藍 - 傳送門
SKY_BLUE    = (100, 150, 200)       # 🌤 天藍 - 大廳房間

# ====== 紫色系 ======
DEEP_PURPLE = (100, 50, 100)        # 🟪 深紫 - 特殊效果
VIOLET_GLOW = (150, 100, 150)       # 💜 紫羅蘭 - 魔法或傳送門

# ====== 棕色系 ======
STONE_BROWN = (90, 70, 50)          # 🟫 石棕 - 牆面或地面
SANDSTONE   = (140, 110, 80)        # 🏜 砂岩 - 陷阱房間

# ====== 透明色 ======
TRANSPARENT = (0, 0, 0, 0)          # 透明（RGBA） - 用於迷霧或效果

# ====== 遊戲特定顏色 ======
BORDER_WALL_TOP_COLOR = DARK_GRAY    # 邊界牆頂部 - 深灰，石牆質感
BORDER_WALL_SIDE_COLOR = STONE_BROWN # 邊界牆側面 - 石棕，增加立體感
OUTSIDE_COLOR = BLACK                # 地圖外部 - 黑色

ROOM_FLOOR_COLORS = {
    'Room_floor': GRAY,              # 普通房間地板 - 中性灰色
    'Bridge_floor': LIGHT_GRAY,      # 走廊地板 - 淺灰，連接區域
    'End_room_floor': DARK_BLUE,     # 終點房間地板 - 暗藍，神秘感
    'End_room_portal': VIOLET_GLOW,  # 終點房間傳送門 - 紫羅蘭，魔法效果
    'Start_room_floor': DARK_GREEN,  # 起始房間地板 - 暗綠，自然感
    'Lobby_room_floor': SKY_BLUE,    # 大廳房間地板 - 天藍，開闊感
    'Monster_room_floor': FOREST_GREEN,  # 怪物房間地板 - 森林綠，危險氛圍
    'Trap_room_floor': SANDSTONE,    # 陷阱房間地板 - 砂岩，荒涼感
    'Reward_room_floor': DARK_GOLD,  # 獎勵房間地板 - 暗金，財寶感
    'Player_spawn': LIME_GLOW,       # 玩家出生點 - 青綠，高亮
    'NPC_spawn': PALE_RED,           # NPC出生點 - 淡紅，
    'Monster_spawn': CRIMSON,        # 怪物出生點 - 深紅，警示
    'Trap_spawn': AMBER,             # 陷阱出生點 - 琥
    'Reward_spawn': GOLD,            # 獎勵出生點 - 金黃，吸引目光
    'Outside': OUTSIDE_COLOR,  # 地圖外部 - 黑色
    'Door': IRON_GRAY,  # 門 - 使用與橋相近的顏色
    'NPC_room_floor': PALE_RED,  # NPC房間地板 - 淡紅，柔和感
}

PASSABLE_TILES = {
    'Room_floor',
    'Bridge_floor',
    'End_room_floor',
    'Lobby_room_floor',
    'Monster_room_floor',
    'Trap_room_floor',
    'Reward_room_floor',
    'Start_room_floor',
    'End_room_portal',
    'Player_spawn',
    'NPC_spawn',
    'Monster_spawn',
    'Trap_spawn',
    'Reward_spawn',
    'Door',
    'NPC_room_floor',
}