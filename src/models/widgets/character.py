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
from styles.colors import dark_gradient




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

        # Update our padding to be none on the right to handle scrollbars better
        self.padding = ft.padding.only(top=0, bottom=8, left=8, right=0)

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                # Widget data
                'tag': "character",
                'pin_location': "left" if data is None else data.get('pin_location', "left"),     # Start our characters on the left pin
                'color': app.settings.data.get('default_character_color'),
                'edit_mode': True,  # Whether we are in edit mode or not

                # If this dict doesn't exist, create it with our active template data. Otherwise
                'character_data': app.settings.data.get('character_templates', {}).get(app.settings.get('active_character_template', ""), default_character_template_data_dict()) if
                    data is None or 'character_data' not in data else data['character_data'],
            },
        )
        
        self.icon = ft.Icon(ft.Icons.PERSON, size=100, expand=False),
        
        self.custom_field_controls = {}  # Store references to custom field TextFields

        # Build our widget on start, but just reloads it later
        self.reload_widget()


    

    def _get_menu_options(self) -> list[ft.Control]:

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
    
    # Called when user wants to create a new text field in character
    def _new_custom_field_clicked(self, e):
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

    # Called when user wants to create a new text field in character
    def _new_connection_clicked(self, e):
        ''' Handles prompting user for custom textfield name and creating it '''

        def _create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            try:
                field_name = return_safe_name(field_name_input.value)

                print("Safe field name: ", field_name)
                
                if not field_name:
                    self.p.close(dlg)
                    return  # Don't create if empty
                
                # Add the field to data if it doesn't exist
                if field_name not in self.data['character_data']['Connections']:
                    self.data['character_data']['Connections'][field_name] = ""
                
                # Save and reload
                self.save_dict()
                self.p.close(dlg)
                self.reload_widget()
                                
            except Exception as ex:
                print(f"Error creating custom field: {ex}")
                self.p.close(dlg)


        def _character_options() -> list[ft.dropdown.Option]:
            '''Generate dropdown options for connections excluding already connected characters.'''
            options = []
            existing_connections = set(self.data.get('character_data', {}).get('Connections', {}).values())
            for story in app.stories.values():
                for character in story.characters.values():
                    if character.title != self.title and character.title not in existing_connections:
                        options.append(ft.dropdown.Option(character.title))
            return options

        # Create a dialog to ask for the field name
        field_name_input = ft.Dropdown(
            value="Selected Character", hint_text="Character Name",
            options=_character_options(), expand=True
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Create a New Connection to {self.title}"),
            content=field_name_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.close(dlg)),
                ft.TextButton("Create", on_click=_create_field),
            ],
        )
        
        try:
            dlg.open = True
            self.p.open(dlg)

        except Exception as ex:
            print(f"Error opening dialog: {ex}") 
    

    
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

        # Check if we're sorting by the updated key, and if characters rail is selected. If it is, reload the rail
        sort_method = self.story.data.get('settings', {}).get('character_rail_sort_by', "Role")
        if sort_method == key and self.story.data.get('selected_rail', "") == "characters":
            self.story.active_rail.content.reload_rail()

    def _delete_custom_field_clicked(self, field_name: str):
        ''' Handles deleting a custom text field from character '''

        try:
            if field_name in self.data['character_data']['Custom Fields']:
                del self.data['character_data']['Custom Fields'][field_name]
                self.save_dict()
                self.reload_widget()
        except Exception as e:
            print(f"Error deleting custom field: {e}")


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
                ft.IconButton(tooltip="Exit Edit Mode", icon=ft.Icons.EDIT_OFF_OUTLINED, icon_color=self.data.get('color', None), on_click=self._edit_mode_clicked),
                #ft.Divider(color="transparent"),    # Used as new line
            ], wrap=True),
        ], scroll="auto", expand=True)

        # Add our summary
        body.controls.append(ft.TextField(
            self.data.get('character_data', {}).get('Basic Info', {}).get('Summary', ""), label="Summary", dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES, adaptive=True, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            on_blur=lambda e: self._update_character_data("Basic Info", **{"Summary": e.control.value}),
        ))

        
        # Add our Role and morality dropdowns
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
                        ft.dropdown.Option("Good"),
                        ft.dropdown.Option("Neutral"),
                        ft.dropdown.Option("Evil"),
                        ft.dropdown.Option("Lawful Good"),
                        ft.dropdown.Option("Lawful Neutral"),
                        ft.dropdown.Option("Lawful Evil"),
                        ft.dropdown.Option("Neutral Good"),
                        ft.dropdown.Option("Neutral Evil"),
                        ft.dropdown.Option("Chaotic Good"),
                        ft.dropdown.Option("Chaotic Neutral"),
                        ft.dropdown.Option("Chaotic Evil"),
                        ft.dropdown.Option("None"),
                    ],
                    value=self.data.get('character_data', {}).get('Morality', ""),
                    on_change=lambda e: self._update_character_data(**{"Morality": e.control.value}),
                )
            ], wrap=True)
        )

        # Age 
        body.controls.append(
            ft.TextField(
                self.data.get('character_data', {}).get('Age', "").capitalize(), label="Age", dense=True, multiline=True, expand=True,
                capitalization=ft.TextCapitalization.WORDS, adaptive=True, input_filter=ft.NumbersOnlyInputFilter(),
                on_blur=lambda e: self._update_character_data(**{"Age": str(e.control.value)}), text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            ) 
        )

        # Nationality and Occupation
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
            controls_padding=ft.padding.only(left=20,top=6,right=20), controls=[ft.Column(spacing=4)]
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


        # Physical Description Expansion Tile
        physical_description = ft.ExpansionTile(
            ft.Text("Physical Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)), 
            shape=ft.RoundedRectangleBorder(), initially_expanded=True, dense=True,
            controls_padding=ft.padding.only(left=20,top=6,right=20), controls=[ft.Column(spacing=4)]
        )

        for key, value in self.data.get('character_data', {}).get('Physical Description', {}).items():
            physical_description.controls[0].controls.append(
                ft.TextField(
                    value, label=key, dense=True, multiline=True, expand=True,
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=lambda e, k=key: self._update_character_data("Physical Description", **{k: e.control.value}),
                )
            )

        body.controls.append(physical_description)

        # Family Expansion Tile
        family = ft.ExpansionTile(
            ft.Text("Family", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)), 
            shape=ft.RoundedRectangleBorder(), initially_expanded=True, dense=True,
            controls_padding=ft.padding.only(left=20,top=6,right=20), controls=[ft.Column(spacing=4)]
        )

        for key, value in self.data.get('character_data', {}).get('Family', {}).items():
            family.controls[0].controls.append(
                ft.TextField(
                    value, label=key, dense=True, multiline=True, expand=True,
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=lambda e, k=key: self._update_character_data("Family", **{k: e.control.value}),
                )
            )

        body.controls.append(family)

        # Origin Expansion Tile
        origin = ft.ExpansionTile(
            ft.Text("Origin", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
            shape=ft.RoundedRectangleBorder(), initially_expanded=True, dense=True,
            controls_padding=ft.padding.only(left=20,top=6,right=20), controls=[ft.Column(spacing=4)]
        )
        for key, value in self.data.get('character_data', {}).get('Origin', {}).items():
            origin.controls[0].controls.append(
                ft.TextField(
                    value, label=key, dense=True, multiline=True, expand=True,
                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                    on_blur=lambda e, k=key: self._update_character_data("Origin", **{k: e.control.value}),
                )
            )
        body.controls.append(origin)


        connections = ft.ExpansionTile(
            ft.Text("Connections", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)), 
            shape=ft.RoundedRectangleBorder(), initially_expanded=True, dense=True,
            controls_padding=ft.padding.only(left=20,top=6,right=20), 
            controls=[ft.Column(spacing=4, controls=[])]
        )

        
        
        for key, value in self.data.get('character_data', {}).get('Connections', {}).items():
            connections.controls[0].controls.append(
                ft.Dropdown(
                    value, label=key, dense=True, expand=True, 
                    on_change=lambda e, k=key: self._update_character_data("Connections", **{k: e.control.value}),
                    options=[
                        ft.DropdownOption("Spouse"),
                        ft.DropdownOption("Child"),
                        ft.DropdownOption("Parent"),
                        ft.DropdownOption("Sibling"),
                        ft.DropdownOption("Friend"),
                        ft.DropdownOption("Rival"),
                        ft.DropdownOption("Other")
                    ]
                )
            )
        connections.controls.append(ft.IconButton(tooltip="Add Connection", icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=self._new_connection_clicked))


        body.controls.append(connections)



        # Give us a divider before custom fields and add a label
        body.controls.append(ft.Divider())
        body.controls.append(
            ft.Row([
                ft.Text("Custom Fields:", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), text_align=ft.TextAlign.CENTER),
                ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=self._new_custom_field_clicked),
            ])
        )

        # Any custom fields we have
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
        # Personality
        # Nationality ^ 
        # Occupation ^
        # Goals ^
        # Physical Description {} ^
        # Family {} ^
        # Origin {} ^
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

        def _load_dict_data(dict: dict, container: ft.Container):
            ''' Loads data from a dict into a given container '''
            for key, value in dict.items():
                if isinstance(value, str):
                    text_control = ft.Text(
                            expand=True, selectable=True, spans=[
                                ft.TextSpan(f"{key.capitalize()}: ", ft.TextStyle(weight=ft.FontWeight.BOLD)),   # Key is bold with formatting
                                ft.TextSpan(value)     # Rest of the value
                            ]
                        )
                    
                    if value or app.settings.data.get('show_empty_character_fields', True):
                        container.content.controls.append(text_control)
                    else:
                        continue
                    
                elif isinstance(value, list):
                    text_control = ft.Text(
                        expand=True, selectable=True, spans=[
                        ft.TextSpan(f"{key.capitalize()}:", ft.TextStyle(weight=ft.FontWeight.BOLD)),
                    ])
                    for val in value:
                            text_control.spans.append(ft.TextSpan(f"\n\t\u2022\t{val}", ft.TextStyle()))
                        
                    if text_control.spans.__len__() > 1 or app.settings.data.get('show_empty_character_fields', True):
                        container.content.controls.append(text_control)
        
        # Rebuild out tab to reflect any changes
        self.reload_tab()

        
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
                    ft.IconButton(tooltip="Edit Mode", icon=ft.Icons.EDIT_OUTLINED, icon_color=self.data.get('color', None), on_click=self._edit_mode_clicked),
                ], wrap=True),
            ], scroll="auto", expand=True)

            # Create a container for our dicts that we have data in and load them. 
            template_data_container = ft.Container(         # For template data
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(5), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), #bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE_VARIANT),
                content=ft.Column([]), 
            )
        
            basic_info_container = ft.Container(            # For basic info
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(5), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), #bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE_VARIANT),
                content=ft.Column([]), 
                
            )

            physical_description_container = ft.Container(  # For physical description
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), #bgcolor=ft.Colors.with_opacity(.1, ft.Colors.ON_SURFACE_VARIANT),
                content=ft.Column([]), 
            )   

            family_container = ft.Container(                # For family
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), #bgcolor=ft.Colors.with_opacity(.1, ft.Colors.ON_SURFACE_VARIANT),
                content=ft.Column([]), 
            )

            origin_container = ft.Container(                # For origin 
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), #bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE_VARIANT),
                content=ft.Column([]),
            )

            connections_container = ft.Container(           # For connections
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), #bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE_VARIANT),
                content=ft.Column([]), 
            )

            custom_fields_container = ft.Container(        # For custom fields
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), #bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE_VARIANT),
                content=ft.Column([]), 
            )

            _load_dict_data(self.data.get('character_data', {}).get('Template Data', {}), template_data_container)
            _load_dict_data(self.data.get('character_data', {}).get('Basic Info', {}), basic_info_container)
            _load_dict_data(self.data.get('character_data', {}).get('Physical Description', {}), physical_description_container)
            _load_dict_data(self.data.get('character_data', {}).get('Family', {}), family_container)
            _load_dict_data(self.data.get('character_data', {}).get('Origin', {}), origin_container)
            _load_dict_data(self.data.get('character_data', {}).get('Connections', {}), connections_container)
            _load_dict_data(self.data.get('character_data', {}).get('Custom Fields', {}), custom_fields_container)

            row1 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            row2 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            row3 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            row4 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)


            
    
            # If we have basic info, this will add it to the page. Protects against custom templates getting rid of certain sections
            if basic_info_container.content.controls:
                row1.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Container(width=6), 
                            ft.Text("Basic Info", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                        ], spacing=0),
                        ft.Row([basic_info_container])
                    ], expand=True, spacing=4)
                )
            # If we have temlpate data, this will add it to the page
            if 'Template Data' not in self.data.get('character_data', {}):
                pass
            else:
                
                if app.settings.data.get('show_empty_character_fields', True) or template_data_container.content.controls:
                    template_title = self.data.get('character_data', {}).get('Template Data', {}).get('Template Name', 'Template Data')
                    row1.controls.append(
                        ft.Column([
                            ft.Row([
                                ft.Container(width=6), 
                                ft.Text(template_title, style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), color=self.data.get('color', None), selectable=True, expand=True)
                            ], spacing=0),
                            ft.Row([template_data_container])
                        ], expand=True, spacing=4)
                    )
            if physical_description_container.content.controls:
                row2.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Container(width=6), 
                            ft.Text("Physical Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                        ], spacing=0),
                        ft.Row([physical_description_container])
                    ], expand=True, spacing=4)
                )
            if family_container.content.controls:
                row2.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Container(width=6), 
                            ft.Text("Family", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                        ], spacing=0),
                        ft.Row([family_container])
                    ], expand=True, spacing=4)
                )
            if origin_container.content.controls:
                row3.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Container(width=6), 
                            ft.Text("Origin", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                        ], spacing=0),
                        ft.Row([origin_container])
                    ], expand=True, spacing=4)
                )
            if app.settings.data.get('show_empty_character_fields', True):
                row3.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Container(width=6), 
                            ft.Text("Connections", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                        ], spacing=0),
                        ft.Row([connections_container])
                    ], expand=True, spacing=4)
                )
            if custom_fields_container.content.controls:
                row4.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Container(width=6), 
                            ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                        ], spacing=0),
                        ft.Row([custom_fields_container])
                    ], expand=True, spacing=4)
                )

            body.controls.append(ft.Container(padding=ft.padding.only(right=8), content=ft.Column([row1, row2, row3, row4], spacing=16)))
        
            self.body_container.content = body

            # Call render widget (from Widget class) to update the UI
            self._render_widget()