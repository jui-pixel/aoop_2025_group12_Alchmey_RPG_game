from src.skills.skill import Skill
from src.character.character import Player
from src.dungeon.dungeon import Dungeon
from src.config import TILE_SIZE
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
    """使玩家向前衝刺並短暫無敵，檢查碰撞"""
    direction = player.direction  # 固定向上衝刺，可根據鼠標方向動態調整
    dash_distance = 5 * TILE_SIZE
    new_x = player.pos[0] + direction[0] * dash_distance
    new_y = player.pos[1] + direction[1] * dash_distance

    # 檢查新位置是否可通行
    tile_x = int(new_x // TILE_SIZE)
    tile_y = int(new_y // TILE_SIZE)
    dungeon: Dungeon = game.dungeon
    if (0 <= tile_x < dungeon.grid_width and 0 <= tile_y < dungeon.grid_height and
            dungeon.dungeon_tiles[tile_y][tile_x] not in ('Border_wall', 'Outside')):
        player.pos = (new_x, new_y)
        player.rect.center = player.pos
        player.invulnerable = 1.0
        # 更新迷霧地圖
        game.update_fog_map(tile_x, tile_y)
        print(f"Skill 'Shadow Dash' used: Player dashed to ({new_x}, {new_y})")
    else:
        print(f"Skill 'Shadow Dash' blocked: Invalid destination ({tile_x}, {tile_y})")


def time_slow_effect(player: Player, game: 'Game') -> None:
    """減慢遊戲時間 2 秒"""
    game.time_scale = 0.5
    pygame.time.set_timer(pygame.USEREVENT, 2000)
    print("Skill 'Time Warp' used: Time scale set to 0.5 for 2 seconds")


def reveal_fog_effect(player: Player, game: 'Game') -> None:
    """臨時擴大玩家的迷霧揭示範圍"""
    original_radius = game.vision_radius
    game.vision_radius = original_radius * 5  # 擴大視野
    tile_x = int(player.pos[0] / TILE_SIZE)
    tile_y = int(player.pos[1] / TILE_SIZE)
    game.update_fog_map(tile_x, tile_y)
    game.vision_radius = original_radius  # 恢復原始視野
    print(f"Skill 'Reveal Fog' used: Temporarily doubled vision radius to {original_radius * 2}")


SKILL_LIBRARY = [
    Skill(name="Restore Ammo", cooldown=2.0, duration=0.0, effect=restore_ammo_effect),
    Skill(name="Carry 10 Weapons", cooldown=0.0, duration=0.0, effect=carry_more_weapons_effect),
    Skill(name="Shadow Dash", cooldown=2.0, duration=1.0, effect=shadow_dash_effect),
    Skill(name="Time Warp", cooldown=2.0, duration=2.0, effect=time_slow_effect),
    Skill(name="Reveal Fog", cooldown=5.0, duration=0.0, effect=reveal_fog_effect),
]