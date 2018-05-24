# -*- coding: utf-8 -*-

bl_info = {
    "name": "Elan Batch Importer",
    "category": "Import-Export",
    "version": (0, 2, 0),
    "description": "Add-on Development for Finep/Dtita Project",
}


import bpy
import pympi, os

SECOND_TO_FRAME = .03

class BVHPanel(bpy.types.Panel):
    bl_category = "Finep_Dtita_M2"
    bl_label = "BVH Batch Importer v%d.%d.%d" % bl_info["version"]
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "posemode"

    def draw(self, context):
        layout = self.layout
        object = context.object
        scene = context.scene

        layout.label(text="Folder with BVH:")
        row = layout.row()



class ElanBatchImporterPanel(bpy.types.Panel):
    """Creates a panel"""
    bl_label = "Elan Batch Importer v%d.%d.%d" % bl_info["version"]
    bl_idname = "SCENE_PT_elan_batch_importer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Finep_Dtita_M2"
    bl_context = "posemode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.label(text="Folder with Elan:")
        row = layout.row()
        row.prop(scene.elan_batch_importer, "path", text="")

        # TODO To implement the operator for import files
        row = layout.row()
        row.operator("add.start_processing")


class ElanImporterSettings(bpy.types.PropertyGroup):
    path = bpy.props.StringProperty(
        name="",
        description="Path to dir",
        default="",
        maxlen=1024,
        subtype="DIR_PATH"
    )


class ElanImporterOperator(bpy.types.Operator):
    bl_idname = "add.start_processing"
    bl_label = "Start Batch Processing"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        folder = scene.elan_batch_importer.path
        # print(folder)
        for file in os.listdir(folder):
            # print("Looking {}.".format(file))
            if not file.endswith(".eaf"):
                continue
            action_name = file.rsplit(".", 1)[0].lower()

            if not action_name in bpy.data.actions:
                print("No matching action for {}.".format(file))
                continue

            action = bpy.data.actions[action_name]
            obj = bpy.data.objects["F2"]
            obj.animation_data.action = action
            path = os.path.join(folder, file)
            print(path)

            group_name = "Mão Direita"
            annotations = read_elan(path, group_name)
            print("Mão direita:")
            print(annotations)
            if annotations:
                for annotation in annotations:
                    insert_keyframe(group_name, annotation)

            group_name = "Mão Esquerda"
            annotations = read_elan(path, group_name)
            # print("Mão esquerda:")
            # print(annotations[])
            if annotations:
                for annotation in annotations:
                    insert_keyframe(group_name, annotation)

            group_name = "Libras"
            annotations = read_elan(path, group_name)
            print("Libras")
            if not annotations:
                annotations = [(34, 34, '1')]

            for annotation in annotations:
                start_end_keyframe(annotation)
                print(annotation)


        return{'FINISHED'}


def read_elan(file, tier_name):
    eaf = pympi.Elan.Eaf(file)
    annotations = eaf.get_annotation_data_for_tier(tier_name)
    if not annotations:
        return
    return annotations

def select_bone_group(group_name):
    if group_name == "Mão Esquerda":
        group_index = 0
    elif group_name == "Mão Direita":
        group_index = 1
    elif group_name == "Expressão Facial":
        group_index = 2
    else:
        raise ValueError('Invalid value')
    obj = bpy.data.objects['F2']
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='DESELECT')
    obj.pose.bone_groups.active_index = group_index
    bpy.ops.pose.group_select()
    return {'FINISHED'}

def apply_pose(group_name,value):
    bpy.ops.poselib.apply_pose(pose_index=(value - 1))
    return {'FINISHED'}

def insert_keyframe(group_name, annotation):
    select_bone_group(group_name)
    for i in range(2):
        bpy.context.scene.frame_current = annotation[i] * SECOND_TO_FRAME
        apply_pose(group_name, int(annotation[2]))
        bpy.ops.anim.keyframe_insert_menu(type='Rotation')
    bpy.ops.pose.select_all(action='DESELECT')
    bpy.context.scene.frame_current = 1
    return {'FINISHED'}

def start_end_keyframe(annotation):
    for group in ["Mão Direita", "Mão Esquerda"]:
        select_bone_group(group)
        for i in range(2):
            bpy.context.scene.frame_current = annotation[i] * SECOND_TO_FRAME
            apply_pose(group, 1)
            bpy.ops.anim.keyframe_insert_menu(type='Rotation')
        bpy.ops.pose.select_all(action='DESELECT')
        bpy.context.scene.frame_current = 1
    return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.elan_batch_importer = bpy.props.PointerProperty(type=ElanImporterSettings)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()