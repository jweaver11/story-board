''' 
Our widget class that displays our world and lore information. Essentially, all information not displayed visually on the maps goes here
Maps can tie into one widget 'world' widget
'''

import os
import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.app import app
from utils.safe_string_checker import return_safe_name



class World(Widget):

    # Constructor
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict=None, is_rebuilt: bool = False):

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
        
        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'tag': "world",     
                'color': app.settings.data.get('default_world_color'),   

                # State and view data
                'edit_mode': bool,              # Whether we are in edit mode or not
                'image_base64': str,            # Saves our image as img64 string

                'About': str,

                # World data
                'world_data': {
                    'Locations': dict,
                    'Lore': dict,
                    'Power Systems': dict,
                    'Social Systems': dict,
                    'Geography': dict,
                    'Technology': dict,
                    'History': dict,
                    'Governments': dict,
                    'Custom Fields': dict,  
                },
            }
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
      
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init
    

    

    # Called when a field is changed in edit mode
    def _update_world_data(self, **kwargs):
        ''' Updates the world data dict or up to one sub dict '''

        for key, value in kwargs.items():
            if 'world_data' not in self.data:
                self.data['world_data'] = {}

            if key in self.data['world_data']:
                self.data['world_data'][key] = value
            else:
                # Check if this key is in a sub dict, and update it there if it is
                for sub_key, sub_dict in self.data['world_data'].items():
                    if isinstance(sub_dict, dict) and key in sub_dict:
                        self.data['world_data'][sub_key][key] = value
                        break
        
        self.save_dict()

    

    # Deletes a field from our world data dict
    def _delete_world_data(self, **kwargs):
        ''' Deletes fields from the world data dict or up to one sub dict '''

        for key in kwargs.keys():
            if 'world_data' not in self.data:
                return

            if key in self.data['world_data']:
                del self.data['world_data'][key]
            else:
                # Check if this key is in a sub dict, and delete it there if it is
                for sub_key, sub_dict in self.data['world_data'].items():
                    if isinstance(sub_dict, dict) and key in sub_dict:
                        del self.data['world_data'][sub_key][key]
                        break
                
        self.save_dict()
        self.reload_widget()

    # Called when adding a new field to a section
    def _new_field_clicked(self, section: str):
        ''' Opens a dialog to name a new field inside a section '''

        if 'world_data' not in self.data:
            self.data['world_data'] = {}

        if section not in self.data['world_data']:
            self.data['world_data'][section] = {}

        def create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            
            field_name = return_safe_name(field_name_input.value)
            
            if not field_name:
                self.p.pop_dialog()
                return  # Don't create if empty
            
            # Add the field to data if it doesn't exist
            if field_name not in self.data['world_data'][section]:
                self.data['world_data'][section][field_name] = ""
            
            # Save and reload
            self.save_dict()
            self.p.pop_dialog()
            self.reload_widget()
                                
            

        # Create a dialog to ask for the field name
        field_name_input = ft.TextField(
            label="Field Name",
            autofocus=True, capitalization=ft.TextCapitalization.SENTENCES,
            on_submit=create_field,     # Closes the overlay when submitting
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Create New Field in {section}"),
            content=field_name_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                ft.TextButton("Create", on_click=create_field),
            ],
        )
     
        self.p.show_dialog(dlg)

    # Called when clicking our upload image button
    async def _upload_world_image(self, e=None):

        files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
        if files:

            file_path = files[0].path
            try:
                import base64

                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    # Save to our data
                    self.data['image_base64'] = f"{encoded_string}"
                    self.save_dict()
                    self.reload_widget()

            except Exception as _:
                pass
    
    # Called when clicking the edit mode button
    def _edit_mode_clicked(self, e=None):
        ''' Switches between edit mode and not for the world '''

        # Change our edit mode data flag, and save it to file
        self.data['edit_mode'] = not self.data['edit_mode']
        self.save_dict()

        # Reload the widget. The reload widget should load differently depending on if we're in edit mode or not
        self.reload_widget()

    # Called if our widget is in edit view. 
    def _edit_mode_view(self):
        ''' Returns our world data with input capabilities '''

        def _get_help_text(key: str="") -> str:
            ''' Returns help text for certain fields '''
            match key:
                
                case "Locations":
                    return "Detail the key locations within the world, including cities, landmarks, and significant sites."
                case "Lore":
                    return "Detail the myths, legends, and historical narratives that shape the world's culture and identity."
                case "Power Systems":
                    return "Magic systems, supernatural abilities, or other extraordinary powers."
                case "Social Systems":
                    return "Describe the social structures, hierarchies, and interactions within the world."
            
                case _:
                    return None


        # Loads our world data dict into text controls for editing
        def _load_world_data_controls() -> list[ft.Control]:
            ''' Loads data from a dict into a given container '''
            control_list = []
            
            # Go through our sections inside of our world data
            for section, values in self.data.get('world_data', {}).items():

                # Skip non-dict sections 
                if not isinstance(values, dict):
                    continue

                # Set a label and container to hold our text spans for each section
                label = ft.Row([
                    ft.Text(f"\t\t{section}", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.IconButton(
                        tooltip="Add New Field", icon=ft.Icons.NEW_LABEL_OUTLINED, mouse_cursor="click",
                        on_click=lambda e, s=section:self._new_field_clicked(s), icon_color=self.data.get('color', None)
                    ),
                ])
                # Container to hold the text control of our section info
                container = ft.Container(         # For template data
                    padding=ft.Padding.all(6), border_radius=ft.BorderRadius.all(10), expand=True,
                    border=ft.Border.all(2, ft.Colors.OUTLINE), margin=ft.Margin.only(bottom=10),
                    content=ft.Column(expand=True, spacing=6) # Forces container to take up space
                )

                # Go through every key/value pair in this section and add it to our text span list with formatting
                for key, value in values.items():
                    if isinstance(value, str) and (value or app.settings.data.get('show_empty_world_fields', True)):

                        # Add the each key for this section
                        container.content.controls.append(
                            ft.Row([
                                ft.TextField(
                                    label=key, hint_text=_get_help_text(key), value=value, 
                                    on_blur=lambda e, k=key: self._update_world_data(**{k: e.control.value}), expand=True,
                                    dense=True, capitalization=ft.TextCapitalization.SENTENCES, multiline=True,
                                    focus_color=self.data.get('color', "primary"), focused_border_color=self.data.get('color', "primary"), 
                                    cursor_color=self.data.get('color', "primary"),
                                ),
                                ft.IconButton(
                                    tooltip="Delete Field", icon=ft.Icons.DELETE_OUTLINE, mouse_cursor="click",
                                    on_click=lambda e, k=key: self._delete_world_data(**{k: ""}), icon_color=ft.Colors.ERROR
                                )
                            ])
                        )

                if len(container.content.controls) == 0:
                    container.content.controls.append(
                        ft.Row([
                            ft.Text("No fields to display", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                            ft.TextButton(
                                ft.Text("Delete Section?", color=ft.Colors.ERROR),
                                on_click=lambda e, s=section: self._delete_world_data(**{s: ""})
                            )
                        ])
                    )


                # Add the label and container with our text spans to the control list for this section
                control_list.append(label)
                control_list.append(container)

            return control_list
                    
        if self.data.get('image_base64', ""):
            img = ft.Container(
                ft.Image(
                    src=self.data.get('image_base64', ""),
                    width=80,
                    height=80,
                    fit=ft.BoxFit.FILL,
                ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
        else:
            img = ft.Icon(ft.Icons.PERSON_OUTLINE, size=100, color=self.data.get('color', "primary"), expand=False)

        # Changes for the about section
        async def _change_about_data(e):
            ''' Called when the about section is changed in edit mode '''
            self.data['About'] = e.control.value
            self.save_dict()

        about_section = ft.Column([
            ft.Row([
                ft.Text(f"\t\tAbout", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                ft.IconButton(
                    tooltip="Edit Mode", icon=ft.Icons.EDIT_OFF_OUTLINED, icon_color=self.data.get('color', None), 
                    on_click=self._edit_mode_clicked, mouse_cursor="click"
                ),
            ]),
            ft.Container(
                border_radius=ft.BorderRadius.all(10), expand=True,
                border=ft.Border.all(2, ft.Colors.OUTLINE), margin=ft.Margin.only(left=6),   
                content=ft.TextField(
                    self.data.get('char_data', {}).get('About', ""), on_blur=_change_about_data, expand=True, 
                    dense=True, capitalization=ft.TextCapitalization.SENTENCES, multiline=True,
                    focus_color="transparent", focused_border_color="transparent", 
                    cursor_color=self.data.get('color', "primary"), border_color="transparent"
                ), 
            )
        ], expand=True, spacing=0)

        
        # Header that holds our image, edit mode button, and about section
        header = ft.Row([
            ft.IconButton(img, tooltip="Upload Image", on_click=self._upload_world_image, mouse_cursor="click"),
            about_section
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

        body = ft.Column([
            header
        ], scroll="auto", expand=True, spacing=4)

        body.controls.extend(_load_world_data_controls())   

        self.body_container.content = body


    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self): #this is the edit view currently
        ''' Reloads/Rebuilds our widget based on current data '''

        def _load_world_data_controls() -> list[ft.Control]:
            ''' Loads data from a dict into a given container '''

            # TODO: Skip empty ones check

            control_list = []
            
            # Go through our sections inside of our world data
            for section, values in self.data.get('world_data', {}).items():

                # Skip non-dict sections 
                if not isinstance(values, dict):
                    continue

                # Set a label and container to hold our text spans for each section
                label = ft.Text(f"\t\t{section}", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None))
                
                # List to hold text spans for each text control in the container
                text_span_list = []

                # Container to hold the text control of our section info
                container = ft.Container(         # For template data
                    padding=ft.Padding.all(6), border_radius=ft.BorderRadius.all(10), expand=True,
                    border=ft.Border.all(2, ft.Colors.OUTLINE), margin=ft.Margin.only(bottom=10),
                    content=ft.Row([ft.Text(expand=True, spans=text_span_list, size=14)]), # Forces container to take up space
                )

                # Go through every key/value pair in this section and add it to our text span list with formatting
                for key, value in values.items():
                    if isinstance(value, str) and (value or app.settings.data.get('show_empty_world_fields', True)):


                        # If artifically created new lines, treat as bullet point list
                        if "\n" in value:
                            text_span_list.append(
                                ft.TextSpan(f"{key.capitalize()}:\n", ft.TextStyle(weight=ft.FontWeight.BOLD))
                            )

                            # Add the value for this key, with a bullet point if there are multiple values separated by new lines
                            values = [v.strip() for v in value.replace('\n', ',').split(',') if v.strip()]
                            for val in values:
                                text_span_list.append(ft.TextSpan(f"\t\u2022\t{val.capitalize()}\n"))

                        # Otherwise, just add the key and value normally
                        else:

                            # Add the each key for this section
                            text_span_list.append(
                                ft.TextSpan(f"{key.capitalize()}:\t\t", ft.TextStyle(weight=ft.FontWeight.BOLD))
                            )
                            text_span_list.append(ft.TextSpan(f"{value}\n"))     # Rest of the value


                # Remove unnecessary new line at the end for cleaner formatting
                last_span = text_span_list[-1] if text_span_list else None
                if last_span and last_span.text.endswith("\n"):
                    last_span.text = last_span.text[:-1]  # Remove the last new line for cleaner formatting

                # Add the label and container with our text spans to the control list for this section
                control_list.append(label)
                control_list.append(container)

            return control_list

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        # Check if we're in edit mode or not. If yes, build the edit view like this
        if self.data.get('edit_mode', False):
            self._edit_mode_view()
            self._render_widget()
            return


        # If NOT in edit mode, build our normal view
        # Set either our image or a default icon
        if self.data.get('image_base64', ""):
            img = ft.Container(
                ft.Image(
                    src=self.data.get('image_base64', ""),
                    width=80,
                    height=80,
                    fit=ft.BoxFit.FILL,
                ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            )
        else:
            img = ft.Icon(ft.Icons.PERSON_OUTLINE, size=100, color=self.data.get('color', "primary"), expand=False)

        about_section = ft.Column([
            ft.Row([
                ft.Text(f"\t\tAbout", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                ft.IconButton(
                    tooltip="Edit Mode", icon=ft.Icons.EDIT_OUTLINED, icon_color=self.data.get('color', None), 
                    on_click=self._edit_mode_clicked, mouse_cursor="click"
                ),
            ]),
            ft.Container(
                padding=ft.Padding.all(6), border_radius=ft.BorderRadius.all(10), expand=True,
                border=ft.Border.all(2, ft.Colors.OUTLINE), margin=ft.Margin.only(left=6),   
                content=ft.Row([ft.Text(self.data.get('About', ""), expand=True, size=14)], expand=True), # Forces container to take up space
            )
        ], expand=True, spacing=0)

        
        # Header that holds our image, edit mode button, and about section
        header = ft.Row([
            ft.IconButton(img, tooltip="Upload Image", on_click=self._upload_world_image, mouse_cursor="click"),
            about_section
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)


        # Body that holds the rest of our widget
        body = ft.Column(
            controls=[header],
            scroll="auto", expand=True, spacing=4
        )

        # Load in our world data controls after the header
        body.controls.extend(_load_world_data_controls())   

        # Set the body we built
        self.body_container.content = body

        # Call render widget (from Widget class) to update the UI
        self._render_widget()



