# src/skills/skill_library.py
from src.entities.character.skills.skill import Skill
from src.entities.character.character import Player
from src.dungeon.dungeon import Dungeon
from src.config import TILE_SIZE
from src.entities.buff import Buff
import pygame


def restore_ammo_effect(player: Player, game: 'Game') -> None:
    """恢復所有非近戰武器的彈藥"""
    for weapon in player.weapons:
        if not weapon.is_melee:
            weapon.ammo = weapon.max_ammo
    print(f"Skill 'Restore Ammo' used: Restored ammo for {len(player.weapons)} weapons")


def carry_more_weapons_effect(player: Player, game: 'Game') -> None:
    """增加玩家可攜帶的武器數量至 10"""
    player.max_weapons = 10
    print(f"Skill 'Carry 10 Weapons' used: Player max_weapons set to {player.max_weapons}")


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
        duration=1.0,  # 1 second duration
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
    """減慢遊戲時間 2 秒"""
    game.time_scale = 0.3
    pygame.time.set_timer(pygame.USEREVENT, 2000)
    print("Skill 'Time Warp' used: Time scale set to 0.3 for 2 seconds")


def reveal_fog_effect(player: Player, game: 'Game') -> None:
    """臨時擴大玩家的迷霧揭示範圍"""
    original_radius = game.player.vision_radius
    game.player.apply_buff(Buff("vision_radius", 5.0, {"vision_radius_multiplier" : 2.0}))  # 臨時加倍視野半徑
    game.player.fog = False  # 取消迷霧效果
    tile_x = int(player.pos[0] / TILE_SIZE)
    tile_y = int(player.pos[1] / TILE_SIZE)
    game.update_fog_map(tile_x, tile_y)
    print(f"Skill 'Reveal Fog' used: Temporarily doubled vision radius to {original_radius * 2}")


SKILL_LIBRARY = [
    Skill(name="Restore Ammo", cooldown=2.0, duration=0.0, effect=restore_ammo_effect),
    Skill(name="Carry 10 Weapons", cooldown=0.0, duration=0.0, effect=carry_more_weapons_effect),
    Skill(name="Shadow Dash", cooldown=2.0, duration=1.0, effect=shadow_dash_effect),
    Skill(name="Time Warp", cooldown=2.0, duration=2.0, effect=time_slow_effect),
    Skill(name="Reveal Fog", cooldown=5.0, duration=5.0, effect=reveal_fog_effect),
]