from typing import List, Tuple, Optional, Dict
import pygame # 繪圖和 Surface 相關
# 假設所有相關的基礎類別和技能類別都在正確的路徑下
from ..attack_entity import AttackEntity
from ..buffable_entity import BuffableEntity
from ..movement_entity import MovementEntity # 推斷：從 update 方法推斷出
from ..health_entity import HealthEntity     # 推斷：從 update 方法推斷出
from ...skills.skill import Skill            # 推斷：從 skill_chain 相關方法推斷出

# 為了讓 Player 類別能夠作為 ECS 實體的"門面" (Facade)
# 它應該繼承自所有的功能基類，並持有對 Game 實例和 ECS 實體 ID 的引用。

class Player(MovementEntity, HealthEntity, AttackEntity, BuffableEntity):
    """
    玩家實體類別。它是一個傳統 OOP 實體，
    同時作為一個 ECS 實體的門面 (Facade)，管理其自身的 Component ID。
    """
    def __init__(self, game, ecs_entity: int, vision_radius: int = 10):
        # 核心引用
        self.game = game
        self.ecs_entity = ecs_entity # 這是 ECS 中的實體ID
        
        # 必須呼叫所有父類的構造函式來初始化它們的屬性
        # 注意: 這裡假設它們的 __init__ 接受 game 和 ecs_entity
        MovementEntity.__init__(self, game, ecs_entity) 
        HealthEntity.__init__(self, game, ecs_entity)
        AttackEntity.__init__(self, game, ecs_entity)
        BuffableEntity.__init__(self, game, ecs_entity)
        
        # 技能相關屬性
        self.skill_chain: List[List[Skill]] = [[] for _ in range(4)] # 假設默認 4 條鏈
        self.current_skill_chain_idx = 0
        self.current_skill_idx = 0
        self.max_skill_chains = 4 
        
        # 能量和視野屬性
        self.max_skill_chain_length = 8  # Updated to 8 as per menu description
        self.base_max_energy = 100.0
        self.max_energy = self.base_max_energy
        self.energy = self.max_energy
        self.energy_regen_rate = 20.0
        self.original_energy_regen_rate = 20.0
        self.fog = True
        self.vision_radius = vision_radius  # In tiles
        self.mana = 0 # 貨幣單位
        
        # 確保第一條技能鏈至少存在
        if not self.skill_chain:
             self.skill_chain.append([])

    def update(self, dt: float, current_time: float) -> None:
        """
        更新邏輯：主要調用父類的 update，並處理非 ECS 屬性（如能量）。
        
        注意：在 ECS 架構中，Movement, Health, Attack 的處理應該由系統 (System) 完成。
        這些父類 update 方法可能負責非 Component 相關的邏輯 (如計時器、緩存更新)。
        """
        # Call parent classes' update methods in order
        MovementEntity.update(self, dt, current_time)
        HealthEntity.update(self, dt, current_time)
        AttackEntity.update(self, dt, current_time)
        BuffableEntity.update(self, dt, current_time)
        self.regenerate_energy(dt)

    def regenerate_energy(self, dt: float) -> None:
        """Regenerate energy over time."""
        if self.energy < self.max_energy:
            self.energy += self.energy_regen_rate * dt
            if self.energy > self.max_energy:
                self.energy = self.max_energy
    
    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """
        繪製玩家實體。在 ECS 架構中，通常由 RenderSystem 負責。
        這裡的 draw 方法是為了舊的架構兼容性而保留。
        
        注意：這裡的 self.x, self.y, self.w, self.h 必須在父類的 __init__ 或 update 
        中從 ECS 的 Position/Renderable Component 中同步過來，否則它們將是未定義的。
        """
        # 這裡假設 self.x/y/w/h 已經在父類中被定義和同步
        if hasattr(self, 'w') and hasattr(self, 'h'):
             pygame.draw.rect(screen, (255, 255, 255), 
                              (self.x - camera_offset[0] -self.w//2, self.y - camera_offset[1] -self.h//2, self.w, self.h))
        # 如果沒有 self.w/h，則假設一個默認值
        else:
             # 為防止 AttributeError，這裡只繪製一個點或默認矩形 (需要手動處理 w/h 的同步)
             pass 

    def add_skill_to_chain(self, skill: Skill, chain_idx: int = 0) -> bool:
        """Add a skill to the specified skill chain if space is available."""
        if chain_idx >= self.max_skill_chains:
            print(f"Invalid chain index: {chain_idx}. Maximum is {self.max_skill_chains - 1}.")
            return False
        # 確保技能鏈列表的長度足夠
        while len(self.skill_chain) <= chain_idx:
            self.skill_chain.append([])
            
        if len(self.skill_chain[chain_idx]) < self.max_skill_chain_length:
            self.skill_chain[chain_idx].append(skill)
            return True
        print(f"Skill chain {chain_idx} is full (max length: {self.max_skill_chain_length}).")
        return False

    def switch_skill_chain(self, chain_idx: int) -> None:
        """Switch to the specified skill chain."""
        if 0 <= chain_idx < len(self.skill_chain):
            self.current_skill_chain_idx = chain_idx
            self.current_skill_idx = 0
            # 確保打印時顯示的是用戶友好的索引 (從 1 開始)
            print(f"Switched to skill chain {chain_idx + 1}/{len(self.skill_chain)}")
        else:
            print(f"Invalid chain index: {chain_idx}. Available chains: {len(self.skill_chain)}")

    def switch_skill(self, index: int) -> None:
        """Switch to the specified skill in the current skill chain."""
        if 0 <= self.current_skill_chain_idx < len(self.skill_chain):
            current_chain = self.skill_chain[self.current_skill_chain_idx]
            if 0 <= index < len(current_chain):
                self.current_skill_idx = index
                print(f"Switched to skill: {current_chain[self.current_skill_idx].name}")
            else:
                print(f"Invalid skill index: {index}. Available skills: {len(current_chain)}")

    def activate_skill(self, direction: Tuple[float, float], current_time: float, target_position: Tuple[float, float]) -> None:
        """Activate the current skill in the active skill chain."""
        # 檢查當前技能鏈是否為空
        if not self.skill_chain[self.current_skill_chain_idx]:
            print("No skills available in current chain.")
            return
            
        skill = self.skill_chain[self.current_skill_chain_idx][self.current_skill_idx]
        if self.energy < skill.energy_cost:
            print(f"Not enough energy for {skill.name} (required: {skill.energy_cost}, available: {self.energy})")
            return

        skill.activate(self, self.game, target_position, current_time)
        self.energy -= skill.energy_cost
        assert self.energy >= 0, "Energy should not be negative after skill activation"
        
        # Auto-switch to next skill in chain
        current_chain = self.skill_chain[self.current_skill_chain_idx]
        if len(current_chain) > 1:
            self.current_skill_idx = (self.current_skill_idx + 1) % len(current_chain)
            print(f"Switched to next skill: {current_chain[self.current_skill_idx].name}")

    def canfire(self) -> bool:
        """Check if the player can activate a skill."""
        # 這裡假設 self.can_attack 屬性由 AttackEntity 父類提供
        return self.can_attack