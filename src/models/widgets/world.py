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
                'tag': "world",     
                'color': app.settings.data.get('default_world_color'),   
                'edit_mode': bool,              # Whether we are in edit mode or not

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

        # Dict of different worlds and their maps stored
        #self.maps = {}

        self.locations = {}
        self.lore = {}
        self.power_systems = {}         # Tie to any
        self.social_systems = {}        # Tie to countries, tribes, continents, etc
        self.geography = {}             # Tie to any
        self.technology = {}            # Tie to any
        self.history = {}               # Tie to any
        self.governments = {}           # Tie to countries, tribes, etc

        # Load our live objects from our data
        #self.load_maps() 
        self.load_lore()
        self.load_power_systems()
        self.load_social_systems()
        self.load_geography()
        self.load_technology()
        self.load_history()

        self.icon = ft.Icon(ft.Icons.PUBLIC_OUTLINED, size=100, color=self.data.get('color', "primary"), expand=False)

        self.reload_tab()
        self.reload_widget()
    

    def load_lore(self):
        pass

    def load_power_systems(self):
        pass

    def load_social_systems(self):
        pass

    def load_geography(self):
        pass

    def load_technology(self):
        pass

    def load_history(self): 
        pass

    def load_governments(self):
        pass

    def _update_world_data(self, key: str, **kwargs):
        ''' Updates our world data field with a new value '''

        for k, value in kwargs.items():
            self.data['world_data'][key][k] = value

        
        self.save_dict()
        #self.reload_widget()

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
        ''' Called when the new custom field button is clicked '''

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
                
                
                
                case _:
                    return None


        def _load_dict_data(dict: dict, container: ft.Container, sub_key: str=""):
            ''' Loads data from a dict into a given container '''
            for key, value in dict.items():
                if isinstance(value, str):
                    text_control = ft.TextField(
                        expand=True, value=value, dense=True, multiline=True, hint_text=_get_help_text(key),
                        capitalization=ft.TextCapitalization.SENTENCES, adaptive=True, label=key.capitalize(),
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
                    
                    

        # Column we will append to for the bot of our view. Has our icon, and exit edit mode button
        # TODO: Foreground decoration when hovering adds the ("upload image" button)
        body = ft.Column([
            ft.Row([
                self.icon,
                ft.IconButton(tooltip="Exit Edit Mode", icon=ft.Icons.EDIT_OFF_OUTLINED, icon_color=self.data.get('color', None), on_click=self._edit_mode_clicked),
                #ft.Divider(color="transparent"),    # Used as new line
            ], wrap=True),
        ], scroll="auto", expand=True)


        # Create a container for our dicts that we have data in and load them. 
        template_data_container = ft.Container(            # For basic info
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(5), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.Column([]), 
        )
        summary_container = ft.Container(            # For basic info
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(5), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.TextField(
                expand=True, value=self.data.get('world_data', {}).get('Summary', ""), dense=True, multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=lambda e: self._update_world_data('Summary', e.control.value),
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


        row1.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Summary", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                ], spacing=0),
                ft.Row([summary_container])
            ], expand=True, spacing=4)
        )
        
        if 'Template Data' not in self.data.get('world_data', {}):
                pass
        else:
            
            template_title = self.data.get('character_data', {}).get('Template Data', {}).get('Template Name', 'Template Data')
            row1.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text(template_title, style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14), color=self.data.get('color', None), selectable=True, expand=True),
                        ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Template Data", "Template"), icon_color=self.data.get('color', None)),

                    ], spacing=0),
                    ft.Row([template_data_container])
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
        row2.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Lore", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Lore", "Lore"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([lore_container])
            ], expand=True, spacing=4)
        )
        row3.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Social Systems", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Social Systems", "Social System"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([social_systems_container])
            ], expand=True, spacing=4)
        )
        row3.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Power Systems", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Power Systems", "Power System"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([power_systems_container])
            ], expand=True, spacing=4)
        )
        row4.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Geography", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Geography", "Geography"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([geography_container])
            ], expand=True, spacing=4)
        )
        row4.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Technology", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Technology", "Technology"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([technology_container])
            ], expand=True, spacing=4)
        )
        row5.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("History", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("History", "History"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([history_container])
            ], expand=True, spacing=4)
        )
        row5.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Governments", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Governments", "Government"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([governments_container])
            ], expand=True, spacing=4)
        )
        row6.controls.append(
            ft.Column([
                ft.Row([
                    ft.Container(width=6),
                    ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ft.IconButton(tooltip="Add Custom Field", icon=ft.Icons.NEW_LABEL_OUTLINED, on_click=lambda e: self._new_field_clicked("Custom Fields", "Custom"), icon_color=self.data.get('color', None)),

                ], spacing=0),
                ft.Row([custom_fields_container])
            ], expand=True, spacing=4)
        )
        

        body.controls.append(ft.Container(padding=ft.padding.only(right=8), content=ft.Column([row1, row2, row3, row4, row5, row6], spacing=16)))

        self.body_container.content = body


        self._render_widget()

    # Called to reload our widget UI
    def reload_widget(self):
        ''' Reloads our world building widget '''


        def _load_dict_data(dict: dict, container: ft.Container):
            ''' Loads data from a dict into a given container '''
            for key, value in dict.items():
                if isinstance(value, str):
                    # Treat Goals as a list for display purposes
                    if "\n" in value:  
                        text_control = ft.Text(
                            expand=True, selectable=True, 
                            spans=[ft.TextSpan(f"{key.capitalize()}: ", ft.TextStyle(weight=ft.FontWeight.BOLD))]   # Key is bold with formatting
                        )
                        # Treat string as a list and split by new lines or commas
                        values = [v.strip() for v in value.replace('\n', ',').split(',') if v.strip()]
                        for val in values:
                            text_control.spans.append(ft.TextSpan(f"\n\t\u2022\t{val.capitalize()}"))

                        container.content.controls.append(text_control)

                    else:
                        text_control = ft.Text(
                            expand=True, selectable=True, 
                            spans=[
                                ft.TextSpan(f"{key.capitalize()}: ", ft.TextStyle(weight=ft.FontWeight.BOLD)),   # Key is bold with formatting
                                ft.TextSpan(f"{value.capitalize()}")    # Value normal
                            ]
                        )
                        container.content.controls.append(text_control)
                    

        self.reload_tab()

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
            template_data_container = ft.Container(            # For basic info
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(5), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), 
                content=ft.Column([]), 
            )
            summary_container = ft.Container(            # For basic info
                padding=ft.padding.all(8), border_radius=ft.border_radius.all(5), expand=True,
                border=ft.border.all(2, ft.Colors.OUTLINE), 
                content=ft.Text(
                    self.data.get('world_data', {}).get('Summary', ""),
                    expand=True, selectable=True, 
                )
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

            _load_dict_data(self.data.get('world_data', {}).get('Template Data', {}), template_data_container)
            _load_dict_data(self.data.get('world_data', {}).get('Locations', {}), locations_container)
            _load_dict_data(self.data.get('world_data', {}).get('Lore', {}), lore_container)
            _load_dict_data(self.data.get('world_data', {}).get('Power Systems', {}), power_systems_container)
            _load_dict_data(self.data.get('world_data', {}).get('Social Systems', {}), social_systems_container)
            _load_dict_data(self.data.get('world_data', {}).get('Geography', {}), geography_container)
            _load_dict_data(self.data.get('world_data', {}).get('Technology', {}), technology_container)
            _load_dict_data(self.data.get('world_data', {}).get('History', {}), history_container)
            _load_dict_data(self.data.get('world_data', {}).get('Custom Fields', {}), custom_fields_container)

            row1 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            row2 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            row3 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            row4 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            row5 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            row6 = ft.Row(alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)

            
                
            row1.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Summary", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True, expand=True)
                    ], spacing=0),
                    ft.Row([summary_container])
                ], expand=True, spacing=4)
            )
            
            if 'Template Data' not in self.data.get('world_data', {}):
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
            row2.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Locations", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([locations_container])
                ], expand=True, spacing=4)
            )
            row2.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Lore", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([lore_container])
                ], expand=True, spacing=4)
            )
            row3.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Social Systems", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([social_systems_container])
                ], expand=True, spacing=4)
            )
            row3.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Power Systems", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([power_systems_container])
                ], expand=True, spacing=4)
            )
            row4.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Geography", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([geography_container])
                ], expand=True, spacing=4)
            )
            row4.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Technology", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([technology_container])
                ], expand=True, spacing=4)
            )
            row5.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("History", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([history_container])
                ], expand=True, spacing=4)
            )
            row5.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Governments", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([governments_container])
                ], expand=True, spacing=4)
            )
            row6.controls.append(
                ft.Column([
                    ft.Row([
                        ft.Container(width=6),
                        ft.Text("Custom Fields", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Row([custom_fields_container])
                ], expand=True, spacing=4)
            )
            

            body.controls.append(ft.Container(padding=ft.padding.only(right=8), content=ft.Column([row1, row2, row3, row4, row5, row6], spacing=16)))

            self.body_container.content = body


            self._render_widget()



