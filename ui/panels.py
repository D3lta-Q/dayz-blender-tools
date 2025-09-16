import bpy

class DAYZ_UL_NamedPropertiesList(bpy.types.UIList):
    """UIList for named properties"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "name", text="", emboss=False)
            row.label(text="=")
            row.prop(item, "value", text="", emboss=False)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name)

class DAYZ_UL_GrassObjectsList(bpy.types.UIList):
    """UIList for grass objects"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            if item.obj:
                row.prop(item.obj, "name", text="", emboss=False, icon='MESH_DATA')
                row.prop(item, "weight", text="", slider=True)
            else:
                row.label(text="(No Object)", icon='ERROR')
                row.prop(item, "weight", text="", slider=True)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            if item.obj:
                layout.label(text=item.obj.name, icon='MESH_DATA')
            else:
                layout.label(text="(No Object)", icon='ERROR')

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
        
        # Only enable remove if there are items and one is selected
        remove_op = row.operator("dayz.remove_named_property", text="Remove", icon='REMOVE')
        remove_op.enabled = len(settings.named_properties) > 0
        
        # UIList for named properties
        if settings.named_properties:
            box.template_list(
                "DAYZ_UL_NamedPropertiesList", "",  # UIList class and identifier
                settings, "named_properties",       # Collection object and property
                settings, "named_properties_index", # Active index object and property
                rows=3                              # Minimum rows to display
            )
            
            # Show details for selected property
            if 0 <= settings.named_properties_index < len(settings.named_properties):
                selected_prop = settings.named_properties[settings.named_properties_index]
                prop_box = box.box()
                prop_box.label(text="Edit Selected Property:", icon='EDIT')
                
                col = prop_box.column()
                col.prop(selected_prop, "name", text="Property Name")
                col.prop(selected_prop, "value", text="Property Value")
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
        
        # Only enable remove if there are items
        remove_op = row.operator("dayz.remove_grass_object", text="Remove", icon='REMOVE')
        remove_op.enabled = len(settings.grass_objects) > 0
        
        # UIList for grass objects
        if settings.grass_objects:
            box.template_list(
                "DAYZ_UL_GrassObjectsList", "",     # UIList class and identifier
                settings, "grass_objects",          # Collection object and property
                settings, "grass_objects_index",    # Active index object and property
                rows=3                              # Minimum rows to display
            )
            
            # Show details for selected grass object
            if 0 <= settings.grass_objects_index < len(settings.grass_objects):
                selected_grass = settings.grass_objects[settings.grass_objects_index]
                grass_box = box.box()
                grass_box.label(text="Edit Selected Grass:", icon='EDIT')
                
                col = grass_box.column()
                col.prop(selected_grass, "obj", text="Grass Object")
                col.prop(selected_grass, "weight", text="Weight", slider=True)
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
    DAYZ_UL_NamedPropertiesList,    # Add the UIList classes
    DAYZ_UL_GrassObjectsList,
    DAYZ_PT_main_panel,
    DAYZ_PT_GrassPlacerPanel,
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