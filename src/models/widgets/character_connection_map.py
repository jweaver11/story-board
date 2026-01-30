'''
Class for showing all our characters laid out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.app import app

# TODO: Should allow user to pick primary character(s) that will build the map around
# Edit view or not. Show characters on the map as nodes that can add connection to other characters
# Add label to the connection type. Allow changable symbols, colors, styles, etc
class CharacterConnectionMap(Widget):
    # Constructor
    def __init__(self, name: str, page: ft.Page, directory_path: str, story: Story, data: dict=None):

        # Parent class constructor
        super().__init__(
            title = name,  
            page = page,   
            directory_path = directory_path, 
            story = story,   
            data = data,    
        )

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                # Widget data
                'tag': "character_connection_map",
                'color': app.settings.data.get('default_character_connection_map_color'),
                
                'primary_characters': list,    # List of primary characters to build the map around
            },
        )
        
        self.icon = ft.Icon(ft.Icons.PERSON, size=100, expand=False)    # Icon of character

        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init
    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: Show filters at top for our characters to show
        # PURPOSE: To show a family tree view of our characters and their connections to one another
        # HAS Family view
        # Has primary user, and all connections to them, and option to expand and show secondary connections (connections of their connections)

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        if self.data['is_active_tab']:
            self.icon = ft.Icon(ft.Icons.PERSON, size=100, color="primary", expand=False)
        else:
            self.icon = ft.Icon(ft.Icons.PERSON_OUTLINE, size=100, color="disabled", expand=False)



        # Body of the tab, which is the content of flet container
        body = ft.Container(
            expand=True,                # Takes up maximum space allowed in its parent container
            padding=6,                  # Padding around everything inside the container
            content=ft.Column([                 # The column that will hold all our stuff top down
                self.icon,                          # The icon above the name
                ft.Text("hi from " + self.title),           # Text that shows the title
                
            ])
        )     
        
        # Set our content to the body_container (from Widget class) as the body we just built
        self.body_container.content = body

        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


