import os, sys

import bpy
import pympi

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


class ElanData:
    def __init__(self, filename):
        self.eaf = pympi.Elan.Eaf(filename)

    def annotations(self, tier_name):
        annotations = self.eaf.get_annotation_data_for_tier(tier_name)
        if not annotations:
            return None
        return annotations


class ElanImporterOperator(bpy.types.Operator):
    bl_idname = "add.start_processing"
    bl_label = "Start Batch Processing"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global SECOND_TO_FRAME
        global ARMATURE_NAME
        SECOND_TO_FRAME = bpy.context.scene.render.fps / 1000
        ARMATURE_NAME = guess_obj_name()
        scene = context.scene
        folder = scene.elan_batch_importer.path
        # print(folder)
        for filename in os.listdir(folder):
            # print("Looking {}.".format(filename))
            if not filename.endswith(".eaf"):
                continue
            if 1:
                path = os.path.join(folder, filename)
                import_elan(path)
            #except RuntimeError as error:
                #print("Não foi possível importar '{}': {}".format(filename, error), file=sys.stderr)
        return {'FINISHED'}


def import_elan(filename):
    action_name = os.path.basename(filename).rsplit(".", 1)[0].lower()

    if not action_name in bpy.data.actions:
        raise RuntimeError("No matching action {} ".format(action_name))

    action = bpy.data.actions[action_name]
    obj = bpy.data.objects[ARMATURE_NAME]
    obj.animation_data.action = action

    elan_data = ElanData(filename)

    annotations = elan_data.annotations("Português")
    if not annotations:
        raise RuntimeError("Não há anotações na trilha 'Português'")

    start_time, end_time = annotations[0][:2]
    start_frame = int(start_time * SECOND_TO_FRAME)
    end_frame = int(end_time * SECOND_TO_FRAME)

    start_end_keyframe(start_frame, end_frame)

    for group_name in ("Mão Direita", "Mão Esquerda",  "Expressão Facial"):
        annotations = elan_data.annotations(group_name)

        print(group_name)
        print(annotations)

        last_inserted_frame = 0
        select_bone_group(group_name)
        if annotations:
            for annotation in annotations:
                last_inserted_frame = insert_keyframe(group_name, annotation, last_inserted_frame, start_frame)
        if end_frame - last_inserted_frame > 15:
            apply_pose(group_name, value=1, frame=last_inserted_frame + 15)
            apply_pose(group_name, value=1, frame=end_frame)


def insert_keyframe(group_name, annotation, last_inserted_frame, start_frame):
    f1 = (annotation[0] * SECOND_TO_FRAME) - start_frame + 1
    f2 = (annotation[1] * SECOND_TO_FRAME) - start_frame + 1
    if last_inserted_frame == 0:
        apply_pose(group_name, value=1, frame=1)
        if f1 > 15:
            apply_pose(group_name, value=1, frame=f1 - 15)
    elif (f1 - last_inserted_frame) >= 15:
        if (f1 - last_inserted_frame) >= 30:
            apply_pose(group_name, value=1, frame=last_inserted_frame + 15)
        apply_pose(group_name, value=1, frame=f1 - 15)

    apply_pose(group_name, value=int(annotation[2]), frame=f1)
    apply_pose(group_name, value=int(annotation[2]), frame=f2)
    return f2


def select_bone_group(group_name):
    obj = bpy.data.objects[ARMATURE_NAME]
    if group_name == "Mão Esquerda":
        group = obj.pose.bone_groups["hand.L"]
        poselib = "maos"
    elif group_name == "Mão Direita":
        group = obj.pose.bone_groups["hand.R"]
        poselib = "maos"
    elif group_name == "Expressão Facial":
        group = obj.pose.bone_groups["face"]
        poselib = "face"
    else:
        print("Unknown value for group name: {}".format(group_name))
        return
    bpy.ops.object.mode_set(mode='POSE')
    obj.pose_library = bpy.data.actions[poselib]
    bpy.ops.pose.select_all(action='DESELECT')
    obj.pose.bone_groups.active = group
    bpy.ops.pose.group_select()


def apply_pose(group_name, value, frame):
    bpy.context.area.type = 'VIEW_3D'
    bpy.context.scene.frame_current = int(frame)
    bpy.ops.poselib.apply_pose(pose_index=(value - 1))
    bpy.ops.anim.keyframe_insert_menu(type='Rotation')


def start_end_keyframe(start_frame, end_frame):
    print(f"Start and end frame for cut: {start_frame}, {end_frame}")
    bpy.context.area.type = 'DOPESHEET_EDITOR'
    obj = bpy.data.objects[ARMATURE_NAME]

    bpy.ops.pose.select_all(action="SELECT")
    # bpy.context.scene.frame_current = end_frame
    # bpy.ops.anim.keyframe_insert_menu(type='Rotation')
    bpy.context.scene.frame_current = end_frame + 1
    bpy.ops.action.select_leftright(mode='RIGHT', extend=False)
    bpy.ops.action.delete()

    bpy.ops.pose.select_all(action="SELECT")
    #bpy.context.scene.frame_current = start_frame
    #bpy.ops.anim.keyframe_insert_menu(type='Rotation')
    bpy.context.scene.frame_current = start_frame - 1
    bpy.ops.action.select_leftright(mode='LEFT', extend=False)
    bpy.ops.action.delete()

    bpy.context.area.type = 'VIEW_3D'
    bpy.ops.pose.select_all(action="SELECT")
    bpy.context.area.type = 'DOPESHEET_EDITOR'
    bpy.ops.action.select_column(mode='CFRA')
    bpy.ops.action.select_all_toggle()
    bpy.ops.action.select_all_toggle()
    bpy.ops.transform.transform(mode='TIME_TRANSLATE', value=(-start_frame +1, 0, 0, 0))
    bpy.context.area.type = 'VIEW_3D'


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.elan_batch_importer = bpy.props.PointerProperty(type=ElanImporterSettings)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
