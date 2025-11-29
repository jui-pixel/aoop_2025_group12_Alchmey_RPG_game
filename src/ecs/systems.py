import esper
import pygame
import math
from .components import Position, Velocity, Renderable, Input, Health, Defense, Combat, Buffs, AI, Collider
from src.config import TILE_SIZE, PASSABLE_TILES, SCREEN_WIDTH, SCREEN_HEIGHT

class MovementSystem(esper.Processor):
    def process(self, dt):
        # Get dungeon from game instance attached to world
        game = getattr(self.world, 'game', None)
        dungeon = game.dungeon_manager.get_dungeon() if game else None
        
        for ent, (pos, vel) in self.world.get_components(Position, Velocity):
            if vel.x == 0 and vel.y == 0:
                continue
            
            # Get Collider if exists, else default
            collider = self.world.try_component(ent, Collider)
            pass_wall = collider.pass_wall if collider else False
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
    def process(self, dt):
        game = getattr(self.world, 'game', None)
        if not game:
            return
            
        screen = game.screen
        camera_offset = game.render_manager.camera_offset
        
        # Collect and sort renderables
        render_list = []
        for ent, (pos, rend) in self.world.get_components(Position, Renderable):
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
                
            # Draw Health Bar if entity has Health component
            if self.world.has_component(ent, Health):
                health = self.world.component_for_entity(ent, Health)
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
    def process(self, dt):
        keys = pygame.key.get_pressed()
        
        for ent, (inp, vel) in self.world.get_components(Input, Velocity):
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
    def process(self, dt):
        game = getattr(self.world, 'game', None)
        
        # Check for dead entities and handle death
        for ent, health in self.world.get_component(Health):
            if health.current_hp <= 0:
                self._handle_death(ent, game)
    
    def take_damage(self, entity, factor=1.0, element="untyped", base_damage=0,
                   max_hp_percentage_damage=0, current_hp_percentage_damage=0,
                   lose_hp_percentage_damage=0, cause_death=True):
        """
        Apply damage to an entity with Health and Defense components.
        Returns: (killed: bool, actual_damage: int)
        """
        if not self.world.has_component(entity, Health):
            return False, 0
        
        health = self.world.component_for_entity(entity, Health)
        defense = self.world.try_component(entity, Defense)
        
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
        
        # Create damage text
        self._create_damage_text(entity, final_damage)
        
        return killed, final_damage
    
    def heal(self, entity, amount):
        """Heal an entity by the specified amount."""
        if not self.world.has_component(entity, Health):
            return
        
        health = self.world.component_for_entity(entity, Health)
        health.current_hp = min(health.max_hp, health.current_hp + amount)
    
    def add_shield(self, entity, amount):
        """Add shield to an entity by the specified amount."""
        if not self.world.has_component(entity, Health):
            return
        
        health = self.world.component_for_entity(entity, Health)
        health.current_shield = min(health.max_shield, health.current_shield + amount)
    
    def set_max_hp(self, entity, new_max_hp):
        """Set max HP and scale current HP proportionally."""
        if not self.world.has_component(entity, Health):
            return
        
        health = self.world.component_for_entity(entity, Health)
        old_max = health.max_hp
        health.max_hp = max(0, new_max_hp)
        
        if old_max > 0:
            health.current_hp = int(health.current_hp * new_max_hp / old_max)
        else:
            health.current_hp = new_max_hp
    
    def set_max_shield(self, entity, new_max_shield):
        """Set max shield and clamp current shield."""
        if not self.world.has_component(entity, Health):
            return
        
        health = self.world.component_for_entity(entity, Health)
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
        game = getattr(self.world, 'game', None)
        if not game or not self.world.has_component(entity, Position):
            return
        
        pos = self.world.component_for_entity(entity, Position)
        
        from src.entities.damage_text import DamageText
        damage_text = DamageText((pos.x, pos.y), text)
        game.entity_manager.damage_text_group.add(damage_text)
    
    def _handle_death(self, entity, game):
        """Handle entity death."""
        print(f"Entity {entity} died!")
        # Option: Mark for deletion (to be handled by a cleanup system)
        # self.world.delete_entity(entity)  # Careful: don't delete during iteration

class BuffSystem(esper.Processor):
    def process(self, dt):
        for ent, buffs in self.world.get_component(Buffs):
            if not buffs.active_buffs:
                continue
                
            for buff in buffs.active_buffs[:]:
                buff.duration -= dt
                if buff.duration <= 0:
                    buffs.active_buffs.remove(buff)
                    # Trigger on_remove if needed
                else:
                    # Apply effect per second
                    if buff.effect_per_second:
                        buff.effect_time += dt
                        if buff.effect_time - buff.last_effect_time >= 1.0:
                            # We need the entity object to pass to effect_per_second
                            # This is tricky in pure ECS if effects expect an Entity object
                            # We might need to pass the ID or a wrapper
                            pass 

