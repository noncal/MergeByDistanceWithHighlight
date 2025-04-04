# MIT License

# Copyright (c) 2025 non_col

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

bl_info = {
    'name': 'Merge by distance with highlight',
    'author': 'non_col',
    'version': (1, 0),
    'blender': (4, 2, 0),
    'description': 'Highlight vertices that will be removed when performing merge by distance',
    'category': 'Mesh',
}

import bpy
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty

handle = None
highlight_coords = []


class MergeHighlightOperator(bpy.types.Operator):
    bl_idname = 'mesh.merge_by_distance_highlight'
    bl_label = 'Merge by Distance (Highlight)'
    bl_description = 'Merge vertices based on thier proximity (with highlight)'
    bl_options = {'REGISTER', 'UNDO'}

    merge_distance: FloatProperty(
        name="Merge Distance",
        description="Distance within which vertices are merged",
        soft_min=1e-5,
        soft_max=10,
        default=0.0001,
        unit='LENGTH',
    )
    unselected: BoolProperty(name='Unselected')
    sharp_edges: BoolProperty(name='Sharp Edges')


    def execute(self, context):
        global handle

        self.update_highlight(context)

        if not handle:
            handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, (), 'WINDOW', 'POST_VIEW')

        return {'FINISHED'}


    def update_highlight(self, context):
        global highlight_coords

        obj = context.object
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        verts = {}
        for v in bm.verts:
            vert = tuple(v.co.copy())
            if vert not in verts:
                verts[vert] = 0
            verts[vert] += 1

        original_verts = set(verts.keys())
        duplicate_verts = set()
        for vert, count in verts.items():
            if count > 1:
                duplicate_verts.add(vert)

        bpy.ops.mesh.remove_doubles(threshold=self.merge_distance, use_unselected=self.unselected, use_sharp_edge_from_normals=self.sharp_edges)
        merged_verts = set(tuple(v.co.copy()) for v in bm.verts)

        removed_verts = (original_verts - merged_verts).union(duplicate_verts)

        highlight_coords = list(map(Vector, removed_verts))


def draw_callback():
    global handle

    op = bpy.context.window_manager.operators
    if op and not isinstance(op[-1], MergeHighlightOperator):
        bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
        handle = None
        highlight_coords.clear()
        return

    if highlight_coords:
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'POINTS', {'pos': highlight_coords})
        gpu.state.point_size_set(6.0)
        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 0.0, 0.5))
        batch.draw(shader)


def menu(self, context):
    self.layout.operator(MergeHighlightOperator.bl_idname, text='By Distance (Highlight)')


def register():
    bpy.utils.register_class(MergeHighlightOperator)
    bpy.types.VIEW3D_MT_edit_mesh_merge.append(menu)


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_merge.remove(menu)
    bpy.utils.unregister_class(MergeHighlightOperator)


if __name__ == "__main__":
    register()
