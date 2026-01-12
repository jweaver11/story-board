'''
Most model classes really container 2 models: the character model itself and the associated widget model.
Inside of the 'data' dict, we store our characters model for the manipulative data...
the app will change. Everything else is built upon program launch so we can display it in the UI.
'''

import flet as ft
import os
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app



# Sets our Character as an extended Widget object, which is a subclass of a flet Container
# Widget requires a title, tag, page reference, and a pin location
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
                # Widget data
                'tag': "character",
                'pin_location': "left" if data is None else data.get('pin_location', "left"),     # Start our characters on the left pin
                'color': app.settings.data.get('default_character_color'),
                'edit_mode': bool,  # Whether we are in edit mode or not


                # Character specific data
                'character_data': {
                    'Prefix': str, # Prefix for their name (sir, mr, etc.)
                    'Role': "None",   # Importance of character in the story. main, side, background, uncategorized
                    'Morality': str,  # Lawful, netural, chaotic all have good, neutral, evil (9 alignments)
                    'Age': str, # Age of the character
                    'Nationality': str, # Where character is from

                    'Physical Description': {
                        'Species': str,
                        'Sex': str,     # Biology of the character. Has add option
                        'Race': str,    # Race of the character. Has add option
                        'Skin Color': str,
                        'Hair Color': str,   
                        'Eye Color': str,    
                        'Height': str,   
                        'Weight': str,   
                        'Build': str,    
                        'Distinguishing Features': str,  
                    },
                    
                    'Family':  { #TODO "connections" dropdown+tree/detective view?
                        'Love Interest': str,    
                        'Father': str,   
                        'Mother': str,    
                        'Siblings': str,
                        'Children': str,
                        'Ancestors': str,
                    },   
                    'origin': {     
                        'birth_date': str,   
                        'hometown': str,     
                        'education': str,        
                    },
                    'strengths': list,
                    'weaknesses': list,
                    'occupation': str,
                    'goals': str,
                    'personality': str,
                    'abilities': list,
                    'deceased': bool,    # Defaults to false
                    'connections': {
                        #TODO list of other characters and relationship types
                    },
                    'custom_fields': dict       # Anything the user wants to add on their own
                    # custom fields {key: {label: str, value: str}, key2: {label: str, value: str} ... }
                }
            },
        )
        
        self.icon = ft.Icon(ft.Icons.PERSON, size=100, expand=False),
        
        self.custom_field_controls = {}  # Store references to custom field TextFields

        # Build our widget on start, but just reloads it later
        self.reload_widget()


    # Called when user wants to create a new text field in character
    def new_custom_textfield_clicked(self, e):
        ''' Handles prompting user for custom textfield name and creating it '''

        def close_dialog(e):
            '''Close the dialog'''
            dlg.open = False
            self.p.update()

        def create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            try:
                field_name = field_name_input.value.strip()
                
                if not field_name:
                    close_dialog(None)
                    return  # Don't create if empty
                
                # Add the field to data if it doesn't exist
                if field_name not in self.data['custom_fields']:
                    self.data['custom_fields'][field_name] = ""
                
                # Save and reload
                self.save_dict()
                self.reload_widget()
                
                # Close dialog
                self.p.close(dlg)
            except Exception as ex:
                print(f"Error creating custom field: {ex}")
                close_dialog(None)

        # Create a dialog to ask for the field name
        field_name_input = ft.TextField(
            label="Field Name",
            hint_text="e.g., Notes, Hobbies, etc.",
            autofocus=True,
            on_submit=create_field,     # Closes the overlay when submitting
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text("Create New Custom Field"),
            content=field_name_input,
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Create", on_click=create_field),
            ],
        )
        
        try:
            dlg.open = True
            self.p.open(dlg)

        except Exception as ex:
            print(f"Error opening dialog: {ex}") 

    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename, delete
        return [
            MenuOptionStyle(
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
            MenuOptionStyle(
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
    
    

    
    
    def _on_custom_field_change(self, field_name: str, value: str):
        '''Called when a custom field is modified'''
        self.data['custom_fields'][field_name] = value
        self.save_dict()
    
    def _on_field_change(self, field_name: str, value: str):
        '''Generic handler for any field change - saves to data and persists'''
        self.data[field_name] = value
        self.save_dict()
    
    def _on_race_change(self, field_name: str, value: str):
        '''Handler for race field which is nested in physical_description'''
        self.data['physical_description']['Race'] = value
        self.save_dict()

    def _ensure_connections_list(self):
        '''Normalize connections into a list stored at self.data['connections'].'''
        try:
            conn = self.data.get('connections')
            if isinstance(conn, list):
                return
            if isinstance(conn, dict):
                # Try extract reasonable string entries from dict
                extracted = []
                for k, v in conn.items():
                    if isinstance(v, str) and v:
                        extracted.append(v)
                    elif isinstance(k, str) and k:
                        extracted.append(k)
                self.data['connections'] = extracted
                return
            # Any other type, replace with empty list
            self.data['connections'] = []
        except Exception:
            self.data['connections'] = []

    def _on_add_connection(self, value: str):
        '''Add a selected character name to connections (if not present) and persist.'''
        try:
            if not value:
                return
            self._ensure_connections_list()
            if value in self.data['connections']:
                return
            self.data['connections'].append(value)
            self.save_dict()
            # Rebuild UI so the dropdown options exclude the added entry
            self.reload_widget()
        except Exception as e:
            print(f"Error adding connection: {e}")

    def _on_remove_connection(self, name: str):
        '''Remove an existing connection and persist.'''
        try:
            self._ensure_connections_list()
            if name in self.data['connections']:
                self.data['connections'].remove(name)
                self.save_dict()
                self.reload_widget()
        except Exception as e:
            print(f"Error removing connection: {e}")

    # CORY NOTES:
    # Added edit mode clicked function to toggle edit mode on or off
    # Always use reload widget to simplify UI rebuilding when needed. Let the reload widget handle the differences

    # Called when clicking the edit mode button
    def _edit_mode_clicked(self, e=None):
        ''' Switches between edit mode and not for the character '''

        #print("Switching to edit mode for character:", self.title)

        # Change our edit mode data flag, and save it to file
        self.data['edit_mode'] = not self.data['edit_mode']
        self.save_dict()

        # Reload the widget. The reload widget should load differently depending on if we're in edit mode or not
        self.reload_widget()

    # Called if our widget is in edit view. 
    def _edit_mode_view(self):
        ''' Returns our character data with input capabilities '''

        body = ft.Column([
            ft.Row([
                self.icon,
                ft.IconButton(tooltip="Exit Edit Mode", icon=ft.Icons.EDIT_OFF_OUTLINED, on_click=self._edit_mode_clicked),
                ft.Divider(color="transparent"),    # Used as new line
            ], wrap=True),
        ])

        data_row = ft.Row(wrap=True)

        # Run through all our data and add it to the widget
        for key, value in self.data['character_data'].items():

            if key == "prefix":
                data_row.controls.append(
                    ft.TextField(
                        value.capitalize(), label="Prefix", dense=True, multiline=False,
                        capitalization=ft.TextCapitalization.WORDS, adaptive=True, width=70,
                        on_change=lambda e, k=key: self._on_field_change(k, e.control.value),
                    )
                )

            # Fields we want to manage ourselfs
            elif key == "role":
                data_row.controls.append(
                    ft.Dropdown(
                        label="Role", dense=True,
                        options=[
                            ft.dropdown.Option("main", "Main"),
                            ft.dropdown.Option("side", "Side"),
                            ft.dropdown.Option("background", "Background"),
                            ft.dropdown.Option("none", "None"),
                        ],
                        value=value,
                        on_change=lambda e, k=key: self._on_field_change(k, e.control.value),
                    )
                )

            elif key == "morality":
                data_row.controls.append(
                    ft.Dropdown(
                        label="Morality", dense=True,
                        options=[
                            ft.dropdown.Option("Lawful Good", content=ft.Text("Lawful Good", color="green")),
                            ft.dropdown.Option("Lawful Neutral", "Lawful Neutral"),
                            ft.dropdown.Option("Lawful Evil", content=ft.Text("Lawful Evil", color="red")),
                            ft.dropdown.Option("Neutral Good", content=ft.Text("Neutral Good", color="green")),
                            ft.dropdown.Option("Neutral Evil", content=ft.Text("Neutral Evil", color="red")),
                            ft.dropdown.Option("Chaotic Good", content=ft.Text("Chaotic Good", color="green")),
                            ft.dropdown.Option("Chaotic Neutral", "Chaotic Neutral"),
                            ft.dropdown.Option("Chaotic Evil", content=ft.Text("Chaotic Evil", color="red")),
                        ],
                        value=value,
                        on_change=lambda e, k=key: self._on_field_change(k, e.control.value),
                    )
                )

            elif key == "age":
                data_row.controls.append(
                    ft.TextField(
                        value.capitalize(), label="Age", dense=True, multiline=False,
                        capitalization=ft.TextCapitalization.WORDS, adaptive=True, width=70,
                        on_change=lambda e, k=key: self._on_field_change(k, e.control.value),
                    )
                )

            # All other fields that can be auto added to the widget
            elif isinstance(value, str):
                #data_row.controls.append(ft.Row([ft.Text(f"{key.capitalize()}: ", weight=ft.FontWeight.BOLD), ft.Text(value)], wrap=True))
                data_row.controls.append(
                    ft.TextField(
                        value.capitalize(), label=key.capitalize(), dense=True, multiline=True,
                        capitalization=ft.TextCapitalization.SENTENCES, adaptive=True, width=200,
                        on_change=lambda e, k=key: self._on_field_change(k, e.control.value),
                    )
                )
                
            elif isinstance(value, int) and value:
                data_row.controls.append(ft.Row([ft.Text(f"{key.capitalize()}: ", weight=ft.FontWeight.BOLD), ft.Text(str(value))], wrap=True))

        body.controls.append(data_row)

        self.body_container.content = body

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self): #this is the edit view currently
        ''' Reloads/Rebuilds our widget based on current data '''
        
        # Rebuild out tab to reflect any changes
        self.reload_tab()

        if self.data['is_active_tab']:
            self.icon = ft.Icon(ft.Icons.PERSON, size=100, color=self.data.get('color', "primary"), expand=False)
        else:
            self.icon = ft.Icon(ft.Icons.PERSON_OUTLINE, size=100, color=self.data.get('color', "primary"), expand=False)
        

        # Check if we're in edit mode or not. If yes, build the edit view like this
        if self.data.get('edit_mode', False):
            self._edit_mode_view()
            self._render_widget()


        # If NOT in edit mode, build our normal view
        else:

            body = ft.Column([
                ft.Row([
                    self.icon,
                    ft.IconButton(tooltip="Edit Mode", icon=ft.Icons.EDIT_OUTLINED, on_click=self._edit_mode_clicked),
                    ft.Divider(color="transparent"),    # Used as new line
                ], wrap=True),
            ])

            data_row = ft.Row(wrap=True)

            # Run through all our data and add it to the widget
            for key, value in self.data['character_data'].items():

                # All other fields that can be auto added to the widget. Check to make sure not empty
                if isinstance(value, str) or isinstance(value, int):
                    if app.settings.data.get('show_empty_character_fields', True):
                        data_row.controls.append(ft.Row([ft.Text(f"{key.capitalize()}: ", weight=ft.FontWeight.BOLD), ft.Text(str(value))], wrap=True))
                    elif not value:
                        continue
                      
                elif isinstance(value, bool):
                    data_row.controls.append(ft.Row([ft.Text(f"{key.capitalize()}: ", weight=ft.FontWeight.BOLD), ft.Text("Yes" if value else "No")], wrap=True))

                # Role
                # Morality
                # Sex 
                # age
                # Nationality
                # Physical Description {}
                # Family {}
                # Origin {}
                # Strengths []
                # Weaknesses []
                # Occupation
                # Goals
                # Personality
                # Abilities
                # is dead
                # Connections {}
                # Custom fields {}

            body.controls.append(data_row)
        
            self.body_container.content = body

            # Call render widget (from Widget class) to update the UI
            self._render_widget()