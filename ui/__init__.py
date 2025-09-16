"""
UI module for DayZ Asset Tools
"""

from .panels import register as register_panels, unregister as unregister_panels

def register():
    """Register all UI components"""
    register_panels()

def unregister():
    """Unregister all UI components"""
    unregister_panels()