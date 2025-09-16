"""
Operators module for DayZ Asset Tools
"""

from .grass_placer import register_grass_placer, unregister_grass_placer

def register():
    """Register all operators"""
    register_grass_placer()

def unregister():
    """Unregister all operators"""
    unregister_grass_placer()