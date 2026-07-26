import bpy
import numpy
from pathlib import Path


from collada import *

obj = bpy.context.active_object

desgraph = bpy.context.evaluated_depsgraph_get()
obj_eval = obj.evaluated_get(desgraph)

mesh = obj_eval.to_mesh()

# ensure all faces are triangles
mesh.calc_loop_triangles()

vertex_data = []
normal_data = []

vertex_indices = []
normal_indices = []

for v in mesh.vertices:
    vertex_data.extend(v.co)

for loop in mesh.loops:
    normal_data.extend(loop.normal)

# Triangle indices
for tri in mesh.loop_triangles:
    for vert_index, loop_index in zip(tri.vertices, tri.loops):
        vertex_indices.append(vert_index)
        normal_indices.append(loop_index)

# Float Sources
vert_src = source.FloatSource(
    "verts-array",
    numpy.array(vertex_data),
    ('X','Y','Z')
)

normal_src = source.FloatSource(
    "normals-array",
    numpy.array(normal_data),
    ('X','Y','Z')
)

# Geometry

dae = Collada()
geom = geometry.Geometry(
    dae,
    "geometry0",
    obj.name,
    [vert_src, normal_src]
)

input_list = source.InputList()

input_list.addInput(
    0,
    "VERTEX",
    "#verts-array"
)

input_list.addInput(
    1,
    "NORMAL",
    "#normals-array"
)

#COllada index buffer

indices = []
for v, n in zip(vertex_indices, normal_indices):
    indices.append(v)
    indices.append(n)

indices = numpy.array(indices)

# indices = []

# for tri in mesh.loop_triangles:
#     for vert_idx, loop_idx in zip(tri.vertices, tri.loops):
#         indices.extend((vert_idx, loop_idx))

# Triangle Set
triset = geom.createTriangleSet(
    indices,
    input_list,
    "materialref"
)

geom.primitives.append(triset)

dae.geometries.append(geom)

# Scene
node = scene.Node(
    "node0",
    children=[
        scene.GeometryNode(geom)
    ]
)

myscene = scene.Scene(
    "scene0",
    [node]
)

dae.scenes.append(myscene)
dae.scene = myscene


output = Path.home() / "Desktop" / "testfile.dae"

dae.write(str(output))