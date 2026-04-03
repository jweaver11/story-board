# Charts for a story

''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_field import TextField
    

class Chart(Widget):

    # Constructor
    def __init__(
        self, 
        title: str, 
        page: ft.Page, 
        directory_path: str, 
        story: Story, 
        data: dict = None, 
        is_rebuilt: bool = False,
        type: str = "bar"           # Type of chart we are (either bar or radar)
    ):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      
            page = page,                        
            directory_path = directory_path,    
            story = story,                     
            data = data,
            is_rebuilt = is_rebuilt
        )
        

        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_chart", 
                'tag': "chart",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_chart_color'),
                'pin_location': app.settings.data.get('default_chart_pin_location', "right") if data is None else data.get('pin_location', "right"),   # Default pin location for items
                'type': type,             # Type of chart (bar or radar)
                #'edit_mode': True,      # Whether we are in edit mode or not
                'Description': str,

            },
        )

        if self.data.get('type', "") == "bar":
            self.icon.icon = ft.Icons.INSERT_CHART_OUTLINED
        else:
            self.icon.icon = ft.CupertinoIcons.COMPASS

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    def _bar_chart_view(self):
        ''' Builds out the body of our bar chart widget '''
        pass

    def _radar_chart_view(self):
        ''' Builds out the body of our radar chart widget '''
        pass

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        if self.data.get('type', "") == "bar":
            self._bar_chart_view()
        else:
            self._radar_chart_view()
        
        self.body_container.content = ft.Text("Chart: " + self.title, size=20)
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        