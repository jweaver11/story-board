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
from styles.text_field import TextField

MINIMUM_SEGMENT_DISTANCE = 2
MAX_SHAPES_BEFORE_CAPTURE = 30   # Prevent lag from too many paths on the canvas without being removed
MAX_UNDO_LIST_TASKS = 30         # Max number of undo tasks to store in our undo list before we start deleting old ones


class Canvas(Widget):
    def __init__(
        self, 
        title: str, 
        directory_path: str, 
        story: Story, 
        data: dict = None,
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

                # Info about the canvas
                'canvas_data': {

                    # Sizing
                    "width": 1920 if data.get('canvas_data', {}).get('width') is None else data.get('canvas_data', {}).get('width'),              # Resolution size used for exporting
                    "height": 1080 if data.get('canvas_data', {}).get('height') is None else data.get('canvas_data', {}).get('height'),

                    # Undo and redo list
                    'undo_list': list(),        # Each undo/redo item {'layer_name': "", 'capture': ""} 
                    'redo_list': list(),

                    'active_layer_idx': 1,   # Index of our active layer we are drawing on

                    # Layer info for our canvases
                    'layers': [
                        {       # First/Bottom most layer
                            'name': "Background",       # Name of that layer. We keep unique so our undo/redo system can correctly identify it
                            'visible': True,            # Whether this layer is currently visible or not
                            'capture': "",              # The current displayed capture for this layer
                        },
                        {        # Second layer
                            'name': "Layer 1", 
                            'visible': True, 
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
        
        self.manipulating_shape = False     # Whether we're currently manipulating a shape or not, so we know whether to update our active path or not when dragging
        self.active_layer_idx: int = self.data.get('canvas_data', {}).get('active_layer_idx', 1)
        
        self.layer_canvases = []                  # List of our layers, which are each their own canvas
        self.layer_stack: ft.Stack          # Stack to hold our layers on top of each other

        self.bg_image: ft.DecorationImage   # Hold our background image
        
        # The active stroke we are adding to the canvas when drawing so we know how to update it
        self.current_path = cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))

        self.active_tool: CanvasShape                    # The active shape being added if we're using a tool

        # We render our own mini widgets (comments), so we don't need parent class to render them as well
        


        # OLD - Phase out
        self.needs_redraw = False           # Used to track if we need to redraw canvas after a resize
        self.skip_first_resize = True       # Skip the first resize since it will fix itself
        self.initial_resize = True          # Initial resize to track our canvases size without rebuild
        self.no_render_mini_widgets = True  


    
        
            

    # Sets the size of the canvas for redrawing logic
    async def _set_size_old(self, e: cv.CanvasResizeEvent):
        if e: 
            
            self.needs_redraw = True           # Prevent resizing for now
            if self.initial_resize:
                self.initial_resize = False
                self.needs_redraw = False

                # Handles switching to tab of canvas upon first launch
                try:
                    for layer in self.layer_canvases:
                        container = layer.get('canvas')
                        if container and isinstance(container.content, cv.Canvas):
                            shapes = container.content.shapes
                            if shapes and isinstance(shapes[0], cv.Image):
                                shapes[0].width = self.canvas_width
                                shapes[0].height = self.canvas_height
                    self.layer_stack.update()
                except Exception:
                    pass
                
            return
    
    # Sets our mouse cursor on hovering for feedback, depending on drawing or using tool
    async def set_mouse_cursor(self, update: bool=True):
        
        control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
        active_tool = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
        
        if active_tool == "erase" or active_tool == "line":
            new_mouse_cursor = ft.MouseCursor.PRECISE
        else:
            new_mouse_cursor = ft.MouseCursor.CLICK
        if control_mode == "draw":
            new_mouse_cursor = ft.MouseCursor.PRECISE

        if self.active_layer_idx >= len(self.layer_canvases):
            self.active_layer_idx = len(self.layer_canvases) - 1
            return
        if self.layer_canvases[self.active_layer_idx].visible == False:
            new_mouse_cursor = None
        
        self.canvas_controller.mouse_cursor = new_mouse_cursor
        if update:
            self.canvas_controller.update()

        # Paints a shape we're modifying if the rail tool changes
        if self.manipulating_shape:
            await self.paint_tool_on_canvas()
            self.manipulating_shape = False
       

    

    async def show_sidebar(self, e: ft.Event):
        if self.manipulating_shape:
            await self.paint_tool_on_canvas()
            self.manipulating_shape = False
        await super().show_sidebar(e)
           
    # If we have an active tool/shape that we are manipulating, paint it on the canvas
    async def paint_tool_on_canvas(self):
        ''' Converts the displayed shapes rotation and size onto our active layer and paints it there '''

      
        active_canvas: cv.Canvas = self.layer_canvases[self.active_layer_idx]
        for layer in self.layer_canvases:
            if self.data.get('canvas_data', {}).get('active_layer_idx', 0) == self.layer_canvases.index(layer):
                active_canvas = layer.get('canvas', None).content
                break

        if self.active_tool is None:
            return
        
        # Text can be rotated, so we can just grab it and put it in the right spot
        if self.active_tool.shape_type == "text":

            # Align our text to account for size of our layer canvas
            text_shape: cv.Text = self.active_tool.cv_shape
            text_shape.x += self.active_tool.left + 2
            text_shape.y += self.active_tool.top + 2
            
            active_canvas.shapes.append(text_shape)
            
            active_canvas.update()
            await self.save_canvas(canvas=active_canvas)
            self.active_tool.visible = False
            self.active_tool.rotate_handle.visible = False
            self.active_tool.rotate_handle.update()
            self.active_tool.update()
            return
        
        await self.active_tool.canvas.capture()
        shape_capture = await self.active_tool.canvas.get_capture()
        await self.active_tool.canvas.clear_capture()

        shape_img = Image.open(BytesIO(shape_capture)).convert("RGBA")

        angle = self.active_tool.rotate.angle

        # Flet rotate.angle is radians; PIL rotate() takes degrees counterclockwise
        angle_degrees = -math.degrees(angle)
        rotated = shape_img.rotate(angle_degrees, expand=True, resample=Image.Resampling.BICUBIC)

        # Set rotation (with border padding)
        rotation_cx = self.active_tool.left + (self.active_tool.canvas.width + 4) / 2
        rotation_cy = self.active_tool.top + (self.active_tool.canvas.height + 4) / 2


        paste_x = int(rotation_cx - rotated.width / 2)
        paste_y = int(rotation_cy - rotated.height / 2)

        active_layer_idx = self.data.get('canvas_data', {}).get('active_layer_idx', 0)  

        # Decode existing layer capture
        layer_b64 = self.data['canvas_data']['layers'][active_layer_idx].get('capture')
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

        active_canvas.shapes.clear()   
        active_canvas.shapes.append(cv.Image(encoded, 0, 0))
        active_canvas.update()
        await self.save_canvas(canvas=active_canvas) 
            

        # Finally, remove the active tool stuff
        self.active_tool.visible = False
        self.active_tool.rotate_handle.visible = False
        self.active_tool.rotate_handle.update()
        self.active_tool.update()


    # Called when we click the canvas and don't initiate a drag
    async def add_shape(self, e: ft.TapEvent):
        ''' Adds a point to the canvas if we just clicked and didn't initiate a drag '''

        # Set our paint settings in case we need to change them
        paint_settings = app.settings.data.get('paint_settings', {}).copy()

        # Check if we're in tool mode, and what tool we're using
        if app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") != "draw":

            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            match tool_name:

                # Erase tool - make sure our paint settings don't break the drawing
                case "erase":
                    paint_settings['blend_mode'] = "clear"
                    paint_settings['blur_image'] = 0
                    paint_settings['style'] = "stroke"

                # Skip lines, since they are drawn normally
                case "line":
                    pass

                # All other tools/shapes get added here
                case _:

                    if self.manipulating_shape:
                        self.manipulating_shape = False
                        await self.paint_tool_on_canvas()
                        return
    

                    self.manipulating_shape = True
                    self.active_tool = CanvasShape(tool_name, left=e.local_position.x, top=e.local_position.y)
                    self.layer_stack.controls.append(self.active_tool)
                    self.layer_stack.update()
                    self.layer_stack.controls.append(self.active_tool.rotate_handle)
                    self.layer_stack.update()
                    return
                
        self.manipulating_shape = False 

        # If we didn't return, we're either in erase tool or drawing mode
        canvas: cv.Canvas = self.layer_canvases[self.active_layer_idx]
        if not canvas.visible:
            return

        # Create the point using our paint settings and point mode
        point = cv.Points(
            points=[(e.local_position.x, e.local_position.y)],
            paint=ft.Paint(**paint_settings),
        )
        
        # Add point to the canvas and our state data
        canvas.shapes.append(point)

        # After dragging canvas widget, it loses page reference and can't update, so the exception handles that.
        canvas.update()
            
        # Need to save, as this function stands alone and no others will run after it
        await self.save_canvas(e)
        
    # Called when we start drawing on the canvas
    async def start_new_stroke(self, e: ft.DragStartEvent):
        ''' Set our initial starting x and y coordinates for the element we're drawing. '''

        # Grab the canvas and paint settings
        canvas: cv.Canvas = self.layer_canvases[self.active_layer_idx]
        if not canvas.visible:  # Protect when we shouldnt be drawing with it
            return
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
    
        # Update our state x and y coordinates
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

        # Recreate our active path with correct starting positiuon
        self.current_path = cv.Path(elements=[cv.Path.MoveTo(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
        
        # Check if we're in tool mode, and what tool we're using
        if app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") != "draw":

            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            match tool_name:

                # Erase tool - make sure our paint settings don't break the drawing
                case "erase":
                    paint_settings['blend_mode'] = "clear"
                    paint_settings['blur_image'] = 0
                    paint_settings['style'] = "stroke"
                    self.current_path.paint = ft.Paint(**paint_settings) # Make the active path match the paint

                # For line tool - add the first line element to the path
                case "line":
                    line_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
                    self.current_path.elements.append(line_element)

                # Ignore all other tools, as they will control themselves
                case _:
                    return
            
            
        # Add our path to the canvas so we can see it
        canvas.shapes.append(self.current_path)
        canvas.update()
        
    # Called when actively drawing on the canvas
    async def update_stroke(self, e: ft.DragUpdateEvent):
        ''' Determines which drawing tool we're using, and updates accordingly as we drag our mouse '''
        
        # Sampling to improve perforamance. If the line length is too small, we skip it
        dx = e.local_position.x - self.state.x
        dy = e.local_position.y - self.state.y
        if dx * dx + dy * dy < MINIMUM_SEGMENT_DISTANCE * MINIMUM_SEGMENT_DISTANCE:
            return
        
        canvas: cv.Canvas =  self.layer_canvases[self.active_layer_idx]
        if not canvas.visible:  # Protect when we shouldnt be drawing with it
            return
        self.current_path = canvas.shapes[-1] if canvas.shapes else None

        # Catch errors
        if not self.current_path:
            return
                
        # Check if we're in tool mode, and what tool we're using
        if app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") != "draw":

            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            match tool_name:

                # Skip erase tool as it will free stroke
                case "erase":
                    pass

                # For line tool - Update our straight line element to the current mouse position
                case "line":
                    # Set the element and its data
                    line_element = self.current_path.elements[-1]
                    line_dict = line_element.__dict__

                    # Update the elements position
                    line_element.x = e.local_position.x
                    line_element.y = e.local_position.y

                    # Update the dict to match
                    line_dict['x'] = line_element.x
                    line_dict['y'] = line_element.y

                    self.current_path.update()
                    return

                # Ignore all other tools and return out so we don't draw
                case _:
                    return
                

        # Everything else is just drawing, so if we didn't return early we add a new line element to our current path
        
        # Smooth drawing, on by default
        if app.settings.data.get('canvas_settings', {}).get('use_path_smoothing', False): 
            path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
            self.current_path.elements.append(path_element)
            self.current_path.update()

        # Non-smooth drawing
        else: 
            canvas.shapes.append(cv.Line(self.state.x, self.state.y, e.local_position.x, e.local_position.y, paint=self.current_path.paint))
            canvas.update()
            
        # Update our state x and y positions
        self.state.x = e.local_position.x
        self.state.y =  e.local_position.y
        

    # Called when we release the mouse to stop drawing a line
    async def save_canvas(self, e: ft.DragEndEvent=None, canvas: cv.Canvas=None):
        """ Saves our paths to our canvas data for storage """

        # Set our canvas, layer name, and update our shapes count
        canvas: cv.Canvas = self.layer_canvases[self.active_layer_idx]
        if not canvas.visible:  # Protect when we shouldnt be drawing with it
            return
        layer_name = canvas.data

        # Grab the old capture for this layer and add it as an undo task for the canvas
        for layer in self.data.get('canvas_data', {}).get('layers', []):
            if layer.get('name', None) == layer_name:
                if layer.get('capture', None):
                    old_capture = layer.get('capture')
                    self.data['canvas_data']['undo_list'].append({'layer_name': layer_name, 'capture': old_capture})
                    self.data['canvas_data']['redo_list'].clear()     # Clear redo list after new action
        
                    # Make sure undo list is not too long and hog to many resources
                    if len(self.data['canvas_data']['undo_list']) > MAX_UNDO_LIST_TASKS:
                        self.data['canvas_data']['undo_list'].pop(0)
        try:
            # Captures the current state of this canvas
            await canvas.capture()  

            # Get the capture and encode it so we can store it where we need to
            capture = await canvas.get_capture()
            encoded_capture = base64.b64encode(capture).decode('utf-8')      # Requires encoding to save json

            # If capture failed, return
            if not encoded_capture:
                await canvas.clear_capture()
                return

            # With this:
            for layer in self.data['canvas_data']['layers']:
                if layer.get('name') == layer_name:
                    layer['capture'] = encoded_capture
                    break
            self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})   # Update our data with the new capture  
                
            await canvas.clear_capture()

            

            # Check if we have too many shapes on the canvas. If we do, capture them and put it in an image
            if len(canvas.shapes) > MAX_SHAPES_BEFORE_CAPTURE:   
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, self.canvas_width, self.canvas_height))  
                canvas.update()

            # Always re-render end of erase strokes, or they will appear broken. TEMPORARY FIX
            elif app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") == "tool" and app.settings.data.get('canvas_settings', {}).get('current_tool_name', "") == "erase":   
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, self.canvas_width, self.canvas_height))
                canvas.update()

            # Always re-render end of non-none blend mode strokes, or they will appear broken. TEMPORARY FIX
            elif app.settings.data.get('paint_settings', {}).get('blend_mode', "") is not None: 
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, self.canvas_width, self.canvas_height))
                canvas.update()

            
        except Exception as e:
            print("failed to save canvas", e)

    # Redraws the canvas upon size changing. Not used currently
    async def _redraw_canvas(self, e=ft.PointerEvent):
        if self.story.workspace.is_resizing:    # If we're resizing just ignore this call
            self.needs_redraw = True
            return
        
        # Skip unneccesary redraw on first launch since it fixes itself
        if self.skip_first_resize:
            self.skip_first_resize = False
            self.needs_redraw = False
            return
        
        # If we're not resizing but don't need to redraw, set our coords
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y

        
        # If we need to redraw, do that
        if self.needs_redraw:
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)   

            for ctrl in self.layer_stack.controls:
                if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas):
                    
                    # If any changes had been made, clear the shapes on screen and set the most recent capture
                    if len(ctrl.content.shapes) > 1:   
                        for layer in self.data.get('canvas_data', {}).get('layers', []):
                            if layer.get('name', None) == ctrl.data:
                                capture = layer.get('capture', None)
                                if capture:
                                    ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                                    ctrl.content.shapes.append(cv.Image(capture, 0, 0, self.canvas_width, self.canvas_height))   # Re-add most reccent capture
                                    continue        

                    # Run logic here to resize the canvas capture
                    ctrl.content.shapes[0].width = self.canvas_width
                    ctrl.content.shapes[0].height = self.canvas_height

            self.layer_stack.update()
            self.story.blocker.visible = False
            self.story.blocker.update()
            self.needs_redraw = False

    class InformationDisplay(ft.Column):

        # Constructor.
        def __init__(
            self, 
            widget: 'Canvas',                  
            data: dict = None               
        ):

            # Parent constructor
            super().__init__(data=data) 
            self.widget = widget

            # Reloads the information display of the canvas

        
            

        async def _set_layer_content(self, e: ft.Event):

            await self.widget.story.close_menu()

            layer_name, type = e.control.data

            # Grab the layer this is. Set its capture as color or image

            # Set a color as the background
            if type == "color":

                async def _color_change(e):     # Set the color to the picked one
                    color_picker.color = e.data

                async def _set_color_confirmed(e=None):

                    for layer in self.widget.data.get('layers', []):
                        if layer.get('name') == layer_name:
                            for ctrl in self.widget.layer_stack.controls:
                                if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas) and ctrl.data == layer_name:
                                    ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                                    ctrl.content.shapes.append(cv.Color(color_picker.color))   # Re-add empty images so it can capture
                                    ctrl.content.update()
                                    await self.widget.save_canvas(canvas=ctrl.content)  
                                    break
                            break

                    self.page.pop_dialog()
                    

                color_picker = ColorPicker(
                    self.widget.data.get('background', ft.Colors.PRIMARY) if self.widget.data.get('bg_type') == "color" else ft.Colors.PRIMARY,
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
                            print("Opened file")
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                            for layer in self.widget.data.get('layers', []):
                                if layer.get('name') == layer_name:
                                    print("Found layer: ", layer_name)
                                    for ctrl in self.widget.layer_stack.controls:
                                        if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas) and ctrl.data == layer_name:
                                            print("Set image")
                                            ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                                            ctrl.content.shapes.append(cv.Image(f"{encoded_string}", 0, 0, self.widget.canvas_width, self.widget.canvas_height))   # Re-add empty images so it can capture
                                            ctrl.content.update()
                                            await self.widget.save_canvas(canvas=ctrl.content)
                                            break
                                    break
                        self.page.pop_dialog()

                    except Exception as _:
                        pass   

        async def _set_layer_blur(self, e: ft.Event):
            await self.widget.story.close_menu()

            layer_name = e.control.data
            #capture = None
            for layer in self.widget.data.get('layers', []):
                if layer.get('name') == layer_name:
                    if layer.get('capture', "") == "":
                        
                        self.page.show_dialog(SnackBar("Layer must have existing content to set blur"))
                        return
                    capture = layer.get('capture', "")
                    break

            if capture is None:
                self.page.show_dialog(SnackBar("Error finding layer capture for blur"))
                return
            
            # Updates the visual canvas with new blur amount
            async def _blur_amount_changed(e):
                blur_amount = e.control.value
                active_preview_image.paint.blur_image = blur_amount
                active_preview_image.update()

            # Apply that level of blur to the layer
            async def _apply_blur(e=None):

                for layer in self.widget.data.get('layers', []):
                    if layer.get('name') == layer_name:
                        for ctrl in self.widget.layer_stack.controls:
                            if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas) and ctrl.data == layer_name:
                                ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                                ctrl.content.shapes.append(cv.Image(capture, 0, 0, self.widget.canvas_width, self.widget.canvas_height, paint=ft.Paint(blur_image=blur_strength_slider.value)))
                                ctrl.content.update()
                                await self.widget.save_canvas(canvas=ctrl.content)  
                                break
                        break

                self.page.pop_dialog()
            
            blur_strength_slider = ft.Slider(1, "{value}", min=0, max=50, on_change=_blur_amount_changed)
            
            
            preview_canvas = ft.Container(
                cv.Canvas(
                    #shapes=[preview_image], 
                    shapes=[],
                    
                    expand=True,
                    width=self.widget.canvas_width / 2, height=self.widget.canvas_height / 2
                ),
                image=ft.DecorationImage("dark_mode_transparent_background.jpg", fit=ft.BoxFit.FILL) 
            )

            active_preview_image = None

            # Add the entire canvas to the preview, but mark the active layer we will change blur of
            for layer in self.widget.data.get('layers', []):
                if layer.get('name') == layer_name:
                    active_preview_image = cv.Image(layer.get('capture', ""), 0, 0, self.widget.canvas_width / 2, self.widget.canvas_height / 2, paint=ft.Paint(blur_image=1))
                    preview_canvas.content.shapes.append(active_preview_image)
                    continue
                preview_canvas.content.shapes.append(cv.Image(layer.get('capture', ""), 0, 0, self.widget.canvas_width / 2, self.widget.canvas_height / 2))
                
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
                    ft.TextButton("Apply", on_click=_apply_blur, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)),
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
        for layer in self.layer_canvases:

            # Grab container to check if actually visible. Not visible, not exporting
            container = layer.get('canvas', None)
            if not container.visible:   
                continue

            # Grab canvas our canvas for that layer
            canvas: cv.Canvas = self.layer_canvases[self.active_layer_idx]

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
        

        # Add new layer to the stack of canvas controls and sidebar list tiles
        new_canvas_ctrl = self.create_new_layer_canvas_ctrl(len(self.layer_canvases), self.data.get('canvas_data', {}).get('layers', [])[-1])
        self.layer_canvases.append(new_canvas_ctrl)
        self.layer_stack.controls.insert(len(self.layer_stack.controls) - 1, new_canvas_ctrl)
        self.sidebar_layers_list_view.controls.append(self.create_new_layer_sidebar_ctrl(len(self.sidebar_layers_list_view.controls), self.data.get('canvas_data', {}).get('layers', [])[-1]))

        # Set the active index to the newly created layer
        self.active_layer_idx = len(self.layer_canvases) - 1
        self.data['canvas_data']['active_layer_idx'] = self.active_layer_idx
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
        self.layer_stack.update()
        self.update()
        
    # Cretes a new layer canvas control for the stack
    def create_new_layer_canvas_ctrl(self, idx: int, canvas_data: dict):
        visible = canvas_data.get('visible', True)
        capture = canvas_data.get('capture', None)
        name = canvas_data.get('name', f"Layer {idx}")

        return cv.Canvas(
            data=name,        # Save the index of this layer so we know where to save it in our data
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

            for task in self.data.get('canvas_data', {}).get('undo_list', [])[:]:   # Update any undo tasks related to this layer
                if task.get('layer_name') == layer_name:
                    self.data['canvas_data']['undo_list'].remove(task)
            for task in self.data.get('canvas_data', {}).get('redo_list', [])[:]:   # Update any redo tasks related to this layer
                if task.get('layer_name') == layer_name:
                    self.data['canvas_data']['redo_list'].remove(task)

            # Remove the canvas and sidebar entry for this layer
            self.layer_canvases.pop(layer_idx)
            self.layer_stack.controls.pop(layer_idx + 1)    # Skip background container
            self.sidebar_layers_list_view.controls.pop(layer_idx)

            # Clamp active_layer_idx to valid range and sync to data
            if self.active_layer_idx >= len(self.layer_canvases):
                self.active_layer_idx = len(self.layer_canvases) - 1
            self.data['canvas_data']['active_layer_idx'] = self.active_layer_idx

            self.layer_stack.update()
            self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
            self.update()
            await self.update_indices()
            
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
                            ft.MenuItemButton(
                                "Set Color", leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                                #on_click=self._set_layer_content, 
                                tooltip="Set this layer to a solid color. This will overwrite any drawings on the layer currently." if visible else
                                "Layer must be visible to set color",
                                data=(name, "color"), focus_on_hover=False,
                                disabled=not visible,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            
                            ft.MenuItemButton(
                                "Set Image", leading=ft.Icon(ft.Icons.IMAGE_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)), 
                                #on_click=self._set_layer_content, 
                                tooltip="Upload an image for this layer. This will overwrite any drawings on the layer currently." if visible else
                                "Layer must be visible to set image", 
                                data=(name, "image"),
                                disabled=not visible, focus_on_hover=False,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            ft.MenuItemButton(
                                "Set Blur", leading=ft.Icon(ft.Icons.BLUR_ON_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)), 
                                #on_click=self._set_layer_blur, 
                                tooltip="Set the blur only for existing content on this layer. Useful for backgrounds and effects. " \
                                "Will NOT effect any future content drawn on this layer" if visible else
                                "Layer must be visible to set image", 
                                data=name, focus_on_hover=False,
                                disabled=not visible,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            
                            ft.MenuItemButton(
                                "Rename", leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                                focus_on_hover=False,
                                on_click=rename_layer_clicked, 
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            ),
                            
                            ft.MenuItemButton(
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

        # Deselcted old list tile:
        for ctrl in self.sidebar_layers_list_view.controls:
            ctrl.content.bgcolor = None

        # Update our new index live and in data
        new_layer_idx = e.control.data
        self.active_layer_idx = new_layer_idx
        self.data['canvas_data']['active_layer_idx'] = self.active_layer_idx
        
        # If not visible, set the list tile as visible and the canvas as well
        canvas = self.layer_canvases[self.active_layer_idx]
        if not canvas.visible:
            canvas.visible = True   # Update canvas
            self.data.get('canvas_data', {}).get('layers', [])[self.active_layer_idx]['visible'] = True # update data
            e.control.leading.icon = ft.Icons.VISIBILITY
            

        # Apply data updates
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})

        # Update sidebar list tile background to reflect
        e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH
        await self.set_mouse_cursor(False)
        self.update()

    async def toggle_layer_visibility(self, e: ft.Event):
        layer_idx = e.control.parent.data

        new_visibility = not self.layer_canvases[layer_idx].visible

        # Update canvas visibility
        self.layer_canvases[layer_idx].visible = new_visibility
        self.data.get('canvas_data', {}).get('layers', [])[layer_idx]['visible'] = new_visibility

        # Update the icon in the sidebar list tile
        e.control.icon = ft.Icons.VISIBILITY if new_visibility else ft.Icons.VISIBILITY_OFF
        e.control.parent.bgcolor = None

        # If we are still active layer while being turned back visible, reflect that in sidebar
        if new_visibility and layer_idx == self.active_layer_idx:
            e.control.parent.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH

        # Set mouse cursor
        await self.set_mouse_cursor()

        # Apply data updates
        self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
        self.update()

    # Update all our controls data that use indices to mainstain state. Only sidebar needs them
    async def update_indices(self):
        for idx, control in enumerate(self.sidebar_layers_list_view.controls):
            control.content.data = idx
    
    def build(self):
        super().build()

    # Called when we need to rebuild out plotline UI
    def reload_widget(self):       
        ''' Rebuilds/reloads our Canvas '''

        # Called when undoing a stroke on the canvas
        async def undo_stroke(e: ft.Event=None):

            # If there's nothing to undo, return early
            if len(self.data.get('canvas_data', {}).get('undo_list', [])) == 0:
                return
            active_canvas: cv.Canvas = self.layer_canvases[self.active_layer_idx]
            if not active_canvas.visible:  # Protect when we shouldnt be drawing with it
                return
                    
            # Grab the task we're going to carry out and its name and capture
            #task = self.widget.state.undo_list.pop()    
            task = self.data.get('canvas_data', {}).get('undo_list', []).pop()
            layer_name = task.get('layer_name', None)
            capture = task.get('capture', None)

            # Set data back to old capture state
            for layer in self.data.get('canvas_data', {}).get('layers', []):
                if layer.get('name', None) == layer_name:
                    previous_capture = layer.get('capture', None)   # Grab current capture of the layer and add it to the redo list
                    self.data.get('canvas_data', {}).get('redo_list', []).append({'layer_name': layer_name, 'capture': previous_capture})
                    layer['capture'] = capture     
                    # Update data
                    self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
                    if redo_button.disabled:
                        redo_button.disabled = False
                        redo_button.update()
                    break

            # Update the UI
            
            active_canvas.shapes.clear()
            active_canvas.shapes.append(cv.Image(capture, 0, 0, self.canvas_width, self.canvas_width))
            active_canvas.update()

        # Called when redoing a stroke on the canvas after a previous undo
        async def redo_stroke(e: ft.Event=None):
            # Return early if nothing to redo
            if len(self.data.get('canvas_data', {}).get('redo_list', [])) == 0:
                return
            active_canvas: cv.Canvas = self.layer_canvases[self.active_layer_idx]
            if not active_canvas.visible:  # Protect when we shouldnt be drawing with it
                return
            
            # Most recent task we want to redo
            task = self.data.get('canvas_data', {}).get('redo_list', []).pop() 
            layer_name = task.get('layer_name', None)
            capture = task.get('capture', None)

            # Set data back to old capture state
            for layer in self.data.get('canvas_data', {}).get('layers', []):
                if layer.get('name', None) == layer_name:
                    previous_capture = layer.get('capture', None)   # Grab current capture of the layer and add it to undo list
                    self.data.get('canvas_data', {}).get('undo_list', []).append({'layer_name': layer_name, 'capture': previous_capture})
                    layer['capture'] = capture     # Set the capture of the layer to the one from our undo task
                    self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})
                    if undo_button.disabled:
                        undo_button.disabled = False
                        undo_button.update()
                    break

            # Update UI
            active_canvas.shapes.clear()
            active_canvas.shapes.append(cv.Image(capture, 0, 0, self.canvas_width, self.canvas_width))
            active_canvas.update()

        # Reorder layers
        async def reorder_layers(e: ft.OnReorderEvent):
            # Grab the active layer name before we move
            active_layer_name = self.data.get('canvas_data', {}).get('layers', [])[self.active_layer_idx].get('name', None)

            self.data.get('canvas_data', {}).get('layers', []).insert(e.new_index, self.data.get('canvas_data', {}).get('layers', []).pop(e.old_index))
            self.layer_canvases.insert(e.new_index, self.layer_canvases.pop(e.old_index))
            # Reorder in layer_stack too (offset by 1 for the background container)
            self.layer_stack.controls.insert(e.new_index + 1, self.layer_stack.controls.pop(e.old_index + 1))
            self.sidebar_layers_list_view.controls.insert(e.new_index, self.sidebar_layers_list_view.controls.pop(e.old_index))

            # Find the active layer's new index and sync both self and data
            for i, ctrl in enumerate(self.sidebar_layers_list_view.controls):
                if ctrl.data == active_layer_name:
                    self.active_layer_idx = i
                    break
            self.data['canvas_data']['active_layer_idx'] = self.active_layer_idx
            self.update_data(**{'canvas_data': self.data.get('canvas_data', {})})

            self.layer_stack.update()
            self.update()
            await self.update_indices()  # Update indices so sidebar controls maintain correct idx reference
            

        
            

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

                
        

        # Add our layers to the stack in order
        for idx, canvas_data in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            self.layer_canvases.append(self.create_new_layer_canvas_ctrl(idx, canvas_data))

        

        self.layer_stack = ft.Stack(
            [
                ft.Container(   # Transparent Background
                    ignore_interactions=True,
                    image=ft.DecorationImage("dark_mode_transparent_background.jpg", fit=ft.BoxFit.FILL),
                    #border=ft.Border.all(2, ft.Colors.RED),
                    width=self.canvas_width,
                    height=self.canvas_height,
                    expand=False
                ),      
            ] + self.layer_canvases,  
            alignment=ft.Alignment.CENTER, expand=False
        ) 

        self.canvas_controller = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.PRECISE,
            on_pan_start=self.start_new_stroke,         # Starts a new brush stroke with current paint settings
            on_pan_update=self.update_stroke,           # Updates the current stroke based on mouse movement
            on_pan_end=self.save_canvas,                # Saves the now complete stroke to our data and canvas capture
            on_tap_up=self.add_shape,                   # Handles adding dots and tools
            width=self.canvas_width,
            height=self.canvas_height
        )

        
        # Controller
        self.layer_stack.controls.append(self.canvas_controller)

        layers_container = ft.Container(
            border=ft.Border.all(2, ft.Colors.OUTLINE),
            content=self.layer_stack, expand=False,
            opacity=0.99,    # Forces canvas onto its own opacity layer for rendering to avoid blend mode bugs
            #on_size_change=self._set_size_old       # Set the size of the canvases needed for recapturing
        )

        
        

        # Holds our drawing so we can interact with it, zoom, pan, etc.
        interactive_viewer = ft.InteractiveViewer(
            content=layers_container,
            expand=3, 
            constrained=False,
            scale_factor=500, boundary_margin=200,
            min_scale=0.02, max_scale=3.0,
        )

        self.sidebar_header.controls.insert(
            1, 
            undo_button := ft.IconButton(
                ft.Icons.UNDO, self.data.get('color', None), tooltip="Undo", mouse_cursor=ft.MouseCursor.CLICK, 
                on_click=undo_stroke, disabled=len(self.data.get('canvas_data', {}).get('undo_list', [])) == 0
            )
        )
        self.sidebar_header.controls.insert(
            2, 
            redo_button := ft.IconButton(
                ft.Icons.REDO_OUTLINED, self.data.get('color', None), tooltip="Redo", mouse_cursor=ft.MouseCursor.CLICK, 
                on_click=redo_stroke, disabled=len(self.data.get('canvas_data', {}).get('redo_list', [])) == 0
            )
        )

        
        self.sidebar_layers_list_view = ft.ReorderableListView(
            [], 
            on_reorder=reorder_layers, 
            scroll="auto", 
            expand=True, #show_default_drag_handles=False
        )   # This will hold our layers and allow us to reorder them


        # Add each layer to the expansion tile
        for idx, layer_data in enumerate(self.data.get('canvas_data', {}).get('layers', [])):
            self.sidebar_layers_list_view.controls.append(self.create_new_layer_sidebar_ctrl(idx, layer_data))

             

        self.sidebar_body.controls.append(
            ft.Column([
                self.description_tf,
                
                ft.Row([    # Layer Label
                    ft.Text(f"\tLayers", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)), 
                    ft.IconButton(      # Create new Layer button
                        ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        self.data.get('color', ft.Colors.PRIMARY),
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_click=self.create_new_layer,
                    )
                ], spacing=0),
                

                self.sidebar_layers_list_view,

                #ft.Row([    # Label dataset
                    #ft.Text(f"\tNotes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)), 
                    #ft.IconButton(      # Create new notes button
                        #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        #self.data.get('color', ft.Colors.PRIMARY),
                        #mouse_cursor=ft.MouseCursor.CLICK,
                    #)
                #], spacing=0),

                #ft.Container(notes_column, margin=ft.Margin.symmetric(horizontal=20)),
            ], scroll=ft.ScrollMode.AUTO)
        )

        self.body_container.content = ft.Row([interactive_viewer, self.show_sidebar_button, self.sidebar], expand=True, spacing=0)

        self._render_widget()

        self.page.run_task(self.set_mouse_cursor)