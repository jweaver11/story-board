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
from utils.safe_string_checker import return_safe_name
from models.dataclasses.character_template import default_character_template_data_dict



# Sets our Character as an extended Widget object, which is a subclass of a flet Container
# Widget requires a title, tag, page reference, and a pin location
class Character(Widget):
    # Constructor
    def __init__(self, name: str, page: ft.Page, directory_path: str, story: Story, data: dict=None, ):

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
                'edit_mode': True,  # Whether we are in edit mode or not


                # Character specific data. If we're using a template, this will already be passed in with our data
                'character_data': default_character_template_data_dict()
            },
        )
        
        self.icon = ft.Icon(ft.Icons.PERSON, size=100, expand=False),
        
        self.custom_field_controls = {}  # Store references to custom field TextFields

        # Build our widget on start, but just reloads it later
        self.reload_widget()


    # Called when user wants to create a new text field in character
    def _new_custom_textfield_clicked(self, e):
        ''' Handles prompting user for custom textfield name and creating it '''

        def create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            try:
                field_name = return_safe_name(field_name_input.value)

                print("Safe field name: ", field_name)
                
                if not field_name:
                    self.p.close(dlg)
                    return  # Don't create if empty
                
                # Add the field to data if it doesn't exist
                if field_name not in self.data['character_data']['Custom Fields']:
                    self.data['character_data']['Custom Fields'][field_name] = ""
                
                # Save and reload
                self.save_dict()
                self.p.close(dlg)
                self.reload_widget()
                                
            except Exception as ex:
                print(f"Error creating custom field: {ex}")
                self.p.close(dlg)

        # Create a dialog to ask for the field name
        field_name_input = ft.TextField(
            label="Field Name", hint_text="Notes, Hobbies, Pets, etc.",
            autofocus=True, capitalization=ft.TextCapitalization.SENTENCES,
            on_submit=create_field,     # Closes the overlay when submitting
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text("Create New Custom Field"),
            content=field_name_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.close(dlg)),
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
    
    

    
    # Called when a field is changed in edit mode
    def _update_character_data(self, sub_key: str="", **kwargs):
        ''' Updates the character data dict or up to one sub dict '''

        for key, value in kwargs.items():
            #print("Updating field:", key, "to value:", value)
            if sub_key != "":
                self.data['character_data'][sub_key][key] = value
            else:
                self.data['character_data'][key] = value
                
        self.save_dict()

    def _delete_custom_field_clicked(self, field_name: str):
        ''' Handles deleting a custom text field from character '''

        try:
            if field_name in self.data['character_data']['Custom Fields']:
                del self.data['character_data']['Custom Fields'][field_name]
                self.save_dict()
                self.reload_widget()
        except Exception as e:
            print(f"Error deleting custom field: {e}")

    
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

        # Change our edit mode data flag, and save it to file
        self.data['edit_mode'] = not self.data['edit_mode']
        self.save_dict()

        # Reload the widget. The reload widget should load differently depending on if we're in edit mode or not
        self.reload_widget()

    # Called if our widget is in edit view. 
    def _edit_mode_view(self):
        ''' Returns our character data with input capabilities '''

        # Column we will append to for the bot of our view. Has our icon, and exit edit mode button
        # TODO: Foreground decoration when hovering adds the ("upload image" button)
        body = ft.Column([
            ft.Row([
                self.icon,
                ft.IconButton(tooltip="Exit Edit Mode", icon=ft.Icons.EDIT_OFF_OUTLINED, on_click=self._edit_mode_clicked),
                ft.Divider(color="transparent"),    # Used as new line
            ], wrap=True),
        ], scroll="auto", expand=True)

        body.controls.append(ft.TextField(
            self.data.get('character_data', {}).get('Summary', ""), label="Summary", dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES, adaptive=True, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            on_blur=lambda e: self._update_character_data(**{"Summary": e.control.value}),
        ))

        # Proceduarally go through all character_data that is not custom fields and add them to edit view

        body.controls.append(
            ft.Row([
                ft.Dropdown(
                    label="Role", dense=True, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    options=[
                        ft.dropdown.Option("Main"), ft.dropdown.Option("Side"),
                        ft.dropdown.Option("Background"), ft.dropdown.Option("None"),
                    ],
                    value=self.data.get('character_data', {}).get('Role', "None"),
                    on_change=lambda e: self._update_character_data(**{"Role": e.control.value}),
                ),
                ft.Dropdown(
                    label="Morality", dense=True, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    options=[
                        ft.dropdown.Option("Lawful Good"),
                        ft.dropdown.Option("Lawful Neutral"),
                        ft.dropdown.Option("Lawful Evil"),
                        ft.dropdown.Option("Neutral Good"),
                        ft.dropdown.Option("Neutral Evil"),
                        ft.dropdown.Option("Chaotic Good"),
                        ft.dropdown.Option("Chaotic Neutral"),
                        ft.dropdown.Option("Chaotic Evil"),
                    ],
                    value=self.data.get('character_data', {}).get('Morality', ""),
                    on_change=lambda e: self._update_character_data(**{"Morality": e.control.value}),
                )
            ], wrap=True)
        )

        body.controls.append(
            ft.Row([
                ft.TextField(
                    self.data.get('character_data', {}).get('Age', "").capitalize(), label="Age", dense=True, multiline=True, expand=True,
                    capitalization=ft.TextCapitalization.WORDS, adaptive=True, input_filter=ft.NumbersOnlyInputFilter(),
                    on_blur=lambda e: self._update_character_data(**{"Age": str(e.control.value)}), text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                ),
                ft.TextField(
                    self.data.get('character_data', {}).get('Prefix', "").capitalize(), label="Prefix", dense=True, multiline=True,
                    capitalization=ft.TextCapitalization.WORDS, adaptive=True, expand=True, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    on_blur=lambda e: self._update_character_data(**{"Prefix": e.control.value}),
                ),
            ])
        )

        body.controls.append(
            ft.Row([
                ft.TextField(
                    self.data.get('character_data', {}).get('Nationality', "").capitalize(), label="Nationality", dense=True, 
                    capitalization=ft.TextCapitalization.WORDS, adaptive=True, expand=True, multiline=True,
                    on_blur=lambda e: self._update_character_data(**{"Nationality": e.control.value}), text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                ),
                ft.TextField(
                    self.data.get('character_data', {}).get('Occupation', "").capitalize(), label="Occupation", dense=True, multiline=True,
                    capitalization=ft.TextCapitalization.WORDS, adaptive=True, expand=True, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    on_blur=lambda e: self._update_character_data(**{"Occupation": e.control.value}),
                ),
            ])
        )

        # Goals Expansion Tile
        goals = ft.ExpansionTile(
            ft.Text("Goals", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)), 
            shape=ft.RoundedRectangleBorder(), initially_expanded=True, dense=True,
            controls_padding=ft.padding.only(left=10,top=6), controls=[ft.Column(spacing=4)]
        )

        # Called when submitting a new goal via the button or submitting textfield
        def _submit_new_goal(e=None):
            '''Handles adding a new goal when user submits the new goal text field.'''
            new_goal = new_goal_textfield.value.strip()
            if not new_goal:
                return
            current_goals = self.data.get('character_data', {}).get('Goals', [])
            updated_goals = current_goals + [new_goal]
            self._update_character_data(**{"Goals": updated_goals})
            self.reload_widget()

        # Called when deleting goal by clicking the delete button to right of it
        def _delete_goal(i: int):
            '''Handles deleting a goal at index i.'''
            current_goals = self.data.get('character_data', {}).get('Goals', [])
            if 0 <= i < len(current_goals):
                updated_goals = current_goals[:i] + current_goals[i+1:]
                self._update_character_data(**{"Goals": updated_goals})
                self.reload_widget()

        # Go through our goals and create textfields for each one
        for index, value in enumerate(self.data.get('character_data', {}).get('Goals', [])):
            goals.controls[0].controls.append(
                ft.Row([
                    ft.TextField(
                        value, dense=True, multiline=True, expand=True,
                        capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                        on_blur=lambda e, i=index: self._update_character_data(**{"Goals": self.data['character_data']['Goals'][:i] + [e.control.value] + self.data['character_data']['Goals'][i+1:]}),
                    ),
                    ft.IconButton(
                        tooltip="Delete Goal", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,   
                        on_click=lambda e, i=index: _delete_goal(i)
                    )
                ])
            )

        # Create a new textfield and add button for adding new goals
        new_goal_textfield = ft.TextField(
            label="New Goal", dense=True, expand=True, 
            adaptive=True, capitalization=ft.TextCapitalization.SENTENCES, on_submit=_submit_new_goal
        )
        goals.controls[0].controls.append(
            ft.Row([
                new_goal_textfield,
                ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="Add Goal", on_click=_submit_new_goal),
            ])
        )

        # Add our goals
        body.controls.append(goals)

        # Give us a divider before custom fields and add a label
        body.controls.append(ft.Divider())
        body.controls.append(
            ft.Row([
                ft.Text("Custom Fields:", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), text_align=ft.TextAlign.CENTER),
                ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=self._new_custom_textfield_clicked),
            ])
        )

        for key, value in self.data.get('character_data', {}).get('Custom Fields', {}).items():
            body.controls.append(
                ft.Row([
                    ft.TextField(
                        value, label=key, dense=True, multiline=True, expand=True,
                        capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                        on_blur=lambda e, k=key: self._update_character_data("Custom Fields", **{k: e.control.value}),
                    ),
                    ft.IconButton(
                        tooltip="Delete Field", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,   
                        on_click=lambda e, k=key: self._delete_custom_field_clicked(k)
                    ),
                ])
            )
                


        


        # Role ^
        # Morality ^
        # Age ^
        # Prefix ^
        # Nationality ^ 
        # Nationality ^
        # Occupation ^
        # Goals ^
        # Abilities - Add to Shonen template
        # Physical Description {}
        # Family {}
        # Origin {}
        # Strengths []
        # Weaknesses []
        # Personality
        # Connections {}
        # Custom fields {}
                
        

        # Run through all our data and add it to the widget
        for key, value in self.data.get('character_data', {}).get('custom_fields', {}).items():

            # All other fields that can be auto added to the widget
            if isinstance(value, str):
                #data_row.controls.append(ft.Row([ft.Text(f"{key.capitalize()}: ", weight=ft.FontWeight.BOLD), ft.Text(value)], wrap=True))
                body.controls.append(
                    ft.TextField(
                        value.capitalize(), label=key.capitalize(), dense=True, multiline=True,
                        capitalization=ft.TextCapitalization.SENTENCES, adaptive=True, width=200,
                        on_change=lambda e, k=key: self._update_character_data(k, e.control.value),
                    )
                )
                
            elif isinstance(value, int) and value:
                body.controls.append(ft.Row([ft.Text(f"{key.capitalize()}: ", weight=ft.FontWeight.BOLD), ft.Text(str(value))], wrap=True))

        #body.controls.append(data_row)

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