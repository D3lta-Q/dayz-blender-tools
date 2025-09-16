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

def register():
    print("DayZ Asset Tools: Starting registration...")
    
    try:
        from . import operators, ui
        operators.register()
        ui.register()
        print("DayZ Asset Tools: Registration successful!")
    except Exception as e:
        print(f"DayZ Asset Tools: Registration failed - {e}")
        raise e

def unregister():
    print("DayZ Asset Tools: Starting unregistration...")
    
    try:
        from . import operators, ui
        operators.unregister()
        ui.unregister()
        print("DayZ Asset Tools: Unregistration successful!")
    except Exception as e:
        print(f"DayZ Asset Tools: Unregistration failed - {e}")

if __name__ == "__main__":
    register()