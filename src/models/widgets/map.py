'''
The map class for all maps inside our story
Maps are widgets that have their own drawing canvas, background image, information display, and locations
'''


import flet as ft
from models.widget import Widget
from models.mini_widgets.map_info import MapInformationDisplay
from models.views.story import Story
from models.dataclasses.canvas_state import State
import flet.canvas as cv
from models.app import app
from styles.menu_option_style import MenuOptionStyle
import asyncio
from models.mini_widgets.map_location import MapLocation
from models.dataclasses.canvas_shape import CanvasShape 
import uuid
from styles.colors import colors


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
                'draw_mode': True,      # Whether we're in draw mode or not
                'show_background_image': True,      # Whether we show the background image or not
                'background_image': "map_bg_fantasy.jpg",    # The background image of the map
                'lore': list(),     # List of lores
                'history': list(),      # List of histories  

                # Holds our labels that sit on the map like locations, but don't have an icon or location
                'labels': {
                    #'id': {'id': 'id_str', 'value': 'Label Text', 'position': (x, y), 'color': 'white'}
                },                              
                              
                # Holds our data for locations
                'mini_widgets_data': {     
                    #'id': {data}
                },

                # Info about the canvas in the back of the map
                'canvas_data': {

                    # Sizing
                    "width": (data or {}).get('canvas_data', {}).get('width') or 2000,
                    "height": (data or {}).get('canvas_data', {}).get('height') or 1000,

                    # Undo and redo list
                    'undo_list': list(),        #['capture_str1', 'capture_str2']
                    'redo_list': list(),

                    'capture': str(),   # Current capture of our layer
                },
            })

        
        # Drawing elements
        self.state = State()
        self.canvas_width = self.data.get('canvas_data', {}).get('width', 0)    # Ez size grabbing later
        self.canvas_height = self.data.get('canvas_data', {}).get('height', 0)
        self.manipulating_shape = False     # Whether we're currently manipulating a shape or not, so we know whether to update our active path or not when dragging
        self.current_path = cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))
        self.active_tool: CanvasShape                    # The active shape being added if we're using a tool

        # The canvas we draw on and the stack that holds our location controls
        self.bg_image: ft.Container
        self.canvas: cv.Canvas 
        self.location_stack: ft.Stack
        self.map_controller: ft.GestureDetector

        # Rest of state elements
        self.new_location_position = (200, 200)     # Where new locations go 
        self.locked_new_location_position = (200, 200)

    # Class for labels on our map, which are like locations but don't have a sidebar info to show
    class Label(ft.GestureDetector):
        def __init__(self, widget: 'Map', data: dict):

            # Initialize node properties
            self.widget = widget
            self.id = data.get('id', str(uuid.uuid4()))
            self.label = data.get('label', 'Label')
            self.position = data.get('position', (0, 0))
            self.color = data.get('color', None)
            
            super().__init__(
                left=self.position[0],  # Give us our position
                top=self.position[1],
                width=150, 
                animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
                on_secondary_tap=lambda: self.widget.story.open_menu(self.get_label_options()),
                on_pan_update=self.move_location,
                on_pan_end=self.save_position,
                on_double_tap=self.focus_tf,
                on_tap_up=self.focus_tf,
                hover_interval=20, 
                on_hover=self.widget.set_mouse_coords,
                mouse_cursor=ft.MouseCursor.MOVE,
            )

        # Moves the node on the stack and updates the drawing that connects the edges
        async def move_location(self, e: ft.DragUpdateEvent):
            
            # Update us visually
            self.left += e.local_delta.x
            self.top += e.local_delta.y
            # Clamp near edges
            if self.left < 20:
                self.left = 0
            if self.left > self.widget.canvas_width - 150:
                self.left = self.widget.canvas_width - 150
            if self.top < 20:
                self.top = 20
            if self.top > self.widget.canvas_height - 20: 
                self.top = self.widget.canvas_height - 20
            self.update()
            
        # Saves updated position to our data
        async def save_position(self, e: ft.DragEndEvent):
            # Update our data to match our new position
            self.position = (self.left, self.top)
            self.widget.data.get('labels', {}).get(self.label, {}).update({'position': self.position})
            self.widget.update_data(**{'labels': self.widget.data.get('labels', {})})
            self.widget.set_mouse_coords(e)     # Reset the menu position

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
                self.widget.data.get('labels', {}).pop(self.label, None)
                self.widget.update_data(**{'labels': self.widget.data.get('labels', {})})
                self.widget.location_stack.controls.remove(self)
                self.widget.location_stack.update()

            return [
                MenuOptionStyle(        # Edit label text
                    ft.MenuItemButton(
                        f"Edit", leading=ft.Icon(ft.Icons.EDIT_OUTLINED, self.color),
                        on_click=self.focus_tf, data="force_focus", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),
                    no_effects=True, no_padding=True
                ),
                MenuOptionStyle(            # Change label color
                    ft.SubmenuButton(
                        ft.Row([
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.color), 
                            ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
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
                        tooltip="Change this widget's color"
                    ),
                    no_padding=True, no_effects=True
                ),
                MenuOptionStyle(        # Delete label
                    ft.MenuItemButton(
                        f"Delete {self.label}", leading=ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR),
                        on_click=handle_delete, data={"icon": "location_pin"},
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),
                    no_effects=True, no_padding=True
                ),
            ]
        
        # Focuses our textfield for editing
        async def focus_tf(self, e: ft.PointerEvent[ft.GestureDetector]):
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
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
                expand=True, text_align=ft.TextAlign.CENTER,
                content_padding=ft.Padding.all(0),
                on_blur=save_label, dense=True, border_radius=4,
                border_color=ft.Colors.TRANSPARENT,
                focused_border_color=ft.Colors.PRIMARY,
                multiline=True,
            )

            # Set our labels content
            self.content = ft.Container(self.label_tf, ignore_interactions=True)    # Let Gesture Detector handle all interactions
            

    # Creates our location control in data, on the location_stack, and focuses it in the sidebar
    async def create_location(self, e: ft.Event[ft.Button]=None):
        await self.story.close_menu()
        return
    
    # Creates our label control in data and on the location stack
    async def create_label(self, e: ft.Event[ft.Button]=None):
        await self.story.close_menu()

        # Create default data
        new_id = str(uuid.uuid4())
        new_data = {
            'id': new_id,
            'label': "New Label",
            'position': self.locked_new_location_position,
            'color': "on_surface",
        }

        # Add to data and update
        self.data.get('labels', {}).update({new_id: new_data})
        self.update_data(**{'labels': self.data.get('labels', {})})

        # Add to stack and update
        self.location_stack.controls.append(self.Label(self, new_data))
        self.location_stack.update()
    
    def create_sidebar_ctrls(self) -> list[ft.Control]:

        # TODO: Lore, history

        return [
            
            self.description_tf,
            #lore_tf,
            #history_tf, 
                        
            ft.Text("Locations", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None),),

            ft.Divider(),
            self.sidebar_notes_label,
            self.sidebar_notes_column,
                    
        ] 
            
            
        

    # Called when clicking to show our info in the sidebar
    async def show_info(self, e: ft.Event=None):
        self.shown_in_sidebar = True
        self.sidebar_title.value = self.data.get('title', '')   # Update title to match us
        self.sidebar_body.controls = self.create_sidebar_ctrls()  # Build info sidebar content here
        
        # Applies the update
        self.sidebar.update()
        await self.show_sidebar()

    # Sets our background image
    async def set_bg_image(self, e):
        return

    
    def get_new_item_options(self) -> list[ft.Control]:
        
        

        async def _create_location(e: ft.Event[ft.Button]):
            await self.create_location(e)
            await self.story.close_menu()

        # Locks our position at wherever we clicked to open the menu
        self.locked_new_location_position = self.new_location_position

        return [
            
            MenuOptionStyle(
                ft.MenuItemButton(
                    "New Location", leading=ft.Icon(ft.Icons.LOCATION_PIN, self.data.get('color', "primary")),
                    on_click=self.create_location, data={"icon": "location_pin"},
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_effects=True, no_padding=True
            ),
            MenuOptionStyle(
                ft.MenuItemButton(
                    "New Label", leading=ft.Icon(ft.Icons.TEXT_FIELDS_OUTLINED, self.data.get('color', "primary")),
                    on_click=self.create_label, data={"icon": "location_pin"},
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_effects=True, no_padding=True
            )
        ]
    
    def set_mouse_coords(self, e: ft.PointerEvent):
        self.new_location_position = (e.local_position.x, e.local_position.y)
        super().set_mouse_coords(e)


    def build(self):
        super().build()

        self.bg_image = ft.Container(           # Background container
            ignore_interactions=True,
            width=self.canvas_width, height=self.canvas_height,
            image=ft.DecorationImage(       # Background image
                "map_bg_fantasy.jpg", 
                #ft.ColorFilter(ft.Colors.with_opacity(1, ft.Colors.BLACK), ft.BlendMode.SOFT_LIGHT),
                #repeat=ft.ImageRepeat.REPEAT
                fit=ft.BoxFit.FILL
            ) if self.data.get('map_data', {}).get('show_bg_map', True) else None,
        )

        self.canvas= cv.Canvas(
            shapes=[],
            width=self.canvas_width,
            height=self.canvas_height,
        )  

        # TODO:  
        # Users can choose to create their image or use some default ones, or upload their own
        # Handle resizing
        # Our stack for map locations

        self.location_stack = ft.Stack(
            [self.Label(self, data) for data in self.data.get('labels', {}).values()], 
            width=self.canvas_width, height=self.canvas_height,
        )

        self.map_controller = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.PRECISE if self.data.get('draw_mode', False) else None, 
            expand=True,

            # Drawing event handlers
            #on_pan_start=self.start_drawing,
            #on_pan_update=self.is_drawing,
            #on_pan_end=lambda e: self.save_canvas(),
            #on_tap_up=self.add_point,      # Handles so we can add points

            # Non-drawing event handlers
            on_secondary_tap=lambda: self.story.open_menu(self.get_new_item_options()),
            on_hover=self.set_mouse_coords,
            #on_tap=lambda: self.story.open_menu(self.get_new_item_options()),
        )
                
        interactive_viewer = ft.InteractiveViewer(
            content=ft.Stack([
                self.bg_image,
                self.canvas,        # Canvas with our map drawing
                self.map_controller,        # Gesture detector for our map
                self.location_stack,        # Stack with our map locations
            ], width=self.canvas_width, height=self.canvas_height),
            expand=3, 
            constrained=False,
            scale_factor=800, boundary_margin=500,
            min_scale=0.01, max_scale=3.0,
        )


        # TODO: Add settings to select from maps, or none, or upload your own. or use a canvas

        self.sidebar_body.controls = self.create_sidebar_ctrls()  # Build info sidebar content here

        
        # Set up our main conent
        self.content = ft.Stack([
            ft.Row([interactive_viewer, self.sidebar], spacing=0, expand=True),
            self.show_sidebar_button, 
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)



        
               
    



        