class CombatSystem(esper.Processor):
    def process(self, dt):
        game = getattr(self.world, 'game', None)
        if not game:
            return
            
        # 1. Update Cooldowns
        for ent, combat in self.world.get_component(Combat):
            if combat.collision_list:
                to_remove = []
                for key in combat.collision_list.keys():
                    combat.collision_list[key] -= dt
                    if combat.collision_list[key] <= 0:
                        to_remove.append(key)
                for key in to_remove:
                    del combat.collision_list[key]

        # 2. Check Collisions
        entities = []
        for ent, (pos, combat) in self.world.get_components(Position, Combat):
            if not combat.can_attack:
                continue
                
            w, h = 32, 32
            if self.world.has_component(ent, Collider):
                col = self.world.component_for_entity(ent, Collider)
                w, h = col.w, col.h
            elif self.world.has_component(ent, Renderable):
                rend = self.world.component_for_entity(ent, Renderable)
                w, h = rend.w, rend.h
            
            rect = pygame.Rect(pos.x - w//2, pos.y - h//2, w, h)
            entities.append((ent, rect, combat, pos))
            
        # Naive O(N^2) check for now
        for i, (ent1, rect1, combat1, pos1) in enumerate(entities):
            for j, (ent2, rect2, combat2, pos2) in enumerate(entities):
                if i == j:
                    continue
                
                # Check if ent1 can damage ent2 (Player vs Enemy)
                is_player_1 = self.world.has_component(ent1, Input)
                is_player_2 = self.world.has_component(ent2, Input)
                
                # Don't hit same team
                if is_player_1 == is_player_2:
                    continue
                    
                if rect1.colliderect(rect2):
                    # Check cooldown
                    if ent2 in combat1.collision_list:
                        continue
                    
                    # Check penetration
                    if combat1.max_penetration_count > 0 and combat1.current_penetration_count >= combat1.max_penetration_count:
                        continue
                        
                    # Apply Damage
                    if self.world.has_component(ent2, Health):
                        self._apply_collision_damage(ent1, ent2, combat1, game, entities)
    
    def _apply_collision_damage(self, attacker, target, combat, game, all_entities):
        """Apply damage from attacker to target."""
        # Get damage multiplier from buffs if attacker has buffs
        damage_mult = 1.0
        if self.world.has_component(attacker, Buffs):
            buffs_comp = self.world.component_for_entity(attacker, Buffs)
            damage_mult = buffs_comp.modifiers.get('damage_multiplier', 1.0)
        
        # Calculate element multiplier
        element_mult = 1.0
        if combat.damage_to_element:
            element_mult = combat.damage_to_element.get(combat.atk_element, 1.0)
        
        # Calculate effective damage
        effective_damage = int(combat.damage * element_mult * damage_mult)
        
        # Use HealthSystem to apply damage
        health_system = game.ecs_world.get_processor(HealthSystem)
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
            if combat.buffs and self.world.has_component(target, Buffs):
                target_buffs = self.world.component_for_entity(target, Buffs)
                for buff in combat.buffs:
                    # Deep copy buff before applying
                    import copy
                    buff_copy = copy.deepcopy(buff)
                    target_buffs.active_buffs.append(buff_copy)
                    print(f"Applied buff to entity {target}")
            
            # Trigger explosion if configured
            if combat.explosion_range > 0:
                self._trigger_explosion(attacker, combat, game, all_entities, damage_mult)
    
    def _trigger_explosion(self, source, combat, game, all_entities, damage_mult):
        """Trigger explosion damage around source entity."""
        if combat.explosion_range <= 0:
            return
        
        # Get source position
        if not self.world.has_component(source, Position):
            return
        
        source_pos = self.world.component_for_entity(source, Position)
        
        # Get source size for center calculation
        w, h = 32, 32
        if self.world.has_component(source, Collider):
            col = self.world.component_for_entity(source, Collider)
            w, h = col.w, col.h
        elif self.world.has_component(source, Renderable):
            rend = self.world.component_for_entity(source, Renderable)
            w, h = rend.w, rend.h
        
        explosion_center = (source_pos.x + w / 2, source_pos.y + h / 2)
        
        # Check all entities for explosion damage
        for ent, ent_rect, ent_combat, ent_pos in all_entities:
            if ent == source:
                continue
            
            # Check team (don't damage same team)
            is_player_source = self.world.has_component(source, Input)
            is_player_target = self.world.has_component(ent, Input)
            if is_player_source == is_player_target:
                continue
            
            # Calculate distance
            ent_w, ent_h = 32, 32
            if self.world.has_component(ent, Collider):
                col = self.world.component_for_entity(ent, Collider)
                ent_w, ent_h = col.w, col.h
            elif self.world.has_component(ent, Renderable):
                rend = self.world.component_for_entity(ent, Renderable)
                ent_w, ent_h = rend.w, rend.h
            
            entity_center = (ent_pos.x + ent_w / 2, ent_pos.y + ent_h / 2)
            distance = math.sqrt(
                (explosion_center[0] - entity_center[0])**2 + 
                (explosion_center[1] - entity_center[1])**2
            )
            
            if distance <= combat.explosion_range:
                # Apply explosion damage
                if self.world.has_component(ent, Health):
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
                        if combat.explosion_buffs and self.world.has_component(ent, Buffs):
                            target_buffs = self.world.component_for_entity(ent, Buffs)
                            for buff in combat.explosion_buffs:
                                import copy
                                buff_copy = copy.deepcopy(buff)
                                target_buffs.active_buffs.append(buff_copy)

class AISystem(esper.Processor):
    def process(self, dt):
        game = getattr(self.world, 'game', None)
        current_time = game.current_time if game else 0
        
        for ent, (ai, pos, vel) in self.world.get_components(AI, Position, Velocity):
            if ai.behavior_tree:
                # We need to pass an 'entity' object to the behavior tree
                # because existing nodes expect it.
                # This is a hybrid approach issue.
                # Ideally, BehaviorTree should operate on Components, not Entity objects.
                # For now, we might skip this or assume the Entity object calls the tree in its update (which it does).
                pass