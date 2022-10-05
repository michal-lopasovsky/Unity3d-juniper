bl_info = {
    "name": "FBX EXPORTER",
    "category": "EXPORTER",
    "author": "Michal Lopasovsky",
    "version": (1, 0, 1),
    "blender": (2, 90, 1),
    "location": "VIEW_3D > Sidebar > EXPORTER",
    "description": "Export all child objects under exporting node.",
}

import os
import pathlib
import bpy

from P4 import P4, P4Exception
from collections import defaultdict


DEPOTROOT       = "D:\depots"
DEPOT           = "juniper_game_dev"
P4CONFIGFILE    = DEPOTROOT + "\\" + DEPOT + "\.p4config"

p4 = P4()

with open(P4CONFIGFILE, "r") as file:
    P4_CONFIG = defaultdict(str)
    for line in file:
        data = line.strip().split('=')
        P4_CONFIG[data[0].strip()] = data[1].strip()

p4.port     = P4_CONFIG['P4PORT']
p4.user     = P4_CONFIG['P4USER']
p4.client   = P4_CONFIG['P4CLIENT']


def check_out_exported_file(desc, fbx_file_to_export, cleaned_path):
    try:
        p4.connect()
        result = p4.fetch_change()

        if os.path.isfile(str(cleaned_path)):
            p4.run("edit", cleaned_path)
        else:
            result['Description'] = "Exported from Blender"
            result['Files'] = []
            change_list = p4.save_change(result)[0].split()[1]
            output = p4.run_add("-c", change_list, cleaned_path)
        p4.disconnect()

    except P4Exception:
        print("----- P4 Related errors START ----")
        for e in p4.errors:
            print(e)
        print("----- P4 Related errors END ----")

def get_children():
    return bpy.ops.object.select_grouped(type='CHILDREN_RECURSIVE')

def export_to_fbx(context):
    relatpath = bpy.path.relpath(context.fbx_export_path)
    fbx_file_to_export = context.fbx_export_name + ".fbx"
    cleaned_path = DEPOTROOT + "\\" + relatpath[relatpath.find(DEPOT):] + fbx_file_to_export
    export_path = os.path.normpath(cleaned_path)

    # P4 checkout fbx file first
    desc = "Saved from Blender"
    check_out_exported_file(desc, fbx_file_to_export, export_path)

    # Finally export to fbx
    bpy.ops.export_scene.fbx(
        filepath=str(export_path),
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        use_custom_props=True,
        bake_space_transform=True,
        use_mesh_modifiers=True,
        add_leaf_bones=True,
        object_types={'MESH', 'EMPTY', 'ARMATURE', 'OTHER'},
    )


class ExporterPanel(bpy.types.Panel):
    bl_label        = "EXPORTER"
    bl_idname       = "UTILS_EXPORTER"
    bl_space_type   = 'VIEW_3D'
    bl_region_type  = 'UI'
    bl_category     = 'EXPORTER'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        # row.label(text="Export selected node", icon = 'EXPORT')

        # custom property from selected node
        if context.object and context.object.type == 'EMPTY' and len(bpy.context.selected_objects) > 0:# and context.object.name == 'export_node*':
            node = bpy.context.selected_objects[0]
            row = layout.row()
            row.prop(node, 'fbx_export_name')

            row = layout.row()
            row.prop(node, 'fbx_export_path')

            row = layout.row()
            row.prop(node, 'fbx_export_isStatic')

            # export button
            row = layout.row()
            row.scale_y = 2.0
            row.operator("export_mesh.fbx_exporter")
            row.label(icon = 'EXPORT')

        # create new node button
        row = layout.row()
        row.scale_y = 1.0
        row.operator("export_mesh.create_new_node")

class CreateExportNode(bpy.types.Operator):
    bl_idname       = "export_mesh.create_new_node"
    bl_label        = "Create a new export node"
    bl_description  = "Creates a new export node positioned at the pivot point of your selection."


    def execute(self, context):
        location = (0, 0, 0)
        if (len(bpy.context.selected_objects) > 0):
            location = (bpy.context.selected_objects[0].location.x, bpy.context.selected_objects[0].location.y, bpy.context.selected_objects[0].location.z)

        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=location, scale=(1, 1, 1))
        bpy.context.selected_objects[0].name = "export_node_"

        return {'FINISHED'}

class ExportOperator(bpy.types.Operator):
    bl_idname       = "export_mesh.fbx_exporter"
    bl_label        = "Export to FBX"
    bl_name         = "FBX_EXPORTER"
    bl_description  = "Exports all objects linked under the export node."

    def execute(self, children):
        parent = bpy.context.selected_objects[0]

        for col in bpy.context.scene.collection.children:
            vlayer = bpy.context.scene.view_layers['View Layer']
            current_col = vlayer.layer_collection.children[col.name].hide_viewport = False

        for o in bpy.context.scene.objects:
            o.hide_set(False)

        get_children()
        bpy.data.objects[parent.name].select_set(True)

        # CHECK if export node has static bool set to true
        if (bpy.context.object.fbx_export_isStatic == True):
            for o in bpy.context.scene.objects: # add custom property on these child objects
                o['isStatic'] = 1
        else:
            for o in bpy.context.scene.objects: # add custom property on these child objects
                o['isStatic'] = 0

        export_to_fbx(children.object)

        bpy.ops.object.select_all(action='INVERT')
        for obj in bpy.context.selected_objects:
            obj.hide_set(True)

        return {'FINISHED'}

# ---------- REGISTER/UNREGISTER CLASSES ---------- #
custom_classes = [
    ExporterPanel,
    ExportOperator,
    CreateExportNode
]

def register():
    bpy.types.Object.fbx_export_path = bpy.props.StringProperty(name='Path', subtype='FILE_PATH')
    bpy.types.Object.fbx_export_name = bpy.props.StringProperty(name='Name')
    bpy.types.Object.fbx_export_isStatic = bpy.props.BoolProperty(name="isStatic", default=False)

    for custom_class in custom_classes:
        bpy.utils.register_class(custom_class)

def unregister():
    del bpy.types.Object.export_path
    del bpy.types.Object.fbx_export_name
    del bpy.types.Object.fbx_export_isStatic

    for custom_class in custom_classes:
        bpy.utils.unregister_class(custom_class)

if __name__ == "__main__":
    register()