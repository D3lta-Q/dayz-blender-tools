"""
Grass Placer Tool for DayZ Asset Tools Extension
Automates placing grass meshes onto target surfaces with normal alignment
"""

import bpy
import bmesh
import random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from math import radians, sqrt
# import numpy as np

# Property Groups
class DAYZ_TargetObject(bpy.types.PropertyGroup):
    """Target object reference"""
    obj: bpy.props.PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="Target mesh for grass placement"
    )

class DAYZ_GrassObject(bpy.types.PropertyGroup):
    """Individual grass object with weight"""
    obj: bpy.props.PointerProperty(
        name="Grass Object",
        type=bpy.types.Object,
        description="Grass mesh to place",
        poll=lambda self, obj: obj and obj.type == 'MESH'
    )
    
    weight: bpy.props.FloatProperty(
        name="Weight",
        description="Probability of this grass appearing (0=never, 1=very common)",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )

class DAYZ_GrassPlacerSettings(bpy.types.PropertyGroup):
    """Grass placer settings"""
    
    # Target objects
    target_objects: bpy.props.CollectionProperty(
        type=DAYZ_TargetObject
    )
    
    # Grass objects collection
    grass_objects: bpy.props.CollectionProperty(
        type=DAYZ_GrassObject
    )
    
    grass_objects_index: bpy.props.IntProperty(default=0)
    
    # Placement settings
    total_count: bpy.props.IntProperty(
        name="Total Count",
        description="Number of grass instances per target object",
        default=500,
        min=1,
        max=10000
    )
    
    surface_offset: bpy.props.FloatProperty(
        name="Surface Offset",
        description="Raise/lower grass above/below surface",
        default=0.0,
        unit='LENGTH'
    )
    
    # Distribution settings
    clumping_factor: bpy.props.FloatProperty(
        name="Clumping",
        description="How much grass clumps together (0=even, 1=very clumped)",
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    distribution_seed: bpy.props.IntProperty(
        name="Seed",
        description="Random seed for reproducible results",
        default=42,
        min=0
    )
    
    # Scale variation
    scale_min: bpy.props.FloatProperty(
        name="Min Scale",
        description="Minimum random scale",
        default=0.8,
        min=0.1,
        max=2.0
    )
    
    scale_max: bpy.props.FloatProperty(
        name="Max Scale",
        description="Maximum random scale",
        default=1.2,
        min=0.1,
        max=2.0
    )
    
    # Rotation
    random_rotation: bpy.props.BoolProperty(
        name="Random Rotation",
        description="Randomly rotate grass around surface normal",
        default=True
    )
    
    # Organization
    parent_to_empty: bpy.props.BoolProperty(
        name="Parent to Empty",
        description="Create empty object to organize grass instances",
        default=True
    )
    
    # Merge options
    merge_all_grass: bpy.props.BoolProperty(
        name="Merge All Grass",
        description="Merge all grass instances into a single object",
        default=False
    )
    
    merge_by_variant: bpy.props.BoolProperty(
        name="Merge by Variant",
        description="Merge grass instances by variant (one object per grass type)",
        default=False
    )

# Operators
class DAYZ_OT_SetGrassTargets(bpy.types.Operator):
    """Set selected mesh objects as grass targets"""
    bl_idname = "dayz.set_grass_targets"
    bl_label = "Set Target Objects"
    bl_description = "Use selected mesh objects as targets for grass placement"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        settings = context.scene.dayz_grass_placer_settings
        
        # Clear existing targets
        settings.target_objects.clear()
        
        # Add selected mesh objects
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        for obj in mesh_objects:
            target = settings.target_objects.add()
            target.obj = obj
        
        self.report({'INFO'}, f"Set {len(mesh_objects)} target objects")
        return {'FINISHED'}

class DAYZ_OT_AddGrassObject(bpy.types.Operator):
    """Add a new grass object slot"""
    bl_idname = "dayz.add_grass_object"
    bl_label = "Add Grass Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.dayz_grass_placer_settings
        settings.grass_objects.add()
        settings.grass_objects_index = len(settings.grass_objects) - 1
        return {'FINISHED'}

class DAYZ_OT_RemoveGrassObject(bpy.types.Operator):
    """Remove selected grass object slot"""
    bl_idname = "dayz.remove_grass_object"
    bl_label = "Remove Grass Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Safety check - make sure the property exists
        if not hasattr(context.scene, 'dayz_grass_placer_settings'):
            return False
        settings = context.scene.dayz_grass_placer_settings
        return len(settings.grass_objects) > 0 and 0 <= settings.grass_objects_index < len(settings.grass_objects)

    def execute(self, context):
        settings = context.scene.dayz_grass_placer_settings
        index = settings.grass_objects_index
        
        if 0 <= index < len(settings.grass_objects):
            settings.grass_objects.remove(index)
            # Adjust index to stay within bounds
            if settings.grass_objects_index >= len(settings.grass_objects):
                settings.grass_objects_index = max(0, len(settings.grass_objects) - 1)
        
        return {'FINISHED'}

class DAYZ_OT_GenerateGrass(bpy.types.Operator):
    """Generate grass on target objects"""
    bl_idname = "dayz.generate_grass"
    bl_label = "Generate Grass"
    bl_description = "Place grass objects on target surfaces"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.dayz_grass_placer_settings
        
        # Validation
        if not settings.target_objects:
            self.report({'ERROR'}, "No target objects set")
            return {'CANCELLED'}
        
        valid_grass = [g for g in settings.grass_objects if g.obj and g.weight > 0]
        if not valid_grass:
            self.report({'ERROR'}, "No valid grass objects with weight > 0")
            return {'CANCELLED'}
        
        # Set random seed
        random.seed(settings.distribution_seed)
        
        # Create weighted grass selection
        total_weight = sum(g.weight for g in valid_grass)
        if total_weight == 0:
            self.report({'ERROR'}, "Total grass weight is 0")
            return {'CANCELLED'}
        
        # Generate grass
        all_grass_instances = []
        grass_by_variant = {}  # For merge by variant option
        
        for target_ref in settings.target_objects:
            target_obj = target_ref.obj
            if not target_obj or target_obj.type != 'MESH':
                continue
            
            grass_instances = self.generate_on_object(context, target_obj, valid_grass, total_weight, settings)
            all_grass_instances.extend(grass_instances)
            
            # Group by variant for merge option
            if settings.merge_by_variant:
                for grass_instance in grass_instances:
                    original_name = self.get_original_grass_name(grass_instance, valid_grass)
                    if original_name not in grass_by_variant:
                        grass_by_variant[original_name] = []
                    grass_by_variant[original_name].append(grass_instance)
        
        # Handle merge options
        if settings.merge_all_grass and all_grass_instances:
            self.merge_all_objects(context, all_grass_instances, "DayZ_Merged_Grass")
        elif settings.merge_by_variant and grass_by_variant:
            self.merge_by_variants(context, grass_by_variant)
        elif settings.parent_to_empty and all_grass_instances:
            # Only parent to empty if not merging
            empty = bpy.data.objects.new("DayZ_Grass_Container", None)
            context.collection.objects.link(empty)
            for grass in all_grass_instances:
                grass.parent = empty
        
        self.report({'INFO'}, f"Generated {len(all_grass_instances)} grass instances")
        return {'FINISHED'}
    
    def generate_on_object(self, context, target_obj, valid_grass, total_weight, settings):
        """Generate grass on a single target object"""
        
        # Get mesh data with modifiers applied
        depsgraph = context.evaluated_depsgraph_get()
        target_eval = target_obj.evaluated_get(depsgraph)
        mesh = target_eval.to_mesh()
        
        # Create bmesh for face sampling
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        
        # Calculate face areas for weighted sampling
        face_areas = [face.calc_area() for face in bm.faces]
        total_area = sum(face_areas)
        
        if total_area == 0:
            bm.free()
            target_eval.to_mesh_clear()
            return []
        
        grass_instances = []
        
        for i in range(settings.total_count):
            # Select random face weighted by area
            face = self.select_weighted_face(bm.faces, face_areas, total_area)
            if not face:
                continue
            
            # Get random point on face
            point_local = self.random_point_on_face(face)
            
            # Apply clumping if needed
            if settings.clumping_factor > 0:
                point_local = self.apply_clumping(point_local, face, settings.clumping_factor)
            
            # Transform to world space
            point_world = target_obj.matrix_world @ point_local
            
            # Get surface normal
            normal_local = face.normal
            normal_world = target_obj.matrix_world.to_quaternion() @ normal_local
            normal_world.normalize()
            
            # Apply surface offset
            if settings.surface_offset != 0:
                point_world += normal_world * settings.surface_offset
            
            # Select grass object based on weight
            grass_obj = self.select_weighted_grass(valid_grass, total_weight)
            if not grass_obj:
                continue
            
            # Create grass instance
            grass_instance = self.create_grass_instance(context, grass_obj, point_world, normal_world, settings)
            if grass_instance:
                grass_instances.append(grass_instance)
        
        # Cleanup
        bm.free()
        target_eval.to_mesh_clear()
        
        return grass_instances
    
    def select_weighted_face(self, faces, face_areas, total_area):
        """Select a face weighted by area"""
        if not faces or total_area == 0:
            return None
        
        rand_val = random.uniform(0, total_area)
        current_area = 0
        
        for i, face in enumerate(faces):
            current_area += face_areas[i]
            if rand_val <= current_area:
                return face
        
        return faces[-1]  # fallback
    
    def random_point_on_face(self, face):
        """Get random point on triangular face using barycentric coordinates"""
        if len(face.verts) < 3:
            return face.verts[0].co.copy()
        
        # Generate random barycentric coordinates
        r1, r2 = random.random(), random.random()
        if r1 + r2 > 1:
            r1 = 1 - r1
            r2 = 1 - r2
        
        r3 = 1 - r1 - r2
        
        # Interpolate position
        v0, v1, v2 = face.verts[0].co, face.verts[1].co, face.verts[2].co
        return r1 * v0 + r2 * v1 + r3 * v2
    
    def apply_clumping(self, point, face, clump_factor):
        """Apply clumping effect to point placement"""
        if clump_factor <= 0:
            return point
        
        # Simple clumping by biasing toward face center
        face_center = face.calc_center_median()
        return point.lerp(face_center, clump_factor * random.random())
    
    def select_weighted_grass(self, valid_grass, total_weight):
        """Select grass object based on weight"""
        rand_val = random.uniform(0, total_weight)
        current_weight = 0
        
        for grass_item in valid_grass:
            current_weight += grass_item.weight
            if rand_val <= current_weight:
                return grass_item.obj
        
        return valid_grass[-1].obj  # fallback
    
    def create_grass_instance(self, context, grass_obj, location, normal, settings):
        """Create a single grass instance"""
        
        # Duplicate grass object
        new_grass = grass_obj.copy()
        new_grass.data = grass_obj.data.copy()
        context.collection.objects.link(new_grass)
        
        # Position
        new_grass.location = location
        
        # Orientation - align Z-axis with normal
        if normal.length > 0:
            # Create rotation to align Z with normal
            z_axis = Vector((0, 0, 1))
            rotation_quat = z_axis.rotation_difference(normal)
            
            # Apply random rotation around normal if enabled
            if settings.random_rotation:
                import math
                random_angle = random.uniform(0, 2 * math.pi)
                random_quat = Matrix.Rotation(random_angle, 4, normal).to_quaternion()
                rotation_quat = random_quat @ rotation_quat
            
            new_grass.rotation_euler = rotation_quat.to_euler()
        
        # Random scale
        if settings.scale_min != settings.scale_max:
            scale = random.uniform(settings.scale_min, settings.scale_max)
            new_grass.scale = (scale, scale, scale)
        
        return new_grass
    
    def merge_all_objects(self, context, objects_to_merge, merged_name):
        """Merge all grass objects into a single object"""
        if not objects_to_merge:
            return
        
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select all grass objects
        for obj in objects_to_merge:
            obj.select_set(True)
        
        # Set the first object as active
        context.view_layer.objects.active = objects_to_merge[0]
        
        # Join all objects
        bpy.ops.object.join()
        
        # Rename the merged object
        context.view_layer.objects.active.name = merged_name
    
    def merge_by_variants(self, context, grass_by_variant):
        """Merge grass objects by variant type"""
        for variant_name, objects in grass_by_variant.items():
            if len(objects) > 1:
                self.merge_all_objects(context, objects, f"DayZ_{variant_name}_Merged")
    
    def get_original_grass_name(self, grass_instance, valid_grass):
        """Get the name of the original grass object this instance came from"""
        instance_data_name = grass_instance.data.name
        
        # Try to match with original grass objects
        for grass_item in valid_grass:
            if grass_item.obj and grass_item.obj.data.name in instance_data_name:
                return grass_item.obj.name
        
        # Fallback: try to clean up common Blender suffixes
        clean_name = instance_data_name
        for suffix in ['.001', '.002', '.003', '.004', '.005', '.006', '.007', '.008', '.009']:
            clean_name = clean_name.replace(suffix, '')
        
        return clean_name

# Classes to register
grass_classes = (
    DAYZ_TargetObject,
    DAYZ_GrassObject,
    DAYZ_GrassPlacerSettings,
    DAYZ_OT_SetGrassTargets,
    DAYZ_OT_AddGrassObject,
    DAYZ_OT_RemoveGrassObject,
    DAYZ_OT_GenerateGrass,
)

def register_grass_placer():
    """Register grass placer classes"""
    for cls in grass_classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.dayz_grass_placer_settings = bpy.props.PointerProperty(type=DAYZ_GrassPlacerSettings)

def unregister_grass_placer():
    """Unregister grass placer classes"""
    if hasattr(bpy.types.Scene, 'dayz_grass_placer_settings'):
        del bpy.types.Scene.dayz_grass_placer_settings
    
    for cls in reversed(grass_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass  # Class wasn't registered