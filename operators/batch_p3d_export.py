"""
Batch P3D Export Tool for DayZ Asset Tools Extension
Exports each selected mesh as an individual P3D file including proxies
"""

import bpy
import bmesh
import os
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class DAYZ_OT_BatchExportP3D(Operator, ExportHelper):
    """Export each selected mesh as individual P3D files"""
    bl_idname = "dayz.batch_export_p3d"
    bl_label = "Batch Export P3D Files"
    bl_description = "Export each selected mesh object as a separate P3D file"
    bl_options = {'REGISTER', 'UNDO'}

    # ExportHelper properties
    filename_ext = ".p3d"
    filter_glob: StringProperty(
        default="*.p3d",
        options={'HIDDEN'},
        maxlen=255
    )

    # Export options
    use_selection: BoolProperty(
        name="Selected Objects Only",
        description="Export only selected objects",
        default=True,
    )
    
    include_children: BoolProperty(
        name="Include Children/Proxies",
        description="Include child objects (proxies) in the export",
        default=True,
    )
    
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers during export",
        default=True,
    )
    
    apply_transforms: BoolProperty(
        name="Apply Transforms",
        description="Apply object transforms during export",
        default=True,
    )
    
    validate_meshes: BoolProperty(
        name="Validate Meshes",
        description="Run mesh validation before export",
        default=True,
    )
    
    preserve_normals: BoolProperty(
        name="Preserve Normals",
        description="Keep custom split normals",
        default=False,
    )
    
    sort_sections: BoolProperty(
        name="Sort Sections",
        description="Sort material sections for better performance",
        default=True,
    )
    
    force_lowercase: BoolProperty(
        name="Force Lowercase",
        description="Convert all names to lowercase",
        default=True,
    )
    
    relative_paths: BoolProperty(
        name="Relative Paths",
        description="Use relative paths for textures and materials",
        default=True,
    )
    
    naming_convention: EnumProperty(
        name="File Naming",
        description="How to name the exported files",
        items=[
            ('OBJECT_NAME', "Object Name", "Use the object's name as filename"),
            ('MESH_NAME', "Mesh Name", "Use the mesh data name as filename"),
            ('CUSTOM', "Custom Pattern", "Use a custom naming pattern with object name"),
        ],
        default='OBJECT_NAME',
    )
    
    custom_prefix: StringProperty(
        name="Prefix",
        description="Prefix to add to filenames",
        default="",
    )
    
    custom_suffix: StringProperty(
        name="Suffix", 
        description="Suffix to add to filenames (before .p3d)",
        default="",
    )

    @classmethod
    def poll(cls, context):
        # Check if we have mesh objects selected or in scene
        if context.selected_objects:
            return any(obj.type == 'MESH' for obj in context.selected_objects)
        return any(obj.type == 'MESH' for obj in context.scene.objects)

    def get_export_objects(self, context):
        """Get the objects to export based on settings"""
        if self.use_selection:
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        else:
            objects = [obj for obj in context.scene.objects if obj.type == 'MESH']
        
        return objects

    def get_filename(self, obj):
        """Generate filename for an object based on naming convention"""
        if self.naming_convention == 'OBJECT_NAME':
            base_name = obj.name
        elif self.naming_convention == 'MESH_NAME':
            base_name = obj.data.name
        else:  # CUSTOM
            base_name = obj.name
        
        # Clean the name for filesystem
        base_name = self.clean_filename(base_name)
        
        # Add prefix and suffix
        if self.custom_prefix:
            base_name = f"{self.custom_prefix}{base_name}"
        if self.custom_suffix:
            base_name = f"{base_name}{self.custom_suffix}"
            
        return f"{base_name}.p3d"

    def clean_filename(self, name):
        """Clean a name to be filesystem-safe"""
        # Remove or replace invalid characters
        import re
        # Replace spaces and special characters with underscores
        name = re.sub(r'[<>:"/\\|?*\s]', '_', name)
        # Remove multiple underscores
        name = re.sub(r'_+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        return name

    def setup_lod_properties(self, obj):
        """Set up basic LOD properties for objects that don't have them"""
        if not hasattr(obj, 'a3ob_properties_object'):
            return False
            
        props = obj.a3ob_properties_object
        
        # If not set as LOD, make it a geometry LOD
        if not props.is_a3_lod:
            props.is_a3_lod = True
            props.lod = "1.000"  # Geometry LOD
            props.resolution = 1.0
            
        return True

    def get_object_hierarchy(self, obj):
        """Get object and all its children (proxies) recursively"""
        objects = [obj]
        
        # Only include children if the option is enabled
        if self.include_children:
            def get_children_recursive(parent):
                for child in parent.children:
                    objects.append(child)
                    get_children_recursive(child)  # Get children of children
            
            get_children_recursive(obj)
        
        return objects

    def prepare_object_hierarchy_for_export(self, obj, temp_collection):
        """Prepare an object and all its children for P3D export"""
        # Get all objects in the hierarchy (main object + children/proxies)
        hierarchy_objects = self.get_object_hierarchy(obj)
        prepared_objects = []
        
        # Duplicate each object in the hierarchy
        for orig_obj in hierarchy_objects:
            # Duplicate the object to avoid modifying the original
            new_obj = orig_obj.copy()
            if orig_obj.data:
                new_obj.data = orig_obj.data.copy()
            temp_collection.objects.link(new_obj)
            
            # Ensure object is in object mode
            bpy.context.view_layer.objects.active = new_obj
            if new_obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Set up LOD properties for mesh objects
            if orig_obj.type == 'MESH':
                if not self.setup_lod_properties(new_obj):
                    self.report({'WARNING'}, f"Could not set up LOD properties for {orig_obj.name}")
                
                # Apply modifiers if requested (only for mesh objects)
                if self.apply_modifiers:
                    self.apply_object_modifiers(new_obj)
                    
                # Validate mesh if requested (only for mesh objects)
                if self.validate_meshes:
                    new_obj.data.validate(clean_customdata=False)
            
            prepared_objects.append(new_obj)
        
        # Rebuild parent-child relationships in the duplicated objects
        for i, orig_obj in enumerate(hierarchy_objects):
            new_obj = prepared_objects[i]
            
            # Find parent in the prepared objects list
            if orig_obj.parent and orig_obj.parent in hierarchy_objects:
                parent_index = hierarchy_objects.index(orig_obj.parent)
                new_obj.parent = prepared_objects[parent_index]
                new_obj.parent_type = orig_obj.parent_type
                new_obj.parent_bone = orig_obj.parent_bone
        
        # Apply transforms if requested (to all objects in hierarchy)
        if self.apply_transforms:
            for new_obj in prepared_objects:
                self.apply_object_transforms(new_obj)
        
        return prepared_objects

    def apply_object_modifiers(self, obj):
        """Apply all visible modifiers to an object"""
        bpy.context.view_layer.objects.active = obj
        
        # Get modifiers that are visible
        modifiers = [m for m in obj.modifiers if m.show_viewport]
        
        for modifier in modifiers:
            try:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except RuntimeError as e:
                self.report({'WARNING'}, f"Could not apply modifier {modifier.name} on {obj.name}: {str(e)}")

    def apply_object_transforms(self, obj):
        """Apply transforms to an object"""
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        
        try:
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        except RuntimeError as e:
            self.report({'WARNING'}, f"Could not apply transforms to {obj.name}: {str(e)}")

    def create_temp_collection(self, context):
        """Create a temporary collection for export processing"""
        temp_name = "DAYZ_P3D_Export_Temp"
        temp = bpy.data.collections.get(temp_name)
        if temp is None:
            temp = bpy.data.collections.new(temp_name)
            context.scene.collection.children.link(temp)
        
        # Clear any existing objects
        objects_to_remove = [obj for obj in temp.objects]
        for obj in objects_to_remove:
            try:
                temp.objects.unlink(obj)
                if obj.data and obj.data.users <= 1:
                    if obj.type == 'MESH':
                        bpy.data.meshes.remove(obj.data)
                bpy.data.objects.remove(obj)
            except (ReferenceError, RuntimeError):
                pass
        
        return temp

    def cleanup_temp_collection(self, temp):
        """Clean up the temporary collection"""
        # Get list of objects to remove before we start removing them
        objects_to_remove = [obj for obj in temp.objects]
        
        # Remove objects from collection first, then from bpy.data
        for obj in objects_to_remove:
            try:
                # Remove from collection
                if obj.name in temp.objects:
                    temp.objects.unlink(obj)
                # Remove mesh data if it exists and has no other users
                if obj.data and obj.data.users <= 1:
                    if obj.type == 'MESH':
                        mesh_data = obj.data
                        bpy.data.meshes.remove(mesh_data)
                # Remove the object itself
                bpy.data.objects.remove(obj)
            except (ReferenceError, RuntimeError):
                pass  # Object already removed or invalid

        # Remove the collection
        try:
            bpy.data.collections.remove(temp)
        except (ReferenceError, RuntimeError):
            pass

    def export_single_object(self, context, obj, export_dir, temp_collection):
        """Export a single object as P3D file including its children (proxies)"""
        try:
            # Prepare object hierarchy for export
            export_objects = self.prepare_object_hierarchy_for_export(obj, temp_collection)
            if not export_objects:
                return False, f"Failed to prepare {obj.name} hierarchy for export"
            
            # Generate filename
            filename = self.get_filename(obj)
            filepath = os.path.join(export_dir, filename)
            
            # Select all objects in the hierarchy for export
            bpy.ops.object.select_all(action='DESELECT')
            for export_obj in export_objects:
                export_obj.select_set(True)
            
            # Set the main object as active
            context.view_layer.objects.active = export_objects[0]
            
            # Check if Arma 3 Object Builder addon is available
            addon_found = False
            export_operator = None
            
            # Check for different possible addon module names
            possible_addon_names = [
                'arma3objectbuilder',
                'Arma3ObjectBuilder', 
                'a3ob',
                'A3OB'
            ]
            
            for addon_name in possible_addon_names:
                if addon_name in bpy.context.preferences.addons:
                    addon_found = True
                    break
            
            # Also check if the export operator is available directly
            if hasattr(bpy.ops, 'a3ob') and hasattr(bpy.ops.a3ob, 'export_p3d'):
                addon_found = True
                export_operator = bpy.ops.a3ob.export_p3d
            elif hasattr(bpy.ops, 'export_scene') and hasattr(bpy.ops.export_scene, 'p3d'):
                addon_found = True  
                export_operator = bpy.ops.export_scene.p3d
            
            if not addon_found:
                # Let's also check what addons are actually enabled for debugging
                enabled_addons = [addon for addon in bpy.context.preferences.addons.keys()]
                print(f"DEBUG: Enabled addons: {enabled_addons}")
                return False, "Arma 3 Object Builder addon not found. Please install and enable it first."
            
            # Count objects being exported for reporting
            mesh_count = sum(1 for obj in export_objects if obj.type == 'MESH')
            proxy_count = len(export_objects) - mesh_count
            
            # Try to export using the P3D exporter
            try:
                # Try the most likely operator first
                result = None
                if export_operator:
                    result = export_operator(
                        filepath=filepath,
                        use_selection=True,
                        apply_modifiers=False,  # We already applied them
                        apply_transforms=False,  # We already applied them
                        validate_meshes=False,  # We already validated
                        preserve_normals=self.preserve_normals,
                        sort_sections=self.sort_sections,
                        force_lowercase=self.force_lowercase,
                        relative_paths=self.relative_paths,
                    )
                elif hasattr(bpy.ops.a3ob, 'export_p3d'):
                    result = bpy.ops.a3ob.export_p3d(
                        filepath=filepath,
                        use_selection=True,
                        apply_modifiers=False,  # We already applied them
                        apply_transforms=False,  # We already applied them
                        validate_meshes=False,  # We already validated
                        preserve_normals=self.preserve_normals,
                        sort_sections=self.sort_sections,
                        force_lowercase=self.force_lowercase,
                        relative_paths=self.relative_paths,
                    )
                elif hasattr(bpy.ops.export_scene, 'p3d'):
                    result = bpy.ops.export_scene.p3d(
                        filepath=filepath,
                        use_selection=True,
                    )
                else:
                    return False, "P3D export operator not available. The addon may not be properly installed."
                
                # Check if the export was successful
                if result and 'CANCELLED' in result:
                    return False, f"P3D export was cancelled for {obj.name}"
                elif result and 'FINISHED' not in result:
                    return False, f"P3D export failed with result: {result}"
                
                # Create detailed success message
                if proxy_count > 0:
                    return True, f"Successfully exported {filename} (1 mesh + {proxy_count} proxies)"
                else:
                    return True, f"Successfully exported {filename}"
                    
            except AttributeError as e:
                return False, f"P3D export operator not found. Check if Arma 3 Object Builder addon is properly enabled. Error: {str(e)}"
            except Exception as e:
                return False, f"P3D export failed for {obj.name}: {str(e)}"
                
        except Exception as e:
            return False, f"Unexpected error exporting {obj.name}: {str(e)}"

    def execute(self, context):
        # Get export directory
        export_dir = os.path.dirname(self.filepath)
        
        # Get objects to export
        objects = self.get_export_objects(context)
        
        if not objects:
            self.report({'ERROR'}, "No mesh objects found to export")
            return {'CANCELLED'}
        
        # Create temporary collection
        temp_collection = self.create_temp_collection(context)
        
        # Track results
        successful_exports = 0
        failed_exports = []
        
        try:
            # Export each object
            for i, obj in enumerate(objects):
                # Update progress
                context.window_manager.progress_begin(0, len(objects))
                context.window_manager.progress_update(i)
                
                success, message = self.export_single_object(context, obj, export_dir, temp_collection)
                
                if success:
                    successful_exports += 1
                    self.report({'INFO'}, message)
                else:
                    failed_exports.append((obj.name, message))
                    self.report({'WARNING'}, message)
                
                # Clear temp collection for next object
                temp_objects = [obj for obj in temp_collection.objects]
                
                # Remove objects from collection and bpy.data
                for obj in temp_objects:
                    try:
                        # Unlink from collection
                        if obj.name in temp_collection.objects:
                            temp_collection.objects.unlink(obj)
                        # Remove mesh data if it has no other users
                        if obj.data and obj.data.users <= 1 and obj.type == 'MESH':
                            mesh_data = obj.data
                            bpy.data.meshes.remove(mesh_data)
                        # Remove the object
                        bpy.data.objects.remove(obj)
                    except (ReferenceError, RuntimeError):
                        pass  # Object already removed or invalid
            
            context.window_manager.progress_end()
            
        except Exception as e:
            # Handle any unexpected errors in the main execute method
            context.window_manager.progress_end()
            self.report({'ERROR'}, f"Unexpected error during batch export: {str(e)}")
            return {'CANCELLED'}
            
        finally:
            # Clean up temp collection
            try:
                self.cleanup_temp_collection(temp_collection)
            except Exception as cleanup_error:
                # Don't let cleanup errors prevent the operation from completing
                print(f"Warning: Cleanup failed: {cleanup_error}")
        
        # Report final results
        if successful_exports > 0:
            self.report({'INFO'}, f"Successfully exported {successful_exports} objects to P3D files")
        
        if failed_exports:
            self.report({'WARNING'}, f"{len(failed_exports)} exports failed")
            for obj_name, error in failed_exports[:5]:  # Show first 5 errors
                self.report({'ERROR'}, f"{obj_name}: {error}")
            if len(failed_exports) > 5:
                self.report({'ERROR'}, f"... and {len(failed_exports) - 5} more errors")
        
        # Return appropriate result
        if successful_exports == 0:
            return {'CANCELLED'}
        
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        
        # Export options
        box = layout.box()
        box.label(text="Export Options", icon='EXPORT')
        box.prop(self, "use_selection")
        box.prop(self, "include_children")
        box.prop(self, "apply_modifiers")
        box.prop(self, "apply_transforms")
        box.prop(self, "validate_meshes")
        
        # P3D specific options
        box = layout.box()
        box.label(text="P3D Options", icon='MESH_DATA')
        box.prop(self, "preserve_normals")
        box.prop(self, "sort_sections")
        box.prop(self, "force_lowercase")
        box.prop(self, "relative_paths")
        
        # Naming options
        box = layout.box()
        box.label(text="File Naming", icon='FILE')
        box.prop(self, "naming_convention")
        
        if self.naming_convention == 'CUSTOM':
            row = box.row(align=True)
            row.prop(self, "custom_prefix", text="Prefix")
            row.prop(self, "custom_suffix", text="Suffix")

# Classes to register - define BEFORE the functions that use it
batch_p3d_classes = (
    DAYZ_OT_BatchExportP3D,
)

def register_batch_p3d():
    """Register batch P3D export classes"""
    for cls in batch_p3d_classes:
        bpy.utils.register_class(cls)

def unregister_batch_p3d():
    """Unregister batch P3D export classes"""
    for cls in reversed(batch_p3d_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass