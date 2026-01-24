# Project Architecture Refactoring

## 1. Directory Structure Setup
- [x] Create `.github/workflows/`
- [x] Create `assets/images`, `assets/audio`, `assets/fonts`
- [x] Create `data/dungeon_flows`, `data/prefabs`, `data/saves`
- [x] Create `src/alchemy_rpg/core`
- [x] Create `src/alchemy_rpg/ecs/components`, `src/alchemy_rpg/ecs/systems`
- [x] Create `src/alchemy_rpg/dungeon/algorithms`
- [x] Create `src/alchemy_rpg/ui/menus`
- [x] Create `src/alchemy_rpg/utils`

## 2. Core Infrastructure implementation
- [x] Implement `src/alchemy_rpg/core/engine.py` (Game Loop)
- [x] Implement `src/alchemy_rpg/core/event_bus.py`
- [x] Implement `src/alchemy_rpg/core/input.py`
- [x] Implement `src/alchemy_rpg/core/resources.py`
- [x] Implement `src/alchemy_rpg/core/state_machine.py`

## 3. ECS Layer Migration
- [x] Implement `src/alchemy_rpg/ecs/world.py`
- [x] Implement `src/alchemy_rpg/ecs/prefabs.py`
- [x] Refactor Components:
    - [x] `src/alchemy_rpg/ecs/components/common.py`
    - [x] `src/alchemy_rpg/ecs/components/combat.py`
    - [x] `src/alchemy_rpg/ecs/components/interaction.py`
    - [x] `src/alchemy_rpg/ecs/components/skills.py`
- [x] Refactor Systems:
    - [x] `src/alchemy_rpg/ecs/systems/movement.py`
    - [x] `src/alchemy_rpg/ecs/systems/render.py`
    - [x] `src/alchemy_rpg/ecs/systems/combat.py`
    - [x] `src/alchemy_rpg/ecs/systems/ai.py`
    - [ ] `src/alchemy_rpg/ecs/systems/skill.py`

## 4. Dungeon System Migration
- [x] Implement `src/alchemy_rpg/dungeon/loader.py`
- [x] Implement `src/alchemy_rpg/dungeon/context.py`
- [x] Implement `src/alchemy_rpg/dungeon/pipeline.py`
- [x] Refactor Algorithms:
    - [x] `src/alchemy_rpg/dungeon/algorithms/registry.py`
    - [ ] `src/alchemy_rpg/dungeon/algorithms/bsp.py`
    - [ ] `src/alchemy_rpg/dungeon/algorithms/automata.py`
    - [ ] `src/alchemy_rpg/dungeon/algorithms/graph.py`
- [x] Implement `src/alchemy_rpg/dungeon/tiles.py`

## 5. UI System Migration
- [x] Implement `src/alchemy_rpg/ui/manager.py`
- [x] Implement `src/alchemy_rpg/ui/base.py`
- [ ] Refactor Menus:
    - [ ] `src/alchemy_rpg/ui/menus/hud.py`
    - [ ] `src/alchemy_rpg/ui/menus/inventory.py`
    - [ ] `src/alchemy_rpg/ui/menus/alchemy.py`
    - [ ] `src/alchemy_rpg/ui/menus/skill_tree.py`

## 6. Data & Utils
- [x] Move/Refactor utils to `src/alchemy_rpg/utils/math.py`, `logger.py`
- [ ] Create JSON data files in `data/`

## 7. Cleanup
- [ ] Remove old source files
- [ ] Update `main.py`
