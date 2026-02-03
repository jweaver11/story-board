'''
Class for showing all our characters laid out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.app import app
import flet.canvas as cv
from models.mini_widgets.ccm_information_display import CCMInformationDisplay

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
                
                'primary_characters': list,    # List of primary characters to build the map around[char_key, char_key]
            },
        )
        
        self.icon = ft.Icon(ft.Icons.PERSON, size=100, expand=False)    # Icon of character

        self.information_display: ft.Container = None
        self._create_information_display()

        self.primary_characters = []
        #self.load_primary_characters()

        self.canvas = cv.Canvas(
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, 
                expand=True,
                # Non-drawing event handlers
                on_secondary_tap=lambda e: self.story.open_menu(self._get_menu_options()),
                on_hover=self._get_coords,
                on_tap=self._show_info_display,
                drag_interval=10, hover_interval=20,
            ),
            expand=True, resize_interval=100,
            #on_resize=self._rebuild_map_canvas, 
        )

        # Our stack for map locations
        self.connections_stack = ft.Stack([
            ft.Container(expand=True, ignore_interactions=True),    # Container to stay expanded (Add bg here)
            self.canvas,
        ], expand=True)

        # Requires all widgets loaded first, so story calls self.load_primary_characters(), which reloads the widget
        #if self.visible:
            #self.reload_widget()

    def load_primary_characters(self):
        ''' Loads our primary characters from our data '''

        self.primary_characters.clear()
        for char_key in self.data.get('primary_characters', []):
            character = self.story.characters.get(char_key)
            if character:
                self.primary_characters.append(character)  

        # Make sure we're reloaded
        if self.visible:
            self.reload_widget()  

         

    # Called in the constructor
    def _create_information_display(self):
        ''' Creates our plotline information display mini widget '''
        
        self.information_display = CCMInformationDisplay(
            title=self.title,
            owner=self,
            page=self.p,
            key="none",     # Not used, but its required so just whatever works
            data=None,      # It uses our data, so we don't need to give it a copy that we would have to constantly maintain
        )
        # Add to our mini widgets so it shows up in the UI
        self.mini_widgets.append(self.information_display)

    # Called when clicking on our map to show our information display
    async def _show_info_display(self, e: ft.TapEvent):
        ''' If we're not in drawing mode, show our information display '''
        self.information_display.show_mini_widget()


    def _set_primary_characters(self, e=None):

        class CharCheckbox(ft.Checkbox):
            def __init__(self, character: Widget, is_selected: bool=False):
                super().__init__(
                    label=character.title,
                    value=is_selected,
                )
                self.character = character

        # Goes through and see what characters were selected and saves them
        def _save_and_close(e):

            # Go through the content column control. Any checkboxes get added/removed from primary characters
            for control in content.controls:
                if isinstance(control, CharCheckbox):
                    if control.value and control.character not in self.primary_characters:
                        self.primary_characters.append(control.character)
                    elif not control.value and control.character in self.primary_characters:
                        self.primary_characters.remove(control.character)

            # Save the new primary characters to data
            self.data.get('primary_characters').clear()
            for char in self.primary_characters:
                self.data.get('primary_characters').append(char.data.get('key'))

            # Save and reload our widget. Close the dialog
            self.save_dict()
            self.reload_widget()
            self.p.close(dlg)


        # Sets our content to add too
        content = ft.Column(
            [
                ft.Divider()
            ], 
            scroll="auto",
            width=self.p.width * .5,
        )
        
        # Go through all our characters and add a checkbox for each one. If they are already primary, have it checked
        for char in self.story.characters.values():
            if char.data.get('key') == self.data.get('key'):
                continue
            if char in self.primary_characters:
                content.controls.append(CharCheckbox(character=char, is_selected=True))
            else:
                content.controls.append(CharCheckbox(character=char))
            
        # Alert dialog to show everything we've built
        dlg = ft.AlertDialog(
            title=ft.Text(f"Select Primary Character(s)"),
            content=content,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                ft.TextButton("Save", on_click=_save_and_close),   # Start enabled to just save existing connections
            ],
        )
        
        self.p.open(dlg)        # open the dialog
    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # PURPOSE: To show a character connection map of our characters and their connections to one another
        # HAS Family view
        # Has primary user, and all connections to them, and option to expand and show secondary connections (connections of their connections)

        # Love interest -> Sides
        # Parents -> Up
        # Siblings -> Side
        # Children -> Down
        # Friends -> Side-Down diagonal

        # Rebuild out tab to reflect any changes
        self.reload_tab()

         

        # Clear our map stack controls so we can re-add them
        self.connections_stack.controls.clear()
        self.connections_stack.controls = [     # Add our background and canvas
            ft.Container(expand=True, ignore_interactions=True, border=ft.border.all(2, "red")),    # Container to stay expanded (Add bg here)
            self.canvas,
        ]

        if not self.primary_characters:
            self.connections_stack.controls.append(
                ft.Container(
                    expand=True, alignment=ft.alignment.center,
                    content=ft.Button("Select Primary Character(s)", on_click=self._set_primary_characters, scale=2)
                )
            )

        else:
            standard_length = 150   # Standard length for connection lines?


        iv = ft.InteractiveViewer(
            content=self.connections_stack, expand=True,
            scale_factor=750, boundary_margin=50,
            min_scale=0.5, max_scale=2.0, scale=1.0,
        )
        
        
        # Set our content to the body_container (from Widget class) as the body we just built
        self.body_container.content = iv


        button_title = "Primary Characters: "
        for idx, char in enumerate(self.primary_characters):
            if idx > 0:
                button_title += f" | {char.title}"
            else:
                button_title += char.title

        # Build a header for our filters
        self.header = ft.Row([ft.Button(button_title, tooltip="Change Primary Characters", on_click=self._set_primary_characters)], alignment=ft.MainAxisAlignment.CENTER, height=50)

        # Option to show secondary character connections??

        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


