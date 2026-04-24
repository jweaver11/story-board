''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_field import TextField
    

class ComicPreview(Widget):

    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict = None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      # Title of the note
            page = page,                        # Grabs our original page for convenience and consistency
            directory_path = directory_path,    # Path to our notes json file
            story = story,                      # Reference to our story object
            data = data,
            is_rebuilt = is_rebuilt
        )


        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_comic_preview", 
                'tag': "comic_preview",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_comic_preview_color', "primary"),
                'pin_location': app.settings.data.get('default_comic_preview_pin_location', "right") if data is None else data.get('pin_location', "right"),   # Default pin location for notes
                'preview_direction': "vertical",    # Default direction for comic preview, can be vertical or horizontal
                'snapshots': [],                      # List to hold our snapshots of the canvases. Also allows png uploads
            
            },
        )

        #self.body_container.padding = ft.Padding.only(left=16, top=16, bottom=16)
        

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init


    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: 
        # Add canvases or independent images to the snapshots 
        # Ability to reorder and delete the images in small column on the left

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        body = ft.Column() if self.data.get('preview_direction', "vertical") == "vertical" else ft.Row()
        

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = body
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        