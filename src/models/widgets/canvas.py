'''
The canvas class for all canvases inside our story
Canvases are drawings and images
'''

#TODO: 
# Option for transparent background/no brackground
# Option to upload image as background
# Option to export canvas as image file (png, jpg, etc). Option to change how image fits on canvas (stretch, fit, fill, tile, center, etc)
# Add ft.DecorationImage options to the canvas container for background images??
# Add color_filter for both decoration image and container ?
# Fill tool??
# Ability to Lock (no drawing mode) for images
# Little Info Display Button in the bottom right that can be dragged around and shows canvas info display

from flet_color_pickers import ColorPicker
import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from styles.snack_bar import SnackBar
from models.dataclasses.state import State
import flet.canvas as cv
import math
from models.app import app
from models.mini_widgets.canvas_info import CanvasInformationDisplay



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

                # Canvas drawing data we save and load from
                "canvas_data": {

                    # Data for the info display
                    'Description': str,

                    # Drawing data
                    'paths': list,              # All our shapes, lines, dashed lines, curves, etc.
                    'shadow_paths': list,       # All paths but with shadows
                    'points': list,             # All our points

                    # Sizing of the canvas
                    "width": None,
                    "height": None,
                    "aspect_ratio": None,      # Used over height and width if set

                    # Background settings
                    'bgcolor': str,                 # If its a color
                    'image_base64': str,            # If an image is used. Color ignored if this is set
                    'bg_blend_mode': "src_over",    # Blend mode for background. Starts default
                    'bg_is_transparent': True,    
                
                },

            },
        )

        # State tracking for canvas drawing info
        self.state: State = State()         # Used for our coordinates and how to apply things
        self.min_segment_dist: float = 3.0
        self.canvas_width: int = 0
        self.canvas_height: int = 0

      

        self.canvas = cv.Canvas(
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.PRECISE,
                on_pan_start=self.start_drawing,
                on_pan_update=self.is_drawing,
                on_pan_end=lambda e: self.save_canvas(),
                on_tap_up=self.add_point,      # Handles so we can add points
                drag_interval=5,
                expand=True,
            ),
            expand=True,
            on_resize=self.on_canvas_resize, resize_interval=500,
        )

        self.canvases_list = [self.canvas]  # Not used, but may be for layering

        self.canvas_container = ft.Container(
            width=self.data.get('canvas_data', {}).get('width', None),
            height=self.data.get('canvas_data', {}).get('height', None),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.Border.all(1, ft.Colors.ON_SURFACE_VARIANT),
            aspect_ratio=self.data.get('canvas_data', {}).get('aspect_ratio'),       # If set, ignores width and height
            content=self.canvas
        )

        self.canvas_stack = ft.Stack(expand=True)   

        self.current_path= cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))
       
        # Load our drawing/display
        self.load_canvas()

        self.information_display: ft.Container = None
        self._create_information_display()

        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Called in the constructor
    def _create_information_display(self):
        ''' Creates our plotline information display mini widget '''
        
        self.information_display = CanvasInformationDisplay(
            title=self.title,
            owner=self,
            page=self.p,
            key="canvas_data",     
            data=self.data.get('canvas_data'),      
        )
        # Add to our mini widgets so it shows up in the UI
        self.mini_widgets.append(self.information_display)


    # Called on launch to load our drawing from data into our canvas
    def load_canvas(self):
        """ Loads our drawing from our data """

        # Clear our canvas, and load our shapes stored in data
        self.canvas.shapes.clear()
        shapes = self.data.get('canvas_data', {})

        # Load our background color if we have one
        bgcolor = self.data.get('canvas_data', {}).get('bgcolor', None)
        if bgcolor is not None:
            if bgcolor != "":
                blend_mode = self.data.get('canvas_data', {}).get('bg_blend_mode', 'src_over')
                self.canvas.shapes.append(
                    cv.Color(       # Can use effects here as well
                        color=bgcolor,
                        blend_mode=blend_mode,
                    )
                )

        # Loading points
        for point in shapes.get('points', []):
            px, py, point_mode, paint_settings = point
            self.canvas.shapes.append(
                cv.Points(
                    points=[(px, py)],
                    point_mode=point_mode,
                    paint=ft.Paint(**paint_settings),
                )
            )

        # Loading our paths, which most of the drawing
        for path in shapes.get('paths', []):
            
            elements = path.get('elements', [])         # List of the elements in this path
            paint_settings = path.get('paint', {})      # Paint settings for this path

            # Grab our style for simple logic
            style = path.get('paint', {}).get('style', 'stroke')

            # Make a copy of our paint settings to modify for drawing
            safe_paint_settings = path.get('paint', {}).copy()

            # If in erase mode, we have to set blur_image to 0 and
            if safe_paint_settings.get('blend_mode', 'src_over') == 'clear':
                safe_paint_settings['blur_image'] = 0

            # Set stroke or fill based on custom styles
            safe_stroke = 'fill' if style.endswith('fill') else 'stroke'
            safe_paint_settings['style'] = safe_stroke

            new_path = cv.Path(elements=[], paint=ft.Paint(**safe_paint_settings))   # Set a new path for this path with our paint settings

            # Iterate through each element for its type, and create a new path element based on that
            for element in elements:

                # MoveTo just has x and y
                if element['type'] == 'moveto':
                    new_path.elements.append(cv.Path.MoveTo(element['x'], element['y']))

                # Lineto jjust has x and y
                elif element['type'] == 'lineto':
                    new_path.elements.append(cv.Path.LineTo(element['x'], element['y']))

                elif element['type'] == 'arc':
                    new_path.elements.append(
                        cv.Path.Arc(
                            width=element['width'],
                            height=element['height'],
                            x=element['x'],
                            y=element['y'],
                            start_angle=element['start_angle'],
                            sweep_angle=element['sweep_angle'],
                        )
                    )
                        

                # QuadraticTo has cp1x, cp1y, x, y, w
                elif element['type'] == 'arcto':
                    new_path.elements.append(
                        cv.Path.ArcTo(
                            radius=element['radius'],
                            rotation=element['rotation'],
                            large_arc=element['large_arc'],
                            x=element['x'],
                            y=element['y'],
                        )
                    )

                
                else:
                    print("Unknown path element type while loading: ", element)
                    self.p.open(SnackBar(f"Error loading {self.title}"))

            self.canvas.shapes.append(new_path)
    

    # Called when we click the canvas and don't initiate a drag
    async def add_point(self, e: ft.TapEvent):
        ''' Adds a point to the canvas if we just clicked and didn't initiate a drag '''

        # Create the point using our paint settings and point mode
        point = cv.Points(
            points=[(e.local_x, e.local_y)],
            paint=ft.Paint(**app.settings.data.get('paint_settings', {})),
        )
        
        # Add point to the canvas and our state data
        self.canvas.shapes.append(point)
        self.state.points.append((e.local_x, e.local_y, point.point_mode, point.paint.__dict__))

        # After dragging canvas widget, it loses page reference and can't update, so the exception handles that.
        try:
            self.canvas.update()
        except Exception as ex:
            #self.canvas.page = self.p
            self.canvas.update()
            
        # Save our canvas data
        self.save_canvas()
        
    # Called when we start drawing on the canvas
    async def start_drawing(self, e: ft.DragStartEvent):
        ''' Set our initial starting x and y coordinates for the element we're drawing '''

        # Grab our style so we can compare it
        style = str(app.settings.data.get('paint_settings', {}).get('style', 'stroke'))

        # Make a copy of our paint settings to modify it, since some of the styles are not built in
        safe_paint_settings = app.settings.data.get('paint_settings', {}).copy()

        # Copy of our paint settings for our state tracking and data storage (only erase mode needs this)
        state_paint_settings = app.settings.data.get('paint_settings', {}).copy()

        # Set either stroke or fill based on custom styles
        safe_stroke = 'fill' if style.endswith('fill') else 'stroke'
        safe_paint_settings['style'] = safe_stroke

        # Check if we're in erase mode or not. If we are, set blend mode to clear and blur image to 0
        if self.story.data.get('canvas_settings', {}).get('erase_mode', False):
            safe_paint_settings['blend_mode'] = "clear"
            safe_paint_settings['blur_image'] = 0
            state_paint_settings['blend_mode'] = "clear"
            state_paint_settings['blur_image'] = 0
        

        # Update state x and y coordinates
        self.state.x, self.state.y = e.local_x, e.local_y

        # Clear and set our current path and state to match it
        self.current_path = cv.Path(elements=[], paint=ft.Paint(**safe_paint_settings))
        self.state.paths.clear()
        self.state.paths.append({'elements': list(), 'paint': state_paint_settings})

        # Set move to element at our starting position that the mouse is at for the path to start from
        move_to_element = cv.Path.MoveTo(e.local_x, e.local_y)

        # Add that element to current paths elements and our state paths
        self.current_path.elements.append(move_to_element)
        self.state.paths[0]['elements'].append((move_to_element.__dict__))


        match style:
            # If we're using lineto (straight lines), add that element to the current path and state right away
            case "lineto":
                line_element = cv.Path.LineTo(e.local_x, e.local_y)
                self.current_path.elements.append(line_element)
                self.state.paths[0]['elements'].append((line_element.__dict__))

            case "arc":
                arc_element = cv.Path.Arc(
                    width=20,
                    height=20,
                    
                    x=e.local_x,
                    y=e.local_y,
                    start_angle=math.pi,
                    sweep_angle=-math.pi,
                )
                self.current_path.elements.append(arc_element)
                self.state.paths[0]['elements'].append((arc_element.__dict__))

        # Else if we're using arcto, add that element to the current path and state right away
            case 'arcto' | 'arctofill':
                arc_element = cv.Path.ArcTo(
                    radius=12,
                    rotation=0,
                    large_arc=False,
                    x=e.local_x,
                    y=e.local_y,
                    clockwise=True,
                )
                self.current_path.elements.append(arc_element)
                self.state.paths[0]['elements'].append((arc_element.__dict__))

        # Add the path to the canvas so we can see it
        self.canvas.shapes.append(self.current_path)


        
    # Called when actively drawing on the canvas
    async def is_drawing(self, e: ft.DragUpdateEvent):
        ''' Creates our line to add to the canvas as we draw, and saves that paths data to self.state '''

        # Sampling to improve perforamance. If the line length is too small, we skip it
        #dx = e.local_x - self.state.x
        #dy = e.local_y - self.state.y
        #if dx * dx + dy * dy < self.min_segment_dist * self.min_segment_dist:
            #return
        
        # Grab our style so we can compare it
        style = str(app.settings.data.get('paint_settings', {}).get('style', 'stroke'))


        match style:
        # Handle lineto (Straight lines). Grab the element we created on start drawing, update its data
            case "lineto":
            
                # Set the element and its data
                line_element = self.current_path.elements[-1]
                line_dict = line_element.__dict__

                # Update the elements position
                line_element.x = e.local_x
                line_element.y = e.local_y

                # Update the dict to match
                line_dict['x'] = line_element.x
                line_dict['y'] = line_element.y

                # Update the page and return early
                try:
                    # Much more effecient to just update the path, but that fails on first update due to lost page references
                    self.current_path.update()
                    
                # This re-sets the canvas page, which all paths need to update correctly. This should only catch one time per stroke
                except Exception as ex:
                    #self.canvas.page = self.p
                    self.canvas.update()
                return
        
            case "arc" | "arcfill":
            
                # Set the element and its data
                arc_element = self.current_path.elements[-1]
                arc_dict = arc_element.__dict__

                # Swap directions of arc depending if we drag up or down from starting point
                if e.local_y - self.state.y >= 0:   # Dragging down
                    arc_element.sweep_angle = -math.pi
                    arc_element.height = abs(self.state.y - e.local_y)
                    arc_element.y = self.state.y - (arc_element.height / 2)
                    
                else:       # Dragging up
                    arc_element.sweep_angle = math.pi
                    arc_element.height = abs(e.local_y - self.state.y)
                    arc_element.y = abs(self.state.y - (arc_element.height / 2))

                if e.local_x - self.state.x < 0:   # Dragging left, move X position of arc to match
                    arc_element.x = e.local_x

                arc_element.width = abs(e.local_x - self.state.x) 

                # Update the page and return early
                try:
                    self.current_path.update()
                    
                except Exception as ex:
                    #self.canvas.page = self.p
                    self.canvas.update()
                return
        
            # Handle arcs
            case 'arcto' | 'arctofill':
            
                arc_element = self.current_path.elements[-1]
                arc_dict = arc_element.__dict__

                arc_element.x = e.local_x
                arc_element.y = e.local_y

                arc_dict['x'] = arc_element.x
                arc_dict['y'] = arc_element.y

                # Update the page and return early
                try:
                    # Page reference gets lost after dragging widget to new canvas, so we reset it and update
                    self.current_path.update()
                   
                except Exception as ex:
                    #self.canvas.page = self.p
                    self.canvas.update()
                return
        
        
            # If its not one of our custom styles, use free-draw stroke, which is constantly adding line_to segements
            case _:

                #TODO: Add check here to reduce num of lines based on previous start and end??
                # Set the path element based on what kind of path we're adding, add it to our current path and our state paths
                path_element = cv.Path.LineTo(e.local_x, e.local_y)

                # Add the declared element to our current path and state paths
                self.current_path.elements.append(path_element)
                self.state.paths[0]['elements'].append((path_element.__dict__))  

                # After dragging canvas widget, it loses page reference and can't update
                try:
                    self.current_path.update()
                except Exception as ex:
                    #self.canvas.page = self.p
                    self.canvas.update()
                

                # Update our state x and y for the next segment
                self.state.x, self.state.y = e.local_x, e.local_y
        

    # Called when we release the mouse to stop drawing a line
    def save_canvas(self):
        """ Saves our paths to our canvas data for storage """
        
        # Add on to what we already have
        if self.state.paths:
            self.data['canvas_data']['paths'].extend(self.state.paths)
        if self.state.points:
            self.data['canvas_data']['points'].extend(self.state.points)

        self.save_dict()

        # Clear the current state, otherwise it constantly grows and lags the program
        self.state.paths.clear()
        self.state.points.clear()

        #print("Length of canvas paths data: ", len(self.data['canvas']['paths']))
        #print("Number of elements in all paths: ", sum(len(p['elements']) for p in self.data['canvas']['paths']))


    # Called when the canvas control is resized
    async def on_canvas_resize(self, e: cv.CanvasResizeEvent=None):
        """ Rescales stored drawing coordinates to match the new canvas size """
        # Update our page reference and size
        #self.canvas.page = self.p
        if e is not None:
            self.canvas_width = int(e.width)
            self.canvas_height = int(e.height)

        if self.information_display.data.get('left', None) is None or self.information_display.data.get('top', None) is None:
            self.information_display.data['left'] = 30
            self.information_display.data['top'] = self.canvas_height - 30
            self.information_display.show_info_button.left = 30
            self.information_display.show_info_button.top = self.canvas_height - 30
            #self.information_display.show_info_button.page = self.p
            self.information_display.show_info_button.update()
            self.information_display.save_dict()


    def _set_canvas_background(self, e):
        """ Sets the canvas background based on menu selection. """

        cp = ColorPicker()

        choice = e.control.text

        if choice == "None":
            pass


        elif choice == "Color":
            pass
            # Pop up color picker with opacity slider to the right of it
            # When hitting apply, set the data and color

        elif choice == "Image":
            pass
            # Open file dialog to select image


    # TODO: NOT TESTED ----------------------------------
    def export_canvas(self, filename: str = "canvas_export.png", desired_width: int = 1920, desired_height: int = 1080):
        """Exports the canvas as an image at desired size, computing bounds if no meta exists."""
        shapes = self.data.get('canvas_data', {})
        
        # Compute bounding box from all coordinates
        min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
        
        # Check points
        for point in shapes.get('points', []):
            px, py = point[0], point[1]
            min_x = min(min_x, px)
            min_y = min(min_y, py)
            max_x = max(max_x, px)
            max_y = max(max_y, py)
        
        # Check paths
        for path in shapes.get('paths', []):
            for element in path.get('elements', []):
                if 'x' in element and 'y' in element:
                    min_x = min(min_x, element['x'])
                    min_y = min(min_y, element['y'])
                    max_x = max(max_x, element['x'])
                    max_y = max(max_y, element['y'])
        
        # If no shapes, use defaults
        if min_x == float('inf'):
            min_x, min_y, max_x, max_y = 0, 0, desired_width, desired_height
        
        # Calculate original bounds
        orig_width = max_x - min_x
        orig_height = max_y - min_y
        
        # Avoid division by zero
        if orig_width == 0:
            orig_width = 1
        if orig_height == 0:
            orig_height = 1
        
        # Scale factor to fit desired size (maintain aspect ratio or stretch as needed)
        scale_x = desired_width / orig_width
        scale_y = desired_height / orig_height
        scale = min(scale_x, scale_y)  # To fit without cropping; use max for stretching
        
        # Create image at desired size
        #img = Image.new("RGBA", (desired_width, desired_height), (255, 255, 255, 0))
        #draw = ImageDraw.Draw(img)
        
        # Render shapes, scaled and translated
        offset_x = (desired_width - orig_width * scale) / 2  # Center horizontally
        offset_y = (desired_height - orig_height * scale) / 2  # Center vertically
        
        # Render points
        for point in shapes.get('points', []):
            px, py, point_mode, paint_settings = point
            scaled_x = (px - min_x) * scale + offset_x
            scaled_y = (py - min_y) * scale + offset_y
            # Draw as circle (adapt for point_mode)
            #draw.ellipse((scaled_x-2, scaled_y-2, scaled_x+2, scaled_y+2), fill=paint_settings.get('color', 'black'))
        
        # Render paths (simplified; full path rendering needs more logic for curves)
        for path in shapes.get('paths', []):
            paint_settings = path.get('paint', {})
            points = []
            for element in path.get('elements', []):
                if element['type'] in ['moveto', 'lineto']:
                    scaled_x = (element['x'] - min_x) * scale + offset_x
                    scaled_y = (element['y'] - min_y) * scale + offset_y
                    points.append((scaled_x, scaled_y))
            #if points:
                #draw.line(points, fill=paint_settings.get('color', 'black'), width=2)
        
        #img.save(os.path.join(self.directory_path, filename))
        self.page.open(SnackBar(f"Canvas exported to {filename} at {desired_width}x{desired_height}"))
        self.page.update()

    # Called when we need to rebuild out plotline UI
    def reload_widget(self):       
        ''' Rebuilds/reloads our Canvas '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        

        iv = ft.InteractiveViewer(
            content=self.canvas_container, expand=True,
            scale_factor=750, boundary_margin=50,
            min_scale=0.5, max_scale=2.0, scale=1.0,
        )

        self.canvas_stack.controls = [
            ft.Container(expand=True, ignore_interactions=True),
            iv,
            self.information_display.show_info_button,
        ]

        self.body_container.content = self.canvas_stack

        self._render_widget()
 

