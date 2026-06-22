"""Edit Subdivision - batch-edit Subdivision Surface modifier settings.

Adds an N-panel that toggles viewport/render visibility, sets viewport/render
levels and Optimal Display on every Subdivision Surface (SUBSURF) modifier of
the selected objects or the whole scene at once. Objects can be excluded from
processing by name using glob patterns (e.g. *_face_*).
"""

import fnmatch

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup
from bpy_extras.io_utils import ExportHelper, ImportHelper

ADDON_ID = __package__
DEFAULT_PANEL_CATEGORY = "EditSubdiv"


# ---------------------------------------------------------------------------
# Target resolution + live update callbacks
# ---------------------------------------------------------------------------

def _objects_for(settings, context):
    """Objects targeted by the current 'target' enum, minus excluded names."""
    if settings.target == 'SCENE':
        objs = context.scene.objects
    elif settings.target == 'SELECTION':
        objs = context.selected_objects
    else:
        return ()

    if settings.use_exclude:
        patterns = [item.pattern for item in settings.exclude_patterns if item.pattern]
        if patterns:
            objs = [
                obj for obj in objs
                if not any(fnmatch.fnmatchcase(obj.name, pat) for pat in patterns)
            ]
    return objs


def _update_realtime(self, context):
    for obj in _objects_for(self, context):
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                mod.show_viewport = self.realtime


def _update_render(self, context):
    for obj in _objects_for(self, context):
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                mod.show_render = self.render


def _update_editmode(self, context):
    for obj in _objects_for(self, context):
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                mod.show_in_editmode = self.editmode


def _update_on_cage(self, context):
    for obj in _objects_for(self, context):
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                mod.show_on_cage = self.on_cage


def _update_levels_viewport(self, context):
    for obj in _objects_for(self, context):
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                mod.levels = self.levels_viewport


def _update_levels_render(self, context):
    for obj in _objects_for(self, context):
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                mod.render_levels = self.levels_render


def _update_optimal_display(self, context):
    for obj in _objects_for(self, context):
        for mod in obj.modifiers:
            if mod.type == 'SUBSURF':
                mod.show_only_control_edges = self.optimal_display


def _apply_all(settings, context):
    _update_editmode(settings, context)
    _update_on_cage(settings, context)
    _update_realtime(settings, context)
    _update_render(settings, context)
    _update_levels_viewport(settings, context)
    _update_levels_render(settings, context)
    _update_optimal_display(settings, context)


# ---------------------------------------------------------------------------
# Property group
# ---------------------------------------------------------------------------

class EDITSUBDIV_PG_exclude_item(PropertyGroup):
    pattern: StringProperty(
        name="",
        description="Glob pattern matched against object names (e.g. *_face_*)",
        default="",
    )


class EDITSUBDIV_PG_settings(PropertyGroup):
    target: EnumProperty(
        name="",
        items=[
            ('SCENE', "Scene", "All objects in the scene"),
            ('SELECTION', "Selection", "Selected objects only"),
        ],
        default='SELECTION',
    )
    editmode: BoolProperty(name="Edit Mode", update=_update_editmode)
    on_cage: BoolProperty(name="On Cage", update=_update_on_cage)
    realtime: BoolProperty(name="Realtime", update=_update_realtime)
    render: BoolProperty(name="Render", update=_update_render)
    levels_viewport: IntProperty(
        name="Levels Viewport", default=1, min=0, max=6,
        update=_update_levels_viewport,
    )
    levels_render: IntProperty(
        name="Levels Render", default=2, min=0, max=6,
        update=_update_levels_render,
    )
    optimal_display: BoolProperty(
        name="Optimal Display", default=False,
        update=_update_optimal_display,
    )
    use_exclude: BoolProperty(
        name="Exclude",
        description="Skip objects whose name matches any pattern below",
        default=False,
    )
    show_exclude: BoolProperty(default=True)
    exclude_patterns: CollectionProperty(type=EDITSUBDIV_PG_exclude_item)
    exclude_index: IntProperty(name="", default=0)


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------

class EDITSUBDIV_OT_change_all(Operator):
    bl_idname = "edit_subdivision.change_all"
    bl_label = "Apply to All"
    bl_description = "Apply all settings to Subdivision Surface modifiers at once"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _apply_all(context.scene.edit_subdivision, context)
        return {'FINISHED'}


