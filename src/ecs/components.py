from dataclasses import dataclass, field
from typing import Optional, List, Dict, TYPE_CHECKING, Tuple
from ..config import TILE_SIZE

if TYPE_CHECKING:
    from ..skills.skill import Skill 
    SkillType = Skill 
else:
    # 運行時可能不需要實際的 Skill 類別，用 Any 替代或忽略
    SkillType = object

# ProjectileState 和 BulletComponent 合併
@dataclass
class ProjectileState:
    """
    通用拋射物 (Projectile) 的運行狀態組件。
    包含移動、壽命追蹤和碰撞機制，適用於所有子彈。
    """
    # 運動屬性
    direction: Tuple[float, float] = (0.0, 0.0) 
    max_speed: float = 300.0  
    can_move: bool = True
    
    # 壽命與計時
    max_lifetime: float = 5.0     # 總壽命
    current_lifetime: float = field(init=False)
    
    # 碰撞行為
    explode_on_collision: bool = True # 在非穿透碰撞時是否觸發爆炸或銷毀
    
    # 碰撞追蹤 (取代 hitted_entities / last_hit_times)
    # Key: 實體 ID (int), Value: 上次擊中時間 (float)
    collision_tracking: Dict[int, float] = field(default_factory=dict)

    def __post_init__(self):
        """初始化後，當前壽命等於最大壽命。"""
        self.current_lifetime = self.max_lifetime

# ExpandingCircleState (名稱更精確為 ExpansionLifecycle)
@dataclass
class ExpansionLifecycle:
    """
    ExpandingCircleBullet 獨特的生命週期組件。
    用於管理子彈的隱藏、等待、擴張和爆炸階段。
    """
    # 階段計時 (初始值)
    hide_time: float = 0.0     # 隱藏階段剩餘時間
    wait_time: float = 0.0     # 等待階段剩餘時間

    # 階段狀態 (運行時追蹤)
    is_hidden: bool = field(init=False)
    expanded: bool = False             # 擴張動畫/傷害判定是否完成
    explosion_animation_done: bool = False # 爆炸後的銷毀動畫是否完成
    
    def __post_init__(self):
        self.is_hidden = self.hide_time > 0
        
# ExpansionRenderData (保留，但名稱稍作調整以強調其視覺性質)
@dataclass
class ExpansionRenderData:
    """
    ExpandingCircleBullet 視覺上的半徑、擴張速度和動畫幀數據。
    用於 RenderSystem 繪製和 ExpansionSystem 計算大小。
    """
    # 擴張參數
    outer_radius: float = TILE_SIZE 
    expansion_duration: float = 1.0  # 擴張所需時間
    
    # 運行時狀態
    initial_inner_radius: float = field(init=False)
    current_inner_radius: float = field(init=False)
    expansion_time: float = 0.0
    explosion_animation_time: float = 0.0

    # 動畫幀
    animation_frames: List[object] = field(default_factory=list) # List[pygame.Surface]

    def __post_init__(self):
        # 初始半徑計算
        self.initial_inner_radius = self.outer_radius * 0.1
        self.current_inner_radius = self.initial_inner_radius

@dataclass
class PlayerComponent:
    """
    玩家專屬的資料組件 (ECS Component)。
    包含了玩家的能量、技能鏈、視野等狀態數據。
    """
    # --- 技能鏈 (Skill Chain) 屬性 ---
    
    # max_skill_chains (Player 類別中推斷為 9)
    max_skill_chains: int = 9
    
    # max_skill_chain_length (程式碼中為 8)
    max_skill_chain_length: int = 8
    
    # skill_chain: 技能鏈列表。由於是可變類型 (List)，使用 field(default_factory) 確保每個實例獨立。
    skill_chain: List[List[SkillType]] = field(default_factory=lambda: [[] for _ in range(9)])
    
    # 當前活動技能鏈索引
    current_skill_chain_idx: int = 0
    
    # 當前活動技能在鏈中的索引
    current_skill_idx: int = 0
    
    # --- 能量 (Energy) 屬性 ---
    base_max_energy: float = 100.0
    
    # max_energy、energy 默認與 base_max_energy 相同
    max_energy: float = field(default=100.0) 
    energy: float = field(default=100.0)
    
    base_energy_regen_rate: float = 20.0
    energy_regen_rate: float = 20.0
    original_energy_regen_rate: float = 20.0
    
    # current_shield 屬性 (PlayerComponent 中新增)
    current_shield: int = 0
    max_shield: int = 0
    
    # --- 視野與貨幣屬性 ---
    fog: bool = True           # 是否啟用戰爭迷霧
    vision_radius: int = 10    # 視野半徑 (以地圖格計算)
    mana: int = 0              # 貨幣單位 (在您的程式碼片段中為 0)


