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
        self.minimap_cache_surface = None
        self.minimap_width = 0
        self.minimap_height = 0
        self.minimap_offset = (0, 0)
        self.fog_map = None
        self.fog_surface = None
        self.last_player_pos = None
        self.last_vision_radius = None

    def reset_minimap(self) -> None:
        """重置小地圖"""
        self._initialize_minimap()
        # 如果需要，這裡也可以重置 fog_map
        # self._initialize_fog_map()
        
    def reset_fog(self) -> None:
        self._initialize_fog_map()
    
    def _initialize_minimap(self) -> None:
        """初始化小地圖的尺寸、偏移與緩存 Surface。"""
        dungeon = self.game.dungeon_manager.get_dungeon()
        self.minimap_width = int(dungeon.grid_width * self.minimap_scale)
        self.minimap_height = int(dungeon.grid_height * self.minimap_scale)
        self.minimap_offset = (SCREEN_WIDTH - self.minimap_width - 10, 10)
        
        # 初始化緩存 Surface (全黑)
        self.minimap_cache_surface = pygame.Surface((self.minimap_width, self.minimap_height))
        self.minimap_cache_surface.fill((0, 0, 0))
        
        print(f"RenderManager: 初始化小地圖與緩存，尺寸 ({self.minimap_width}, {self.minimap_height})")
    
    def _draw_tile_to_minimap_cache(self, x: int, y: int, tile_type: int) -> None:
        """[優化輔助] 將單個格子繪製到小地圖緩存上"""
        if self.minimap_cache_surface is None:
            return
            
        color = ROOM_FLOOR_COLORS.get(tile_type, (50, 50, 50))
        pygame.draw.rect(
            self.minimap_cache_surface, 
            color,
            (x * self.minimap_scale, y * self.minimap_scale, self.minimap_scale, self.minimap_scale)
        )

    def _initialize_fog_map(self) -> None:
        """初始化視野迷霧地圖。"""
        dungeon = self.game.dungeon_manager.get_dungeon()
        self.fog_map = [[False for _ in range(dungeon.grid_width)]
                       for _ in range(dungeon.grid_height)]
        self.fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        print("RenderManager: 初始化視野迷霧地圖")

    def _update_fog_map_from_player(self) -> None:
        """根據玩家位置更新視野迷霧 (含小地圖增量更新)。"""
        if not self.game.entity_manager.player:
            return
        
        # 確保 fog_map 和 cache 都已初始化
        if not self.fog_map:
            self._initialize_fog_map()
        if self.minimap_cache_surface is None:
            self._initialize_minimap()

        player = self.game.entity_manager.player
        dungeon = self.game.dungeon_manager.get_dungeon()
        vision_radius = getattr(player, 'vision_radius', 5)
        player_tile_x = int(player.x // TILE_SIZE)
        player_tile_y = int(player.y // TILE_SIZE)

        # 效能優化：如果玩家位置和視野半徑沒變，直接返回
        if self.last_player_pos == (player_tile_x, player_tile_y) and self.last_vision_radius == vision_radius:
            return

        self.last_player_pos = (player_tile_x, player_tile_y)
        self.last_vision_radius = vision_radius

        # 計算視野邊界，避免不必要的迴圈
        start_x = max(0, player_tile_x - vision_radius)
        end_x = min(dungeon.grid_width, player_tile_x + vision_radius + 1)
        start_y = max(0, player_tile_y - vision_radius)
        end_y = min(dungeon.grid_height, player_tile_y + vision_radius + 1)

        vision_sq = vision_radius ** 2  # 使用距離平方避免開根號

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # 簡單的距離檢查
                if (x - player_tile_x) ** 2 + (y - player_tile_y) ** 2 <= vision_sq:
                    # 只有當該格 "尚未被探索" 時，才進行視線檢查與更新
                    if not self.fog_map[y][x]:
                        can_see = False
                        if dungeon.dungeon_tiles[y][x] not in PASSABLE_TILES:
                            # 牆壁通常直接視為可見（如果距離夠近），或者也做視線檢查
                            # 這裡簡化邏輯：如果在範圍內且是牆壁，設為可見
                            can_see = True 
                        elif self.has_line_of_sight(player_tile_x, player_tile_y, x, y, dungeon):
                            can_see = True
                        
                        if can_see:
                            self.fog_map[y][x] = True
                            # [關鍵優化] 立即將新探索的格子畫到小地圖緩存上
                            self._draw_tile_to_minimap_cache(x, y, dungeon.dungeon_tiles[y][x])
                            
        # 移除這裡的 print，避免洗版
        # print(f"RenderManager: 更新迷霧...")

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
        """繪製小地圖 (極速版)。"""
        # 1. 安全檢查：如果緩存不存在，初始化它 (並可能需要重繪已探索區域)
        if self.minimap_cache_surface is None:
            self._initialize_minimap()
            # 如果是中途載入，這裡可能需要根據 fog_map 重建整個緩存，
            # 但通常 _update_fog_map_from_player 會隨著移動慢慢補上，
            # 若要完美，可以加一個 _rebuild_minimap_cache() 方法。

        # 2. 直接繪製緩存的靜態背景 (O(1) 操作)
        self.screen.blit(self.minimap_cache_surface, self.minimap_offset)

        # 3. 繪製動態物件：玩家 (O(1) 操作)
        if self.game.entity_manager.player:
            # 計算玩家在小地圖上的相對座標
            p_x = self.game.entity_manager.player.x
            p_y = self.game.entity_manager.player.y
            
            # 轉換為小地圖座標
            minimap_player_x = self.minimap_offset[0] + (p_x / TILE_SIZE * self.minimap_scale)
            minimap_player_y = self.minimap_offset[1] + (p_y / TILE_SIZE * self.minimap_scale)

            # 畫紅點
            pygame.draw.rect(
                self.screen, 
                (255, 0, 0),
                (minimap_player_x, minimap_player_y, self.minimap_scale, self.minimap_scale)
            )

    def _draw_fog(self) -> None:
        """優化版：只繪製攝影機範圍內的迷霧"""
        dungeon = self.game.dungeon_manager.get_dungeon()
        # 填充全黑背景 (假設未探索區域是全黑)
        self.fog_surface.fill(BLACK) 

        # 1. 計算攝影機涵蓋的 Tile 索引範圍 (加上 buffer 避免邊緣閃爍)
        start_col = max(0, int(self.camera_offset[0] // TILE_SIZE))
        end_col = min(dungeon.grid_width, int((self.camera_offset[0] + SCREEN_WIDTH) // TILE_SIZE) + 1)
        
        start_row = max(0, int(self.camera_offset[1] // TILE_SIZE))
        end_row = min(dungeon.grid_height, int((self.camera_offset[1] + SCREEN_HEIGHT) // TILE_SIZE) + 1)

        # 2. 優化距離計算：使用「距離平方」避免開根號 (sqrt 很慢)
        vision_sq = self.last_vision_radius ** 2
        px, py = self.last_player_pos

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                # 如果這個格子已經探索過 (fog_map 記錄已探索區域)
                if self.fog_map[y][x]:
                    screen_x = x * TILE_SIZE - self.camera_offset[0]
                    screen_y = y * TILE_SIZE - self.camera_offset[1]
                    
                    # 計算距離平方
                    dist_sq = (x - px) ** 2 + (y - py) ** 2
                    
                    if dist_sq <= vision_sq:
                        # 視野內：完全透明 (挖洞)
                        # 注意：fill((0,0,0,0)) 需要 surface 支援 SRCALPHA
                        self.fog_surface.fill((0, 0, 0, 0), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    else:
                        # 已探索但不在視野內：半透明迷霧 (記憶迷霧)
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
        self._draw_boss_health_bar()  # 繪製 Boss 血條
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

        # 從 ECS 系統獲取 Health 組件
        import esper
        from src.ecs.components import Health, PlayerComponent, Defense
        
        player_entity_id = player.ecs_entity
        health_comp = None
        player_comp = None
        defense_comp = None
        
        if esper.has_component(player_entity_id, Health):
            health_comp = esper.component_for_entity(player_entity_id, Health)
        if esper.has_component(player_entity_id, PlayerComponent):
            player_comp = esper.component_for_entity(player_entity_id, PlayerComponent)
        if esper.has_component(player_entity_id, Defense):
            defense_comp = esper.component_for_entity(player_entity_id, Defense)

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
        panel_height = (bar_height + bar_spacing) * 6 + 20  # 增加一行給防禦
        self._draw_stone_panel(x_offset - 8, y_offset - 8, panel_width, panel_height)

        # HP 條（紅色，帶血液感）- 使用 ECS Health 組件
        if health_comp:
            hp_ratio = health_comp.current_hp / max(health_comp.max_hp, 1)
            self._draw_dungeon_bar(
                x_offset, y_offset, bar_width, bar_height,
                hp_ratio, 
                bar_color=(180, 30, 30),  # 深紅色
                bar_glow=(255, 60, 60),   # 高光紅
                label="生命",
                value_text=f"{health_comp.current_hp}/{health_comp.max_hp}",
                font=font, font_small=font_small
            )
        else:
            # 回退到舊系統
            hp_ratio = player.current_hp / max(player.max_hp, 1)
            self._draw_dungeon_bar(
                x_offset, y_offset, bar_width, bar_height,
                hp_ratio, 
                bar_color=(180, 30, 30),
                bar_glow=(255, 60, 60),
                label="生命",
                value_text=f"{player.current_hp}/{player.max_hp}",
                font=font, font_small=font_small
            )

        # 護盾條（藍色，帶魔法感）- 使用 ECS Health 組件
        y_offset += bar_height + bar_spacing
        if health_comp:
            shield_ratio = health_comp.current_shield / max(health_comp.max_shield, 1) if health_comp.max_shield > 0 else 0
            self._draw_dungeon_bar(
                x_offset, y_offset, bar_width, bar_height,
                shield_ratio,
                bar_color=(30, 80, 150),  # 深藍
                bar_glow=(60, 140, 255),  # 亮藍
                label="護盾",
                value_text=f"{health_comp.current_shield}/{health_comp.max_shield}",
                font=font, font_small=font_small
            )
        else:
            # 回退到舊系統
            shield_ratio = player.current_shield / max(player.max_shield, 1) if player.max_shield > 0 else 0
            self._draw_dungeon_bar(
                x_offset, y_offset, bar_width, bar_height,
                shield_ratio,
                bar_color=(30, 80, 150),
                bar_glow=(60, 140, 255),
                label="護盾",
                value_text=f"{player.current_shield}/{player.max_shield}",
                font=font, font_small=font_small
            )

        # 能量條（綠色，帶自然感）
        y_offset += bar_height + bar_spacing
        if player_comp:
            energy_ratio = player_comp.energy / max(player_comp.max_energy, 1)
            energy_current = int(player_comp.energy)
            energy_max = int(player_comp.max_energy)
        else:
            energy_ratio = player.energy / max(player.max_energy, 1)
            energy_current = int(player.energy)
            energy_max = int(player.max_energy)
            
        self._draw_dungeon_bar(
            x_offset, y_offset, bar_width, bar_height,
            energy_ratio,
            bar_color=(40, 120, 40),  # 深綠
            bar_glow=(80, 200, 80),   # 亮綠
            label="能量",
            value_text=f"{energy_current}/{energy_max}",
            font=font, font_small=font_small
        )

        # 防禦顯示（灰色，帶金屬感）- 使用 ECS Defense 組件
        y_offset += bar_height + bar_spacing
        if defense_comp:
            defense_value = defense_comp.defense
            dodge_rate = defense_comp.dodge_rate * 100  # 轉換為百分比
            defense_label = font_small.render("防禦:", True, (200, 180, 150))
            defense_value_text = font.render(f"{defense_value}", True, (200, 200, 200))
            dodge_text = font_small.render(f"閃避: {dodge_rate:.0f}%", True, (180, 180, 180))
            
            self.screen.blit(defense_label, (x_offset, y_offset + 2))
            self.screen.blit(defense_value_text, (x_offset + 60, y_offset))
            self.screen.blit(dodge_text, (x_offset + 120, y_offset + 4))
        else:
            # 回退顯示
            defense_label = font_small.render("防禦:", True, (200, 180, 150))
            defense_value_text = font.render(f"{player.defense if hasattr(player, 'defense') else 0}", True, (200, 200, 200))
            self.screen.blit(defense_label, (x_offset, y_offset + 2))
            self.screen.blit(defense_value_text, (x_offset + 60, y_offset))

        # 技能鏈顯示（文字加裝飾）
        y_offset += bar_height + bar_spacing
        chain_idx = player.current_skill_chain_idx + 1
        chain_label = font_small.render("連擊鏈:", True, (200, 180, 150))
        chain_value = font.render(f"#{chain_idx}", True, (255, 220, 120))
        self.screen.blit(chain_label, (x_offset, y_offset + 2))
        self.screen.blit(chain_value, (x_offset + 80, y_offset))

        # 下個技能顯示
        y_offset += bar_height + bar_spacing
        next_skill_name = "無"
        if player.skill_chain and len(player.skill_chain) > player.current_skill_chain_idx:
            current_chain = player.skill_chain[player.current_skill_chain_idx]
            if current_chain and len(current_chain) > player.current_skill_idx:
                next_skill = current_chain[player.current_skill_idx]
                if next_skill and len(current_chain) > 0:
                    next_skill_name = current_chain[player.current_skill_idx].name if hasattr(current_chain[player.current_skill_idx], 'name') else "未知"
        
        next_skill_label = font_small.render("下個技能:", True, (200, 180, 150))
        next_skill_value = font_small.render(next_skill_name, True, (150, 255, 150))
        self.screen.blit(next_skill_label, (x_offset, y_offset + 2))
        self.screen.blit(next_skill_value, (x_offset + 85, y_offset + 2))

        # 顯示當前 Buffs（右側區域）
        buff_x = SCREEN_WIDTH - 220
        buff_y = 15
        
        # 獲取 Buffs 組件
        from src.ecs.components import Buffs
        buffs_comp = None
        if esper.has_component(player_entity_id, Buffs):
            buffs_comp = esper.component_for_entity(player_entity_id, Buffs)
        
        if buffs_comp and buffs_comp.active_buffs:
            # 繪製 Buff 面板背景
            buff_panel_width = 200
            buff_panel_height = min(len(buffs_comp.active_buffs) * 28 + 20, 300)  # 最多顯示10個
            self._draw_stone_panel(buff_x, buff_y, buff_panel_width, buff_panel_height)
            
            # 繪製標題
            buff_title = font_small.render("當前增益效果:", True, (255, 220, 120))
            self.screen.blit(buff_title, (buff_x + 10, buff_y + 5))
            
            # 繪製每個 buff
            current_y = buff_y + 25
            for i, buff in enumerate(buffs_comp.active_buffs[:10]):  # 最多顯示10個
                # Buff 名稱
                buff_name_text = font_small.render(buff.name if buff.name else "未知", True, (200, 255, 200))
                self.screen.blit(buff_name_text, (buff_x + 10, current_y))
                
                # Buff 剩餘時間
                duration_text = font_small.render(f"{buff.duration:.1f}s", True, (180, 180, 180))
                self.screen.blit(duration_text, (buff_x + 140, current_y))
                
                current_y += 28

        # 法力值顯示（左側，主面板下方）
        mana_panel_width = 160
        mana_panel_height = 50
        mana_x = 15  # 與主面板對齊
        mana_y = y_offset + bar_height + 15  # 主面板下方
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

    def _draw_boss_health_bar(self) -> None:
        """繪製 Boss 血條於螢幕上方中央"""
        import esper
        from src.ecs.components import BossComponent, Health, Position
        
        # 尋找所有帶有 BossComponent 的實體
        boss_entities = []
        for ent, (boss_comp, health_comp) in esper.get_components(BossComponent, Health):
            if health_comp.current_hp > 0:
                boss_entities.append((ent, boss_comp, health_comp))
        
        if not boss_entities:
            return
        
        # 如果有多個 boss，只顯示第一個（通常只有一個）
        boss_ent, boss_comp, boss_health = boss_entities[0]
        
        # Boss 血條參數
        bar_width = 500
        bar_height = 40
        x = (SCREEN_WIDTH - bar_width) // 2
        y = 30
        
        # 使用 Boss 組件中的名稱
        boss_name = boss_comp.boss_name.upper() if boss_comp.boss_name else "BOSS"
        
        # 繪製背景面板
        panel_padding = 15
        panel_width = bar_width + panel_padding * 2
        panel_height = bar_height + panel_padding * 2 + 30  # 額外空間給名稱
        panel_x = x - panel_padding
        panel_y = y - panel_padding - 25
        self._draw_stone_panel(panel_x, panel_y, panel_width, panel_height)
        
        # 繪製 Boss 名稱
        font_boss = FontManager.get_font("Silver.ttf", 24)
        name_surf = font_boss.render(boss_name, True, (255, 50, 50))  # 紅色名稱
        name_x = (SCREEN_WIDTH - name_surf.get_width()) // 2
        name_y = y - 20
        self.screen.blit(name_surf, (name_x, name_y))
        
        # 計算血量比例
        hp_ratio = boss_health.current_hp / max(boss_health.max_hp, 1)
        
        # 外框（加厚，更顯眼）
        frame_thickness = 3
        pygame.draw.rect(self.screen, (15, 12, 10), 
                        (x - frame_thickness, y - frame_thickness, 
                         bar_width + frame_thickness * 2, bar_height + frame_thickness * 2))
        
        # 背景（深色）
        pygame.draw.rect(self.screen, (30, 25, 20), (x, y, bar_width, bar_height))
        
        # Boss 血條填充（紅色帶脈動感）
        fill_width = int(bar_width * hp_ratio)
        if fill_width > 0:
            # 深紅色底色
            pygame.draw.rect(self.screen, (150, 20, 20), (x, y, fill_width, bar_height))
            
            # 漸層高光（上半部）
            glow_height = bar_height // 2
            glow_surface = pygame.Surface((fill_width, glow_height), pygame.SRCALPHA)
            for i in range(glow_height):
                alpha = int(120 * (1 - i / glow_height))
                color = (255, 80, 80, alpha)
                pygame.draw.line(glow_surface, color, (0, i), (fill_width, i))
            self.screen.blit(glow_surface, (x, y))
            
            # 底部陰影
            shadow_height = bar_height // 3
            shadow_surface = pygame.Surface((fill_width, shadow_height), pygame.SRCALPHA)
            for i in range(shadow_height):
                alpha = int(80 * (i / shadow_height))
                pygame.draw.line(shadow_surface, (0, 0, 0, alpha), (0, i), (fill_width, i))
            self.screen.blit(shadow_surface, (x, y + bar_height - shadow_height))
        
        # 內框高光
        pygame.draw.rect(self.screen, (100, 90, 80), (x, y, bar_width, bar_height), 2)
        
        # HP 數值文字（中央，大字體）
        font_hp = FontManager.get_font("Silver.ttf", 22)
        hp_text = f"{boss_health.current_hp} / {boss_health.max_hp}"
        hp_surf = font_hp.render(hp_text, True, (255, 255, 255))
        hp_x = x + (bar_width - hp_surf.get_width()) // 2
        hp_y = y + (bar_height - hp_surf.get_height()) // 2
        
        # 文字陰影（增加可讀性）
        shadow_surf = font_hp.render(hp_text, True, (0, 0, 0))
        self.screen.blit(shadow_surf, (hp_x + 2, hp_y + 2))
        self.screen.blit(hp_surf, (hp_x, hp_y))