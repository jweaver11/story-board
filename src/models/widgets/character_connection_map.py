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
    

        


        

        # Requires all widgets to be loaded first, so story calls reload_widget first
        if self.visible:
            self.reload_widget()
    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: 
        # PURPOSE: To show a character connection map of our characters and their connections to one another
        # character_bank = show all characters in the story not included (dragged out) onto the map already
        # Inside the character bank, they are a draggable. Inside the stack, they are a gd. (their draggable dragging content is the gd). 
        # When dragged left less than 200 px, remove from stack and add to char bank


    
        

        # Starts highlighting the character bank
        async def highlight_character_bank(e: ft.Event[ft.Draggable]=None):
            ''' Highlights the character bank when we hover over a character on the map, so we can see the other characters we can connect to '''
            if highlight_container.bgcolor != ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE) and self.is_dragging:
                highlight_container.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
                highlight_container.update()
                self.is_dragging = True

        # Stops highlighting the character bank and lets us know we dragged a character from the bank onto the map
        async def stop_highlight_character_bank(e: ft.Event[ft.Draggable]=None):
            ''' Stops highlighting the character bank when we stop hovering over a character on the map '''
            highlight_container.bgcolor = ft.Colors.TRANSPARENT
            highlight_container.update()
            #print(e)

        

        

               
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

        # What we need:
        # scrollable column to hold all unused characters
        # Ability to drag characters from that column onto the map
        # Ability to drag characters from map back to column
        # Ability to drag characters around on the map to rearrange them, with lines following them as we move them
        


        async def _drag_start(e: ft.Event[ft.Draggable]):
            ''' When we start dragging a character, we want to highlight the character bank so we can see where to drag it '''
            self.is_dragging = True
            await highlight_character_bank()
            #print("Drag start")

        async def _drag_end(e: ft.DragTargetEvent):
            ''' When we stop dragging a character, we want to check if we dragged it onto the map or back to the bank, and update our data accordingly '''
            self.is_dragging = False
            await stop_highlight_character_bank()
            print(e)

        


        # Where we add the characters so we can drag them ont the map
        character_bank = ft.Column([
            ft.Container(height=1),
            ft.Text("\tCharacter Bank", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
        ] +
            # Our characters
            [ft.Draggable(
                ft.Container(height=100, width=100, bgcolor=ft.Colors.RED), 
                on_drag_start=_drag_start,
                content_when_dragging=ft.Container(height=100, width=100, bgcolor=ft.Colors.TRANSPARENT),
            ) for i in range(20)
                 
        ], width=150, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START,)

        

        # Container holder bank trigger used for highlighting
        highlight_container = ft.Container(
            character_bank, width=152,
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.Border.only(right=ft.BorderSide(2, ft.Colors.OUTLINE)),
            alignment=ft.Alignment.TOP_CENTER, 
        )

        
        connections_stack = ft.Stack([
            ft.Container(expand=True, ignore_interactions=True, border=ft.Border.all(2, ft.Colors.RED)),    # Container to stay expanded (Add bg here)
            ft.GestureDetector(
                highlight_container,
                on_enter=highlight_character_bank, 
                on_exit=stop_highlight_character_bank,
                #on_hover=print_pos,
            ),
            
            
            #ft.TransparentPointer(canvas),
            ft.DragTarget(ft.TransparentPointer(canvas), expand=True, on_accept=_drag_end)
            
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
            


