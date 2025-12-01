# Roguelike Dungeon 專案 Class Diagram

## 專案架構概述

這是一個AOOP架構的 Roguelike 地牢遊戲專案，使用 Pygame 和 Esper 框架開發。

---

## 核心架構圖

```mermaid
classDiagram
    %% ========================================
    %% 核心遊戲類別
    %% ========================================
    class Game {
        +screen: pygame.Surface
        +clock: pygame.time.Clock
        +world: esper.World
        +state: str
        +dungeon_manager: DungeonManager
        +entity_manager: EntityManager
        +event_manager: EventManager
        +render_manager: RenderManager
        +menu_manager: MenuManager
        +storage_manager: StorageManager
        +audio_manager: AudioManager
        +player_entity: int
        +__init__(screen, clock)
        +start_game()
        +show_menu(menu_name, data)
        +hide_menu(menu_name)
        +update(dt)
        +draw()
        +run()
    }

    %% ========================================
    %% Manager 類別群組
    %% ========================================
    class DungeonManager {
        +game: Game
        +dungeon: Dungeon
        +current_dungeon_id: int
        +__init__(game)
        +initialize_lobby()
        +initialize_dungeon(dungeon_id)
        +get_dungeon()
    }

    class EntityManager {
        +game: Game
        +world: esper.World
        +player_entity: int
        +__init__(game)
        +get_valid_tiles(room, tile_types)
        +tile_to_pixel(tile_x, tile_y)
        +initialize_lobby_entities(room)
        +initialize_dungeon_entities()
        +clear_entities()
        +get_interactable_entities()
        +get_player_component()
    }

    class EventManager {
        +game: Game
        +keys_pressed: Dict
        +mouse_pressed: Dict
        +__init__(game)
        +handle_event(event)
        -_handle_menu_event(event)
        -_handle_skill_selection_event(event)
        -_handle_lobby_event(event)
        -_handle_playing_event(event)
        -_handle_interaction()
    }

    class RenderManager {
        +game: Game
        +screen: pygame.Surface
        +camera_offset: List[float]
        +target_camera_offset: List[float]
        +minimap_surface: pygame.Surface
        +fog_map: List[List[bool]]
        +__init__(game)
        +reset_minimap()
        +reset_fog()
        +update_camera(dt)
        +draw_game_world()
        +draw_menu()
        +draw_skill_selection()
        +draw_lobby()
        +draw_playing()
        +draw_win()
        -_draw_ui()
        -_draw_minimap()
        -_draw_fog()
    }

    class MenuManager {
        +game: Game
        +menus: Dict
        +current_menu: AbstractMenu
        +__init__(game)
        +show_menu(menu_name)
        +hide_menu()
        +handle_event(event)
        +draw(screen)
    }

    class StorageManager {
        +game: Game
        +player_data: Dict
        +__init__(game)
        +save_player_data()
        +load_player_data()
        +get_player_stat(key)
        +set_player_stat(key, value)
    }

    class AudioManager {
        +bgm_volume: float
        +sfx_volume: float
        +current_bgm: str
        +__init__()
        +play_bgm(name)
        +stop_bgm()
        +play_sfx(name)
        +set_bgm_volume(volume)
        +set_sfx_volume(volume)
    }

    %% ========================================
    %% Dungeon 模組
    %% ========================================
    class Dungeon {
        +config: DungeonConfig
        +rooms: List[Room]
        +grid: List[List[str]]
        +width: int
        +height: int
        +start_position: Tuple[int, int]
        +background_tileset: Dict
        +foreground_tileset: Dict
        +builder: DungeonBuilder
        +tile_manager: TileManager
        +__init__(config)
        +initialize_dungeon(dungeon_id)
        +initialize_lobby()
        +set_tilesets(background_ts, foreground_ts)
        +draw_background(screen, camera_offset)
        +draw_foreground(screen, camera_offset)
        +get_tile(x, y)
        +is_passable(x, y)
        +get_start_position()
    }

    class DungeonBuilder {
        +config: DungeonConfig
        +bsp_generator: BSPGenerator
        +room_placer: RoomPlacer
        +room_type_assigner: RoomTypeAssigner
        +corridor_generator: CorridorGenerator
        +door_generator: DoorGenerator
        +tile_manager: TileManager
        +__init__(config)
        +build()
        +initialize_dungeon(dungeon_id)
        -_build_room_graph(rooms)
        +generate_room(x, y, width, height, room_id, room_type)
        -_place_room(room)
        -_add_walls()
        +adjust_wall()
        -_calculate_room_distance(room1, room2)
        +get_statistics(rooms, grid)
        -_initialize_grid()
    }

    class Room {
        +id: int
        +x: float
        +y: float
        +width: float
        +height: float
        +tiles: List[List[str]]
        +room_type: RoomType
        +connections: List[Tuple[int, str]]
        +__post_init__()
        +generate_tiles()
        +get_tiles()
        +is_end_room()
    }

    class DungeonConfig {
        +width: int
        +height: int
        +min_room_size: int
        +max_room_size: int
        +max_depth: int
        +min_rooms: int
        +max_rooms: int
        +corridor_width: int
        +room_padding: int
    }

    class RoomType {
        <<enumeration>>
        EMPTY
        START
        END
        LOBBY
        MONSTER
        TRAP
        REWARD
        NPC
    }

    %% Dungeon 生成器與管理器
    class BSPGenerator {
        +config: DungeonConfig
        +__init__(config)
        +generate()
        -_split_node(node, depth)
    }

    class BSPNode {
        +x: int
        +y: int
        +width: int
        +height: int
        +left: BSPNode
        +right: BSPNode
    }

    class RoomPlacer {
        +config: DungeonConfig
        +__init__(config)
        +place_rooms(nodes)
    }

    class RoomTypeAssigner {
        +config: DungeonConfig
        +__init__(config)
        +assign_types(rooms, dungeon_id)
    }

    class CorridorGenerator {
        +config: DungeonConfig
        +tile_manager: TileManager
        +__init__(config, tile_manager)
        +generate_corridors(rooms, mst_edges)
    }

    class DoorGenerator {
        +tile_manager: TileManager
        +__init__(tile_manager)
        +place_doors(rooms)
    }

    class TileManager {
        +grid: List[List[str]]
        +width: int
        +height: int
        +__init__(width, height)
        +get_tile(x, y)
        +set_tile(x, y, tile_type)
        +is_passable(x, y)
    }

    %% 圖算法模組
    class GraphAlgorithms {
        <<utility>>
        +kruskal_mst(edges)
        +build_complete_graph(rooms)
    }

    class Pathfinding {
        <<utility>>
        +a_star(start, goal, grid)
        +bresenham_line(x0, y0, x1, y1)
    }

    %% ========================================
    %% ECS 架構
    %% ========================================
    
    %% ECS Components
    class Position {
        +x: float
        +y: float
    }

    class Velocity {
        +x: float
        +y: float
        +speed: float
    }

    class Health {
        +base_max_hp: int
        +max_hp: int
        +current_hp: int
        +max_shield: int
        +current_shield: int
        +regen_rate: float
    }

    class Defense {
        +defense: int
        +dodge_rate: float
        +element: str
        +resistances: Dict[str, float]
        +invulnerable: bool
    }

    class Combat {
        +damage: int
        +can_attack: bool
        +atk_element: str
        +damage_to_element: Dict[str, float]
        +max_penetration_count: int
        +current_penetration_count: int
        +collision_cooldown: float
        +buffs: List
        +explosion_damage: int
    }

    class Renderable {
        +image: pygame.Surface
        +shape: str
        +w: int
        +h: int
        +color: tuple
        +layer: int
        +visible: bool
    }

    class Input {
        +dx: float
        +dy: float
        +attack: bool
        +special: bool
        +target_x: float
        +target_y: float
    }

    class Collider {
        +w: int
        +h: int
        +pass_wall: bool
        +collision_group: str
        +collision_mask: List[str]
    }

    class AI {
        +behavior_tree: object
        +current_action: str
        +action_list: List[str]
        +actions: Dict
        +vision_radius: int
        +half_hp_triggered: bool
    }

    class Buffs {
        +active_buffs: List
        +modifiers: Dict[str, float]
    }

    class Tag {
        +tag: str
    }

    class PlayerComponent {
        +max_skill_chains: int
        +max_skill_chain_length: int
        +skill_chains: List[List[Skill]]
        +current_skill_chain_index: int
        +current_skill_index: int
        +energy: float
        +max_energy: float
        +base_energy_regen_rate: float
        +energy_regen_rate: float
        +current_shield: int
        +max_shield: int
        +fog: bool
        +vision_radius: int
        +mana: int
    }

    class NPCInteractComponent {
        +tag: str
        +interaction_range: float
        +alchemy_options: List[Dict]
        +is_interacting: bool
        +show_interact_prompt: bool
        +start_interaction: Callable
    }

    class ProjectileState {
        +direction: Tuple[float, float]
        +max_speed: float
        +max_lifetime: float
        +current_lifetime: float
        +explode_on_collision: bool
        +collision_tracking: Dict[int, float]
    }

    class ExpansionLifecycle {
        +hide_time: float
        +wait_time: float
        +is_hidden: bool
        +expanded: bool
        +explosion_animation_done: bool
    }

    class ExpansionRenderData {
        +outer_radius: float
        +inner_radius: float
        +current_outer_radius: float
        +current_inner_radius: float
        +expansion_time: float
        +explosion_animation_time: float
        +animation_frames: List
    }

    %% ECS Systems
    class MovementSystem {
        +process(*args, **kwargs)
    }

    class RenderSystem {
        +process(*args, **kwargs)
        +draw_health_bar(screen, pos, health, rend, camera_offset)
    }

    class InputSystem {
        +process(*args, **kwargs)
    }

    class HealthSystem {
        +process(*args, **kwargs)
        +take_damage(entity, factor, element, base_damage, ...)
        +heal(entity, amount)
        +add_shield(entity, amount)
        +set_max_hp(entity, new_max_hp)
        +set_max_shield(entity, new_max_shield)
        -_calculate_affinity_multiplier(attack_element, defend_element)
        -_create_damage_text(entity, text)
        -_handle_death(entity, game)
    }

    class BuffSystem {
        +synthesis_rules: Dict
        +process(*args, **kwargs)
        -_apply_buff_effects(entity, buff, dt, game)
        -_remove_buff(entity, buff, buffs_comp, game)
        -_synthesize_buffs(entity, buffs_comp, game)
        -_update_modifiers(entity, buffs_comp, game)
    }

    class CollisionSystem {
        +process(*args, **kwargs)
    }

    class AISystem {
        +process(*args, **kwargs)
    }

    class ProjectileSystem {
        +process(*args, **kwargs)
    }

    class ExpansionSystem {
        +process(*args, **kwargs)
    }

    class EnergySystem {
        +process(*args, **kwargs)
    }

    %% ========================================
    %% Entity Facade 類別
    %% ========================================
    class Player {
        +game: Game
        +ecs_entity: int
        +__init__(game, ecs_entity)
        -_get_player_comp()
        -_get_combat_comp()
        -_get_position_comp()
        -_get_health_comp()
        -_get_defense_comp()
        -_get_velocity_comp()
        -_get_renderable_comp()
        -_get_buffs_comp()
        +update(dt, current_time)
        +add_skill_to_chain(skill, chain_idx)
        +switch_skill_chain(chain_idx)
        +switch_skill(index)
        +activate_skill(direction, current_time, target_position)
        +canfire()
        +add_buff(buff)
        +energy
        +max_energy
        +x, y, w, h
        +current_hp, max_hp
        +speed, damage
    }

    class Enemy1 {
        +game: Game
        +ecs_entity: int
        +__init__(game, ecs_entity)
        +update(dt, current_time)
    }

    class AlchemyPotNPC {
        +game: Game
        +ecs_entity: int
        +__init__(game, ecs_entity)
        +start_interaction()
    }

    class DungeonPortalNPC {
        +game: Game
        +ecs_entity: int
        +available_dungeons: List[Dict]
        +__init__(game, ecs_entity)
        +start_interaction()
    }

    class MagicCrystalNPC {
        +game: Game
        +ecs_entity: int
        +__init__(game, ecs_entity)
        +start_interaction()
    }

    class Dummy {
        +game: Game
        +ecs_entity: int
        +__init__(game, ecs_entity)
    }

    %% ECS Factory
    class ECSFactory {
        <<utility>>
        +create_player_entity(world, x, y, tag, game)
        +create_enemy1_entity(world, x, y, game, tag, ...)
        +create_alchemy_pot_npc(world, x, y, w, h, tag, ...)
        +create_dungeon_portal_npc(world, x, y, w, h, ...)
        +create_magic_crystal_npc(world, x, y, w, h, tag, ...)
        +create_dummy_entity(world, x, y, w, h, tag, game)
    }

    %% ========================================
    %% Skill 系統
    %% ========================================
    class Skill {
        <<abstract>>
        +name: str
        +description: str
        +energy_cost: float
        +cooldown: float
        +last_used: float
        +__init__(name, description, energy_cost, cooldown)
        +can_use(player, current_time)
        +use(player, direction, current_time, target_position)*
        +get_info()
    }

    class ShootSkill {
        +bullet_type: str
        +bullet_speed: float
        +bullet_damage: int
        +bullet_element: str
        +use(player, direction, current_time, target_position)
    }

    class BuffSkill {
        +buff_type: str
        +buff_duration: float
        +buff_strength: float
        +use(player, direction, current_time, target_position)
    }

    %% ========================================
    %% Buff 系統
    %% ========================================
    class Buff {
        <<abstract>>
        +name: str
        +duration: float
        +remaining_time: float
        +on_apply(entity, game)*
        +on_remove(entity, game)*
        +update(entity, dt, game)*
    }

    class ElementBuff {
        +element: str
        +strength: float
        +on_apply(entity, game)
        +on_remove(entity, game)
        +update(entity, dt, game)
    }

    %% ========================================
    %% Menu 系統
    %% ========================================
    class AbstractMenu {
        <<abstract>>
        +game: Game
        +buttons: List[Button]
        +__init__(game)
        +handle_event(event)*
        +draw(screen)*
    }

    class Button {
        +rect: pygame.Rect
        +text: str
        +action: Callable
        +__init__(rect, text, action)
        +is_clicked(pos)
        +draw(screen)
    }

    class StatMenu {
        +handle_event(event)
        +draw(screen)
    }

    class AmplifierChooseMenu {
        +handle_event(event)
        +draw(screen)
    }

    class SkillChainMenu {
        +handle_event(event)
        +draw(screen)
    }

    class SkillChainEditMenu {
        +handle_event(event)
        +draw(screen)
    }

    class SkillLibraryMenu {
        +handle_event(event)
        +draw(screen)
    }

    class SettingsMenu {
        +handle_event(event)
        +draw(screen)
    }

    %% ========================================
    %% 關聯關係
    %% ========================================
    
    %% Game 與 Managers 的關聯
    Game --> DungeonManager : 管理
    Game --> EntityManager : 管理
    Game --> EventManager : 管理
    Game --> RenderManager : 管理
    Game --> MenuManager : 管理
    Game --> StorageManager : 管理
    Game --> AudioManager : 管理

    %% DungeonManager 與 Dungeon 的關聯
    DungeonManager --> Dungeon : 管理

    %% Dungeon 與其組件的關聯
    Dungeon --> DungeonBuilder : 使用
    Dungeon --> DungeonConfig : 配置
    Dungeon --> Room : 包含多個
    Dungeon --> TileManager : 使用

    %% DungeonBuilder 與生成器的關聯
    DungeonBuilder --> BSPGenerator : 使用
    DungeonBuilder --> RoomPlacer : 使用
    DungeonBuilder --> RoomTypeAssigner : 使用
    DungeonBuilder --> CorridorGenerator : 使用
    DungeonBuilder --> DoorGenerator : 使用
    DungeonBuilder --> TileManager : 使用
    DungeonBuilder --> Room : 創建

    %% BSP 相關
    BSPGenerator --> BSPNode : 創建

    %% Room 與 RoomType 的關聯
    Room --> RoomType : 使用

    %% EntityManager 與 ECS 的關聯
    EntityManager --> ECSFactory : 使用
    EntityManager --> Player : 創建 Facade

    %% ECS Factory 與 Entity Facade 的關聯
    ECSFactory --> Player : 創建
    ECSFactory --> Enemy1 : 創建
    ECSFactory --> AlchemyPotNPC : 創建
    ECSFactory --> DungeonPortalNPC : 創建
    ECSFactory --> MagicCrystalNPC : 創建
    ECSFactory --> Dummy : 創建

    %% Entity Facade 與 Components 的關聯
    Player --> Position : 使用
    Player --> Velocity : 使用
    Player --> Health : 使用
    Player --> Defense : 使用
    Player --> Combat : 使用
    Player --> Renderable : 使用
    Player --> Input : 使用
    Player --> PlayerComponent : 使用
    Player --> Buffs : 使用
    Player --> Collider : 使用

    Enemy1 --> Position : 使用
    Enemy1 --> Velocity : 使用
    Enemy1 --> Health : 使用
    Enemy1 --> Defense : 使用
    Enemy1 --> Combat : 使用
    Enemy1 --> Renderable : 使用
    Enemy1 --> AI : 使用
    Enemy1 --> Buffs : 使用
    Enemy1 --> Collider : 使用

    %% NPC Facade 與 Components 的關聯
    AlchemyPotNPC --> NPCInteractComponent : 使用
    DungeonPortalNPC --> NPCInteractComponent : 使用
    MagicCrystalNPC --> NPCInteractComponent : 使用

    %% Systems 處理 Components
    MovementSystem ..> Position : 處理
    MovementSystem ..> Velocity : 處理
    MovementSystem ..> Collider : 處理

    RenderSystem ..> Position : 處理
    RenderSystem ..> Renderable : 處理
    RenderSystem ..> Health : 處理

    InputSystem ..> Input : 處理
    InputSystem ..> Velocity : 處理

    HealthSystem ..> Health : 處理
    HealthSystem ..> Defense : 處理

    BuffSystem ..> Buffs : 處理

    CollisionSystem ..> Position : 處理
    CollisionSystem ..> Collider : 處理
    CollisionSystem ..> Combat : 處理

    AISystem ..> AI : 處理
    AISystem ..> Position : 處理

    ProjectileSystem ..> ProjectileState : 處理

    ExpansionSystem ..> ExpansionLifecycle : 處理
    ExpansionSystem ..> ExpansionRenderData : 處理

    EnergySystem ..> PlayerComponent : 處理

    %% Player 與 Skill 的關聯
    Player --> Skill : 使用多個
    PlayerComponent --> Skill : 包含多個

    %% Skill 繼承關係
    Skill <|-- ShootSkill : 繼承
    Skill <|-- BuffSkill : 繼承

    %% Buff 繼承關係
    Buff <|-- ElementBuff : 繼承

    %% Menu 繼承關係
    AbstractMenu <|-- StatMenu : 繼承
    AbstractMenu <|-- AmplifierChooseMenu : 繼承
    AbstractMenu <|-- SkillChainMenu : 繼承
    AbstractMenu <|-- SkillChainEditMenu : 繼承
    AbstractMenu <|-- SkillLibraryMenu : 繼承
    AbstractMenu <|-- SettingsMenu : 繼承

    %% MenuManager 與 Menu 的關聯
    MenuManager --> AbstractMenu : 管理多個
    AbstractMenu --> Button : 包含多個
```

