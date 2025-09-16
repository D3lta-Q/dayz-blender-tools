"""
Batch Properties Tool for DayZ Asset Tools Extension
Adds named properties to .p3d files in a directory
"""

import bpy
import os
from bpy.props import StringProperty, BoolProperty, CollectionProperty, IntProperty
from bpy_extras.io_utils import ImportHelper

# Property Groups
class DAYZ_NamedProperty(bpy.types.PropertyGroup):
    """Named property for batch processing"""
    name: bpy.props.StringProperty(
        name="Property Name",
        description="Name of the property to add",
        default="lodnoshadow"
    )
    
    value: bpy.props.StringProperty(
        name="Property Value", 
        description="Value of the property to add",
        default="1"
    )

class DAYZ_BatchPropertiesSettings(bpy.types.PropertyGroup):
    """Batch properties settings"""
    
    target_directory: bpy.props.StringProperty(
        name="Target Directory",
        description="Directory containing .p3d files to process",
        default="",
        subtype='DIR_PATH'
    )
    
    recursive_search: bpy.props.BoolProperty(
        name="Recursive Search",
        description="Search subdirectories for .p3d files",
        default=True
    )
    
    # Named properties collection
    named_properties: bpy.props.CollectionProperty(
        type=DAYZ_NamedProperty
    )
    
    named_properties_index: bpy.props.IntProperty(default=0)

# Operators
class DAYZ_OT_AddNamedProperty(bpy.types.Operator):
    """Add a new named property slot"""
    bl_idname = "dayz.add_named_property"
    bl_label = "Add Property"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.dayz_batch_properties_settings
        new_prop = settings.named_properties.add()
        new_prop.name = "lodnoshadow"
        new_prop.value = "1"
        settings.named_properties_index = len(settings.named_properties) - 1
        return {'FINISHED'}

class DAYZ_OT_RemoveNamedProperty(bpy.types.Operator):
    """Remove selected named property slot"""
    bl_idname = "dayz.remove_named_property"
    bl_label = "Remove Property"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not hasattr(context.scene, 'dayz_batch_properties_settings'):
            return False
        settings = context.scene.dayz_batch_properties_settings
        return len(settings.named_properties) > 0

    def execute(self, context):
        settings = context.scene.dayz_batch_properties_settings
        index = settings.named_properties_index
        
        if 0 <= index < len(settings.named_properties):
            settings.named_properties.remove(index)
            settings.named_properties_index = max(0, index - 1)
        
        return {'FINISHED'}

class DAYZ_OT_SelectDirectory(bpy.types.Operator, ImportHelper):
    """Select directory for batch processing"""
    bl_idname = "dayz.select_directory"
    bl_label = "Select Directory"
    bl_description = "Select directory containing .p3d files"
    bl_options = {'REGISTER'}
    
    # Use directory selection
    use_filter_folder = True
    filename_ext = ""
    
    def execute(self, context):
        settings = context.scene.dayz_batch_properties_settings
        # Get directory from selected file path
        settings.target_directory = os.path.dirname(self.filepath)
        return {'FINISHED'}

