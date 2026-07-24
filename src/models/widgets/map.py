'''
The map class for all maps inside our story
Maps are widgets that have their own drawing canvas, background image, information display, and locations
'''


import flet as ft
from models.widget import Widget
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
from styles.text_fields import TextField


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
                'draw_mode': False,      # Whether we're in draw mode or not
                'show_background_image': True,      # Whether we show the background image or not
                'background_image': "map_bg_fantasy.jpg",    # The background image of the map

                'lore': list(),     # List of lores [{'label': "Lore Label", 'content': "Lore Content"}]
                'history': list(),      # List of histories  [{'label': "History Label", 'content': "History Content"}]

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
        self.map_width = self.data.get('canvas_data', {}).get('width', 0)    # Ez size grabbing later
        self.map_height = self.data.get('canvas_data', {}).get('height', 0)
        self.manipulating_shape = False     # Whether we're currently manipulating a shape or not, so we know whether to update our active path or not when dragging
        self.current_path = cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))
        self.active_tool: CanvasShape                    # The active shape being added if we're using a tool

        # The canvas we draw on and the stack that holds our location controls
        self.bg_image: ft.Container
        self.canvas: cv.Canvas 
        self.location_stack: ft.Stack
        self.label_stack: ft.Stack
        self.map_controller: ft.GestureDetector

        # Rest of state elements
        self.new_location_position = (200, 200)     # Where new locations go 
        self.locked_new_location_position = (200, 200)
        self.showing_info: bool = False

    # Class for labels on our map, which are like locations but don't have a sidebar info to show
    class Label(ft.GestureDetector):
        def __init__(self, widget: 'Map', data: dict):

            # Initialize node properties
            self.widget = widget
            self.id = data.get('id', str(uuid.uuid4()))
            self.label = data.get('label', 'Label')
            self.position = data.get('position', (0, 0))
            self.color = data.get('color', None)

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
                self.widget.data.get('labels', {}).pop(self.label, None)
                self.widget.update_data(**{'labels': self.widget.data.get('labels', {})})
                self.widget.location_stack.controls.remove(self)
                self.widget.location_stack.update()

            return [
                MenuOptionStyle(        # Edit label text
                    ft.MenuItemButton(
                        ft.Text("Edit Label", weight=ft.FontWeight.BOLD, expand=True), leading=ft.Icon(ft.Icons.EDIT_OUTLINED, self.color),
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
                        ft.Text(f"Delete {self.label}", weight=ft.FontWeight.BOLD, expand=True), leading=ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR),
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
            self.content = ft.Container(self.label_tf, ignore_interactions=True, border_radius=4)    # Let Gesture Detector handle all interactions
            

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
            'color': "on_surface",
        }

        # Add to data and update
        self.data.get('labels', {}).update({new_id: new_data})
        self.update_data(**{'labels': self.data.get('labels', {})})

        # Add to stack and update
        self.label_stack.controls.append(self.Label(self, new_data))
        self.label_stack.update()
    
    def create_sidebar_ctrls(self) -> list[ft.Control]:
        
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
                ft.Text("Lores", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                new_lore_button := ft.IconButton(
                    ft.Icons.NEW_LABEL_OUTLINED, self.data.get('color', "primary"), 
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
            
            
        

    # Called when clicking to show our info in the sidebar
    async def show_info(self, e=None):

        # Close menu
        await self.story.close_menu()
        if self.showing_info:   # Already showing info, so no need to re-call it
            return
        
        # Rebuild header stuff
        self.sidebar_title.value = self.data.get('title', '')   # Update title to match us
        self.sidebar_header.controls[1] = self.create_sidebar_header_setting_ctrl()  # Build our settings button

        # Build the body
        self.sidebar_body.controls = self.create_sidebar_ctrls()  
        self.sidebar.content.controls.append(ft.Row([self.description_tf]))

        # Applies the update
        if not await self.show_sidebar():
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
                    "New Location", leading=ft.Icon(ft.Icons.LOCATION_PIN, self.data.get('color', "primary")),
                    on_click=self.create_location, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_effects=True, no_padding=True
            ),
            MenuOptionStyle(
                ft.MenuItemButton(
                    "New Label", leading=ft.Icon(ft.Icons.TEXT_FIELDS_OUTLINED, self.data.get('color', "primary")),
                    on_click=self.create_label, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_effects=True, no_padding=True
            ),
            MenuOptionStyle(
                ft.MenuItemButton(
                    "Show Info", leading=ft.Icon(ft.Icons.INFO_OUTLINE, self.data.get('color', "primary")),
                    on_click=self.show_info, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Show this map's info in the sidebar",
                ),
                no_effects=True, no_padding=True
            )
        ]
    
    # Also sets our mouse coordinates for the menu to open at the right place
    def set_mouse_coords(self, e: ft.PointerEvent):
        self.new_location_position = (e.local_position.x, e.local_position.y)
        super().set_mouse_coords(e)

    def create_sidebar_header_setting_ctrl(self) -> ft.MenuBar:
    
        # TODO: Settings - show/change map bg, select from canvas, upload, etc, enable drawing
        # Change select build in image to submenubutton
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

    # Build the map
    def build(self):
        super().build()

        self.bg_image = ft.Container(           # Background container
            ignore_interactions=True,
            width=self.map_width, height=self.map_height,
            image=ft.DecorationImage(       # Background image
                "map_bg_fantasy.jpg", 
                #ft.ColorFilter(ft.Colors.with_opacity(1, ft.Colors.BLACK), ft.BlendMode.SOFT_LIGHT),
                #repeat=ft.ImageRepeat.REPEAT
                fit=ft.BoxFit.FILL
            ) if self.data.get('map_data', {}).get('show_bg_map', True) else None,
        )

        self.canvas= cv.Canvas(
            shapes=[],
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
            #on_tap_up=self.add_point,          # Handles so we can add points
            #on_pan_start=self.start_drawing,   
            #on_pan_update=self.is_drawing,
            #on_pan_end=lambda e: self.save_canvas(),
            

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
                self.label_stack,           # Stack with our map labels
            ], width=self.map_width, height=self.map_height),
            expand=3, 
            constrained=False,
            scale_factor=800, boundary_margin=500,
            min_scale=0.01, max_scale=3.0,
        )


        # Add our settings button to the sidebar header, and build our body
        self.sidebar_header.controls.insert(1, self.create_sidebar_header_setting_ctrl()) 
        self.sidebar_body.controls = self.create_sidebar_ctrls()  
        self.sidebar.content.controls.append(ft.Row([self.description_tf]))
        
        


        if self.data.get('show_sidebar', True):
            self.showing_info = True

        
        
        # Set up our main conent
        self.content = ft.Stack([
            ft.Row([interactive_viewer, self.sidebar], spacing=0, expand=True),
            self.show_sidebar_button, 
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)



        
               
    



        