---

## 多餘與未使用的檔案分析

### 🔴 可能多餘的檔案

以下檔案在當前架構中可能是多餘的或未被使用：

1. **`backup/dungeon.py`** ⚠️
   - **狀態**: 備份檔案
   - **說明**: 這是舊版的地牢實作，已被重構後的模組化架構取代
   - **建議**: 可以刪除或保留作為參考

2. **`src/ecs/test.py`** ⚠️
   - **狀態**: 測試檔案
   - **說明**: 看起來是用於測試 ECS 系統的臨時檔案
   - **建議**: 如果不再使用，可以刪除；或移至專門的測試目錄

3. **`png_processer.py`** ⚠️
   - **狀態**: 工具腳本
   - **說明**: 圖片處理工具，可能用於資源預處理
   - **建議**: 如果只在開發階段使用，可移至 tools 或 scripts 目錄

4. **`esper/__init__.py`** ⚠️
   - **狀態**: 第三方函式庫
   - **說明**: Esper ECS 框架的本地副本
   - **建議**: 應該使用 pip 安裝的版本，而非專案內的副本

5. **`src/entities/basic_entity.py`** ⚠️
   - **狀態**: 幾乎空白的檔案（只有 32 bytes）
   - **說明**: 可能是早期架構的殘留
   - **建議**: 可以刪除

