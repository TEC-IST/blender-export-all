bl_info = {
    "name": "Export All Formats + Renders + Wireframe, Solid, and Material Viewports",
    "blender": (4, 2, 0),
    "category": "Import-Export",
    "version": (1, 0),
    "description": "Exports the scene in all formats and captures orbiting renders and viewports (wireframe, solid, and material)",
    "author": "TEC.IST",
    "location": "File > Export > Export All Formats + Orbit Images",
    "warning": "",
    "doc_url": "https://github.com/TEC-IST/blender-export-all",
    "tracker_url": "https://github.com/TEC-IST/blender-export-all/issues",
    "support": "COMMUNITY",
}

import bpy
import os
import math

class EXPORT_OT_export_all_formats(bpy.types.Operator):
    """Export Scene in All Formats + Generate Orbit Images of Selected [or All] Objects"""
    bl_idname = "export_scene.export_all_formats"
    bl_label = "Export Scene in All Formats + Generate Orbit Images of Selected [or All] Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Define the output directory
        export_dir = bpy.path.abspath("//exports")
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Get the current file name for export naming
        base_name = bpy.path.basename(bpy.context.blend_data.filepath)
        if not base_name:
            base_name = "untitled"
        base_name = os.path.splitext(base_name)[0]

        # Export in all available formats
        formats = {
            'fbx': bpy.ops.export_scene.fbx,
            'obj': bpy.ops.wm.obj_export,
            'gltf': bpy.ops.export_scene.gltf,
            'dae': bpy.ops.wm.collada_export,
            'stl': bpy.ops.wm.stl_export,
            'ply': bpy.ops.wm.ply_export,
            'abc': bpy.ops.wm.alembic_export,
            'usd': bpy.ops.wm.usd_export,
        }

        for ext, export_op in formats.items():
            export_path = os.path.join(export_dir, f"{base_name}.{ext}")
            export_op(filepath=export_path)

        # Set the shading modes and number of images to generate
        modes = {
            'WIREFRAME':4,
            'SOLID':4,
            'MATERIAL':4,
            'RENDERED':12,
        }

        #store which object(s) were selected
        selected_objects = bpy.context.selected_objects
        #if no objects are selected, select all objects except cameras, lights, empties, and armatures
        if not selected_objects:
            for obj in bpy.context.scene.objects:
                if obj.type == 'CAMERA' or obj.type == 'LIGHT' or obj.type == 'EMPTY' or obj.type == 'ARMATURE':
                    obj.select_set(False)
                else:
                    obj.select_set(True)
            selected_objects = bpy.context.selected_objects

        #add a camera and set it to the view
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 0), rotation=(0, 0, 0))
        temp_camera = bpy.context.object
        original_camera = bpy.context.scene.camera
        bpy.context.scene.camera = temp_camera

        #deselect temp camera
        temp_camera.select_set(False)

        #re-select object(s)
        for obj in selected_objects:
           obj.select_set(True)

        for mode, number_of_images in modes.items():

            #set the shading mode
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].region_3d.view_perspective = 'CAMERA'
                    space = area.spaces.active
                    space.shading.type = mode

            for image in range(number_of_images):

                #Rotate the camera
                temp_camera.rotation_euler = (math.radians(90), 0, 2 * math.pi * image / number_of_images)

                #set the camera to the view
                bpy.ops.view3d.camera_to_view_selected()
                
                #update view
                bpy.context.view_layer.update()

                # Render the viewport
                render_path = os.path.join(export_dir, f"{base_name}_{mode}_{image}.png")
                bpy.context.scene.render.filepath = render_path
                bpy.context.scene.render.resolution_x = 1920
                bpy.context.scene.render.resolution_y = 1080
                bpy.context.scene.render.resolution_percentage = 100

                #for solid, wireframe, and material, deselect the objects and render the viewport
                if mode == 'WIREFRAME' or mode == 'SOLID' or mode == 'MATERIAL':
                    for obj in selected_objects:
                        obj.select_set(False)
                    bpy.ops.render.opengl(animation=False, render_keyed_only=False, sequencer=False, write_still=True, view_context=True)
                    for obj in selected_objects:
                        obj.select_set(True)
                else:
                    bpy.ops.render.render(animation=False, write_still=True, use_viewport=False)

        # Restore original camera if it existed; remove temporary camera
        if original_camera is not None:
            bpy.context.scene.camera = original_camera
        bpy.data.objects.remove(temp_camera, do_unlink=True)

        self.report({'INFO'}, "Exports and renders completed")
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(EXPORT_OT_export_all_formats.bl_idname, text="Export All Formats + Orbit Images")

def register():
    bpy.utils.register_class(EXPORT_OT_export_all_formats)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(EXPORT_OT_export_all_formats)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()