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
from models.dataclasses.state import State
import flet.canvas as cv
import math
from models.app import app
from models.mini_widgets.canvas_info import CanvasInformationDisplay
import json
import base64



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

                # Info display and general canvas data
                'canvas_data': {},       

                'capture': str,             # Capture of what we currently look like
                'snapshot': str,            # Most recent completed snapshot of our canvas used by other widgets

                # Canvas drawing data we save and load from
                #"canvas": {},
            },
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)

        self.information_display: ft.Container = None
        self._create_information_display()

        # State tracking for canvas drawing info
        self.state = State()         # Used for our coordinates and how to apply things
        self.canvas_width = 0
        self.canvas_height = 0
        self.undo_idx = 0       #??


        
        self.layers = [{}]    # List of our layers, which are each their own canvas
        self.layer_stack: ft.Stack  # Stack to hold our layers on top of each other

        self.bg_image: ft.DecorationImage   # Hold our background image
        
        self.current_path= cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))


        # Canvas has a custom tab, so it re-uses almost everything from widget
        # UI ELEMENTS - Tab
        self.tabs: ft.Tabs 
        self.tab: ft.Tab  
        self.icon: ft.Icon
        self.tab_text: ft.Text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True)

        # Grabs our tag to determine the icon we'll use
        tag = self.data.get('tag', '')

        # Set our icon based on what type of widget we are using tag
        match tag:
            case "document": self.icon = ft.Icon(ft.Icons.DESCRIPTION_OUTLINED)
            case "canvas": self.icon = ft.Icon(ft.Icons.BRUSH_OUTLINED)
            case "canvas_board": self.icon = ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED)
            case "note": self.icon = ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED)
            case "character": self.icon = ft.Icon(ft.Icons.PERSON_OUTLINE)
            case "character_connection_map": self.icon = ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED)
            case "plotline": self.icon = ft.Icon(ft.Icons.TIMELINE)
            case "map": self.icon = ft.Icon(ft.Icons.MAP_OUTLINED)
            case "world": self.icon = ft.Icon(ft.Icons.PUBLIC_OUTLINED)
            case "object": self.icon = ft.Icon(ft.Icons.SHIELD_OUTLINED)
            case _: self.icon = ft.Icon(ft.Icons.ERROR_OUTLINE)


        # Set the color and size
        self.icon.color = self.data.get('color', ft.Colors.PRIMARY)

        tab_text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS)
        
        # Our icon button that will hide the widget when clicked in the workspace
        hide_tab_icon_button = ft.IconButton(    # Icon to hide the tab from the workspace area
            scale=0.8,
            on_click=self.hide_widget,
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Hide",
            mouse_cursor=ft.MouseCursor.CLICK,
        )

        self.toggle_info_button = ft.IconButton(
            ft.Icons.INFO_OUTLINE, self.data.get('color', "primary"), scale=0.8,
            mouse_cursor=ft.MouseCursor.CLICK,
            tooltip="Show Canvas Info",
            on_click=self.information_display.show_mini_widget,
            # on_click here
        )


        self.tab_gd = ft.GestureDetector(
            ft.Row(
                [self.icon, ft.Container(width=10), tab_text, self.toggle_info_button, ft.Container(expand=True), hide_tab_icon_button],
                spacing=0
            ),     # Changes here to add show info button
            mouse_cursor=ft.MouseCursor.CLICK,
            hover_interval=100,
            #on_enter=self._set_coords,
            on_hover=self._set_coords,
            #on_exit=self._exit_tab,
            on_secondary_tap=lambda _: self.story.open_menu(self._get_menu_options()),
        )

        # Tab that holds our widget title and 'body'.
        # Since this is a ft.Tab, it needs to be nested in a ft.Tabs control or it wont render.
        self.tab = ft.Tab(

            # Content of the tab itself. Has widgets name and hide widget icon, and functionality for dragging
            label=ft.Draggable(   # Draggable is the control so we can drag and drop to different pin locations
                group="widgets",    # Group for draggables (and receiving drag targets) to accept each other
                data=self.data.get('key', ""),  # Pass ourself through the data (of our tab, NOT our object) so we can move ourself around

                # Drag event utils
                on_drag_start=self._start_drag,    # Shows our pin targets when we start dragging

                # Content when we are dragging the follows the mouse
                content_feedback=ft.TextButton(self.title), # Normal text won't restrict its own size, so we use a button

                # The content of our draggable. We use a gesture detector so we have more events
                content=self.tab_gd
            )                    
        )

        # Tabs stuff
        self.tabs = ft.Tabs(
            expand=True,  
            length=1,
            selected_index=0,
            content=ft.Column([
                ft.TabBar(tabs=[self.tab]),     # Holds our tab at the top of the widget
                ft.TabBarView([self.master_stack], expand=True)# Holds our body
            ], expand=True),
            
        )   
        self.content = self.tabs

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
                        on_pan_start=self.start_drawing,
                        on_pan_update=self.is_drawing,
                        on_pan_end=self.save_canvas,
                        on_tap_up=self.add_point,      # Handles so we can add points
                        on_secondary_tap=lambda _: self.story.open_menu(self._get_menu_options()),
                        on_hover=self._set_coords,
                        hover_interval=20,
                        drag_interval=10,
                        expand=True,
                    ),
                    expand=True, 
                    shapes=[
                        cv.Image(capture, 0, 0)     # Set the capture of the layer for all but background
                    ],
                ),
                expand=True, data=name,
                visible=visible,    # Set visibility

                # Only active layer can draw
                ignore_interactions=True if self.data.get('canvas_data', {}).get('Active Layer', 0) != idx else False,   
            )
            
            self.layers.append({'name': name, 'visible': visible, 'canvas': new_layer})


    # Special color changes for this one
    def reload_tab(self):
        self.toggle_info_button.icon_color = self.data.get('color', "primary")
        self.information_display.reload_mini_widget()
        super().reload_tab()     

    # Called in the constructor
    def _create_information_display(self):
        ''' Creates our plotline information display mini widget '''
        
        self.information_display = CanvasInformationDisplay(
            title=self.title,
            widget=self,
            page=self.p,
            key="canvas_data",     
            data=self.data.get('canvas_data'),      
        )
        # Add to our mini widgets so it shows up in the UI
        self.mini_widgets.append(self.information_display)

    def _get_menu_options(self):
        ''' Gets the menu options for when we right click on the canvas '''

        options = [
            # Show info
            # Set background image
        ]

        options.extend(super()._get_menu_options())     # Get the default menu options for widgets and add them to our information display options
        return options
        
    # Called when changing our bg color from the info display
    async def set_canvas_bg_clicked(self, e):
        ''' '''
    

    # Called when we click the canvas and don't initiate a drag
    async def add_point(self, e: ft.TapEvent):
        ''' Adds a point to the canvas if we just clicked and didn't initiate a drag '''

        canvas: cv.Canvas = e.control.parent

        # Create the point using our paint settings and point mode
        point = cv.Points(
            points=[(e.local_position.x, e.local_position.y)],
            paint=ft.Paint(**app.settings.data.get('paint_settings', {})),
        )
        
        # Add point to the canvas and our state data
        canvas.shapes.append(point)
        self.state.points.append((e.local_position.x, e.local_position.y, point.point_mode.value, app.settings.data.get('paint_settings', {})))

        # After dragging canvas widget, it loses page reference and can't update, so the exception handles that.
        try:
            canvas.update()
        except Exception as _:
            print("Failed to update canvas")

        #print(self.state.points)
        #print(self.canvas.shapes)
            
        # Save our canvas data
        #self.save_canvas()
        
    # Called when we start drawing on the canvas
    async def start_drawing(self, e: ft.DragStartEvent):
        ''' Set our initial starting x and y coordinates for the element we're drawing '''

        canvas: cv.Canvas = e.control.parent

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
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

        # Clear and set our current path and state to match it
        self.current_path = cv.Path(elements=[], paint=ft.Paint(**safe_paint_settings))
        self.state.paths.clear()
        self.state.paths.append({'elements': list(), 'paint': state_paint_settings})

        # Set move to element at our starting position that the mouse is at for the path to start from
        move_to_element = cv.Path.MoveTo(e.local_position.x, e.local_position.y)

        # Add that element to current paths elements and our state paths
        self.current_path.elements.append(move_to_element)
        self.state.paths[0]['elements'].append((move_to_element.__dict__))


        match style:
            # If we're using lineto (straight lines), add that element to the current path and state right away
            case "lineto":
                line_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
                self.current_path.elements.append(line_element)
                self.state.paths[0]['elements'].append((line_element.__dict__))

            case "arc":
                arc_element = cv.Path.Arc(
                    width=20,
                    height=20,
                    
                    x=e.local_position.x,
                    y=e.local_position.y,
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
                    x=e.local_position.x,
                    y=e.local_position.y,
                    clockwise=True,
                )
                self.current_path.elements.append(arc_element)
                self.state.paths[0]['elements'].append((arc_element.__dict__))

        # Add the path to the canvas so we can see it
        canvas.shapes.append(self.current_path)
        canvas.update()


        
    # Called when actively drawing on the canvas
    async def is_drawing(self, e: ft.DragUpdateEvent):
        ''' Creates our line to add to the canvas as we draw, and saves that paths data to self.state '''

        # Sampling to improve perforamance. If the line length is too small, we skip it
        #dx = e.local_position.x - self.state.x
        #dy = e.local_position.y - self.state.y
        #if dx * dx + dy * dy < self.min_segment_dist * self.min_segment_dist:
            #return

        canvas: cv.Canvas = e.control.parent
        
        # Grab our style so we can compare it
        style = str(app.settings.data.get('paint_settings', {}).get('style', 'stroke'))


        match style:
        # Handle lineto (Straight lines). Grab the element we created on start drawing, update its data
            case "lineto":
            
                # Set the element and its data
                line_element = self.current_path.elements[-1]
                line_dict = line_element.__dict__

                # Update the elements position
                line_element.x = e.local_position.x
                line_element.y = e.local_position.y

                # Update the dict to match
                line_dict['x'] = line_element.x
                line_dict['y'] = line_element.y

                # Update the page and return early
                try:
                    # Much more effecient to just update the path, but that fails on first update due to lost page references
                    self.current_path.update()
                # This re-sets the canvas page, which all paths need to update correctly. This should only catch one time per stroke
                except Exception as _:
                    canvas.update()
                return
        
            case "arc" | "arcfill":
            
                # Set the element and its data
                arc_element = self.current_path.elements[-1]
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

                # Update the page and return early
                try:
                    self.current_path.update()
                except Exception as _:
                    canvas.update()
                return
        
            # Handle arcs
            case 'arcto' | 'arctofill':
            
                arc_element = self.current_path.elements[-1]
                arc_dict = arc_element.__dict__

                arc_element.x = e.local_position.x
                arc_element.y = e.local_position.y

                arc_dict['x'] = arc_element.x
                arc_dict['y'] = arc_element.y

                # Update the page and return early
                try:
                    # Page reference gets lost after dragging widget to new canvas, so we reset it and update
                    self.current_path.update()
                except Exception as _:
                    canvas.update()
                return
        
        
            # If its not one of our custom styles, use free-draw stroke, which is constantly adding line_to segements
            case _:

                #TODO: Add check here to reduce num of lines based on previous start and end??
                # Set the path element based on what kind of path we're adding, add it to our current path and our state paths
                path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)

                # Add the declared element to our current path and state paths
                self.current_path.elements.append(path_element)
                self.state.paths[0]['elements'].append((path_element.__dict__))  

                # After dragging canvas widget, it loses page reference and can't update
                try:
                    self.current_path.update()
                except Exception as _:
                    canvas.update()
                

                # Update our state x and y for the next segment
                self.state.x, self.state.y = e.local_position.x, e.local_position.y
        

    # Called when we release the mouse to stop drawing a line
    async def save_canvas(self, e: ft.DragEndEvent):
        """ Saves our paths to our canvas data for storage """

        # TODO: Set a shapes limit on canvas to clear shapes and re-set background after 15 or so

        canvas: cv.Canvas = e.control.parent

        print("Saving canvas: ", self.title)
        try:

            await canvas.capture()
    
            cc = await canvas.get_capture()
            encoded_capture = base64.b64encode(cc).decode('utf-8')      # Requires encoding to save json
            if encoded_capture:
                print("Got capture of canvas for layer name: ", canvas.data)

                # Save the capture, but we don't use it until a reload_widget is called
                self.data['canvas_data']['Layers'][self.data.get('canvas_data', {}).get('Active Layer', 0)]['capture'] = encoded_capture


                await self.save_dict()     # Save our data with the new capture

            # TODO: Set snapshot for canvas boards to use??

            # Must clear the capture or weird UI bugs
            await canvas.clear_capture()

            # Clear the current state
            self.state.paths.clear()
            self.state.points.clear()

        except Exception as _:
            print("failed to save canvas")

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


    # TODO
    def export_canvas(self):
        """ Exports canvas to correct file type based on selection with optional upscaling """

        # TODO: Make sure to build extra background canvas to export image/color background, as they are currently rendered not captured


        # Get correct size that we are, and see what we need to upscale the resolution too

        # Capture and get it using desired size
        #await self.canvas.capture()
        #cc = await self.canvas.get_capture()
        #encoded_capture = base64.b64encode(cc).decode('utf-8')      # Requires encoding to save json

        #await self.file_picker.save_file(src_bytes=cc, file_name=f"{self.title}.png")

    async def _create_layer_clicked(self, e=None):
        pass
        

    # Called when we need to rebuild out plotline UI
    def reload_widget(self):       
        ''' Rebuilds/reloads our Canvas '''

        # TODO: Need a way to show blur and effect for background layer since its unique

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

        # Align our drawing and info display side by side
        row = ft.Row([
            interactive_viewer, self.information_display
        ], scroll="none", expand=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)



        self.body_container.content = row

        self._render_widget()

        
 

