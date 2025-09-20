"""
UV Cleaner Tool for DayZ Asset Tools Extension
Removes empty UV maps from selected objects while preserving at least one UV map per object
"""

import bpy
import bmesh
from mathutils import Vector

class DAYZ_OT_CleanEmptyUVMaps(bpy.types.Operator):
    """Clean empty UV maps from selected objects"""
    bl_idname = "dayz.clean_empty_uv_maps"
    bl_label = "Clean Empty UV Maps"
    bl_description = "Remove UV maps that are empty (all at 0,0) or have insignificant surface area while keeping at least one UV map per object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Check if we have mesh objects selected
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def analyze_uv_map(self, mesh, uv_layer):
        """
        Analyze a UV map and return detailed information
        Returns dictionary with analysis data
        """
        # Create a new bmesh instance from mesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        
        # Ensure face indices are valid
        bm.faces.ensure_lookup_table()
        
        # Get the UV layer
        uv_layer_bmesh = bm.loops.layers.uv.get(uv_layer.name)
        
        analysis = {
            'name': uv_layer.name,
            'total_faces': 0,
            'valid_faces': 0,
            'total_points': 0,
            'unique_points': 0,
            'total_surface_area': 0.0,
            'islands': 0,
            'all_at_origin': True,
            'is_empty': True
        }
        
        if not uv_layer_bmesh:
            bm.free()
            return analysis
        
        unique_uvs = set()
        face_areas = []
        min_area_threshold = 1e-6
        
        # Analyze all faces
        for face in bm.faces:
            analysis['total_faces'] += 1
            face_loops = face.loops
            
            if len(face_loops) < 3:  # Skip degenerate faces
                continue
            
            analysis['valid_faces'] += 1
            
            # Get UV coordinates for this face
            uv_coords = []
            for loop in face_loops:
                uv = loop[uv_layer_bmesh].uv
                uv_coords.append([uv.x, uv.y])
                unique_uvs.add((round(uv.x, 8), round(uv.y, 8)))  # Round for uniqueness check
                analysis['total_points'] += 1
                
                # Check if any UV coordinate is not at origin
                if abs(uv.x) > 1e-6 or abs(uv.y) > 1e-6:
                    analysis['all_at_origin'] = False
            
            # Calculate UV area for this face
            if len(uv_coords) >= 3:
                face_area = abs(self.calculate_polygon_area(uv_coords))
                face_areas.append(face_area)
                analysis['total_surface_area'] += face_area
        
        analysis['unique_points'] = len(unique_uvs)
        
        # Estimate number of islands (simplified - counts disconnected UV coordinate groups)
        analysis['islands'] = self.estimate_uv_islands(bm, uv_layer_bmesh)
        
        # Determine if UV map is considered empty
        analysis['is_empty'] = (analysis['all_at_origin'] or 
                              analysis['total_surface_area'] < min_area_threshold)
        
        bm.free()
        return analysis

    def estimate_uv_islands(self, bm, uv_layer):
        """
        Estimate the number of UV islands by analyzing connected UV coordinates
        This is a simplified estimation
        """
        if not uv_layer:
            return 0
        
        visited_faces = set()
        islands = 0
        
        # Simple island detection based on shared UV coordinates
        for face in bm.faces:
            if face.index in visited_faces:
                continue
            
            # Start a new island
            islands += 1
            island_faces = [face]
            visited_faces.add(face.index)
            
            # Get UV coordinates for this face
            face_uvs = []
            for loop in face.loops:
                uv = loop[uv_layer].uv
                face_uvs.append((round(uv.x, 6), round(uv.y, 6)))
            
            # Find connected faces (simplified - faces sharing UV coordinates)
            i = 0
            while i < len(island_faces):
                current_face = island_faces[i]
                current_uvs = []
                for loop in current_face.loops:
                    uv = loop[uv_layer].uv
                    current_uvs.append((round(uv.x, 6), round(uv.y, 6)))
                
                # Check other faces for shared UV coordinates
                for other_face in bm.faces:
                    if other_face.index in visited_faces:
                        continue
                    
                    other_uvs = []
                    for loop in other_face.loops:
                        uv = loop[uv_layer].uv
                        other_uvs.append((round(uv.x, 6), round(uv.y, 6)))
                    
                    # If faces share UV coordinates, they're connected
                    if any(uv in other_uvs for uv in current_uvs):
                        island_faces.append(other_face)
                        visited_faces.add(other_face.index)
                
                i += 1
        
        return islands

    def is_uv_map_empty(self, mesh, uv_layer):
        """
        Check if a UV map is empty or has insignificant surface area
        Returns True if empty, False otherwise
        """
        analysis = self.analyze_uv_map(mesh, uv_layer)
        
        # Print detailed analysis
        print(f"    UV Map Analysis for '{analysis['name']}':")
        print(f"      Total Faces: {analysis['total_faces']}")
        print(f"      Valid Faces: {analysis['valid_faces']}")
        print(f"      Total Points: {analysis['total_points']}")
        print(f"      Unique Points: {analysis['unique_points']}")
        print(f"      Estimated Islands: {analysis['islands']}")
        print(f"      Total Surface Area: {analysis['total_surface_area']:.8f}")
        print(f"      All at Origin: {analysis['all_at_origin']}")
        print(f"      Considered Empty: {analysis['is_empty']}")
        
        return analysis['is_empty']
    
    def calculate_polygon_area(self, vertices):
        """
        Calculate the area of a polygon using the shoelace formula
        vertices: list of [x, y] coordinates
        """
        if len(vertices) < 3:
            return 0.0
        
        area = 0.0
        n = len(vertices)
        
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        
        return area / 2.0

    def execute(self, context):
        """
        Remove empty UV maps from selected objects, keeping at least one UV map per object
        """
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        total_deleted = 0
        processed_objects = 0
        
        for obj in selected_objects:
            if not obj.data.uv_layers:
                self.report({'INFO'}, f"Object '{obj.name}' has no UV maps")
                continue
            
            # Get all UV layers for this object
            uv_layers = list(obj.data.uv_layers)
            empty_uv_maps = []
            non_empty_uv_maps = []
            
            print(f"\nChecking object: {obj.name}")
            print(f"Total UV maps: {len(uv_layers)}")
            
            # Categorize UV maps as empty or non-empty
            for uv_layer in uv_layers:
                if self.is_uv_map_empty(obj.data, uv_layer):
                    empty_uv_maps.append(uv_layer)
                    print(f"  - Empty/insignificant UV map found: {uv_layer.name}")
                else:
                    non_empty_uv_maps.append(uv_layer)
                    print(f"  - Valid UV map: {uv_layer.name}")
            
            # Only delete empty UV maps if there's at least one non-empty map remaining
            if len(non_empty_uv_maps) > 0 and len(empty_uv_maps) > 0:
                for uv_map in empty_uv_maps:
                    print(f"  - Deleting empty/insignificant UV map: {uv_map.name}")
                    obj.data.uv_layers.remove(uv_map)
                    total_deleted += 1
                processed_objects += 1
            elif len(empty_uv_maps) > 0:
                print(f"  - Skipping deletion: all UV maps are empty/insignificant, keeping at least one")
                processed_objects += 1
            else:
                print(f"  - No empty/insignificant UV maps found")
                processed_objects += 1
        
        print(f"\nOperation complete. Processed {processed_objects} objects, deleted {total_deleted} empty UV maps total.")
        self.report({'INFO'}, f"Processed {processed_objects} objects, deleted {total_deleted} empty UV maps")
        
        return {'FINISHED'}

# Classes to register
uv_cleaner_classes = (
    DAYZ_OT_CleanEmptyUVMaps,
)

def register_uv_cleaner():
    """Register UV cleaner classes"""
    for cls in uv_cleaner_classes:
        bpy.utils.register_class(cls)

def unregister_uv_cleaner():
    """Unregister UV cleaner classes"""
    for cls in reversed(uv_cleaner_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass