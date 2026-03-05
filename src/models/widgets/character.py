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
from models.mini_widgets.character_connection import CharacterConnection
from models.app import app
from utils.safe_string_checker import return_safe_name
from models.dataclasses.character_template import default_character_template_data_dict
from utils.alert_dialogs.character_connection import new_character_connection_clicked
import flet.canvas as cv
import asyncio




# Sets our Character as an extended Widget object, which is a subclass of a flet Container
# Widget requires a title, tag, page reference, and a pin location
class Character(Widget):
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
                'tag': "character",
                'pin_location': "left" if data is None else data.get('pin_location', "left"),     # Start our characters on the left pin
                'color': app.settings.data.get('default_character_color'),

                # State and view data
                'edit_mode': True,      # Whether we are in edit mode or not
                'image_base64': str,    # Saves our icon as img64 string 

                # Character data
                'About': "",
                # If this dict doesn't exist, we create it with our active template data. If we fail to pull that, we use a default template (which has quite a lot)
                'character_data': app.settings.data.get('character_templates', {}).get(app.settings.get('active_character_template', ""), default_character_template_data_dict()) 
                if data is None or 'character_data' not in data else data['character_data'],
            },
        ) 
 

        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init


    # TODO: RENAME AND DELETE Will need to be custom here, to alter ccm and connections that used our old name and key
        
    # Called when adding a new field to a section
    def _new_field_clicked(self, section: str):
        ''' Opens a dialog to name a new field inside a section '''

        if 'character_data' not in self.data:
            self.data['character_data'] = {}

        if section not in self.data['character_data']:
            self.data['character_data'][section] = {}

        def create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            
            field_name = return_safe_name(field_name_input.value)
            
            if not field_name:
                self.p.pop_dialog()
                return  # Don't create if empty
            
            # Add the field to data if it doesn't exist
            if field_name not in self.data['character_data'][section]:
                self.data['character_data'][section][field_name] = ""
            
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

    
    # Called when a field is changed in edit mode
    def _update_character_data(self, **kwargs):
        ''' Updates the character data dict or up to one sub dict '''

        for key, value in kwargs.items():
            if 'character_data' not in self.data:
                self.data['character_data'] = {}

            if key in self.data['character_data']:
                self.data['character_data'][key] = value
            else:
                # Check if this key is in a sub dict, and update it there if it is
                for sub_key, sub_dict in self.data['character_data'].items():
                    if isinstance(sub_dict, dict) and key in sub_dict:
                        self.data['character_data'][sub_key][key] = value
                        break
        
        self.save_dict()

    # Deletes a field from our character data dict
    def _delete_character_data(self, **kwargs):
        ''' Deletes fields from the character data dict or up to one sub dict '''

        for key in kwargs.keys():
            if 'character_data' not in self.data:
                return

            if key in self.data['character_data']:
                del self.data['character_data'][key]
            else:
                # Check if this key is in a sub dict, and delete it there if it is
                for sub_key, sub_dict in self.data['character_data'].items():
                    if isinstance(sub_dict, dict) and key in sub_dict:
                        del self.data['character_data'][sub_key][key]
                        break
                
        self.save_dict()
        self.reload_widget()

    # Called when clicking our upload image button
    async def _upload_character_image(self, e=None):

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

    def _load_connections(self, connections_list: list, container: ft.Container):
        ''' Loads our connections into a given container '''

        # Grabs all our character options for the dropdown. Exclude already existing connections with those characters
        def _get_char_options(tag: str) -> list[ft.PopupMenuButton]:
            ''' Excludes the already selected character (If one exists) and returns a list of all other characters as control items '''
            
            options = []        # Character options stored as keys
            ctrl_options = []   # Character options stored as dropdown items
            # Key of all characters in the story
            for char_key in self.story.characters.keys():
                options.append(char_key)

            # Make controls for every option
            for key, character in self.story.characters.items():
              
                ctrl_options.append(
                    ft.PopupMenuItem(
                        text=character.data.get('title'),       # Set title for display
                        #on_click=self._set_name_and_key,
                        content=ft.Text(character.data.get('title'), color=character.data.get('color', ft.Colors.ON_SURFACE)),
                        data=[key, tag]         # Set key for easy retrievel
                    )
                )

            # Exclude already selected character from options so they can't connect to themselves
            if tag == "char1":
                if self.data.get('char2_key') in options:
                    # Remove char2 from options
                    remove_key = self.data.get('char2_key')
                    ctrl_options = [ctrl for ctrl in ctrl_options if ctrl.data[0] != remove_key]
            else:
                if self.data.get('char1_key') in options:
                    # Remove char1 from options
                    remove_key = self.data.get('char1_key')
                    ctrl_options = [ctrl for ctrl in ctrl_options if ctrl.data[0] != remove_key]

            if self.data.get('key') in options:
                # Remove self from options
                remove_key = self.data.get('key')
                ctrl_options = [ctrl for ctrl in ctrl_options if ctrl.data[0] != remove_key]
                    
            return ctrl_options     # Return the formatted controls

        # Edit view
        if self.data.get('edit_mode', False):

            # Go through our connections
            for conn in connections_list:

                # Ignore connections not involving this character
                if self.data.get('key') not in [conn.get('char1_key', ""), conn.get('char2_key', "")]:
                    continue

                # Set the two characters in the connection
                char1 = self.story.characters.get(conn.get('char1_key', ""))
                char2 = self.story.characters.get(conn.get('char2_key', ""))

                # Protect against reload_widget calls before other characters are loaded, or both characters not yet set
                if char1 is None or char2 is None:
                    continue
               
                # Build the controls
                container.content.controls.append(
                    ft.Row([
                        ft.PopupMenuButton(      # Name one
                            ft.Container(
                                ft.Text(
                                    conn.get('char1_name', "Change Character 1"), color=char1.data.get('color', "primary"),
                                    overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
                                ),
                                padding=ft.padding.all(6), border_radius=ft.BorderRadius.all(8), ink=True,
                            ), tooltip="Change Character 1", items=_get_char_options(tag="char1"), menu_padding=ft.padding.all(0)
                        ),
                        ft.IconButton(      # Icon
                            conn.get('icon', "connect_without_contact"), icon_color=conn.get('color', "primary"), 
                            on_click=lambda e: new_character_connection_clicked(self.story)
                        ),      
                        ft.TextButton(      # Name 2
                            conn.get('char2_name', "Unknown Character"), on_click=lambda e: new_character_connection_clicked(self.story),
                            style=ft.ButtonStyle(color=char2.data.get('color', "primary"))
                        ),
                        ft.TextField(       # Description
                            conn.get('description', ""), dense=True, expand=True, multiline=True,
                            focused_border_color=conn.get('color', "primary"), cursor_color=conn.get('color', "primary"),
                        ),
                        ft.PopupMenuButton(   # Color button
                            icon=ft.Icons.COLOR_LENS, icon_color=conn.get('color', "primary"), tooltip="Change color",
                        ),
                        # Delete button here
                    ], spacing=0)
                )

        else:

            # Not in edit view
            for conn in connections_list:
                if self.data.get('key') not in [conn.get('char1_key', ""), conn.get('char2_key', "")]:
                    continue
                char1 = self.story.characters.get(conn.get('char1_key', ""))
                char2 = self.story.characters.get(conn.get('char2_key', ""))
                if char1 is None or char2 is None:
                    continue
                # Name1, icon, name2, description
                container.content.controls.append(
                    ft.Row([
                        ft.Text(conn.get('char1_name', "Unknown Character"), color=char1.data.get('color', "primary"), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Icon(conn.get('icon', "connect_without_contact"), color=conn.get('color', "primary")),
                        ft.Text(conn.get('char2_name', "Unknown Character"), color=char2.data.get('color', "primary"), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(conn.get('description', ""), expand=True)
                    ])
                )

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

        def _get_help_text(key: str="") -> str:
            ''' Returns help text for certain fields '''
            match key:
                
                case "Morality":
                    return "Good, Evil, Neutral..."
                case "Role":
                    return "Main, Supporting, Background... "
                case "Tag":
                    return "Protagonist, Antagonist, ..."
                case "Goals":
                    return "Separate Goals with new lines"
                
                case _:
                    return None

        # Loads our character data dict into text controls for editing
        def _load_character_data_controls() -> list[ft.Control]:
            ''' Loads data from a dict into a given container '''
            control_list = []
            
            # Go through our sections inside of our character data
            for section, values in self.data.get('character_data', {}).items():

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
                    content=ft.Column(expand=True, spacing=6, controls=[]) # Forces container to take up space
                )

                # Go through every key/value pair in this section and add it to our text span list with formatting
                for key, value in values.items():
                    if isinstance(value, str) and (value or app.settings.data.get('show_empty_character_fields', True)):

                        # Add the each key for this section
                        container.content.controls.append(
                            ft.Row([
                                ft.TextField(
                                    label=key, hint_text=_get_help_text(key), value=value, 
                                    on_blur=lambda e, k=key: self._update_character_data(**{k: e.control.value}), expand=True,
                                    dense=True, capitalization=ft.TextCapitalization.SENTENCES, multiline=True,
                                    focus_color=self.data.get('color', "primary"), focused_border_color=self.data.get('color', "primary"), 
                                    cursor_color=self.data.get('color', "primary"),
                                ),
                                ft.IconButton(
                                    tooltip="Delete Field", icon=ft.Icons.DELETE_OUTLINE, mouse_cursor="click",
                                    on_click=lambda e, k=key: self._delete_character_data(**{k: ""}), icon_color=ft.Colors.ERROR
                                )
                            ])
                        )

                if len(container.content.controls) == 0:
                    container.content.controls.append(
                        ft.Row([
                            ft.Text("No fields to display", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                            ft.TextButton(
                                ft.Text("Delete Section?", color=ft.Colors.ERROR),
                                on_click=lambda e, s=section: self._delete_character_data(**{s: ""})
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
            await self.save_dict()

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
                    self.data.get('About', ""), on_blur=_change_about_data, expand=True, 
                    dense=True, capitalization=ft.TextCapitalization.SENTENCES, multiline=True,
                    focus_color="transparent", focused_border_color="transparent", 
                    cursor_color=self.data.get('color', "primary"), border_color="transparent"
                ), 
            )
        ], expand=True, spacing=0)

        
        # Header that holds our image, edit mode button, and about section
        header = ft.Row([
            ft.IconButton(img, tooltip="Upload Image", on_click=self._upload_character_image, mouse_cursor="click"),
            about_section
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

        body = ft.Column([
            header
        ], scroll="auto", expand=True, spacing=4)

        body.controls.extend(_load_character_data_controls())   

        self.body_container.content = body

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self): #this is the edit view currently
        ''' Reloads/Rebuilds our widget based on current data '''

        def _load_character_data_controls() -> list[ft.Control]:
            ''' Loads data from a dict into a given container '''

            # TODO: Skip empty ones check

            control_list = []
            
            # Go through our sections inside of our character data
            for section, values in self.data.get('character_data', {}).items():

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
                    if isinstance(value, str) and (value or app.settings.data.get('show_empty_character_fields', True)):


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
            ft.IconButton(img, tooltip="Upload Image", on_click=self._upload_character_image, mouse_cursor="click"),
            about_section
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)


        # Body that holds the rest of our widget
        body = ft.Column(
            controls=[header],
            scroll="auto", expand=True, spacing=4
        )

        # Load in our character data controls after the header
        body.controls.extend(_load_character_data_controls())   

        # Set the body we built
        self.body_container.content = body

        # Call render widget (from Widget class) to update the UI
        self._render_widget()