class EDITSUBDIV_OT_exclude_add(Operator):
    bl_idname = "edit_subdivision.exclude_add"
    bl_label = "Add Exclude Pattern"
    bl_description = "Add an exclude pattern row"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        settings = context.scene.edit_subdivision
        settings.exclude_patterns.add()
        settings.exclude_index = len(settings.exclude_patterns) - 1
        return {'FINISHED'}


class EDITSUBDIV_OT_exclude_remove(Operator):
    bl_idname = "edit_subdivision.exclude_remove"
    bl_label = "Remove Exclude Pattern"
    bl_description = "Remove the active exclude pattern"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        settings = context.scene.edit_subdivision
        patterns = settings.exclude_patterns
        idx = settings.exclude_index
        if 0 <= idx < len(patterns):
            patterns.remove(idx)
            settings.exclude_index = min(idx, len(patterns) - 1)
        return {'FINISHED'}


class EDITSUBDIV_OT_exclude_export(Operator, ExportHelper):
    bl_idname = "edit_subdivision.exclude_export"
    bl_label = "Export Patterns"
    bl_description = "Export exclude patterns to a text file"
    bl_options = {'INTERNAL'}

    filename_ext = ".txt"
    filter_glob: StringProperty(default="*.txt", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "edit_subdivision_exclude" + self.filename_ext
        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        settings = context.scene.edit_subdivision
        lines = ["# Edit Subdivision exclude patterns"]
        lines += [item.pattern for item in settings.exclude_patterns if item.pattern]
        try:
            with open(self.filepath, "w", encoding="utf-8") as fp:
                fp.write("\n".join(lines) + "\n")
        except OSError as ex:
            self.report({'ERROR'}, f"Export failed: {ex}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Exported {len(lines) - 1} pattern(s)")
        return {'FINISHED'}


class EDITSUBDIV_OT_exclude_import(Operator, ImportHelper):
    bl_idname = "edit_subdivision.exclude_import"
    bl_label = "Import Patterns"
    bl_description = "Replace exclude patterns with the contents of a text file"
    bl_options = {'INTERNAL'}

    filename_ext = ".txt"
    filter_glob: StringProperty(default="*.txt", options={'HIDDEN'})

    def execute(self, context):
        try:
            with open(self.filepath, "r", encoding="utf-8") as fp:
                raw_lines = fp.readlines()
        except OSError as ex:
            self.report({'ERROR'}, f"Import failed: {ex}")
            return {'CANCELLED'}

        patterns = []
        for line in raw_lines:
            text = line.strip()
            if text and not text.startswith("#"):
                patterns.append(text)

        settings = context.scene.edit_subdivision
        settings.exclude_patterns.clear()
        for pattern in patterns:
            settings.exclude_patterns.add().pattern = pattern
        settings.exclude_index = max(0, min(settings.exclude_index, len(patterns) - 1))
        self.report({'INFO'}, f"Imported {len(patterns)} pattern(s)")
        return {'FINISHED'}


class EDITSUBDIV_UL_exclude(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "pattern", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.pattern)


class EDITSUBDIV_MT_exclude_specials(bpy.types.Menu):
    bl_idname = "EDITSUBDIV_MT_exclude_specials"
    bl_label = "Exclude Patterns"

    def draw(self, context):
        layout = self.layout
        layout.operator(EDITSUBDIV_OT_exclude_import.bl_idname, icon='IMPORT')
        layout.operator(EDITSUBDIV_OT_exclude_export.bl_idname, icon='EXPORT')


# ---------------------------------------------------------------------------
# Panel (built dynamically so the N-panel category is configurable)
# ---------------------------------------------------------------------------

def _build_panel(category):
    """Create and return a Panel class bound to the given N-panel category."""

    class EDITSUBDIV_PT_panel(Panel):
        bl_label = "Edit Subdivision"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = category

        def draw(self, context):
            layout = self.layout
            settings = getattr(context.scene, "edit_subdivision", None)
            if settings is None:
                layout.label(text="Settings unavailable", icon='ERROR')
                return

            layout.prop(settings, "target")

            row = layout.row(align=True)
            row.prop(settings, "on_cage", text="", icon='MESH_DATA')
            row.prop(settings, "editmode", text="", icon='EDITMODE_HLT')
            row.prop(
                settings, "realtime", text="",
                icon='RESTRICT_VIEW_OFF' if settings.realtime else 'RESTRICT_VIEW_ON',
            )
            row.prop(
                settings, "render", text="",
                icon='RESTRICT_RENDER_OFF' if settings.render else 'RESTRICT_RENDER_ON',
            )

            col = layout.column(align=True)
            col.use_property_split = True
            col.use_property_decorate = False
            col.prop(settings, "levels_viewport", text="Levels Viewport")
            col.prop(settings, "levels_render", text="Render")

            col = layout.column()
            col.use_property_split = True
            col.use_property_decorate = False
            col.prop(settings, "optimal_display")

            box = layout.box()
            header = box.row(align=True)
            header.prop(
                settings, "show_exclude", text="",
                icon='TRIA_DOWN' if settings.show_exclude else 'TRIA_RIGHT',
                emboss=False,
            )
            header.prop(settings, "use_exclude", text="Exclude")
            if settings.show_exclude:
                row = box.row()
                row.template_list(
                    "EDITSUBDIV_UL_exclude", "",
                    settings, "exclude_patterns",
                    settings, "exclude_index",
                    rows=3,
                )
                col = row.column(align=True)
                col.operator(EDITSUBDIV_OT_exclude_add.bl_idname, icon='ADD', text="")
                col.operator(EDITSUBDIV_OT_exclude_remove.bl_idname, icon='REMOVE', text="")
                col.separator()
                col.menu(EDITSUBDIV_MT_exclude_specials.bl_idname, icon='DOWNARROW_HLT', text="")

            layout.operator(EDITSUBDIV_OT_change_all.bl_idname, text="Apply to All")

    return EDITSUBDIV_PT_panel


# ---------------------------------------------------------------------------
# Preferences (General section hosting the N-panel category)
# ---------------------------------------------------------------------------

def _category_update(self, context):
    _reregister_panel(self.panel_category)


class EDITSUBDIV_OT_reset_panel_category(Operator):
    """Reset panel category to default"""
    bl_idname = "edit_subdivision.reset_panel_category"
    bl_label = "Reset to Default"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        prefs = _get_prefs()
        if prefs is not None:
            prefs.panel_category = DEFAULT_PANEL_CATEGORY
        return {'FINISHED'}


class EDITSUBDIV_AddonPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    panel_category: StringProperty(
        name="Category (N-Panel)",
        description="Tab category in the N-panel sidebar (bl_category)",
        default=DEFAULT_PANEL_CATEGORY,
        update=_category_update,
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="General")
        split = box.split(factor=0.3, align=True)
        split.label(text="Category (N-Panel)")
        row = split.row(align=True)
        row.prop(self, "panel_category", text="")
        row.operator(
            EDITSUBDIV_OT_reset_panel_category.bl_idname,
            text="",
            icon='LOOP_BACK',
        )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_classes = (
    EDITSUBDIV_PG_exclude_item,
    EDITSUBDIV_PG_settings,
    EDITSUBDIV_UL_exclude,
    EDITSUBDIV_MT_exclude_specials,
    EDITSUBDIV_OT_change_all,
    EDITSUBDIV_OT_exclude_add,
    EDITSUBDIV_OT_exclude_remove,
    EDITSUBDIV_OT_exclude_export,
    EDITSUBDIV_OT_exclude_import,
    EDITSUBDIV_OT_reset_panel_category,
    EDITSUBDIV_AddonPreferences,
)

_panel_cls = None


def _get_prefs():
    addon = bpy.context.preferences.addons.get(ADDON_ID)
    return addon.preferences if addon is not None else None


def _reregister_panel(category):
    global _panel_cls
    if _panel_cls is not None:
        try:
            bpy.utils.unregister_class(_panel_cls)
        except RuntimeError:
            pass
    _panel_cls = _build_panel(category or DEFAULT_PANEL_CATEGORY)
    bpy.utils.register_class(_panel_cls)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.edit_subdivision = PointerProperty(type=EDITSUBDIV_PG_settings)

    prefs = _get_prefs()
    category = prefs.panel_category if prefs is not None else DEFAULT_PANEL_CATEGORY
    _reregister_panel(category)


def unregister():
    global _panel_cls
    if _panel_cls is not None:
        try:
            bpy.utils.unregister_class(_panel_cls)
        except RuntimeError:
            pass
        _panel_cls = None

    if hasattr(bpy.types.Scene, "edit_subdivision"):
        del bpy.types.Scene.edit_subdivision

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
