import bpy
from bpy.types import Panel, Operator, AddonPreferences, Menu, UIList
from bpy.props import *

bl_info = {
    "name": "ViewLayer Manager",
    "description": "Create, Rename and Remove view layers without changing currently active view layer",
    "author": "Lateasusual",
    "version": (1, 1, 0),
    "blender": (2, 81, 0),
    "location": "Properties -> View Layer",
    "warning": '',  # used for warning icon and text in addons panel
    "wiki_url": "",
    "category": "User Interface"}


def recursive_attributes(collection, new_collection):
    new_collection.exclude = collection.exclude
    new_collection.holdout = collection.holdout
    new_collection.indirect_only = collection.indirect_only
    new_collection.hide_viewport = collection.hide_viewport

    for i, _ in enumerate(new_collection.children):
        old_child = collection.children[i]
        new_child = new_collection.children[i]
        recursive_attributes(old_child, new_child)

    for i, _ in enumerate(new_collection.collection.objects):
        tmp = collection.collection.objects[i].hide_get()
        new_collection.collection.objects[i].hide_set(tmp)

    return 0


def duplicate_layer(context):
    old_layer = context.window.view_layer
    new_layer = context.scene.view_layers.new(old_layer.name)
    collection = old_layer.layer_collection
    new_collection = new_layer.layer_collection

    for prop in dir(new_layer):
        try:
            attr = getattr(old_layer, prop)
            setattr(new_layer, prop, attr)
        except:
            pass

    if hasattr(old_layer, 'cycles'):
        cycles = old_layer.cycles
        new_cycles = new_layer.cycles
        for prop in dir(new_cycles):
            try:
                attr = getattr(cycles, prop)
                setattr(new_cycles, prop, attr)
            except:
                pass

    recursive_attributes(collection, new_collection)
    context.window.view_layer = new_layer


def add_blank_layer(context):
    layer = context.scene.view_layers.new(context.view_layer.name)
    for c in layer.layer_collection.children:
        c.exclude = True
    context.window.view_layer = layer
    context.scene.active_view_layer_index = context.scene.view_layers.find(layer.name)


def delete_all_but_active(context):
    layer_to_keep = context.window.view_layer
    for layer in context.scene.view_layers:
        if layer == layer_to_keep:
            continue
        else:
            context.scene.view_layers.remove(layer)
    for window in bpy.context.window_manager.windows:
        window.view_layer = layer_to_keep


def delete_view_layer(context, name):
    layer = context.scene.view_layers[name]
    context.scene.view_layers.remove(layer)
    context.scene.active_view_layer_index = context.scene.view_layers.find(context.window.view_layer.name)


remove_items = [
    ('DEFAULT', 'Active', 'Delete active viewlayer'),
    ('NAME', 'By Name', 'Delete view layer by name'),
    ('ALL', 'All but Active', 'Delete all but the active view layer')
]


class VLM_OT_remove_view_layer_extras(bpy.types.Operator):
    """Remove View Layer"""
    bl_label = "Remove View Layer"
    bl_idname = "scene.view_layer_remove_extra"

    mode: bpy.props.EnumProperty(items=remove_items, name='Mode', default='DEFAULT', options=set())
    name: bpy.props.StringProperty(name='Name', description='Name of view layer to remove')

    @classmethod
    def poll(cls, context):
        return len(context.scene.view_layers) > 1

    def execute(self, context):
        if self.mode == 'DEFAULT':
            bpy.ops.scene.view_layer_remove()
        if self.mode == 'NAME':
            if self.name in context.scene.view_layers:
                delete_view_layer(context, self.name)
            else:
                self.report({'INFO'}, 'No view layer name supplied!')
                return {'CANCELLED'}
        if self.mode == 'ALL':
            delete_all_but_active(context)
        return {'FINISHED'}


add_items = [
    ('DEFAULT', 'New', 'New view layer'),
    ('COPY', 'Copy settings', 'New view layer with the same active collections'),
    ('EMPTY', 'Empty', 'New view layer with all collections disabled')
]


def draw_add_options(self, context):
    layout = self.layout
    op = layout.operator('scene.view_layer_add_extra', text='New',
                    text_ctxt='New view layer')
    op.mode = 'DEFAULT'
    op = layout.operator('scene.view_layer_add_extra', text='Copy settings',
                    text_ctxt='New view layer with the same active collections')
    op.mode = 'COPY'
    op = layout.operator('scene.view_layer_add_extra', text='Empty',
                    text_ctxt='New view layer with all collections disabled')
    op.mode = 'EMPTY'


class VLM_OT_add_view_layer_extras(bpy.types.Operator):
    """Add a View Layer"""
    bl_label = "Add View Layer"
    bl_idname = 'scene.view_layer_add_extra'

    mode: EnumProperty(items=add_items, name='mode', default='DEFAULT', options=set())

    def execute(self, context):
        if self.mode == 'DEFAULT':
            bpy.ops.scene.view_layer_add()
        if self.mode == 'COPY':
            duplicate_layer(context)
        if self.mode == 'EMPTY':
            add_blank_layer(context)
        return {'FINISHED'}


