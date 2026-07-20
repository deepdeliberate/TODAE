import collada
import os

import bpy

def create_basic_dae(output_filename):
    # 1. Initialize a completely fresh COLLADA document
    mesh = collada.Collada()
    
    # 2. COLLADA assets require basic metadata (like up-axis)
    mesh.assetInfo.upaxis = collada.asset.UP_AXIS.Z_UP
    
    # 3. Save the document to a file
    mesh.write(output_filename)
    print(f"Successfully created a baseline DAE file at: {output_filename}")

if __name__ == "__main__":
    output_path = "output_test.dae"
    create_basic_dae(output_path)
