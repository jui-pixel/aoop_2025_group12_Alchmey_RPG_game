def create_bullet(game, x, y, direction):
    import esper
    from ...ecs.components import Position, Velocity, Combat, Renderable, Collider, BulletComponent
    
    bullet_id = esper.create_entity()
    
    # 1. 基礎位置和速度
    esper.add_component(bullet_id, Position(x=x, y=y))
    esper.add_component(bullet_id, Velocity(x=direction[0]*300.0, y=direction[1]*300.0, speed=300.0))
    
    # 2. 視覺和碰撞 (使用子彈默認值)
    esper.add_component(bullet_id, Renderable(w=8, h=8, color=(255, 255, 0))) 
    # 注意: pass_wall 來自 Bullet.__init__ 參數
    esper.add_component(bullet_id, Collider(w=8, h=8, pass_wall=False)) 
    
    # 3. 戰鬥屬性 (自定義或來自玩家/技能)
    esper.add_component(bullet_id, Combat(damage=15, max_penetration_count=1, explosion_range=50.0))
    
    # 4. 子彈狀態 (壽命和目標追蹤)
    esper.add_component(bullet_id, BulletComponent(direction=direction, lifetime=3.0))
    
    return bullet_id