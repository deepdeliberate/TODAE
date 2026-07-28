import bpy
import numpy

from collada import *
from collada.asset import UP_AXIS

from datetime import datetime



objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']


depsgraph = bpy.context.evaluated_depsgraph_get()


# Collada Document
dae = Collada()

# PRIMARY SETTINGS ----------------------------------------------------
now = datetime.now().replace(microsecond=0)
dae.assetInfo.upaxis = UP_AXIS.Z_UP
dae.assetInfo.unitname = "meter"
dae.assetInfo.unitmeter = 1.0
dae.assetInfo.created = now
dae.assetInfo.modified = now


scene_nodes = []
for obj in objects:

    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()
    mesh.calc_loop_triangles()


    #vertex Data
    vertex_data = []

    for v in mesh.vertices:
        vertex_data.extend(v.co)

    vert_src = source.FloatSource(
        f"{obj.name}-verts",
        numpy.array(vertex_data, dtype=numpy.float32),
        ('X', 'Y', 'Z')
    )


    # Split normal source
    # One normal per Blender loop

    normal_data = []

    for loop in mesh.loops:
        normal_data.extend(loop.normal)

    normal_src = source.FloatSource(
        f"{obj.name}-normals",
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
            f"{obj.name}-uv{i}",
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

    geometry_id = f"geometry_{obj.name}"

    geom = geometry.Geometry(
        dae,
        geometry_id,
        obj.name,
        sources
    )

    # Input layout
    input_list = source.InputList()

    input_list.addInput(
        0,
        "VERTEX",
        f"#{obj.name}-verts"
    )

    input_list.addInput(
        1,
        "NORMAL",
        f"#{obj.name}-normals"
    )

    offset = 2
    for i in range(len(uv_sources)):
        input_list.addInput(
            offset,
            "TEXCOORD",
            f"#{obj.name}-uv{i}",
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
    symbol = f"{obj.name}_mat"
    triset = geom.createTriangleSet(
        indices,
        input_list,
        symbol
    )

    # Dummy mat

    effect = material.Effect(
        f"{obj.name}_effect",
        [],
        "phong",
        diffuse=(0.8, 0.8, 0.8),
        specular=(0,0,0)
    )

    mat = material.Material(
        f"{obj.name}_material",
        "DefaultMaterial",
        effect
    )

    dae.effects.append(effect)
    dae.materials.append(mat)

    matnode = scene.MaterialNode(
        symbol,
        mat,
        inputs = []
    )


    geonode = scene.GeometryNode(
        geom,
        [matnode]
    )


    # Object Transform matrix ------------------------------------------

    transform = scene.MatrixTransform(
        numpy.array(obj.matrix_world, dtype=numpy.float32).flatten()
    )
    node = scene.Node(
        f"node_{obj.name}",
        transforms=[transform],
        children=[geonode]
    )

    geom.primitives.append(triset)
    dae.geometries.append(geom)

    scene_nodes.append(node)

    obj_eval.to_mesh_clear()



myscene = scene.Scene(
    "scene0",
    scene_nodes
)

dae.scenes.append(myscene)
dae.scene = myscene

# Write

dae.write(r"C:\Users\naman\Desktop\testfile.dae")
print("Export Finished")