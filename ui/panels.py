import bpy

class DAYZ_UL_NamedPropertiesList(bpy.types.UIList):
    """UIList for named properties"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=f"{index + 1}:", icon='PROPERTIES')
            row.label(text=f"{item.name or '(empty)'} = {item.value or '(empty)'}")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name or f"Property {index + 1}")

class DAYZ_UL_TargetObjectsList(bpy.types.UIList):
    """UIList for target objects"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            if item.obj:
                row.label(text=f"{index + 1}: {item.obj.name}", icon='OBJECT_DATA')
            else:
                row.label(text=f"{index + 1}: (No Object)", icon='ERROR')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            if item.obj:
                layout.label(text=item.obj.name, icon='OBJECT_DATA')
            else:
                layout.label(text=f"Target {index + 1}", icon='ERROR')

class DAYZ_UL_GrassObjectsList(bpy.types.UIList):
    """UIList for grass objects"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            if item.obj:
                row.label(text=f"{index + 1}: {item.obj.name}", icon='MESH_DATA')
                row.prop(item, "weight", text="Weight", slider=True)
            else:
                row.label(text=f"{index + 1}: (No Object)", icon='ERROR')
                row.prop(item, "weight", text="Weight", slider=True)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            if item.obj:
                layout.label(text=item.obj.name, icon='MESH_DATA')
            else:
                layout.label(text=f"Grass {index + 1}", icon='ERROR')

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
        
        row = box.row(align=True)
        row.operator("dayz.add_named_property", text="Add", icon='ADD')
        
        remove_row = row.row(align=True)
        remove_row.enabled = len(settings.named_properties) > 0
        remove_row.operator("dayz.remove_named_property", text="Remove", icon='REMOVE')
        
        if settings.named_properties:
            box.template_list(
                "DAYZ_UL_NamedPropertiesList", "",
                settings, "named_properties",
                settings, "named_properties_index",
                rows=3
            )
            
            if 0 <= settings.named_properties_index < len(settings.named_properties):
                selected_prop = settings.named_properties[settings.named_properties_index]
                prop_box = box.box()
                prop_box.label(text="Edit Selected Property:", icon='GREASEPENCIL')
                
                col = prop_box.column()
                col.prop(selected_prop, "name", text="Property Name")
                col.prop(selected_prop, "value", text="Property Value")
        else:
            box.label(text="No properties added", icon='INFO')

        layout.separator()

        # Process Button
        row = layout.row()
        row.scale_y = 2.0
        
        if not settings.target_directory or not settings.named_properties:
            row.enabled = False
        
        row.operator("dayz.process_batch_properties", text="Process", icon='PLAY')
        
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
        
        row = box.row(align=True)
        row.operator("dayz.add_target_object", text="Add", icon='ADD')
        remove_row = row.row(align=True)
        remove_row.enabled = len(settings.target_objects) > 0
        remove_row.operator("dayz.remove_target_object", text="Remove", icon='REMOVE')
        
        row = box.row(align=True)
        row.operator("dayz.add_selected_to_targets", text="Add Selected", icon='PLUS')
        clear_row = row.row(align=True)
        clear_row.enabled = len(settings.target_objects) > 0
        clear_row.operator("dayz.clear_target_objects", text="Clear", icon='X')
        
        if settings.target_objects:
            box.template_list(
                "DAYZ_UL_TargetObjectsList", "",
                settings, "target_objects",
                settings, "target_objects_index",
                rows=3
            )
            
            if 0 <= settings.target_objects_index < len(settings.target_objects):
                selected_target = settings.target_objects[settings.target_objects_index]
                target_box = box.box()
                target_box.prop(selected_target, "obj", text="Target Object")
        else:
            box.label(text="No targets set", icon='INFO')

        layout.separator()

        # Grass Objects Section
        box = layout.box()
        box.label(text="Grass Objects", icon='MESH_DATA')
        
        row = box.row(align=True)
        row.operator("dayz.add_grass_object", text="Add", icon='ADD')
        remove_row = row.row(align=True)
        remove_row.enabled = len(settings.grass_objects) > 0
        remove_row.operator("dayz.remove_grass_object", text="Remove", icon='REMOVE')

        row = box.row(align=True)
        row.operator("dayz.add_selected_to_grass", text="Add Selected", icon='PLUS')
        clear_row = row.row(align=True)
        clear_row.enabled = len(settings.grass_objects) > 0
        clear_row.operator("dayz.clear_grass_objects", text="Clear", icon='X')
        
        if settings.grass_objects:
            box.template_list(
                "DAYZ_UL_GrassObjectsList", "",
                settings, "grass_objects",
                settings, "grass_objects_index",
                rows=3
            )
            
            if 0 <= settings.grass_objects_index < len(settings.grass_objects):
                selected_grass = settings.grass_objects[settings.grass_objects_index]
                grass_box = box.box()
                grass_box.label(text="Edit Selected Grass:", icon='GREASEPENCIL')
                
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
        col.prop(settings, "use_density_mode")
        
        row = col.row()
        row.enabled = settings.use_density_mode
        row.prop(settings, "density")
        
        row = col.row()
        row.enabled = not settings.use_density_mode
        row.prop(settings, "total_count")
        
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

# Panel for the batch P3D export tool
class DAYZ_PT_BatchP3DPanel(bpy.types.Panel):
    """Batch P3D export panel within DayZ tools"""
    bl_label = "Batch P3D Export"
    bl_idname = "DAYZ_PT_batch_p3d_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DayZ Tools'
    bl_parent_id = "DAYZ_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        
        # Info section
        box = layout.box()
        box.label(text="Export Individual P3D Files", icon='EXPORT')
        
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        total_meshes = len([obj for obj in context.scene.objects if obj.type == 'MESH'])
        
        col = box.column()
        col.label(text=f"Selected meshes: {len(selected_meshes)}", icon='OBJECT_DATA')
        col.label(text=f"Total meshes in scene: {total_meshes}", icon='SCENE_DATA')
        
        layout.separator()
        
        # Export button
        row = layout.row()
        row.scale_y = 2.0
        
        if selected_meshes:
            row.operator("dayz.batch_export_p3d", text=f"Export {len(selected_meshes)} Objects as P3D", icon='EXPORT')
        else:
            row.operator("dayz.batch_export_p3d", text="Export All Meshes as P3D", icon='EXPORT')
        
        # Requirements info
        layout.separator()
        box = layout.box()
        box.label(text="Requirements:", icon='INFO')
        col = box.column(align=True)
        col.label(text="• Arma 3 Object Builder addon", icon='DOT')
        col.label(text="• Objects should be manifold meshes", icon='DOT')
        col.label(text="• Materials should be properly set up", icon='DOT')

# Panel for the Texturing & UV Mapping tools
class DAYZ_PT_TexturingUVPanel(bpy.types.Panel):
    """Texturing & UV Mapping panel within DayZ tools"""
    bl_label = "Texturing & UV Mapping"
    bl_idname = "DAYZ_PT_texturing_uv_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DayZ Tools'
    bl_parent_id = "DAYZ_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        
        # UV Cleanup section
        box = layout.box()
        box.label(text="UV Map Cleanup", icon='GROUP_UVS')
        
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        col = box.column()
        if selected_meshes:
            col.label(text=f"Selected mesh objects: {len(selected_meshes)}", icon='OBJECT_DATA')
            
            # Show UV map info for selected objects
            total_uv_maps = 0
            for obj in selected_meshes[:3]:  # Show info for first 3 objects
                if obj.data.uv_layers:
                    uv_count = len(obj.data.uv_layers)
                    total_uv_maps += uv_count
                    col.label(text=f"  {obj.name}: {uv_count} UV maps", icon='DOT')
                else:
                    col.label(text=f"  {obj.name}: No UV maps", icon='DOT')
            
            if len(selected_meshes) > 3:
                col.label(text=f"  ... and {len(selected_meshes) - 3} more objects", icon='DOT')
        else:
            col.label(text="No mesh objects selected", icon='INFO')
        
        layout.separator()
        
        # Clean UV Maps button
        row = layout.row()
        row.scale_y = 1.5
        row.enabled = len(selected_meshes) > 0
        row.operator("dayz.clean_empty_uv_maps", text="Clean Empty UV Maps", icon='TRASH')
        
        # Info section
        layout.separator()
        box = layout.box()
        box.label(text="UV Cleanup Info:", icon='INFO')
        col = box.column(align=True)
        col.label(text="• Removes UV maps with all coordinates at (0,0)", icon='DOT')
        col.label(text="• Preserves at least one UV map per object", icon='DOT')
        col.label(text="• Safe operation - won't break your models", icon='DOT')
        col.label(text="• Works on selected mesh objects only", icon='DOT')

# Register panels
panels = (
    DAYZ_UL_NamedPropertiesList,
    DAYZ_UL_TargetObjectsList,
    DAYZ_UL_GrassObjectsList,
    DAYZ_PT_main_panel,
    DAYZ_PT_GrassPlacerPanel,
    DAYZ_PT_BatchPropertiesPanel,
    DAYZ_PT_BatchP3DPanel,
    DAYZ_PT_TexturingUVPanel,
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