import bpy

class DAYZ_PT_main_panel(bpy.types.Panel):
    bl_label = "DayZ Asset Tools"
    bl_idname = "DAYZ_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DayZ Tools"
    
    def draw(self, context):
        layout = self.layout
        
        # Main tools section
        box = layout.box()
        box.label(text="Asset Tools", icon='TOOL_SETTINGS')
        
        # Placeholder for future tools
        box.label(text="Additional tools will be added here", icon='INFO')

# Register panels
panels = (
    DAYZ_PT_main_panel,
)

def register():
    """Register UI panels"""
    for cls in panels:
        bpy.utils.register_class(cls)

def unregister():
    """Unregister UI panels"""
    for cls in reversed(panels):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass