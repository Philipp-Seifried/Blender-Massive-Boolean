# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Massive Boolean",
    "author": "Philipp Seifried",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "description": "Joins all selected objects, performing mesh cleanup operations after each boolean operation.",
    "warning": "Beta",
    "category": "Object",
}

import bpy
from bpy.types import Panel, Operator
import math, random
from mathutils import *
import bmesh
import time; 
from mathutils.bvhtree import BVHTree

operation_types = [
    ("UNION", "Union", "", 1),
    ("DIFFERENCE", "Difference", "", 2),
]

class Object_OT_massive_boolean(Operator):
    """Joins all selected objects, performing mesh cleanup operations after each boolean operation."""
    bl_idname = "object.massive_boolean"
    bl_label = "Massive Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    operation : bpy.props.EnumProperty(items=operation_types, default='UNION', name='Operation Type')

    def scene_update(self, context):
        dg = context.evaluated_depsgraph_get() 
        dg.update()

    def get_num_tris(self, me):
        num_tris = sum(len(p.vertices) - 2 for p in me.polygons)
        return num_tris

    def select_single_object(self, ob, context):
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(state=True)
        context.view_layer.objects.active = ob
        self.scene_update(context)

    def massive_boolean(self, context):
        C = context
        D = bpy.data

        ob_list = context.selected_objects

        main_ob = context.view_layer.objects.active
        if (main_ob in ob_list):
            ob_list.remove(main_ob)
        main_ob.data = main_ob.data.copy()

        non_meshes = [o for o in ob_list if o.type != 'MESH']
        for o in non_meshes:
            ob_list.remove(o)

        self.select_single_object(main_ob, context)
        bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True, material=False, animation=False)
        bpy.ops.object.convert(target='MESH')
        self.scene_update(context)

        if (context.scene.massive_boolean_settings.sort_by_distance):
            print("Sorting by distance.")
            ob_list.sort(key=lambda o: (o.location-main_ob.location).length)

        time_start = time.time()*1000.0
        initial_num_obs = len(ob_list)

        orig_len = len(ob_list)
        wm = context.window_manager
        wm.progress_begin(0.0, 1.0)
        last_count = 0

        while len(ob_list) > 0:
            self.select_single_object(main_ob, context)
            wm.progress_update(1-len(ob_list)/orig_len)
            # boolean ops
            bool_ob = ob_list[0]
            bool_ob.data = bool_ob.data.copy()
            ob_list.remove(bool_ob)
            bpy.ops.object.modifier_add(type='BOOLEAN')
            context.object.modifiers["Boolean"].operation = self.operation
            context.object.modifiers["Boolean"].double_threshold = 0
            context.object.modifiers["Boolean"].object = bool_ob
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
            
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')

            bpy.ops.mesh.fill_holes()

            if (context.scene.massive_boolean_settings.remove_doubles):
                bpy.ops.mesh.remove_doubles(threshold=context.scene.massive_boolean_settings.remove_doubles_threshold)

            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

            if (C.scene.massive_boolean_settings.dissolve_limited):
                bpy.ops.mesh.dissolve_limited(angle_limit=0.01)

            if (C.scene.massive_boolean_settings.vert_connect_concave):
                bpy.ops.mesh.vert_connect_concave()
            if (C.scene.massive_boolean_settings.dissolve_degenerate):
                bpy.ops.mesh.dissolve_degenerate()
            
            if (C.scene.massive_boolean_settings.delete_loose):
                bpy.ops.mesh.delete_loose()

            bpy.ops.mesh.tris_convert_to_quads()
            
            bpy.ops.object.editmode_toggle()
            if (C.scene.massive_boolean_settings.delete_operands):
                D.objects.remove(bool_ob, do_unlink=True)

            if (C.scene.massive_boolean_settings.dissolve_limited):
                bpy.ops.object.modifier_add(type='DECIMATE')
                bpy.context.object.modifiers["Decimate"].decimate_type = 'DISSOLVE'
                bpy.context.object.modifiers["Decimate"].angle_limit = 0.001
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')

            if (C.scene.massive_boolean_settings.dissolve_degenerate):
                bpy.ops.mesh.dissolve_degenerate()

            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.ops.mesh.select_non_manifold(extend=True, use_wire=True, use_boundary=True, use_multi_face=True, use_non_contiguous=False, use_verts=True)
            bpy.ops.object.editmode_toggle()
            self.scene_update(context)
            selected_verts = list(filter(lambda v: v.select, main_ob.data.vertices))
            
            if (len(selected_verts) != 0):
                print("Non manifold geometry found.")
                if (C.scene.massive_boolean_settings.collapse_non_manifold):
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.merge(type='COLLAPSE')
                    bpy.ops.mesh.delete_loose()
                    bpy.ops.object.editmode_toggle()

            # time estimate:
            c_time = time.time()*1000.0 - time_start
            num_obs_left = len(ob_list)
            time_per_ob = c_time / max(initial_num_obs-num_obs_left, 0.0001)
            time_left = round((time_per_ob*num_obs_left)/1000)
            time_running = round(c_time/1000)
            tri_count = self.get_num_tris(main_ob.data)
            last_count = tri_count

            self.scene_update(context)
            print (f"boolean {self.operation}: {num_obs_left} items left... {time_running} seconds running. estimated {time_left} seconds left. tri count: {tri_count}")
        wm.progress_end()
        print (f"Total time taken: {(time.time()*1000.0 - time_start)/1000} seconds.")

        return True


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        result = self.massive_boolean(context)
        if (result != True):
            self.report({'ERROR'}, result)
            return {'CANCELLED'}
        return {'FINISHED'}


