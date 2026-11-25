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
from styles.tooltip import Tooltip
import asyncio
from styles.highlight_button import HighlightButton
import math


IMAGES_SPACING = 20
IMAGES_SIZE = 250
IMAGES_ICON_SIZE = 150
MAX_IMAGES = 5


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

                'images': ["", "", "", "", ""],     # Images of this template (up to 5)
                'selected_index': 0,                # Index of the currently selected tab in the template widget

                'section_data': section_data,       # Data of our template broken into sections
            })



    def update_section_data(self, section_name, field_name, value):
        self.data['section_data'][section_name][field_name] = value
        self.update_data(section_data=self.data['section_data'])

    

    def build(self):
        super().build()

        # Show the tf to the right of the tabs to name a new section and hide the button
        async def show_new_section_tf(e=None):
            new_section_tf.visible = True
            new_section_button.visible = False
            new_section_button.update()
            new_section_tf.update()
            await new_section_tf.focus()
            await tab_header.scroll_to(offset=-1, duration=ft.Duration(milliseconds=200))

        # Hide the tf for naming a new section and show the new section button again
        async def hide_new_section_tf(e=None):
            new_section_tf.visible = False
            new_section_tf.value = ""
            new_section_tf.error = None
            new_section_tf.update()
            new_section_button.visible = True
            new_section_button.update()

        # Deletes a field from a section
        def delete_field(section_name, field_name):
            del self.data['section_data'][section_name][field_name]
            self.update_data(section_data=self.data['section_data'])
            refresh_sections()

        

        async def create_section(e=None):
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
            
            # Set new section as our active one
            tab_buttons.selected_index = len(tab_buttons.controls) - 1
            tabs.selected_index = tab_buttons.selected_index
            tab_buttons.update()
            tabs.update()

        

        # Builds our section ctrl for sections not in the overview tab
        def build_section_ctrl(section_name, section_data) -> ft.Column:
        
            # Creates a new field within this section when the user submits the text field.
            def create_field(e=None):
                # Get name and add to data
                field_name = return_safe_name(new_field_tf.value) or ""
                if not field_name:  # Handle empty
                    return
                for ctrl in section_row.controls:    # Check if a control with the same field name already exists so we don't get bad sync
                    if ctrl.data == field_name:
                        return
                # Delete the placeholder if its there
                if section_row.controls and section_row.controls[0].data is None:
                    section_row.controls.pop(0)
                # Update the data and add the control to the end of the row
                self.update_section_data(section_name, field_name, None)
                section_row.controls.append(build_field_ctrl(section_name, field_name, None))
                section_row.update()

            # Hides the new field text field and shows the new field button
            def hide_new_field_tf(e=None):
                new_field_tf.visible = False
                new_field_tf.value = ""
                new_field_button.visible = True
                new_field_button.update()
                new_field_tf.update()

            # Shows the new field text field for creating a new field within this section and hides the button
            async def show_new_field_tf(e=None):
                new_field_tf.visible = True
                new_field_button.visible = False
                new_field_button.update()
                new_field_tf.update()
                await new_field_tf.focus()

            # Button for creating a new field within this section
            new_field_button = ft.TextButton(
                "New Field", ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY),
                style=ft.ButtonStyle(bgcolor=ft.Colors.SURFACE, shape=ft.RoundedRectangleBorder(radius=8), mouse_cursor=ft.MouseCursor.CLICK),
                on_click=show_new_field_tf, 
            )

            

            # Text field for entering the name of the new field
            new_field_tf = ft.TextField(
                label="New Field Name", capitalization=ft.TextCapitalization.SENTENCES,
                visible=False, on_submit=create_field, on_blur=hide_new_field_tf,
                dense=True, bgcolor=ft.Colors.SURFACE, data=section_name,
            )

            section_row = ft.Row(
                [
                    build_field_ctrl(section_name, field_name, field_value)
                    for field_name, field_value in section_data.items()
                ] if section_data else [
                    ft.Text("Click New Field to add fields to this section", italic=True, color=ft.Colors.ON_SURFACE_VARIANT)
                ],
                wrap=True, spacing=20, run_spacing=20, expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )

            return ft.Column([section_row, new_field_button, new_field_tf], expand=True, scroll=ft.ScrollMode.HIDDEN, spacing=20) 

        # Builds a normal field control for a section view not inside the overview tab
        def build_field_ctrl(section_name, field_name, field_value):

            def show_delete_field(e=None):
                delete_button.visible = True
                delete_button.update()

            def hide_delete_field(e=None):
                delete_button.visible = False
                delete_button.update()

            # Delete button for removing the field
            delete_button = ft.IconButton(
                ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 18,
                bgcolor=ft.Colors.SURFACE, height=26, width=30,
                on_click=lambda: delete_field(section_name, field_name),
                tooltip=Tooltip("Delete Field"), visible=False,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding.symmetric(vertical=4, horizontal=6), mouse_cursor=ft.MouseCursor.CLICK), 
            )

            # Textfield for the field value
            field_value_ctrl = FieldTextField(
                value=field_value,
                on_blur=lambda e: self.update_section_data(section_name, field_name, e.control.value),
                data=field_name,
            )

            # Gesture detector to show/hide delete button on hover
            return ft.GestureDetector(
                on_enter=show_delete_field, 
                on_exit=hide_delete_field,
                data=field_name,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Row(
                            tight=True,
                            controls=[
                                ft.Text(field_name, size=18, weight=ft.FontWeight.BOLD),
                                delete_button,                   
                            ]
                        ),
                        field_value_ctrl
                    ], 
                ),
            )

        # Builds our field ctrl for the overview tab
        def build_overview_field_ctrl(section_name, field_name, field_value):
            def show_delete_button(e=None):
                delete_button.visible = True
                delete_button.update()

            def hide_delete_button(e=None):
                delete_button.visible = False
                delete_button.update()

            delete_button = ft.IconButton(
                ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 16, 
                bgcolor=ft.Colors.SURFACE,
                on_click=lambda: delete_field(section_name, field_name),
                tooltip=Tooltip(f"Delete Field: {field_name}"), 
                height=20, width=24, 
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=2), visible=False
            )
            
            value_control = OverviewFieldTextField(
                field_value, expand=True,
                on_blur=lambda e: self.update_section_data(section_name, field_name, e.control.value),
                #suffix_icon=delete_button,
            )
            return ft.GestureDetector(
                ft.Row([
                    ft.Text(f"{field_name}", size=14, selectable=True, weight=ft.FontWeight.W_500),
                    value_control,
                    delete_button,
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                on_enter=show_delete_button, on_exit=hide_delete_button,
                data=field_name
            )

        


        # Highlight our thumbnail upon entering it
        def highlight_thumbnail(e: ft.Event[ft.GestureDetector]):
            e.control.content.bgcolor = ft.Colors.SURFACE_CONTAINER_LOW
            e.control.update()

        # Unhighlight our thumbnail upon leaving it
        def unhighlight_thumbnail(e: ft.Event[ft.GestureDetector]):
            e.control.content.bgcolor = ft.Colors.SURFACE
            e.control.update()

        # Build us a column for each section within the overview view
        def build_overview_section_ctrl(section_name: str, section_data: dict) -> ft.Column:

            # Show the text field for adding a new field within this section.
            async def show_new_field_tf(e=None):
                new_field_tf.visible = True
                new_field_button.visible = False
                new_field_tf.update()
                new_field_button.update()
                await new_field_tf.focus()

            # Hide the text field for adding a new field within this section.
            def hide_new_field_tf(e=None):
                new_field_tf.visible = False
                new_field_tf.value = ""
                new_field_button.visible = True
                new_field_tf.update()
                new_field_button.update()

            # Creates a new field within this section when the user submits the text field.
            def create_field(e=None):
                # Get name and add to data
                field_name = return_safe_name(new_field_tf.value) or ""
                if not field_name:  # Handle empty
                    return
                for ctrl in section_column.controls:    # Check if a control with the same field name already exists so we don't get bad sync
                    if ctrl.data == field_name:
                        return
                self.update_section_data(section_name, field_name, None)
                section_column.controls.append(build_overview_field_ctrl(section_name, field_name, None))
                section_column.update()
                
            # Button for adding a new field within this section.
            new_field_button = ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, 22,
                height=32, width=40, 
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8), bgcolor=ft.Colors.SURFACE, mouse_cursor=ft.MouseCursor.CLICK,
                    padding=ft.Padding.symmetric(vertical=5, horizontal=9)
                ),
                on_click=show_new_field_tf,
            )

            # Text field for adding a new field within this section.
            new_field_tf = ft.TextField(
                autofocus=True, label="Field Name", capitalization=ft.TextCapitalization.SENTENCES, visible=False,
                on_submit=create_field, 
                on_blur=hide_new_field_tf, 
                dense=True, bgcolor=ft.Colors.SURFACE,
                margin=ft.Margin.only(left=10), content_padding=ft.Padding.symmetric(vertical=8, horizontal=10)
            )

            # The column to hold those section controls so we can reference it
            section_column = ft.Column([
                ft.Divider(),
                ft.Row([
                    ft.Text(section_name, size=18, weight=ft.FontWeight.BOLD),
                    new_field_button,
                    new_field_tf,
                ]),
                *[
                    build_overview_field_ctrl(section_name, field_name, field_value)
                    for field_name, field_value in section_data.items()
                ],
            ], spacing=8, tight=True)
            
            return section_column

        # Builds out the tab bar and views for each section. Called after adding a new section or deleting one
        def refresh_sections(update: bool=True):

            sections = self.data.get('section_data', {})    # Easier reference
            
            # Rebuild our tab controls. Overview + each section
            tab_buttons.controls = [ft.Text("Overview")] + [
                build_tab_ctrl(index + 1, section_name) for index, section_name in enumerate(self.data.get('section_data', []))
            ]

            overview_sections.controls = [
                build_overview_section_ctrl(section_name, section_data)
                for section_name, section_data in self.data.get('section_data', {}).items()
            ]

            # Rebuild the views for overview + each section
            tab_views.controls = [overview_view] + [
                build_section_ctrl(section_name, section_data) for section_name, section_data in sections.items()
            ]

            # Set the length correctly, and clamp if we were just deleted
            tabs.length = len(tab_buttons.controls)     # Set the length correctly
            if tabs.selected_index > tabs.length - 1:   # Clamp the index if we deleted the last tab
                tabs.selected_index = tabs.length - 1
                tab_buttons.selected_index = tabs.selected_index

            # Update if not on build
            if update:
                self.update()

        # Change the tab manually
        def change_tab(e: ft.Event[ft.Control]):

            if isinstance(e.control, ft.GestureDetector):   # Handle our manual tab switching via gesture detector
                new_index = e.control.data
            else:
                new_index = e.control.selected_index    # Use built in tab switching
            
            self.update_data(**{'selected_index': new_index})   # Update data

            # Update controls
            tabs.selected_index = new_index
            tab_buttons.selected_index = new_index
            tab_buttons.update()
            tabs.update()

        # Builds a tab control for the given section index and name
        def build_tab_ctrl(index: int, section_name: str):

            # Rename the section
            def rename_section(e=None):
                def confirm_rename(e=None):
                    new_section_title = return_safe_name(section_title_tf.value)
                    if new_section_title and new_section_title != section_name and new_section_title not in self.data.get('section_data', {}):
                        self.data['section_data'][new_section_title] = self.data['section_data'].pop(section_name)
                        self.update_data(**{'section_data': self.data['section_data']})
                        refresh_sections()
                        ft.context.page.pop_dialog()
                    else:
                        ft.context.page.pop_dialog()
                        ft.context.page.show_dialog(
                            shad.Toast("Section name already exists or is invalid", variant=shad.ToastVariant.DESTRUCTIVE)
                        )
                    

                section_title_tf = shad.Input(
                    value=section_name,
                    autofocus=True, #capitalization=ft.TextCapitalization.WORDS,
                    on_submit=confirm_rename,
                )

                self.page.show_dialog(
                    shad.Dialog(
                                    
                        # Title of our dialog
                        title=f"Rename {section_name}", 
                            
                        # Main content is text box for user to input story title
                        content=section_title_tf,
            
                        # Our two action buttons at the bottom of the dialog
                        actions=[
                            shad.Button("Cancel", on_click=lambda: ft.context.page.pop_dialog(), color=ft.Colors.ERROR, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM),
                            shad.Button("Rename", on_click=confirm_rename, color=ft.Colors.PRIMARY, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM),
                        ],
                    )
                )

            # Delete the section from data, tab bar, and tab bar views
            def delete_section(e=None):

                # Delete from data
                if section_name in self.data.get('section_data', {}):
                    del self.data['section_data'][section_name]
                    self.update_data(**{'section_data': self.data['section_data']}) 

                # Rebuild our tabs and views after deletion
                refresh_sections()

            # Moves the given section left or right in the tab order
            async def move_section(e: ft.Event[ft.Control]):
                old_index = index - 1   # Offset for the overview tab
                new_index = old_index + e.control.data

                # Clamp new index to valid range - should be impossible but just in case
                if new_index < 0 or new_index >= tabs.length:
                    return

                # Update the data
                section_items = list(self.data.get('section_data', {}).items())
                
                section_items[old_index], section_items[new_index] = section_items[new_index], section_items[old_index]
                
                new_section_data = dict(section_items)
                
                self.data['section_data'] = new_section_data
                self.update_data(**{'section_data': self.data['section_data'], 'selected_index': new_index + 1})
                tabs.selected_index = new_index + 1
                tab_buttons.selected_index = new_index + 1

                # Update U
                refresh_sections()
                
            # First one can't be deleted, since the tabs need 2 or more tabs (overview + section 1)
            if index == 0:   
                return ft.Text(section_name, data=index)

            # Otherwise build out a context menu tab with delete option
            return shad.ContextMenu(    # CM so we can right click on the tab
                content=ft.GestureDetector(     # GD to switch tabs since the CM blocks click events :(
                    ft.Row([ft.Text(section_name)], alignment=ft.MainAxisAlignment.CENTER), # Row forces text to take up the full width of the tab
                    on_tap=change_tab, data=index  # Hold index so we know which tab was right clicked or changed to
                ),
                items=[
                    shad.MenuItem(
                        "Rename", ft.Icon(ft.Icons.EDIT_OUTLINED, ft.Colors.PRIMARY, 20),
                        on_click=rename_section,
                    ),
                    shad.MenuItem(
                        "Move Left", ft.Icon(ft.Icons.ARROW_RIGHT_ALT_OUTLINED, ft.Colors.PRIMARY, 20, rotate=math.pi),
                        on_click=move_section, data=-1, disabled=index <= 1
                    ),
                    shad.MenuItem(
                        "Move Right", ft.Icon(ft.Icons.ARROW_RIGHT_ALT_OUTLINED, ft.Colors.PRIMARY, 20),
                        on_click=move_section, data=1, disabled=index >= len(self.data.get('section_data', {}))
                    ),
                    shad.Separator(ft.Margin.symmetric(vertical=4)),
                    shad.MenuItem(  # Delete section option
                        "Delete Section", ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 20),
                        on_click=delete_section, disabled=len(self.data.get('section_data', {})) <= 1
                    )
                ],
            )

        # Options when setting the image of a widget. Either upload, set a canvas, or clear image
        def set_image_options(index: int) -> list[ft.Control]:
    
            # Called when clicking our upload image button 
            async def upload_image(e: ft.Event):
                # Grab a file and upload it
                files = await ft.FilePicker().pick_files(
                    allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"],
                    dialog_title="Select image"
                )
                if files:
                    file_path = files[0].path
                    try:
                        import base64
                        with open(file_path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            self.data['images'][index] = f"{encoded_string}"
                            self.update_data(**{'images': self.data['images']})
                            refresh_images()
    
                    except Exception:
                        pass
    
            # Sets a canvas as our image
            async def set_canvas_as_image(e=None):
                # Set the canvas id when selecting a canvas from the radio group
                def select_canvas(e: ft.Event[ft.RadioGroup]):
                    nonlocal canvas_id
                    canvas_id = e.data
                # Sets the canvas image from the returned canvas snapshot
                def set_canvas_image(e=None):
                    if canvas_id is None:
                        self.page.pop_dialog()
                        return
                    widget = self.story.get_widget_by_id(canvas_id)
                    if widget is None:
                        self.page.pop_dialog()
                        self.page.show_dialog(shad.Toast("Canvas not found. Please try again."))
                        return
                    snapshot_str = widget.get_snapshot_string(quality="low")
                    if not snapshot_str:
                        self.page.pop_dialog()
                        self.page.show_dialog(shad.Toast("Empty Canvas cannot be made as the image"))
                        return
                    #self.update_data(**{'thumbnail': snapshot_str})
                    refresh_images()
                canvas_id: str = None
                dlg = shad.Dialog(
                    title="Set a Canvas as Image",
                    content=shad.RadioGroup(
                        [
                            shad.Radio(
                                label=widget.data.get('title', 'Untitled'),
                                value=id, 
                            ) for id, widget in self.story.widgets.items() if widget.data.get('tag', '') == "canvas"
                        ],   
                        on_change=select_canvas
                    ),
                    actions=[
                        shad.Button("Cancel", on_click=lambda: self.page.pop_dialog(), color=ft.Colors.ERROR, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM),
                        shad.Button("Select", on_click=set_canvas_image, color=ft.Colors.PRIMARY, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM),
                    ]
                )
                self.page.show_dialog(dlg)
    
            # Resets our image in data and refreshes the images
            async def clear_image(e: ft.Event):
                self.data.get('images', [])[index] = ""
                self.update_data(**{'images': self.data.get('images', [])})
                refresh_images()
    
            # Build the options
            return [
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY, size=20),
                    content="Set Canvas",
                    on_click=set_canvas_as_image,
                    visible=False
                ),
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.IMAGE_SEARCH_OUTLINED, ft.Colors.PRIMARY, size=20),
                    content="Upload Image",
                    on_click=upload_image,
                ),
                shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.HIDE_IMAGE_OUTLINED, ft.Colors.ERROR, size=20),
                    content="Clear Image",
                    on_click=clear_image,
                )
            ]

        # Returns a control for an image in the gallery
        def build_image_ctrl(idx: int, src: str):
            ''' Returns a standardized control to set or clear an image, with the first one being the thumbnail image '''

            return shad.ContextMenu(
                ft.GestureDetector(
                    ft.Container(
                        ft.Image(
                            src=src,
                            gapless_playback=True,
                            width=IMAGES_SIZE + IMAGES_SPACING if idx == 0 else IMAGES_SIZE / 2,
                            height=IMAGES_SIZE + IMAGES_SPACING if idx == 0 else IMAGES_SIZE / 2,
                            fit=ft.BoxFit.CONTAIN,
                        ) if src else ft.Icon(
                            ft.Icons.IMAGE_OUTLINED, 
                            ft.Colors.PRIMARY, 
                            size=IMAGES_ICON_SIZE if idx == 0 else IMAGES_ICON_SIZE / 2
                        ), 
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS, border_radius=8,
                        width=IMAGES_SIZE + IMAGES_SPACING if idx == 0 else IMAGES_SIZE / 2,
                        height=IMAGES_SIZE + IMAGES_SPACING if idx == 0 else IMAGES_SIZE / 2,
                        bgcolor=ft.Colors.SURFACE
                    ), 
                    on_enter=highlight_thumbnail, on_exit=unhighlight_thumbnail, 
                    mouse_cursor=ft.MouseCursor.CLICK,
                    
                ), 
                set_image_options(idx),
                open_on_tap=True,
                tooltip="Upload an Image for this widget",
            )

        # Refresh the image gallery with the current images in the widget's data
        def refresh_images(update=True):
            image_gallery.controls.clear()
            for idx, image in enumerate(self.data.get('images', [])):
                if idx == 0:
                    thumbnail.content = build_image_ctrl(idx, image)
                else:
                    image_gallery.controls.append(build_image_ctrl(idx, image))
            if update:
                thumbnail.update()
                image_gallery.update()


        # Give us some padding
        self.padding = ft.Padding.only(left=16, right=16, top=6, bottom=16)
        
        # Re-style our description tf since it wont be in a sidebar
        self.description_tf.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.description_tf.expand = True
        self.description_tf.label = None
        self.description_tf.margin = None

        thumbnail = ft.Container()  # Just a container to hold the one larger image

        # The row that holds our images at the top of the overview tab
        image_gallery = ft.Row(
            spacing=IMAGES_SPACING, 
            run_spacing=IMAGES_SPACING,  
            min_width=0, min_height=0, 
            max_width=IMAGES_SIZE + IMAGES_SPACING,
            max_height=IMAGES_SIZE + IMAGES_SPACING,
            wrap=True,
            controls=[]
        )

        # Column that holds our sections controls within the overview tab
        overview_sections = ft.Column(spacing=20, tight=True)

        # The 'view' (column) of our Overview tab, which contains our images, description, and modified sections of each section
        overview_view = ft.Column([
            ft.Row(
                spacing=IMAGES_SPACING * 2,
                controls=[
                    thumbnail,      # Holds the first image, which is displayed larger than the rest
                    image_gallery,
                    ft.Column([
                        ft.Text("Description", size=18, weight=ft.FontWeight.BOLD),
                        self.description_tf,
                    ], expand=True)
                ]
            ),
            overview_sections,
        ], scroll=ft.ScrollMode.HIDDEN, expand=True)

        # Button to add new sections
        new_section_button = ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, 22, #size=20,
            bgcolor=ft.Colors.SURFACE,
            height=32, width=40, 
            on_click=show_new_section_tf,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), mouse_cursor=ft.MouseCursor.CLICK, padding=ft.Padding.symmetric(vertical=5, horizontal=9))
        )

        # Textfield for adding new sections
        new_section_tf = ft.TextField(
            autofocus=True, label="Section Name", capitalization=ft.TextCapitalization.SENTENCES, visible=False,
            on_submit=create_section, on_blur=hide_new_section_tf, dense=True, bgcolor=ft.Colors.SURFACE,
            content_padding=ft.Padding.symmetric(vertical=8, horizontal=10)
        )

        # Our buttons that are our 'tabs' controls at the top of the template
        tab_buttons = ft.CupertinoSlidingSegmentedButton(
            thumb_color=ft.Colors.SURFACE,
            selected_index=self.data.get('selected_index', 0),
            on_change=change_tab,
            controls=[ft.Text(section_name) for index, section_name in enumerate(self.data.get('section_data', []))],            
        )

        # Simple header to hold our tab buttons + a button and textfield to add new sections
        tab_header = ft.Row([  
            ft.Row([
                tab_buttons,
                new_section_button, 
                new_section_tf
            ], margin=ft.Margin.only(bottom=10, top=10)),   # Padding for scrollbar bottom, and textfield label on top
        ], scroll=ft.ScrollMode.AUTO)

        # Our tab views
        tab_views = ft.TabBarView(
            expand=True, 
            controls=[
                overview_view
            ] + [
                #ft.Text(section_name) for index, section_name in enumerate(self.data.get('section_data', []))
            ]
        )

        # The tabs control to manage our tab buttons and views
        tabs = ft.Tabs(
            length=len(self.data.get('section_data', [])) + 1, 
            selected_index=self.data.get('selected_index', 0), 
            expand=True,
            content=ft.Column(
                expand=True,
                spacing=20,
                controls=[
                    tab_header, 
                    tab_views
                ]
            ), 
        )

        self.content = tabs

        refresh_images(update=False)
        refresh_sections(update=False)  # Build the sections content


# Styling for fields under the overview tab
@ft.control
class OverviewFieldTextField(ft.TextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dense = True
        self.border = {
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4)
        }
        self.text_style = ft.TextStyle(size=14)
        self.multiline = kwargs.get('multiline', True)
        self.content_padding = ft.Padding.all(4)
        self.capitalization = ft.TextCapitalization.SENTENCES
        self.bgcolor = kwargs.get('bgcolor', ft.Colors.SURFACE_CONTAINER_HIGHEST)

# Styling for fields not under the overview tab
@ft.control
class FieldTextField(ft.TextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.border = {ft.ControlState.DEFAULT: ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.OUTLINE_VARIANT), border_radius=8)}
        self.text_style = ft.TextStyle(size=18)
        self.multiline = kwargs.get('multiline', True)
        self.capitalization = ft.TextCapitalization.SENTENCES
        self.bgcolor = kwargs.get('bgcolor', ft.Colors.SURFACE)
        self.width = 475