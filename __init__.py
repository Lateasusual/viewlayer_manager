import bpy

bl_info = {
    "name": "ViewLayer Manager",
    "description": "Create, Rename and Remove view layers without changing currently active view layer",
    "author": "Lateasusual",
    "version": (1, 0, 1),
    "blender": (2, 80, 0),
    "location": "Header -> View Layer",
    "warning": '',  # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "User Interface"}


class VLM_UL_layers(bpy.types.UIList):

    def draw_item(self,
                  context,
                  layout,
                  data,
                  item,
                  icon: int,
                  active_data,
                  active_property: str,
                  index: int = 0,
                  flt_flag: int = 0):
        self.use_filter_show = True
        split = layout.split(factor=0.8, align=True)
        row = split.row()
        row.alignment = "LEFT"
        row.prop(item, "name", text="", expand=True)
        row.label()
        row = split.row()
        row.alignment = "RIGHT"
        if len(context.scene.view_layers) > 1:
            row.operator("scene.remove_view_layer", icon="PANEL_CLOSE", text="").name = item.name
        if item.use:
            row.prop(item, "use", icon="RESTRICT_RENDER_OFF", text="", toggle=1)
        else:
            row.prop(item, "use", icon="RESTRICT_RENDER_ON", text="", toggle=1)


def disable_collection(col):
    for child in col.children:
        disable_collection(child)
    col.exclude = True


class VLM_OT_remove_view_layer(bpy.types.Operator):
    """Removes a view layer by name, instead of the active layer"""
    bl_label = "Remove view layer by index"
    bl_idname = "scene.remove_view_layer"

    name: bpy.props.StringProperty()

    def execute(self, context):
        layer = context.scene.view_layers[self.name]
        context.scene.view_layers.remove(layer)
        context.scene.active_view_layer_index = context.scene.view_layers.find(context.window.view_layer.name)
        return {'FINISHED'}


class VLM_OT_add_blank_layer(bpy.types.Operator):
    """Adds a new view layer with layer collections disabled by default"""
    bl_label = "Create Blank ViewLayer"
    bl_idname = "scene.view_layer_add_blank"

    def execute(self, context):
        layer = context.scene.view_layers.new(context.view_layer.name)
        for c in layer.layer_collection.children:
            if not context.scene.exclude_only_top_layer:
                disable_collection(c)
            else:
                c.exclude = True
        context.window.view_layer = layer
        context.scene.active_view_layer_index = context.scene.view_layers.find(layer.name)
        return {'FINISHED'}


def update_active_layer(self, context):
    context.window.view_layer = context.scene.view_layers[context.scene.active_view_layer_index]


class ViewLayerManagerPanel(bpy.types.Panel):
    """ View Layer Manager """
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'view_layer'
    bl_label = "ViewLayer Manager"

    @classmethod
    def poll(cls, context):
        return context.engine is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.template_list("VLM_UL_layers", "", scene, "view_layers", scene, "active_view_layer_index")
        layout.prop(context.window.view_layer, "name")
        row = layout.row()
        row.operator("scene.view_layer_add_blank", icon="PLUS")
        row.operator("scene.view_layer_add")
        layout.prop(scene, "exclude_only_top_layer")


classes = [
    VLM_OT_add_blank_layer,
    VLM_OT_remove_view_layer,
    VLM_UL_layers,
    ViewLayerManagerPanel
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.active_view_layer_index = bpy.props.IntProperty(default=0, name="Active view layer index",
                                                                    update=update_active_layer)
    bpy.types.Scene.exclude_only_top_layer = bpy.props.BoolProperty(default=False,
                                                                    name="Exclude only top layer collections")


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
