''' Class for the Notes widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from handlers.verify_data import verify_data
from styles.menu_option_style import Menu_Option_Style
    

class Note(Widget):

    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict = None):

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      # Title of the note
            page = page,                        # Grabs our original page for convenience and consistency
            directory_path = directory_path,    # Path to our notes json file
            story = story,                      # Reference to our story object
            data = data,
        )

        # Verifies this object has the required data fields, and creates them if not.
        # If the fields exist already, they will be skipped. Example, loaded notes have the "note" tag, so that would be skipped
        # If you provide default types, it gives it default values, otherwise you can specify values
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                'tag': "note",             # Tag to identify what type of object this is
                'pin_location': "right" if data is None else data.get('pin_location', "right"),   # Default pin location for notes
                'character_count': int,
                'created_at': str,
                'last_modified': str,
                'content': str
            },
        )

        
        # Load our widget UI on start after we have loaded our data
        self.reload_widget()

    # Called when right clicking our controls for either timeline or an arc
    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            Menu_Option_Style(
                #on_click=self.rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            # Color changing popup menu
            Menu_Option_Style(
                content=ft.PopupMenuButton(
                    expand=True,
                    tooltip="",
                    padding=None,
                    content=ft.Row(
                        expand=True,
                        controls=[
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=ft.Colors.PRIMARY),
                            ft.Text("Color", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True), 
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN_OUTLINED, color=ft.Colors.ON_SURFACE, size=16),
                        ]
                    ),
                    items=self.get_color_options()
                )
            ),
        ]


    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()
        
        # Body of the tab, which is the content of flet container
        body = ft.TextField(
            expand=True,
            multiline=True,
            value=self.data.get('content', ''),
        )

        # Assign the body_container content as whatever view you have built in the widget
        self.body_container.content = body
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        