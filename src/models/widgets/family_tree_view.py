'''
Class for showing all our characters laidd out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from handlers.verify_data import verify_data



class Character(Widget):
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
                'tag': "character",
                
            },
        )
        
        self.icon = ft.Icon(ft.Icons.PERSON, size=100, expand=False)    # Icon of character

        # Build our widget on start, but just reloads it later
        self.reload_widget()
    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: Show filters at top for our characters to show
        # PURPOSE: To show a family tree view of our characters and their connections to one another

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
                
                ]
            )

        )     
        
        # Set our content to the body_container (from Widget class) as the body we just built
        self.body_container.controls.clear()
        self.body_container.controls.append(body)

        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


