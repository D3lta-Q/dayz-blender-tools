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

class DAYZ_PT_BatchPropertiesPanel(bpy.types.Panel):
    """Batch Add Named Properties panel within DayZ tools"""
    bl_label = "Batch Add Named Properties"
    bl_idname = "DAYZ_PT_batch_properties_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DayZ Tools'
    bl_parent_id = "DAYZ_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.dayz_batch_properties_settings

        # Target Directory Section
        box = layout.box()
        box.label(text="Target Directory", icon='FOLDER_REDIRECT')
        
        col = box.column()
        row = col.row()
        row.prop(settings, "target_directory", text="")
        row.operator("dayz.select_directory", text="", icon='FILEBROWSER')
        
        col.prop(settings, "recursive_search")

        layout.separator()

        # Named Properties Section
        box = layout.box()
        box.label(text="Named Properties", icon='PROPERTIES')
        
        row = box.row()
        row.operator("dayz.add_named_property", text="Add", icon='ADD')
        row.operator("dayz.remove_named_property", text="Remove", icon='REMOVE')
        
        # Show named properties
        if settings.named_properties:
            for i, prop_item in enumerate(settings.named_properties):
                prop_box = box.box()
                
                row = prop_box.row()
                row.label(text=f"Property {i+1}:")
                
                col = prop_box.column()
                col.prop(prop_item, "name", text="Name")
                col.prop(prop_item, "value", text="Value")
        else:
            box.label(text="No properties added", icon='INFO')

        layout.separator()

        # Process Button
        row = layout.row()
        row.scale_y = 2.0
        
        # Enable/disable button based on settings
        if not settings.target_directory or not settings.named_properties:
            row.enabled = False
        
        row.operator("dayz.process_batch_properties", text="Process", icon='PLAY')
        
        # Show status info
        if not settings.target_directory:
            layout.label(text="Select target directory", icon='ERROR')
        elif not settings.named_properties:
            layout.label(text="Add at least one property", icon='ERROR')

class DAYZ_PT_GrassPlacerPanel(bpy.types.Panel):
    """Grass placer panel within DayZ tools"""
    bl_label = "Grass Placer"
    bl_idname = "DAYZ_PT_grass_placer_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DayZ Tools'
    bl_parent_id = "DAYZ_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.dayz_grass_placer_settings

        # Target Objects Section
        box = layout.box()
        box.label(text="Target Objects", icon='SURFACE_DATA')
        box.operator("dayz.set_grass_targets", text="Set Selected as Targets", icon='PLUS')
        
        if settings.target_objects:
            col = box.column()
            for target in settings.target_objects:
                if target.obj:
                    col.label(text=f"• {target.obj.name}", icon='OBJECT_DATA')
                else:
                    col.label(text="• (Missing Object)", icon='ERROR')
        else:
            box.label(text="No targets set", icon='INFO')

        layout.separator()

        # Grass Objects Section
        box = layout.box()
        box.label(text="Grass Objects", icon='MESH_DATA')
        
        row = box.row()
        row.operator("dayz.add_grass_object", text="Add", icon='ADD')
        row.operator("dayz.remove_grass_object", text="Remove", icon='REMOVE')
        
        # Show grass objects with proper object selectors
        if settings.grass_objects:
            for i, grass_item in enumerate(settings.grass_objects):
                item_box = box.box()
                row = item_box.row()
                
                # Object selector with eyedropper
                row.prop(grass_item, "obj", text=f"Grass {i+1}")
                
                # Weight slider
                weight_row = item_box.row()
                weight_row.prop(grass_item, "weight", text="Weight", slider=True)
        else:
            box.label(text="No grass objects added", icon='INFO')

        layout.separator()

        # Placement Settings
        box = layout.box()
        box.label(text="Placement Settings", icon='SETTINGS')
        
        col = box.column()
        col.prop(settings, "total_count")
        col.prop(settings, "surface_offset")
        col.prop(settings, "distribution_seed")

        layout.separator()

        # Distribution Settings
        box = layout.box()
        box.label(text="Distribution", icon='FORCE_TURBULENCE')
        
        col = box.column()
        col.prop(settings, "clumping_factor", slider=True)

        layout.separator()

        # Variation Settings
        box = layout.box()
        box.label(text="Variation", icon='MODIFIER_DATA')
        
        col = box.column()
        row = col.row(align=True)
        row.prop(settings, "scale_min")
        row.prop(settings, "scale_max")
        col.prop(settings, "random_rotation")

        layout.separator()

        # Organization
        box = layout.box()
        box.label(text="Organization", icon='OUTLINER')
        
        col = box.column()
        col.prop(settings, "parent_to_empty")
        
        col.separator()
        col.label(text="Merge Options:")
        col.prop(settings, "merge_all_grass")
        col.prop(settings, "merge_by_variant")
        
        if settings.merge_all_grass:
            col.label(text="Significantly increases processing time", icon='ERROR')

        layout.separator()

        # Generate Button
        row = layout.row()
        row.scale_y = 2.0
        row.operator("dayz.generate_grass", text="Generate Grass", icon='MOD_PARTICLES')

# Register panels
panels = (
    DAYZ_PT_main_panel,
    DAYZ_PT_GrassPlacerPanel,  # Add the grass panel here
    DAYZ_PT_BatchPropertiesPanel,
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