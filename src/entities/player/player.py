# src/entities/player.py (重構後的 Player 門面類別)
from typing import List, Tuple, Optional, Dict
import pygame
import esper # 新增 esper 依賴以讀寫 ECS World
# 假設所有 ECS Component 和 Skill 類別已從正確路徑導入
from ...ecs.components import PlayerComponent, Combat, Position, Velocity, Health, Defense, Renderable
from ...skills.skill import Skill
import math
# 為了簡化，假設其他組件的類別名稱如 Combat, Position, Velocity 
# 可以直接被 esper 的 component_for_entity 找到

class Player:
    """
    玩家實體門面 (Facade)。
    它不包含任何狀態，而是透過 ecs_entity ID 讀寫 ECS Component 的數據，
    並處理高層次的遊戲邏輯（如技能管理）。
    """
    def __init__(self, game, ecs_entity: int):
        # 核心引用
        self.game = game
        self.ecs_entity = ecs_entity # ECS 中的實體 ID
        self.world = game.world      # 假設 game 實例持有 esper.World

        # 移除所有父類構造函式的調用
        # 狀態已全部轉移到 ECS Component 中，並由 Entity Factory 負責初始化。
        
        # 確保 PlayerComponent 已經附加，否則 Facade 無法工作
        if not self.world.has_component(self.ecs_entity, PlayerComponent):
            raise ValueError("PlayerComponent must be attached to the ECS entity upon creation.")

    # --- 輔助方法：獲取核心組件 ---

    def _get_player_comp(self) -> 'PlayerComponent':
        """獲取 PlayerComponent (包含技能鏈和能量狀態)"""
        return self.world.component_for_entity(self.ecs_entity, PlayerComponent)

    def _get_combat_comp(self) -> 'Combat':
        """獲取 Combat 組件 (用於檢查 can_attack)"""
        return self.world.component_for_entity(self.ecs_entity, Combat) 

    def _get_position_comp(self) -> 'Position':
        """獲取 Position 組件 (用於技能起點計算)"""
        return self.world.component_for_entity(self.ecs_entity, Position)
    
    def _get_health_comp(self) -> 'Health':
        """獲取 Health 組件 (用於生命值管理)"""
        return self.world.component_for_entity(self.ecs_entity, Health)
    def _get_defense_comp(self) -> 'Defense':
        """獲取 Defense 組件 (用於防禦值管理)"""
        return self.world.component_for_entity(self.ecs_entity, Defense)
    def _get_velocity_comp(self) -> 'Velocity':
        """獲取 Velocity 組件 (用於速度管理)"""
        return self.world.component_for_entity(self.ecs_entity, Velocity)
    def _get_renderable_comp(self):
        """獲取 Renderable 組件 (用於寬高管理)"""
        return self.world.component_for_entity(self.ecs_entity, Renderable)
    # --- 邏輯方法重構 ---

    def update(self, dt: float, current_time: float) -> None:
        """
        更新邏輯：在 ECS 架構中，Facade 的 update 應保持精簡。
        Movement, Health, Attack 的處理應完全由系統 (System) 完成。
        能量再生邏輯將被移至 EnergySystem。
        """
        # 移除父類更新調用：MovementEntity.update(), HealthEntity.update(), etc.
        # 移除能量再生調用：self.regenerate_energy(dt)
        pass # Facade 幾乎不做連續更新，依賴 System

    # 移除 regenerate_energy 方法，功能移至 EnergySystem

    def draw(self, screen: pygame.Surface, camera_offset: List[float]) -> None:
        """移除 draw 方法。繪製應完全由 RenderSystem 負責。"""
        pass

    # --- 技能管理方法 (修改 PlayerComponent 數據) ---

    def add_skill_to_chain(self, skill: 'Skill', chain_idx: int = 0) -> bool:
        """Add a skill to the specified skill chain if space is available."""
        comp = self._get_player_comp() # 讀取 PlayerComponent
        
        # 邏輯保持不變，但操作的是 comp.skill_chain, comp.max_skill_chains 等屬性
        if chain_idx >= comp.max_skill_chains:
            # ... print statements ...
            return False
        
        while len(comp.skill_chain) <= chain_idx:
            comp.skill_chain.append([])
            
        if len(comp.skill_chain[chain_idx]) < comp.max_skill_chain_length:
            comp.skill_chain[chain_idx].append(skill)
            return True
        # ... print statements ...
        return False

    def switch_skill_chain(self, chain_idx: int) -> None:
        """Switch to the specified skill chain."""
        comp = self._get_player_comp()
        
        if 0 <= chain_idx < len(comp.skill_chain):
            comp.current_skill_chain_idx = chain_idx
            comp.current_skill_idx = 0
            # ... print statements ...
        # ... else print statements ...

    def switch_skill(self, index: int) -> None:
        """Switch to the specified skill in the current skill chain."""
        comp = self._get_player_comp()
        
        if 0 <= comp.current_skill_chain_idx < len(comp.skill_chain):
            current_chain = comp.skill_chain[comp.current_skill_chain_idx]
            if 0 <= index < len(current_chain):
                comp.current_skill_idx = index
                # ... print statements ...
            # ... else print statements ...

    def activate_skill(self, direction: Tuple[float, float], current_time: float, target_position: Tuple[float, float]) -> None:
        """Activate the current skill in the active skill chain."""
        comp = self._get_player_comp()

        # 檢查當前技能鏈是否為空
        if not comp.skill_chain[comp.current_skill_chain_idx]:
            # ... print statements ...
            return
            
        skill = comp.skill_chain[comp.current_skill_chain_idx][comp.current_skill_idx]
        
        # 檢查能量
        if comp.energy < skill.energy_cost:
            # ... print statements ...
            return

        # 核心技能調用 (保持不變)
        # skill.activate 內部應使用 ECS 工廠創建子彈實體 (已在上一輪重構)
        skill.activate(self, self.game, target_position, current_time) 
        
        # 消耗能量 (直接修改 Component)
        comp.energy -= skill.energy_cost
        comp.energy = max(0.0, comp.energy) # 確保能量不為負

        # Auto-switch to next skill in chain
        current_chain = comp.skill_chain[comp.current_skill_chain_idx]
        if len(current_chain) > 1:
            comp.current_skill_idx = (comp.current_skill_idx + 1) % len(current_chain)
            # ... print statements ...
    
    def canfire(self) -> bool:
        """Check if the player can activate a skill. 從 Combat 組件獲取狀態。"""
        # 假設 Combat 組件存在
        try:
            return self._get_combat_comp().can_attack
        except esper.NoSuchComponent:
            # 如果 Combat 組件不存在，則默認允許攻擊
            return True 

    # --- Property 訪問器 (用於取代直接屬性訪問) ---
    @property
    def energy(self) -> float:
        return self._get_player_comp().energy
        
    @property
    def max_energy(self) -> float:
        return self._get_player_comp().max_energy
    
    # 為了兼容舊的技能邏輯，可能需要訪問 x, y, w, h
    @property
    def x(self) -> float:
        return self._get_position_comp().x
        
    @property
    def y(self) -> float:
        return self._get_position_comp().y
    
    @property
    def w(self) -> int:
        # 假設 Renderable 組件存在
        return self._get_renderable_comp().w

    @property
    def h(self) -> int:
        # 假設 Renderable 組件存在
        return self._get_renderable_comp().h

    @property
    def damage_to_element(self) -> Dict[str, float]:
        # 假設 Combat 組件存在
        return self._get_combat_comp().damage_to_element

    @property
    def atk_element(self) -> str:
        # 假設 Combat 組件存在
        return self._get_combat_comp().atk_element
    
    @property
    def speed(self) -> float:
        return self.world.component_for_entity(self.ecs_entity, Velocity).speed

    @max_energy.setter
    def max_energy(self, value: float) -> None:
        self._get_player_comp().max_energy = value

    # --- Health / Shield Properties (Health Component) ---
    @property
    def current_hp(self) -> int: return self._get_health_comp().current_hp
    @current_hp.setter
    def current_hp(self, value: int) -> None: self._get_health_comp().current_hp = value
    
    @property
    def max_hp(self) -> int: return self._get_health_comp().max_hp
    @max_hp.setter
    def max_hp(self, value: int) -> None: self._get_health_comp().max_hp = value
    
    @property
    def base_max_hp(self) -> int: return self._get_health_comp().base_max_hp
    @base_max_hp.setter
    def base_max_hp(self, value: int) -> None: self._get_health_comp().base_max_hp = value

    @property
    def max_shield(self) -> int: return self._get_health_comp().max_shield
    @max_shield.setter
    def max_shield(self, value: int) -> None: self._get_health_comp().max_shield = value
    
    # --- Defense Properties (Defense Component) ---
    @property
    def defense(self) -> int: return self._get_defense_comp().defense
    @defense.setter
    def defense(self, value: int) -> None: self._get_defense_comp().defense = value
    
    # --- Combat Properties (Combat Component) ---
    @property
    def damage(self) -> int: return self._get_combat_comp().damage
    @damage.setter
    def damage(self, value: int) -> None: self._get_combat_comp().damage = value
    
    # --- Movement/Velocity Properties (Velocity/PlayerComponent) ---
    @property
    def speed(self) -> float: return self._get_velocity_comp().speed
    @speed.setter
    def speed(self, value: float) -> None: self._get_velocity_comp().speed = value
    
    @property
    def _base_max_speed(self) -> float: return self._get_player_comp().base_max_speed
    @_base_max_speed.setter
    def _base_max_speed(self, value: float) -> None: self._get_player_comp().base_max_speed = value

    # --- Energy Properties (PlayerComponent) ---
    @property
    def energy_regen_rate(self) -> float: return self._get_player_comp().energy_regen_rate
    @energy_regen_rate.setter
    def energy_regen_rate(self, value: float) -> None: self._get_player_comp().energy_regen_rate = value

    @property
    def base_energy_regen_rate(self) -> float: return self._get_player_comp().base_energy_regen_rate
    @base_energy_regen_rate.setter
    def base_energy_regen_rate(self, value: float) -> None: self._get_player_comp().base_energy_regen_rate = value

    # --- Element/Amplifier/Skill Properties (PlayerComponent) ---
    @property
    def elements(self) -> set: return self._get_player_comp().elements
    @elements.setter
    def elements(self, value: set) -> None: self._get_player_comp().elements = value

    @property
    def amplifiers(self) -> Dict: return self._get_player_comp().amplifiers
    @amplifiers.setter
    def amplifiers(self, value: Dict) -> None: self._get_player_comp().amplifiers = value
    
    @property
    def max_skill_chains(self) -> int: return self._get_player_comp().max_skill_chains
    @property
    def skill_chain(self) -> List: return self._get_player_comp().skill_chain
    @skill_chain.setter
    def skill_chain(self, value: List) -> None: self._get_player_comp().skill_chain = value
    
    @property
    def current_skill_chain_idx(self) -> int: return self._get_player_comp().current_skill_chain_idx
    @current_skill_chain_idx.setter
    def current_skill_chain_idx(self, value: int) -> None: self._get_player_comp().current_skill_chain_idx = value

    @property
    def current_skill_idx(self) -> int: return self._get_player_comp().current_skill_idx
    @current_skill_idx.setter
    def current_skill_idx(self, value: int) -> None: self._get_player_comp().current_skill_idx = value
    
    # 視野屬性 (兼容 RenderManager)
    @property
    def fog(self) -> bool: return self._get_player_comp().fog 
    @property
    def vision_radius(self) -> int: return self._get_player_comp().vision_radius

    @property
    def mana(self) -> int: return self._get_player_comp().mana
    @mana.setter
    def mana(self, value: int) -> None: self._get_player_comp().mana = value
    
    @property
    def current_shield(self) -> int: return self._get_player_comp().current_shield
    @current_shield.setter
    def current_shield(self, value: int) -> None: self._get_player_comp().current_shield = value
    
    @property
    def max_shield(self) -> int: return self._get_player_comp().max_shield
    @max_shield.setter
    def max_shield(self, value: int) -> None: self._get_player_comp().max_shield = value
    
    @property
    def displacement(self) -> Tuple[int, int]:
        """讀取 Velocity 組件，並反推回 EventManager 期望的 (-1, 0, 1) 標準化方向向量。"""
        vel_comp = self._get_velocity_comp()
        dx = 0
        if vel_comp.x < 0: dx = -1
        elif vel_comp.x > 0: dx = 1
        dy = 0
        if vel_comp.y < 0: dy = -1
        elif vel_comp.y > 0: dy = 1
        return (dx, dy)
    
    @displacement.setter
    def displacement(self, value: Tuple[int, int]) -> None:
        """設定標準化移動方向，並計算出最終的速度向量 (speed * normalized_direction) 寫入 Velocity 組件。"""
        dx, dy = value
        vel_comp = self._get_velocity_comp()
        speed = vel_comp.speed
        
        magnitude = math.sqrt(dx**2 + dy**2)
        
        if magnitude > 0:
            # 計算單位方向向量並乘上速度，以避免對角線加速
            normalized_dx = dx / magnitude
            normalized_dy = dy / magnitude
            vel_comp.x = normalized_dx * speed
            vel_comp.y = normalized_dy * speed
        else:
            vel_comp.x = 0
            vel_comp.y = 0