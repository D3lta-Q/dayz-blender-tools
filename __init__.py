bl_info = {
    "name": "Delta's DayZ Asset Tools",
    "author": "DeltaQ",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > DayZ Asset Tools",
    "description": "A collection of various tools to help automate/streamline the process of configuring 3D assets to be imported into DayZ.",
    "category": "Import-Export",
    "license": "GPL-3.0-or-later",
}

import bpy
from . import operators, ui

def register():
    operators.register()
    ui.register()

def unregister():
    operators.unregister()
    ui.unregister()

if __name__ == "__main__":
    register()