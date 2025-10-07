# src/utils/helpers.py
import os

def get_project_path(*subpaths):
    """Get the absolute path to the project root (roguelike_dungeon/) and join subpaths."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(project_root, *subpaths)