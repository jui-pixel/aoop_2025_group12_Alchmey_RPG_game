from src.entities.buff import Buff

def paralysis_on_apply(entity: 'MovableEntity') -> None:
    """Handle paralysis effect application."""
    entity.paralysis = True  # Disable firing

def paralysis_on_remove(entity: 'MovableEntity') -> None:
    """Handle paralysis effect removal."""
    entity.paralysis = False  # Re-enable firing
    
def freeze_on_apply(entity: 'MovableEntity') -> None:
    """Handle freeze effect application."""
    entity.freeze = True
    
def freeze_on_remove(entity: 'MovableEntity') -> None:
    """Handle freeze effect removal."""
    entity.freeze = False
    
def petrochemical_on_apply(entity: 'MovableEntity') -> None:
    """Handle petrochemical effect application."""
    entity.petrochemical = True
    
def petrochemical_on_remove(entity: 'MovableEntity') -> None:
    """Handle petrochemical effect removal."""
    entity.petrochemical = False
    
ELEMENTBUFFLIBRARY = {
    "Dist" : Buff( 
        name="Dist",
        duration=5.0,  # 5 second duration
        effects={"speed_multiplier": 0.95},
        on_apply=None,
        on_remove=None
    ),
    
    "Humid" : Buff(
        name="Humid",
        duration=5.0,  # 5 second duration
        effects={},
        on_apply=None,
        on_remove=None
    ),
    
    "Cold" : Buff(
        name="Cold",
        duration=5.0,  # 5 second duration
        effects={"speed_multiplier": 0.5},
        on_apply=None,
        on_remove=None
    ),
    
    "Burn" : Buff(
        name="Burn",
        duration=3.0,  # 5 second duration
        effects={"health_regen_per_second": -10.0},
        on_apply=None,
        on_remove=None
    ),
    
    "Tear" : Buff(
        name="Tear",
        duration=5.0,  # 5 second duration
        effects={"health_regen_per_second": -10.0},
        on_apply=None,
        on_remove=None
    ),
    
    "Paralysis" : Buff(
        name="Paralysis",
        duration=5.0,  # 5 second duration
        effects={"speed_multiplier": 0.0},
        on_apply=paralysis_on_apply,
        on_remove=paralysis_on_remove
    ),
    
    "Entangled" : Buff(
        name="Entangled",
        duration=5.0,  # 5 second duration
        effects={"speed_multiplier": 0.0},
        on_apply=None,
        on_remove=None
    ),
    
    "Erosion" : Buff(
        name="Erosion",
        duration=5.0,  # 5 second duration
        effects={"health_regen_per_second": -10.0},
        on_apply=None,
        on_remove=None
    ),
    
    "Blind" : Buff(
        name="Blind",
        duration=5.0,  # 5 second duration
        effects={"vision_radius_multiplier": 0.1},
        on_apply=None,
        on_remove=None
    ),
    
    "Mud" : Buff(
        name="Mud",
        duration=5.0,  # 5 second duration
        effects={"speed_multiplier": 0.5},
        on_apply=None,
        on_remove=None
    ),
    
    "Freeze" : Buff(
        name="Freeze",
        duration=5.0,  # 5 second duration
        effects={"speed_multiplier": 0.0, "defense_multiplier": 2.0},
        on_apply=freeze_on_apply,
        on_remove=freeze_on_remove
    ),
    
    "Petrochemical" : Buff(
        name="Petrochemical",
        duration=5.0,  # 5 second duration
        effects={"speed_multiplier": 0.0, "defense_multiplier": 10.0},
        on_apply=petrochemical_on_apply,
        on_remove=petrochemical_on_remove
    ),
}