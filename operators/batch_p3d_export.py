"""
Batch P3D Export Tool for DayZ Asset Tools Extension
Exports each selected mesh as an individual P3D file
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

    def prepare_object_for_export(self, obj, temp_collection):
        """Prepare a single object for P3D export"""
        # Duplicate the object to avoid modifying the original
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        temp_collection.objects.link(new_obj)
        
        # Ensure object is in object mode
        bpy.context.view_layer.objects.active = new_obj
        if new_obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Set up LOD properties if needed
        if not self.setup_lod_properties(new_obj):
            self.report({'WARNING'}, f"Could not set up LOD properties for {obj.name}")
            return None
            
        # Apply modifiers if requested
        if self.apply_modifiers:
            self.apply_object_modifiers(new_obj)
            
        # Apply transforms if requested
        if self.apply_transforms:
            self.apply_object_transforms(new_obj)
            
        # Validate mesh if requested
        if self.validate_meshes:
            new_obj.data.validate(clean_customdata=False)
            
        return new_obj

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
        objects = [obj for obj in temp.objects]
        while objects:
            bpy.data.objects.remove(objects.pop())
        
        return temp

    def cleanup_temp_collection(self, temp):
        """Clean up the temporary collection"""
        temp_objects = [obj for obj in temp.objects]
        while temp_objects:
            obj = temp_objects.pop()
            if obj.data:
                bpy.data.meshes.remove(obj.data)
            bpy.data.objects.remove(obj)

        bpy.data.collections.remove(temp)

    def export_single_object(self, context, obj, export_dir, temp_collection):
        """Export a single object as P3D file"""
        try:
            # Prepare object for export
            export_obj = self.prepare_object_for_export(obj, temp_collection)
            if not export_obj:
                return False, f"Failed to prepare {obj.name} for export"
            
            # Generate filename
            filename = self.get_filename(obj)
            filepath = os.path.join(export_dir, filename)
            
            # Ensure the object is selected and active
            bpy.ops.object.select_all(action='DESELECT')
            export_obj.select_set(True)
            context.view_layer.objects.active = export_obj
            
            # Check if Arma 3 Object Builder addon is available
            if 'io_scene_p3d' not in bpy.context.preferences.addons:
                return False, "Arma 3 Object Builder addon not found. Please install it first."
            
            # Try to export using the P3D exporter
            try:
                # Use the actual P3D export operator if available
                if hasattr(bpy.ops.a3ob, 'export_p3d'):
                    bpy.ops.a3ob.export_p3d(
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
                    return True, f"Successfully exported {filename}"
                else:
                    return False, "P3D export operator not available"
                    
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
        
        try:
            # Track results
            successful_exports = 0
            failed_exports = []
            
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
                while temp_objects:
                    obj = temp_objects.pop()
                    if obj.data:
                        bpy.data.meshes.remove(obj.data)
                    bpy.data.objects.remove(obj)
            
            context.window_manager.progress_end()
            
            # Report final results
            if successful_exports > 0:
                self.report({'INFO'}, f"Successfully exported {successful_exports} objects to P3D files")
            
            if failed_exports:
                self.report({'WARNING'}, f"{len(failed_exports)} exports failed")
                for obj_name, error in failed_exports[:5]:  # Show first 5 errors
                    self.report({'ERROR'}, f"{obj_name}: {error}")
                if len(failed_exports) > 5:
                    self.report({'ERROR'}, f"... and {len(failed_exports) - 5} more errors")
            
            if successful_exports == 0:
                return {'CANCELLED'}
            
        finally:
            # Clean up
            self.cleanup_temp_collection(temp_collection)
        
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        
        # Export options
        box = layout.box()
        box.label(text="Export Options", icon='EXPORT')
        box.prop(self, "use_selection")
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