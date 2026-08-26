'''
The map class for all maps inside our story
Maps are widgets that have their own drawing canvas, background image, information display, and locations
'''

from models.mini_widgets.map_location import MapLocation
from styles.colors import colors
from styles.text_styles import TextShadow
from flet_color_pickers import ColorPicker
import flet as ft
from collections import deque
from models.widget import Widget
from models.views.story import Story
from styles.snack_bar import SnackBar
from models.dataclasses.canvas_state import State
import flet.canvas as cv
import math
from models.app import app
import json
import base64
from io import BytesIO
from PIL import Image
import asyncio
from styles.menu_option_style import MenuOptionStyle
from models.dataclasses.canvas_shape import CanvasShape
from styles.text_fields import TextField
import time
import uuid
import os
from PIL import Image, ImageDraw, ImageTk, ImageColor
import utils.drawing as drawing


MAP_WIDTH = 2000
MAP_HEIGHT = 1000

MINIMUM_SEGMENT_DISTANCE = 2
MAX_SHAPES_BEFORE_CAPTURE = 50
MAX_UNDO_LIST_TASKS = 30

class Map(Widget):

    # Constructor. Requires title, widget widget, page reference, world map widget, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        directory_path: str, 
        story: Story,                  
        data: dict = {},
        is_new: bool = False
    ):
                
        # Parent constructor
        super().__init__(
            title=title,           
            directory_path=directory_path, 
            story=story,
            data=data,  
            is_new=is_new
        ) 


        # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget data
                'tag': "map", 
                'color': app.settings.data.get('widget_defaults', {}).get('map', {}).get('color'),
                'show_sidebar': True,

                # Info about the map
                'draw_mode': app.settings.data.get('widget_defaults', {}).get('map', {}).get('draw_mode'),      # Whether we're in draw mode or not
                'background_image': app.settings.data.get('widget_defaults', {}).get('map', {}).get('background_image'),    # The background image of the map

                'lore': list(),     # List of lores [{'label': "Lore Label", 'content': "Lore Content"}]
                'history': list(),      # List of histories  [{'label': "History Label", 'content': "History Content"}]

                # Holds our labels that sit on the map like locations, but don't have an icon or location
                'labels': {
                    #'id': {'id': 'id_str', 'value': 'Label Text', 'position': (x, y), 'color': 'white', outline_thickness: 1}
                },                              
                              
                # Holds our data for locations
                'mini_widgets_data': {     
                    #'id': {data}
                },

                # Sizing
                "width": (data or {}).get('width') or MAP_WIDTH,
                "height": (data or {}).get('height') or MAP_HEIGHT,

                # Canvas drawing stuff
                'capture': str(),
            
            })

        
        # Drawing elements
        self.state = State()
        self.map_width = self.data.get('width', MAP_WIDTH)
        self.map_height = self.data.get('height', MAP_HEIGHT)
        self.manipulating_shape = False     # Whether we're currently manipulating a shape or not, so we know whether to update our active path or not when dragging
        self.current_path = cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))
        self.active_tool: CanvasShape                    # The active shape being added if we're using a tool

        # The canvas we draw on and the stack that holds our location controls
        self.bg_image: ft.Container
        self.canvas: cv.Canvas 
        self.location_stack: ft.Stack
        self.label_stack: ft.Stack
        self.map_controller: ft.GestureDetector

        # Sidebar elements
        self.sidebar_draw_mode_toggle_button: ft.MenuItemButton
        self.CANVAS_WIDTH = MAP_WIDTH
        self.CANVAS_HEIGHT = MAP_HEIGHT

        # Rest of state elements
        self.new_location_position = (200, 200)     # Where new locations go 
        self.locked_new_location_position = (200, 200)
        self.showing_info: bool = True

        self.current_path: cv.Path = None      # The current path being drawn on the canvas, if any
        
        # Tool and shape stuff
        self.current_tool: CanvasShape = None                     # The active shape being added if we're using a tool
        #self.tool_rotate_handle: ft.GestureDetector         # Handle for rotating the current tool 
        
        # Sidebar controls. Undo/redo buttons
        self.undo_button: ft.IconButton
        self.redo_button: ft.IconButton
        self.canvas_bytes: bytes    # Bytes stored of drawing in memory

    

    async def hide_widget(self, e=None):
        self.story.block_page()
        await super().hide_widget()
        self.story.unblock_page()

    # Class for labels on our map, which are like locations but don't have a sidebar info to show
    class Label(ft.GestureDetector):
        def __init__(self, widget: 'Map', data: dict):

            # Initialize node properties
            self.widget = widget
            self.id = data.get('id', str(uuid.uuid4()))
            self.label = data.get('label', 'Label')
            self.position = data.get('position', (0, 0))
            self.color = data.get('color', None)
            self.outline_thickness = data.get('outline_thickness', 0)

            # State
            self.is_dragging = False
            
            super().__init__(
                left=self.position[0],  # Give us our position
                top=self.position[1],
                width=150, 
                animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                on_secondary_tap=lambda: self.widget.story.open_menu(self.get_label_options()),
                on_pan_start=self.start_drag,
                on_pan_update=self.move_label,
                on_pan_end=self.save_position,
                on_double_tap=self.focus_tf,
                on_tap_up=self.focus_tf,
                on_enter=self.highlight,
                on_exit=self.stop_highlight,
                hover_interval=20, 
                on_hover=self.widget.set_mouse_coords,
                mouse_cursor=ft.MouseCursor.CLICK,
            )

        # Highlight the label
        def highlight(self, e=None):
            self.label_tf.parent.shadow = ft.BoxShadow(4, 8, ft.Colors.with_opacity(0.25, self.color))
            self.update()
        
        # Stop highlighting the label
        def stop_highlight(self, e=None):
            if self.is_dragging:
                return
            self.label_tf.parent.shadow = None
            self.update()

        # Update state and close any open menus
        async def start_drag(self, e=None):
            self.is_dragging = True
            await self.widget.story.close_menu()

        # Moves the node on the stack and updates the drawing that connects the edges
        async def move_label(self, e: ft.DragUpdateEvent):
            
            # Update us visually
            self.left += e.local_delta.x
            self.top += e.local_delta.y
            # Clamp near edges
            if self.left < 20:
                self.left = 0
            elif self.left > self.widget.map_width - 150:
                self.left = self.widget.map_width - 150
            if self.top < 20:
                self.top = 20
            elif self.top > self.widget.map_height - 40: 
                self.top = self.widget.map_height - 40
            self.update()
            
        # Saves updated position to our data
        async def save_position(self, e: ft.DragEndEvent):
            # Update our data to match our new position
            self.is_dragging = False
            self.position = (self.left, self.top)
            self.widget.data.get('labels', {}).get(self.id, {}).update({'position': self.position})
            self.widget.update_data(**{'labels': self.widget.data.get('labels', {})})
            self.widget.set_mouse_coords(e)     # Reset the menu position
            self.stop_highlight()

        # Returns our options for our label
        def get_label_options(self) -> list[MenuOptionStyle]:

            # Changes our label text color in data, on our tf, and updates
            async def change_label_color(e: ft.Event[ft.MenuItemButton]):
                await self.widget.story.close_menu()
                self.color = e.control.data
                self.widget.update_data(**{'labels': {self.id: {'color': self.color}}})
                self.label_tf.color = self.color
                self.update()

            # Handles deleteing a label
            async def handle_delete(e: ft.Event[ft.Button]):
                await self.widget.story.close_menu()
                self.widget.data.get('labels', {}).pop(self.id, None)
                self.widget.update_data(**{'labels': self.widget.data.get('labels', {})})
                self.widget.label_stack.controls.remove(self)
                self.widget.label_stack.update()

            # Handles changing the outline thickness of our label text
            async def change_outline_thickness(e: ft.Event[ft.MenuItemButton]):
                # Update data
                await self.widget.story.close_menu()
                self.outline_thickness = int(e.control.content)
                self.widget.update_data(**{'labels': {self.id: {'outline_thickness': self.outline_thickness}}})
                # Update our text field style
                self.label_tf.text_style.shadow = TextShadow(thickness=self.outline_thickness)
                self.update()

            return [
                MenuOptionStyle(        # Edit label text
                    ft.MenuItemButton(
                        ft.Text("Edit Label", weight=ft.FontWeight.BOLD, expand=True), leading=ft.Icon(ft.Icons.EDIT_OUTLINED, self.color),
                        on_click=self.focus_tf,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),
                    no_effects=True, no_padding=True
                ),
                MenuOptionStyle(            # Change label color
                    ft.SubmenuButton(
                        ft.Row([
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.color), 
                            ft.Text("Label Color", weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        [
                            ft.MenuItemButton(
                                content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                                on_click=change_label_color, close_on_click=True, data=color,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
                            ) for color in colors
                        ],
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),
                    no_padding=True, no_effects=True
                ),

                #MenuOptionStyle(        # Text outline thickness
                    #ft.SubmenuButton(
                        #ft.Row([
                            #ft.Icon(ft.Icons.FORMAT_SIZE_OUTLINED, self.color), 
                            #ft.Text("Label Outline Size", weight=ft.FontWeight.BOLD, expand=True),
                            #ft.Icon(ft.Icons.ARROW_RIGHT),
                       # ], expand=True),
                        #[
                            #ft.MenuItemButton(
                                #str(i), on_click=change_outline_thickness, close_on_click=True, 
                               # style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4))
                           # ) for i in range(4)
                        #], 
                        #menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                       # style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    #),
                   # no_effects=True, no_padding=True
                #),
                MenuOptionStyle(        # Delete label
                    ft.MenuItemButton(
                        ft.Text(f"Delete label", weight=ft.FontWeight.BOLD, expand=True), leading=ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR),
                        on_click=handle_delete, data={"icon": "location_pin"},
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),
                    no_effects=True, no_padding=True
                ),
            ]
        
        # Focuses our textfield for editing
        async def focus_tf(self, e=None):
            await self.widget.story.close_menu()
            await self.label_tf.focus()
            self.label_tf.update()

        # Build our label control
        def build(self):
            
            # Saves the labels value
            async def save_label(e: ft.Event[ft.TextField]):
                await self.widget.story.close_menu()
                self.label = e.control.value
                self.widget.data.get('labels', {}).get(self.id, {}).update({'label': self.label})
                self.widget.update_data(**{'labels': self.widget.data.get('labels', {})})
                self.label_tf.parent.ignore_interactions = True
                self.label_tf.parent.update()
            
            # Text field for editing our label
            self.label_tf = ft.TextField(
                self.label, color=self.color, 
                text_style=ft.TextStyle(
                    weight=ft.FontWeight.BOLD, 
                    overflow=ft.TextOverflow.ELLIPSIS, 
                    shadow=TextShadow(thickness=self.outline_thickness)
                ),
                expand=True, text_align=ft.TextAlign.CENTER,
                content_padding=ft.Padding.all(0),
                on_blur=save_label, dense=True, border_radius=4,
                border_color=ft.Colors.TRANSPARENT,
                focused_border_color=ft.Colors.PRIMARY,
                multiline=True,
            )

            # Set our labels content
            self.content = ft.Container(self.label_tf, ignore_interactions=True, border_radius=4)    # Let Gesture Detector handle all interactions


    async def hide_widget(self, e=None):
        self.story.block_page()
        await super().hide_widget()
        self.story.unblock_page()

    # If we have an active tool/shape that we are manipulating, paint it on the canvas
    async def paint_tool_on_canvas(self):
        ''' Converts the displayed shapes rotation and size onto our active layer and paints it there '''

        
        if not self.canvas.visible or self.current_tool is None:  # Catch errors
            self.page.show_dialog(SnackBar("Error finding visible canvas or tool."))
            return

        self.state.manipulating_shape = False   # Update state
        
        # Text can be rotated, so we can just grab it and put it in the right spot
        if self.current_tool.shape_type == "text":

            # Align our text to account for size of our layer canvas
            text_shape: cv.Text = self.current_tool.cv_shape
            text_shape.x += self.current_tool.left + 2
            text_shape.y += self.current_tool.top + 2
            
            self.canvas.shapes.append(text_shape)
            await self.end_stroke(canvas=self.canvas)
            
            self.map_controller.parent.controls.remove(self.current_tool)
            self.map_controller.parent.controls.remove(self.current_tool.rotate_handle)
            self.map_controller.parent.update()
            return

        # Capture the current tool
        await self.current_tool.canvas.capture()
        shape_capture = await self.current_tool.canvas.get_capture()

        if not shape_capture:
            self.page.show_dialog(SnackBar("Error capturing shape."))
            return

        # Grab the image and rotate
        shape_img = Image.open(BytesIO(shape_capture)).convert("RGBA")
        angle = self.current_tool.rotate.angle
        angle_degrees = -math.degrees(angle)
        rotated = shape_img.rotate(angle_degrees, expand=True, resample=Image.Resampling.BICUBIC)

        # Set rotation (with border padding)
        rotation_cx = self.current_tool.left + (self.current_tool.canvas.width + 4) / 2
        rotation_cy = self.current_tool.top + (self.current_tool.canvas.height + 4) / 2
        paste_x = int(rotation_cx - rotated.width / 2)
        paste_y = int(rotation_cy - rotated.height / 2)


        output = BytesIO()
        rotated.save(output, format="PNG")
        stamped_bytes = output.getvalue()

        self.canvas.shapes.append(cv.Image(stamped_bytes, paste_x, paste_y))
        await self.end_stroke(canvas=self.canvas)
        self.canvas.update()
            
        self.map_controller.parent.controls.remove(self.current_tool)
        self.map_controller.parent.controls.remove(self.current_tool.rotate_handle)
        self.map_controller.parent.update()





    # Updates any live text tools if we changed a setting that would affect it
    def update_tool_preview(self):
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        text_settings = app.settings.data.get('text_settings', {}).copy()

        if self.state.manipulating_shape:
        
            # Fix any paint changess
            self.current_tool.paint = ft.Paint(**paint_settings)

            if self.current_tool.shape_type == "text":
                self.current_tool.cv_shape.style = ft.TextStyle(**text_settings)
                # Match decoration accordingly, since its str -> control doesnt work
                decoration = text_settings.get('decoration', None)
                match decoration:
                    case "underline":
                        self.current_tool.cv_shape.style.decoration = ft.TextDecoration.UNDERLINE
                    case "overline":
                        self.current_tool.cv_shape.style.decoration = ft.TextDecoration.OVERLINE
                    case "line_through":
                        self.current_tool.cv_shape.style.decoration = ft.TextDecoration.LINE_THROUGH
                    case _:
                        self.current_tool.cv_shape.style.decoration = None
    
                self.current_tool.cv_shape.style.shadow = ft.BoxShadow(
                    blur_radius=text_settings.get('shadow', {}).get('blur_radius', 0),
                    color=text_settings.get('shadow', {}).get('color', None),
                    offset=ft.Offset(
                        text_settings.get('shadow', {}).get('offset_x', 0),
                        text_settings.get('shadow', {}).get('offset_y', 0)
                    ),
                )
            elif self.current_tool.shape_type == "rectangle":
                self.current_tool.cv_shape.border_radius = ft.BorderRadius.all(canvas_settings.get('rectangle_border_radius', 0))
            else:
                for shape in self.current_tool.canvas.shapes:
                    shape.paint = ft.Paint(**paint_settings)

            self.current_tool.update()

    # Handles all tap events on the canvas and decides how to handle them based on the current control mode
    async def handle_tap(self, e: ft.TapEvent):

        if self.data.get('draw_mode', False):
            control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
            # Add a point if in draw mode
            if control_mode == "draw":
                await self.add_point(e)
            # Add a tool if in tool mode, unless its a line or erase tool, which are drawn like normal
            elif control_mode == "tool":
                tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
                if tool_name == "line" or tool_name == "erase":
                    await self.add_point(e)
                if tool_name == "fill":
                    await self.fill_tool(e)
                else:
                    await self.add_shape(e)
            # Add text if in text mode
            else:
                await self.add_text(e)
        else:
            self.story.open_menu(self.get_new_item_options())





    # Handles all pan start events
    async def handle_pan_start(self, e: ft.DragStartEvent):
        if not self.data.get('draw_mode', False):
            return
        control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
        # Draw mode, so we start our stroke
        if control_mode == "draw":
            self.start_stroke(e)
        # Tool mode - lines and erase draw like normal, so we start our stroke
        elif control_mode == "tool":
            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            if tool_name == "line" or tool_name == "erase":
                self.start_stroke(e)
        # Tool and Text control themselves, so we don't need to do anything here

    # Handles all pan update events
    async def handle_pan_update(self, e: ft.DragUpdateEvent):
        if not self.data.get('draw_mode', False):
            return

        control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
        # Draw mode, so we update our stroke
        if control_mode == "draw": 
            self.update_stroke(e)
        # Tool mode - lines and erase draw like normal, so we update our stroke
        elif control_mode == "tool":    
            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            if tool_name == "line" or tool_name == "erase":
                self.update_stroke(e)
        # Text and other tools (shapes) handle themselves, so do nothing here

            
    # Handles all pan end events
    async def handle_pan_end(self, e: ft.DragEndEvent):
        if not self.data.get('draw_mode', False):
            return
        control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
        # Draw mode, so we end our stroke
        if control_mode == "draw":  
            await self.end_stroke(e)
        # Tool mode - lines and erase draw like normal, so we end our stroke
        elif control_mode == "tool":   
            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            if tool_name == "line" or tool_name == "erase":
                await self.end_stroke(e)
        # Text and other tools (shapes) handle themselves, so do nothing here

    # Tap event for adding a circular point to the canvas using our paint settings
    async def add_point(self, e: ft.TapEvent):
        canvas: cv.Canvas = self.canvas
        await drawing.draw_point(canvas, e.local_position)
        self.current_path = cv.Points(
            points=[(e.local_position.x, e.local_position.y)],
            paint=ft.Paint(**app.settings.data.get('paint_settings', {}).copy()),
        )
        await self.end_stroke(canvas)   # Force a stroke end since it wont have pan end events


    async def fill_tool(self, e: ft.TapEvent):
        if not self.data.get('draw_mode'):
            return
        # Parse any app color format we may get into a Pillow RGBA tuple.
        def _parse_rgba(color_value) -> tuple[int, int, int, int]:
            def _parse_hex_like(raw: str) -> tuple[int, int, int, int] | None:
                value = raw.strip()

                # Standard #RRGGBB or #RRGGBBAA path first.
                try:
                    color = ImageColor.getcolor(value, "RGBA")
                    if isinstance(color, tuple) and len(color) == 4:
                        rgba = color
                    elif isinstance(color, tuple) and len(color) == 3:
                        rgba = (color[0], color[1], color[2], 255)
                    else:
                        rgba = None
                except Exception:
                    rgba = None

                # Heuristic support for possible #AARRGGBB sources.
                if value.startswith("#") and len(value) == 9:
                    argb_swapped = f"#{value[3:]}{value[1:3]}"
                    try:
                        alt = ImageColor.getcolor(argb_swapped, "RGBA")
                        alt_rgba = (alt[0], alt[1], alt[2], alt[3])
                    except Exception:
                        alt_rgba = None

                    if rgba is None:
                        return alt_rgba
                    if alt_rgba is None:
                        return rgba

                    # Prefer the parse that does not accidentally force near-zero alpha.
                    if rgba[3] <= 8 < alt_rgba[3]:
                        return alt_rgba
                    if alt_rgba[3] <= 8 < rgba[3]:
                        return rgba

                    # Default to #RRGGBBAA interpretation (matches project comments/settings).
                    return rgba

                return rgba

            if color_value is None:
                return (0, 0, 0, 255)

            # Handle Flet opacity format: "color,0.5"
            if isinstance(color_value, str) and "," in color_value:
                base, opacity_str = color_value.rsplit(",", 1)
                try:
                    opacity = float(opacity_str.strip())
                except ValueError:
                    opacity = None

                if opacity is not None:
                    base_rgba = _parse_rgba(base.strip())
                    opacity = max(0.0, min(opacity, 1.0))
                    scaled_alpha = int(round(base_rgba[3] * opacity))
                    return (base_rgba[0], base_rgba[1], base_rgba[2], scaled_alpha)

            # Normalize Flet color names like "primary" -> ft.Colors.PRIMARY if possible.
            if isinstance(color_value, str) and not color_value.startswith("#"):
                maybe_color = getattr(ft.Colors, color_value.upper(), None)
                if maybe_color is not None:
                    color_value = maybe_color

            # Resolve theme semantic names like "primary" to an actual color value when possible.
            if isinstance(color_value, str):
                token = color_value.strip().lower().replace("_", "")
                color_scheme = getattr(getattr(self.page, "theme", None), "color_scheme", None)
                semantic_map = {
                    "primary": "primary",
                    "onprimary": "on_primary",
                    "secondary": "secondary",
                    "onsecondary": "on_secondary",
                    "tertiary": "tertiary",
                    "ontertiary": "on_tertiary",
                    "surface": "surface",
                    "onsurface": "on_surface",
                    "onsurfacevariant": "on_surface_variant",
                    "outline": "outline",
                    "outlinevariant": "outline_variant",
                    "error": "error",
                    "onerror": "on_error",
                }
                attr_name = semantic_map.get(token)
                if color_scheme is not None and attr_name:
                    resolved = getattr(color_scheme, attr_name, None)
                    if resolved:
                        color_value = resolved

            if isinstance(color_value, str):
                parsed = _parse_hex_like(color_value)
                if parsed is not None:
                    return parsed

            try:
                color = ImageColor.getcolor(str(color_value), "RGBA")
                if isinstance(color, tuple) and len(color) == 4:
                    return color
                if isinstance(color, tuple) and len(color) == 3:
                    return (color[0], color[1], color[2], 255)
            except Exception:
                pass
            return (0, 0, 0, 255)

        # Alpha-composite fill over the destination pixel so translucent fills behave naturally.
        def _composite_over(dst: tuple[int, int, int, int], src: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
            src_a = src[3] / 255.0
            dst_a = dst[3] / 255.0
            out_a = src_a + dst_a * (1.0 - src_a)

            if out_a <= 0.0:
                return (0, 0, 0, 0)

            out_r = int(round(((src[0] * src_a) + (dst[0] * dst_a * (1.0 - src_a))) / out_a))
            out_g = int(round(((src[1] * src_a) + (dst[1] * dst_a * (1.0 - src_a))) / out_a))
            out_b = int(round(((src[2] * src_a) + (dst[2] * dst_a * (1.0 - src_a))) / out_a))
            out_alpha = int(round(out_a * 255.0))
            return (out_r, out_g, out_b, out_alpha)

        # RGBA distance check used for tolerance-based flood fill.
        def _within_tolerance(px_a: tuple[int, int, int, int], px_b: tuple[int, int, int, int], tolerance: int) -> bool:
            # Give alpha differences less weight than RGB so anti-aliased edges
            # are easier to include without color bleeding across hard boundaries.
            return (
                abs(px_a[0] - px_b[0])
                + abs(px_a[1] - px_b[1])
                + abs(px_a[2] - px_b[2])
                + int(abs(px_a[3] - px_b[3]) * 0.35)
            ) <= tolerance

        def _count_filled_neighbors(mask_px, x: int, y: int, width: int, height: int) -> int:
            total = 0
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    if nx == x and ny == y:
                        continue
                    if mask_px[nx, ny] != 0:
                        total += 1
            return total

        # Scanline flood fill for better performance on large regions, plus
        # an edge candidate pass to close tiny anti-aliased gaps.
        def _flood_fill_rgba(
            img: Image.Image,
            start_x: int,
            start_y: int,
            fill_color: tuple[int, int, int, int],
            tolerance: int,
        ) -> bool:
            width, height = img.size
            pixels = img.load()
            original_pixels = img.copy().load()
            target_color = pixels[start_x, start_y]

            if _within_tolerance(target_color, fill_color, tolerance):
                return False

            queue = deque([(start_x, start_y)])
            fill_mask = Image.new("L", (width, height), 0)
            fill_mask_px = fill_mask.load()
            edge_candidates: set[tuple[int, int]] = set()

            while queue:
                x, y = queue.popleft()

                if x < 0 or y < 0 or x >= width or y >= height:
                    continue
                if not _within_tolerance(pixels[x, y], target_color, tolerance):
                    continue

                left = x
                while left - 1 >= 0 and _within_tolerance(pixels[left - 1, y], target_color, tolerance):
                    left -= 1

                right = x
                while right + 1 < width and _within_tolerance(pixels[right + 1, y], target_color, tolerance):
                    right += 1

                for fill_x in range(left, right + 1):
                    if fill_mask_px[fill_x, y] != 0:
                        continue
                    pixels[fill_x, y] = _composite_over(pixels[fill_x, y], fill_color)
                    fill_mask_px[fill_x, y] = 255

                    if y - 1 >= 0 and _within_tolerance(pixels[fill_x, y - 1], target_color, tolerance):
                        queue.append((fill_x, y - 1))
                    elif y - 1 >= 0:
                        edge_candidates.add((fill_x, y - 1))
                    if y + 1 < height and _within_tolerance(pixels[fill_x, y + 1], target_color, tolerance):
                        queue.append((fill_x, y + 1))
                    elif y + 1 < height:
                        edge_candidates.add((fill_x, y + 1))

                    if fill_x - 1 >= 0 and not _within_tolerance(pixels[fill_x - 1, y], target_color, tolerance):
                        edge_candidates.add((fill_x - 1, y))
                    if fill_x + 1 < width and not _within_tolerance(pixels[fill_x + 1, y], target_color, tolerance):
                        edge_candidates.add((fill_x + 1, y))

            # Edge anti-gap pass: iteratively close tiny transparent/near-transparent
            # fringe holes around the filled frontier without crossing solid boundaries.
            edge_tolerance = min(1020, tolerance + 100)
            alpha_gap_limit = 112
            frontier = set(edge_candidates)
            for _ in range(3):
                if not frontier:
                    break

                next_frontier: set[tuple[int, int]] = set()
                to_fill: list[tuple[int, int]] = []

                for edge_x, edge_y in frontier:
                    if edge_x < 0 or edge_y < 0 or edge_x >= width or edge_y >= height:
                        continue
                    if fill_mask_px[edge_x, edge_y] != 0:
                        continue

                    filled_neighbors = _count_filled_neighbors(fill_mask_px, edge_x, edge_y, width, height)

                    original_px = original_pixels[edge_x, edge_y]
                    is_soft_gap = original_px[3] <= alpha_gap_limit
                    is_similar_edge = _within_tolerance(original_px, target_color, edge_tolerance)

                    if not is_soft_gap and not is_similar_edge:
                        continue

                    # Soft anti-aliased holes can be single-pixel wide, so allow one
                    # neighbor for transparent fringe; keep stricter gating for color edges.
                    if is_soft_gap and filled_neighbors < 1:
                        continue
                    if not is_soft_gap and filled_neighbors < 2:
                        continue

                    to_fill.append((edge_x, edge_y))

                if not to_fill:
                    break

                for fill_x, fill_y in to_fill:
                    pixels[fill_x, fill_y] = _composite_over(pixels[fill_x, fill_y], fill_color)
                    fill_mask_px[fill_x, fill_y] = 255

                    for ny in range(max(0, fill_y - 1), min(height, fill_y + 2)):
                        for nx in range(max(0, fill_x - 1), min(width, fill_x + 2)):
                            if fill_mask_px[nx, ny] == 0:
                                next_frontier.add((nx, ny))

                frontier = next_frontier

            return True

        canvas: cv.Canvas = self.canvas
        if not canvas.visible:
            return

        # Ensure any pending vector strokes are merged before we sample fill boundaries.
        if canvas.shapes:
            await self.save_canvas(canvas)

        self.story.block_page()
        await asyncio.sleep(0)  # Allow UI to update before potentially long operation.
        capture = self.data.get('capture', '')
        existing_bytes = base64.b64decode(capture) if capture else None
        if existing_bytes:
            image = Image.open(BytesIO(existing_bytes)).convert("RGBA")
        else:
            image = Image.new("RGBA", (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), (0, 0, 0, 0))

        x = max(0, min(int(e.local_position.x), image.width - 1))
        y = max(0, min(int(e.local_position.y), image.height - 1))

        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()

        fill_color = _parse_rgba(paint_settings.get('color', ft.Colors.BLACK))
        fill_tolerance = int(canvas_settings.get('fill_tolerance', 24))
        fill_tolerance = max(0, min(fill_tolerance, 1020))

        changed = _flood_fill_rgba(image, x, y, fill_color, fill_tolerance)
        if not changed:
            self.story.unblock_page()
            return

        output = BytesIO()
        image.save(output, format="PNG")
        filled_bytes = output.getvalue()
        image_str = base64.b64encode(filled_bytes).decode('utf-8')

        # Replace vector shapes with the filled image and persist the map's sole capture.
        canvas.shapes.clear()
        canvas.shapes.append(cv.Image(filled_bytes, 0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT))
        canvas.update()

        self.update_data(**{'capture': image_str})
        self.story.unblock_page()

    # Tap event for adding a tool to the canvas
    async def add_shape(self, e: ft.TapEvent):

        if not self.data.get('draw_mode'):
            return
        
        # Check if we're in tool mode, and what tool we're using
        tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")

        # Skip lines and erase mode, since they are drawn normally, I.E. have no tap event
        if tool_name == "line" or tool_name == "erase":
            return 
        
        # If we are currently manipulating one shape, paint it to the canvas and return early
        if self.state.manipulating_shape:
            self.state.manipulating_shape = False
            await self.paint_tool_on_canvas()
            return
        
        # All other tools/shapes get added here
        self.state.manipulating_shape = True
        self.current_tool = CanvasShape(tool_name, left=e.local_position.x, top=e.local_position.y)
        self.map_controller.parent.controls.append(self.current_tool)
        self.map_controller.parent.update()
        self.map_controller.parent.controls.append(self.current_tool.rotate_handle)
        self.map_controller.parent.update()

    # Adds our canvas shape (text) control to our stack oto start controlling
    async def add_text(self, e: ft.DragStartEvent):
        
        # If we are currently manipulating one shape, paint it to the canvas
        if self.state.manipulating_shape:
            self.state.manipulating_shape = False
            await self.paint_tool_on_canvas()
            return

        # Update state and add our text control to the canvas stack
        self.state.manipulating_shape = True
        self.current_tool = CanvasShape("text", left=e.local_position.x, top=e.local_position.y)
        self.map_controller.parent.controls.append(self.current_tool)
        self.map_controller.parent.update()
        self.map_controller.parent.controls.append(self.current_tool.rotate_handle)
        self.map_controller.parent.update()

    # Adds our initial stroke (cv.Shape) to the canvas with correct settings
    def start_stroke(self, e: ft.DragStartEvent):
        canvas: cv.Canvas = self.canvas
        drawing.start_stroke(canvas, e.local_position, ft.Offset(self.state.x, self.state.y))
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

    # Sets our mouse cursor on hovering for feedback, depending on drawing or using tool
    def set_mouse_cursor(self, update: bool=True):


        # For setting the standard cursor
        def set_standard_cursor():
            # If using tool mode
            if control_mode == "tool":
                if active_tool == "erase" or active_tool == "line": # Erase or line get normal draw cursor
                    standard_mouse_cursor = ft.MouseCursor.PRECISE
                else:
                    standard_mouse_cursor = ft.MouseCursor.CLICK     # Other tools get responsive click cursor
            elif control_mode == "text":
                standard_mouse_cursor = ft.MouseCursor.TEXT
            # Draw mode
            else:
                standard_mouse_cursor = ft.MouseCursor.PRECISE
            self.map_controller.mouse_cursor = standard_mouse_cursor


        # Grab out settings for paint and canvas
        control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
        active_tool = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")

        # TODO: Only use custom on drawing tools and erase. Tools and text should use standard even if the option is set      

        # Sets our mouse cursor as the standard one or custom one depending on setting
        if self.data.get('draw_mode'):
            set_standard_cursor()
        else:
            self.map_controller.mouse_cursor = ft.MouseCursor.CLICK

        

        if update:
            self.map_controller.update()

    # Updates the current stroke shape on the canvas depending on our settings
    def update_stroke(self, e: ft.DragUpdateEvent):
        drawing.update_stroke(self.canvas, e.local_position, ft.Offset(self.state.x, self.state.y))
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

    # Ends the current stroke and flattens it when the retained shape count is too large.
    async def end_stroke(self, e: ft.DragEndEvent=None, canvas: cv.Canvas=None):
        canvas = self.canvas if canvas is None else canvas
        if not canvas.visible or not canvas.shapes:
            return

        committed_shape = canvas.shapes[-1]
        self.add_undo_task({
            'task_type': 'path_stroke',
            'data': committed_shape,
        })
        saved_bytes = await self.save_canvas(canvas)
        if not saved_bytes:
            return

        is_clear_stroke = str(
            getattr(getattr(committed_shape, 'paint', None), 'blend_mode', '')
        ).lower().endswith('clear')
        if len(canvas.shapes) <= MAX_SHAPES_BEFORE_CAPTURE and not is_clear_stroke:
            return

        canvas.shapes.clear()
        canvas.shapes.append(cv.Image(saved_bytes, 0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT))
        canvas.update()
        self.state.undo_list.clear()
        self.state.redo_list.clear()
        self.undo_button.disabled = True
        self.undo_button.icon_color = ft.Colors.OUTLINE_VARIANT
        self.redo_button.disabled = True
        self.redo_button.icon_color = ft.Colors.OUTLINE_VARIANT
        self.undo_button.update()
        self.redo_button.update()

    # Saves any changes to the current layer canvas to its png file, and returns the bytes if other functions need it
    async def save_canvas(self, canvas: cv.Canvas) -> bytes:
        if not canvas.visible:
            return None

        await canvas.capture(pixel_ratio=app.settings.data.get('canvas_settings', {}).get('capture_ratio', 1))
        captured_bytes = await canvas.get_capture()
        await canvas.clear_capture()
        if not captured_bytes:
            self.page.show_dialog(SnackBar("Error capturing map drawing."))
            return None

        image = Image.open(BytesIO(captured_bytes)).convert("RGBA")
        if image.size != (self.CANVAS_WIDTH, self.CANVAS_HEIGHT):
            image = image.resize((self.CANVAS_WIDTH, self.CANVAS_HEIGHT), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format="PNG")
        saved_bytes = output.getvalue()
        self.update_data(**{'capture': base64.b64encode(saved_bytes).decode('utf-8')})
        return saved_bytes

    # Accepts the formatted undo task data, adds it to state and handles UI updates for the undo/redo buttons
    def add_undo_task(self, task_data: dict):
        self.state.undo_list.append(task_data)
        self.state.redo_list.clear()
        if len(self.state.undo_list) > MAX_UNDO_LIST_TASKS:
            self.state.undo_list.pop(0)
        self._update_history_buttons()

    def add_redo_task(self, task_data: dict):
        self.state.redo_list.append(task_data)
        if len(self.state.redo_list) > MAX_UNDO_LIST_TASKS:
            self.state.redo_list.pop(0)
        self._update_history_buttons()

    def _update_history_buttons(self):
        has_undo = bool(self.state.undo_list)
        has_redo = bool(self.state.redo_list)
        self.undo_button.disabled = not has_undo
        self.undo_button.icon_color = ft.Colors.PRIMARY if has_undo else ft.Colors.OUTLINE_VARIANT
        self.redo_button.disabled = not has_redo
        self.redo_button.icon_color = ft.Colors.PRIMARY if has_redo else ft.Colors.OUTLINE_VARIANT
        self.undo_button.update()
        self.redo_button.update()

    # Called when undoing a stroke on the canvas
    async def undo_task(self, e=None):

        # If there's nothing to undo, return early
        if len(self.state.undo_list) == 0:
            return
                
        task = self.state.undo_list.pop()
        if self.canvas.shapes:
            self.canvas.shapes.pop()
            self.canvas.update()
            await self.save_canvas(self.canvas)
        self.add_redo_task(task)
        

    # Called when redoing a stroke on the canvas after a previous undo
    async def redo_task(self, e=None):
        
        # If there's nothing to redo, return early
        if len(self.state.redo_list) == 0:
            return

        task = self.state.redo_list.pop()
        self.canvas.shapes.append(task['data'])
        self.canvas.update()
        await self.save_canvas(self.canvas)
        self.state.undo_list.append(task)
        self._update_history_buttons()


    # Creates our location control in data, on the location_stack, and focuses it in the sidebar
    async def create_location(self, e: ft.Event[ft.Button]=None):
        await self.story.close_menu()   # Close menu
        # Create the new location and add it to data
        new_location = MapLocation(
            widget=self,
            is_new=True,
            data={
                'position': self.locked_new_location_position, 
                'title': "New Location",
            },
        )
        self.update_data(**{'mini_widgets_data': {new_location.data.get('id'): new_location.data}})

        self.location_stack.controls.append(new_location)   # Add to stack
        self.location_stack.update()   # Update stack
        await new_location.show_mini_widget()   # Show in sidebar
    
    # Creates our label control in data and on the location stack
    async def create_label(self, e: ft.Event[ft.Button]=None):
        await self.story.close_menu()

        # Create default data
        new_id = str(uuid.uuid4())
        new_data = {
            'id': new_id,
            'label': "New Label",
            'position': self.locked_new_location_position,
            'color': "#FFFFFF",
            'outline_thickness': 1,
        }

        # Add to data and update
        self.data.get('labels', {}).update({new_id: new_data})
        self.update_data(**{'labels': self.data.get('labels', {})})

        # Add to stack and update
        self.label_stack.controls.append(self.Label(self, new_data))
        self.label_stack.update()
    
    def create_sidebar_body_ctrls(self) -> list[ft.Control]:
        
        # Handles showing text field for new lore and hiding the new lore button
        async def create_lore_clicked(e=None):
            new_lore_button.visible = False
            new_lore_tf.visible = True
            new_lore_button.update()
            new_lore_tf.update()
            await new_lore_tf.focus()

        # Handles showing text field for new history and hiding the new history button
        #async def create_history_clicked(e: ft.Event[ft.Button]):
            #new_history_button.visible = False
            #new_history_tf.visible = True
            #new_history_button.update()
            #new_history_tf.update()
            #await new_history_tf.focus()
        
        # Creates a new lore entry in our data and adds it to the lore column
        def create_lore(e: ft.Event[ft.TextField]):
            self.data.get('lore', []).append({'label': e.control.value, 'content': ""})
            self.update_data(**{'lore': self.data.get('lore', [])})
            lore_column.controls.append(create_new_lore_ctrl(len(lore_column.controls), {'label': e.control.value, 'content': ""}))
            lore_column.update()

        # Creates a new history entry in our data and adds it to the history column
        def create_history(e: ft.Event[ft.TextField]):
            self.data.get('history', []).append({'label': e.control.value, 'content': ""})
            self.update_data(**{'history': self.data.get('history', [])})
            #history_column.controls.append(create_new_history_ctrl(len(history_column.controls), {'label': e.control.value, 'content': ""}))
            #history_column.update()

        # Handles blurring our new lore and history text fields, hiding them, and showing the buttons again
        def blur_textfields(e: ft.Event[ft.TextField]):
            new_lore_button.visible = True
            #new_history_button.visible = True
            new_lore_tf.value = ""
            new_lore_tf.visible = False
            #new_history_tf.value = ""
            #new_history_tf.visible = False
            self.sidebar_body.update()
            pass
        
        # Save value of a lore when text field loses focus
        def save_lore_value(e: ft.Event[ft.TextField]):
            new_value = e.control.value
            idx = e.control.data
            self.data.get('lore', [])[idx].update({'content': new_value})
            self.update_data(**{'lore': self.data.get('lore', [])})

        # Save value of either lore or history text field when it loses focus
        def save_history_value(e: ft.Event[ft.TextField]):
            new_value = e.control.value
            idx = e.control.data
            self.data.get('history', [])[idx].update({'content': new_value})
            self.update_data(**{'history': self.data.get('history', [])})

        # Delete the lore or history text field and remove it from our data and column
        def delete_lore_content(e: ft.Event[ft.IconButton]):
            idx = e.control.parent.data
            self.data.get('lore', []).pop(idx)
            self.update_data(**{'lore': self.data.get('lore', [])})
            lore_column.controls.pop(idx)
            lore_column.update()
            update_indices()

        # Delete the lore or history text field and remove it from our data and column
        def delete_history_content(e: ft.Event[ft.IconButton]):
            idx = e.control.parent.data
            self.data.get('history', []).pop(idx)
            self.update_data(**{'history': self.data.get('history', [])})
            #history_column.controls.pop(idx)
            #history_column.update()
            update_indices()

        # Creates a new lore text field control for our lore column
        def create_new_lore_ctrl(idx: int, data: dict) -> ft.TextField:
            return TextField(
                data.get('content'), label=data.get('label'), data=idx, expand=True, on_blur=save_lore_value, capitalization=ft.TextCapitalization.SENTENCES, multiline=True, dense=True,
                suffix_icon=ft.IconButton(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR, on_click=delete_lore_content, mouse_cursor=ft.MouseCursor.CLICK),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY),
                border_color=ft.Colors.TRANSPARENT, focused_border_color=ft.Colors.PRIMARY,
            )
        
        # Creates a new history text field control for our history column
        def create_new_history_ctrl(idx: int, data: dict) -> ft.TextField:
            return TextField(
                data.get('content'), label=data.get('label'), data=idx, expand=True, on_blur=save_history_value, capitalization=ft.TextCapitalization.SENTENCES, multiline=True, dense=True,
                suffix_icon=ft.IconButton(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR, on_click=delete_history_content, mouse_cursor=ft.MouseCursor.CLICK),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, 
                border_color=ft.Colors.TRANSPARENT, focused_border_color=ft.Colors.PRIMARY,
                label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY) 
            )
        
        # Update the indices of our lore and history controls so we can save them properly after a delete
        def update_indices():
            for idx, ctrl in enumerate(lore_column.controls):
                ctrl.data = idx
            #for idx, ctrl in enumerate(history_column.controls):
                #ctrl.data = idx
        
        
        return [
                ft.Row([
                    ft.Text("Lores", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                    new_lore_button := ft.IconButton(
                        ft.Icons.NEW_LABEL_OUTLINED, ft.Colors.PRIMARY, 
                        tooltip="Add Note",
                        on_click=create_lore_clicked,
                        mouse_cursor="click"
                    ),
                    new_lore_tf := ft.TextField(
                        label="New Lore", expand=True, on_blur=blur_textfields, capitalization=ft.TextCapitalization.WORDS, autofocus=True,
                        on_submit=create_lore, visible=False, dense=True, margin=ft.Margin.only(left=10), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH
        
                    )
                ], spacing=0),
                lore_column := ft.Column([create_new_lore_ctrl(idx, data) for idx, data in enumerate(self.data.get('lore', []))]),

            # ft.Divider(),
                #ft.Row([
                    #ft.Text("Histories", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    #new_history_button := ft.IconButton(
                        #ft.Icons.NEW_LABEL_OUTLINED, self.data.get('color', "primary"), 
                        #tooltip="Add Note",
                        #on_click=create_history_clicked,
                        #mouse_cursor="click"
                    #),
                    #new_history_tf := ft.TextField(
                        #label="New History", expand=True, on_blur=blur_textfields, capitalization=ft.TextCapitalization.WORDS, autofocus=True,
                        #on_submit=create_history, visible=False, dense=True, margin=ft.Margin.only(left=10), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH
                    #)
                #], spacing=0),
                #history_column := ft.Column([create_new_history_ctrl(idx, data) for idx, data in enumerate(self.data.get('history', []))]),

                #ft.Divider(),         
                #ft.Text("Locations", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),


                ft.Divider(),
                self.sidebar_notes_label,
                self.sidebar_notes_column,

            
        ]  
            
            
    async def hide_sidebar(self, e=None): 
        await super().hide_sidebar(e)
        self.showing_info = False

    # Called when clicking to show our info in the sidebar
    async def show_info(self, e=None):

        # Close menu
        await self.story.close_menu()
        if self.showing_info:   # Already showing info, so no need to re-call it
            return
        
        # Re-build header, body, and footer
        self.sidebar_header.controls = self.create_sidebar_header_ctrls()
        self.sidebar_body.controls = self.create_sidebar_body_ctrls()  
        self.sidebar_footer.controls = [self.description_tf]
        self.visible_mw_id = ""     # Reset our state for tracking visible mw

        # Applies the update
        if not await self.show_sidebar():   # If already showing, just update the sidebar
            self.sidebar.update()
        self.showing_info = True


    # Sets our background image
    async def set_bg_image(self, e):
        return

    
    def get_new_item_options(self) -> list[ft.Control]:

        # Locks our position at wherever we clicked to open the menu
        self.locked_new_location_position = self.new_location_position

        return [
            
            MenuOptionStyle(
                ft.MenuItemButton(
                    "New Location", leading=ft.Icon(ft.Icons.LOCATION_PIN, ft.Colors.PRIMARY),
                    on_click=self.create_location, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_effects=True, no_padding=True
            ),
            MenuOptionStyle(
                ft.MenuItemButton(
                    "New Label", leading=ft.Icon(ft.Icons.TEXT_FIELDS_OUTLINED, ft.Colors.PRIMARY),
                    on_click=self.create_label, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_effects=True, no_padding=True
            ),
            MenuOptionStyle(
                ft.MenuItemButton(
                    "Show Info", leading=ft.Icon(ft.Icons.INFO_OUTLINE, ft.Colors.PRIMARY),
                    on_click=self.show_info, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Show this map's info in the sidebar",
                ),
                no_effects=True, no_padding=True
            ),
            MenuOptionStyle(
                ft.MenuItemButton(
                    ("Disable" if self.data.get('draw_mode') else "Enable") + " Drawing", 
                    close_on_click=True, on_click=self.toggle_draw_mode,
                    leading=ft.Icon(ft.Icons.EDIT_OUTLINED if self.data.get('draw_mode', False) else ft.Icons.EDIT_OFF_OUTLINED, ft.Colors.PRIMARY),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_effects=True, no_padding=True
            )
        ]
    
    # Also sets our mouse coordinates for the menu to open at the right place
    def set_mouse_coords(self, e: ft.PointerEvent):
        self.new_location_position = (e.local_position.x, e.local_position.y)
        super().set_mouse_coords(e)

    
    async def toggle_draw_mode(self, e=None):
        await self.story.close_menu()   # Close menu
        new_draw_mode = not self.data.get('draw_mode', False)
        self.update_data(**{'draw_mode': new_draw_mode})
        if self.showing_info:
            self.sidebar_draw_mode_toggle_button.content = ("Disable" if new_draw_mode else "Enable") + " Drawing"
            self.sidebar_draw_mode_toggle_button.leading = ft.Icon(ft.Icons.EDIT_OUTLINED if new_draw_mode else ft.Icons.EDIT_OFF_OUTLINED, ft.Colors.PRIMARY)
            self.sidebar_draw_mode_toggle_button.update()
        self.map_controller.mouse_cursor = ft.MouseCursor.PRECISE if new_draw_mode else None
        self.map_controller.update()

    # Creates our header controls for the sidebar, including our settings button
    def create_sidebar_header_ctrls(self) -> list[ft.Control]:

        def set_canvas_bg_image(e: ft.Event[ft.MenuItemButton]):
        
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
                    self.page.show_dialog(SnackBar("Canvas not found. Please try again."))
                    self.page.pop_dialog()
                    return

                snapshot_str = widget.get_snapshot_string()
                title = widget.data.get('title', 'Untitled')
                if snapshot_str is None:
                    self.page.show_dialog(SnackBar("Failed to get canvas snapshot. Please try again."))
                    self.page.pop_dialog()
                    return

                self.update_data(**{'background_image': snapshot_str})  # Update our data
                
                # Update the image in our widget
                self.bg_image.image = ft.DecorationImage(
                    f"data:image/png;base64,{snapshot_str}",
                    fit=ft.BoxFit.FILL
                )
                self.bg_image.update()
                self.page.pop_dialog()

            canvas_id: str = None
        
            dlg = ft.AlertDialog(
                title=ft.Text("Set a Canvas as Image", weight=ft.FontWeight.BOLD),
                content=ft.RadioGroup(
                    ft.Column([
                        ft.Radio(
                            label=widget.data.get('title', 'Untitled'),
                            value=id, mouse_cursor=ft.MouseCursor.CLICK,
                        ) for id, widget in self.story.widgets.items() if widget.data.get('tag', '') == "canvas"],
                    ),
                    on_change=select_canvas
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                    ft.TextButton("Select", on_click=set_canvas_image, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click")),]
            )
            self.page.show_dialog(dlg)

        # Uploads an image and sets it as the background image for our map
        async def handle_set_bg_image(e: ft.Event[ft.MenuItemButton]):
            await self.story.close_menu()   # Close menu
            
            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:

                file_path = files[0].path
                try:
                    import base64

                    with open(file_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        # Save to our data
                        self.update_data(**{'background_image': f"{encoded_string}"})

                    # Update the image in our widget
                    self.bg_image.image = ft.DecorationImage(
                        f"data:image/png;base64,{encoded_string}",
                        fit=ft.BoxFit.FILL
                    )
                    self.bg_image.update()

                except Exception:
                    pass

        # Set our built in options, or none, to set no background image
        def handle_set_built_in_image(e: ft.Event[ft.MenuItemButton]):

            self.update_data(**{'background_image': e.control.data})
            self.bg_image.image = ft.DecorationImage(
                e.control.data,
                fit=ft.BoxFit.FILL
            )
            self.bg_image.update()

        self.undo_button = ft.IconButton(
            ft.Icons.UNDO,
            ft.Colors.OUTLINE_VARIANT,
            mouse_cursor=ft.MouseCursor.CLICK,
            on_click=self.undo_task,
            disabled=True,
            tooltip="Undo drawing",
        )
        self.redo_button = ft.IconButton(
            ft.Icons.REDO_OUTLINED,
            ft.Colors.OUTLINE_VARIANT,
            mouse_cursor=ft.MouseCursor.CLICK,
            on_click=self.redo_task,
            disabled=True,
            tooltip="Redo drawing",
        )


        ctrls: list = super().create_sidebar_header_ctrls()

        self.sidebar_draw_mode_toggle_button = ft.MenuItemButton(
            ("Disable" if self.data.get('draw_mode') else "Enable") + " Drawing", 
            close_on_click=True, on_click=self.toggle_draw_mode,
            leading=ft.Icon(ft.Icons.EDIT_OUTLINED if self.data.get('draw_mode', False) else ft.Icons.EDIT_OFF_OUTLINED, ft.Colors.PRIMARY),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
        )

        ctrls.extend([
            self.undo_button,
            self.redo_button,
            ft.MenuBar(
                [
                    ft.SubmenuButton(
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY),
                        [
                            self.sidebar_draw_mode_toggle_button,
                            ft.SubmenuButton(
                                "Set Background Image",
                                [
                                    ft.MenuItemButton(      
                                        leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Select Canvas", 
                                        close_on_click=True,
                                        on_click=set_canvas_bg_image,
                                        tooltip="Select a canvas to use as the background for this map",
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                    ), 
                                    ft.MenuItemButton(      # Folders
                                        leading=ft.Icon(ft.Icons.IMAGE_SEARCH_OUTLINED, ft.Colors.PRIMARY), content="Upload Image", 
                                        close_on_click=True,
                                        tooltip="Upload an image to use as the background for this map",
                                        on_click=handle_set_bg_image,
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                    ),  
                                    ft.MenuItemButton(      # 1
                                        "Dark Fantasy", leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), 
                                        close_on_click=True,
                                        data="map_bg_fantasy_dark.png", on_click=handle_set_built_in_image,
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                    ), 
                                    ft.MenuItemButton(      # 1
                                        "Light Fantasy", leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), 
                                        close_on_click=True,
                                        data="map_bg_fantasy_light.png", on_click=handle_set_built_in_image,
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                    ), 
                                    ft.MenuItemButton(      # 2
                                        "Sci-Fi", leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), 
                                        close_on_click=True,
                                        data="map_bg_scifi.png", on_click=handle_set_built_in_image,
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                    ),
                                    ft.MenuItemButton(      # 1
                                        "Space", leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), 
                                        close_on_click=True,
                                        data="map_bg_space.jpg", on_click=handle_set_built_in_image,
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                    ), 
                                    #ft.MenuItemButton(      # 2
                                        #"None", leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), 
                                        #close_on_click=True,
                                        #data="", on_click=handle_set_built_in_image,
                                        #style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                    #),
                                ],
                                leading=ft.Icon(ft.Icons.IMAGE_OUTLINED, ft.Colors.PRIMARY),
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                                menu_style=ft.MenuStyle(alignment=ft.Alignment.BOTTOM_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
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
        ])
        return ctrls


    # Build the map
    def build(self):
        super().build()

        self.bg_image = ft.Container(           # Background container
            ignore_interactions=True,
            width=self.map_width, height=self.map_height,
            image=ft.DecorationImage(       # Background image
                self.data.get('background_image', "map_bg_fantasy.jpg"),
                fit=ft.BoxFit.FILL
            ) 
        )

        capture = self.data.get('capture', '')
        canvas_shapes = []
        if capture:
            try:
                canvas_shapes.append(cv.Image(
                    base64.b64decode(capture),
                    0,
                    0,
                    self.CANVAS_WIDTH,
                    self.CANVAS_HEIGHT,
                ))
            except (TypeError, ValueError):
                pass

        self.canvas= cv.Canvas(
            shapes=canvas_shapes,
            width=self.map_width,
            height=self.map_height,
        )  

        
        

        # Declare our label stack
        self.label_stack = ft.Stack(
            
            [self.Label(self, data) for data in self.data.get('labels', {}).values()],
            width=self.map_width, height=self.map_height,
        )

        # Declare our location stack
        self.location_stack = ft.Stack(
            [MapLocation(self, data) for data in self.data.get('mini_widgets_data', {}).values()], 
            width=self.map_width, height=self.map_height,
        )

        self.map_controller = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.PRECISE if self.data.get('draw_mode', False) else None, 
            expand=True,

            # Drawing event handlers
            on_tap=self.handle_tap,
            on_pan_start=self.handle_pan_start,
            on_pan_update=self.handle_pan_update,
            on_pan_end=self.handle_pan_end,
            
            # Non-drawing event handlers
            on_secondary_tap=lambda: self.story.open_menu(self.get_new_item_options()),
            on_hover=self.set_mouse_coords,

            drag_interval=5,
            hover_interval=5
        )
                
        interactive_viewer = ft.InteractiveViewer(
            content=ft.Stack([
                self.bg_image,
                self.canvas,        # Canvas with our map drawing
                self.map_controller,        # Gesture detector for our map
                self.location_stack,        # Stack with our map locations
                self.label_stack,           # Stack with our map labels
            ], width=self.map_width, height=self.map_height),
            expand=3, 
            constrained=False,
            scale_factor=800, boundary_margin=1500,
            min_scale=0.01, max_scale=3.0,
        )


        # Add our settings button to the sidebar header, and build our body
        
        self.sidebar_body.controls = self.create_sidebar_body_ctrls()  
        if self.data.get('show_sidebar', True) == False:
            self.showing_info = False
        
        # Set up our main conent
        self.content = ft.Stack([
            interactive_viewer,
            ft.Row(
                [self.toggle_sidebar_visibility_button, self.sidebar], 
                spacing=0, expand=True, alignment=ft.MainAxisAlignment.END, 
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)


# TODO Label and Location label size adjustments