# src/skills/skill_library.py
from src.entities.character.skills.skill import Skill
from src.entities.character.character import Player
from src.dungeon.dungeon import Dungeon
from src.config import TILE_SIZE
from src.entities.buff import Buff
import pygame


def inf_energy(player: Player, game: 'Game') -> None:
    """高速恢復玩家能量"""
    def on_apply(entity: 'Player') -> None:
        """Set high energy regeneration rate."""
        entity.energy_regen_rate = 500.0  # 25x default rate
        print(f"Skill 'Inf Energy' applied: Energy regeneration rate set to {entity.energy_regen_rate} for {buff.duration}s")

    def on_remove(entity: 'Player') -> None:
        """Restore original energy regeneration rate."""
        entity.energy_regen_rate = entity.original_energy_regen_rate
        print(f"Skill 'Inf Energy' ended: Energy regeneration rate reset to {entity.energy_regen_rate}")

    buff = Buff(
        name="InfEnergy",
        duration=5.0,  # 5 second duration
        effects={"energy_regen_per_second": 500.0},
        on_apply=on_apply,
        on_remove=on_remove
    )
    player.apply_buff(buff)


def shadow_dash_effect(player: Player, game: 'Game') -> None:
    """Apply a Shadow Dash buff to the player, increasing speed and granting invulnerability for 1 second."""
    
    def on_apply(entity: 'MovableEntity') -> None:
        """Handle movement and collision detection when the buff is applied."""
        entity.invulnerable = buff.duration  # Set invulnerability for the buff duration
        print(f"Skill 'Shadow Dash' applied: Speed increased to {entity.speed * 3}, invulnerable for {buff.duration}s")

    def on_remove(entity: 'MovableEntity') -> None:
        """Reset speed when the buff is removed."""
        entity.invulnerable = 0.0
        print(f"Skill 'Shadow Dash' ended: Player speed reset to {entity.speed}, position at ({entity.pos[0]}, {entity.pos[1]})")

    # def check_collision(entity: 'MovableEntity', dt: float) -> None:
    #     """Check for collisions during movement and stop if hitting a wall."""
    #     if not entity.game or not entity.dungeon:
    #         return

    #     dx = entity.direction[0] * entity.speed * dt
    #     dy = entity.direction[1] * entity.speed * dt
    #     new_x = entity.pos[0] + dx
    #     new_y = entity.pos[1] + dy
    #     tile_x = int(new_x // TILE_SIZE)
    #     tile_y = int(new_y // TILE_SIZE)

    #     if (0 <= tile_x < entity.dungeon.grid_width and 
    #         0 <= tile_y < entity.dungeon.grid_height and
    #         entity.dungeon.dungeon_tiles[tile_y][tile_x] not in ('Border_wall', 'Outside')):
    #         entity.pos = [new_x, new_y]
    #         entity.rect.center = entity.pos
    #         game.update_fog_map(tile_x, tile_y)
    #     else:
    #         # Hit a wall, remove the buff to stop dashing
    #         entity.remove_buff(buff)
    #         print(f"Skill 'Shadow Dash' stopped: Hit wall at ({tile_x}, {tile_y})")

    # Create and apply the Shadow Dash buff
    buff = Buff(
        name="ShadowDash",
        duration=0.1,  # 1 second duration
        effects={"speed_multiplier": 3.0},
        on_apply=on_apply,
        on_remove=on_remove
    )

    # # Override the player's update_buffs to include collision checking during the dash
    # original_update_buffs = player.update_buffs
    # def custom_update_buffs(dt: float) -> None:
    #     original_update_buffs(dt)
    #     if buff in player.buffs:
    #         check_collision(player, dt)

    # player.update_buffs = custom_update_buffs  # Temporarily override update_buffs
    player.apply_buff(buff)

    # # Restore original update_buffs after buff expires
    # def restore_update_buffs():
    #     import time
    #     time.sleep(buff.duration)
    #     player.update_buffs = original_update_buffs

    # import threading
    # threading.Thread(target=restore_update_buffs, daemon=True).start()


def time_slow_effect(player: Player, game: 'Game') -> None:
    """減慢遊戲時間 2 秒，但不影響玩家移動與攻擊"""
    time_scale = 0.1
    duration = 0.5
    game.time_scale = time_scale
    game.camera_lerp_factor /= time_scale

    def on_apply(entity: 'MovableEntity') -> None:
        """Apply speed and attack rate compensation."""
        # Counteract time scale reduction for movement and firing
        speed_multiplier = 1.0 / time_scale
        for weapon in player.weapons:
            weapon.fire_rate = weapon.original_fire_rate * time_scale
        print(f"Skill 'Time Warp' applied: Time scale set to {time_scale}, player speed multiplied by {speed_multiplier}, weapon cooldowns adjusted")

    def on_remove(entity: 'MovableEntity') -> None:
        """Restore original speed and weapon cooldowns."""
        for weapon in player.weapons:
            weapon.fire_rate = weapon.original_fire_rate
        game.time_scale = 1.0
        game.camera_lerp_factor = game.original_camera_lerp_factor
        print(f"Skill 'Time Warp' ended: Time scale restored to 1.0, player speed and weapon cooldowns reset")

    # Create and apply the Time Warp buff to counteract time scale effects
    buff = Buff(
        name="TimeWarpCompensate",
        duration=duration,
        effects={"speed_multiplier": 1.0 / time_scale},
        on_apply=on_apply,
        on_remove=on_remove
    )
    player.apply_buff(buff)

    # Set a timer to ensure time scale is reset after duration
    pygame.time.set_timer(pygame.USEREVENT, int(duration * 1000))


def reveal_fog_effect(player: Player, game: 'Game') -> None:
    """臨時擴大玩家的迷霧揭示範圍"""
    original_radius = game.player.vision_radius
    game.player.apply_buff(Buff("vision_radius", 5.0, {"vision_radius_multiplier" : 20.0}))  # 臨時加倍視野半徑
    game.player.fog = False  # 取消迷霧效果
    tile_x = int(player.pos[0] / TILE_SIZE)
    tile_y = int(player.pos[1] / TILE_SIZE)
    game.update_fog_map(tile_x, tile_y)
    print(f"Skill 'Reveal Fog' used: Temporarily doubled vision radius to {original_radius * 20}")


SKILL_LIBRARY = [
    Skill(name="Inf Energy", cooldown=2.0, duration=0.0, effect=inf_energy),
    Skill(name="Shadow Dash", cooldown=0.5, duration=0.1, effect=shadow_dash_effect),
    Skill(name="Time Warp", cooldown=2.0, duration=2.0, effect=time_slow_effect),
    Skill(name="Reveal Fog", cooldown=5.0, duration=5.0, effect=reveal_fog_effect),
]