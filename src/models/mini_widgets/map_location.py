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

                'icon_size': 30,                       # Size of our icon/image on the map, default 30  
                'map_id': "",                       # id of map we're connected too (if we're connected to one)

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

        self.map_label_tf.parent.shadow= ft.BoxShadow(4, 8, ft.Colors.with_opacity(0.25, self.data.get('color'))) 
        self.icon.parent.shadow = ft.BoxShadow(4, 8, ft.Colors.with_opacity(0.25, self.data.get('color')))
        self.update()
        if self._hover_task:
            self._hover_task.cancel()
        self._hover_task = asyncio.create_task(self.show_image_preview())

    # Hides are shadow unless our info display is visible, then stay highlighted
    def stop_highlight(self, e=None):
        # If we're dragging, keep highlighted
        if self.is_dragging:
            return
        self.map_label_tf.parent.shadow = None
        self.icon.parent.shadow = None
        self.update()
        self.hover_timer = 0.0    # Reset our hover timer so we don't show our snapshot after we stop hovering
        if self._hover_task:
            self._hover_task.cancel()
            self._hover_task = None
            if self.image_preview in self.widget.location_stack.controls:
                self.widget.location_stack.controls.remove(self.image_preview)
                self.widget.location_stack.update()

    # Shows our image on the stack after 1 second of hovering
    async def show_image_preview(self):
        ''' Waits 2 seconds; if stop_highlight hasn't cancelled this task, prints a statement '''
        await asyncio.sleep(1)
        if self.data.get('image_base64', ""):
            self.widget.location_stack.controls.append(self.image_preview)
            self.widget.location_stack.update()

    # Overrite parent method of renaming if called from sidebar
    async def handle_rename(self, e=None):
        await self.widget.story.close_menu()
        await self.map_label_tf.focus()

    # Handles deleting our location from the map and data
    async def handle_delete(self, e=None):
        await super().handle_delete()
        self.widget.location_stack.controls.remove(self)
        self.widget.location_stack.update()
        if self.shown_in_sidebar:
            await self.widget.hide_sidebar()

    # Called when color button is clicked
    def get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Changes our color in data and the UI to reflect
        async def change_color(e: ft.Event[ft.MenuItemButton]):
            await self.widget.story.close_menu()
            self.update_data(**{'color': e.control.data})
            self.icon.color = e.control.data
            self.map_label_tf.color = e.control.data
            self.update()

        return [
            ft.MenuItemButton(
                content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                on_click=change_color, close_on_click=True,
                data=color,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
            ) for color in colors
        ]
        
    # Gets our menu options for the location
    def get_menu_options(self) -> list[ft.Control]:
        
        return [
            MenuOptionStyle(
                on_click=self.handle_rename,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text(
                        f"Rename", 
                        weight=ft.FontWeight.BOLD, 
                        overflow=ft.TextOverflow.ELLIPSIS, expand=True
                    ), 
                ]),
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")), 
                        ft.Text("Icon", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self.get_color_options(), 
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
                        ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self.get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Change this locations color"
                ),
                no_padding=True, no_effects=True
            ),
            MenuOptionStyle(
                on_click=self.handle_delete,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text(f"Delete {self.data.get('title')}", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]

    

    # Return a menubar
    def create_sidebar_header_setting_ctrl(self) -> ft.MenuBar:
        # TODO: Change icon, title, color, lore
        # Upload image button
        return ft.MenuBar(
            [
                ft.SubmenuButton(
                    ft.Icon(ft.Icons.SETTINGS_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                    [
                        ft.Text("Set Map Backgroound", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, margin=ft.Margin.only(left=4)),
                        ft.MenuItemButton(      # 
                            leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY), content="Choose Built-in Image", 
                            close_on_click=True,
                            tooltip="Choose a built-in image to use as the background for this map",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(      # Folders
                            leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY), content="Select Canvas", 
                            close_on_click=True,
                            tooltip="Select a canvas to use as the background for this map",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(      # Folders
                            leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY), content="Upload Image", 
                            close_on_click=True,
                            tooltip="Upload an image to use as the background for this map",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ),  
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
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

    # Return a list of header controls
    def create_sidebar_header_ctrls(self) -> list[ft.Control]:
        ctrls = super().create_sidebar_header_ctrls()
        ctrls.insert(1, self.create_sidebar_header_setting_ctrl())
        return ctrls

    # Called when reloading changes to our plot point and in constructor
    def create_sidebar_body_ctrls(self) -> list[ft.Control]:
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        # TODO: Change icon, title, color, lore
        # Show preview if connected to other map
        # Upload image button
        
        
        if self.data.get('image_base64', ""):
            img = ft.Container(
                ft.Image(
                    src=self.data.get('image_base64', ""),
                    width=100,
                    height=100,
                    fit=ft.BoxFit.FILL,
                ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            )
        else:
            img = ft.Icon(ft.Icons.LOCATION_PIN, size=100, color=self.data.get('color', "primary"), expand=False)

        #upload_image_button = ft.IconButton(img, tooltip="Upload Image", on_click=self._upload_location_image, mouse_cursor="click")
        
        return [

            # Add Image
        
            self.sidebar_info_label,
            self.sidebar_info_column,

        ]

    

    # Called from reload_mini_widget
    def build(self):
        """ Rebuilds our map control that holds our plot point and slider """

        super().build()  # Call parent build to set up our data and content

        # Updates state and close any open menus
        async def start_drag(e=None):
            self.is_dragging = True
            await self.widget.story.close_menu()
            
        # Saves the labels value
        async def save_rename(e: ft.Event[ft.TextField]):
            await self.widget.story.close_menu()
            new_title = e.control.value
            self.widget.data.get('mini_widgets_data', {}).get(self.data.get('id'), {}).update({'title': new_title})
            self.widget.update_data(**{'mini_widgets_data': self.widget.data.get('mini_widgets_data', {})})
            self.map_label_tf.parent.update()
        
        # Set our position on the map
        self.left = self.data.get('position', (200, 0))[0]
        self.top = self.data.get('position', (200, 0))[1]
        self.width = 150
        
        # Create our label above our icon in our content
        self.map_label_tf = ft.TextField(
            self.data.get('title'), color=self.data.get('color', None), 
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
            expand=True, text_align=ft.TextAlign.CENTER,
            content_padding=ft.Padding.all(0),
            on_blur=save_rename, dense=True, border_radius=10,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.PRIMARY,
            multiline=True,
        )

        # Create our icon with the right color and size
        self.icon = ft.Icon(
            ft.Icons.LOCATION_PIN, self.data.get('color', None), expand=False, size=self.data.get('icon_size', 30),
            animate_size=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        )
        

        # Set our content in a column with label on top
        self.content = ft.Column([
            ft.GestureDetector(     # Allows us to drag from our tf and still use it by focusing it
                ft.Container(self.map_label_tf, ignore_interactions=True, border_radius=10),
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
            height=100, width=100,
            left=self.left, top=self.top,
            offset=ft.Offset(1.5, -0.5)
        )
        
        
        

        