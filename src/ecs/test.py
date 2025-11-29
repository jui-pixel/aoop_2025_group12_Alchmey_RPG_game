# test.py
import pygame
import esper
from .components import *
from .systems import *

pygame.init()
SCREEN_W, SCREEN_H = 1000, 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Esper + Pygame 簡易 Roguelike 可視化")
clock = pygame.time.Clock()

world = esper.World()
world.game = None  # 這裡不需要 Game 物件，系統直接拿 screen 參數

# 加入系統
world.add_processor(InputSystem())
world.add_processor(MovementSystem())
world.add_processor(CombatSystem())
world.add_processor(RenderSystem())

# ==== 產生玩家 ====
player = world.create_entity()
world.add_component(player, Position(x=500, y=300))
world.add_component(player, Velocity(speed=250))
world.add_component(player, Input())
player_surf = pygame.Surface((32,32), pygame.SRCALPHA)
pygame.draw.circle(player_surf, (0,200,255), (16,16), 16)
world.add_component(player, Renderable(image=player_surf, color=(0,200,255)))
world.add_component(player, Health(max_hp=100, current_hp=100))
world.add_component(player, Collider(w=32, h=32))

# ==== 產生幾隻怪物 ====
for i in range(8):
    e = world.create_entity()
    world.add_component(e, Position(x=200 + i*90, y=200 + (i%3)*80))
    world.add_component(e, Velocity(speed=80))
    world.add_component(e, AI())
    surf = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (200,50,50), [(16,0),(0,32),(32,32)])
    world.add_component(e, Renderable(image=surf, color=(200,50,50), layer=1))
    world.add_component(e, Health(max_hp=50, current_hp=50))
    world.add_component(e, Combat(damage=12, collision_cooldown=0.5))
    world.add_component(e, Collider(w=32, h=32))

running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    screen.fill((30, 30, 40))  # 深色背景

    # 簡單相機跟隨玩家
    player_pos = world.component_for_entity(player, Position)
    camera_x = player_pos.x - SCREEN_W//2
    camera_y = player_pos.y - SCREEN_H//2

    world.process(dt,
                  screen=screen,
                  camera=(camera_x, camera_y))

    # 顯示 FPS
    fps = clock.get_fps()
    font = pygame.font.SysFont("consolas", 20)
    screen.blit(font.render(f"FPS: {fps:.1f}", True, (255,255,0)), (10,10))

    pygame.display.flip()

pygame.quit()