6. **`src/dungeon/bridge.py`** ⚠️
   - **狀態**: 橋接檔案（469 bytes）
   - **說明**: 可能是用於舊架構與新架構的橋接
   - **建議**: 如果重構完成，可以刪除

7. **`src/dungeon/examples/simple_dungeon_generation.py`** ⚠️
   - **狀態**: 範例檔案
   - **說明**: 地牢生成的簡單範例
   - **建議**: 保留作為文檔或移至 examples 目錄

### ✅ 重要且正在使用的檔案

以下是專案的核心檔案，**不應刪除**：

#### 核心遊戲邏輯
- `main.py` - 遊戲入口
- `src/game.py` - 遊戲主類別
- `src/config.py` - 全域配置

#### Manager 層
- `src/dungeon_manager.py` - 地牢管理
- `src/entity_manager.py` - 實體管理
- `src/event_manager.py` - 事件管理
- `src/render_manager.py` - 渲染管理
- `src/menu_manager.py` - 菜單管理
- `src/storage_manager.py` - 存檔管理
- `src/audio_manager.py` - 音效管理

#### Dungeon 模組
- `src/dungeon/dungeon.py` - 地牢主類別
- `src/dungeon/room.py` - 房間類別
- `src/dungeon/bsp_node.py` - BSP 節點
- `src/dungeon/builder/dungeon_builder.py` - 地牢建造器
- `src/dungeon/config/dungeon_config.py` - 地牢配置
- `src/dungeon/algorithms/*` - 演算法（BSP、路徑尋找、圖算法）
- `src/dungeon/generators/*` - 生成器（走廊、門、房間）
- `src/dungeon/managers/tile_manager.py` - 瓦片管理