class DAYZ_OT_ProcessBatchProperties(bpy.types.Operator):
    """Process .p3d files and add named properties"""
    bl_idname = "dayz.process_batch_properties"
    bl_label = "Process"
    bl_description = "Process .p3d files in the target directory and add named properties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.dayz_batch_properties_settings
        
        # Validation
        if not settings.target_directory:
            self.report({'ERROR'}, "No target directory specified")
            return {'CANCELLED'}
        
        if not os.path.isdir(settings.target_directory):
            self.report({'ERROR'}, f"Target directory does not exist: {settings.target_directory}")
            return {'CANCELLED'}
        
        if not settings.named_properties:
            self.report({'ERROR'}, "No named properties defined")
            return {'CANCELLED'}
        
        # Process files
        processed_count = self.process_p3d_files_in_directory(settings.target_directory, settings)
        
        if processed_count > 0:
            self.report({'INFO'}, f"Successfully processed {processed_count} .p3d files")
        else:
            self.report({'WARNING'}, "No .p3d files found or processed")
        
        return {'FINISHED'}
    
    def clear_scene(self):
        """Safely removes all objects and collections from the current scene."""
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
        
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.selected_objects:
            bpy.ops.object.delete()

        for collection in bpy.data.collections:
            if collection.name != "Scene Collection":
                bpy.data.collections.remove(collection)
    
    def process_p3d_files_in_directory(self, directory, settings):
        """Finds and processes all .p3d files in a given directory."""
        p3d_files = []
        
        if settings.recursive_search:
            # Recursive search
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(".p3d"):
                        p3d_files.append(os.path.join(root, file))
        else:
            # Non-recursive search
            try:
                files = os.listdir(directory)
                for file in files:
                    if file.lower().endswith(".p3d"):
                        filepath = os.path.join(directory, file)
                        if os.path.isfile(filepath):
                            p3d_files.append(filepath)
            except OSError as e:
                self.report({'ERROR'}, f"Error reading directory: {e}")
                return 0

        if not p3d_files:
            return 0

        print(f"Found {len(p3d_files)} .p3d file(s) to process...")

        processed_count = 0
        for filepath in p3d_files:
            if self.process_single_p3d(filepath, settings):
                processed_count += 1
        
        print(f"\n--- {processed_count} files processed successfully! ---")
        return processed_count
    
    def process_single_p3d(self, filepath, settings):
        """Imports, modifies, and re-exports a single .p3d file."""
        print(f"\n--- Processing: {os.path.basename(filepath)} ---")

        self.clear_scene()

        try:
            bpy.ops.a3ob.import_p3d(filepath=filepath)
            print(f"  > Imported: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  ! ERROR: Failed to import {filepath}. Skipping. Reason: {e}")
            return False

        main_collection_name = os.path.basename(filepath)
        main_collection = bpy.data.collections.get(main_collection_name)

        if not main_collection:
            print(f"  ! ERROR: Could not find main collection '{main_collection_name}'. Skipping.")
            return False

        visuals_collection = next((coll for coll in main_collection.children if coll.name == "Visuals"), None)

        if not visuals_collection:
            print("  - WARNING: No 'Visuals' collection found. Properties will not be changed.")
            return False
        
        resolution_lods = [obj for obj in visuals_collection.objects if obj.type == 'MESH']
        if not resolution_lods:
            print("  - No meshes found in 'Visuals' collection to modify.")
            return False
        
        modified_count = 0
        for lod_mesh in resolution_lods:
            # Add each named property from settings
            for prop_item in settings.named_properties:
                if not prop_item.name:  # Skip empty property names
                    continue
                
                # Ensure properties collection exists
                if not lod_mesh.a3ob_properties_object.properties:
                    lod_mesh.a3ob_properties_object.properties.add()
                
                # Find existing property or add new one
                existing_prop = None
                for existing in lod_mesh.a3ob_properties_object.properties:
                    if existing.name == prop_item.name:
                        existing_prop = existing
                        break
                
                if existing_prop:
                    existing_prop.value = prop_item.value
                    print(f"    > Updated property '{prop_item.name}' = '{prop_item.value}'")
                else:
                    new_prop = lod_mesh.a3ob_properties_object.properties.add()
                    new_prop.name = prop_item.name
                    new_prop.value = prop_item.value
                    print(f"    > Added property '{prop_item.name}' = '{prop_item.value}'")
            
            modified_count += 1
        
        print(f"  > Modified properties for {modified_count} Resolution LOD(s).")

        # Select objects for export
        bpy.ops.object.select_all(action='DESELECT')
        for obj in main_collection.all_objects:
            obj.select_set(True)

        if bpy.context.selected_objects:
            try:
                bpy.ops.a3ob.export_p3d(filepath=filepath, use_selection=True)
                print(f"  > Successfully exported to: {filepath}")
                return True
            except Exception as e:
                print(f"  ! ERROR: Failed to export {filepath}. Reason: {e}")
                return False
        else:
            print(f"  ! ERROR: No objects were selected for export from '{main_collection_name}'.")
            return False

# Classes to register
batch_properties_classes = (
    DAYZ_NamedProperty,
    DAYZ_BatchPropertiesSettings,
    DAYZ_OT_AddNamedProperty,
    DAYZ_OT_RemoveNamedProperty,
    DAYZ_OT_SelectDirectory,
    DAYZ_OT_ProcessBatchProperties,
)

def register_batch_properties():
    """Register batch properties classes"""
    for cls in batch_properties_classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.dayz_batch_properties_settings = bpy.props.PointerProperty(type=DAYZ_BatchPropertiesSettings)

def unregister_batch_properties():
    """Unregister batch properties classes"""
    if hasattr(bpy.types.Scene, 'dayz_batch_properties_settings'):
        del bpy.types.Scene.dayz_batch_properties_settings
    
    for cls in reversed(batch_properties_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass  # Class wasn't registered