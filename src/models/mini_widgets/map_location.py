'''
Class for marking any point of interest (location) on a map
'''

import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
import math
from styles.text_styles import text_style
import flet.canvas as cv 
from styles.icons import location_icons
from styles.text_fields import TextField
import time
import asyncio
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
from styles.text_styles import TextShadow
from styles.snack_bar import SnackBar

# Locations that appear on our map
class MapLocation(MiniWidget):

    # Constructor. Requires title, widget widget, page reference, and optional data dictionary
    def __init__(
        self, 
        widget: Widget, 
        data: dict = {},
        is_new: bool=False
    ):

        # Parent constructor
        super().__init__(widget=widget, data=data, is_new=is_new) 

        # If we're new, give default values for our data 
        if self.is_new:
            self.data.update({ 
                'tag': "location",            # Tag to identify what type of object this is

                'icon': "location_pin",                 # Which icon to use for this location
                'image_base64': "",                     # If we have a custom image for this location. Shown in sidebar and when hovering over the location on the map

                'label_color': "#FFFFFF",                # Color of the label text on the map, default white
                'icon_size': "Small",                       # Size of our icon on the map. small=30, medium=65, large=100  
                'map_id': "",                       # id of map we're connected too (if we're connected to one)
                'text_outline_thickness': 1,              # Thickness of the outline around our text label on the map

                # Information for our information display
                'info': [
                    {'label': 'Type', 'value': ""},
                    {'label': 'Lore', 'value': ""},
                ]
            })

        # UI elements
        self.map_label: ft.Text     # Label above our icon/image on the map
        self.snapshot: ft.Image     # Snapshot that appears on the stack 
        self.hover_timer: float = 0.0    # Timer for how long we've been hovering over our location, used to show our snapshot after a delay
        self._hover_task: asyncio.Task = None
        self.image_preview: ft.Image
        self.set_image_preview_button: ft.GestureDetector
        
       
    # Moves our location on the map
    async def move_location(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''
        # Update our position
        self.left += e.local_delta.x
        self.top += e.local_delta.y

        # Clamp our position to the bounds of our map
        if self.left < 20:
            self.left = 0
        elif self.left > self.widget.map_width - 150:
            self.left = self.widget.map_width - 150
        if self.top < 20:
            self.top = 20
        elif self.top > self.widget.map_height - 40: 
            self.top = self.widget.map_height - 40
        self.update()

    

    # Called when hovering over our plot point to show the slider
    async def highlight(self, e=None):
        ''' Shows our slider and hides our map_marker. Makes sure all other sliders are hidden '''

        #self.map_label_tf.parent.shadow = ft.BoxShadow(4, 8, ft.Colors.with_opacity(0.25, self.data.get('color'))) 
        self.icon.parent.shadow = ft.BoxShadow(4, 8, ft.Colors.with_opacity(0.25, self.data.get('color')))
        self.update()
        if self._hover_task:
            self._hover_task.cancel()
        self._hover_task = asyncio.create_task(self.show_image_preview())

    # Hides are shadow unless our info display is visible, then stay highlighted
    def stop_highlight(self, e=None):
        if self._hover_task:
            self._hover_task.cancel()
            self._hover_task = None
            if self.image_preview in self.widget.location_stack.controls:
                self.widget.location_stack.controls.remove(self.image_preview)
                self.widget.location_stack.update()
        # If we're dragging, keep highlighted
        if self.is_dragging:
            return
        # Stay highlighted if we're showing our info display
        if self.widget.visible_mw_id == self.data.get('id', ''):
            return
        #self.map_label_tf.parent.shadow = None
        self.icon.parent.shadow = None
        self.update()
        self.hover_timer = 0.0    # Reset our hover timer so we don't show our snapshot after we stop hovering

        

    # Shows our image on the stack after 1 second of hovering
    async def show_image_preview(self):
        ''' Waits 2 seconds; if stop_highlight hasn't cancelled this task, prints a statement '''
        await asyncio.sleep(1)
        if self.data.get('image_base64', ""):
            self.image_preview.left = self.left
            self.image_preview.top = self.top
            self.image_preview.src = self.data.get('image_base64', "")
            self.widget.location_stack.controls.append(self.image_preview)
            self.widget.location_stack.update()

    # Overrite parent method of renaming if called from sidebar
    async def handle_rename(self, e=None):
        await self.widget.story.close_menu()
        await self.map_label_tf.focus()

    # Handles deleting our location from the map and data
    async def handle_delete(self, e=None):
        if self._hover_task:    # If preview is showing, remove it
            self.stop_highlight()
        await super().handle_delete()   # Delete from data
        # Remove from stack and sidebar if we're showing
        self.widget.location_stack.controls.remove(self)
        self.widget.location_stack.update()
        if self.widget.visible_mw_id == self.data.get('id', ''):
            await self.widget.show_info()

    # Called when color button is clicked
    def get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Changes our color in data and the UI to reflect
        async def change_color(e: ft.Event[ft.MenuItemButton]):
            await self.widget.story.close_menu()
            self.update_data(**{'color': e.control.data})
            self.icon.color = e.control.data
            self.update()
            if self.widget.visible_mw_id == self.data.get('id', ''):
                self.widget.sidebar_header.controls = self.create_sidebar_header_ctrls()    # Rebuild our header if we're shown in sidebar
                self.widget.sidebar_header.update()

        return [
            ft.MenuItemButton(
                content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                on_click=change_color, close_on_click=True,
                data=color,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
            ) for color in colors
        ]

    def get_label_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''
        async def change_label_color(e: ft.Event[ft.MenuItemButton]):
            await self.widget.story.close_menu()
            self.update_data(**{'label_color': e.control.data})
            self.map_label_tf.color = e.control.data
            self.map_label_tf.update()
            if self.widget.visible_mw_id == self.data.get('id', ''):
                self.widget.sidebar_header.controls = self.create_sidebar_header_ctrls()    # Rebuild our header if we're shown in sidebar
                self.widget.sidebar_header.update()

        return [
            ft.MenuItemButton(
                content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                on_click=change_label_color, close_on_click=True,
                data=color,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
            ) for color in colors
        ]

    # Handles changing the outline thickness of our label text
    async def change_outline_thickness(self, e: ft.Event[ft.MenuItemButton]):
        # Update data
        await self.widget.story.close_menu()
        self.update_data(**{'text_outline_thickness': int(e.control.content)})
        # Update our text field style
        self.map_label_tf.text_style.shadow = TextShadow(thickness=int(e.control.content))
        self.map_label_tf.update()
        if self.widget.visible_mw_id == self.data.get('id', ''):
            self.widget.sidebar_header.controls = self.create_sidebar_header_ctrls()    # Rebuild our header if we're shown in sidebar
            self.widget.sidebar_header.update()

    def get_icon_options(self) -> list[ft.Control]:
        ''' Returns a list of all available icons for icon changing '''
        async def change_icon(e: ft.Event[ft.MenuItemButton]):
            await self.widget.story.close_menu()
            self.update_data(**{'icon': e.control.data})
            self.icon.icon = location_icons.get(e.control.data, ft.Icons.LOCATION_PIN)
            self.update()
            if self.widget.visible_mw_id == self.data.get('id', ''):
                self.widget.sidebar_header.controls = self.create_sidebar_header_ctrls()    # Rebuild our header if we're shown in sidebar
                self.widget.sidebar_header.update()
        return [
            ft.MenuItemButton(
                ft.Icon(icon, self.data.get('color', "primary")),
                on_click=change_icon, close_on_click=True,
                data=icon_str,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
            ) for icon_str, icon in location_icons.items()
        ]

    async def set_icon_size(self, e: ft.Event[ft.MenuItemButton]):
        ''' Sets the size of our icon on the map '''
        await self.widget.story.close_menu()
        self.update_data(**{'icon_size': e.control.data})
        if e.control.data == "Small":
            self.icon.size = 30
        elif e.control.data == "Medium":
            self.icon.size = 65
        elif e.control.data == "Large":
            self.icon.size = 100
        else:
            self.icon.size = 150
        self.update()
        if self.widget.visible_mw_id == self.data.get('id', ''):
            self.widget.sidebar_header.controls = self.create_sidebar_header_ctrls()    # Rebuild our header if we're shown in sidebar
            self.widget.sidebar_header.update()
        
    # Gets our menu options for the location
    def get_menu_options(self) -> list[ft.Control]:

            
        return [
            
           MenuOptionStyle(
                on_click=self.handle_rename,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text(
                        f"Rename {self.data.get('title')}", 
                        weight=ft.FontWeight.BOLD, 
                        overflow=ft.TextOverflow.ELLIPSIS, expand=True
                    ), 
                ]),
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('label_color', "primary")), 
                        ft.Text("Label Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self.get_label_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Change this locations color"
                ),
                no_padding=True, no_effects=True
            ),
            
            MenuOptionStyle(        # Text outline thickness
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.FORMAT_SIZE_OUTLINED, self.data.get('label_color', "primary")), 
                        ft.Text("Label Outline Size", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    [
                        ft.MenuItemButton(
                            str(i), on_click=self.change_outline_thickness, close_on_click=True, 
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4))
                        ) for i in range(4)], 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_effects=True, no_padding=True
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(location_icons.get(self.data.get('icon'), ft.Icons.LOCATION_PIN), self.data.get('color', "primary")), 
                        ft.Text("Icon", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self.get_icon_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Change this locations icon on the map"
                ),
                no_padding=True, no_effects=True
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")), 
                        ft.Text("Icon Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self.get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Change this locations color"
                ),
                no_padding=True, no_effects=True
            ),
            ft.SubmenuButton(
                f"Icon Size: {self.data.get('icon_size', "Small")}",
                [
                    ft.MenuItemButton(
                        size, data=size, close_on_click=True,
                        on_click=self.set_icon_size, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
                    ) for size in ("Small", "Medium", "Large", "Beefy")
                ],
                tooltip="Adjust the spacing between panels in the preview display.",
                leading=ft.Icon(ft.Icons.PHOTO_SIZE_SELECT_SMALL_OUTLINED, self.data.get('color', "primary")),
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),

            MenuOptionStyle(
                on_click=self.handle_delete,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text(f"Delete {self.data.get('title')}", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]

    # Return a list of header controls
    def create_sidebar_header_ctrls(self) -> list[ft.Control]:
        ctrls: list = super().create_sidebar_header_ctrls()

        # TODO: Figure out map_id if needed and how to impliment
        # Set preview to read the description of the location right below the image
        

        ctrls.append(
            ft.MenuBar(
                [
                    ft.SubmenuButton(
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY),
                        [
                            ft.SubmenuButton(
                                "Label Color",
                                self.get_label_color_options(),
                                leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('label_color', "primary")),
                                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                                style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.SubmenuButton(
                                "Label Outline Size",
                                [
                                    ft.MenuItemButton(
                                        str(i), on_click=self.change_outline_thickness, close_on_click=True, 
                                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4))
                                    ) for i in range(4)
                                ], 
                                leading=ft.Icon(ft.Icons.FORMAT_SIZE_OUTLINED, self.data.get('label_color', "primary")),
                                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                                style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.SubmenuButton(
                                "Icon",
                                self.get_icon_options(), 
                                leading=ft.Icon(location_icons.get(self.data.get('icon'), ft.Icons.LOCATION_PIN), self.data.get('color', "primary")),
                                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                                style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                tooltip="Change this locations icon on the map"
                            ),
                            ft.SubmenuButton(
                                "Icon Color",
                                self.get_color_options(),
                                leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")),
                                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                                style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                tooltip="Change this locations color"
                            ),
                            ft.SubmenuButton(
                                f"Icon Size: {self.data.get('icon_size', "Small")}",
                                [
                                    ft.MenuItemButton(
                                        size, data=size, close_on_click=True,
                                        on_click=self.set_icon_size, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
                                    ) for size in ("Small", "Medium", "Large", "Beefy")
                                ],
                                tooltip="Adjust the spacing between panels in the preview display.",
                                leading=ft.Icon(ft.Icons.PHOTO_SIZE_SELECT_SMALL_OUTLINED, self.data.get('color', "primary")),
                                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                                style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(
                                "Delete", leading=ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR), 
                                close_on_click=True,
                                on_click=self.handle_delete,
                                tooltip="Delete this location",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                        ],
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.BOTTOM_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                        style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                        tooltip="Adjust the settings for this map"
                    ),
                ],
                style=ft.MenuStyle(
                    bgcolor="transparent", shadow_color="transparent",
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                )
            ) 
        )
        return ctrls

    # Options when setting the image of a widget. Either upload, set a canvas, or clear image
    def set_mw_image_options(self) -> list[ft.Control]:

        # Called when clicking our upload image button 
        async def upload_image(e: ft.Event):
            await self.widget.story.close_menu()   # Close menu

            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:

                file_path = files[0].path
                try:
                    import base64

                    with open(file_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        # Save to our data
                        self.update_data(**{'image_base64': f"{encoded_string}"})

                    # Update the image in our widget
                    self.set_image_preview_button.content.icon = ft.Container(
                        ft.Image(
                            src=self.data.get('image_base64', ""),
                            width=150,
                            height=150,
                            fit=ft.BoxFit.FILL,
                        ), border_radius=4, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                    )
                    self.set_image_preview_button.update()

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
                widget = self.widget.story.get_widget_by_id(canvas_id)
                if widget is None:
                    self.page.show_dialog(SnackBar("Canvas not found. Please try again."))
                    self.page.pop_dialog()
                    return

                snapshot_str = widget.get_snapshot_string(quality="low")
                if snapshot_str is None:
                    self.page.show_dialog(SnackBar("Failed to get canvas snapshot. Please try again."))
                    self.page.pop_dialog()
                    return

                self.update_data(**{'image_base64': snapshot_str})
                self.set_image_preview_button.content.icon = ft.Container(
                    ft.Image(
                        src=self.data.get('image_base64', ""),
                        width=150,
                        height=150,
                        fit=ft.BoxFit.FILL,
                    ), 
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                )
                self.set_image_preview_button.update()
                
                self.page.pop_dialog()

            canvas_id: str = None

            dlg = ft.AlertDialog(
                title=ft.Text("Set a Canvas as Image", weight=ft.FontWeight.BOLD),
                content=ft.RadioGroup(
                    ft.Column([
                        ft.Radio(
                            label=widget.data.get('title', 'Untitled'),
                            value=id, mouse_cursor=ft.MouseCursor.CLICK,
                        ) for id, widget in self.widget.story.widgets.items() if widget.data.get('tag', '') == "canvas"],
                    ),
                    on_change=select_canvas
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                    ft.TextButton("Select", on_click=set_canvas_image, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click")),]
            )
            self.page.show_dialog(dlg)

            await self.widget.story.close_menu()   # Close menu

        # Resets our image to nothing and our button to the placeholder
        async def clear_image(e: ft.Event):
            await self.widget.story.close_menu()   # Close menu
            self.update_data(**{'image_base64': ""})
            self.set_image_preview_button.content.icon = ft.Icons.IMAGE_OUTLINED
            self.set_image_preview_button.update()

        # Build the options
        return [
            MenuOptionStyle(
                on_click=set_canvas_as_image,
                content=ft.Row([
                    ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY),
                    ft.Text("Set Canvas", weight=ft.FontWeight.BOLD), 
                ], tooltip="Set a canvas as the image for this widget"),
            ),
            MenuOptionStyle(
                on_click=upload_image,
                content=ft.Row([
                    ft.Icon(ft.Icons.IMAGE_SEARCH_OUTLINED, ft.Colors.PRIMARY),
                    ft.Text("Upload Image", weight=ft.FontWeight.BOLD), 
                ]),
            ),
            MenuOptionStyle(
                on_click=clear_image,
                content=ft.Row([
                    ft.Icon(ft.Icons.HIDE_IMAGE_OUTLINED, ft.Colors.PRIMARY),
                    ft.Text("Clear Image", weight=ft.FontWeight.BOLD), 
                ]),
            ),
        ]

    # Called when reloading changes to our plot point and in constructor
    def create_sidebar_body_ctrls(self) -> list[ft.Control]:
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        # Our image button 
        self.set_image_preview_button = ft.GestureDetector(
            ft.IconButton(
                ft.Container(
                    ft.Image(
                        src=self.data.get('image_base64', ""),
                        width=150,
                        height=150,
                        #fit=ft.BoxFit.FILL,
                    ), #shape=ft.BoxShape.CIRCLE, 
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                ) if self.data.get('image_base64', '') else ft.Icons.IMAGE_OUTLINED, 
                ft.Colors.PRIMARY, icon_size=150,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                tooltip="Upload an Image for this widget", mouse_cursor=ft.MouseCursor.CLICK,
                on_click=lambda: self.widget.story.open_menu(self.set_mw_image_options()), 
            ),
            on_hover=self.set_mouse_coords,
            hover_interval=100
        )
                
        return [

            # Add Image
            ft.Row([self.set_image_preview_button], alignment=ft.MainAxisAlignment.CENTER),
        
            self.sidebar_info_label,
            self.sidebar_info_column,

        ]

    async def save_rename(self, e: ft.Event[ft.TextField]):
        await super().save_rename(e)
        self.map_label_tf.value = e.control.value
        self.map_label_tf.update()
    

    # Called from reload_mini_widget
    def build(self):
        """ Rebuilds our map control that holds our plot point and slider """

        super().build()  # Call parent build to set up our data and content

        # Updates state and close any open menus
        async def start_drag(e=None):
            self.is_dragging = True
            await self.widget.story.close_menu()
            
        
        # Set our position on the map
        self.left = self.data.get('position', (200, 0))[0]
        self.top = self.data.get('position', (200, 0))[1]
        self.width = 150
        
        # Create our label above our icon in our content
        self.map_label_tf = ft.TextField(
            self.data.get('title'), color=self.data.get('label_color', None), 
            text_style=ft.TextStyle(
                weight=ft.FontWeight.BOLD, 
                overflow=ft.TextOverflow.ELLIPSIS, 
                shadow=TextShadow(thickness=self.data.get('text_outline_thickness', 1)),
            ),
            expand=True, text_align=ft.TextAlign.CENTER,
            content_padding=ft.Padding.all(0),
            on_blur=self.save_rename, dense=True, border_radius=4,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.PRIMARY,
            multiline=True,
        )

        # Create our icon with the right color and size
        icon_size_map = {"Small": 30, "Medium": 65, "Large": 100, "Beefy": 150}
        self.icon = ft.Icon(
            location_icons.get(self.data.get('icon'), ft.Icons.LOCATION_PIN), self.data.get('color', None), expand=False, 
            size=icon_size_map.get(self.data.get('icon_size', 30), 30),
            animate_size=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        )
        

        # Set our content in a column with label on top
        self.content = ft.Column([
            ft.GestureDetector(     # Allows us to drag from our tf and still use it by focusing it
                ft.Container(self.map_label_tf, ignore_interactions=True, border_radius=4),
                on_pan_start=start_drag,
                on_pan_update=self.move_location, 
                on_pan_end=self.save_position,
                on_double_tap=self.handle_rename,
                on_tap=self.handle_rename,
                on_enter=self.highlight, on_exit=self.stop_highlight,
                on_secondary_tap=lambda: self.widget.story.open_menu(self.get_menu_options()),
                mouse_cursor=ft.MouseCursor.TEXT,
            ),
            ft.Row([        # Constrain icon size to not fit our whole width
                ft.GestureDetector(     # GD that holds our icon and allows us to drag
                    ft.Container(self.icon, shape=ft.BoxShape.CIRCLE),    # Stick in container so we can apply shadows
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_enter=self.highlight, on_exit=self.stop_highlight,
                    on_pan_start=start_drag,
                    on_pan_update=self.move_location, 
                    on_pan_end=self.save_position,
                    drag_interval=20, 
                    expand=False,
                    on_secondary_tap=lambda: self.widget.story.open_menu(self.get_menu_options()),
                    on_tap=self.show_mini_widget,
                )
            ], tight=True, expand=False),   # End row constrainment
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=False, spacing=0)


        self.image_preview = ft.Image(
            self.data.get('image_base64', ""),
            height=150, width=150,
            left=self.left, top=self.top,
            offset=ft.Offset(1, -0.5)
        )