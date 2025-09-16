"""
Operators module for DayZ Asset Tools
"""

from .grass_placer import register_grass_placer, unregister_grass_placer
from .batch_properties import register_batch_properties, unregister_batch_properties

def register():
    """Register all operators"""
    register_grass_placer()
    register_batch_properties()

def unregister():
    """Unregister all operators"""
    unregister_grass_placer()
    unregister_batch_properties()