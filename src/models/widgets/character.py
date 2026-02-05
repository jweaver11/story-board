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
from models.mini_widgets.connection import Connection
from models.app import app
from utils.safe_string_checker import return_safe_name
from models.dataclasses.character_template import default_character_template_data_dict
from utils.character_connection_alert_dlg import new_character_connection_clicked




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
        self.body_container.padding = ft.padding.only(top=8, bottom=8, left=8, right=0)

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
                # If this dict doesn't exist, we create it with our active template data. If we fail to pull that, we use a default template (which has quite a lot)
                'character_data': app.settings.data.get('character_templates', {}).get(app.settings.get('active_character_template', ""), default_character_template_data_dict()) 
                if data is None or 'character_data' not in data else data['character_data'],
            },
        ) 


        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init


        # TODO: RENAME AND DELETE Will need to be custom here, to alter ccm and connections that used our old name and key
        
    
    def _new_field_clicked(self, sub_key: str, category: str=""):
        ''' Called when the new field button is clicked '''

        if 'character_data' not in self.data:
            self.data['character_data'] = {}

        if sub_key not in self.data['character_data']:
            self.data['character_data'][sub_key] = {}

        def create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            
            field_name = return_safe_name(field_name_input.value)
            
            if not field_name:
                self.p.close(dlg)
                return  # Don't create if empty
            
            # Add the field to data if it doesn't exist
            if field_name not in self.data['character_data'][sub_key]:
                self.data['character_data'][sub_key][field_name] = ""
            
            # Save and reload
            self.save_dict()
            self.p.close(dlg)
            self.reload_widget()
                                
            

        # Create a dialog to ask for the field name
        field_name_input = ft.TextField(
            label="Field Name", hint_text=f"New {category} Name",
            autofocus=True, capitalization=ft.TextCapitalization.SENTENCES,
            on_submit=create_field,     # Closes the overlay when submitting
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Create New {category} Field"),
            content=field_name_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                ft.TextButton("Create", on_click=create_field),
            ],
        )
        
        
        dlg.open = True
        self.p.open(dlg)



       

    

    
    # Called when a field is changed in edit mode
    def _update_character_data(self, sub_key: str="", **kwargs):
        ''' Updates the character data dict or up to one sub dict '''

        will_reload_rail = False
    
        sort_method = self.story.data.get('settings', {}).get('character_rail_sort_by', "Role")

        for k, value in kwargs.items():
            self.data['character_data'][sub_key][k] = value
            if sort_method == k and self.story.data.get('selected_rail', "") == "characters":
                will_reload_rail = True

        
        self.save_dict()

        
        if will_reload_rail:
            self.story.active_rail.content.reload_rail()

    def _delete_character_data(self, sub_key: str="", **kwargs):
        ''' Deletes fields from the character data dict or up to one sub dict '''

        for key in kwargs.keys():
            if sub_key != "":
                if key in self.data['character_data'][sub_key]:
                    del self.data['character_data'][sub_key][key]
            else:
                if key in self.data['character_data']:
                    del self.data['character_data'][key]
                
        self.save_dict()
        self.reload_widget()

        # Check if we're sorting by the updated key, and if characters rail is selected. If it is, reload the rail
        sort_method = self.story.data.get('settings', {}).get('character_rail_sort_by', "Role")
        if sort_method == key and self.story.data.get('selected_rail', "") == "characters":
            self.story.active_rail.content.reload_rail()

    async def _files_uploaded(self, e: ft.FilePickerResultEvent):

        if e.files:
            file_path = e.files[0].path
            #print("File path:", file_path)

            try:
                import base64

                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    # Save to our data
                    self.data['image_base64'] = f"{encoded_string}"
                    self.save_dict()
                    self.reload_widget()
                    print("Success")

            except Exception as ex:
                print(f"Error uploading file: {ex}")

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
                    return "Protagonist, Antagonist, etc..."
                case "Goals":
                    return "Separate Goals with new lines"
                
                case _:
                    return None


        def _load_dict_data(dict: dict, container: ft.Container, sub_key: str=""):
            ''' Loads data from a dict into a given container '''
            for key, value in dict.items():
                if isinstance(value, str):
                    text_control = ft.TextField(
                        expand=True, label=key.capitalize(), value=value, dense=True, multiline=True, hint_text=_get_help_text(key),
                        capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                        on_blur=lambda e, k=key: self._update_character_data(sub_key, **{k: e.control.value})
                    )

                    
                    container.content.controls.append(
                        ft.Row([
                            text_control,
                            ft.IconButton(
                                tooltip="Delete Field", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,   
                                on_click=lambda e, k=key: self._delete_character_data(sub_key=sub_key, **{k: None})
                            ),
                        ])
                    )


        
        if self.data.get('image_base64', ""):
            img = ft.Container(
                ft.Image(
                    src_base64=self.data.get('image_base64', ""),
                    width=100,
                    height=100,
                    fit=ft.ImageFit.FILL,
                ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            )
        else:
            img = ft.Icon(ft.Icons.PERSON_OUTLINE, size=100, color=self.data.get('color', "primary"), expand=False)

        fp = ft.FilePicker(on_result=self._files_uploaded)
            
        # Column we will append to for the bot of our view. Has our icon, and exit edit mode button
        # TODO: Foreground decoration when hovering adds the ("upload image" button)
        body = ft.Column([
            ft.Row([
                ft.IconButton(
                    content=img, tooltip="Upload Image", on_click=lambda e: fp.pick_files(
                    allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg", "webp"])
                ),
                ft.IconButton(tooltip="Exit Edit Mode", icon=ft.Icons.EDIT_OFF_OUTLINED, icon_color=self.data.get('color', None), on_click=self._edit_mode_clicked),
                fp, 
            ], wrap=True),
        ], scroll="auto", expand=True)


        # Create a container for our dicts that we have data in and load them. 
        basic_info_container = ft.Container(            # For basic info
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.Column([]), 
        )
        template_data_container = ft.Container(         # For template data
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.Column([]), 
        )
        physical_description_container = ft.Container(  # For physical description
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )   
        family_container = ft.Container(                # For family
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )
        origin_container = ft.Container(                # For origin 
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.Column([]),
        )
        connections_container = ft.Container(           # For connections
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )
        custom_fields_container = ft.Container(        # For custom fields
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )

        # Load the dicts into controls
        _load_dict_data(self.data.get('character_data', {}).get('Basic Info', {}), basic_info_container, "Basic Info")
        _load_dict_data(self.data.get('character_data', {}).get('Template Data', {}), template_data_container, "Template Data")
        _load_dict_data(self.data.get('character_data', {}).get('Physical Description', {}), physical_description_container, "Physical Description")
        _load_dict_data(self.data.get('character_data', {}).get('Family', {}), family_container, "Family")
        _load_dict_data(self.data.get('character_data', {}).get('Origin', {}), origin_container, "Origin")
        #_load_dict_data(self.story.data.get('connections'), connections_container, "Connections")
        _load_dict_data(self.data.get('character_data', {}).get('Custom Fields', {}), custom_fields_container, "Custom Fields")


        # Create rows for each section
        row1 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row2 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row3 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row4 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row5 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row6 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row7 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)


        # Add the labels and containers that have the data controls into the rows for formatting
        row1.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Basic Info", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Basic Info", "Basic Info"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([basic_info_container])
            ], expand=True, spacing=4)
        )
        # If we have temlpate data, this will add it to the page
        if 'Template Data' not in self.data.get('character_data', {}):
            pass
        else:
            
            template_title = self.data.get('character_data', {}).get('Template Data', {}).get('Template Name', 'Template Data')
            row2.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text(template_title, style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), color=self.data.get('color', None), selectable=True),
                        ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Template Data", "Template Data"), icon_color=self.data.get('color', None)),

                    ], spacing=0),
                    ft.Row([template_data_container])
                ], expand=True, spacing=4)
            )

        row3.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Physical Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Physical Description", "Physical Description"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([physical_description_container])
            ], expand=True, spacing=4)
        )
        row4.controls.append(
            
            ft.Column([
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Origin", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Origin", "Origin"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([origin_container])
            ], expand=True, spacing=4)
        )
        row5.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Family", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Family", "Family"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([family_container])
            ], expand=True, spacing=4)
        )
        row6.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Connections", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: new_character_connection_clicked(self.story), icon_color=self.data.get('color', None)),
                ], spacing=0),
                ft.Row([connections_container])
            ], expand=True, spacing=4)  
        )

        row7.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Custom Fields", "Custom"), icon_color=self.data.get('color', None)),
                ], spacing=0),
                ft.Row([custom_fields_container])
            ], expand=True, spacing=4)
        )

        body.controls.append(ft.Container(padding=ft.padding.only(right=8), content=ft.Column([row1, row2, row3, row4, row5, row6, row7], spacing=16)))

        self.body_container.content = body

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self): #this is the edit view currently
        ''' Reloads/Rebuilds our widget based on current data '''

        def _load_dict_data(dict: dict, container: ft.Container) -> list[ft.TextSpan]:
            ''' Loads data from a dict into a given container '''

            span_list = []
            dict_length = len(dict)
            idx = 0

            for key, value in dict.items():    
                
                if isinstance(value, str):
                    # Treat Goals as a list for display purposes
                    if "\n" in value:  
                        spans = [ft.TextSpan(f"{key.capitalize()}:\n", ft.TextStyle(weight=ft.FontWeight.BOLD))]  # Key is bold with formatting

                        # Treat string as a list and split by new lines or commas
                        values = [v.strip() for v in value.replace('\n', ',').split(',') if v.strip()]
                        for val in values:
                            spans.append(ft.TextSpan(f"\t\u2022\t{val.capitalize()}\n"))

                        spans.append(ft.TextSpan("\n"))  # Extra new line at end

                    # Everything else just gets simple display
                    else:
                        
                        spans = [ft.TextSpan(f"{key.capitalize()}: ", ft.TextStyle(weight=ft.FontWeight.BOLD))]   # Key is bold with formatting

                        if idx == dict_length - 1:  # Last item, no new line
                            spans.append(ft.TextSpan(f"{value}"))     # Last item, no new line
                        else:
                            spans.append(ft.TextSpan(f"{value}\n\n"))     # Rest of the value

                    # Only show the item if it has a value or if we are set to show empty fields
                    if value or app.settings.data.get('show_empty_character_fields', True):
                        span_list.extend(spans)

                idx += 1

            container.content.spans = span_list
            

                    
                
        
        # Rebuild out tab to reflect any changes
        self.reload_tab()


        # Check if we're in edit mode or not. If yes, build the edit view like this
        if self.data.get('edit_mode', False):
            self._edit_mode_view()
            self._render_widget()


        # If NOT in edit mode, build our normal view
        else:

            if self.data.get('image_base64', ""):
                img = ft.Container(
                    ft.Image(
                        src_base64=self.data.get('image_base64', ""),
                        width=100,
                        height=100,
                        fit=ft.ImageFit.FILL,
                    ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                )
            else:
                img = ft.Icon(ft.Icons.PERSON_OUTLINE, size=100, color=self.data.get('color', "primary"), expand=False)

            fp = ft.FilePicker(on_result=self._files_uploaded)

            body = ft.Column([
                ft.Row([
                    ft.IconButton(
                        content=img, tooltip="Upload Image", on_click=lambda e: fp.pick_files(
                        allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg", "webp"])
                    ),
                    ft.IconButton(tooltip="Edit Mode", icon=ft.Icons.EDIT_OUTLINED, icon_color=self.data.get('color', None), on_click=self._edit_mode_clicked),
                    fp
                ], wrap=True),
            ], scroll="auto", expand=True)

            # Create a container for our dicts that we have data in and load them. 
            basic_info_container = ft.Container(            # For basic info
                padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), 
                content=ft.Text(expand=True, selectable=True, spans=[]), 
            )
            template_data_container = ft.Container(         # For template data
                padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), 
                content=ft.Text(expand=True, selectable=True, spans=[]), 
            )
            physical_description_container = ft.Container(  # For physical description
                padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]), 
            )   
            family_container = ft.Container(                # For family
                padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),  
            )
            origin_container = ft.Container(                # For origin 
                padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), 
                content=ft.Text(expand=True, selectable=True, spans=[]), 
            )
            connections_container = ft.Container(           # For connections
                padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]), 
            )
            custom_fields_container = ft.Container(        # For custom fields
                padding=ft.padding.all(6), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]), 
            )

            _load_dict_data(self.data.get('character_data', {}).get('Template Data', {}), template_data_container)
            _load_dict_data(self.data.get('character_data', {}).get('Basic Info', {}), basic_info_container)
            _load_dict_data(self.data.get('character_data', {}).get('Physical Description', {}), physical_description_container)
            _load_dict_data(self.data.get('character_data', {}).get('Family', {}), family_container)
            _load_dict_data(self.data.get('character_data', {}).get('Origin', {}), origin_container)
            #_load_dict_data(self.data.get('character_data', {}).get('Connections', {}), connections_container)
            _load_dict_data(self.data.get('character_data', {}).get('Custom Fields', {}), custom_fields_container)

            # Set our columns to hold our data sections
            column1 = ft.Column([], expand=True, spacing=4, alignment=ft.MainAxisAlignment.START)
            column2 = ft.Column([], expand=True, spacing=4, alignment=ft.MainAxisAlignment.START)
            
            # If we have basic info, this will add it to the page. Protects against custom templates getting rid of certain sections
            if basic_info_container.content.spans:
                
                column1.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Basic Info", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column1.controls.append(ft.Row([basic_info_container]))
                column1.controls.append(ft.Container(height=16))  # Spacer

            # If we have temlpate data, this will add it to the page
            if 'Template Data' not in self.data.get('character_data', {}):
                pass
            else:
                
                if app.settings.data.get('show_empty_character_fields', True) or template_data_container.content.spans:
                    template_title = self.data.get('character_data', {}).get('Template Data', {}).get('Template Name', 'Template Data')
        
                    column2.controls.append(
                        ft.Row([
                            ft.Container(width=6), 
                            ft.Text(template_title, style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                        ], spacing=0),
                    )
                    column2.controls.append(ft.Row([template_data_container]))
                    column2.controls.append(ft.Container(height=16))  # Spacer

            if physical_description_container.content.spans:
                column2.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Physical Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0), 
                )
                column2.controls.append(ft.Row([physical_description_container]))
                column2.controls.append(ft.Container(height=16))  # Spacer

            if family_container.content.spans:
                column2.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Family", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column2.controls.append(ft.Row([family_container]))
                column2.controls.append(ft.Container(height=16))  # Spacer
            if origin_container.content.spans:
                column1.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Origin", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column1.controls.append(ft.Row([origin_container]))
                column1.controls.append(ft.Container(height=16))  # Spacer
            if app.settings.data.get('show_empty_character_fields', True):
                column1.controls.append(
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Connections", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),    
                )
                column1.controls.append(ft.Row([connections_container]))
                column1.controls.append(ft.Container(height=16))  # Spacer

            if custom_fields_container.content.spans:
                column2.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column2.controls.append(ft.Row([custom_fields_container]))
                column2.controls.append(ft.Container(height=16))  # Spacer


            body.controls.append(ft.Container(padding=ft.padding.only(right=8), content=ft.Column([ft.Row([column1, column2], vertical_alignment=ft.CrossAxisAlignment.START)], spacing=16)))
        
            self.body_container.content = body

            # Call render widget (from Widget class) to update the UI
            self._render_widget()