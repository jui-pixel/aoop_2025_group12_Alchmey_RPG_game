# src/ecs/ai.py
from typing import List, Dict, Callable
from abc import ABC, abstractmethod
from src.ecs.components import AI

# --- 行為樹節點 (BehaviorNode) ---
# 這些 Node 類無需大改，但它們現在操作的是 Context 對象
# 簽名: execute(self, context: EnemyContext, dt: float, current_time: float)

class BehaviorNode(ABC):
    @abstractmethod
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        pass

class ConditionNode(BehaviorNode):
    def __init__(self, condition: Callable[['EnemyContext', float], bool], on_success: BehaviorNode, on_fail: BehaviorNode = None):
        self.condition = condition
        self.on_success = on_success
        self.on_fail = on_fail
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        if self.condition(context, current_time):
            return self.on_success.execute(context, dt, current_time)
        elif self.on_fail:
            return self.on_fail.execute(context, dt, current_time)
        return False

# ... Sequence, Selector 保持與 ConditionNode 類似的簽名修改 ...

class Sequence(BehaviorNode):
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        for child in self.children:
            if not child.execute(context, dt, current_time):
                return False
        return True

class Selector(BehaviorNode):
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        for child in self.children:
            if child.execute(context, dt, current_time):
                return True
        return False

class PerformNextAction(BehaviorNode):
    def __init__(self, actions: Dict[str, 'Action']):
        self.actions = actions
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        ai_comp = context._get_comp(AI)
        if not ai_comp.action_list:
            return False
        
        action_id = ai_comp.action_list[0]
        action = self.actions.get(action_id)
        if not action:
            ai_comp.action_list.pop(0)
            return False
            
        if not action.started:
            action.start(context, current_time)
            action.started = True
            
        if action.update(context, dt, current_time):
            # print(f"{action.timer:.2f} seconds remaining for {action.action_id}")
            return True # Action is still running
            
        ai_comp.action_list.pop(0)
        # print(f"Action {action.action_id} finished. Remaining actions: {ai_comp.action_list}")
        action.reset()
        
        if len(ai_comp.action_list) >= 1:
            return True
        return False

class RefillActionList(BehaviorNode):
    def __init__(self, actions: Dict[str, 'Action'], default_combo: Callable[['EnemyContext'], List[str]]):
        self.actions = actions
        self.default_combo = default_combo
    
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        context._get_comp(AI).action_list = self.default_combo(context)
        # print(f"Refilled action list: {context._get_comp(AI).action_list}")
        return True

class IdleNode(BehaviorNode):
    def execute(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        context.set_current_action('idle')
        context.move(0, 0, dt)
        return True


# --- 動作定義 (Action) ---
# 所有的 Action.update/start 簽名也必須調整為接受 Context

class Action(ABC):
    # ... (init, reset 保持不變) ...
    def __init__(self, action_id: str, duration: float = 0.0):
        self.action_id = action_id
        self.duration = duration
        self.timer = 0.0
        self.started = False
    
    @abstractmethod
    def start(self, context: 'EnemyContext', current_time: float) -> None:
        pass
    
    @abstractmethod
    def update(self, context: 'EnemyContext', dt: float, current_time: float) -> bool:
        pass
    
    def reset(self) -> None:
        self.timer = 0.0
        self.started = False