#### ECS 架構
- `src/ecs/components.py` - ECS 組件定義
- `src/ecs/systems.py` - ECS 系統實作
- `src/ecs/ai.py` - AI 行為樹

#### Entity 層
- `src/entities/ecs_factory.py` - ECS 實體工廠
- `src/entities/player/player.py` - 玩家 Facade
- `src/entities/enemy/*` - 敵人實體
- `src/entities/npc/*` - NPC 實體
- `src/entities/bullet/*` - 子彈實體
- `src/entities/trap/*` - 陷阱實體
- `src/entities/*_entity.py` - 各種實體 Mixin

#### Skill 系統
- `src/skills/skill.py` - 技能基類
- `src/skills/abstract_skill.py` - 抽象技能
- `src/skills/shoot_skill.py` - 射擊技能
- `src/skills/buff_skill.py` - Buff 技能

#### Buff 系統
- `src/buffs/buff.py` - Buff 基類
- `src/buffs/element_buff.py` - 元素 Buff

#### Menu 系統
- `src/menu/abstract_menu.py` - 抽象菜單
- `src/menu/button.py` - 按鈕組件
- `src/menu/menus/*` - 各種菜單實作

---

## 架構設計模式總結

### 1. **ECS (Entity Component System) 架構**
   - **Components**: 純數據容器（Position, Velocity, Health 等）
   - **Systems**: 處理邏輯（MovementSystem, RenderSystem 等）
   - **Entities**: 由 Components 組成的 ID

