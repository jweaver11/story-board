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
                'lore': list(),     # List of lores
                'history': list(),      # List of histories                                
                              
                # Holds our data for locations
                'mini_widgets_data': {     
                    #'id': {data}
                },

                # Info about the canvas in the back of the map
                'canvas_data': {

                    # Sizing
                    "width": (data or {}).get('canvas_data', {}).get('width') or 1920,
                    "height": (data or {}).get('canvas_data', {}).get('height') or 1080,

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
        self.canvas: cv.Canvas 
        self.location_stack: ft.Stack

        # Rest of state elements
        self.new_location_position = (0, 0)     # Where new locations go 

    async def create_location(self, title: str, data: dict=None):
        
        new_location = MapLocation(
            title=title,
            widget=self,
            key="locations",   
            data=data,      
            
        )

    # Called when clicking on our map to show our information display
    async def _show_info_display(self, e: ft.TapEvent=None):
        ''' If we're not in drawing mode, show our information display '''
        if not self.data.get('map_data', {}).get('drawing_mode', False):
            await self._show_info_mini_widget()

    async def _open_menu(self, e: ft.PointerEvent):
        
        self.lock_position = True 
        self.story.open_menu(self.get_map_menu_options())

    # Called when right cliicking a new pp, arc, or marker ON the plotline to create it at a specific location
    async def new_location_clicked(self, e):
        ''' Opens a dialog to input the mini widgets name, and creates it at that location '''

        await self.story.close_menu()

        # Checks that the name in the textfield does not match any of the existing mini widgets of that type, and updates visually to reflect
        async def _check_name_unique(e):
            name = new_item_tf.value.strip()
            submit_button.disabled = False
            new_item_tf.error = None
            if not name:
                submit_button.disabled = True
            elif name in self.locations:
                submit_button.disabled = True
                new_item_tf.error = "Name must be unique"
                await new_item_tf.focus()

            else:
                submit_button.disabled = False
                new_item_tf.error = None
            
            new_item_tf.update()
            submit_button.update()
            
        # Create the nwew mini widget with the current text field value. Makes sure we passed checks first
        async def _create_new_mw(e):

            # Button is disabled if name is the same
            if submit_button.disabled:
                new_item_tf.focus()
                return
            
            title = new_item_tf.value.strip()
            await self.create_location(title,)
            

            self.page.pop_dialog()   # Close the dialog

            #await asyncio.sleep(0)        # Needs a buffer or wont work for some reason
            await self.story.close_menu()       


        # Grab the type of mini widget we are creating
        #data = e.control.data

        # Textfield for the name of the new mw
        new_item_tf = ft.TextField(
            label=f"Location Name", expand=True, on_change=_check_name_unique, autofocus=True,
            capitalization=ft.TextCapitalization.WORDS, on_submit=_create_new_mw
        )

        # Button for creating new mw. Can also press enter in the textfield
        submit_button = ft.TextButton("Create", on_click=_create_new_mw, disabled=True, style=ft.ButtonStyle(mouse_cursor="click"))

        # Dialog we open onto the page
        dlg = ft.AlertDialog(
            title=ft.Text(f"New Location Name"),
            content=new_item_tf,
            actions=[
                ft.TextButton("Cancel", style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click"), on_click=lambda _: self.page.pop_dialog()),
                submit_button
            ],
        )

        self.page.show_dialog(dlg)    
    
 
    def get_map_menu_options(self) -> list[ft.Control]:
        

        # TODO: Add Valley, Plains, Rivers, Storm, Lake, Village, Desert, Castle, Other (Rest of options)
            

        # New (all dif types of locations), rename color
        return [
            MenuOptionStyle(
                ft.MenuItemButton(
                    "Location", leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.data.get('color', "primary")),
                    on_click=self.new_location_clicked, 
                    tooltip="Create a new location on your map",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True 
            ),
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.data.get('color', "primary")), 
                            ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    controls=[
                        
                        ft.MenuItemButton(
                            "Label", leading=ft.Icon(ft.Icons.TEXT_FIELDS_OUTLINED, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data={"icon": "label"},
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Point of Interest", leading=ft.Icon(ft.Icons.LOCATION_PIN, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data={"icon": "location_pin"},
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Mountain", leading=ft.Icon(ft.Icons.TERRAIN, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data={"icon": "terrain"},
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Forest", leading=ft.Icon(ft.Icons.FOREST, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data={"icon": "forest"},
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Water", leading=ft.Icon(ft.Icons.WATER, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data={"icon": "water"},
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "City", leading=ft.Icon(ft.Icons.LOCATION_CITY, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data={"icon": "location_city"},
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Dungeon", leading=ft.Icon(ft.Icons.STAIRS_OUTLINED, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data={"icon": "stairs_outlined"},
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
 
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ), 
                no_padding=True, no_effects=True
            ),
        ]
    

    # Called for any size changes to our map canvas
    async def _rebuild_map_canvas(self, e: cv.CanvasResizeEvent=None):
        ''' Redraws our map on the canvas when it is resized. Does it on startup as well '''


    def build(self):
        super().build()

        self.canvas= cv.Canvas(
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.PRECISE if self.data.get('draw_mode', False) else None, 
                expand=True,

                # Drawing event handlers
                #on_pan_start=self.start_drawing,
                #on_pan_update=self.is_drawing,
                #on_pan_end=lambda e: self.save_canvas(),
                #on_tap_up=self.add_point,      # Handles so we can add points

                # Non-drawing event handlers
                on_secondary_tap=lambda: self.story.open_menu(self.get_map_menu_options()),
                on_hover=self._get_coords,
                on_tap=lambda: self.story.open_menu(self.get_map_menu_options()),
            ),
            expand=True,
            width=self.canvas_width,
            height=self.canvas_height,
        )  

        # TODO:  
        # Users can choose to create their image or use some default ones, or upload their own
        # Handle resizing
        # Our stack for map locations

        self.location_stack = ft.Stack(
            [     # Add our background and canvas
            ft.Container(
                expand=True, ignore_interactions=True, #border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT),
                image=ft.DecorationImage(       # Background image
                    "map_background.png", 
                    ft.ColorFilter(ft.Colors.with_opacity(1, ft.Colors.BLACK), ft.BlendMode.SOFT_LIGHT),
                    fit=ft.BoxFit.FILL,
                ) if self.data.get('map_data', {}).get('show_bg_map', True) else None,
                #color_filter=ft.ColorFilter(ft.Colors.with_opacity(1, ft.Colors.BLACK), ft.BlendMode.SOFT_LIGHT),
            ),
            self.canvas, 
         
        ], expand=True)

        # Add our map locations to the stack
        for mw in self.mini_widgets:
            
            if hasattr(mw, 'map_control') and mw.data.get('icon', "") != "label":
                self.location_stack.controls.append(mw.map_control)
            if hasattr(mw, 'map_label'):
                self.location_stack.controls.append(mw.map_label)
            
        
                
        interactive_viewer = ft.InteractiveViewer(
            content=self.location_stack,
            expand=3, 
            constrained=False,
            scale_factor=800, boundary_margin=200,
            min_scale=0.02, max_scale=3.0,
        )

        self.sidebar_body.controls.extend([
            self.description_tf,

            #ft.Row([    # Label Notes
                #ft.Text(f"\tNotes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)), 
                #ft.IconButton(      # Create new notes button
                    #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    #self.data.get('color', ft.Colors.PRIMARY),
                    #mouse_cursor=ft.MouseCursor.CLICK,
                #)
            #], spacing=0),

            #ft.Container(notes_column, margin=ft.Margin.symmetric(horizontal=20)),
        ])

        
        # Set up our main conent
        self.content = ft.Stack([
            ft.Row([interactive_viewer, self.sidebar], spacing=0, expand=True),
            self.show_sidebar_button, 
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)



        
               
    



        