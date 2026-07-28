import bpy
import numpy

from collada import *

obj = bpy.context.active_object

depsgraph = bpy.context.evaluated_depsgraph_get()
obj_eval = obj.evaluated_get(depsgraph)

mesh = obj_eval.to_mesh()
mesh.calc_loop_triangles()

# Collada Document
dae = Collada()

vertex_data = []

for v in mesh.vertices:
    vertex_data.extend(v.co)

vert_src = source.FloatSource(
    "verts-array",
    numpy.array(vertex_data, dtype=numpy.float32),
    ('X', 'Y', 'Z')
)


# Split normal source
# One normal per Blender loop

normal_data = []

for loop in mesh.loops:
    normal_data.extend(loop.normal)

normal_src = source.FloatSource(
    "normals-array",
    numpy.array(normal_data, dtype=numpy.float32),
    ('X','Y','Z')
)

# UVs

uv_layers_data = []

for uv_layer in mesh.uv_layers:
    uv_data = []

    for loop in mesh.loops:
        uv = uv_layer.data[loop.index].uv
        uv_data.extend((uv.x, uv.y))

    uv_layers_data.append(uv_data)


# Each UVLayer -> FloatSource
uv_sources = []
for i, uv_data in enumerate(uv_layers_data):
    uv_src = source.FloatSource(
        f"uv{i}-array",
        numpy.array(uv_data, dtype=numpy.float32),
        ('S','T')
    )

    uv_sources.append(uv_src)



sources = [
    vert_src,
    normal_src,
]

sources.extend(uv_sources)

# Geometry

geom = geometry.Geometry(
    dae,
    "geometry0",
    obj.name,
    sources
)

# Input layout
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

offset = 2
for i in range(len(uv_sources)):
    input_list.addInput(
        offset,
        "TEXCOORD",
        f"#uv{i}-array",
        str(i)
    )

    offset += 1



# Collada Index Buffer
# For each Triangle corner : vertex index, loop(normal)_index, uv0, uv1 ,..

# vertex
# normal
# uv0
# uv1
# uv2

indices = []
uv_count = len(mesh.uv_layers)

for tri in mesh.loop_triangles:
    for corner in range(3):
        vertex_index = tri.vertices[corner]
        loop_index = tri.loops[corner]

        indices.append(vertex_index)
        indices.append(loop_index)

        for _ in range(uv_count):
            indices.append(loop_index)

indices = numpy.array(indices, dtype=numpy.uint32)




# Triangle Set

triset = geom.createTriangleSet(
    indices,
    input_list,
    "materialref"
)

geom.primitives.append(triset)
dae.geometries.append(geom)

# Dummy mat

effect = material.Effect(
    "effect0",
    [],
    "phong",
    diffuse=(0.8, 0.8, 0.8),
    specular=(0,0,0)
)

mat = material.Material(
    "material0",
    "DefaultMaterial",
    effect
)

dae.effects.append(effect)
dae.materials.append(mat)

matnode = scene.MaterialNode(
    "materialref",
    mat,
    inputs = []
)


geonode = scene.GeometryNode(
    geom,
    [matnode]
)

node = scene.Node(
    "node0",
    children=[geonode]
)

myscene = scene.Scene(
    "scene0",
    [node]
)

dae.scenes.append(myscene)
dae.scene = myscene

# Write

dae.write(r"C:\Users\naman\Desktop\testfile.dae")
print("Export Finished")