class VLM_OT_add_view_layer(bpy.types.Operator):
    """ Add a View Layer """
    bl_label = "Add View Layer"
    bl_idname = 'scene.view_layer_add_menu'

    def execute(self, context):
        context.window_manager.popup_menu(draw_add_options, title="New View Layer")
        return {'FINISHED'}


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
        split = layout.split(factor=0.8, align=True)
        row = split.row()
        row.alignment = "LEFT"
        row.scale_x = 2.0
        row.prop(item, "name", text="", expand=False, emboss=False)
        row.label()
        row = split.row()
        row.alignment = "RIGHT"
        if len(context.scene.view_layers) > 1:
            op = row.operator("scene.view_layer_remove_extra", icon="X", text="", emboss=False)
            op.mode = 'NAME'
            op.name = item.name
        if item.use:
            row.prop(item, "use", icon="CHECKBOX_HLT", text="", emboss=False)
        else:
            row.prop(item, "use", icon="CHECKBOX_DEHLT", text="", emboss=False)


class VLM_PT_Menu(bpy.types.Menu):
    bl_label = "View Layer Extras"

    def draw(self, context):
        self.layout.operator("scene.view_layer_add_extra", icon='DUPLICATE',
                             text="Duplicate current layer").mode = 'COPY'
        self.layout.operator("scene.view_layer_remove_extra", icon='X',
                             text="Remove all but active").mode = 'ALL'


def update_active_layer(self, value):
    bpy.context.window.view_layer = bpy.context.scene.view_layers[value]


def get_active_layer(self):
    return bpy.context.scene.view_layers.find(bpy.context.window.view_layer.name)


def draw_op(self, context):
    if self.is_popover:
        self.layout.ui_units_x = 18
    layout = self.layout
    scene = context.scene
    row = layout.row()
    row.template_list("VLM_UL_layers", "", scene, "view_layers", scene, "active_view_layer_index")
    if not self.is_popover:
        col = row.column(align=True)
        col.operator("scene.view_layer_add_extra", icon="FILE_HIDDEN", text="").mode = 'EMPTY'
        col.operator("scene.view_layer_add_extra", icon="FILE", text="").mode = 'DEFAULT'
        col.separator()
        col.menu("VLM_PT_Menu", icon='DOWNARROW_HLT', text="")


class ViewLayerManagerPanel(bpy.types.Panel):
    """ View Layer Manager """
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'view_layer'
    bl_label = "View Layer Manager"

    @classmethod
    def poll(cls, context):
        return context.engine is not None

    def draw(self, context):
        draw_op(self, context)


class ViewLayerManagerPrefs(AddonPreferences):
    bl_idname = __name__

    replace_dropdown: BoolProperty(name='Replace original ViewLayer menu',
                                   description='Replace the drop down view layer selection menu with a new one',
                                   default=True,
                                   options=set()
                                   )

    replace_add: BoolProperty(name='Replace add button',
                              description='Replace Add View Layer button with a new one',
                              default=True,
                              options=set()
                              )

    def draw(self, context):
        row = self.layout.row(align=True)
        row.prop(self, 'replace_dropdown')
        row.prop(self, 'replace_add')


def draw_right_start(self, context):
    layout = self.layout

    window = context.window
    screen = context.screen
    scene = window.scene

    # If statusbar is hidden, still show messages at the top
    if not screen.show_statusbar:
        layout.template_reports_banner()
        layout.template_running_jobs()

    # Active workspace view-layer is retrieved through window, not through workspace.
    layout.template_ID(window, "scene", new="scene.new",
                       unlink="scene.delete")


# Override for built-in topbar
def draw_right(self, context):
    layout = self.layout
    preferences = context.preferences
    addon_prefs = preferences.addons[__name__].preferences

    window = context.window
    screen = context.screen
    scene = window.scene

    # If statusbar is hidden, still show messages at the top
    if not screen.show_statusbar:
        layout.template_reports_banner()
        layout.template_running_jobs()

    # Active workspace view-layer is retrieved through window, not through workspace.
    layout.template_ID(window, "scene", new="scene.new",
                       unlink="scene.delete")
    row = layout.row(align=True)

    if addon_prefs.replace_dropdown:
        row.popover('ViewLayerManagerPanel', icon='RENDERLAYERS', text="")
        row.prop(context.window.view_layer, 'name', text="")
        row.operator('scene.view_layer_add_menu' if addon_prefs.replace_add else 'scene.view_layer_add',
                     icon='DUPLICATE', text="")
        row.operator("scene.view_layer_remove_extra", icon='X', text="").mode = 'DEFAULT'
    else:
        row.template_search(
            window, "view_layer",
            scene, "view_layers",
            new='scene.view_layer_add_menu' if addon_prefs.replace_add else 'scene.view_layer_add',
            unlink="scene.view_layer_remove")


# Built in topbar
def draw_right_original(self, context):
    layout = self.layout

    window = context.window
    screen = context.screen
    scene = window.scene

    # If statusbar is hidden, still show messages at the top
    if not screen.show_statusbar:
        layout.template_reports_banner()
        layout.template_running_jobs()

    # Active workspace view-layer is retrieved through window, not through workspace.
    layout.template_ID(window, "scene", new="scene.new",
                       unlink="scene.delete")

    row = layout.row(align=True)
    row.template_search(
        window, "view_layer",
        scene, "view_layers",
        new="scene.view_layer_add",
        unlink="scene.view_layer_remove")


classes = [
    VLM_OT_remove_view_layer_extras,
    VLM_OT_add_view_layer_extras,
    VLM_UL_layers,
    ViewLayerManagerPanel,
    VLM_PT_Menu,
    ViewLayerManagerPrefs,
    VLM_OT_add_view_layer,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.active_view_layer_index = IntProperty(name="Active view layer index",
                                                          set=update_active_layer, get=get_active_layer,
                                                          options=set())
    bpy.types.TOPBAR_HT_upper_bar.draw_right = draw_right


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_HT_upper_bar.draw_right = draw_right_original


if __name__ == '__main__':
    register()
