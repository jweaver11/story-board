'''
Template widget for characters, worlds, and items.
'''

import base64
from copy import deepcopy

import flet as ft
import flet_shadcn_ui as shad

from models.app import app
from models.dataclasses.templates import get_template
from models.views.story import Story
from models.widget import Widget
from utils.safe_string_checker import return_safe_name


def normalize_item_sections(data):
    if isinstance(data, list):
        data = {field['title']: field['content'] for field in data}
    sections = {name: value for name, value in data.items() if isinstance(value, dict)}
    fields = {name: value for name, value in data.items() if not isinstance(value, dict)}
    if fields:
        section_name = 'Basic'
        if section_name in sections and fields.keys() & sections[section_name].keys():
            section_name = 'Other Fields'
            while section_name in sections:
                section_name += '_'
        sections.setdefault(section_name, {}).update(fields)
    return sections


class Template(Widget):
    def __init__(self, title: str, directory_path: str, story: Story, data: dict = {}, is_new: bool = False):
        super().__init__(
            title=title,
            directory_path=directory_path,
            story=story,
            data=data,
            is_new=is_new,
        )

        if self.is_new:
            tag = data.get('tag', 'character')
            section_data = deepcopy(get_template(app.settings.data, tag))
            self.data.update({
                'tag': tag,
                'color': app.settings.data.get('widget_defaults', {}).get(tag, {}).get('color'),
                'additional_images': [],
                'section_data': normalize_item_sections(section_data) if tag == 'item' else section_data,
            })

    def build(self):
        super().build()

        if self.data.get('tag') == 'item':
            sections = normalize_item_sections(self.data.get('section_data', {}))
            if sections != self.data.get('section_data', {}):
                self.update_data(section_data=sections)
                self.data['section_data'] = sections

        if not self.page.platform.is_mobile():
            self.padding = ft.Padding.all(10)

        def update_section_data(section_name, field_name, value):
            self.data['section_data'][section_name][field_name] = value
            self.update_data(section_data=self.data['section_data'])
            for control in field_controls.get((section_name, field_name), []):
                if control is not None and control.value != value:
                    control.value = value
                    control.update()

        async def add_section_clicked(e=None):
            new_section_button.visible = False
            new_section_tf.visible = True
            new_section_tf.value = ""
            new_section_tf.error = None
            new_section_button.update()
            new_section_tf.update()
            await new_section_tf.focus()

        async def hide_new_section_tf(e=None):
            new_section_tf.visible = False
            new_section_tf.value = ""
            new_section_tf.error = None
            new_section_tf.update()
            new_section_button.visible = True
            new_section_button.update()

        async def create_new_section(e=None):
            section_name = return_safe_name(new_section_tf.value)
            if not section_name:
                self.page.show_dialog(shad.Toast("Section name cannot be empty.", variant=shad.ToastVariant.DESTRUCTIVE))
                return
            if section_name in self.data['section_data']:
                self.page.show_dialog(shad.Toast("Section name already exists.", variant=shad.ToastVariant.DESTRUCTIVE))
                return

            self.data['section_data'][section_name] = {}
            self.update_data(section_data=self.data['section_data'])
            await hide_new_section_tf()
            refresh_sections()

        def delete_section(section_name):
            self.page.pop_dialog()
            section_index = list(self.data['section_data']).index(section_name) + 1
            del self.data['section_data'][section_name]
            self.update_data(section_data=self.data['section_data'])
            if section_index < tabs.selected_index:
                tabs.selected_index -= 1
            refresh_sections()


        async def create_new_field(e):
            section_name = e.control.data
            field_name = return_safe_name(e.control.value)
            if not field_name or field_name in self.data['section_data'][section_name]:
                self.page.show_dialog(shad.Toast("Field name already exists or is blank.", variant=shad.ToastVariant.DESTRUCTIVE))
                return
            self.data['section_data'][section_name][field_name] = ""
            self.update_data(section_data=self.data['section_data'])
            refresh_sections()

        def delete_field(section_name, field_name):
            del self.data['section_data'][section_name][field_name]
            self.update_data(section_data=self.data['section_data'])
            refresh_sections()

        def create_field_ctrl(section_name, field_name, field_value):
            value_control = FieldTextField(
                value=field_value,
                on_blur=lambda e: update_section_data(section_name, field_name, e.control.value),
            )
            field_controls.setdefault((section_name, field_name), []).append(value_control)

            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(field_name, weight=ft.FontWeight.W_500, expand=True),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,
                            tooltip=f"Delete Field: {field_name}",
                            on_click=lambda e: delete_field(section_name, field_name),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    value_control,
                ], spacing=4, tight=True),
                padding=12, #border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=8, #bgcolor=ft.Colors.SURFACE, 
                width=400, max_width=400,
            )

        def create_overview_field_ctrl(section_name, field_name, field_value):
            def show_delete_button(e=None):
                delete_button.opacity = 1
                delete_button.update()

            def hide_delete_button(e=None):
                delete_button.opacity = 0
                delete_button.update()

            delete_button = ft.IconButton(
                ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 16,
                opacity=0, on_click=lambda: delete_field(section_name, field_name),
                animate_opacity=ft.Animation(ft.Duration(milliseconds=200), ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                tooltip=f"Delete Field: {field_name}", height=16, #max_height=8,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
            )
            if isinstance(field_value, list):
                value_control = ft.Text("Coming soon", expand=True, color=ft.Colors.ON_SURFACE_VARIANT)
            else:
                value_control = FieldTextField(
                    field_value, expand=True,
                    on_blur=lambda e: update_section_data(section_name, field_name, e.control.value),
                    #suffix_icon=delete_button,
                )
                field_controls.setdefault((section_name, field_name), []).append(value_control)
            return ft.GestureDetector(
                ft.Row([
                    ft.Text(f"{field_name}:", size=14, selectable=True, weight=ft.FontWeight.BOLD),
                    value_control,
                    delete_button,
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                on_enter=show_delete_button, on_exit=hide_delete_button,
            )

        def create_section_ctrl(section_name, section_data):
            def hide_new_field_tf(e=None):
                new_field.visible = False
                new_field.value = ""
                new_field.update()

            async def show_new_field_tf(e=None):
                new_field.visible = True
                new_field.update()
                await new_field.focus()

            new_field = ft.TextField(
                label="New Field Name", capitalization=ft.TextCapitalization.SENTENCES,
                visible=False, on_submit=create_new_field, on_blur=hide_new_field_tf,
                dense=True, bgcolor=ft.Colors.SURFACE, data=section_name,
            )
            return ft.Column([
                ft.Row(
                    [
                        create_field_ctrl(section_name, field_name, field_value)
                        for field_name, field_value in section_data.items()
                    ] if section_data else [
                        ft.Text("Click New Field to add fields to this section", italic=True, color=ft.Colors.ON_SURFACE_VARIANT)
                    ],
                    wrap=True, spacing=12, run_spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Row([
                    shad.Button(
                        "New Field", leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY),
                        bgcolor=ft.Colors.SURFACE, hover_bgcolor=ft.Colors.SURFACE_CONTAINER,
                        size=shad.ButtonSize.SM, color=ft.Colors.ON_SURFACE, hover_color=ft.Colors.ON_SURFACE,
                        on_click=show_new_field_tf,
                    ),
                    new_field,
                ]),
            ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)

        async def upload_additional_image(index):
            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if not files:
                return
            try:
                with open(files[0].path, "rb") as image_file:
                    image = base64.b64encode(image_file.read()).decode('utf-8')
            except (OSError, TypeError) as error:
                self.page.show_dialog(shad.Toast(f"Could not load image: {error}", variant=shad.ToastVariant.DESTRUCTIVE))
                return
            images = list(self.data.get('additional_images', []))
            if index < len(images):
                images[index] = image
            elif len(images) < 4:
                images.append(image)
            self.update_data(additional_images=images)
            refresh_images()

        def remove_additional_image(index):
            images = list(self.data.get('additional_images', []))
            del images[index]
            self.update_data(additional_images=images)
            refresh_images()

        def create_additional_image_ctrl(index, image=None):
            async def upload_image(e):
                await upload_additional_image(index)

            items = [
                shad.MenuItem(
                    "Replace Image" if image else "Upload Image",
                    ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY, 20),
                    on_click=upload_image,
                ),
            ]
            if image:
                items.append(shad.MenuItem(
                    "Remove Image", ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 20),
                    on_click=lambda e: remove_additional_image(index),
                ))
            return shad.ContextMenu(
                ft.Container(
                    ft.Image(src=image, width=115, height=115, fit=ft.BoxFit.COVER, gapless_playback=True)
                    if image else ft.Icon(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, ft.Colors.PRIMARY, size=40),
                    width=115, height=115, alignment=ft.Alignment.CENTER,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=8,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ),
                items, open_on_tap=True,
                tooltip="Manage image" if image else "Add image",
            )

        def refresh_images():
            images = self.data.get('additional_images', [])
            image_gallery.controls = [
                create_additional_image_ctrl(index, image)
                for index, image in enumerate(images[:4])
            ]
            if len(images) < 4:
                image_gallery.controls.append(create_additional_image_ctrl(len(images)))
            image_gallery.update()

        def select_tab(index):
            tabs.selected_index = index
            for button_index, button in enumerate(tab_buttons):
                button.bgcolor = ft.Colors.SURFACE if button_index == index else ft.Colors.TRANSPARENT
            tabs.update()

        def tab_changed(e):
            for index, button in enumerate(tab_buttons):
                button.bgcolor = ft.Colors.SURFACE if index == e.control.selected_index else ft.Colors.TRANSPARENT
            tab_header.update()

        def refresh_sections(update=True):
            field_controls.clear()
            sections = self.data.get('section_data', {})
            overview_sections.controls = [
                ft.Column([
                    ft.Divider(),
                    ft.Text(section_name, size=18, weight=ft.FontWeight.BOLD),
                    *[
                        create_overview_field_ctrl(section_name, field_name, field_value)
                        for field_name, field_value in section_data.items()
                    ],
                ], spacing=8, tight=True)
                for section_name, section_data in sections.items()
            ]
            section_views = [
                create_section_ctrl(section_name, section_data)
                for section_name, section_data in sections.items()
            ]
            section_names = list(sections)
            selected_index = min(tabs.selected_index, len(section_names))
            tab_buttons.clear()
            labels = []
            for index, name in enumerate(["Overview"] + section_names):
                button = ft.Container(
                    ft.Text(name, size=14, weight=ft.FontWeight.W_500),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8), border_radius=4,
                    bgcolor=ft.Colors.SURFACE if index == selected_index else ft.Colors.TRANSPARENT,
                    on_click=lambda e, tab_index=index: select_tab(tab_index),
                )
                tab_buttons.append(button)
                if index > 1:
                    labels.append(shad.ContextMenu(
                        button,
                        [shad.MenuItem(
                            "Delete Section", ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 20),
                            on_click=lambda e, section_name=name: delete_section(section_name),
                        )],
                        open_on_tap=False,
                    ))
                else:
                    labels.append(button)
            tab_header.controls[0] = ft.Container(
                ft.Row(labels, tight=True, spacing=2),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, padding=3, border_radius=6,
            )
            tab_views.controls = [overview_column] + section_views
            tabs.length = len(labels)
            tabs.selected_index = selected_index
            if update:
                tabs.update()

        self.description_tf.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.description_tf.expand = True
        self.description_tf.label = None
        self.description_tf.margin = None
        image_gallery = ft.Row(spacing=20, run_spacing=20, wrap=True, width=270, tight=True)
        images = self.data.get('additional_images', [])
        image_gallery.controls = [
            create_additional_image_ctrl(index, image)
            for index, image in enumerate(images[:4])
        ]
        if len(images) < 4:
            image_gallery.controls.append(create_additional_image_ctrl(len(images)))

        field_controls = {}
        tab_buttons = []
        overview_sections = ft.Column(spacing=20, tight=True)
        overview_column = ft.Column([
            ft.Row([self.select_image_button, image_gallery, self.description_tf,], spacing=20, run_spacing=20),
            ft.Text("Description", size=18, weight=ft.FontWeight.BOLD),
            self.description_tf,
            overview_sections,
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=16)

        new_section_tf = ft.TextField(
            autofocus=True, label="Section Name", capitalization=ft.TextCapitalization.WORDS, visible=False,
            on_submit=create_new_section, on_blur=hide_new_section_tf, dense=True, bgcolor=ft.Colors.SURFACE,
            margin=ft.Margin.only(left=10),
        )
        new_section_button = shad.Button(
            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY),
            bgcolor=ft.Colors.SURFACE, hover_bgcolor=ft.Colors.SURFACE_CONTAINER,
            on_click=add_section_clicked, size=shad.ButtonSize.SM,
        )
        tab_header = ft.Row([ft.Text("Overview"), new_section_button, new_section_tf], scroll=ft.ScrollMode.AUTO)
        tab_views = ft.TabBarView(expand=True, controls=[overview_column])
        tabs = ft.Tabs(
            ft.Column([tab_header, tab_views]), length=1, on_change=tab_changed, expand=True,
        )
        self.content = tabs
        refresh_sections(update=False)


@ft.control
class FieldTextField(ft.TextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dense = True
        self.border = ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4)
        self.text_style = ft.TextStyle(size=14)
        self.multiline = kwargs.get('multiline', True)
        self.content_padding = ft.Padding.all(4)
        self.capitalization = ft.TextCapitalization.SENTENCES
        self.bgcolor = kwargs.get('bgcolor', ft.Colors.SURFACE_CONTAINER_HIGHEST)
