"""
Algorithm Registry - 裝飾器註冊系統用於地牢生成算法。
"""
from typing import Dict, Callable, Any

# Registry storage
_algorithms: Dict[str, Callable] = {}

def register_algorithm(name: str):
    """Decorator to register a generation algorithm."""
    def decorator(func: Callable):
        _algorithms[name] = func
        return func
    return decorator

def get_algorithm(name: str) -> Callable:
    """Get a registered algorithm by name."""
    if name not in _algorithms:
        raise KeyError(f"Algorithm '{name}' not found. Available: {list(_algorithms.keys())}")
    return _algorithms[name]

def list_algorithms() -> list:
    """List all registered algorithm names."""
    return list(_algorithms.keys())

# Example usage:
# @register_algorithm("bsp")
# def bsp_generate(context):
#     ...
