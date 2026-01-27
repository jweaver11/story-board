''' 
Our widget class that displays our world and lore information. Essentially, all information not displayed visually on the maps goes here
Maps can tie into one owner 'world' widget
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
    def __init__(self, title: str, page: ft.Page, directory_path: str, story: Story, data: dict=None):
        
        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,  
            page = page,   
            directory_path = directory_path,  
            story = story,       
            data = data,    
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

                # World data
                'world_data': {
                    'Summary': str,
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
      
        self.reload_widget()
    

    

    def _update_world_data(self, key: str, **kwargs):
        ''' Updates our world data field with a new value '''

        for k, value in kwargs.items():
            self.data['world_data'][key][k] = value

        self.save_dict()

    def _update_summary(self, value: str):
        ''' Updates our world summary field with a new value '''

        self.data['world_data']['Summary'] = value
        self.save_dict()

    def _delete_world_data(self, sub_key: str="", **kwargs):
        ''' Deletes fields from the character data dict or up to one sub dict '''

        for key in kwargs.keys():
            if sub_key != "":
                if key in self.data['world_data'][sub_key]:
                    del self.data['world_data'][sub_key][key]
            else:
                if key in self.data['world_data']:
                    del self.data['world_data'][key]
                
        self.save_dict()
        self.reload_widget()

    def _new_field_clicked(self, sub_key: str, category: str=""):
        ''' Called when the new field button is clicked '''

        if 'world_data' not in self.data:
            self.data['world_data'] = {}

        if sub_key not in self.data['world_data']:
            self.data['world_data'][sub_key] = {}

        def create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            
            field_name = return_safe_name(field_name_input.value)
            
            if not field_name:
                self.p.close(dlg)
                return  # Don't create if empty
            
            # Add the field to data if it doesn't exist
            if field_name not in self.data['world_data'][sub_key]:
                self.data['world_data'][sub_key][field_name] = ""
            
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
        
        try:
            dlg.open = True
            self.p.open(dlg)

        except Exception as ex:
            print(f"Error opening dialog: {ex}") 

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


        def _load_dict_data(dict: dict, container: ft.Container, sub_key: str=""):
            ''' Loads data from a dict into a given container '''
            for key, value in dict.items():
                if isinstance(value, str):
                    text_control = ft.TextField(
                        expand=True, label=key.capitalize(), value=value, dense=True, multiline=True, hint_text=_get_help_text(key),
                        capitalization=ft.TextCapitalization.SENTENCES, adaptive=True, 
                        on_blur=lambda e, k=key: self._update_world_data(key=sub_key, **{k: e.control.value})
                    )

                    container.content.controls.append(
                        ft.Row([
                            text_control,
                            ft.IconButton(
                                tooltip="Delete Field", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,   
                                on_click=lambda e, k=key: self._delete_world_data(sub_key=sub_key, **{k: None})
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
            img = ft.Icon(ft.Icons.PUBLIC_OUTLINED, size=100, color=self.data.get('color', "primary"), expand=False)

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
                fp
            ], wrap=True),
        ], scroll="auto", expand=True)


        # Create a container for our dicts that we have data in and load them. 
        template_data_container = ft.Container(            # For basic info
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.Column([]), 
        )
        summary_container = ft.Container(            # For basic info
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.TextField(
                expand=True, value=self.data.get('world_data', {}).get('Summary', ""), dense=True, multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=lambda e: self._update_summary(e.control.value),
                border=ft.InputBorder.NONE,                  
            ),
        )
        locations_container = ft.Container(  # For physical description
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )   
        lore_container = ft.Container(                # For family
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )
        power_systems_container = ft.Container(                # For origin 
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.Column([]),
        )
        social_systems_container = ft.Container(           # For connections
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )
        geography_container = ft.Container(           # For connections
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )
        technology_container = ft.Container(           # For connections
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]),
        )
        history_container = ft.Container(           # For connections
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]),
        )
        governments_container = ft.Container(           # For connections
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]),
        )
        custom_fields_container = ft.Container(        # For custom fields
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE),
            content=ft.Column([]), 
        )

        
        _load_dict_data(self.data.get('world_data', {}).get('Template Data', {}), template_data_container, "Template Data")
        _load_dict_data(self.data.get('world_data', {}).get('Locations', {}), locations_container, "Locations")
        _load_dict_data(self.data.get('world_data', {}).get('Lore', {}), lore_container, "Lore")
        _load_dict_data(self.data.get('world_data', {}).get('Power Systems', {}), power_systems_container, "Power Systems")
        _load_dict_data(self.data.get('world_data', {}).get('Social Systems', {}), social_systems_container, "Social Systems")
        _load_dict_data(self.data.get('world_data', {}).get('Geography', {}), geography_container, "Geography")
        _load_dict_data(self.data.get('world_data', {}).get('Technology', {}), technology_container, "Technology")
        _load_dict_data(self.data.get('world_data', {}).get('History', {}), history_container, "History")
        _load_dict_data(self.data.get('world_data', {}).get('Governments', {}), governments_container, "Governments")
        _load_dict_data(self.data.get('world_data', {}).get('Custom Fields', {}), custom_fields_container, "Custom Fields")


        # Create rows for each section
        row1 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row2 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row3 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row4 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row5 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row6 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row7 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row8 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row9 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
        row10 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)


        row1.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Summary", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True),
                ], spacing=0),
                ft.Row([summary_container])
            ], expand=True, spacing=4)
        )
        
        
        row2.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Locations", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Locations", "Location"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([locations_container])
            ], expand=True, spacing=4)
        )
        row3.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Lore", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Lore", "Lore"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([lore_container])
            ], expand=True, spacing=4)
        )
        row4.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Social Systems", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Social Systems", "Social System"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([social_systems_container])
            ], expand=True, spacing=4)
        )
        row5.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Power Systems", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Power Systems", "Power System"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([power_systems_container])
            ], expand=True, spacing=4)
        )
        row6.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Geography", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Geography", "Geography"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([geography_container])
            ], expand=True, spacing=4)
        )
        row7.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Technology", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Technology", "Technology"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([technology_container])
            ], expand=True, spacing=4)
        )
        row8.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("History", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("History", "History"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([history_container])
            ], expand=True, spacing=4)
        )
        row9.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Governments", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Governments", "Government"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([governments_container])
            ], expand=True, spacing=4)
        )
        row10.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Custom Fields", "Custom"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([custom_fields_container])
            ], expand=True, spacing=4)
        )
        

        body.controls.append(ft.Container(padding=ft.padding.only(right=8), content=ft.Column([row1, row2, row3, row4, row5, row6, row7, row8, row9, row10], spacing=16)))

        self.body_container.content = body


    # Called to reload our widget UI
    def reload_widget(self):
        ''' Reloads our world building widget '''


        def _load_dict_data(dict: dict, container: ft.Container):
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
                img = ft.Icon(ft.Icons.PUBLIC_OUTLINED, size=100, color=self.data.get('color', "primary"), expand=False)

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
            template_data_container = ft.Container(            # For basic info
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), 
                content=ft.Text(expand=True, selectable=True, spans=[]), 
            )
            summary_container = ft.Container(            # For basic info
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), 
                content=ft.Text(
                    self.data.get('world_data', {}).get('Summary', ""),
                    expand=True, selectable=True, 
                )
            )
            locations_container = ft.Container(  # For physical description
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )   
            lore_container = ft.Container(                # For family
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )
            power_systems_container = ft.Container(                # For origin 
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), 
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )
            social_systems_container = ft.Container(           # For connections
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )
            geography_container = ft.Container(           # For connections
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )
            technology_container = ft.Container(           # For connections
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )
            history_container = ft.Container(           # For connections
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )
            governments_container = ft.Container(           # For connections
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )
            custom_fields_container = ft.Container(        # For custom fields
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(10), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE),
                content=ft.Text(expand=True, selectable=True, spans=[]),
            )

            _load_dict_data(self.data.get('world_data', {}).get('Template Data', {}), template_data_container)
            _load_dict_data(self.data.get('world_data', {}).get('Locations', {}), locations_container)
            _load_dict_data(self.data.get('world_data', {}).get('Lore', {}), lore_container)
            _load_dict_data(self.data.get('world_data', {}).get('Power Systems', {}), power_systems_container)
            _load_dict_data(self.data.get('world_data', {}).get('Social Systems', {}), social_systems_container)
            _load_dict_data(self.data.get('world_data', {}).get('Geography', {}), geography_container)
            _load_dict_data(self.data.get('world_data', {}).get('Technology', {}), technology_container)
            _load_dict_data(self.data.get('world_data', {}).get('History', {}), history_container)
            _load_dict_data(self.data.get('world_data', {}).get('Custom Fields', {}), custom_fields_container)

            # Set our columns to hold our data sections
            column1 = ft.Column([], expand=True, spacing=4, alignment=ft.MainAxisAlignment.START)
            column2 = ft.Column([], expand=True, spacing=4, alignment=ft.MainAxisAlignment.START)
  
            if locations_container.content.spans:
                column2.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Locations", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0), 
                )
                column2.controls.append(ft.Row([locations_container]))
                column2.controls.append(ft.Container(height=16))  # Spacer

            if lore_container.content.spans:
                column1.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Lore", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column1.controls.append(ft.Row([lore_container]))
                column1.controls.append(ft.Container(height=16))  # Spacer
            if power_systems_container.content.spans:
                column2.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Power Systems", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column2.controls.append(ft.Row([power_systems_container]))
                column2.controls.append(ft.Container(height=16))  # Spacer

            if social_systems_container.content.spans:
                column1.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Social Systems", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column1.controls.append(ft.Row([social_systems_container]))
                column1.controls.append(ft.Container(height=16))  # Spacer

            if geography_container.content.spans:
                column2.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Geography", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column2.controls.append(ft.Row([geography_container]))
                column2.controls.append(ft.Container(height=16))  # Spacer

            if governments_container.content.spans:
                column1.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Governments", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column1.controls.append(ft.Row([governments_container]))
                column1.controls.append(ft.Container(height=16))  # Spacer

            if technology_container.content.spans:
                column1.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Technology", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column1.controls.append(ft.Row([technology_container]))
                column1.controls.append(ft.Container(height=16))  # Spacer

            if history_container.content.spans:
                column1.controls.append(
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("History", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                )
                column1.controls.append(ft.Row([history_container]))
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
        
            body.controls.append(
                ft.Container(
                    padding=ft.padding.only(right=8), 
                    content=ft.Column([
                        ft.Row([
                            ft.Container(width=6), 
                            ft.Text("Summary", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                        ], spacing=0), 
                        ft.Row([summary_container]),
                        ft.Container(height=16),  # Spacer  
                        ft.Row([column1, column2], vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
                    ], spacing=0)
                )
            )

            self.body_container.content = body

            self._render_widget()



