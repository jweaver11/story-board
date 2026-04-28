'''
The canvas class for all canvases inside our story
Canvases are drawings and images
'''

from flet_color_pickers import ColorPicker
import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from styles.snack_bar import SnackBar
from models.dataclasses.canvas_state import State
import flet.canvas as cv
import math
from models.app import app
from models.mini_widgets.canvas_info import CanvasInformationDisplay
import json
import base64
from io import BytesIO
from PIL import Image
import asyncio
from styles.menu_option_style import MenuOptionStyle

MAX_SHAPES_BEFORE_CAPTURE = 30   # Prevent lag from too many paths on the canvas without being removed
MAX_UNDO_LIST_TASKS = 30         # Max number of undo tasks to store in our undo list before we start deleting old ones


class Canvas(Widget):
    def __init__(
        self, 
        title: str, 
        page: ft.Page, 
        directory_path: str, 
        story: Story, 
        data: dict = None,
        is_rebuilt: bool = False
    ):
        
        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True
        elif data.get('tag') is None:
            is_new = True
        
        # Parent constructor
        super().__init__(
            title=title,           
            page=page,                         
            directory_path=directory_path, 
            story=story,
            data=data,  
            is_rebuilt = is_rebuilt
        ) 


        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,
            {
                # Widget data
                "tag": "canvas",
                'color': app.settings.data.get('default_canvas_color'),
                'show_info': True,   # Whether to show the info column on the side of our charts or not.

                # Info display and general canvas data
                'canvas_data': {},       

                'capture': str,             # Capture of what we currently look like
                'snapshot': str,            # Most recent completed snapshot of our canvas used by other widgets

                
            },
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)

        

        # State tracking for canvas drawing info
        self.state = State()                # Used for tracking our coords and current drawing data for the active stroke/shape being applied
        self.canvas_width = 0
        self.canvas_height = 0
        self.min_segment_dist = 2           # Sampling size
        self.needs_redraw = False           # Used to track if we need to redraw canvas after a resize
        self.skip_first_resize = True       # Skip the first resize since it will fix itself
        self.initial_resize = True          # Initial resize to track our canvases size without rebuild

        
        self.layers = [{}]                  # List of our layers, which are each their own canvas
        self.layer_stack: ft.Stack          # Stack to hold our layers on top of each other

        self.bg_image: ft.DecorationImage   # Hold our background image
        
        # The active stroke we are adding to the canvas when drawing so we know how to update it
        self.active_path = cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))

        self.active_tool: cv.Shape                     # The active shape being added if we're using a tool
        self.tool_controller: ft.GestureDetector       # The overlayed controller to modify shapes so we can resize, rotate, transform, etc

        # We render our own mini widgets (comments), so we don't need parent class to render them as well
        self.no_render_mini_widgets = True  

        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init


    def _load_layers(self):
        self.layers.clear()
        
        for idx, layer in enumerate(self.data.get('canvas_data', {}).get('Layers', [])):

            name = layer.get('name', f"Layer {idx + 1}")
            visible = layer.get('visible', True)
            capture = layer.get('capture', None)

            new_layer = ft.Container(
                cv.Canvas(
                    data=name,        # Save the index of this layer so we know where to save it in our data
                    content=ft.GestureDetector(
                        mouse_cursor=ft.MouseCursor.PRECISE,
                        on_pan_start=self.start_new_stroke,         # Starts a new brush stroke with current paint settings
                        on_pan_update=self.update_stroke,           # Updates the current stroke based on mouse movement
                        on_pan_end=self.save_canvas,                # Saves the now complete stroke to our data and canvas capture
                        on_tap_up=self.add_shape,                   # Handles adding dots and tools
                        on_secondary_tap=lambda _: self.story.open_menu(self._get_menu_options()),
                        on_hover=self._redraw_canvas,       # Redraws canvas if it needs it from resizing, otherwise just sets coords
                        hover_interval=20,
                        drag_interval=10,                   
                        expand=True,
                    ),
                    expand=True, 
                    shapes=[
                        cv.Image(       # Sets the background image of the layer to its most recent capture
                            capture, 0, 0, 
                            self.canvas_width if self.canvas_width != 0 else None,          # Ignore setting size before we know it
                            self.canvas_height if self.canvas_height != 0 else None 
                        )    
                    ],
                    on_resize=self._set_size if idx == 0 else None,  # Only one layer (background) needs to set size to avoid redundency
                ),
                expand=True, data=name,
                visible=visible,    # Set visibility

                # Only active layer can draw
                ignore_interactions=True if self.data.get('canvas_data', {}).get('Active Layer', 0) != idx else False,   
            )
            
            self.layers.append({'name': name, 'visible': visible, 'canvas': new_layer})


    async def _set_size(self, e: cv.CanvasResizeEvent):
        if e: 
            self.canvas_width = int(e.width)
            self.canvas_height = int(e.height)
            #self.needs_redraw = True           # Prevent resizing for now
            if self.initial_resize:
                self.initial_resize = False
                self.needs_redraw = False

                # Handles switching to tab of canvas upon first launch
                try:
                    for layer in self.layers:
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

    # Called in the constructor
    def _create_information_display(self) -> CanvasInformationDisplay:
        ''' Creates our plotline information display mini widget '''
        
        return CanvasInformationDisplay(
            title=self.title,
            widget=self,
            page=self.p,
            key="canvas_data",     
            data=self.data.get('canvas_data'),      
        )
        

    def _get_menu_options(self):
        ''' Gets the menu options for when we right click on the canvas '''

        options = [
            MenuOptionStyle(
                on_click=self._toggle_show_info,
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, self.data.get('color', 'primary'),),
                    ft.Text(
                        "Show Info", 
                        weight=ft.FontWeight.BOLD, 
                        
                    ), 
                ]),
            ),
        ]

        options.extend(super()._get_menu_options())     # Get the default menu options for widgets and add them to our information display options
        return options
    
    async def _deselect_shape(self, e=None):
        ''' Deselects the active shape and re-sets our controls'''
        


    # Called when we click the canvas and don't initiate a drag
    async def add_shape(self, e: ft.TapEvent):
        ''' Adds a point to the canvas if we just clicked and didn't initiate a drag '''

        # TODO PS
        # Clicking decifers if drawing or adding a tool
        # if drawing: add point.
        # else: add tool
        # Adds a 200x200 shape of selected tool stacked under the controller, and sets it as the active shape to be modified

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
                    # Add the tool here
                    return

        # If we didn't return, we're either in erase tool or drawing mode
        canvas: cv.Canvas = e.control.parent    # Set the canvas

        # Create the point using our paint settings and point mode
        point = cv.Points(
            points=[(e.local_position.x, e.local_position.y)],
            paint=ft.Paint(**paint_settings),
        )
        
        # Add point to the canvas and our state data
        canvas.shapes.append(point)

        # After dragging canvas widget, it loses page reference and can't update, so the exception handles that.
        try:
            canvas.update()
        except Exception:
            print("Failed to update canvas")
            
        # Need to save, as this function stands alone and no others will run after it
        await self.save_canvas(e)
        
    # Called when we start drawing on the canvas
    async def start_new_stroke(self, e: ft.DragStartEvent):
        ''' Set our initial starting x and y coordinates for the element we're drawing. '''

        # Grab the canvas and paint settings
        canvas: cv.Canvas = e.control.parent
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
    
        # Update our state x and y coordinates
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

        # Recreate our active path with correct starting positiuon
        self.active_path = cv.Path(elements=[cv.Path.MoveTo(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
        
        # Check if we're in tool mode, and what tool we're using
        if app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") != "draw":

            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            match tool_name:

                # Erase tool - make sure our paint settings don't break the drawing
                case "erase":
                    paint_settings['blend_mode'] = "clear"
                    paint_settings['blur_image'] = 0
                    paint_settings['style'] = "stroke"
                    self.active_path.paint = ft.Paint(**paint_settings) # Make the active path match the paint

                # For line tool - add the first line element to the path
                case "line":
                    line_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
                    self.active_path.elements.append(line_element)

                # Ignore all other tools, as they will control themselves
                case _:
                    return
                
        else:
            

            

            # Grab our style so we can compare it
            '''OLD
            style = str(app.settings.data.get('paint_settings', {}).get('style', 'stroke'))
            match style: 
                # If we're using lineto (straight lines), add that element to the current path and state right away
                case "lineto":
                    line_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
                    self.active_path.elements.append(line_element)

                case "arc":
                    
                    arc_element = cv.Path.Arc(
                        width=20,
                        height=20,
                        
                        x=e.local_position.x,
                        y=e.local_position.y,
                        start_angle=math.pi,
                        sweep_angle=-math.pi,
                    )
                    self.active_path.elements.append(arc_element)

            # Else if we're using arcto, add that element to the current path and state right away
                case 'arcto' | 'arctofill':
                    arc_element = cv.Path.ArcTo(
                        radius=12,
                        rotation=0,
                        large_arc=False,
                        x=e.local_position.x,
                        y=e.local_position.y,
                        clockwise=True,
                    )
                    self.active_path.elements.append(arc_element)

                #case ''
            '''

            #cv.Path.CubicTo()
            #cv.Path.QuadraticTo()
            #cv.Path.Oval()
            #cv.Path.Rect()
            #cv.Path.

        # Add our path to the canvas so we can see it
        canvas.shapes.append(self.active_path)
        canvas.update()
        
    # Called when actively drawing on the canvas
    async def update_stroke(self, e: ft.DragUpdateEvent):
        ''' Determines which drawing tool we're using, and updates accordingly as we drag our mouse '''

        #TODO: Add check here to reduce num of lines based on previous start and end??

        # Sampling to improve perforamance. If the line length is too small, we skip it
        dx = e.local_position.x - self.state.x
        dy = e.local_position.y - self.state.y
        if dx * dx + dy * dy < self.min_segment_dist * self.min_segment_dist:
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
                    line_element = self.active_path.elements[-1]
                    line_dict = line_element.__dict__

                    # Update the elements position
                    line_element.x = e.local_position.x
                    line_element.y = e.local_position.y

                    # Update the dict to match
                    line_dict['x'] = line_element.x
                    line_dict['y'] = line_element.y

                    self.active_path.update()
                    return

                # Ignore all other tools and return out so we don't draw
                case _:
                    return
                
        # Everything else is just drawing, so if we didn't return early we add a new line element to our current path
        path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
        self.active_path.elements.append(path_element)
        self.active_path.update()
            
        # Update our state x and y positions
        self.state.x = e.local_position.x
        self.state.y =  e.local_position.y

        # Set our canvas and style
        #style = str(app.settings.data.get('paint_settings', {}).get('style', 'stroke'))
        '''
        OLD

            case "arc" | "arcfill":
            
                # Set the element and its data
                arc_element = self.active_path.elements[-1]
                arc_dict = arc_element.__dict__

                # Swap directions of arc depending if we drag up or down from starting point
                if e.local_position.y - self.state.y >= 0:   # Dragging down
                    arc_element.sweep_angle = -math.pi
                    arc_element.height = abs(self.state.y - e.local_position.y)
                    arc_element.y = self.state.y - (arc_element.height / 2)
                    
                else:       # Dragging up
                    arc_element.sweep_angle = math.pi
                    arc_element.height = abs(e.local_position.y - self.state.y)
                    arc_element.y = abs(self.state.y - (arc_element.height / 2))

                if e.local_position.x - self.state.x < 0:   # Dragging left, move X position of arc to match
                    arc_element.x = e.local_position.x

                arc_element.width = abs(e.local_position.x - self.state.x) 

                self.active_path.update()
                return
        
            # Handle arcs
            case 'arcto' | 'arctofill':
            
                arc_element = self.active_path.elements[-1]
                arc_dict = arc_element.__dict__

                arc_element.x = e.local_position.x
                arc_element.y = e.local_position.y

                arc_dict['x'] = arc_element.x
                arc_dict['y'] = arc_element.y

                self.active_path.update()
                return
        
        
            # If its not one of our custom styles, use free-draw stroke, which is constantly adding line_to segements
            case _:
        
        '''
        

    # Called when we release the mouse to stop drawing a line
    async def save_canvas(self, e: ft.DragEndEvent):
        """ Saves our paths to our canvas data for storage """

        # Set our canvas, layer name, and update our shapes count
        canvas: cv.Canvas = e.control.parent
        layer_name = canvas.data

        # Grab the old capture for this layer and add it as an undo task for the canvas
        for layer in self.data.get('canvas_data', {}).get('Layers', []):
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

            # Save the capture, to whatever layer we're drawing on
            self.data['canvas_data']['Layers'][self.data.get('canvas_data', {}).get('Active Layer', 0)]['capture'] = encoded_capture
            await self.save_dict()     
                
            await canvas.clear_capture()

            # Check if we have too many shapes on the canvas. If we do, capture them and put it in an image
            if len(canvas.shapes) > MAX_SHAPES_BEFORE_CAPTURE:   
                print("Capturing canvas to prevent lag")
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

        return  # Temp before resizing is handled
        
        # If we need to redraw, do that
        if self.needs_redraw:
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)   

            for ctrl in self.layer_stack.controls:
                if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas):
                    
                    # If any changes had been made, clear the shapes on screen and set the most recent capture
                    if len(ctrl.content.shapes) > 1:   
                        for layer in self.data.get('canvas_data', {}).get('Layers', []):
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


    # Called when we click to export a canvas
    async def export_canvas_clicked(self, e=None):
        """ Exports canvas to correct file type based on selection with optional upscaling """

        # Convert colors for color background to rgba format
        def hex_to_rgba(hex_color: str):
            hex_color = hex_color.lstrip("#")

            if len(hex_color) == 8:  # AARRGGBB
                a = int(hex_color[0:2], 16)
                r = int(hex_color[2:4], 16)
                g = int(hex_color[4:6], 16)
                b = int(hex_color[6:8], 16)
                return (r, g, b, a)

            if len(hex_color) == 6:  # RRGGBB
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b, 255)

            raise ValueError("Invalid hex color format")

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
            
            # Determine our background type and create an image for it
            bg_type = self.data.get('canvas_data', {}).get('bg_type', None)

            match bg_type:
                case "color":       # Color backgrounds
                    hex_color = self.data.get('canvas_data', {}).get('background', "#00000000")
                    rgba_color = hex_to_rgba(hex_color) 
                    merged = Image.new("RGBA", (width, height), rgba_color)
                case "image":       # Images
                    bg_image_data = self.data.get('canvas_data', {}).get('background', None)
                    merged = Image.open(BytesIO(base64.b64decode(bg_image_data))).convert("RGBA")
                    merged = merged.resize((width, height))
                case _:     # All others are just invisible
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

        # Expected size the user wants the canvas to be exported at, which they set upon creation
        target_width = self.data.get('canvas_data', {}).get('width', None)
        target_height = self.data.get('canvas_data', {}).get('height', None)
        pixel_ratio = None  # Scale the capture up or down based on expected exported size

        # Check the current width
        current_width = self.canvas_width
        current_height = self.canvas_height

        
        if target_width is None or target_height is None:
            pass

        # If target size != current size, upscale or downscale the capture
        elif target_width != current_width or target_height != current_height:
            width_ratio = target_width / current_width
            height_ratio = target_height / current_height
            pixel_ratio = min(width_ratio, height_ratio)  # Use the smaller ratio to maintain aspect ratio

        # Go through our layers now
        for layer in self.layers:

            # Grab container to check if actually visible. Not visible, not exporting
            container = layer.get('canvas', None)
            if not container.visible:   
                continue

            # Grab canvas our canvas for that layer
            canvas: cv.Canvas = layer.get('canvas', None).content

            # Capture and add that capture to the list
            if canvas is not None:
                await canvas.capture(pixel_ratio)       # Upscale/downscale the capture based on size
                cc = await canvas.get_capture()
                captures_list.append(cc)         # Add the capture to the list
                await canvas.clear_capture()     # Clear the capture to prevent bugs

        # Our exportable image bytes from merging all our layers captures together with any scaling needed
        merged_bytes = _merge_captures(captures_list, target_width, target_height)

        # Open file dialog to save that capture
        if merged_bytes:
            await ft.FilePicker().save_file(
                src_bytes=merged_bytes, file_name=f"{self.title}.png", 
                file_type=ft.FilePickerFileType.IMAGE, allowed_extensions=["png"]
            )

    
        

    # Called when we need to rebuild out plotline UI
    def reload_widget(self):       
        ''' Rebuilds/reloads our Canvas '''

        self._load_layers()

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        self.layer_stack = ft.Stack([
            ft.Container(   # Make sure we're expanded
                expand=True, ignore_interactions=True,
                bgcolor=self.data.get('canvas_data', {}).get('background', None) if self.data.get('canvas_data', {}).get('bg_type') == "color" else None,
                image=ft.DecorationImage(
                    self.data.get('canvas_data', {}).get('background', None), fit=ft.BoxFit.FILL
                ) if self.data.get('canvas_data', {}).get('bg_type') == "image" else None,
            ),      
        ],  expand=False, alignment=ft.Alignment(0, 0))   # Stack so we can have a background that doesn't get captured, and an interactive viewer to zoom and pan without affecting our coordinates

        # Add our layers to the stack in order
        for layer in self.layers:
            self.layer_stack.controls.append(layer.get('canvas', ft.Container(ft.Text("Failed to grab layer"))))
            #print("Added canvas")

        layers_container = ft.Container(
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.Border.all(1, ft.Colors.ON_SURFACE_VARIANT),
            aspect_ratio=self.data.get('canvas_data', {}).get('aspect_ratio'),       # If set, ignores width and height
            content=self.layer_stack, 
            opacity=0.99    # Forces canvas onto its own opacity layer for rendering to avoid blend mode bugs
        )

        
        # Hold layers container to make sure our interactive viewer fills the whole page
        layers_wrapper = ft.Container(
            layers_container, expand=True, 
            alignment=ft.Alignment.CENTER
        )

        # Holds our drawing so we can interact with it, zoom, pan, etc.
        interactive_viewer = ft.InteractiveViewer(
            content=layers_wrapper,
            expand=3,
            scale_factor=500, boundary_margin=50,
            min_scale=0.5, max_scale=3.0,
        )

        # If we're not showing info, just give us a button to show info and return early
        if not self.data.get('show_info', True):

            self.body_container.content = ft.Row( 
                [
                    interactive_viewer, 
                    ft.IconButton(
                        ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY), 
                        mouse_cursor=ft.MouseCursor.CLICK, on_click=self._toggle_show_info,
                        tooltip="Show Canvas Info", bgcolor=ft.Colors.SURFACE_CONTAINER,
                    )
                ], expand=True, spacing=0
            )
            self._render_widget()
            return  # Don't load the info column if we're not showing it   


        information_display = self._create_information_display()  


        self.body_container.content = ft.Row([interactive_viewer, information_display], expand=True, spacing=0)

        self._render_widget()