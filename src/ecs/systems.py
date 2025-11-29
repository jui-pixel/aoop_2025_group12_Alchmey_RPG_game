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
                        # Check X only
                        tile_x_curr = int(pos.x // TILE_SIZE)
                        tile_y_new = int(new_y // TILE_SIZE)
                        
                        # Check Y only
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
                            vel.y = 0 # Stop Y movement
                        elif y_allowed:
                            pos.y = new_y
                            vel.x = 0 # Stop X movement
                        else:
                            vel.x = 0
                            vel.y = 0
                else:
                    # Out of bounds, stop
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
        for ent, health in self.world.get_component(Health):
            # Simple regeneration logic could go here
            # For now, just death check
            if health.current_hp <= 0:
                # Handle death
                # For now, just print, or tag for removal
                # Real removal should probably happen in a cleanup phase or via EventManager
                pass

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
        # Get all entities with Position, Combat, and Renderable (for size)
        # If Renderable is missing, we might need a Size component or Collider
        # We'll use Collider if available, else Renderable, else default 32x32
        
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
                
                # Check if ent1 can damage ent2
                # We need a way to distinguish teams (Player vs Enemy)
                # Currently using 'tag' in Entity classes. 
                # In ECS, we should use a Tag component or check specific components.
                # For now, let's assume we can access the 'tag' from the Entity object wrapper if it exists,
                # or add a Tag component.
                # Let's add a simple Tag component check if we can, otherwise skip friendly fire check for now?
                # No, friendly fire is bad.
                # We can check if one has Input (Player) and other has AI (Enemy).
                
                is_player_1 = self.world.has_component(ent1, Input)
                is_player_2 = self.world.has_component(ent2, Input)
                
                # Don't hit same team
                if is_player_1 == is_player_2:
                    continue
                    
                if rect1.colliderect(rect2):
                    # Check cooldown
                    if ent2 in combat1.collision_list:
                        continue
                        
                    # Apply Damage
                    if self.world.has_component(ent2, Health):
                        health2 = self.world.component_for_entity(ent2, Health)
                        defense2 = self.world.try_component(ent2, Defense)
                        
                        # Calculate Damage
                        damage = combat1.damage
                        # Element modifiers... (simplified for now)
                        
                        # Apply Defense
                        def_val = defense2.defense if defense2 else 0
                        actual_damage = max(1, damage - def_val) # Simplified formula
                        
                        # Apply to Health
                        if not (defense2 and defense2.invulnerable):
                            health2.current_hp -= actual_damage
                            print(f"ECS Combat: Entity {ent1} hit {ent2} for {actual_damage} damage!")
                            
                            # Add to cooldown
                            combat1.collision_list[ent2] = combat1.collision_cooldown
                            
                            # Handle Death (HealthSystem will pick it up, or do it here)
                            if health2.current_hp <= 0:
                                print(f"Entity {ent2} died!")
                                # self.world.delete_entity(ent2) # Defer deletion

class AISystem(esper.Processor):
    def process(self, dt):
        game = getattr(self.world, 'game', None)
        current_time = game.current_time if game else 0
        
        for ent, (ai, pos, vel) in self.world.get_components(AI, Position, Velocity):
            if ai.behavior_tree:
                # We need to pass an 'entity' object to the behavior tree
                # because existing nodes expect it.
                # We can try to find the original entity object from EntityManager
                # using the ID if we stored it, or if 'ent' is the ID.
                # Currently, ECS entities are just IDs.
                # The existing Entity objects (Enemy1) hold the ECS ID.
                # So we might need to find the Entity object that corresponds to this ECS ID.
                
                # This is a hybrid approach issue.
                # Ideally, BehaviorTree should operate on Components, not Entity objects.
                # For now, we might skip this or assume the Entity object calls the tree in its update (which it does).
                pass