import esper
import pygame
import math
from .components import Position, Velocity, Renderable, Input, Health, Defense, Combat, Buffs, AI, Collider, PlayerComponent, Tag
from src.ecs.ai import EnemyContext
from src.core.config import TILE_SIZE, PASSABLE_TILES, SCREEN_WIDTH, SCREEN_HEIGHT
from src.entities.ecs_factory import create_damage_text_entity, create_dungeon_portal_npc

class MovementSystem(esper.Processor):
    def process(self, *args, **kwargs):
        dt = args[0] if args else 0.0
        # Get dungeon from game instance attached to world
        game = getattr( esper, 'game', None)
        dungeon = game.dungeon_manager.get_dungeon() if game else None
        
        for ent, (pos, vel) in  esper.get_components(Position, Velocity):
            if vel.x == 0 and vel.y == 0:
                continue
            
            # Get Collider if exists, else default
            collider =  esper.try_component(ent, Collider)
            pass_wall = collider.pass_wall if collider else False
            destroy_on_collision = collider.destroy_on_collision if collider else False
            w = collider.w if collider else 32
            h = collider.h if collider else 32
            
            # Calculate potential new position
            new_x = pos.x + vel.x * dt
            new_y = pos.y + vel.y * dt
            
            if not pass_wall and dungeon:
                # Check bounds and walls
                tile_x, tile_y = int(new_x // TILE_SIZE), int(new_y // TILE_SIZE)
                x_valid = 0 <= tile_x < dungeon.grid_width
                y_valid = 0 <= tile_y < dungeon.grid_height
                
                if x_valid and y_valid:
                    tile = dungeon.dungeon_tiles[tile_y][tile_x]
                    if tile in PASSABLE_TILES:
                        pos.x = new_x
                        pos.y = new_y
                    else:
                        if destroy_on_collision:
                            # Mark entity for deletion (to be handled by a cleanup system)
                             esper.delete_entity(ent)
                             continue
                        # Sliding logic
                        tile_x_curr = int(pos.x // TILE_SIZE)
                        tile_y_new = int(new_y // TILE_SIZE)
                        tile_x_new = int(new_x // TILE_SIZE)
                        tile_y_curr = int(pos.y // TILE_SIZE)
                        
                        x_allowed = False
                        y_allowed = False
                        
                        # Check if we can move in X direction (keeping Y same)
                        if 0 <= tile_x_new < dungeon.grid_width and 0 <= tile_y_curr < dungeon.grid_height:
                             if dungeon.dungeon_tiles[tile_y_curr][tile_x_new] in PASSABLE_TILES:
                                 x_allowed = True
                        
                        # Check if we can move in Y direction (keeping X same)
                        if 0 <= tile_x_curr < dungeon.grid_width and 0 <= tile_y_new < dungeon.grid_height:
                             if dungeon.dungeon_tiles[tile_y_new][tile_x_curr] in PASSABLE_TILES:
                                 y_allowed = True
                                 
                        if x_allowed:
                            pos.x = new_x
                            vel.y = 0
                        elif y_allowed:
                            pos.y = new_y
                            vel.x = 0
                        else:
                            vel.x = 0
                            vel.y = 0
                else:
                    vel.x = 0
                    vel.y = 0
            else:
                pos.x = new_x
                pos.y = new_y

class RenderSystem(esper.Processor):
    def process(self, *args, **kwargs):
        game = getattr( esper, 'game', None)
        if not game:
            return
        
        screen = game.screen
        camera_offset = game.render_manager.camera_offset
        
        # Collect and sort renderables
        render_list = []
        for ent, (pos, rend) in  esper.get_components(Position, Renderable):
            if not rend.visible:
                continue
            render_list.append((pos, rend, ent))
            
        # Sort by layer then Y position for depth
        render_list.sort(key=lambda x: (x[1].layer, x[0].y))
        
        for pos, rend, ent in render_list:
            screen_x = pos.x - camera_offset[0] - rend.w // 2
            screen_y = pos.y - camera_offset[1] - rend.h // 2
            
            # Culling: Don't draw if off screen
            if (screen_x + rend.w < 0 or screen_x > SCREEN_WIDTH or 
                screen_y + rend.h < 0 or screen_y > SCREEN_HEIGHT):
                continue

            if rend.image:
                screen.blit(rend.image, (screen_x, screen_y))
            else:
                pygame.draw.rect(screen, rend.color, (screen_x, screen_y, rend.w, rend.h))
                
            # Draw Health Bar if entity has Health component (skip bosses)
            if  esper.has_component(ent, Health):
                # Check if this is a boss entity by BossComponent
                from src.ecs.components import BossComponent
                is_boss = esper.has_component(ent, BossComponent)
                
                # Skip drawing health bar above boss (will be drawn at top of screen)
                if not is_boss:
                    health =  esper.component_for_entity(ent, Health)
                    self.draw_health_bar(screen, pos, health, rend, camera_offset)

    def draw_health_bar(self, screen, pos, health, rend, camera_offset):
        if health.max_hp <= 0:
            return
            
        bar_width = 40
        bar_height = 6
        health_ratio = health.current_hp / health.max_hp
        shield_ratio = health.current_shield / health.max_shield if health.max_shield > 0 else 0.0
        
        bar_x = pos.x - camera_offset[0] - bar_width // 2
        bar_y = pos.y - camera_offset[1] - rend.h // 2 - 10
        
        # Background
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # Health
        health_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, health_width, bar_height))
        # Shield
        if shield_ratio > 0:
            shield_width = int(bar_width * shield_ratio)
            pygame.draw.rect(screen, (0, 0, 255), (bar_x + health_width, bar_y, shield_width, bar_height))
        # Border
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 1)

class InputSystem(esper.Processor):
    def process(self, *args, **kwargs):
        keys = pygame.key.get_pressed()
        
        for ent, (inp, vel) in  esper.get_components(Input, Velocity):
            if  esper.has_component(ent, PlayerComponent):
                # Reset velocity intent
                vel.x = 0
                vel.y = 0
                
                # WASD Movement
                if keys[pygame.K_w]:
                    vel.y = -vel.speed
                if keys[pygame.K_s]:
                    vel.y = vel.speed
                if keys[pygame.K_a]:
                    vel.x = -vel.speed
                if keys[pygame.K_d]:
                    vel.x = vel.speed
                    
                # Normalize diagonal movement
                if vel.x != 0 and vel.y != 0:
                    factor = 1.0 / math.sqrt(2)
                    vel.x *= factor
                    vel.y *= factor
                

class HealthSystem(esper.Processor):
    def process(self, *args, **kwargs):
        game = getattr( esper, 'game', None)
        
        # Check for dead entities and handle death
        for ent, health in  esper.get_component(Health):
            self.heal(ent, int(health.regen_rate * args[0] if args else 0.0))
            if health.current_hp <= 0:
                self._handle_death(ent, game)
    
    def take_damage(self, entity, factor=1.0, element="untyped", base_damage=0,
                   max_hp_percentage_damage=0, current_hp_percentage_damage=0,
                   lose_hp_percentage_damage=0, cause_death=True):
        """
        Apply damage to an entity with Health and Defense components.
        Returns: (killed: bool, actual_damage: int)
        """
        if not  esper.has_component(entity, Health):
            return False, 0
        
        health =  esper.component_for_entity(entity, Health)
        defense =  esper.try_component(entity, Defense)
        
        # Check invulnerability
        if defense and defense.invulnerable:
            self._create_damage_text(entity, "Immune")
            return False, 0
        
        # Check dodge
        if defense and defense.dodge_rate > 0:
            import random
            if random.random() < defense.dodge_rate:
                self._create_damage_text(entity, "Miss")
                return False, 0
        
        # Calculate affinity multiplier
        affinity_multiplier = self._calculate_affinity_multiplier(element, defense.element if defense else "untyped")
        
        # Add percentage-based damage
        if max_hp_percentage_damage > 0:
            base_damage += health.max_hp * max_hp_percentage_damage / 100
        if current_hp_percentage_damage > 0:
            base_damage += health.current_hp * current_hp_percentage_damage / 100
        if lose_hp_percentage_damage > 0:
            base_damage += (health.max_hp - health.current_hp) * lose_hp_percentage_damage / 100
        
        # Calculate resistance
        resistance = 0.0
        if defense and defense.resistances:
            resistance = defense.resistances.get(element, 0.0)
        
        # Calculate final damage
        defense_value = defense.defense if defense else 0
        final_damage = max(1, int(base_damage * affinity_multiplier * (1.0 - resistance) * factor - defense_value))
        
        # Apply to shield first
        if health.current_shield > 0:
            shield_damage = min(final_damage, health.current_shield)
            health.current_shield -= shield_damage
            final_damage -= shield_damage
        
        # Apply to health
        if final_damage > 0:
            remain_hp = health.current_hp - final_damage
            if remain_hp <= 0 and not cause_death:
                final_damage = health.current_hp - 1
                health.current_hp = 1
            else:
                health.current_hp = max(0, remain_hp)
        
        killed = health.current_hp <= 0

        self._create_damage_text(entity, final_damage)
        
        return killed, final_damage
    
    def heal(self, entity, amount):
        """Heal an entity by the specified amount."""
        if not  esper.has_component(entity, Health):
            return
        
        health =  esper.component_for_entity(entity, Health)
        health.current_hp = min(health.max_hp, health.current_hp + amount)
    
    def add_shield(self, entity, amount):
        """Add shield to an entity by the specified amount."""
        if not  esper.has_component(entity, Health):
            return
        
        health =  esper.component_for_entity(entity, Health)
        health.current_shield = min(health.max_shield, health.current_shield + amount)
    
    def set_max_hp(self, entity, new_max_hp):
        """Set max HP and scale current HP proportionally."""
        if not  esper.has_component(entity, Health):
            return
        
        health =  esper.component_for_entity(entity, Health)
        old_max = health.max_hp
        health.max_hp = max(0, new_max_hp)
        
        if old_max > 0:
            health.current_hp = int(health.current_hp * new_max_hp / old_max)
        else:
            health.current_hp = new_max_hp
    
    def set_max_shield(self, entity, new_max_shield):
        """Set max shield and clamp current shield."""
        if not  esper.has_component(entity, Health):
            return
        
        health =  esper.component_for_entity(entity, Health)
        health.max_shield = max(0, new_max_shield)
        health.current_shield = min(health.max_shield, health.current_shield)
    
    def _calculate_affinity_multiplier(self, attack_element, defend_element):
        """Calculate elemental affinity multiplier based on WEAKTABLE."""
        if attack_element == 'untyped' or defend_element == 'untyped':
            return 1.0
        
        from src.utils.elements import WEAKTABLE
        
        # Check WEAKTABLE for direct weakness
        for attacker, defender in WEAKTABLE:
            if attack_element == attacker and defend_element == defender:
                return 1.5  # Weakness: attacker deals more damage
            elif attack_element == defender and defend_element == attacker:
                return 0.5  # Resistance: defender takes less damage
        
        return 1.0  # Neutral
    
    def _create_damage_text(self, entity, text):
        """Create damage text at entity position."""
        game = getattr( esper, 'game', None)
        if not game or not  esper.has_component(entity, Position):
            return
        
        pos =  esper.component_for_entity(entity, Position)
        
        create_damage_text_entity(
            world=esper,
            x=pos.x,
            y=pos.y,
            damage=text,
            color=(255, 0, 0),
            duration=1.0
        )
    
    def _handle_death(self, entity, game):
        """Handle entity death."""
        print(f"Entity {entity} died!")
        if esper.has_component(entity, PlayerComponent):
            if game:
                game.on_player_death()
        else:
            # Check for Boss component
            from src.ecs.components import BossComponent
            if esper.has_component(entity, BossComponent):
                boss_comp = esper.component_for_entity(entity, BossComponent)
                print(f"Boss {boss_comp.boss_name} died! Spawning portal...")
                if game and esper.has_component(entity, Position):
                    pos = esper.component_for_entity(entity, Position)
                    
                    # Get portal config from DungeonManager
                    dungeon_config = game.dungeon_manager.current_dungeon_config
                    portal_data = dungeon_config.get('portal') if dungeon_config else None
                    
                    available_dungeons = []
                    if portal_data:
                         available_dungeons = [{
                            'name': portal_data.get('name', 'Unknown Portal'),
                            'level': 1,
                            'dungeon_id': portal_data.get('target_dungeon_id', 1)
                        }]
                    else:
                         available_dungeons = [{'name': 'Return to Start', 'level': 1, 'dungeon_id': 1}]

                    create_dungeon_portal_npc(
                        esper, x=pos.x, y=pos.y, 
                        available_dungeons=available_dungeons, 
                        game=game
                    )

            esper.delete_entity(entity)

class BuffSystem(esper.Processor):
    def __init__(self):
        super().__init__()
        # Buff synthesis rules
        self.synthesis_rules = {
            ('Burn', 'Humid'): 'Fog',
            ('Burn', 'Mud'): 'Petrochemical',
            ('Burn', 'Freeze'): 'Vulnerable',
            ('Burn', 'Entangled'): 'Backdraft',
            ('Humid', 'Cold'): 'Freeze',
            ('Humid', 'Paralysis'): 'Taser',
            ('Humid', 'Dist'): 'Mud',
            ('Humid', 'Tear'): 'Bleeding',
            ('Disorder', 'Dist'): 'Sandstorm',
            ('Blind', 'Erosion'): 'Annihilation',
            ('Mud', 'Humid'): 'Enpty',
            ('Fog', 'Disorder'): 'Enpty',
            ('Entangled', 'Disorder'): 'Enpty',
            ('Tear', 'Dist'): 'Enpty',
            ('Tear', 'Entangled'): 'Enpty',
            ('Paralysis', 'Dist'): 'Enpty',
        }
    
    def process(self, *args, **kwargs):
        dt = args[0] if args else 0.0
        
        game = getattr( esper, 'game', None)
        
        for ent, buffs in  esper.get_component(Buffs):
            if not buffs.active_buffs:
                continue
            
            # 1. Update buff durations and apply effects
            for buff in buffs.active_buffs[:]:
                buff.duration -= dt
                if buff.duration <= 0:
                    # Buff expired, remove it
                    self._remove_buff(ent, buff, buffs, game)
                else:
                    # Apply effect per second
                    self._apply_buff_effects(ent, buff, dt, game)
            
            # 2. Synthesize buffs
            self._synthesize_buffs(ent, buffs, game)
            
            # 3. Update modifiers based on active buffs
            self._update_modifiers(ent, buffs, game)
    
    def _apply_buff_effects(self, entity, buff, dt, game):
        """Apply ongoing effects of a buff."""
        if buff.effect_per_second:
            buff.effect_time += dt
            if buff.effect_time - buff.last_effect_time >= 1.0:
                # Create entity wrapper for callback
                wrapper = EntityWrapper(entity,  esper, game)
                buff.effect_per_second(wrapper)
                buff.last_effect_time = buff.effect_time
        
        # Apply health regen
        health_regen = buff.multipliers.get('health_regen_per_second', 0.0)
        if health_regen != 0 and  esper.has_component(entity, Health):
            health_system = game.ecs_world.get_processor(HealthSystem) if game else None
            if health_system:
                if health_regen > 0:
                    health_system.heal(entity, int(health_regen * dt))
                else:
                    # Negative regen = damage over time
                    defense =  esper.try_component(entity, Defense)
                    if not (defense and defense.invulnerable):
                        health_system.take_damage(entity, base_damage=int(abs(health_regen) * dt), cause_death=False)
    
    def _remove_buff(self, entity, buff, buffs_comp, game):
        """Remove a buff and trigger on_remove callback."""
        buffs_comp.active_buffs.remove(buff)
        
        if buff.on_remove:
            wrapper = EntityWrapper(entity,  esper, game)
            buff.on_remove(wrapper)
        
        print(f"Removed buff: {buff.name} from entity {entity}")
    
    def _synthesize_buffs(self, entity, buffs_comp, game):
        """Check for and apply buff synthesis rules."""
        buff_names = [buff.name for buff in buffs_comp.active_buffs]
        
        for (buff1_name, buff2_name), result_name in self.synthesis_rules.items():
            if buff1_name in buff_names and buff2_name in buff_names:
                # Find the buff objects
                buff1 = next((b for b in buffs_comp.active_buffs if b.name == buff1_name), None)
                buff2 = next((b for b in buffs_comp.active_buffs if b.name == buff2_name), None)
                
                if buff1 and buff2:
                    # Remove both buffs
                    self._remove_buff(entity, buff1, buffs_comp, game)
                    self._remove_buff(entity, buff2, buffs_comp, game)
                    
                    # Add synthesized buff
                    from src.buffs.element_buff import ELEMENTAL_BUFFS
                    if result_name in ELEMENTAL_BUFFS:
                        new_buff = ELEMENTAL_BUFFS[result_name].deepcopy()
                        buffs_comp.active_buffs.append(new_buff)
                        
                        # Trigger on_apply callback
                        if new_buff.on_apply:
                            wrapper = EntityWrapper(entity,  esper, game)
                            new_buff.on_apply(wrapper)
                        
                        print(f"Synthesized {buff1_name} + {buff2_name} = {result_name} on entity {entity}")
                    
                    # Only synthesize once per frame
                    break
    
    def _update_modifiers(self, entity, buffs_comp, game):
        """Recalculate all modifiers based on active buffs."""
        # Reset modifiers
        multiplier_keys = [k for k in buffs_comp.modifiers if 'resistance' not in k.lower() and 'add' not in k.lower()]
        additive_keys = [k for k in buffs_comp.modifiers if 'resistance' in k.lower() or 'add' in k.lower()]
        
        for key in multiplier_keys:
            buffs_comp.modifiers[key] = 1.0
        for key in additive_keys:
            buffs_comp.modifiers[key] = 0.0
        
        # Accumulate modifiers from all active buffs
        for buff in buffs_comp.active_buffs:
            for modifier_name, value in buff.multipliers.items():
                if modifier_name not in buffs_comp.modifiers:
                    # Initialize new modifier
                    if 'resistance' in modifier_name or 'add' in modifier_name:
                        buffs_comp.modifiers[modifier_name] = 0.0
                    else:
                        buffs_comp.modifiers[modifier_name] = 1.0
                
                # Apply modifier
                if 'resistance' in modifier_name or 'add' in modifier_name:
                    buffs_comp.modifiers[modifier_name] += value
                else:
                    buffs_comp.modifiers[modifier_name] *= value

class EntityWrapper:
    """Wrapper class to provide entity-like interface for ECS entities."""
    def __init__(self, ecs_entity, esper, game):
        self.ecs_entity = ecs_entity
        self.game = game
        self.id = ecs_entity
    
    @property
    def x(self):
        if  esper.has_component(self.ecs_entity, Position):
            return  esper.component_for_entity(self.ecs_entity, Position).x
        return 0
    
    @property
    def y(self):
        if  esper.has_component(self.ecs_entity, Position):
            return  esper.component_for_entity(self.ecs_entity, Position).y
        return 0
    
    @property
    def w(self):
        if  esper.has_component(self.ecs_entity, Collider):
            return  esper.component_for_entity(self.ecs_entity, Collider).w
        elif  esper.has_component(self.ecs_entity, Renderable):
            return  esper.component_for_entity(self.ecs_entity, Renderable).w
        return 32
    
    @property
    def h(self):
        if  esper.has_component(self.ecs_entity, Collider):
            return  esper.component_for_entity(self.ecs_entity, Collider).h
        elif  esper.has_component(self.ecs_entity, Renderable):
            return  esper.component_for_entity(self.ecs_entity, Renderable).h
        return 32
    
    @property
    def buffs(self):
        if  esper.has_component(self.ecs_entity, Buffs):
            return  esper.component_for_entity(self.ecs_entity, Buffs).active_buffs
        return []
    
    @property
    def current_hp(self):
        if  esper.has_component(self.ecs_entity, Health):
            return  esper.component_for_entity(self.ecs_entity, Health).current_hp
        return 0
    
    @property
    def max_hp(self):
        if  esper.has_component(self.ecs_entity, Health):
            return  esper.component_for_entity(self.ecs_entity, Health).max_hp
        return 0
    
    def take_damage(self, **kwargs):
        """Delegate to HealthSystem."""
        if self.game:
            health_system = esper.get_processor(HealthSystem)
            if health_system:
                return health_system.take_damage(self.ecs_entity, **kwargs)
        return False, 0
    
    def heal(self, amount):
        """Delegate to HealthSystem."""
        if self.game:
            health_system = self.game.ecs_world.get_processor(HealthSystem)
            if health_system:
                health_system.heal(self.ecs_entity, amount)
    
    def add_buff(self, buff):
        """Add a buff to this entity."""
        if  esper.has_component(self.ecs_entity, Buffs):
            buffs_comp =  esper.component_for_entity(self.ecs_entity, Buffs)
            
            # Check if buff with same name exists, replace if new one has longer duration
            for existing_buff in buffs_comp.active_buffs[:]:
                if existing_buff.name == buff.name:
                    if buff.duration > existing_buff.duration:
                        buffs_comp.active_buffs.remove(existing_buff)
                    else:
                        return  # Keep existing buff
            
            buffs_comp.active_buffs.append(buff)
            
            # Trigger on_apply callback
            if buff.on_apply:
                buff.on_apply(self)
            
            print(f"Added buff: {buff.name} to entity {self.ecs_entity}")

class CombatSystem(esper.Processor):
    def process(self, *args, **kwargs):
        dt = args[0] if args else 0.0
        game = getattr(esper, 'game', None)
        if not game:
            print("CombatSystem: No game instance found.")
            return
        print("CombatSystem: Processing combat...")
        
        # 1. Update Cooldowns
        for ent, combat in esper.get_component(Combat):
            if combat.collision_list:
                to_remove = []
                for key in combat.collision_list.keys():
                    combat.collision_list[key] -= dt
                    if combat.collision_list[key] <= 0:
                        to_remove.append(key)
                for key in to_remove:
                    del combat.collision_list[key]

        # 2. Collect and classify entities by tag
        entities_by_tag = {}  # {tag: [(ent, rect, combat, pos), ...]}
        
        for ent, (pos, combat) in esper.get_components(Position, Combat):
            if not combat.can_attack:
                continue
                
            # Get entity size
            w, h = 32, 32
            if esper.has_component(ent, Collider):
                col = esper.component_for_entity(ent, Collider)
                w, h = col.w, col.h
            elif esper.has_component(ent, Renderable):
                rend = esper.component_for_entity(ent, Renderable)
                w, h = rend.w, rend.h
            
            # Get entity tag
            tagcmp = esper.try_component(ent, Tag)
            tag = tagcmp.tag if tagcmp else "untagged"
            
            # Create rect and add to tag group
            rect = pygame.Rect(pos.x - w//2, pos.y - h//2, w, h)
            
            if tag not in entities_by_tag:
                entities_by_tag[tag] = []
            entities_by_tag[tag].append((ent, rect, combat, pos, tag))
        
        # 3. Check collisions only between different tag groups
        tag_list = list(entities_by_tag.keys())
        
        for i, tag1 in enumerate(tag_list):
            for tag2 in tag_list[i+1:]:  # Only check each pair once
                # Skip if same tag (already filtered by different groups)
                if tag1 == tag2:
                    continue
                
                # Check collisions between tag1 group and tag2 group
                for ent1, rect1, combat1, pos1, _ in entities_by_tag[tag1]:
                    for ent2, rect2, combat2, pos2, _ in entities_by_tag[tag2]:
                        # Check collisiond
                        if rect1.colliderect(rect2):
                            # Check cooldown
                            if ent2 in combat1.collision_list:
                                continue
                            
                            # Check penetration
                            if combat1.max_penetration_count > 0 and combat1.current_penetration_count >= combat1.max_penetration_count:
                                continue
                                
                            # Apply Damage from ent1 to ent2
                            if esper.has_component(ent2, Health):
                                self._apply_collision_damage(ent1, ent2, combat1, game, entities_by_tag)
                        
                        # Also check reverse collision (ent2 attacking ent1)
                        if rect2.colliderect(rect1):
                            # Check cooldown
                            if ent1 in combat2.collision_list:
                                continue
                            
                            # Check penetration
                            if combat2.max_penetration_count > 0 and combat2.current_penetration_count >= combat2.max_penetration_count:
                                continue
                                
                            # Apply Damage from ent2 to ent1
                            if esper.has_component(ent1, Health):
                                self._apply_collision_damage(ent2, ent1, combat2, game, entities_by_tag)

    def _apply_collision_damage(self, attacker, target, combat, game, entities_by_tag):
        """Apply damage from attacker to target."""
        
        print(f"Applying damage from Entity {attacker} to Entity {target}")
        # Get damage multiplier from buffs if attacker has buffs
        damage_mult = 1.0
        if  esper.has_component(attacker, Buffs):
            buffs_comp =  esper.component_for_entity(attacker, Buffs)
            damage_mult = buffs_comp.modifiers.get('damage_multiplier', 1.0)
        
        # Calculate element multiplier
        element_mult = 1.0
        if combat.damage_to_element:
            element_mult = combat.damage_to_element.get(combat.atk_element, 1.0)
        
        # Calculate effective damage
        effective_damage = int(combat.damage * element_mult * damage_mult)
        
        # Use HealthSystem to apply damage
        health_system = esper.get_processor(HealthSystem)
        if health_system:
            killed, actual_damage = health_system.take_damage(
                target,
                element=combat.atk_element,
                base_damage=effective_damage,
                max_hp_percentage_damage=combat.max_hp_percentage_damage,
                current_hp_percentage_damage=combat.current_hp_percentage_damage,
                lose_hp_percentage_damage=combat.lose_hp_percentage_damage,
                cause_death=combat.cause_death
            )
            
            # Add to cooldown
            combat.collision_list[target] = combat.collision_cooldown
            
            # Increment penetration count
            if combat.max_penetration_count > 0:
                combat.current_penetration_count += 1
            
            print(f"ECS Combat: Entity {attacker} hit {target} for {actual_damage} damage!")
            
            # Apply buffs to target
            if combat.buffs and  esper.has_component(target, Buffs):
                target_buffs =  esper.component_for_entity(target, Buffs)
                for buff in combat.buffs:
                    # Deep copy buff before applying
                    import copy
                    buff_copy = copy.deepcopy(buff)
                    target_buffs.active_buffs.append(buff_copy)
                    print(f"Applied buff to entity {target}")
            
            # Trigger explosion if configured
            if combat.explosion_range > 0:
                self._trigger_explosion(attacker, combat, game, damage_mult, entities_by_tag)

    def _trigger_explosion(self, source, combat, game, damage_mult, entities_by_tag):
        """Trigger explosion damage around source entity."""
        if combat.explosion_range <= 0:
            return
        
        # Get source position
        if not  esper.has_component(source, Position):
            return
        
        source_pos =  esper.component_for_entity(source, Position)
        source_tagcmp =  esper.try_component(source, Tag)
        source_tag = source_tagcmp.tag if source_tagcmp else "untagged"
        explosion_center = (source_pos.x, source_pos.y)
        range_sq = combat.explosion_range ** 2
        
        for target_tag, targets in entities_by_tag.items():
            if target_tag == source_tag: # 免疫同標籤傷害
                continue
            # Check all entities for explosion damage
            for ent, ent_rect, ent_combat, ent_pos, tag in targets:
                if ent == source:
                    continue
                
                # Check team (don't damage same team)
                is_player_source =  esper.has_component(source, Input)
                is_player_target =  esper.has_component(ent, Input)
                if is_player_source == is_player_target:
                    continue
                
                # Calculate distance
                ent_w, ent_h = 32, 32
                if  esper.has_component(ent, Collider):
                    col =  esper.component_for_entity(ent, Collider)
                    ent_w, ent_h = col.w, col.h
                elif  esper.has_component(ent, Renderable):
                    rend =  esper.component_for_entity(ent, Renderable)
                    ent_w, ent_h = rend.w, rend.h
                
                entity_center = (ent_pos.x + ent_w / 2, ent_pos.y + ent_h / 2)
                distance = math.sqrt(
                    (explosion_center[0] - entity_center[0])**2 + 
                    (explosion_center[1] - entity_center[1])**2
                )
                
                if distance <= combat.explosion_range:
                    # Apply explosion damage
                    if  esper.has_component(ent, Health):
                        # Calculate explosion element multiplier
                        explosion_mult = 1.0
                        if combat.damage_to_element:
                            explosion_mult = combat.damage_to_element.get(combat.explosion_element, 1.0)
                        
                        effective_explosion_damage = int(combat.explosion_damage * explosion_mult * damage_mult)
                        
                        # Use HealthSystem to apply explosion damage
                        health_system = game.ecs_world.get_processor(HealthSystem)
                        if health_system:
                            killed, actual_damage = health_system.take_damage(
                                ent,
                                element=combat.explosion_element,
                                base_damage=effective_explosion_damage,
                                max_hp_percentage_damage=combat.explosion_max_hp_percentage_damage,
                                current_hp_percentage_damage=combat.explosion_current_hp_percentage_damage,
                                lose_hp_percentage_damage=combat.explosion_lose_hp_percentage_damage,
                                cause_death=combat.cause_death
                            )
                            
                            print(f"Explosion damage: {actual_damage} to entity {ent}")
                            
                            # Apply explosion buffs
                            if combat.explosion_buffs and  esper.has_component(ent, Buffs):
                                target_buffs =  esper.component_for_entity(ent, Buffs)
                                for buff in combat.explosion_buffs:
                                    import copy
                                    buff_copy = copy.deepcopy(buff)
                                    target_buffs.active_buffs.append(buff_copy)

# class AISystem(esper.Processor):
#     def process(self, *args, **kwargs):
#         print("AISystem: Processing AI behavior trees...")
#         dt = args[0] if args else 0.0
#         current_time = args[3] if len(args) > 2 else 0
#         game = args[4] if len(args) > 4 else None
#         for ent, (ai, pos, vel) in  esper.get_components(AI, Position, Velocity):
#             if not ai.behavior_tree:
#                 continue
            
#             # Create entity wrapper for behavior tree
#             context = EnemyContext(esper, ent, game, ai)
            
#             # Execute behavior tree with wrapper
#             try:
#                 ai.behavior_tree.execute(context, dt, current_time)
#             except Exception as e:
#                 print(f"Error executing behavior tree for entity {ent}: {e}")

# class AIEntityWrapper(EntityWrapper):
#     """Extended EntityWrapper specifically for AI behavior trees."""
#     def __init__(self, ecs_entity, world, game, ai_component):
#         super().__init__(ecs_entity, world, game)
#         self.ai_component = ai_component
    
#     # AI-specific properties
#     @property
#     def action_list(self):
#         """Get current action list from AI component."""
#         return self.ai_component.action_list if self.ai_component.action_list else []
    
#     @action_list.setter
#     def action_list(self, value):
#         """Set action list in AI component."""
#         self.ai_component.action_list = value
    
#     @property
#     def current_action(self):
#         """Get current action from AI component."""
#         return self.ai_component.current_action
    
#     @current_action.setter
#     def current_action(self, value):
#         """Set current action in AI component."""
#         self.ai_component.current_action = value
    
#     @property
#     def actions(self):
#         """Get actions dictionary from AI component."""
#         return self.ai_component.actions if self.ai_component.actions else {}
    
#     @property
#     def behavior_tree(self):
#         """Get behavior tree from AI component."""
#         return self.ai_component.behavior_tree
    
#     # Movement properties
#     @property
#     def speed(self):
#         """Get speed from Velocity component."""
#         if  esper.has_component(self.ecs_entity, Velocity):
#             return  esper.component_for_entity(self.ecs_entity, Velocity).speed
#         return 100.0
    
#     @speed.setter
#     def speed(self, value):
#         """Set speed in Velocity component."""
#         if  esper.has_component(self.ecs_entity, Velocity):
#              esper.component_for_entity(self.ecs_entity, Velocity).speed = value
    
#     @property
#     def max_speed(self):
#         """Get max speed (same as speed for now)."""
#         return self.speed
    
#     # Combat properties
#     @property
#     def can_attack(self):
#         """Get can_attack from Combat component."""
#         if  esper.has_component(self.ecs_entity, Combat):
#             return  esper.component_for_entity(self.ecs_entity, Combat).can_attack
#         return False
    
#     @can_attack.setter
#     def can_attack(self, value):
#         """Set can_attack in Combat component."""
#         if  esper.has_component(self.ecs_entity, Combat):
#              esper.component_for_entity(self.ecs_entity, Combat).can_attack = value
    
#     @property
#     def vision_radius(self):
#         """Get vision radius (stored in AI component or default)."""
#         # Vision radius could be stored in AI component or a separate component
#         # For now, return a default value
#         return 10  # tiles
    
#     # Health properties
#     @property
#     def is_alive(self):
#         """Check if entity is alive."""
#         if  esper.has_component(self.ecs_entity, Health):
#             health =  esper.component_for_entity(self.ecs_entity, Health)
#             return health.current_hp > 0
#         return True
    
#     def is_alive(self):
#         """Method version of is_alive for compatibility."""
#         if  esper.has_component(self.ecs_entity, Health):
#             health =  esper.component_for_entity(self.ecs_entity, Health)
#             return health.current_hp > 0
#         return True
    
#     # Movement method
#     def move(self, dx, dy, dt):
#         """Move the entity by setting velocity."""
#         if  esper.has_component(self.ecs_entity, Velocity):
#             vel =  esper.component_for_entity(self.ecs_entity, Velocity)
#             # Normalize if needed
#             magnitude = math.sqrt(dx*dx + dy*dy)
#             if magnitude > 0:
#                 vel.x = (dx / magnitude) * vel.speed
#                 vel.y = (dy / magnitude) * vel.speed
#             else:
#                 vel.x = 0
#                 vel.y = 0
    
#     # Tag property for team identification
#     @property
#     def tag(self):
#         """Get tag (enemy/player). For AI entities, assume 'enemy'."""
#         # Could be stored in a Tag component if we add one
#         if  esper.has_component(self.ecs_entity, Input):
#             return "player"
#         return "enemy"

class EnergySystem(esper.Processor):
    def process(self, dt: float, *args, **kwargs) -> None:
        """處理所有擁有 PlayerComponent 的實體的能量再生。"""
        
        for ent, comp in esper.get_component(PlayerComponent):
            # 檢查是否需要再生
            if comp.energy < comp.max_energy:
                comp.energy += comp.energy_regen_rate * dt
                # 限制不超過最大值
                if comp.energy > comp.max_energy:
                    comp.energy = comp.max_energy

class AISystem(esper.Processor):
    def __init__(self, game: 'Game'):
        super().__init__()
        self.game = game

    def process(self, *args, **kwargs):
        dt = args[0]
        current_time = self.game.current_time
        print("AISystem: Processing AI behavior trees...")
        for ent, (pos, ai_comp) in esper.get_components(Position, AI):
            print(f"AISystem: Executing behavior tree for entity {ent}")
            # 創建 Context Facade
            context = EnemyContext(esper, ent, self.game, ai_comp)
            # 執行行為樹
            ai_comp.behavior_tree.execute(context, dt, current_time)

# 遊戲主循環應在 MovementSystem, RenderSystem 之前調用 AISystem:
# self.world.add_processor(AISystem(self))
# ...
# self.world.process(dt, current_time)