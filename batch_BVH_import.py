import os
import bpy

bl_info = {
    "name": "BVH Batch Importer",
    "category": "Import-Export",
}

file = "/home/gwidion/tmp17/120fps/zangado.bvh"
folder = "/home/gwidion/tmp17/120fps"

def find_files(folder):
    files = []
    for file in os.listdir(folder):
        if not file.endswith("bvh"):
            continue
        files.append(os.path.join(folder, file))

    return files

def get_bvh_len(file_path):
    for line in open(file_path):
        if not line.startswith("Frames:"):
            continue
        n = int(line.split(" ")[-1])
    return n
    

def rename_action(filename):
    # TODO
    """
    action_name = file.rsplit(".", 1)[0].lower()

    if not action_name in bpy.data.actions:
        continue

    action = bpy.data.actions[action_name]
    obj = bpy.data.objects["F2"]
    obj.animation_data.action = action
            
    """


def clear_avatar_position():
    avatar = bpy.data.armatures[0].name
    bpy.data.actions[avatar+action_name].name = action_name
    bpy.ops.pose.select_all(action='DESELECT')
    bpy.data.objects[avatar].data.bones["root"].select = True
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.rot_clear()
    bpy.ops.mcp.shift_bone()
    return{'FINISHED'}
            

class BvhImportSettings(bpy.types.PropertyGroup):
    path = bpy.props.StringProperty(
        name="",
        description="Path to dir",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )


class ImportBvhDirectory(bpy.types.Operator):

    bl_idname = "add.bvh_files_to_actions"
    bl_label = "Batch add BVH files to actions"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        folder = context.scene.bvh_batch_importer.path
        print(folder)
        for file in find_files(folder):
            self.process(file)
                    
        return {'FINISHED',}
    
    def load_bvh(self, file):
        print("loading file {}".format(file))
        bvh_len = get_bvh_len(file)
        bpy.context.scene.McpEndFrame = bvh_len
        bpy.ops.mcp.load_and_retarget(filepath=file)

        
    def guess_obj_name(self):
        for armature in bpy.data.armatures:
            if len(armature.name) >= 2 and armature.name[0] in ("M", "F") and armature.name[1].isdigit():
                return armature.name
        raise RuntimeError("Não foi encontrada a armature alvo")
        
    def process(self, file):

        old_names = set(bpy.data.actions.keys())
        self.load_bvh(file)
        new_names = set(bpy.data.actions.keys())
        avatar_name = self.guess_obj_name()

        if len(old_names) == len(new_names):
            raise RuntimeError("Could not find new action name after import")
        action_name = (new_names - old_names).pop()

        new_action_name = os.path.basename(file).split(".")[0]
        bpy.data.actions[action_name].name = new_action_name
        
        bpy.ops.pose.select_all(action='DESELECT')
        
        # Select data column for inexistent "frame 0"
        # and remove it. 
        bpy.context.area.type = 'DOPESHEET_EDITOR'
        bpy.ops.action.select_all_toggle(invert=False)
        bpy.ops.action.select_column(mode='CFRA')
        bpy.ops.action.delete()
        bpy.context.area.type = 'VIEW_3D'
        bpy.data.objects[avatar_name].data.bones["root"].select = True
        bpy.ops.pose.loc_clear()
        bpy.ops.pose.rot_clear()
        bpy.ops.mcp.shift_bone()

"""        
excluir frame 0
avatar = bpy.data.armatures[0].name
bpy.data.actions[avatar+action_name].name = action_name
bpy.ops.pose.select_all(action='DESELECT')
bpy.data.objects[avatar].data.bones["root"].select = True
bpy.ops.pose.loc_clear()
bpy.ops.pose.rot_clear()
bpy.ops.mcp.shift_bone()
"""


class BVHPanel(bpy.types.Panel):
    bl_category = "Tools"
    bl_label = "BVH Batch Importer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "posemode"
    
    
    def draw(self, context):
        layout = self.layout
        object = context.object
        scene = context.scene
        
        layout.label(text="Folder with BVH:")
        row = layout.row()
        row.prop(scene.bvh_batch_importer, "path", text="")
        
        row = layout.row()
        row.operator("add.bvh_files_to_actions")
    

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.bvh_batch_importer = bpy.props.PointerProperty(type=BvhImportSettings)

def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()

