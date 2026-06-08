'''
Class for showing all our characters laid out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.app import app
import flet.canvas as cv
from models.mini_widgets.character_connection import CharacterConnection

# Add label to the connection type. Allow changable symbols, colors, styles, etc
class CharacterConnectionMap(Widget):
    # Constructor
    def __init__(self, name: str, page: ft.Page, directory_path: str, story: Story, data: dict=None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Parent class constructor
        super().__init__(
            title = name,  
            page = page,   
            directory_path = directory_path, 
            story = story,   
            data = data,    
            is_rebuilt = is_rebuilt
        )

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                # Widget data
                'tag': "character_connection_map",
                'color': app.settings.data.get('default_character_connection_map_color'),
                'included_characters': {
                    #'char_key': (x, y) # position of the character on the map
                },
                'connections': [    # List of our connections
                    {
                        # char 1 key: str
                        # char 1 key: str
                        # description: str
                        # icon: str -- icon of the connection
                        # color: str  -- color of the drawn line and icon for the connection
                        # char1 position: tuple(x,y) -- position of the char1 icon on the map, relative to the center (0,0)
                        # char2 position: tuple(x,y) -- position of the char2 icon on the
                        
                    }
                ],  
            },
        )

        # State tracker for highlighting purposes
        self.is_dragging = False

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
    
        # State tracking
        self.source_character: str = None
        self.target_character: str = None

        


        

        # Requires all widgets to be loaded first, so story calls reload_widget first
        if self.visible:
            self.reload_widget()

    
    class CharacterNode(ft.GestureDetector):
        def __init__(self, char_key: str, position: tuple, parent_map: 'CharacterConnectionMap', color):
            super().__init__(
                content=ft.Container(width=50, height=50, bgcolor=ft.Colors.BLUE, border_radius=25),
                on_enter=self._highlight,
                on_exit=self._stop_highlight,
                #on_pan_start=self._start_drag,  ?
                #on_pan_end=self.
            )
            self.char_key = char_key
            self.position = position
            self.parent_map = parent_map
            self.color = color

        def _highlight(self, e):
            ''' When we hover over a character node, we want to highlight it and show its connections '''
            self.content.bgcolor = ft.Colors.CYAN
            self.content.shadow = ft.BoxShadow(8, 8, ft.Colors.with_opacity(0.6, self.color))
            self.update()

        def _stop_highlight(self, e):
            ''' When we stop hovering over a character node, we want to stop highlighting it '''
            self.content.bgcolor = ft.Colors.BLUE
            self.content.shadow = None
            self.update()
    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: 
        # PURPOSE: To show a character connection map of our characters and their connections to one another
        # Have checkmarks in a column on the left to add or remove characters from the map
        # Use canvas to draw lines between characters for their connections
        # Show info on the right for all connections so we can change color, desc, etc.

        async def draw_connections():
            pass


               
        self.reload_tab()
        

        # Canvas that shows the drawn lines between characters for their connections and icons
        canvas = cv.Canvas(
            content=ft.GestureDetector(
                expand=True,
                on_secondary_tap=lambda _: self.story.open_menu(self._get_menu_options()),
                on_hover=self._get_coords,
                #drag_interval=50, 
                hover_interval=20,
                #on_pan_start=lambda: print("Pan Started")
            ),
            expand=True, resize_interval=100,
            #on_resize=self._rebuild_canvas, 
        )
        
        
        connections_stack = ft.Stack([
            
            
            
            #ft.TransparentPointer(canvas),
            ft.DragTarget(ft.TransparentPointer(canvas), expand=True, on_accept=lambda e: print(e))
            
        ], expand=True, alignment=ft.Alignment.CENTER_LEFT) 

        # TODO: Go through connected characters and add their icons to the map
        # Go through the added character icons and draw the connections between them, with room for icons




        iv = ft.InteractiveViewer(
            content=connections_stack, expand=True,
            scale_factor=750, #boundary_margin=50,
            min_scale=0.5, max_scale=2.0, scale=1.0,
        )
        
        
        # Set our content to the body_container (from Widget class) as the body we just built
        #self.body_container.content = iv
        self.body_container.content = connections_stack
        #self.body_container.content = ft.Container(width=100, height=100, bgcolor=ft.Colors.RED)   # TESTING PURPOSES


        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


