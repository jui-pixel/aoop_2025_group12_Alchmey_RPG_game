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

# --- 移除 world = esper.World() ---

# 這裡可以保留 esper.game = None 作為上下文佔位符
# esper.game = None 

# 加入系統 (使用全域註冊)
esper.add_processor(InputSystem())
esper.add_processor(MovementSystem())
esper.add_processor(CombatSystem())
esper.add_processor(RenderSystem())

# ==== 產生玩家 ====
# 使用全域方法創建實體和新增元件
player = esper.create_entity()
esper.add_component(player, Position(x=500, y=300))
esper.add_component(player, Velocity(speed=250))
esper.add_component(player, Input())
esper.add_component(player, Player())
player_surf = pygame.Surface((32,32), pygame.SRCALPHA)
pygame.draw.circle(player_surf, (0,200,255), (16,16), 16)
esper.add_component(player, Renderable(image=player_surf, color=(0,200,255)))
esper.add_component(player, Health(max_hp=100, current_hp=100))
esper.add_component(player, Collider(w=32, h=32))

# ==== 產生幾隻怪物 ====
for i in range(8):
    e = esper.create_entity()
    esper.add_component(e, Position(x=200 + i*90, y=200 + (i%3)*80))
    esper.add_component(e, Velocity(speed=80))
    esper.add_component(e, AI())
    surf = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (200,50,50), [(16,0),(0,32),(32,32)])
    esper.add_component(e, Renderable(image=surf, color=(200,50,50), layer=1))
    esper.add_component(e, Health(max_hp=50, current_hp=50))
    esper.add_component(e, Combat(damage=12, collision_cooldown=0.5))
    esper.add_component(e, Collider(w=32, h=32))

running = True
while running:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    screen.fill((30, 30, 40))

    # 簡單相機跟隨玩家
    # 在全域模式下，使用 esper.component_for_entity
    player_pos = esper.component_for_entity(player, Position)
    camera_x = player_pos.x - SCREEN_W//2
    camera_y = player_pos.y - SCREEN_H//2
    
    # 【重要修正】: 呼叫全域的 esper.process() 函式
    esper.process(dt,
                  screen=screen,
                  camera_offset=(camera_x, camera_y))

    # 顯示 FPS
    fps = clock.get_fps()
    font = pygame.font.SysFont("consolas", 20)
    screen.blit(font.render(f"FPS: {fps:.1f}", True, (255,255,0)), (10,10))

    pygame.display.flip()

pygame.quit()