@dataclass
class Position:
    x: float
    y: float

@dataclass
class Velocity:
    x: float = 0.0
    y: float = 0.0
    speed: float = 100.0

@dataclass
class Health:
    base_max_hp: int = 100  # 用於儲存基礎最大生命值
    max_hp: int = 100
    current_hp: int = 100
    max_shield: int = 0
    current_shield: int = 0
    regen_rate: float = 0.0
    

@dataclass
class Defense:
    defense: int = 0
    dodge_rate: float = 0.0
    element: str = "untyped"
    resistances: Optional[Dict[str, float]] = None
    invulnerable: bool = False

@dataclass
class Combat:
    damage: int = 0
    can_attack: bool = True
    atk_element: str = "untyped"
    damage_to_element: Optional[Dict[str, float]] = None
    max_penetration_count: int = 0
    current_penetration_count: int = 0
    collision_cooldown: float = 0.2
    collision_list: Dict[int, float] = field(default_factory=dict)
    explosion_range: float = 0.0
    explosion_damage: int = 0
    explosion_element: str = "untyped"
    # Percentage damage
    max_hp_percentage_damage: int = 0
    current_hp_percentage_damage: int = 0
    lose_hp_percentage_damage: int = 0
    cause_death: bool = True
    # Buffs to apply on hit
    buffs: List = field(default_factory=list)  # List[Buff]
    # Explosion percentage damage
    explosion_max_hp_percentage_damage: int = 0
    explosion_current_hp_percentage_damage: int = 0
    explosion_lose_hp_percentage_damage: int = 0
    explosion_buffs: List = field(default_factory=list)  # List[Buff]

@dataclass
class Renderable:
    image: Optional[object] = None  # pygame.Surface
    shape: str = "rect"
    w: int = 32
    h: int = 32
    color: tuple = (255, 255, 255)
    layer: int = 0
    visible: bool = True

@dataclass
class Input:
    dx: float = 0.0
    dy: float = 0.0
    attack: bool = False
    special: bool = False
    target_x: float = 0.0
    target_y: float = 0.0

@dataclass
class Buffs:
    active_buffs: List = field(default_factory=list)  # List[Buff]
    modifiers: Dict[str, float] = field(default_factory=dict)

@dataclass
class Collider:
    w: int = 32
    h: int = 32
    pass_wall: bool = False
    collision_group: str = "default"
    collision_mask: Optional[List[str]] = None

@dataclass
class AI:
    behavior_tree: Optional[object] = None
    current_action: str = "idle"
    action_list: List[str] = field(default_factory=list)
    actions: Dict[str, object] = field(default_factory=dict)
    vision_radius: int = 5
    half_hp_triggered: bool = False

@dataclass
class Tag:
    tag: str = "default"

@dataclass
class NPCInteractComponent:
    """
    NPC 專屬的 ECS 組件。包含其交互範圍和狀態。
    """
    # 交互屬性
    interaction_range: float = 2*TILE_SIZE
    alchemy_options: List[Dict] = field(default_factory=list) # 合成配方列表
    
    # 運行時狀態
    is_interacting: bool = False
    show_interact_prompt: bool = False # 用於 InteractionSystem 和 RenderSystem

@dataclass
class DungeonPortalComponent:
    """
    地牢傳送門專屬 ECS 組件。
    包含可用的地牢列表和傳送門效果狀態。
    """
    available_dungeons: List[Dict] = field(
        default_factory=lambda: [{'name': 'Test Dungeon', 'level': 1, 'dungeon_id': 1}]
    )
    portal_effect_active: bool = False