### 2. **Facade 模式**
   - `Player`, `Enemy1`, `AlchemyPotNPC` 等類別作為 ECS 實體的門面
   - 提供高層次的 API，隱藏 ECS 的複雜性

### 3. **Builder 模式**
   - `DungeonBuilder` 協調多個生成器來構建完整地牢
   - 分離構建過程與表示

### 4. **Factory 模式**
   - `ECSFactory` 負責創建各種 ECS 實體
   - 集中管理實體創建邏輯

### 5. **Manager 模式**
   - 各種 Manager 類別（DungeonManager, EntityManager 等）
   - 負責協調和管理各自領域的邏輯

### 6. **Strategy 模式**
   - AI 系統使用行為樹
   - 不同的技能類型（ShootSkill, BuffSkill）

---

## 模組依賴關係

```
main.py
  └─> Game
       ├─> DungeonManager ──> Dungeon ──> DungeonBuilder ──> Generators
       ├─> EntityManager ──> ECSFactory ──> Entity Facades
       ├─> EventManager
       ├─> RenderManager ──> RenderSystem
       ├─> MenuManager ──> Menus
       ├─> StorageManager
       └─> AudioManager
```

---

## 建議的改進方向

1. **移除多餘檔案**: 清理 backup、test 和未使用的檔案
2. **統一測試**: 將測試檔案移至專門的 `tests/` 目錄
3. **文檔化**: 為每個模組添加詳細的文檔字串
4. **依賴管理**: 使用 `requirements.txt` 管理第三方依賴
5. **配置分離**: 考慮使用配置檔案（JSON/YAML）而非硬編碼
