import pygame
from typing import List
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_SKILLS_DEFAULT, MAX_WEAPONS_DEFAULT, TILE_SIZE, DARK_GRAY, PASSABLE_TILES, ROOM_FLOOR_COLORS
import math
class RenderManager:
    def __init__(self, game: 'Game', screen: pygame.Surface):
        """初始化渲染管理器，負責管理遊戲畫面的繪製，包括小地圖和視野迷霧。

        Args:
            game: 遊戲主類的實例，用於與其他模組交互。
            screen: Pygame 的顯示表面，用於渲染畫面。
        """
        self.game = game  # 保存遊戲實例引用
        self.screen = screen  # 保存 Pygame 顯示表面
        self.camera_offset = [0, 0]  # 攝影機偏移量，初始為 (0, 0)
        self.camera_lerp_factor = 1.5  # 攝影機平滑移動的插值因子
        self.original_camera_lerp_factor = 1.5  # 保存原始插值因子
        self.skill_rects = []  # 儲存技能選擇框的矩形列表
        # 小地圖相關變數
        self.minimap_scale = 1  # 小地圖縮放比例
        self.minimap_width = 0  # 小地圖寬度（像素）
        self.minimap_height = 0  # 小地圖高度（像素）
        self.minimap_offset = (0, 0)  # 小地圖在螢幕上的偏移位置
        # 視野迷霧相關變數
        self.fog_map = None  # 迷霧地圖，記錄可見區域
        self.fog_surface = None  # 迷霧表面，用於渲染
        self.last_player_pos = None  # 上次玩家位置，用於優化迷霧更新
        self.last_vision_radius = None  # 上次視野半徑，用於優化迷霧更新

    def reset_minimap(self) -> None:
        self._initialize_minimap()
        
    def reset_fog(self) -> None:
        self._initialize_fog_map()
    
    def _initialize_minimap(self) -> None:
        """初始化小地圖的尺寸和偏移。

        根據地牢的網格尺寸計算小地圖的寬度和高度，並設置右上角偏移。
        """
        dungeon = self.game.dungeon_manager.get_dungeon()
        self.minimap_width = int(dungeon.grid_width * self.minimap_scale)
        self.minimap_height = int(dungeon.grid_height * self.minimap_scale)
        self.minimap_offset = (SCREEN_WIDTH - self.minimap_width - 10, 10)
        print(f"RenderManager: 初始化小地圖，尺寸 ({self.minimap_width}, {self.minimap_height})，偏移 {self.minimap_offset}")

    def _initialize_fog_map(self) -> None:
        """初始化視野迷霧地圖。

        創建一個二維布林陣列，表示地牢網格的可見性，初始全為不可見（False）。
        """
        dungeon = self.game.dungeon_manager.get_dungeon()
        self.fog_map = [[False for _ in range(dungeon.grid_width)]
                       for _ in range(dungeon.grid_height)]
        self.fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        print("RenderManager: 初始化視野迷霧地圖")

    def _update_fog_map_from_player(self) -> None:
        """根據玩家位置更新視野迷霧。

        檢查玩家當前位置和視野半徑，更新迷霧地圖的可見區域。
        """
        if not self.game.entity_manager.player:
            return
        if not self.fog_map:
            self._initialize_fog_map()
        player = self.game.entity_manager.player
        dungeon = self.game.dungeon_manager.get_dungeon()
        vision_radius = getattr(player, 'vision_radius', 5)  # 假設玩家有 vision_radius 屬性，預設為 5 格
        player_tile_x = int(player.x // TILE_SIZE)
        player_tile_y = int(player.y // TILE_SIZE)

        # 優化：僅在玩家位置或視野半徑改變時更新
        if self.last_player_pos == (player_tile_x, player_tile_y) and self.last_vision_radius == vision_radius:
            return

        self.last_player_pos = (player_tile_x, player_tile_y)
        self.last_vision_radius = vision_radius

        # 更新可見區域
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
        minimap_surface.fill((0, 0, 0))  # 黑色背景

        # 繪製地牢結構
        for y in range(dungeon.grid_height):
            for x in range(dungeon.grid_width):
                if self.fog_map[y][x]:  # 只顯示已探索的區域
                    tile_type = dungeon.dungeon_tiles[y][x]
                    color = ROOM_FLOOR_COLORS[tile_type]
                    pygame.draw.rect(
                        minimap_surface, color,
                        (x * self.minimap_scale, y * self.minimap_scale, self.minimap_scale, self.minimap_scale)
                    )

        # 繪製玩家位置
        if self.game.entity_manager.player:
            player_x = int(self.game.entity_manager.player.x // TILE_SIZE * self.minimap_scale)
            player_y = int(self.game.entity_manager.player.y // TILE_SIZE * self.minimap_scale)
            pygame.draw.rect(minimap_surface, (255, 0, 0),
                            (player_x, player_y, self.minimap_scale, self.minimap_scale))

        # 貼到主螢幕
        self.screen.blit(minimap_surface, self.minimap_offset)


    def _draw_fog(self) -> None:
        """繪製視野迷霧。

        未探索區域為全黑色，探索過但不在視野內為半透明黑色，視野內為完全透明。
        """
        dungeon = self.game.dungeon_manager.get_dungeon()
        self.fog_surface.fill(DARK_GRAY)  # 深灰色，不透明（未探索）

        for y in range(dungeon.grid_height):
            for x in range(dungeon.grid_width):
                screen_x = x * TILE_SIZE - self.camera_offset[0]
                screen_y = y * TILE_SIZE - self.camera_offset[1]
                if self.fog_map[y][x]:
                    
                    if (x, y) in self.last_player_pos or math.sqrt((x - self.last_player_pos[0]) ** 2 + (y - self.last_player_pos[1]) ** 2) <= self.last_vision_radius:
                        self.fog_surface.fill((0, 0, 0, 0), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))  # 完全透明（當前視野內）
                    else:
                        self.fog_surface.fill((0, 0, 0, 128), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))  # 半透明黑色（探索過但不在視野內）

        self.screen.blit(self.fog_surface, (0, 0))
        print("RenderManager: 繪製迷霧")

    def update_camera(self, dt: float) -> None:
        """更新攝影機位置，使其跟隨玩家。

        Args:
            dt: 每幀的時間間隔（秒），用於平滑移動。

        根據玩家的位置計算目標偏移量，並平滑更新攝影機位置。
        """
        if self.game.entity_manager.player:
            target_x = self.game.entity_manager.player.x - SCREEN_WIDTH // 2
            target_y = self.game.entity_manager.player.y - SCREEN_HEIGHT // 2
            self.camera_offset[0] += (target_x - self.camera_offset[0]) * self.camera_lerp_factor * dt
            self.camera_offset[1] += (target_y - self.camera_offset[1]) * self.camera_lerp_factor * dt
            print(f"RenderManager: 攝影機偏移量：{self.camera_offset}")
        self._update_fog_map_from_player()  # 更新迷霧

    def draw_game_world(self) -> None:
        """繪製遊戲世界，包括地牢、實體、小地圖和迷霧。

        清除螢幕並繪製地牢背景、實體、前景、小地圖和迷霧。
        """
        self.screen.fill((0, 0, 0))  # 用黑色填充螢幕
        dungeon = self.game.dungeon_manager.get_dungeon()
        dungeon.draw_background(self.screen, self.camera_offset)
        self.game.entity_manager.draw(self.screen, self.camera_offset)
        if self.game.entity_manager.player and self.game.entity_manager.player.fog:
            self._draw_fog()  # 繪製迷霧
        dungeon.draw_foreground(self.screen, self.camera_offset)
        self._draw_minimap()  # 繪製小地圖

    def draw_menu(self) -> None:
        """繪製當前菜單。

        先繪製遊戲世界作為背景，然後繪製菜單。
        """
        assert self.game.menu_manager.current_menu is not None # 確保有當前菜單
        self.draw_game_world()
        self.game.menu_manager.draw() 
        print(f"RenderManager: 繪製菜單 {self.game.menu_manager.current_menu.__class__.__name__ if self.game.menu_manager.current_menu else 'None'}")

    def draw_skill_selection(self) -> None:
        """繪製技能選擇畫面。

        顯示所有可用技能，標記已選擇的技能，並顯示當前技能鏈和選擇數量。
        """
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 36)
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
        """繪製大廳狀態。

        繪製遊戲世界並在需要時顯示菜單。
        """
        self.draw_game_world()
        if self.game.menu_manager.current_menu:
            self.game.menu_manager.draw()
        pygame.display.flip()

    def draw_playing(self) -> None:
        """繪製遊戲進行狀態。

        繪製遊戲世界並顯示當前技能名稱。
        """
        self.draw_game_world()
        if self.game.entity_manager.player and self.game.entity_manager.player.skill_chain[self.game.entity_manager.player.current_skill_chain_idx]:
            font = pygame.font.SysFont(None, 36)
            skill_name = self.game.entity_manager.player.skill_chain[self.game.entity_manager.player.current_skill_chain_idx][self.game.entity_manager.player.current_skill_idx].name
            skill_text = font.render(f"current skill：{skill_name}", True, (255, 255, 255))
            self.screen.blit(skill_text, (10, 50))
        if self.game.menu_manager.current_menu:
            self.game.menu_manager.draw()
        pygame.display.flip()

    def draw_win(self) -> None:
        """繪製勝利畫面。

        顯示“勝利”消息，表明玩家已清除所有地牢。
        """
        self.screen.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 48)
        win_text = font.render("勝利！您已清除所有地牢！", True, (255, 255, 0))
        self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - win_text.get_height() // 2))
        pygame.display.flip()