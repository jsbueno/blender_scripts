# -*- coding: utf-8 -*-
import bpy
import pympi, os

bl_info = {
    "name": "Elan Batch Importer",
    "category": "Import-Export",
    "version": (0, 2, 0),
    "description": "Add-on Development for Finep/Dtita Project",
}



# This is recalculated from the scene.render.fps value.
SECOND_TO_FRAME = .03
ARMATURE_NAME = "F2"


def guess_obj_name():
    for armature in bpy.data.armatures:
        if len(armature.name) >= 2 and armature.name[0] in ("M", "F") and armature.name[1].isdigit():
            return armature.name
    raise RuntimeError("Não foi encontrada a armature alvo")


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
        global SECOND_TO_FRAME
        global ARMATURE_NAME
        SECOND_TO_FRAME = 1 / bpy.context.scene.render.fps
        ARMATURE_NAME = guess_obj_name()
        scene = context.scene
        folder = scene.elan_batch_importer.path
        # print(folder)
        for filename in os.listdir(folder):
            # print("Looking {}.".format(filename))
            if not filename.endswith(".eaf"):
                continue
            action_name = filename.rsplit(".", 1)[0].lower()

            if not action_name in bpy.data.actions:
                print("No matching action for {}.".format(filename), file=sys.stderr)
                continue

            action = bpy.data.actions[action_name]
            obj = bpy.data.objects[ARMATURE_NAME]
            obj.animation_data.action = action
            path = os.path.join(folder, filename)
            print(path)

            elan_data = ElanData(filename)

            for group_name in ("Mão Direita", "Mão Esquerda", "Português", "Expressão Facial"):
                annotations = elan_data.annotations(group_name)
                if group_name == "Português" and not annotations:
                    annotations = [(34, 34, '1')]

                print(group_name)
                print(annotations)
                if annotations and group_name in ("Mão Direita", "Mão Esquerda", "Expressão Facial"):
                    for annotation in annotations:
                        insert_keyframe(group_name, annotation)
        return {'FINISHED'}

class ElanData:
    def __init__(self, filename):
        self.eaf = pympi.Elan.Eaf(filename)

    def annotations(self, tier_name):
        annotations = self.eaf.get_annotation_data_for_tier(tier_name)
        if not annotations:
            return None
        return annotations

def select_bone_group(group_name):
    if group_name == "Mão Esquerda":
        group_index = 0
        poselib = "maos"
    elif group_name == "Mão Direita":
        group_index = 1
        poselib = "maos"
    elif group_name == "Expressão Facial":
        group_index = 2
        poselib = "face"
    else:
        print("Unknown value for group name: {}".format(group_name))
        return
    obj = bpy.data.objects[ARMATURE_NAME]
    bpy.ops.object.mode_set(mode='POSE')
    obj.pose_library = bpy.data.actions[poselib]
    bpy.ops.pose.select_all(action='DESELECT')
    obj.pose.bone_groups.active_index = group_index
    bpy.ops.pose.group_select()

def apply_pose(group_name,value):
    bpy.ops.poselib.apply_pose(pose_index=(value - 1))

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
