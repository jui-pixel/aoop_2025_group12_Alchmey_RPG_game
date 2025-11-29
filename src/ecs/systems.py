import esper
import pygame
import math
from .components import Position, Velocity, Renderable, Input, Health, Defense, Combat, Buffs, AI
from src.config import TILE_SIZE, PASSABLE_TILES, SCREEN_WIDTH, SCREEN_HEIGHT

class MovementSystem(esper.Processor):
    def process(self, dt):
        # Get dungeon from game instance attached to world
        game = getattr(self.world, 'game', None)
        dungeon = game.dungeon_manager.get_dungeon() if game else None
        
        for ent, (pos, vel) in self.world.get_components(Position, Velocity):
            if vel.x == 0 and vel.y == 0:
                continue
                
            # Calculate potential new position
            new_x = pos.x + vel.x * dt
            new_y = pos.y + vel.y * dt
            
            # Wall Collision Logic
            if dungeon:
                # Simple check: if center is in wall, don't move
                # A more robust check would use the entity's size (Collider)
                # For now, we assume a point or small radius check for simplicity, 
                # or rely on the fact that entities are usually smaller than tiles.
                
                # Check X movement
                tile_x = int(new_x // TILE_SIZE)
                tile_y = int(pos.y // TILE_SIZE)
                if 0 <= tile_x < dungeon.grid_width and 0 <= tile_y < dungeon.grid_height:
                    if dungeon.dungeon_tiles[tile_y][tile_x] in PASSABLE_TILES:
                        pos.x = new_x
                    else:
                        vel.x = 0 # Stop on X collision
                
                # Check Y movement
                tile_x = int(pos.x // TILE_SIZE)
                tile_y = int(new_y // TILE_SIZE)
                if 0 <= tile_x < dungeon.grid_width and 0 <= tile_y < dungeon.grid_height:
                    if dungeon.dungeon_tiles[tile_y][tile_x] in PASSABLE_TILES:
                        pos.y = new_y
                    else:
                        vel.y = 0 # Stop on Y collision
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
        
        # Sort by layer if needed, for now just iterate
        # We might want to collect all renderables and sort them by layer/y-pos
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