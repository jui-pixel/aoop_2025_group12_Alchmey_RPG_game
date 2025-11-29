# src/entities/enemy/enemy1.py (Refactored)

from abc import ABC, abstractmethod
from typing import List, Tuple, Callable, Dict, Optional, Any
import math
import pygame
import random
# 引入 ECS 組件
import esper
from src.ecs.components import Position, Velocity, Health, Combat, AI, Collider, Renderable
from src.config import TILE_SIZE, RED, PASSABLE_TILES
from src.entities.bullet.bullet import Bullet
from src.entities.bullet.expand_circle_bullet import ExpandingCircleBullet
from src.buffs.element_buff import ELEMENTAL_BUFFS










# --- 實體工廠函式 (取代原 Enemy1 類) ---



# --- 3. 創建 AISystem (運行行為樹的 ECS Processor) ---

