import pygame
from typing import List
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SKILLS_DEFAULT, MAX_WEAPONS_DEFAULT, TILE_SIZE, DARK_GRAY, PASSABLE_TILES, ROOM_FLOOR_COLORS, BLACK
from src.utils.helpers import get_project_path
import math
from src.ecs.systems import RenderSystem

class FontManager:
    _fonts = {}
    @staticmethod
    def get_font(name: str, size: int) -> pygame.font.Font:
        key = (name, size)
        if key not in FontManager._fonts:
            font_path = get_project_path("src", "assets", "fonts", name)
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
        # assert self.game.menu_manager.current_menu is not None
        self.draw_game_world()
        self.game.menu_manager.draw()
        print(f"RenderManager: 繪製菜單 {self.game.menu_manager.current_menu.__class__.__name__ if self.game.menu_manager.current_menu else 'None'}")

    def draw_skill_selection(self) -> None:
        """繪製技能選擇畫面。"""
        self.screen.fill((0, 0, 0))
        font = FontManager.get_font("Silver.ttf", 36)
        max_skills = self.game.entity_manager.player.max_skills if self.game.entity_manager.player else MAX_SKILLS_DEFAULT
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
        count_text = font.render(f"已選擇：{len(self.game.event_manager.selected_skills)}/{max_skills}", True, (255, 255, 255))
        self.screen.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 400))
        pygame.display.flip()

    def draw_lobby(self) -> None:
        """繪製大廳狀態。"""
        self.draw_game_world()
        self._draw_ui()
        if self.game.menu_manager.current_menu:
            self.game.menu_manager.draw()
        pygame.display.flip()

    def draw_playing(self) -> None:
        """繪製遊戲進行狀態。"""
        self.draw_game_world()
        self._draw_ui()
        if self.game.menu_manager.current_menu:
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
        """Draw the UI elements: HP, Shield, Energy as progress bars; Mana and Current Skill Chain as text."""
        if not self.game.entity_manager.player:
            return
        player = self.game.entity_manager.player
        font = FontManager.get_font("Silver.ttf", 24)

        # Progress bar settings
        bar_width = 150
        bar_height = 20
        bar_spacing = 10
        x_offset = 10
        y_offset = 10

        # HP Bar (Red)
        hp_ratio = player.current_hp / max(player.max_hp, 1)
        pygame.draw.rect(self.screen, DARK_GRAY, (x_offset, y_offset, bar_width, bar_height))  # Background
        pygame.draw.rect(self.screen, (255, 0, 0), (x_offset, y_offset, bar_width * hp_ratio, bar_height))  # Fill
        hp_text = font.render(f"HP: {player.current_hp}/{player.max_hp}", True, (255, 255, 255))
        self.screen.blit(hp_text, (x_offset + bar_width + 10, y_offset))

        # Shield Bar (Blue)
        y_offset += bar_height + bar_spacing
        shield_ratio = player.current_shield / max(player.max_shield, 1)
        pygame.draw.rect(self.screen, DARK_GRAY, (x_offset, y_offset, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 0, 255), (x_offset, y_offset, bar_width * shield_ratio, bar_height))
        shield_text = font.render(f"Shield: {player.current_shield}/{player.max_shield}", True, (255, 255, 255))
        self.screen.blit(shield_text, (x_offset + bar_width + 10, y_offset))

        # Energy Bar (Green)
        y_offset += bar_height + bar_spacing
        energy_ratio = player.energy / max(player.max_energy, 1)
        pygame.draw.rect(self.screen, DARK_GRAY, (x_offset, y_offset, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 255, 0), (x_offset, y_offset, bar_width * energy_ratio, bar_height))
        energy_text = font.render(f"Energy: {int(player.energy)}/{int(player.max_energy)}", True, (255, 255, 255))
        self.screen.blit(energy_text, (x_offset + bar_width + 10, y_offset))

        # Current Skill Chain (Text only)
        y_offset += bar_height + bar_spacing
        chain_idx = player.current_skill_chain_idx + 1
        chain_text = font.render(f"Current Chain: {chain_idx}", True, (255, 255, 255))
        self.screen.blit(chain_text, (x_offset, y_offset))

        # Mana (Right top, Text only)
        mana_text = font.render(f"Mana: {self.game.storage_manager.mana}", True, (255, 255, 255))
        self.screen.blit(mana_text, (SCREEN_WIDTH - mana_text.get_width() - 10, 10))