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
                'show_secondary_connections': bool,     # Whether to show connections of connections
                'primary_characters': list,    # List of primary characters to build the map around[char_key, char_key]
            },
        )
    

        self.primary_characters = []

        self.canvas = cv.Canvas(
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK, 
                expand=True,
                on_secondary_tap=lambda e: self.story.open_menu(self._get_menu_options()),
                on_hover=self._get_coords,
                drag_interval=10, hover_interval=20,
            ),
            expand=True, resize_interval=100,
            #on_resize=self._rebuild_canvas, 
        )


        # Our stack for map locations
        self.connections_stack = ft.Stack([
            ft.Container(expand=True, ignore_interactions=True),    # Container to stay expanded (Add bg here)
            self.canvas,
        ], expand=True)

        # Requires all widgets to be loaded first, so story calls self.load_primary_characters(), which reloads the widget
        if self.visible:
            self.reload_widget()

    # Load our primary characters from our data. Then loads the connection mini widgets for each connection involving them
    def _load_primary_characters(self):
        ''' Loads our primary characters from our data '''

        self.primary_characters.clear()
        self.mini_widgets.clear()

        # Go through our primary characters and load them
        for char_key in self.data.get('primary_characters', []):
            character = self.story.characters.get(char_key)
            if character:
                # Add their live object to our primary characters list
                self.primary_characters.append(character)  

        # Now go through our story connections and see which ones involve our primary characters
        for idx, conn_data in enumerate(self.story.data.get('connections', [])):
            if conn_data.get('char1_key') in self.data.get('primary_characters', []) or conn_data.get('char2_key') in self.data.get('primary_characters', []):
                # Create a mini widget for this connection
                mw = CharacterConnection(
                    title="NONE",       # Not used but needs a value
                    widget=self,
                    page=self.p,
                    index=idx,
                    data=conn_data,  
                )
                self.mini_widgets.append(mw) 
                

    # Called when app clicks the hide icon in the tab
    def toggle_visibility(self, e=None, value: bool=None):
        ''' Hides the widget from our workspace and updates the json to reflect the change '''

        # If we want to specify we're visible or not, we can pass it in
        if value is not None:
            self.data['visible'] = value
            self.visible = value
        
        else:
            # Change our visibility data, save it, then apply it
            self.data['visible'] = not self.data['visible']
            self.visible = self.data['visible']

        #if self.visible:
            #self.load_primary_characters()   # Load our primary characters when we become visible

        # Save our changes and reload the UI
        self.save_dict()
        self.reload_widget()


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

            self.data.get('primary_characters').clear()     # Clear current primary characters

            # Go through our checkboxes, and see which characters were selected and add them to our data
            for control in content.controls:
                if isinstance(control, CharCheckbox):
                    if control.value:
                        self.data.get('primary_characters').append(control.character.data.get('key'))
                    

            # Save and reload our widget. Close the dialog
            self.save_dict()
            
            self.reload_widget()
            self.p.pop_dialog()


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
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR), scale=1.2),
                ft.Container(width=12),   # Spacer
                ft.TextButton("Save", on_click=_save_and_close, scale=1.2),
            ],
        )
        
        self.p.show_dialog(dlg)        # open the dialog
    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # PURPOSE: To show a character connection map of our characters and their connections to one another
        # Has primary user(s), and all connections to them, 
        # and option to expand and show secondary connections (connections of their connections)

        # Rebuild out tab to reflect any changes
        self._load_primary_characters()
        self.reload_tab()

         

        # Clear our map stack controls so we can re-add them
        self.connections_stack.controls.clear()
        self.connections_stack.controls = [     # Add our background and canvas
            ft.Container(expand=True, ignore_interactions=True, border=ft.Border.all(2, "red")),    # Container to stay expanded (Add bg here)
            self.canvas,
        ]

        if not self.primary_characters:
            self.connections_stack.controls.append(
                ft.Container(
                    expand=True, alignment=ft.Alignment.CENTER,
                    content=ft.Button("Select Primary Character(s)", on_click=self._set_primary_characters, scale=2)
                )
            )

        else:
            standard_length = 150   # some fraction of self.w and self.h
            max_length = 300    # Some fraction of self.w and self.h // 2 - padding


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


        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


