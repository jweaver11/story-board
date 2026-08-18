'''
The canvas class for all canvases inside our story
Canvases are drawings and images
'''

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

MINIMUM_SEGMENT_DISTANCE = 2
MAX_SHAPES_BEFORE_CAPTURE = 50
MAX_UNDO_LIST_TASKS = 30


class Canvas(Widget):
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
            is_new = is_new
        ) 


        # If we're new, give default values for our data 
        if self.is_new == True:
            layer_1_id = str(uuid.uuid4())
            layer_2_id = str(uuid.uuid4())
            self.data.update({
                # Widget data
                "tag": "canvas",
                'layer_directory_path': os.path.join(self.story.data.get('canvas_directory_path'), self.data.get('id')),  # Path to the canvas folder for this story

                'color': app.settings.data.get('widget_defaults', {}).get('canvas', {}).get('color'),
                'show_sidebar': True,   # Whether to show the info column on the side of our charts or not.

                # Info about the canvas
                'canvas_data': {

                    # Sizing
                    "width": (data or {}).get('canvas_data', {}).get('width') or 1920,
                    "height": (data or {}).get('canvas_data', {}).get('height') or 1080,

                    'active_layer_idx': 1,   # Index of our active layer we are drawing on

                    # Layer info for our canvases
                    'layers': [
                        {       # First/Bottom most layer
                            'id': layer_1_id,           # Unique ID for saving files and tracking changes
                            'name': "Background",       # Name of that layer
                            'visible': True,            # Whether this layer is currently visible or not
                            'dirty': False,             # Whether this layer has been changed and needs to be saved
                            'needs_file_write': False,   # Whether this layer needs to be written to disk or not
                            'file_path': os.path.join(self.story.data.get('canvas_directory_path'), self.data.get('id'), f"{layer_1_id}.png"),  # Path to the capture for this layer
                        },
                        {        # Second layer
                            'id': layer_2_id,
                            'name': "Layer 1", 
                            'visible': True, 
                            'dirty': False,
                            'needs_file_write': False,
                            'file_path': os.path.join(self.story.data.get('canvas_directory_path'), self.data.get('id'), f"{layer_2_id}.png"),  # Path to the capture for this layer
                        }
                    ],    
                }
            },
        )

        # State tracking for canvas drawing info
        self.state = State()                # Used for tracking our coords and current drawing data for the active stroke/shape being applied

        # Constants for canvas sizing
        self.CANVAS_WIDTH = self.data.get('canvas_data', {}).get('width', 0)    
        self.CANVAS_HEIGHT = self.data.get('canvas_data', {}).get('height', 0)   

        # Save layer byte data in memory for better performance, and easy identifying
        self.layer_bytes: dict[str, bytes] = {}

        # Load our layer captures into memory for better performance
        for layer_data in self.data.get('canvas_data', {}).get('layers', []):
            try:
                os.makedirs(os.path.dirname(layer_data.get('file_path', '')), exist_ok=True)
                with open(layer_data.get('file_path', ''), 'rb') as f:
                    self.layer_bytes.update(**{layer_data.get('id'): f.read()})   # Add the bytes to live cache list
            except OSError:
                pass    # File doesnt exist yet
        
        # Drawing stuff
        self.current_path: cv.Path = None      # The current path being drawn on the canvas, if any
        self.active_layer_idx: int = self.data.get('canvas_data', {}).get('active_layer_idx', 1)        # Which layer we are drawing on
        self.layer_stack: ft.Stack                # Stack to hold our list of layer canvases on top of each other
        self.canvas_controller: ft.GestureDetector  # Controller that sits over our layer stack and handles mouse events for drawing and tool usage 
        self.mouse_cursor: ft.Icon  # Our 'mouse cursor' that sits overtop the canvas_controller
        self.use_standard_cursor: bool = app.settings.data.get('widget_defaults', {}).get('canvas', {}).get('use_standard_cursor', True)  # Whether to use a standard cursor or one that reflects our paint settings
        
        # Tool and shape stuff
        self.current_tool: CanvasShape = None                     # The active shape being added if we're using a tool
        #self.tool_rotate_handle: ft.GestureDetector         # Handle for rotating the current tool 
        
        # Sidebar controls. Undo/redo buttons
        self.undo_button: ft.IconButton
        self.redo_button: ft.IconButton


    # Overwrite our standard save_file call since we have multiple files
    async def save_file(self):

        # Go through our layer data
        for i, layer in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            # If a change has been made to the layer, save that change.
            if layer.get('dirty', False) == True:
                canvas: cv.Canvas = self.layer_stack.controls[i]
                try:
                    await self.save_canvas(canvas)
                except RuntimeError as e:
                    print(f"Error saving layer {layer.get('name', '')}: {e}")
                    return
                self.needs_file_write = True    # Mark our widget as dirty if we saved anything

            # If the layer needs to be written to disk, write it
            if layer.get('needs_file_write', False) == True:
                try:
                    os.makedirs(os.path.dirname(layer.get('file_path', '')), exist_ok=True)
                    with open(layer.get('file_path', ''), 'wb') as f:
                        f.write(self.layer_bytes.get(layer.get('id', ''), b''))  # Write the bytes to disk
                except Exception as e:
                    print(f"Error writing layer {layer.get('name', '')} to file: {e}")
                    return
                self.needs_file_write = True    # Mark our widget as dirty so we save to file
                layer['needs_file_write'] = False  # Mark the layer as no longer needing a file write
        await super().save_file()   

    async def hide_widget(self, e=None):
        self.story.block_page()
        await super().hide_widget()
        self.story.unblock_page()
        

    # Moves our mouse cursor around to match our drawing
    def move_mouse_cursor(self, position: ft.Offset):
        if not self.use_standard_cursor:
            self.mouse_cursor.left = position.x
            self.mouse_cursor.top = position.y
            self.mouse_cursor.update()         
   
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
            self.canvas_controller.mouse_cursor = standard_mouse_cursor     # Set the decided cursor
            self.mouse_cursor.visible = False       # Hide the custom one

        # For setting a custom cursor that reflects our paint settings
        def set_custom_cursor():
            
            self.canvas_controller.mouse_cursor = ft.MouseCursor.NONE   # Hide standard
            self.mouse_cursor.visible = True    # Make sure we're showing
            
            self.mouse_cursor.size = paint_settings.get('stroke_width', 3) * 1.25
            self.mouse_cursor.color = paint_settings.get('color', ft.Colors.BLACK)
            
            stroke_cap = paint_settings.get('stroke_cap', 'butt')
            # Set mouse cursor based on stroke cap
            if stroke_cap == 'round': self.mouse_cursor.icon = ft.Icons.CIRCLE
            elif stroke_cap == 'square':self.mouse_cursor.icon = ft.Icons.SQUARE
            else: self.mouse_cursor.icon = ft.Icons.SQUARE_ROUNDED

            # If using tool mode, hide our custom one and use the standard, unless using erase or line tool
            if control_mode == "tool":
                if active_tool != "erase" and active_tool != "line": # Erase or line get normal draw cursor
                    self.canvas_controller.mouse_cursor = ft.MouseCursor.CLICK     # Other tools get responsive click cursor
                    self.mouse_cursor.visible = False       # Hide the custom one

        # Grab out settings for paint and canvas
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
        active_tool = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")

        # Catch errors
        if self.active_layer_idx > len(self.data.get('canvas_data', {}).get('layers', [])) - 1:
            self.active_layer_idx = len(self.data.get('canvas_data', {}).get('layers', [])) - 1
            return  

        # TODO: Only use custom on drawing tools and erase. Tools and text should use standard even if the option is set      

        # Sets our mouse cursor as the standard one or custom one depending on setting
        if self.use_standard_cursor:
            set_standard_cursor()
        else:
            if control_mode == "draw" or (control_mode == "tool" and (active_tool == "erase" or active_tool == "line")):
                set_custom_cursor()
            else:
                set_standard_cursor()

        # Check if active layer is hidden, and overrite cursors
        if self.layer_stack.controls[self.active_layer_idx].visible == False:
            self.canvas_controller.mouse_cursor = None
            self.mouse_cursor.visible = False

        if update:
            self.mouse_cursor.update()
            self.canvas_controller.update()
        
        

    # Shows our sidebar and paints a tool on canvas if needed
    async def show_sidebar(self, e: ft.Event):
        if self.state.manipulating_shape:
            await self.paint_tool_on_canvas()
        await super().show_sidebar(e)
           
    # If we have an active tool/shape that we are manipulating, paint it on the canvas
    async def paint_tool_on_canvas(self):
        ''' Converts the displayed shapes rotation and size onto our active layer and paints it there '''

        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
        canvas_id = self.data.get('canvas_data', {}).get('layers', [])[self.active_layer_idx].get('id', '')
        if not canvas.visible or self.current_tool is None:  # Catch errors
            self.page.show_dialog(SnackBar("Error finding visible canvas or tool."))
            return

        self.state.manipulating_shape = False   # Update state
        
        # Text can be rotated, so we can just grab it and put it in the right spot
        if self.current_tool.shape_type == "text":

            # Align our text to account for size of our layer canvas
            text_shape: cv.Text = self.current_tool.cv_shape
            text_shape.x += self.current_tool.left + 2
            text_shape.y += self.current_tool.top + 2
            
            canvas.shapes.append(text_shape)
            await self.end_stroke(canvas=canvas)
            #self.current_tool.visible = False
            #self.current_tool.rotate_handle.visible = False
            self.canvas_controller.parent.controls.remove(self.current_tool)
            self.canvas_controller.parent.controls.remove(self.current_tool.rotate_handle)
            self.canvas_controller.parent.update()
            #self.update()
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

        canvas.shapes.append(cv.Image(stamped_bytes, paste_x, paste_y))
        await self.end_stroke(canvas=canvas)
        canvas.update()
            
        self.canvas_controller.parent.controls.remove(self.current_tool)
        self.canvas_controller.parent.controls.remove(self.current_tool.rotate_handle)
        self.canvas_controller.parent.update()

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

    # Handles all pan start events
    async def handle_pan_start(self, e: ft.DragStartEvent):
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
        paint_settings = app.settings.data.get('paint_settings', {}).copy()

        # Grab our canvas
        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:  # Catch errors
            return

        control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
        tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")

        # Adjust paint settings for erase tool to just add a point. Not compatible with blur or fill, so temp turned off
        if control_mode == "tool":
            if tool_name == "erase":
                paint_settings['blend_mode'] = "clear"
                paint_settings['blur_image'] = 0
                paint_settings['style'] = "stroke"
        
        # Add our point to the canvas and our paint settings, update, and save
        canvas.shapes.append(cv.Points(points=[(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings)))
        canvas.update()
        self.current_path = cv.Points(points=[(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
        await self.end_stroke(canvas)   # Force a stroke end since it wont have pan end events

    async def fill_tool(self, e: ft.TapEvent):
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

        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:
            return

        layer_idx = int(canvas.data)
        layer_data = self.data.get('canvas_data', {}).get('layers', [])[layer_idx]
        layer_id = layer_data.get('id', '')

        # Ensure any pending vector strokes are merged before we sample fill boundaries.
        if layer_data.get('dirty', False):
            await self.save_canvas(canvas)

        self.story.block_page()
        await asyncio.sleep(0)  # Allow UI to update before potentially long operation.
        existing_bytes = self.layer_bytes.get(layer_id)
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

        # Keep layer cache, canvas state, and file-write flags in sync with draw/save flow.
        self.layer_bytes[layer_id] = filled_bytes
        canvas.shapes.clear()
        canvas.shapes.append(cv.Image(filled_bytes, 0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT, data=layer_id))
        canvas.update()

        layer_data['dirty'] = False
        layer_data['needs_file_write'] = True
        self.data.get('canvas_data', {}).get('layers', [])[layer_idx].update(layer_data)
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
        self.story.unblock_page()

    # Tap event for adding a tool to the canvas
    async def add_shape(self, e: ft.TapEvent):
        
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
        self.canvas_controller.parent.controls.append(self.current_tool)
        self.canvas_controller.parent.update()
        self.canvas_controller.parent.controls.append(self.current_tool.rotate_handle)
        self.canvas_controller.parent.update()

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
        self.canvas_controller.parent.controls.append(self.current_tool)
        self.canvas_controller.parent.update()
        self.canvas_controller.parent.controls.append(self.current_tool.rotate_handle)
        self.canvas_controller.parent.update()
        
    # Adds our initial stroke (cv.Shape) to the canvas with correct settings
    def start_stroke(self, e: ft.DragStartEvent):

        # Grab the canvas and paint settings
        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:  # Protect when we shouldnt be drawing with it
            self.page.show_dialog(SnackBar("Set an active layer to draw on."))
            return

        # Grab settings for ez reference
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()
    
        # Update our state x and y coordinates
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

        # Check if we're in tool mode, and what tool we're using
        if canvas_settings.get('current_control_mode', "") == "tool":
            tool_name = canvas_settings.get('current_tool_name', "")

            # Erase tool - Update the paint settings and create a normal path
            if tool_name == "erase":
                paint_settings['blend_mode'] = "clear"
                paint_settings['blur_image'] = 0
                paint_settings['style'] = "stroke"
                self.current_path = cv.Path(elements=[cv.Path.MoveTo(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))

            # Line tool - Create a path using one straight line element that we'll update differently
            elif tool_name == "line":                
                paint_settings['style'] = "stroke"
                self.current_path = cv.Path(elements=[cv.Path.MoveTo(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
                line_element = cv.Path.LineTo(self.state.x, self.state.y)
                self.current_path.elements.append(line_element)

            # Add our tool path to the canvas and return
            canvas.shapes.append(self.current_path)
            canvas.update()
            return

        # Otherwise we're in draw mode
        else:
            # Brush smoothing - use a normal path
            if canvas_settings.get('use_brush_smoothing', False) == True or paint_settings.get('style', "") == "stroke_fill":
                self.current_path = cv.Path(elements=[cv.Path.MoveTo(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
                canvas.shapes.append(self.current_path)
            # No brush smoothing, just add a line element to the canvas
            else: 
                canvas.shapes.append(cv.Line(self.state.x, self.state.y, e.local_position.x, e.local_position.y, paint=ft.Paint(**paint_settings)))
            canvas.update()
        
    # Updates the current stroke shape on the canvas depending on our settings
    def update_stroke(self, e: ft.DragUpdateEvent):

        # TODO: Handle Stroke smoothing
        
        # Sampling to improve perforamance. If the line length is too small, we skip it
        #dx = e.local_position.x - self.state.x
        #dy = e.local_position.y - self.state.y
        #if dx * dx + dy * dy < MINIMUM_SEGMENT_DISTANCE * MINIMUM_SEGMENT_DISTANCE:
            #return

        # Grab canvas and catch errors
        canvas: cv.Canvas =  self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:  
            return
        
        # Grab the current path and catch errors
        self.current_path = canvas.shapes[-1] if canvas.shapes and len(canvas.shapes) > 1 else None # Trips if drawing but havnt finished capture
        if not self.current_path:
            return

        # Paint settings
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()

        self.move_mouse_cursor(e.local_position)    # Make our custom mouse_cursor follow our mouse position when drawing if using it
                
        # Check if we're in tool mode, and what tool we're using
        if canvas_settings.get('current_control_mode', "") == "tool":
            tool_name = canvas_settings.get('current_tool_name', "")
            match tool_name:

                # Erase tool - Add another smooth line to the path
                case "erase":
                    path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
                    self.current_path.elements.append(path_element)

                # Line tool - Update our straight line element to the current mouse position
                case "line":
                    # Set the element and update its position
                    line_element = self.current_path.elements[-1]
                    line_element.x = e.local_position.x
                    line_element.y = e.local_position.y

            # Update state and return
            self.state.x = e.local_position.x
            self.state.y =  e.local_position.y
            self.current_path.update()
            return

        # Otherwise we're in draw mode
        else:

            # If using path smoothing or stroke_fill, update the path with a new line element
            if canvas_settings.get('use_brush_smoothing', False) == True or paint_settings.get('style', "") == "stroke_fill": 
                path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
                self.current_path.elements.append(path_element)
                self.current_path.update()

            # Non-smooth drawing, add another line
            else: 
                canvas.shapes.append(cv.Line(self.state.x, self.state.y, e.local_position.x, e.local_position.y, paint=self.current_path.paint))
                canvas.update()
                
            # Update our state x and y positions
            self.state.x = e.local_position.x
            self.state.y =  e.local_position.y
        

    # Ends the current stroke (cv.Shape) and marks that layer as dirty for saving, and saves if we hit max shape count
    async def end_stroke(self, e: ft.DragEndEvent=None, canvas: cv.Canvas=None):
        """ Saves our paths to our canvas data for storage """

        # Grab our canvas and protect against errors
        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx] if canvas is None else canvas
        if not canvas.visible:  
            return
        
        # Grab our layer data and mark it as dirty, so we know to save it when program closes
        layer_idx = int(canvas.data)
        layer_data = self.data.get('canvas_data', {}).get('layers', [])[layer_idx]
        layer_id = layer_data.get('id', '')
        layer_data['dirty'] = True
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})   # Update our meta data for the layer

        # If we have too many shapes on the canvas, flatten them into the layer's PNG file
        if len(canvas.shapes) > MAX_SHAPES_BEFORE_CAPTURE:
            self.story.block_page()     # Block page to prevent other events whil we do this one
            await self.save_canvas(canvas)  # Save the current canvas added shapes to its bytes stored in memory
            canvas.shapes.clear()
            canvas.shapes.append(cv.Image(self.layer_bytes.get(layer_id), 0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT, data=layer_id))
            canvas.update()
            self.story.unblock_page()   # Unblock page
            self.state.undo_list.clear()
            self.undo_button.disabled = True
            self.undo_button.icon_color = ft.Colors.OUTLINE_VARIANT
            self.undo_button.update()
            self.state.redo_list.clear()
            self.redo_button.disabled = True
            self.redo_button.icon_color = ft.Colors.OUTLINE_VARIANT
            self.redo_button.update()
        else:
            self.add_undo_task({
                'task_type': 'path_stroke',
                'layer_id': layer_data.get('name', ''),
                'data': self.current_path if self.current_path else self.current_tool
            })

        # Add stroke to undo list
        #if self.current_path is not None:
        

        # Else add shape/text
        #else:
            #self.add_undo_task({
                #'task_type': 'tool',
                #'layer_id': layer_data.get('name', ''),
                #'data': self.current_tool
            #})

        # Replace clear strokes with the saved layer image so Flet cannot reuse a stale
        # retained render for the destructive blend operation.
        if self.current_path and str(getattr(getattr(self.current_path, 'paint', None), 'blend_mode', '')).lower().endswith('clear'):
            self.story.block_page()
            try:
                saved_bytes = await self.save_canvas(canvas)
                if not saved_bytes:
                    return
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(
                    saved_bytes,
                    0,
                    0,
                    self.CANVAS_WIDTH,
                    self.CANVAS_HEIGHT,
                    data=layer_id,
                ))
                canvas.update()
            finally:
                self.story.unblock_page()

    # Saves any changes to the current layer canvas to its png file, and returns the bytes if other functions need it
    async def save_canvas(self, canvas: cv.Canvas) -> bytes:

        # Protect bad calls
        if canvas.visible == False:  
            return

        # Grab the layer data using the index
        layer_idx = int(canvas.data)
        layer_data = self.data.get('canvas_data', {}).get('layers', [])[layer_idx]
        layer_id = layer_data.get('id', '')
        
                
        # Clear blend strokes must be captured with the stored image so they can remove
        # pixels from the existing layer instead of being alpha-composited on top of it.
        shapes = list(canvas.shapes)
        base_is_stored_image = shapes and isinstance(shapes[0], cv.Image) and shapes[0].data    # Marked as loaded
        new_strokes = shapes[1:] if base_is_stored_image else shapes
        has_clear_stroke = any(
            str(getattr(getattr(shape, 'paint', None), 'blend_mode', '')).lower().endswith('clear')
            for shape in new_strokes
        )
        capture_shapes = shapes if has_clear_stroke else new_strokes

        # Capture the appropriate layer content, then restore the original shapes to the canvas
        canvas.shapes[:] = capture_shapes
        canvas.update()

        await canvas.capture(pixel_ratio=app.settings.data.get('canvas_settings', {}).get('capture_ratio', 1))
        new_bytes = await canvas.get_capture()
        await canvas.clear_capture()
        canvas.shapes[:] = shapes  # Restore the original shapes to the canvas
        canvas.update()

        # Error capturing new strokes (should be impossible)
        if not new_bytes:
            self.page.show_dialog(SnackBar(f"Error capturing new strokes for layer {layer_data.get('name', '')}."))
            return

        # A full capture already contains the erase result and must replace the old layer.
        if has_clear_stroke:
            result = Image.open(BytesIO(new_bytes)).convert("RGBA")
            if result.size != (self.CANVAS_WIDTH, self.CANVAS_HEIGHT):
                result = result.resize((self.CANVAS_WIDTH, self.CANVAS_HEIGHT), Image.Resampling.LANCZOS)
            output = BytesIO()
            result.save(output, format="PNG")
            combined_bytes = output.getvalue()
            self.layer_bytes[layer_id] = combined_bytes

            layer_data['dirty'] = False
            layer_data['needs_file_write'] = True
            self.data.get('canvas_data', {}).get('layers', [])[layer_idx].update(layer_data)
            self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
            return combined_bytes

        # Load the existing layer capture
        existing_bytes = self.layer_bytes.get(layer_id, None)

        # If we have an existing capture, composite the new strokes onto it; otherwise, create a new base image
        if existing_bytes:
            base_img = Image.open(BytesIO(existing_bytes)).convert("RGBA")
        else:
            base_img = Image.new("RGBA", (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), (0, 0, 0, 0))

        # Composite the new strokes onto the existing base — base pixels are never re-rendered through Flet
        delta_img = Image.open(BytesIO(new_bytes)).convert("RGBA")
        if delta_img.size != base_img.size: # Handle size errors (should be impossible)
            delta_img = delta_img.resize(base_img.size, Image.Resampling.LANCZOS)

        # Merge the two images together and add them to our in memory cache for the next save
        result = Image.alpha_composite(base_img, delta_img)
        output = BytesIO()
        result.save(output, format="PNG")
        combined_bytes = output.getvalue()

        # Update the in-memory cache, and mark the layer as dirty for saving
        self.layer_bytes[layer_id] = combined_bytes

        # Mark the layer as no longer dirty, but needs a file write
        layer_data['dirty'] = False
        layer_data['needs_file_write'] = True
        self.data.get('canvas_data', {}).get('layers', [])[layer_idx].update(layer_data)
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})

        return combined_bytes   # Return our now updated bytes

       
    # Accepts the formatted undo task data, adds it to state and handles UI updates for the undo/redo buttons
    def add_undo_task(self, task_data: dict):
        
        # Add most recent path to undo list, clear redo list, and check undo list not too long
        self.state.undo_list.append(task_data)
        self.state.redo_list.clear()    
        if len(self.state.undo_list) > MAX_UNDO_LIST_TASKS: 
            self.state.undo_list.pop(0)
        
        # Handle buttons
        self.undo_button.disabled = False
        self.undo_button.icon_color = ft.Colors.PRIMARY
        self.redo_button.disabled = True
        if len(self.state.redo_list) == 0:
            self.redo_button.icon_color = ft.Colors.OUTLINE_VARIANT
            self.undo_button.update()
            self.redo_button.update()

    def add_redo_task(self, task_data: dict):
        
        # Add most recent path to redo list, clear undo list, and check redo list not too long
        self.state.redo_list.append(task_data)
        if len(self.state.redo_list) > MAX_UNDO_LIST_TASKS: 
            self.state.redo_list.pop(0)
        
        # Handle buttons
        self.redo_button.disabled = False
        self.redo_button.icon_color = ft.Colors.PRIMARY
        self.redo_button.update()
        if len(self.state.undo_list) == 0:
            self.undo_button.disabled = True
            self.undo_button.icon_color = ft.Colors.OUTLINE_VARIANT
            self.undo_button.update()
        

    # Called when undoing a stroke on the canvas
    async def undo_task(self, e=None):

        # If there's nothing to undo, return early
        if len(self.state.undo_list) == 0:
            return
                
        # Grab the task we're going to carry out and its name and capture
        task = self.state.undo_list.pop()    
        task_type = task.get('task_type', None)
        layer_id = task.get('layer_id', None)
        data = task.get('data', None)

        layer_canvas = None
        layer_idx = None
        for idx, layer in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            if layer.get('name', None) == layer_id:
                layer_canvas: cv.Canvas = self.layer_stack.controls[idx]
                layer_idx = idx
                break
        # Catch errors
        if layer_canvas is None or layer_idx is None:
            return

        # Simple. We just added a shape(s) to the canvas, so undoing we remove it
        if task_type == 'path_stroke':
            layer_canvas.shapes.pop()
        else:
            self.current_tool = data
            await self.paint_tool_on_canvas()
        layer_canvas.update()

        self.add_redo_task(task)    # Add the task we just undid to the redo list
        

    # Called when redoing a stroke on the canvas after a previous undo
    async def redo_task(self, e=None):
        
        # If there's nothing to redo, return early
        if len(self.state.redo_list) == 0:
            return

        # Grab the task we're going to carry out and its name and capture
        task = self.state.redo_list.pop()    
        task_type = task.get('task_type', None)
        layer_id = task.get('layer_id', None)
        data = task.get('data', None)

        layer_canvas = None
        layer_idx = None
        for idx, layer in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            if layer.get('name', None) == layer_id:
                layer_canvas: cv.Canvas = self.layer_stack.controls[idx]
                layer_idx = idx
                break
        # Catch errors
        if layer_canvas is None or layer_idx is None:
            return

        # Just shapes for now
        #match str(task_type):
        #    case _:

        # Simple. We just added a shape(s) to the canvas, so redoing we add it back
        if task_type == 'path_stroke':
            layer_canvas.shapes.append(data)
        else:
            self.current_tool = data
            await self.paint_tool_on_canvas()
            
        
        layer_canvas.update()

        self.add_undo_task(task)    # Add the task we just redid to the undo list

    # Sets either an image or a color as the content of a layer
    async def set_layer_content(self, e: ft.Event):

        await self.story.close_menu()

        content_type = e.control.data
        layer_idx = e.control.parent.parent.parent.data
        layer_id = self.data.get('canvas_data', {}).get('layers', [])[layer_idx].get('name', '')

        # Set a color as the background
        if content_type == "color":

            async def _color_change(e):     # Set the color to the picked one
                color_picker.color = e.data

            async def _set_color_confirmed(e=None):

                canvas: cv.Canvas = self.layer_stack.controls[layer_idx]
                canvas.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                self.layer_bytes[layer_id] = None   # Clear the current capture to ignore it when saving
                canvas.shapes.append(cv.Color(color_picker.color))   # Re-add empty images so it can capture
                canvas.update()
                self.page.pop_dialog()
                await self.save_canvas(canvas=canvas)


            color_picker = ColorPicker(
                self.data.get('background', ft.Colors.PRIMARY) if self.data.get('bg_type') == "color" else ft.Colors.PRIMARY,
                on_color_change=_color_change
            )
            dlg = ft.AlertDialog(
                ft.Column([color_picker], tight=True, expand=False),
                title=f"Set {layer_id} to a Color",
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                    ft.TextButton("Set", on_click=_set_color_confirmed, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)),
                ]
            )
            self.page.show_dialog(dlg)

        # If its not a color, its an image
        else:
            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:

                file_path = files[0].path
                try:
                    
                    with open(file_path, "rb") as image_file:
                        bytes = image_file.read()
                        #encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        canvas: cv.Canvas = self.layer_stack.controls[layer_idx]
                        canvas.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                        self.layer_bytes[layer_id] = None   # Clear the current capture to ignore it when saving
                        canvas.shapes.append(cv.Image(bytes, 0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT, data=layer_id))   # Re-add empty images so it can capture
                        canvas.update()
                        self.page.pop_dialog()
                        await self.save_canvas(canvas=canvas)
                        
                except Exception:
                    self.page.pop_dialog()

    # Sets the blur of a layers
    async def set_layer_blur(self, e: ft.Event):
        await self.story.close_menu()

        layer_name = e.control.parent.parent.parent.parent.data
        layer_idx = e.control.parent.parent.parent.data
        layer_name = self.data.get('canvas_data', {}).get('layers', [])[layer_idx]['name']
        layer_id = self.data.get('canvas_data', {}).get('layers', [])[layer_idx]['id']
        capture = None
        capture = self.data.get('canvas_data', {}).get('layers', [])[layer_idx]['capture']
        if not capture:
            self.page.show_dialog(SnackBar("Layer must have existing content to set blur"))
            return

        # Updates the visual canvas with new blur amount
        async def blur_amount_changed(e: ft.Event):
            blur_amount = e.control.value
            active_preview_image.paint.blur_image = blur_amount
            active_preview_image.update()

        # Apply that level of blur to the layer
        async def apply_blur(e=None):
            
            blur_strength = blur_strength_slider.value

            # Apply the blur to the correct canvas
            canvas: cv.Canvas = self.layer_stack.controls[layer_idx]
            canvas.shapes.clear()
            canvas.shapes.append(cv.Image(capture, 0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT, paint=ft.Paint(blur_image=blur_strength), data=layer_id))
            canvas.update()
            self.page.pop_dialog()

            await self.save_canvas(canvas=canvas)  # Will save new capture to the data
            
        
        blur_strength_slider = ft.Slider(1, "{value}", min=0, max=50, on_change=blur_amount_changed)
        
        preview_canvas = ft.Container(
            cv.Canvas(
                #shapes=[preview_image], 
                shapes=[],
                expand=True,
                width=self.page.width / 2, height=self.page.height / 2
            ),
            image=ft.DecorationImage("canvas_bg.png", alignment=ft.Alignment.TOP_LEFT, repeat=ft.ImageRepeat.REPEAT),
        )

        active_preview_image = None

        # Add the entire canvas to the preview, but mark the active layer we will change blur of
        for layer in self.data.get('canvas_data', {}).get('layers', []):

            # Active layer that the blur will adjust
            if layer.get('name') == layer_name:
                active_preview_image = cv.Image(
                    self.layer_bytes.get(layer.get('id', ''), None),   # Grab our capture from memory
                    0, 0, 
                    self.page.width / 2, self.page.height / 2, 
                    paint=ft.Paint(blur_image=1)
                )
                preview_canvas.content.shapes.append(active_preview_image)
                continue
            # All other layers
            preview_canvas.content.shapes.append(
                cv.Image(
                    self.layer_bytes.get(layer.get('id', ''), None),   # Grab our capture from memory
                    0, 0, 
                    self.page.width / 2, self.page.height / 2
                )
            )
            
        if active_preview_image is None:
            self.page.show_dialog(SnackBar("Error finding layer capture for blur"))
            return

        dlg = ft.AlertDialog(
            ft.Column([
                preview_canvas, 
                blur_strength_slider,
                ft.Text("Adjust Blur Strength", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            title=f"Set Blur for {layer_name}",
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                ft.TextButton("Apply", on_click=apply_blur, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)),
            ]
        )
        self.page.show_dialog(dlg)    

    # Returns our current snapshot in bytes of our canvas layers combined
    def get_snapshot_bytes(self, quality: str="max") -> bytes:

        # Determine target dimensions from quality setting
        match quality:
            case "low":     scale = 0.25
            case "medium":  scale = 0.5
            case _:         scale = 1.0
        width = max(1, int(self.CANVAS_WIDTH * scale))
        height = max(1, int(self.CANVAS_HEIGHT * scale))

        # Merge all our layer/canvas captures together into one image at the right size
        def _merge_captures(captures_list: list):

            images = []     # Start with an images list

            for capture in captures_list:
                image = Image.open(BytesIO(capture)).convert("RGBA")        # Create the image for each capture

                # Resize each layer to the target dimensions before compositing
                if image.size != (width, height):
                    image = image.resize((width, height), Image.Resampling.LANCZOS)

                images.append(image)

            if not images:      # Catch errors
                return None
            
            merged = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            
            # Put all the images together
            for image in images:
                merged = Image.alpha_composite(merged, image)

            # Gives us the output we want
            output = BytesIO()
            merged.save(output, format="PNG")
            return output.getvalue()

        # List to store our captures for each layer of our canvas (skip empty captures)
        captures_list = [capture for capture in self.layer_bytes.values() if capture is not None]

        # Our exportable image bytes from merging all our layers captures together
        return _merge_captures(captures_list)

    # Returns a base64 string of our merged canvas captures
    def get_snapshot_string(self, quality: str="max") -> str | None:
        merged_bytes = self.get_snapshot_bytes(quality)
        if merged_bytes is None:
            return None
        return base64.b64encode(merged_bytes).decode('utf-8')


    # Called when we click to export a canvas
    async def export_canvas_clicked(self, e=None):
        """ Exports canvas to correct file type based on selection with optional upscaling """

        merged_bytes = self.get_snapshot_bytes(quality="max")   # Get the merged bytes of all our layers

        # Open file dialog to save that capture
        if merged_bytes:
            await ft.FilePicker().save_file(
                src_bytes=merged_bytes, file_name=f"{self.data.get('title', 'Canvas')}.png", 
                file_type=ft.FilePickerFileType.IMAGE, allowed_extensions=["png"]
            )

    # Adds a new layer into data, on the canvas, and in the sidebar
    def create_new_layer(self, e=None):
        
        # Add layer to topmost part of the list
        new_id = str(uuid.uuid4())
        self.data.get('canvas_data', {}).get('layers', []).append({
            'id': new_id,
            'name': f"Layer {len(self.data.get('canvas_data', {}).get('layers', [])) + 1}" ,
            'visible': True,
            'dirty': False,
            'file_path': os.path.join(self.data.get('layer_directory_path'), f"{new_id}.png")
        })

        # Grab its index
        new_layer_idx = len(self.data.get('canvas_data', {}).get('layers', [])) - 1

        # Add new layer to the stack of canvas controls and sidebar list tiles
        new_canvas_ctrl = self.create_new_layer_canvas_ctrl(
            new_layer_idx, 
            self.data.get('canvas_data', {}).get('layers', [])[-1]
        )
        self.layer_stack.controls.append(new_canvas_ctrl)
        self.sidebar_layers_list_view.controls.append(
            self.create_new_layer_sidebar_ctrl(
                new_layer_idx, 
                self.data.get('canvas_data', {}).get('layers', [])[-1]
            )
        )

        # Set the active index to the newly created layer
        self.active_layer_idx = new_layer_idx
        self.data['canvas_data']['active_layer_idx'] = self.active_layer_idx

        # Clear the old active highlight and mark the new layer as selected
        for ctrl in self.sidebar_layers_list_view.controls:
            ctrl.content.bgcolor = None
        self.sidebar_layers_list_view.controls[-1].content.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH

        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
        self.layer_stack.update()
        self.update()
        
    # Cretes a new layer canvas control for the stack
    def create_new_layer_canvas_ctrl(self, idx: int, canvas_data: dict):
        visible = canvas_data.get('visible', True)
        capture = self.layer_bytes.get(canvas_data.get('id', ''), None)  # Grab the capture for this layer if it exists

        return cv.Canvas(
            data=idx,        # Save the index of this layer so we know where to save it in our data
            shapes=[
                cv.Image(       # Sets the background image of the layer to its most recent capture
                    capture, 0, 0, 
                    width=self.CANVAS_WIDTH,          
                    height=self.CANVAS_HEIGHT,
                    data=canvas_data.get('id', '')
                )    
            ],
            visible=visible,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
        )

    # Creates a new sidebar ctrl for each layer as a reorderable drag handle
    def create_new_layer_sidebar_ctrl(self, idx: int, layer_data: dict) -> ft.ReorderableDragHandle:

        # Called when rename button clicked
        async def rename_layer_clicked(e: ft.Event):
            title_text.visible = False
            title_tf.visible = True
            title_tf.value = title_text.value   # Make sure updated
            title_text.update()
            title_tf.update()
            await title_tf.focus()

        # Updates the data after changing a title in the textfield
        async def update_layer_name(e: ft.Event):
            layer_idx = e.control.parent.parent.data    # List tile data
            old_name = title_text.value
            new_name = e.control.value
            
            for layer in self.data.get('canvas_data', {}).get('layers', []):   # Update the name in the layer data
                if layer.get('name') == new_name:
                    self.page.show_dialog(SnackBar("Layer name already exists. Layer was not renamed"))
                    return
                
            # Update the name of the layer in the canvas data
            self.data.get('canvas_data', {}).get('layers', [])[layer_idx]['name'] = new_name

            for task in self.data.get('canvas_data', {}).get('undo_list', []):   # Update any undo tasks related to this layer
                if task.get('layer_name') == old_name:
                    task['layer_name'] = new_name
            for task in self.data.get('canvas_data', {}).get('redo_list', []):   # Update any redo tasks related to this layer
                if task.get('layer_name') == old_name:
                    task['layer_name'] = new_name

            self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})   # Update the data

            # Update layer name in the sidebar controls
            for ctrl in self.sidebar_layers_list_view.controls:
                if ctrl.data == old_name:
                    ctrl.data = new_name
                    #ctrl.update()
            title_text.value = new_name
            
        # Hides the textfield and shows the text label when the textfield loses focus
        async def hide_layer_name_tf(e: ft.Event):
            title_tf.visible = False
            title_text.visible = True
            title_tf.update()
            title_text.update()

        async def delete_layer(e: ft.Event):
            # Prevent deleting the last layer
            if len(self.data.get('canvas_data', {}).get('layers', [])) <= 1:
                return

            # Remove from data
            layer_idx = e.control.parent.parent.parent.data
            layer_name = self.data.get('canvas_data', {}).get('layers', [])[layer_idx].get('name')
            self.data.get('canvas_data', {}).get('layers', []).pop(layer_idx)

            for task in self.state.undo_list[:]:   # Update any undo tasks related to this layer
                if task.get('layer_name') == layer_name:
                    self.data['canvas_data']['undo_list'].remove(task)
            for task in self.state.redo_list[:]:   # Update any redo tasks related to this layer
                if task.get('layer_name') == layer_name:
                    self.data['canvas_data']['redo_list'].remove(task)

            # Remove the canvas and sidebar entry for this layer
            self.layer_stack.controls.pop(layer_idx)
            self.sidebar_layers_list_view.controls.pop(layer_idx)

            # Adjust active_layer_idx for the removed layer
            if layer_idx < self.active_layer_idx:
                # Deleted a layer below the active one — shift active index down
                self.active_layer_idx -= 1
            elif self.active_layer_idx >= len(self.layer_stack.controls):
                # Deleted the active layer (was last) — clamp to new last
                self.active_layer_idx = len(self.layer_stack.controls) - 1
            # else: deleted a layer above active, or active is now the same positional index
            self.data['canvas_data']['active_layer_idx'] = self.active_layer_idx

            # Update sidebar highlight to reflect the (possibly changed) active layer
            for ctrl in self.sidebar_layers_list_view.controls:
                ctrl.content.bgcolor = None
            self.sidebar_layers_list_view.controls[self.active_layer_idx].content.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH

            #self.layer_stack.update()
            self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
            self.update()
            self.update_indices()
            
        # Grab name and visibility
        name = layer_data.get('name', f"Layer {idx+1}")
        visible = layer_data.get('visible', True)

        return ft.ReorderableDragHandle(
            ft.ListTile(
                title=ft.Row([
                    title_text := ft.Text(name, weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True), 
                    title_tf := ft.TextField(
                        value=name, visible=False,
                        dense=True, expand=True,
                        on_submit=update_layer_name,
                        on_blur=hide_layer_name_tf,
                        #border=ft.InputBorder.NONE, 
                        border_radius=4,
                        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                        focused_bgcolor=ft.Colors.TRANSPARENT,
                        bgcolor=ft.Colors.TRANSPARENT,
                        capitalization=ft.TextCapitalization.WORDS,
                    ),
                    # TODO: Preview img here
                ], expand=True),
                leading=ft.IconButton(   # Toggle visibility button
                    ft.Icons.VISIBILITY if visible else ft.Icons.VISIBILITY_OFF, 
                    ft.Colors.PRIMARY,
                    mouse_cursor="click",
                    on_click=self.toggle_layer_visibility
                ),  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if self.active_layer_idx == idx and visible == True else None,  # Lighter bg for selected layer
                on_click=self.set_new_active_layer, 
                data=idx,
                dense=True, 
                content_padding=ft.Padding.only(left=20, right=30) if self.active_layer_idx == idx and visible == True else ft.Padding.only(left=10, right=30),
                shape=ft.RoundedRectangleBorder(radius=4), 
                tooltip="Click to select this layer",
                trailing=ft.MenuBar(
                    [
                    ft.SubmenuButton(
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY),
                        [
                            ft.MenuItemButton(      # Rename layer button
                                "Rename", leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, ft.Colors.PRIMARY),
                                focus_on_hover=False,
                                on_click=rename_layer_clicked, 
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(      # Set layer as an image button
                                "Set Image", leading=ft.Icon(ft.Icons.IMAGE_OUTLINED, ft.Colors.PRIMARY), 
                                on_click=self.set_layer_content, 
                                tooltip="Upload an image for this layer. This will overwrite any drawings on the layer currently." if visible else
                                "Layer must be visible to set image", 
                                data="image",
                                disabled=not visible, focus_on_hover=False,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(      # Set layer blur button
                                "Set Blur", leading=ft.Icon(ft.Icons.BLUR_ON_OUTLINED, ft.Colors.PRIMARY), 
                                on_click=self.set_layer_blur, 
                                tooltip="Set the blur only for existing content on this layer. Useful for backgrounds and effects. " \
                                "Will NOT effect any future content drawn on this layer" if visible else
                                "Layer must be visible to set image", 
                                data=name, focus_on_hover=False,
                                disabled=not visible,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(      # Set layer as a color button
                                "Set Color", leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY),
                                on_click=self.set_layer_content, 
                                tooltip="Set this layer to a solid color. This will overwrite any drawings on the layer currently." if visible else
                                "Layer must be visible to set color",
                                data="color", focus_on_hover=False,
                                disabled=not visible,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(      # Delete layer button
                                "Delete", leading=ft.Icon(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR),  
                                focus_on_hover=False,
                                tooltip="Delete this layer. This action cannot be undone.",
                                on_click=delete_layer,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            )
                        ],
                            
                        
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                        style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                    ),
                ],
                style=ft.MenuStyle(
                    bgcolor="transparent", shadow_color="transparent",
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
            ),
                    
                
            ), 
            data=name
        )
    
    # Sets the new active layer based on data
    async def set_new_active_layer(self, e: ft.Event):

        if self.state.manipulating_shape:
            await self.paint_tool_on_canvas()

        # Deselcted old list tile:
        for ctrl in self.sidebar_layers_list_view.controls:
            ctrl.content.bgcolor = None
            ctrl.content.content_padding = ft.Padding.only(left=10, right=30)

        # Update our new index live and in data
        new_layer_idx = e.control.data
        self.active_layer_idx = new_layer_idx
        self.data['canvas_data']['active_layer_idx'] = self.active_layer_idx
        
        # If not visible, set the list tile as visible and the canvas as well
        canvas = self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:
            canvas.visible = True   # Update canvas
            self.data.get('canvas_data', {}).get('layers', [])[self.active_layer_idx]['visible'] = True # update data
            e.control.leading.icon = ft.Icons.VISIBILITY
            

        # Apply data updates
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})

        # Update sidebar list tile background to reflect
        e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH
        e.control.content_padding = ft.Padding.only(left=20, right=30)
        self.set_mouse_cursor()
        self.update()

    # Toggles the visibility of a layer and updates the sidebar icon and background accordingly
    async def toggle_layer_visibility(self, e: ft.Event=None, layer_idx: int=None):
        layer_idx = e.control.parent.data if e is not None else layer_idx

        old_visibility = self.layer_stack.controls[layer_idx].visible
        new_visibility = not old_visibility

        # If we are hiding a dirty layer, save it before we make it invisible
        if new_visibility == False:
            if self.data.get('canvas_data', {}).get('layers', [])[layer_idx].get('dirty', False) == True:
                canvas: cv.Canvas = self.layer_stack.controls[layer_idx]
                if self.state.manipulating_shape:
                    await self.paint_tool_on_canvas()
                await self.save_canvas(canvas=canvas)

        # Update canvas visibility
        self.layer_stack.controls[layer_idx].visible = new_visibility
        self.data.get('canvas_data', {}).get('layers', [])[layer_idx]['visible'] = new_visibility

        # Update the icon in the sidebar list tile
        e.control.icon = ft.Icons.VISIBILITY if new_visibility else ft.Icons.VISIBILITY_OFF
        e.control.parent.bgcolor = None

        # If we are still active layer while being turned back visible, reflect that in sidebar
        if new_visibility and layer_idx == self.active_layer_idx:
            e.control.parent.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH

        # Set mouse cursor
        self.set_mouse_cursor()

        # Apply data updates
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
        self.update()

    # Update all our controls data that use indices to maintain state
    def update_indices(self):
        for idx, control in enumerate(self.sidebar_layers_list_view.controls):
            control.content.data = idx
        # Also update each canvas's stored index so save_canvas looks up the correct layer
        for idx, canvas in enumerate(self.layer_stack.controls):
            canvas.data = idx

    def build(self):
        super().build()

        # Reorder layers
        def reorder_layers(e: ft.OnReorderEvent):
            # Grab the active layer name before we move
            active_layer_name = self.data.get('canvas_data', {}).get('layers', [])[self.active_layer_idx].get('name', None)

            self.data.get('canvas_data', {}).get('layers', []).insert(e.new_index, self.data.get('canvas_data', {}).get('layers', []).pop(e.old_index))
            self.layer_stack.controls.insert(e.new_index, self.layer_stack.controls.pop(e.old_index))
            self.sidebar_layers_list_view.controls.insert(e.new_index, self.sidebar_layers_list_view.controls.pop(e.old_index))

            # Find the active layer's new index and sync both self and data
            for i, ctrl in enumerate(self.sidebar_layers_list_view.controls):
                if ctrl.data == active_layer_name:
                    self.active_layer_idx = i
                    break
            self.data['canvas_data']['active_layer_idx'] = self.active_layer_idx
            self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})

            #self.layer_stack.update()
            self.update()
            self.update_indices()  # Update indices so sidebar controls maintain correct idx reference
            
        
        


        self.layer_stack = ft.Stack(
            [self.create_new_layer_canvas_ctrl(idx, canvas_data) for idx, canvas_data in enumerate(self.data.get('canvas_data', {}).get('layers', []))],  
            alignment=ft.Alignment.CENTER, expand=False
        ) 
        
        
        # Controls drawing for our canvases
        self.canvas_controller = ft.GestureDetector(
            #mouse_cursor=ft.MouseCursor.NONE,
            on_pan_start=self.handle_pan_start,         # Starts a new brush stroke with current paint settings
            on_pan_update=self.handle_pan_update,           # Updates the current stroke based on mouse movement
            on_pan_end=self.handle_pan_end,                # Saves the now complete stroke to our data and canvas capture
            on_hover=lambda e: self.move_mouse_cursor(e.local_position),
            on_tap_up=self.handle_tap,                   # Handles adding dots and tools
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            drag_interval=5,
            hover_interval=5
        )

        self.mouse_cursor = ft.Icon(
            ft.Icons.CIRCLE_OUTLINED,
            size=18, visible=False,
            animate_position=ft.Animation(0, ft.AnimationCurve.LINEAR),
            offset=ft.Offset(-0.5, -0.5),
            left=self.CANVAS_WIDTH / 2,
            top=self.CANVAS_HEIGHT / 2,
        )
        self.set_mouse_cursor(False)
        
        
        # Holds our drawing so we can interact with it, zoom, pan, etc.
        interactive_viewer = ft.InteractiveViewer(
            content=ft.Stack([
                ft.Container(   # Transparent Background
                    ignore_interactions=True,
                    image=ft.DecorationImage("canvas_bg.png", alignment=ft.Alignment.TOP_LEFT, repeat=ft.ImageRepeat.REPEAT),
                    width=self.CANVAS_WIDTH,
                    height=self.CANVAS_HEIGHT,
                    expand=False,
                    #opacity=0.99
                ),     
                self.layer_stack, 
                self.mouse_cursor,
                self.canvas_controller,
            ]),
            expand=3, 
            constrained=False,
            scale_factor=800, boundary_margin=1500,
            min_scale=0.02, max_scale=3.0,
            #opacity=0.99
        )
        self.undo_button = ft.IconButton(
            ft.Icons.UNDO, ft.Colors.OUTLINE_VARIANT, #tooltip="Undo last task (ctrl+z)", 
            mouse_cursor=ft.MouseCursor.CLICK, 
            on_click=self.undo_task, disabled=True,
            tooltip="Coming Soon"
        )
        self.redo_button = ft.IconButton(
            ft.Icons.REDO_OUTLINED, ft.Colors.OUTLINE_VARIANT, #tooltip="Redo last task (ctrl+y or ctrl+shift+z)", 
            mouse_cursor=ft.MouseCursor.CLICK, 
            on_click=self.redo_task, disabled=True,
            tooltip="Coming Soon"
        )
        self.sidebar_header.controls.insert(1, self.undo_button)
        self.sidebar_header.controls.insert(2, self.redo_button)

        
        self.sidebar_layers_list_view = ft.ReorderableListView(
            [], 
            on_reorder=reorder_layers, 
            #scroll=ft.ScrollMode.ALWAYS, 
            expand=True, #show_default_drag_handles=False
        )   # This will hold our layers and allow us to reorder them


        # Add each layer to the expansion tile
        for idx, layer_data in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            self.sidebar_layers_list_view.controls.append(self.create_new_layer_sidebar_ctrl(idx, layer_data))

             

        self.sidebar_body.controls.extend([
            ft.Text(
                spans=[
                    ft.TextSpan("Width: ", ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),),
                    ft.TextSpan(f"{str(self.data.get('canvas_data', {}).get('width', ''))} pixels\n", ft.TextStyle(italic=True, color=ft.Colors.ON_SURFACE_VARIANT, size=14)),
                    ft.TextSpan("Height: ", ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),),
                    ft.TextSpan(f"{str(self.data.get('canvas_data', {}).get('height', ''))} pixels", ft.TextStyle(italic=True, color=ft.Colors.ON_SURFACE_VARIANT, size=14))
                ]
            ),
            
            ft.Row([    # Layer Label
                ft.Text(f"Layers", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=ft.Colors.PRIMARY), 
                ft.IconButton(      # Create new Layer button
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    ft.Colors.PRIMARY,
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_click=self.create_new_layer,
                )
            ], spacing=0),
            

            self.sidebar_layers_list_view,

            ft.Divider(),
            self.sidebar_notes_label,
            self.sidebar_notes_column
        ])

        # Set up our main conent
        self.content = ft.Stack([
            interactive_viewer,
            ft.Row(
                [self.toggle_sidebar_visibility_button, self.sidebar], 
                spacing=0, expand=True, alignment=ft.MainAxisAlignment.END, 
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)