class VIEW3D_PT_massive_boolean(Panel):
    """Main UI Panel"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"
    bl_label = "Massive Boolean"
    bl_context = "objectmode"

    def draw(self, context):
        obj = context.object
        scene = context.scene
        layout = self.layout
        settings = context.scene.massive_boolean_settings

        ob_list = context.selected_objects
        main_ob = context.view_layer.objects.active
        if main_ob == None:
            layout.label(text="No active object selected!", icon='ERROR')
            return
        if main_ob.type != 'MESH':
            layout.label(text="Active object is not a mesh!", icon='ERROR')
            return

        layout.label(text=f"Active object: {main_ob.name}")

        if (main_ob in ob_list):
            ob_list.remove(main_ob)
        if len(ob_list) < 1:
            layout.label(text="Please select more objects!", icon='ERROR')
            return

        layout.label(text=f"{len(ob_list)} operand(s) selected.")

        box = layout.box()
        row = box.row()
        row.prop(settings, "settings_expanded",
            icon="TRIA_DOWN" if settings.settings_expanded else "TRIA_RIGHT", icon_only=True, emboss=False
        )
        row.label(text="Options")

        if settings.settings_expanded:
            box.prop(settings, "delete_operands")
            box.prop(settings, "sort_by_distance")

            box.label(text="Clean-up steps per operand:")
            box.prop(settings, "remove_doubles")
            if (settings.remove_doubles):
                box.prop(settings, "remove_doubles_threshold")
            box.prop(settings, "dissolve_limited")
            box.prop(settings, "vert_connect_concave")
            box.prop(settings, "dissolve_degenerate")
            box.prop(settings, "delete_loose")
            box.prop(settings, "collapse_non_manifold")

        warning_modifiers = len(main_ob.modifiers) != 0
        num_non_meshes = len( [o for o in ob_list if o.type != 'MESH'] )
        warning_non_meshes = num_non_meshes != 0

        if warning_modifiers or warning_non_meshes:
            box = layout.box()
            box.label(text="Warnings:", icon='ERROR')
            if warning_modifiers:
                col = box.column()
                col.label(text="- Main object has modifiers!")
                col.label(text="  Modifiers will be flattened.")
            if warning_non_meshes:
                col = box.column()
                col.label(text=f"- {num_non_meshes} operand(s) are not Meshes.")
                col.label(text="  They will be skipped.")


        op_union = layout.operator(Object_OT_massive_boolean.bl_idname, text="Union", icon='SELECT_EXTEND')
        op_union.operation = 'UNION'
        op_difference = layout.operator(Object_OT_massive_boolean.bl_idname, text="Difference", icon='SELECT_SUBTRACT')
        op_difference.operation = 'DIFFERENCE'


class Settings_massive_boolean(bpy.types.PropertyGroup):
    """Settings for Massive Boolean"""
    settings_expanded : bpy.props.BoolProperty(name="Options", default=False)
    
    sort_by_distance : bpy.props.BoolProperty(name="Sort Operands By Distance", default=False)
    delete_operands : bpy.props.BoolProperty(name="Delete Operands", default=True)
    
    remove_doubles : bpy.props.BoolProperty(name="Merge By Distance", default=False)
    remove_doubles_threshold : bpy.props.FloatProperty(name="Distance Threshold", default=0.01, min=0.0)

    dissolve_limited : bpy.props.BoolProperty(name="Limited Dissolve", default=True)
    vert_connect_concave : bpy.props.BoolProperty(name="Split Concave Faces", default=True)
    dissolve_degenerate : bpy.props.BoolProperty(name="Degenerate Dissolve", default=True)
    delete_loose : bpy.props.BoolProperty(name="Delete Loose", default=True)
    collapse_non_manifold : bpy.props.BoolProperty(name="Collapse Non-Manifold", default=True)


classes = (
    Object_OT_massive_boolean,
    VIEW3D_PT_massive_boolean,
    Settings_massive_boolean,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.massive_boolean_settings = bpy.props.PointerProperty(type=Settings_massive_boolean)


def unregister():
    del bpy.types.Scene.massive_boolean_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
    print("Registered")

