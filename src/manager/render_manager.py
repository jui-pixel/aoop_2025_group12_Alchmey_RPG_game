import pygame
from typing import List
from src.core.config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, DARK_GRAY, PASSABLE_TILES, ROOM_FLOOR_COLORS, BLACK
from src.utils.helpers import get_project_path
import math
from src.ecs.systems import RenderSystem

class FontManager:
    _fonts = {}
    @staticmethod
    def get_font(name: str, size: int) -> pygame.font.Font:
        key = (name, size)
        if key not in FontManager._fonts:
            font_path = get_project_path("assets", "fonts", name)
            try:
                FontManager._fonts[key] = pygame.font.Font(font_path, size)
                print(f"成功載入字體: {font_path}")
            except Exception as e:
                print(f"無法載入 {name}: {e}，使用預設字體")
                FontManager._fonts[key] = pygame.font.SysFont(None, size)
        return FontManager._fonts[key]

class RenderManager:
    def __init__(self, game: 'Game'):
        """初始化渲染管理器，負責管理遊戲畫面的繪製，包括小地圖和視野迷霧。

        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
            screen: Pygame 的顯示表面，用於渲染畫面。
        """
        self.game = game
        self.screen = game.screen
        self.camera_offset = [0, 0]
        self.camera_lerp_factor = 1.5
        self.original_camera_lerp_factor = 1.5
        self.skill_rects = []
        self.minimap_scale = 1
        self.minimap_width = 0
        self.minimap_height = 0
        self.minimap_offset = (0, 0)
        self.fog_map = None
        self.fog_surface = None
        self.last_player_pos = None
        self.last_vision_radius = None

    def reset_minimap(self) -> None:
        self._initialize_minimap()
        
    def reset_fog(self) -> None:
        self._initialize_fog_map()
    
    def _initialize_minimap(self) -> None:
        """初始化小地圖的尺寸和偏移。"""
        dungeon = self.game.dungeon_manager.get_dungeon()
        self.minimap_width = int(dungeon.grid_width * self.minimap_scale)
        self.minimap_height = int(dungeon.grid_height * self.minimap_scale)
        self.minimap_offset = (SCREEN_WIDTH - self.minimap_width - 10, 10)
        print(f"RenderManager: 初始化小地圖，尺寸 ({self.minimap_width}, {self.minimap_height})，偏移 {self.minimap_offset}")

    def _initialize_fog_map(self) -> None:
        """初始化視野迷霧地圖。"""
        dungeon = self.game.dungeon_manager.get_dungeon()
        self.fog_map = [[False for _ in range(dungeon.grid_width)]
                       for _ in range(dungeon.grid_height)]
        self.fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        print("RenderManager: 初始化視野迷霧地圖")

    def _update_fog_map_from_player(self) -> None:
        """根據玩家位置更新視野迷霧。"""
        if not self.game.entity_manager.player:
            return
        if not self.fog_map:
            self._initialize_fog_map()
        player = self.game.entity_manager.player
        dungeon = self.game.dungeon_manager.get_dungeon()
        vision_radius = getattr(player, 'vision_radius', 5)
        player_tile_x = int(player.x // TILE_SIZE)
        player_tile_y = int(player.y // TILE_SIZE)

        if self.last_player_pos == (player_tile_x, player_tile_y) and self.last_vision_radius == vision_radius:
            return

        self.last_player_pos = (player_tile_x, player_tile_y)
        self.last_vision_radius = vision_radius

        for y in range(max(0, player_tile_y - vision_radius), min(dungeon.grid_height, player_tile_y + vision_radius + 1)):
            for x in range(max(0, player_tile_x - vision_radius), min(dungeon.grid_width, player_tile_x + vision_radius + 1)):
                if math.sqrt((x - player_tile_x) ** 2 + (y - player_tile_y) ** 2) <= vision_radius:
                    if 0 <= y < dungeon.grid_height and 0 <= x < dungeon.grid_width:
                        if dungeon.dungeon_tiles[y][x] not in PASSABLE_TILES:
                            self.fog_map[y][x] = True
                        elif self.has_line_of_sight(player_tile_x, player_tile_y, x, y, dungeon):
                            self.fog_map[y][x] = True
                            
        print(f"RenderManager: 更新迷霧，玩家位置 ({player_tile_x}, {player_tile_y})，視野半徑 {vision_radius}")

    def has_line_of_sight(self, x0, y0, x1, y1, dungeon):
        """檢查玩家(x0,y0)到(x1,y1)之間是否有阻擋"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        x, y = x0, y0
        while not (x == x1 and y == y1):
            if dungeon.dungeon_tiles[y][x] not in PASSABLE_TILES:
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        return True
    
    def _draw_minimap(self) -> None:
        """繪製小地圖，僅顯示地牢結構與玩家位置。"""
        dungeon = self.game.dungeon_manager.get_dungeon()
        minimap_surface = pygame.Surface((self.minimap_width, self.minimap_height))
        minimap_surface.fill((0, 0, 0))
        if not self.fog_map:
            self._initialize_fog_map()
        for y in range(dungeon.grid_height):
            for x in range(dungeon.grid_width):
                if self.fog_map[y][x]:
                    tile_type = dungeon.dungeon_tiles[y][x]
                    color = ROOM_FLOOR_COLORS[tile_type]
                    pygame.draw.rect(
                        minimap_surface, color,
                        (x * self.minimap_scale, y * self.minimap_scale, self.minimap_scale, self.minimap_scale)
                    )

        if self.game.entity_manager.player:
            player_x = int(self.game.entity_manager.player.x // TILE_SIZE * self.minimap_scale)
            player_y = int(self.game.entity_manager.player.y // TILE_SIZE * self.minimap_scale)
            pygame.draw.rect(minimap_surface, (255, 0, 0),
                            (player_x, player_y, self.minimap_scale, self.minimap_scale))

        self.screen.blit(minimap_surface, self.minimap_offset)

    def _draw_fog(self) -> None:
        """繪製視野迷霧。"""
        dungeon = self.game.dungeon_manager.get_dungeon()
        self.fog_surface.fill(BLACK)

        for y in range(dungeon.grid_height):
            for x in range(dungeon.grid_width):
                screen_x = x * TILE_SIZE - self.camera_offset[0]
                screen_y = y * TILE_SIZE - self.camera_offset[1]
                if self.fog_map[y][x]:
                    if (x, y) == self.last_player_pos or math.sqrt((x - self.last_player_pos[0]) ** 2 + (y - self.last_player_pos[1]) ** 2) <= self.last_vision_radius:
                        self.fog_surface.fill((0, 0, 0, 0), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    else:
                        self.fog_surface.fill((0, 0, 0, 128), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

        self.screen.blit(self.fog_surface, (0, 0))
        print("RenderManager: 繪製迷霧")

    def update_camera(self, dt: float) -> None:
        """更新攝影機位置，使其跟隨玩家。"""
        if self.game.entity_manager.player:
            target_x = self.game.entity_manager.player.x - SCREEN_WIDTH // 2
            target_y = self.game.entity_manager.player.y - SCREEN_HEIGHT // 2
            self.camera_offset[0] += (target_x - self.camera_offset[0]) * self.camera_lerp_factor * dt
            self.camera_offset[1] += (target_y - self.camera_offset[1]) * self.camera_lerp_factor * dt
            print(f"RenderManager: 攝影機偏移量：{self.camera_offset}")
        self._update_fog_map_from_player()

    def draw_game_world(self) -> None:
        """繪製遊戲世界，包括地牢、實體、小地圖和迷霧。
        
        **職責：協調繪圖層次，並在此處執行 ECS 實體繪製系統。**
        """
        self.screen.fill((0, 0, 0))
        dungeon = self.game.dungeon_manager.get_dungeon()
        
        # 1. 繪製地牢背景
        dungeon.draw_background(self.screen, self.camera_offset)
        
        # 2. 繪製 ECS 實體 (執行 RenderSystem)
        # ⚠️ 重大修改：用 ECS 處理器執行替代舊的 entity_manager.draw()
        try:
            # 假設 self.game.world 存在並儲存 esper.World 實例
            # 這裡執行 RenderSystem，它會迭代 Position 和 Renderable 組件並繪製
            self.game.world.get_processor(RenderSystem).process() 
        except Exception:
            # 如果沒有找到 RenderSystem 處理器，則可能需要使用 esper.dispatch() 或其他方法。
            # 為了避免導入循環或運行時錯誤，這裡可以簡單地跳過或使用主循環的 esper.dispatch()。
            # 但在 RenderManager中手動運行系統是正確的。
            pass
            
        # 3. 繪製迷霧
        if self.game.entity_manager.player and self.game.entity_manager.player.fog:
            self._draw_fog()
            
        # 4. 繪製地牢前景 (例如牆壁頂部、柱子等)
        dungeon.draw_foreground(self.screen, self.camera_offset)
        
        # 5. 繪製小地圖 (UI 元素)
        self._draw_minimap()

    def draw_menu(self) -> None:
        """繪製當前菜單。"""
        self.draw_game_world()
        self.game.menu_manager.draw()
        # 顯示所有激活的菜單名稱
        if self.game.menu_manager.active_menus:
            menu_names = [menu.__class__.__name__ for menu in self.game.menu_manager.active_menus]
            print(f"RenderManager: 繪製菜單 {', '.join(menu_names)}")
        else:
            print("RenderManager: 無激活菜單")

    def draw_skill_selection(self) -> None:
        """繪製技能選擇畫面。"""
        self.screen.fill((0, 0, 0))
        font = FontManager.get_font("Silver.ttf", 36)
        for i, skill in enumerate(self.game.storage_manager.skills):
            is_selected = skill in self.game.event_manager.selected_skills
            hovered = False
            rect = pygame.Rect(50, 50 + i * 50, 300, 40)
            self.skill_rects.append(rect)
            if is_selected:
                pygame.draw.rect(self.screen, (0, 255, 0), rect, 2)
            elif hovered:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)
        chain_text = font.render(f"技能鏈 {self.game.event_manager.selected_skill_chain_idx + 1}/{self.game.entity_manager.player.max_skill_chains}", True, (255, 255, 255))
        self.screen.blit(chain_text, (SCREEN_WIDTH // 2 - chain_text.get_width() // 2, 450))
        count_text = font.render(f"已選擇：{len(self.game.event_manager.selected_skills)}/{4}", True, (255, 255, 255))
        self.screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 400))
        pygame.display.flip()

    def draw_lobby(self) -> None:
        """繪製大廳狀態。"""
        self.draw_game_world()
        self._draw_ui()
        if self.game.menu_manager.active_menus:
            self.game.menu_manager.draw()
        pygame.display.flip()

    def draw_playing(self) -> None:
        """繪製遊戲進行狀態。"""
        self.draw_game_world()
        self._draw_ui()
        if self.game.menu_manager.active_menus:
            self.game.menu_manager.draw()
        pygame.display.flip()

    def draw_win(self) -> None:
        """繪製勝利畫面。"""
        self.screen.fill((0, 0, 0))
        font = FontManager.get_font("Silver.ttf", 48)
        win_text = font.render("勝利！您已清除所有地牢！", True, (255, 255, 0))
        self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - win_text.get_height() // 2))
        pygame.display.flip()

    def _draw_ui(self) -> None:
        """繪製地牢主題的 UI 元素：HP、護盾、能量、技能鏈和法力值"""
        if not self.game.entity_manager.player:
            return
        player = self.game.entity_manager.player
        font = FontManager.get_font("Silver.ttf", 20)
        font_small = FontManager.get_font("Silver.ttf", 16)

        # UI 主題配色（地牢風格：深色、石質感）
        bg_dark = (25, 20, 15)  # 深棕黑色背景
        frame_outer = (80, 70, 60)  # 外框石頭色
        frame_inner = (50, 45, 40)  # 內框陰影色
        frame_highlight = (120, 110, 95)  # 高光色
        
        # 條狀框架設定
        bar_width = 180
        bar_height = 24
        bar_spacing = 8
        x_offset = 15
        y_offset = 15
        
        # 繪製主 UI 面板背景（左上角）
        panel_width = bar_width + 180
        panel_height = (bar_height + bar_spacing) * 4 + 20
        self._draw_stone_panel(x_offset - 8, y_offset - 8, panel_width, panel_height)

        # HP 條（紅色，帶血液感）
        hp_ratio = player.current_hp / max(player.max_hp, 1)
        self._draw_dungeon_bar(
            x_offset, y_offset, bar_width, bar_height,
            hp_ratio, 
            bar_color=(180, 30, 30),  # 深紅色
            bar_glow=(255, 60, 60),   # 高光紅
            label="生命",
            value_text=f"{player.current_hp}/{player.max_hp}",
            font=font, font_small=font_small
        )

        # 護盾條（藍色，帶魔法感）
        y_offset += bar_height + bar_spacing
        shield_ratio = player.current_shield / max(player.max_shield, 1)
        self._draw_dungeon_bar(
            x_offset, y_offset, bar_width, bar_height,
            shield_ratio,
            bar_color=(30, 80, 150),  # 深藍
            bar_glow=(60, 140, 255),  # 亮藍
            label="護盾",
            value_text=f"{player.current_shield}/{player.max_shield}",
            font=font, font_small=font_small
        )

        # 能量條（綠色，帶自然感）
        y_offset += bar_height + bar_spacing
        energy_ratio = player.energy / max(player.max_energy, 1)
        self._draw_dungeon_bar(
            x_offset, y_offset, bar_width, bar_height,
            energy_ratio,
            bar_color=(40, 120, 40),  # 深綠
            bar_glow=(80, 200, 80),   # 亮綠
            label="能量",
            value_text=f"{int(player.energy)}/{int(player.max_energy)}",
            font=font, font_small=font_small
        )

        # 技能鏈顯示（文字加裝飾）
        y_offset += bar_height + bar_spacing
        chain_idx = player.current_skill_chain_idx + 1
        chain_label = font_small.render("連擊鏈:", True, (200, 180, 150))
        chain_value = font.render(f"#{chain_idx}", True, (255, 220, 120))
        self.screen.blit(chain_label, (x_offset, y_offset + 2))
        self.screen.blit(chain_value, (x_offset + 80, y_offset))

        # 法力值顯示（右上角，帶金幣風格）
        mana_panel_width = 160
        mana_panel_height = 50
        mana_x = SCREEN_WIDTH - mana_panel_width - 15
        mana_y = 15
        self._draw_stone_panel(mana_x, mana_y, mana_panel_width, mana_panel_height)
        
        mana_label = font_small.render("法力", True, (200, 180, 150))
        mana_value = font.render(f"{self.game.storage_manager.mana}", True, (255, 215, 0))  # 金色
        self.screen.blit(mana_label, (mana_x + 15, mana_y + 8))
        self.screen.blit(mana_value, (mana_x + 15, mana_y + 26))

    def _draw_stone_panel(self, x: int, y: int, width: int, height: int) -> None:
        """繪製石質面板背景"""
        # 主背景
        pygame.draw.rect(self.screen, (25, 20, 15), (x, y, width, height))
        
        # 外框（淺色高光）
        pygame.draw.rect(self.screen, (90, 80, 70), (x, y, width, height), 2)
        
        # 內陰影（深色）
        pygame.draw.rect(self.screen, (15, 12, 10), (x + 2, y + 2, width - 4, height - 4), 1)
        
        # 角落裝飾
        corner_size = 6
        corner_color = (60, 55, 50)
        # 左上
        pygame.draw.rect(self.screen, corner_color, (x, y, corner_size, corner_size))
        # 右上
        pygame.draw.rect(self.screen, corner_color, (x + width - corner_size, y, corner_size, corner_size))
        # 左下
        pygame.draw.rect(self.screen, corner_color, (x, y + height - corner_size, corner_size, corner_size))
        # 右下
        pygame.draw.rect(self.screen, corner_color, (x + width - corner_size, y + height - corner_size, corner_size, corner_size))

    def _draw_dungeon_bar(self, x: int, y: int, width: int, height: int, 
                          ratio: float, bar_color: tuple, bar_glow: tuple,
                          label: str, value_text: str, font, font_small) -> None:
        """繪製地牢風格的進度條"""
        # 外框（深色凹陷）
        pygame.draw.rect(self.screen, (15, 12, 10), (x - 2, y - 2, width + 4, height + 4))
        
        # 背景（深灰）
        pygame.draw.rect(self.screen, (40, 35, 30), (x, y, width, height))
        
        # 進度條本體
        fill_width = int(width * ratio)
        if fill_width > 0:
            # 底色（深色）
            pygame.draw.rect(self.screen, bar_color, (x, y, fill_width, height))
            
            # 漸層高光（上半部分）
            glow_height = height // 3
            glow_surface = pygame.Surface((fill_width, glow_height), pygame.SRCALPHA)
            for i in range(glow_height):
                alpha = int(100 * (1 - i / glow_height))
                color = (*bar_glow, alpha)
                pygame.draw.line(glow_surface, color, (0, i), (fill_width, i))
            self.screen.blit(glow_surface, (x, y))
            
            # 底部陰影
            shadow_height = height // 4
            shadow_surface = pygame.Surface((fill_width, shadow_height), pygame.SRCALPHA)
            for i in range(shadow_height):
                alpha = int(60 * (i / shadow_height))
                pygame.draw.line(shadow_surface, (0, 0, 0, alpha), (0, i), (fill_width, i))
            self.screen.blit(shadow_surface, (x, y + height - shadow_height))
        
        # 內框高光
        pygame.draw.rect(self.screen, (80, 70, 60), (x, y, width, height), 1)
        
        # 標籤文字（左側）
        label_surf = font_small.render(label, True, (200, 180, 150))
        self.screen.blit(label_surf, (x + 6, y + (height - label_surf.get_height()) // 2))
        
        # 數值文字（右側）
        value_surf = font_small.render(value_text, True, (255, 255, 255))
        self.screen.blit(value_surf, (x + width - value_surf.get_width() - 6, y + (height - value_surf.get_height()) // 2))