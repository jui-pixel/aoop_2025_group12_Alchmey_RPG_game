# Project Restructure TODO

## Phase 1: Setup

- [ ] Create `pyproject.toml` with package configuration
- [ ] Update `.gitignore` to include `data/saves/`
- [ ] Create new directory structure under `src/alchemy_rpg/`

## Phase 2: Directory Creation

- [ ] Create `src/alchemy_rpg/core/`
- [ ] Create `src/alchemy_rpg/dungeon/algorithms/`
- [ ] Create `src/alchemy_rpg/dungeon/builder/`
- [ ] Create `src/alchemy_rpg/dungeon/tiles/`
- [ ] Create `src/alchemy_rpg/ecs/components/`
- [ ] Create `src/alchemy_rpg/ecs/systems/`
- [ ] Create `src/alchemy_rpg/ecs/assemblages/`
- [ ] Create `src/alchemy_rpg/scenes/`
- [ ] Create `src/alchemy_rpg/services/`
- [ ] Create `src/alchemy_rpg/utils/`

## Phase 3: File Migration

### Core Module
- [ ] Move `src/core/config.py` → `src/alchemy_rpg/core/config.py`
- [ ] Move `src/core/game.py` → `src/alchemy_rpg/core/game.py`
- [ ] Create `src/alchemy_rpg/core/__init__.py`

### Dungeon Module
- [ ] Move `src/dungeon/algorithms/` → `src/alchemy_rpg/dungeon/algorithms/`
- [ ] Move `src/dungeon/builder/` → `src/alchemy_rpg/dungeon/builder/`
- [ ] Move `src/dungeon/config/` → `src/alchemy_rpg/dungeon/config/`
- [ ] Move `src/dungeon/generators/` → merge into algorithms
- [ ] Move `src/dungeon/managers/` → `src/alchemy_rpg/dungeon/`
- [ ] Move `src/dungeon/*.py` → `src/alchemy_rpg/dungeon/`
- [ ] Create `src/alchemy_rpg/dungeon/tiles/` with tile definitions

### ECS Module
- [ ] Move `src/ecs/components.py` → `src/alchemy_rpg/ecs/components/`
- [ ] Move `src/ecs/systems.py` → `src/alchemy_rpg/ecs/systems/`
- [ ] Move `src/ecs/ai.py` → `src/alchemy_rpg/ecs/systems/ai.py`
- [ ] Move `src/buffs/` → `src/alchemy_rpg/ecs/components/buffs/`
- [ ] Move `src/skills/` → `src/alchemy_rpg/ecs/components/skills/`

### Assemblages (from entities/)
- [ ] Move `src/entities/` → `src/alchemy_rpg/ecs/assemblages/`
- [ ] Rename/restructure prefab files

### Services (from manager/)
- [ ] Move `src/manager/audio_manager.py` → `src/alchemy_rpg/services/`
- [ ] Move `src/manager/dungeon_manager.py` → `src/alchemy_rpg/services/`
- [ ] Move `src/manager/entity_manager.py` → `src/alchemy_rpg/services/`
- [ ] Move `src/manager/event_manager.py` → `src/alchemy_rpg/services/`
- [ ] Move `src/manager/menu_manager.py` → `src/alchemy_rpg/services/`
- [ ] Move `src/manager/render_manager.py` → `src/alchemy_rpg/services/`
- [ ] Move `src/manager/storage_manager.py` → `src/alchemy_rpg/services/`
- [ ] Create `src/alchemy_rpg/services/__init__.py`

### Scenes (from menu/)
- [ ] Move `src/menu/` → `src/alchemy_rpg/scenes/`
- [ ] Rename menu classes to Scene classes where appropriate

### Utils Module
- [ ] Move `src/utils/` → `src/alchemy_rpg/utils/`

## Phase 4: Import Updates

- [ ] Update all imports in `src/alchemy_rpg/core/`
- [ ] Update all imports in `src/alchemy_rpg/dungeon/`
- [ ] Update all imports in `src/alchemy_rpg/ecs/`
- [ ] Update all imports in `src/alchemy_rpg/scenes/`
- [ ] Update all imports in `src/alchemy_rpg/services/`
- [ ] Update all imports in `src/alchemy_rpg/utils/`
- [ ] Update `main.py` entry point

## Phase 5: Cleanup

- [ ] Remove old directories (`src/core/`, `src/dungeon/`, etc.)
- [ ] Update `tests/` imports
- [ ] Run tests to verify
- [ ] Run game to verify functionality

## Phase 6: Documentation

- [ ] Update `README.md` with new structure
- [ ] Add architecture diagram to `docs/architecture/`
