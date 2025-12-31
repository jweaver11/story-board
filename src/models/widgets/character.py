'''
Most model classes really container 2 models: the character model itself and the associated widget model.
Inside of the 'data' dict, we store our characters model for the manipulative data...
the app will change. Everything else is built upon program launch so we can display it in the UI.
'''

import flet as ft
import os
from models.widget import Widget
from models.views.story import Story
from handlers.verify_data import verify_data
from styles.menu_option_style import Menu_Option_Style



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
                'tag': "character",
                'pin_location': "left" if data is None else data.get('pin_location', "left"),     # Start our characters on the left pin

                'narrator': bool, # Whether this character is a narrator -- check box in edit view
                'tab_color': "primary",
                'name_color': "primary",
                'sex_color': "primary",
                'alignment1': str, #lawful, neutral, chaotic, none
                'alignment2': str, #good, neutral, evil, none
                'gender': str, #text input
                'age': str, #text input
                'sexuality': str, #text input
                'nationality': str, #text input
                'title_prefix': str, #text input
                'edit_mode': bool,  # Whether we are in edit mode or not
                'physical_description': {
                    'Race': str, #having this in a dict sort of complicates the on_change handlers
                    'Species': str,
                    'Ethnicity': str,
                    'Skin Color': str,
                    'Hair Color': str,   
                    'Eye Color': str,    
                    'Height': str,   
                    'Weight': str,   
                    'Build': str,    
                    'Distinguishing Features': str,  
                },
                'connections':{
                    #TODO list of other characters and relationship types
                },
                'family':  { #TODO "connections" dropdown+tree/detective view?
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
                'strengths': {
                    'physical': str,
                    'mental': str,
                    'social': str,
                    'magical': str,
                },
                'weaknesses': {
                    'physical': str,
                    'mental': str,
                    'social': str,
                    'magical': str,
                },
                'trauma': str,
                'occupation': str,
                'goals': str,
                'personality': str,
                'backstory': str,
                'abilities': str,
                'is_dead': bool,    # Defaults to false
            },
        )
        
        self.icon = ft.Icon(ft.Icons.PERSON, size=100, expand=False),
        
        self.custom_field_controls = {}  # Store references to custom field TextFields

        # Build our widget on start, but just reloads it later
        self.reload_widget()

    # Called when user wants to edit character
    def edit_character_clicked(self, e):
        ''' Handles editing character details '''
        # For now, just reload the widget to reflect any changes
        print("Editing character:", self.title)
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

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self): #this is the edit view currently
        ''' Reloads/Rebuilds our widget based on current data '''
        
        # Rebuild out tab to reflect any changes
        self.reload_tab()

        if self.data['is_active_tab']:
            self.icon = ft.Icon(ft.Icons.PERSON, size=100, color="primary", expand=False)
        else:
            self.icon = ft.Icon(ft.Icons.PERSON_OUTLINE, size=100, color="disabled", expand=False)
        #WIP this will be the edit view 
        
        # Body of the tab, which is the content of flet container
        regView_button = ft.Row([
            self.icon,
            ft.IconButton(
                tooltip="regular View",
                icon=ft.Icons.EDIT_OUTLINED,
                on_click=self.edit_mode_clicked
                #this will trigger the regular view
            ),
        ]   
        )

        #print("Edit mode for ", self.title, ": ", self.data['edit_mode'])



        # Check if we're in edit mode or not. If yes, build the edit view like this
        if self.data.get('edit_mode', False):

            # Ensure connections are normalized to a list for UI building
            self._ensure_connections_list()

            #all of this needs to be the edit view
            body = ft.Container(
                expand=True,                # Takes up maximum space allowed in its parent container
                padding=2,                  # Padding around everything inside the container
                content=ft.Column(           # The column that will hold all our stuff top down
                    scroll=ft.ScrollMode.AUTO,  # Enable scrolling when content overflows
                    spacing=2,               # Reduce spacing between elements
                    controls=[
                    regView_button,
                    #self.icon,                          # The icon above the name
                    #ft.Text("hi from " + self.title),           # Text that shows the title
                    ft.Row(                     # The row that will hold our dropdowns
                            wrap=True,          # Allows moving into columns/multiple lines if dropdowns don't fit
                            controls=[          # All flet controls inside our Row
                                ft.Checkbox(label="Narrator",    # Checkbox for narrator status
                                    value=self.data['narrator'],
                                    on_change=lambda e, name='narrator': self._on_field_change(name, e.control.value)
                                    ),
                                ft.Dropdown(        # Dropdown selection of lawful, chaotic, neutral, and n/a
                                    label="alignment1",           # Label at top of dropdown 
                                    value=self.data['alignment1'],        # Value selected in the drop down
                                    dense=True,
                                    color=self.data['name_color'],      # Color of the dropdown text
                                    text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),         # Style of the text in the dropdown
                                    options=[           # Options for the dropdown
                                        ft.DropdownOption(text="Undecided"),
                                        ft.DropdownOption(text="Lawful"),
                                        ft.DropdownOption(text="Neutral"),
                                        ft.DropdownOption(text="Chaotic"),
                                        ft.DropdownOption(text="None"),
                                        
                                    ],
                                    on_change=lambda e,name='alignment1': self._on_field_change(name,e.control.value),
                                ),
                                ft.Dropdown(        # Dropdown selection of good, evil, neutral, and n/a
                                    label="alignment2",           # Label at top of dropdown 
                                    value=self.data['alignment2'],        # Value selected in the drop down
                                    #dense=True,
                                    color=self.data['name_color'],      # Color of the dropdown text
                                    text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),         # Style of the text in the dropdown
                                    options=[           # Options for the dropdown
                                        ft.DropdownOption(text="Undecided"),
                                        ft.DropdownOption(text="Good"),
                                        ft.DropdownOption(text="Neutral"),
                                        ft.DropdownOption(text="Evil"),
                                        ft.DropdownOption(text="None"),
                                        
                                    ],
                                    on_change=lambda e,name='alignment2': self._on_field_change(name,e.control.value),
                                ),
                                # Connections: show existing picks and allow adding more via dropdown
                                ft.Column(
                                    spacing=4,
                                    controls=[
                                        ft.Row(
                                            spacing=6,
                                            controls=[
                                                ft.Container(content=ft.Text("Connections:", weight=ft.FontWeight.BOLD))
                                            ] + [
                                                ft.Container(
                                                    content=ft.Row(
                                                        controls=[
                                                            ft.Text(cname),
                                                            ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e, n=cname: self._on_remove_connection(n), tooltip="Remove")
                                                        ],
                                                        spacing=4
                                                    ),
                                                    padding=ft.padding.all(6),
                                                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                                                    border_radius=ft.border_radius.all(6)
                                                )
                                                for cname in (self.data.get('connections') or [])
                                            ]
                                        ),

                                        # Dropdown to add another connection; options exclude self and already-chosen
                                        ft.Dropdown(
                                            label="Add Connection",
                                            #this will change the connections part of the data 
                                            value=None,
                                            expand = 4,
                                            hint_text="Select character to add",
                                            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                                            options=[
                                                ft.DropdownOption(text=name)
                                                for name in self.story.get_character_names()
                                                if name and name != self.title and name not in (self.data.get('connections') or [])
                                            ],
                                            on_change=lambda e: self._on_add_connection(e.control.value),
                                        ),
                                    ]
                                ),
                                ft.TextField(   # Text field for title_prefix input
                                    label ="Title",
                                    value=self.data['title_prefix'],  # Load saved title data
                                    width=200,
                                    expand = False,
                                    on_change=lambda e, name='title_prefix': self._on_field_change(name, e.control.value),  # Save on change
                                ),
                                ft.TextField(   # Text field for title_prefix input
                                    label ="Nationality",
                                    value=self.data['nationality'],  # Load saved nationality data
                                    width=200,
                                    expand = False,
                                    on_change=lambda e, name='nationality': self._on_field_change(name, e.control.value),  # Save on change
                                ),
                                ft.TextField(   # Text field for sexuality input
                                    label ="Gender",
                                    value=self.data['gender'],  # Load saved sexuality data
                                    width=200,
                                    expand = False,
                                    on_change=lambda e, name='gender': self._on_field_change(name, e.control.value),  # Save on change
                                ),
                                ft.TextField(  # Text field for age input
                                    label ="Age",
                                    value=self.data['age'],  # Load saved age data
                                    max_length=7,#allows for things like "unknown" or "ancient"
                                    width=100,
                                    expand = False,
                                    on_change=lambda e, name='age': self._on_field_change(name, e.control.value),  # Save on change
                                ),
                                
                                ft.TextField(   # Text field for race input
                                    label ="Race",
                                    value=self.data['physical_description'].get('Race', ''),  # Load saved race data
                                    width=250,
                                    expand = False, #prevents stretching too wide
                                    on_change=lambda e, name='physical_description': self._on_race_change(name, e.control.value),  # Save on change
                                ),
                                ft.TextField(   # Text field for sexuality input
                                    label ="Sexuality",
                                    value=self.data['sexuality'],  # Load saved sexuality data
                                    width=200,
                                    expand = False,
                                    on_change=lambda e, name='sexuality': self._on_field_change(name, e.control.value),  # Save on change
                                ),
                                ft.IconButton(
                                    tooltip="New Field",
                                    icon=ft.Icons.NEW_LABEL_OUTLINED,
                                    on_click=self.new_custom_textfield_clicked
                                ),
                            ]
                        ),
                    ]
                )
            )     


        # If NOT in edit mode
        else:

            # Build the edit view like this. 
            body = self.edit_mode_view(edit_button=regView_button)
        
        # After the main body, add a section for custom fields if any exist
        if self.data['custom_fields']:
            # Create a column to hold all custom fields
            custom_fields_column = ft.Column(
                spacing=8,
                controls=[]
            )
            
            # Add each custom field
            for field_name, field_value in self.data['custom_fields'].items():
                custom_textfield = ft.TextField(
                    label=field_name,
                    value=field_value,
                    width=300,
                    expand=False,
                    on_change=lambda e, name=field_name: self._on_custom_field_change(name, e.control.value)
                )
                self.custom_field_controls[field_name] = custom_textfield
                custom_fields_column.controls.append(custom_textfield)
            
            # Add custom fields to the body
            body.content.controls.append(ft.Divider())
            body.content.controls.append(ft.Text("Custom Fields", weight=ft.FontWeight.BOLD, size=12))
            body.content.controls.append(custom_fields_column)
        
        # Set our content to the body_container (from Widget class) as the body we just built
        self.body_container.content = body

        # Call render widget (from Widget class) to update the UI
        self._render_widget()
    
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


    # Called when not in edit mode FROM reload_widget
    def edit_mode_view(self, edit_button) -> ft.Container:
        ''' Example function for character details '''
        
        body = ft.Container(
            expand=True,                # Takes up maximum space allowed in its parent container
            padding=5,                  # Padding around everything inside the container
            content=ft.Column(           # The column that will hold all our stuff top down
                scroll=ft.ScrollMode.AUTO,  # Enable scrolling when content overflows
                spacing=1,               # Reduce spacing between elements
                controls=[
                edit_button,            # Just pass in the edit button for now so we don't build it twice
                #self.icon,                          # The icon above the name
                #ft.Text("hi from " + self.title),           # Text that shows the title
                ft.Row(                     # The row that will hold our dropdowns
                        wrap=True,          # Allows moving into columns/multiple lines if dropdowns don't fit
                        controls= (          # All flet controls inside our Row
                            [
                                ft.Icon(ft.Icons.MIC, size=20),
                                #ft.Text("Narrator", weight=ft.FontWeight.BOLD),
                            ] if self.data['narrator'] else []
                        ) + [
                            ft.Text("Full Title: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(self.data['title_prefix'] + " " + self.title),
                            ft.Text("Alignment: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(self.data['alignment1'] + " " + self.data['alignment2']),
                            ft.Text("Gender: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(self.data['gender']),
                            ft.Text("Age: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(self.data['age']),  
                            ft.Text("Race: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(self.data['physical_description'].get('Race', '')),
                            ft.Text("Sexuality: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(self.data['sexuality']),
                            ft.Text("Nationality: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(self.data['nationality']),
                            ft.Text("Connections: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(str(self.data['connections'])),
                            ft.Text("Custom Fields: ",
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(str(self.data['custom_fields'])),
                        ]
                    ),
                ]
            )
        )
        
        return body



    # CORY NOTES:
    # Added edit mode clicked function to toggle edit mode on or off
    # Always use reload widget to simplify UI rebuilding when needed. Let the reload widget handle the differences

    # Called when clicking the edit mode button
    def edit_mode_clicked(self, e=None):
        ''' Switches between edit mode and not for the character '''

        #print("Switching to edit mode for character:", self.title)

        # Change our edit mode data flag, and save it to file
        self.data['edit_mode'] = not self.data['edit_mode']
        self.save_dict()

        # Reload the widget. The reload widget should load differently depending on if we're in edit mode or not
        self.reload_widget()