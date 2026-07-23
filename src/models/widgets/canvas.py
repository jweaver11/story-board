'''
The canvas class for all canvases inside our story
Canvases are drawings and images
'''

from flet_color_pickers import ColorPicker
import flet as ft
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

MINIMUM_SEGMENT_DISTANCE = 2
MAX_SHAPES_BEFORE_CAPTURE = 30
MAX_UNDO_LIST_TASKS = 30
MIN_UPDATE_INTERVAL = 0.016  # ~60fps cap on canvas updates


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
            self.data.update({
                # Widget data
                "tag": "canvas",
                'color': app.settings.data.get('widget_defaults', {}).get('canvas', {}).get('color'),
                'show_sidebar': True,   # Whether to show the info column on the side of our charts or not.

                'capture': str(),             # Capture of what we currently look like
                'snapshot': str(),            # Most recent completed snapshot of our canvas used by other widgets

                'reference_images': list(),     # Reference images from sketches from a canvas board or uploaded images that appear in sidebar

                # Info about the canvas
                'canvas_data': {

                    # Sizing
                    "width": (data or {}).get('canvas_data', {}).get('width') or 1920,
                    "height": (data or {}).get('canvas_data', {}).get('height') or 1080,

                    'active_layer_idx': 1,   # Index of our active layer we are drawing on

                    # Layer info for our canvases
                    'layers': [
                        {       # First/Bottom most layer
                            'name': "Background",       # Name of that layer. We keep unique so our undo/redo system can correctly identify it
                            'visible': True,            # Whether this layer is currently visible or not
                            'dirty': False,              # Whether this layer has been modified since last save and needs to be re-captured
                            'capture': "",              # The current displayed capture for this layer
                        },
                        {        # Second layer
                            'name': "Layer 1", 
                            'visible': True, 
                            'dirty': False,
                            'capture': "",   
                        }
                    ],    
                }
            },
        )

        # State tracking for canvas drawing info
        self.state = State()                # Used for tracking our coords and current drawing data for the active stroke/shape being applied
        self.canvas_width = self.data.get('canvas_data', {}).get('width', 0)    # Ez size grabbing later
        self.canvas_height = self.data.get('canvas_data', {}).get('height', 0)   

        # Drawing stuff
        self.current_path: cv.Path      # The current path being drawn on the canvas, if any
        self.active_layer_idx: int = self.data.get('canvas_data', {}).get('active_layer_idx', 1)        # Which layer we are drawing on
        self.layer_stack: ft.Stack                # Stack to hold our list of layer canvases on top of each other
        self.canvas_controller: ft.GestureDetector  # Controller that sits over our layer stack and handles mouse events for drawing and tool usage
        
        # Tool and shape stuff
        self.current_tool: CanvasShape = None                     # The active shape being added if we're using a tool
        #self.tool_rotate_handle: ft.GestureDetector         # Handle for rotating the current tool 
        
        # Sidebar controls. Undo/redo buttons
        self.undo_button: ft.IconButton
        self.redo_button: ft.IconButton


    # If we have changes that havnt been saved to data, we save them before writing
    async def save_file(self):
        for i, layer in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            if layer.get('dirty', False) == True:
                canvas: cv.Canvas = self.layer_stack.controls[i]
                await self.save_canvas(canvas)
                self.needs_file_write = True    # Mark our widget as dirty if we saved anything
        await super().save_file()            
   
    # Sets our mouse cursor on hovering for feedback, depending on drawing or using tool
    def set_mouse_cursor(self):
        
        control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
        active_tool = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
        
        if active_tool == "erase" or active_tool == "line":
            new_mouse_cursor = ft.MouseCursor.PRECISE
        else:
            new_mouse_cursor = ft.MouseCursor.CLICK
        if control_mode == "draw":
            new_mouse_cursor = ft.MouseCursor.PRECISE

        if self.active_layer_idx > len(self.data.get('canvas_data', {}).get('layers', [])) - 1:
            self.active_layer_idx = len(self.data.get('canvas_data', {}).get('layers', [])) - 1
            return
        if self.layer_stack.controls[self.active_layer_idx].visible == False:
            new_mouse_cursor = None
            print("Mouse cursor set to: 4", new_mouse_cursor)

        # Paints a shape we're modifying if the rail tool changes
        if self.state.manipulating_shape:
            self.page.run_task(self.paint_tool_on_canvas)
        
        return new_mouse_cursor

    # Shows our sidebar and paints a tool on canvas if needed
    async def show_sidebar(self, e: ft.Event):
        if self.state.manipulating_shape:
            await self.paint_tool_on_canvas()
            
        await super().show_sidebar(e)
           
    # If we have an active tool/shape that we are manipulating, paint it on the canvas
    async def paint_tool_on_canvas(self):
        ''' Converts the displayed shapes rotation and size onto our active layer and paints it there '''

        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible or self.current_tool is None:  # Catch errors
            self.page.show_dialog(SnackBar("Error finding visible canvas or tool."))
            return

        self.manipulating_shape = False   # Update state
        
        # Text can be rotated, so we can just grab it and put it in the right spot
        if self.current_tool.shape_type == "text":

            # Align our text to account for size of our layer canvas
            text_shape: cv.Text = self.current_tool.cv_shape
            text_shape.x += self.current_tool.left + 2
            text_shape.y += self.current_tool.top + 2
            
            canvas.shapes.append(text_shape)
            await self.end_stroke(canvas=canvas)
            self.current_tool.visible = False
            self.current_tool.rotate_handle.visible = False
           
            self.update()
            return

        # Capture the current tool
        await self.current_tool.canvas.capture()
        shape_capture = await self.current_tool.canvas.get_capture()

        # Grab the image and rotate
        shape_img = Image.open(BytesIO(shape_capture)).convert("RGBA")
        angle = self.current_tool.rotate.angle

        # Flet rotate.angle is radians; PIL rotate() takes degrees counterclockwise
        angle_degrees = -math.degrees(angle)
        rotated = shape_img.rotate(angle_degrees, expand=True, resample=Image.Resampling.BICUBIC)
        # Set rotation (with border padding)
        rotation_cx = self.current_tool.left + (self.current_tool.canvas.width + 4) / 2
        rotation_cy = self.current_tool.top + (self.current_tool.canvas.height + 4) / 2

        # Calculate the position to paste the rotated image onto the canvas
        paste_x = int(rotation_cx - rotated.width / 2)
        paste_y = int(rotation_cy - rotated.height / 2)

        # Grab the existing capture
        layer_b64 = self.data['canvas_data']['layers'][self.active_layer_idx].get('capture')
        if layer_b64:
            layer_img = Image.open(BytesIO(base64.b64decode(layer_b64))).convert("RGBA")
        else:
            layer_img = Image.new("RGBA", (self.canvas_width, self.canvas_height), (0, 0, 0, 0))

        # Composite using the shape's alpha channel as the mask
        overlay = Image.new("RGBA", layer_img.size, (0, 0, 0, 0))
        overlay.paste(rotated, (paste_x, paste_y))
        layer_img = Image.alpha_composite(layer_img, overlay)

        output = BytesIO()
        layer_img.save(output, format="PNG")
        encoded = base64.b64encode(output.getvalue()).decode('utf-8')

        canvas.shapes.clear()   
        canvas.shapes.append(cv.Image(encoded, 0, 0))
        await self.end_stroke(canvas=canvas)
            
        # Finally, remove the active tool stuff
        self.current_tool.visible = False
        self.current_tool.rotate_handle.visible = False
        self.update()

    # Updates any live text tools if we changed a setting that would affect it
    def update_tool_preview(self):
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()
        paint_settings = app.settings.data.get('paint_settings', {}).copy()

        decoration = canvas_settings.get('text_shape_decoration', "none")
        match decoration:
            case "Underline": text_decoration = ft.TextDecoration.UNDERLINE
            case "Overline": text_decoration = ft.TextDecoration.OVERLINE
            case "Line Through": text_decoration = ft.TextDecoration.LINE_THROUGH
            case _: text_decoration = None

        if self.state.manipulating_shape:
        
            # Fix any paint changess
            self.current_tool.paint.color = paint_settings.get('color', ft.Colors.BLACK) if canvas_settings.get('use_paint_for_shapes', True) else ft.Colors.BLACK
            self.current_tool.paint.stroke_width=paint_settings.get('stroke_width', 3) if canvas_settings.get('use_paint_for_shapes', True) else 3
            self.current_tool.paint.style=paint_settings.get('style', ft.PaintingStyle.STROKE)
            self.current_tool.paint.stroke_cap=paint_settings.get('stroke_cap', "round") if canvas_settings.get('use_paint_for_shapes', True) else "round"
            self.current_tool.paint.stroke_join=paint_settings.get('stroke_join', "round") if canvas_settings.get('use_paint_for_shapes', True) else "round"
            self.current_tool.paint.blur_image=paint_settings.get('blur_image', 0) if canvas_settings.get('use_paint_for_shapes', True) else 0
            self.current_tool.paint.anti_alias=paint_settings.get('anti_alias', True) if canvas_settings.get('use_paint_for_shapes', True) else True
        
            if self.current_tool.shape_type == "text":
                self.current_tool.cv_shape.style = ft.TextStyle(
                    size=canvas_settings.get('text_shape_size', 20),
                    weight=ft.FontWeight.BOLD if canvas_settings.get('text_shape_bold', False) else ft.FontWeight.NORMAL,
                    color=canvas_settings.get('text_shape_color', ft.Colors.ON_SURFACE),
                    italic=canvas_settings.get('text_shape_italic', False),
                    decoration=text_decoration,
                    shadow=ft.BoxShadow(color=canvas_settings.get('text_shadow_color', ft.Colors.TRANSPARENT), blur_radius=5),
                    letter_spacing=canvas_settings.get('text_shape_letter_spacing', 0),
                    word_spacing=canvas_settings.get('text_shape_word_spacing', 0),
                )
            elif self.current_tool.shape_type == "rectangle":
                self.current_tool.cv_shape.border_radius = ft.BorderRadius.all(
                    canvas_settings.get('rectangle_border_radius', 0)
                )

            self.current_tool.cv_shape.update()


    # Called when we click the canvas and don't initiate a drag. Adds either a point if in draw mode, or active tool/shape if in tool mode
    async def handle_tap(self, e: ft.TapEvent):

        # Set our paint settings in case we need to change them
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()

        # Check if we're in tool mode, and what tool we're using
        if canvas_settings.get('current_control_mode', "") == "tool":
            tool_name = canvas_settings.get('current_tool_name', "")
            match tool_name:

                # Skip lines and erase mode, since they are drawn normally
                case "line" | "erase":
                    pass

                # All other tools/shapes get added here
                case _:

                    # If we are currently manipulating one shape, paint it to the canvas
                    if self.state.manipulating_shape:
                        self.state.manipulating_shape = False
                        await self.paint_tool_on_canvas()
                        return
    

                    self.state.manipulating_shape = True
                    self.current_tool = CanvasShape(tool_name, left=e.local_position.x, top=e.local_position.y)
                    self.canvas_controller.parent.controls.append(self.current_tool)
                    self.canvas_controller.parent.update()
                    self.canvas_controller.parent.controls.append(self.current_tool.rotate_handle)
                    self.canvas_controller.parent.update()
            return
            
        else:
            # We're not manipulating a shape, so we can add a point to the canvas
            self.state.manipulating_shape = False 

            # Grab our canvas
            canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
            if not canvas.visible:  # Catch errors
                return
            
            # Add our point to the canvas and our paint settings, update, and save
            canvas.shapes.append(cv.Points(points=[(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings)))
            canvas.update()
            await self.end_stroke(canvas)
        
    # Called when we start drawing on the canvas
    def start_stroke(self, e: ft.DragStartEvent):
        ''' Set our initial starting x and y coordinates for the element we're drawing. '''

        # Grab the canvas and paint settings
        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:  # Protect when we shouldnt be drawing with it
            self.page.show_dialog(SnackBar("Set an active layer to draw on."))
            return
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()
    
        # Update our state x and y coordinates
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

        # Check if we're in tool mode, and what tool we're using
        if canvas_settings.get('current_control_mode', "") == "tool":
            tool_name = canvas_settings.get('current_tool_name', "")
            match tool_name:
                # Erase tool - make sure our paint settings don't break the drawing because of blur or style
                case "erase":
                    paint_settings['blend_mode'] = "clear"
                    paint_settings['blur_image'] = 0
                    paint_settings['style'] = "stroke"
                    self.current_path = cv.Path(elements=[cv.Path.MoveTo(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
                # For line tool - add the first line element to the path
                case "line":
                    paint_settings['style'] = "stroke"
                    self.current_path = cv.Path(elements=[cv.Path.MoveTo(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
                    line_element = cv.Path.LineTo(self.state.x, self.state.y)
                    self.current_path.elements.append(line_element)

                # Ignore all other tools, as they will control themselves by getting added to the canvas
                case _:
                    return
                
            # Add our tool to the canvas so we can see it
            canvas.shapes.append(self.current_path)
            canvas.update()
            return

        # Otherwise we're in draw mode
        else:
            # If we're using brush smoothing, create a path element for consistant paint
            if canvas_settings.get('use_brush_smoothing', False) == True or paint_settings.get('style', "") == "stroke_fill":
                self.current_path = cv.Path(elements=[cv.Path.MoveTo(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
                canvas.shapes.append(self.current_path)

            # No brush smoothing, just add a line element to the canvas
            else: 
                canvas.shapes.append(cv.Line(self.state.x, self.state.y, e.local_position.x, e.local_position.y, paint=ft.Paint(**paint_settings)))
            canvas.update()
        
    # Called when actively drawing on the canvas
    def update_stroke(self, e: ft.DragUpdateEvent):
        ''' Determines which drawing tool we're using, and updates accordingly as we drag our mouse '''
        
        # Sampling to improve perforamance. If the line length is too small, we skip it
        #dx = e.local_position.x - self.state.x
        #dy = e.local_position.y - self.state.y
        #if dx * dx + dy * dy < MINIMUM_SEGMENT_DISTANCE * MINIMUM_SEGMENT_DISTANCE:
            #return

        # Grab canvas and catch errors
        canvas: cv.Canvas =  self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:  
            return
        
        # Grab the current path
        self.current_path = canvas.shapes[-1] if canvas.shapes else None

        # Catch errors
        if not self.current_path:
            return
        
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()
                
        # Check if we're in tool mode, and what tool we're using
        if canvas_settings.get('current_control_mode', "") == "tool":

            tool_name = canvas_settings.get('current_tool_name', "")
            match tool_name:

                # Make erase tool use a path
                case "erase":
                    path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
                    self.current_path.elements.append(path_element)

                # For line tool - Update our straight line element to the current mouse position
                case "line":
                    # Set the element and update its position
                    line_element = self.current_path.elements[-1]
                    line_element.x = e.local_position.x
                    line_element.y = e.local_position.y
                    
                # Ignore all other tools and return out so we don't draw
                case _:
                    pass

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
        

    # Called when we release the mouse to stop drawing a line
    async def end_stroke(self, e: ft.DragEndEvent=None, canvas: cv.Canvas=None):
        """ Saves our paths to our canvas data for storage """

        # Set our canvas, layer name, and update our shapes count
        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx] if canvas is None else canvas
        if not canvas.visible:  # Protect when we shouldnt be drawing with it
            return
        
        # Grab our layer and mark it as dirty
        layer_idx = int(canvas.data)
        layer_data = self.data.get('canvas_data', {}).get('layers', [])[layer_idx]
        layer_data['dirty'] = True
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})   # Update our data with the new capture for this layer

        # Grab paint and canvas settings
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        canvas_settings = app.settings.data.get('canvas_settings', {}).copy()

        # If we have too many shapes on the canvas, save its capture to the layer data
        if len(canvas.shapes) > MAX_SHAPES_BEFORE_CAPTURE:
            updated_capture = await self.save_canvas(canvas)
            canvas.shapes.clear()
            canvas.shapes.append(cv.Image(updated_capture, 0, 0, self.canvas_width, self.canvas_height)) 
            canvas.update()
            
            
        # Always re-render end of erase strokes, or they will appear broken?
        #elif canvas_settings.get('current_control_mode', "") == "tool" and canvas_settings.get('current_tool_name', "") == "erase":   
            #updated_capture = await self.save_canvas(canvas)
            #canvas.shapes.clear()
            #canvas.shapes.append(cv.Image(updated_capture, 0, 0, self.canvas_width, self.canvas_height))
            #canvas.update()

        # Always re-render end of non-none blend mode strokes, or they will appear broken?
        #elif paint_settings.get('blend_mode', "") is not None: 
            #updated_capture = await self.save_canvas(canvas)
            #canvas.shapes.clear()
            #canvas.shapes.append(cv.Image(updated_capture, 0, 0, self.canvas_width, self.canvas_height))
            #canvas.update()

        self.add_undo_task({
            'task_type': 'path_stroke',
            'layer_name': layer_data.get('name', ''),
            #'data': self.current_path
        })

        

    # Saves the current capture of a canvas to data
    async def save_canvas(self, canvas: cv.Canvas) -> bytes:

        # Protect bad calls
        if canvas.visible == False:  
            return
                
        # Grab our capture for the canvas
        await canvas.capture()
        capture = await canvas.get_capture()
        encoded_capture = base64.b64encode(capture).decode('utf-8') 
        await canvas.clear_capture()

        # Grab the layer data using the index
        layer_idx = int(canvas.data)
        layer_data = self.data.get('canvas_data', {}).get('layers', [])[layer_idx]

        # Update its capture and mark it as not dirty anymore
        layer_data['capture'] = encoded_capture      
        layer_data['dirty'] = False    
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})   # Update our data with the new capture

        return capture  # Return capture if other functions want to use it
    
    # Accepts the formatted undo task data, adds it to state and handles UI updates for the undo/redo buttons
    def add_undo_task(self, task_data: dict):
        # Add most recent path to undo list, clear redo list, and check undo list not too long
        self.state.undo_list.append(task_data)
        self.state.redo_list.clear()    
        if len(self.state.undo_list) > MAX_UNDO_LIST_TASKS: 
            self.state.undo_list.pop(0)
        
        # Handle buttons
        self.undo_button.disabled = False
        self.undo_button.icon_color = self.data.get('color', None)
        self.redo_button.disabled = True
        if len(self.state.redo_list) == 0:
            self.redo_button.icon_color = ft.Colors.OUTLINE_VARIANT
            self.undo_button.update()
            self.redo_button.update()

    def add_redo_task(self, task_data: dict):
        # Add most recent path to redo list, clear undo list, and check redo list not too long
        self.state.redo_list.append(task_data)
        self.state.undo_list.clear()    
        if len(self.state.redo_list) > MAX_UNDO_LIST_TASKS: 
            self.state.redo_list.pop(0)
        
        # Handle buttons
        self.redo_button.disabled = False
        self.redo_button.icon_color = self.data.get('color', None)
        self.redo_button.update()
        if len(self.state.undo_list) == 0:
            self.undo_button.disabled = True
            self.undo_button.icon_color = ft.Colors.OUTLINE_VARIANT
            self.undo_button.update()
        

    # Called when undoing a stroke on the canvas
    def undo_task(self, e=None):

        # If there's nothing to undo, return early
        if len(self.state.undo_list) == 0:
            return
        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:  # Should be impossible
            return
                
        # Grab the task we're going to carry out and its name and capture
        task = self.state.undo_list.pop()    
        task_type = task.get('task_type', None)
        layer_name = task.get('layer_name', None)
        data = task.get('data', None)

        layer_canvas = None
        for idx, layer in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            if layer.get('name', None) == layer_name:
                layer_canvas = self.layer_stack.controls[idx]
                break
        if layer_canvas is None:
            self.page.show_dialog(SnackBar(f"Error finding layer {layer_name} to undo task."))
            return

        match str(task_type):
            case "path_stroke":
                pass
            case "line_strokes":
                pass
            case "set_layer_visibility":
                pass
            case _:
                print("Unknown task type for undo: ", task_type)

        self.add_redo_task(task)    # Add the task we just undid to the redo list
        

    # Called when redoing a stroke on the canvas after a previous undo
    def redo_task(self, e=None):
        # Return early if nothing to redo
        if len(self.state.redo_list) == 0:
            return
        canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]
        if not canvas.visible:  # Should be impossible
            return
        
        # Grab the task we're going to carry out and its name and capture
        task = self.state.redo_list.pop()    
        task_type = task.get('task_type', None)
        layer_name = task.get('layer_name', None)
        data = task.get('data', None)

        layer_canvas = None
        for idx, layer in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            if layer.get('name', None) == layer_name:
                layer_canvas = self.layer_stack.controls[idx]
                break
        if layer_canvas is None:
            self.page.show_dialog(SnackBar(f"Error finding layer {layer_name} to undo task."))
            return

        match task_type:
            case "path_stroke":
                pass
            case "line_strokes":
                pass
            case "set_layer_visibility":
                pass
            case _:
                print("Unknown task type for undo: ", task_type)

        self.add_undo_task(task)    # Add the task we just undid to the redo list

    # Sets either an image or a color as the content of a layer
    async def set_layer_content(self, e: ft.Event):

        await self.story.close_menu()

        content_type = e.control.data
        layer_idx = e.control.parent.parent.parent.data
        layer_name = self.data.get('canvas_data', {}).get('layers', [])[layer_idx].get('name', '')

        # Set a color as the background
        if content_type == "color":

            async def _color_change(e):     # Set the color to the picked one
                color_picker.color = e.data

            async def _set_color_confirmed(e=None):

                canvas: cv.Canvas = self.layer_stack.controls[layer_idx]
                canvas.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
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
                title=f"Set {layer_name} to a Color",
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
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        canvas: cv.Canvas = self.layer_stack.controls[layer_idx]
                        canvas.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                        canvas.shapes.append(cv.Image(f"{encoded_string}", 0, 0, self.canvas_width, self.canvas_height))   # Re-add empty images so it can capture
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
            canvas.shapes.append(cv.Image(capture, 0, 0, self.canvas_width, self.canvas_height, paint=ft.Paint(blur_image=blur_strength)))
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
            if layer.get('name') == layer_name:
                active_preview_image = cv.Image(layer.get('capture', ""), 0, 0, self.page.width / 2, self.page.height / 2, paint=ft.Paint(blur_image=1))
                preview_canvas.content.shapes.append(active_preview_image)
                continue
            preview_canvas.content.shapes.append(cv.Image(layer.get('capture', ""), 0, 0, self.page.width / 2, self.page.height / 2))
            
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


    # Called when we click to export a canvas
    async def export_canvas_clicked(self, e=None):
        """ Exports canvas to correct file type based on selection with optional upscaling """

        # Merge all our layer/canvas captures together into one image at the right size
        def _merge_captures(captures_list: list, target_width: int=None, target_height: int=None):

            images = []     # Start with an images list

            if target_width is None or target_height is None:
                images = [Image.open(BytesIO(capture)).convert("RGBA") for capture in captures_list]
                width, height = images[0].size      # Set the width and height we use based on actual size

            else:
                width, height = target_width, target_height     # Set width and height to target size

                # Go through our captures list
                for capture in captures_list:
                    image = Image.open(BytesIO(capture)).convert("RGBA")        # Create the image for each capture

                    # Resize if necessary
                    if target_width and target_height:
                        if image.size != (target_width, target_height):
                            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

                    images.append(image)        # Add to list

            if not images:      # Catch errors
                return
            
            merged = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            
            # Put all the images together
            for image in images:
                merged = Image.alpha_composite(merged, image)

            # Gives us the output we want
            output = BytesIO()
            merged.save(output, format="PNG")
            file_output = output.getvalue()
            return file_output

        # List to store our captures for each layer of our canvas
        captures_list = []


        # Go through our layers now
        for layer in self.layer_stack.controls:

            # Grab container to check if actually visible. Not visible, not exporting
            container = layer.get('canvas', None)
            if not container.visible:   
                continue

            # Grab canvas our canvas for that layer
            canvas: cv.Canvas = self.layer_stack.controls[self.active_layer_idx]

            # Capture and add that capture to the list
            if canvas is not None:
                await canvas.capture()       # Upscale/downscale the capture based on size
                cc = await canvas.get_capture()
                captures_list.append(cc)         # Add the capture to the list
                await canvas.clear_capture()     # Clear the capture to prevent bugs 

        # Our exportable image bytes from merging all our layers captures together with any scaling needed
        merged_bytes = _merge_captures(captures_list, self.canvas_width, self.canvas_height)

        # Open file dialog to save that capture
        if merged_bytes:
            await ft.FilePicker().save_file(
                src_bytes=merged_bytes, file_name=f"{self.title}.png", 
                file_type=ft.FilePickerFileType.IMAGE, allowed_extensions=["png"]
            )

    # Adds a new layer into data, on the canvas, and in the sidebar
    def create_new_layer(self, e: ft.Event=None):
        # Find a unique layer name
        existing_names = {layer.get('name') for layer in self.data.get('canvas_data', {}).get('layers', [])}
        n = len(existing_names)
        while f"Layer {n}" in existing_names:
            n += 1
        new_name = f"Layer {n}"
        # Update data
        self.data.get('canvas_data', {}).get('layers', []).append({
            'name': new_name,
            'visible': True,
            'capture': None
        })

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
        capture = canvas_data.get('capture', None)

        return cv.Canvas(
            data=idx,        # Save the index of this layer so we know where to save it in our data
            shapes=[
                cv.Image(       # Sets the background image of the layer to its most recent capture
                    capture, 0, 0, 
                    width=self.canvas_width,          # Ignore setting size before we know it
                    height=self.canvas_height
                )    
            ],
            visible=visible,
            width=self.canvas_width,
            height=self.canvas_height,
            opacity=0.99    # Forces dif render layer
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
                    title_text := ft.Text(name, weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE), 
                    title_tf := ft.TextField(
                        value=name, visible=False,
                        dense=True, 
                        on_submit=update_layer_name,
                        on_blur=hide_layer_name_tf,
                        #border=ft.InputBorder.NONE, 
                        border_radius=4,
                        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                        focused_bgcolor=ft.Colors.TRANSPARENT,
                        bgcolor=ft.Colors.TRANSPARENT,
                        capitalization=ft.TextCapitalization.WORDS,
                    ),
                ]),
                leading=ft.IconButton(   # Toggle visibility button
                    ft.Icons.VISIBILITY if visible else ft.Icons.VISIBILITY_OFF, 
                    self.data.get('color', ft.Colors.PRIMARY),
                    mouse_cursor="click",
                    on_click=self.toggle_layer_visibility
                ),  
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if self.active_layer_idx == idx and visible == True else None,  # Lighter bg for selected layer
                on_click=self.set_new_active_layer, 
                data=idx,
                dense=True, content_padding=ft.Padding.only(left=10, right=30), 
                shape=ft.RoundedRectangleBorder(radius=4), 
                tooltip="Click to select this layer",
                trailing=ft.MenuBar(
                    [
                    ft.SubmenuButton(
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                        [
                            ft.MenuItemButton(      # Rename layer button
                                "Rename", leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                                focus_on_hover=False,
                                on_click=rename_layer_clicked, 
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(      # Set layer as an image button
                                "Set Image", leading=ft.Icon(ft.Icons.IMAGE_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)), 
                                on_click=self.set_layer_content, 
                                tooltip="Upload an image for this layer. This will overwrite any drawings on the layer currently." if visible else
                                "Layer must be visible to set image", 
                                data="image",
                                disabled=not visible, focus_on_hover=False,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(      # Set layer blur button
                                "Set Blur", leading=ft.Icon(ft.Icons.BLUR_ON_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)), 
                                on_click=self.set_layer_blur, 
                                tooltip="Set the blur only for existing content on this layer. Useful for backgrounds and effects. " \
                                "Will NOT effect any future content drawn on this layer" if visible else
                                "Layer must be visible to set image", 
                                data=name, focus_on_hover=False,
                                disabled=not visible,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(      # Set layer as a color button
                                "Set Color", leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
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
                        tooltip="Adjust the settings for this bar chart."
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
        self.canvas_controller.mouse_cursor = self.set_mouse_cursor()
        self.update()

    # Toggles the visibility of a layer and updates the sidebar icon and background accordingly
    async def toggle_layer_visibility(self, e: ft.Event=None):
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
        self.canvas_controller.mouse_cursor = self.set_mouse_cursor()

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
        async def reorder_layers(e: ft.OnReorderEvent):
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
            
        # Downscales images for preview to improve performance
        def downscale_image(image_str: str) -> str:

            try:
                image_bytes = base64.b64decode(image_str)
                img = Image.open(BytesIO(image_bytes))
                if img.mode in ("P", "PA"):  # palette images with transparency must go via RGBA
                    img = img.convert("RGBA")
                has_alpha = img.mode in ("RGBA", "LA")
                if not has_alpha:
                    img = img.convert("RGB")
                max_dim = 2160  # cap at 4K height; anything larger is not visible anyway
                if img.width > max_dim or img.height > max_dim:
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                output = BytesIO()
                if has_alpha:
                    img.save(output, format="PNG", optimize=True)
                else:
                    img.save(output, format="JPEG", quality=92, optimize=True)
                image_str = base64.b64encode(output.getvalue()).decode("utf-8")
            except Exception:
                pass 
            return image_str
        

        self.layer_stack = ft.Stack(
            [self.create_new_layer_canvas_ctrl(idx, canvas_data) for idx, canvas_data in enumerate(self.data.get('canvas_data', {}).get('layers', []))],  
            alignment=ft.Alignment.CENTER, expand=False
        ) 

        
        # Controls drawing for our canvases
        self.canvas_controller = ft.GestureDetector(
            mouse_cursor=self.set_mouse_cursor(),        # Set our mouse cursor based on current control mode
            on_pan_start=self.start_stroke,         # Starts a new brush stroke with current paint settings
            on_pan_update=self.update_stroke,           # Updates the current stroke based on mouse movement
            on_pan_end=self.end_stroke,                # Saves the now complete stroke to our data and canvas capture
            on_tap_up=self.handle_tap,                   # Handles adding dots and tools
            width=self.canvas_width,
            height=self.canvas_height,
            drag_interval=5
        )
        
        
        # Holds our drawing so we can interact with it, zoom, pan, etc.
        interactive_viewer = ft.InteractiveViewer(
            content=ft.Stack([
                ft.Container(   # Transparent Background
                    ignore_interactions=True,
                    image=ft.DecorationImage("canvas_bg.png", alignment=ft.Alignment.TOP_LEFT, repeat=ft.ImageRepeat.REPEAT),
                    width=self.canvas_width,
                    height=self.canvas_height,
                    expand=False
                ),     
                #canvas_transparent_bg_dark_mode.png
                #dark_mode_transparent_background.jpg
                self.layer_stack, 
                self.canvas_controller      # Controller that sits on top
            ]),
            expand=3, 
            constrained=False,
            scale_factor=800, boundary_margin=500,
            min_scale=0.02, max_scale=3.0,
        )
        self.undo_button = ft.IconButton(
            ft.Icons.UNDO, ft.Colors.OUTLINE_VARIANT, tooltip="Undo", mouse_cursor=ft.MouseCursor.CLICK, 
            on_click=self.undo_task, disabled=True
        )
        self.redo_button = ft.IconButton(
            ft.Icons.REDO_OUTLINED, ft.Colors.OUTLINE_VARIANT, tooltip="Redo", mouse_cursor=ft.MouseCursor.CLICK, 
            on_click=self.redo_task, disabled=True
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
            self.description_tf,

            ft.Text(
                spans=[
                    ft.TextSpan("Width: ", ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),),
                    ft.TextSpan(f"{str(self.data.get('canvas_data', {}).get('width', ''))} pixels\n", ft.TextStyle(italic=True, color=ft.Colors.ON_SURFACE_VARIANT, size=14)),
                    ft.TextSpan("Height: ", ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),),
                    ft.TextSpan(f"{str(self.data.get('canvas_data', {}).get('height', ''))} pixels", ft.TextStyle(italic=True, color=ft.Colors.ON_SURFACE_VARIANT, size=14))
                ]
            ),
            
            ft.Row([    # Layer Label
                ft.Text(f"Layers", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)), 
                ft.IconButton(      # Create new Layer button
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    self.data.get('color', ft.Colors.PRIMARY),
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_click=self.create_new_layer,
                )
            ], spacing=0),
            

            self.sidebar_layers_list_view,

            ft.Divider(),
            self.sidebar_notes_label,
            self.sidebar_notes_column
        ])

        #self.content = ft.Row([interactive_viewer, self.show_sidebar_button, self.sidebar], expand=True, spacing=0)

        # Set up our main conent
        self.content = ft.Stack([
            ft.Row([interactive_viewer, self.sidebar], spacing=0, expand=True),
            self.show_sidebar_button, 
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)

        

        


# TODO: 
# Closing app, or hiding widget makes sure to save all canvases that are dirty