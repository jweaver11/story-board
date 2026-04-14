''' 
Model for our settings widget. Settings widget stores app and story settings, and displays them in a tab
A Settings object is created for every story
'''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from utils.alert_dialogs.character_connection import new_character_connection_clicked
from styles.colors import colors
import os
import json
from styles.colors import dark_gradient
from ui.menu_bar import create_menu_bar
from ui.workspaces_rail import WorkspacesRail
from models.dataclasses.character_template import default_character_template_data_dict
from styles.text_field import TextField

 
class Settings(ft.View):

    # Constructor
    def __init__(
        self, 
        page: ft.Page, 
        file_path: str, 
        story: Story = None, 
        data: dict = None,
        selected_index: int = 0,   # Which category to show when opening settings. 0 = Appearance, 1 = Widgets, 2 = Story, 3 = Templates, 4 = Resources
    ):
        
        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True
        
        # Constructor the parent widget class
        super().__init__(
            route=f"/settings",                                      # Sets our route for our new story
            padding=ft.Padding.only(top=0, left=0, right=0, bottom=0),      # No padding for the page
            spacing=0,                                                   # No spacing between menubar and rest of page
        )

        self.p = page   # Grabs our original page, as sometimes the reference gets lost. with all the UI changes that happen. p.update() always works
        self.route = "/settings"   # Sets our route for our settings view
        self.story = story
        self.file_path = file_path
        self.data = data
        self.selected_index = selected_index

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Settings the app uses and users do not directly change in the settings view
                'active_story': "/",    # Route to our active story
                'workspaces_rail_is_collapsed': bool,  # If the all workspaces rail is collapsed or not
                'active_rail_width': 225,  # Width of our active rail that we can resize
                'page_is_maximized': True,   # If the window is maximized or not
                'page_width': int,     # Last known page width
                'page_height': int,    # Last known page height
                'is_first_launch': True,    # If this is the first time the app has been launched or not

                # Paint settings for our canvas drawings to use as default that users can change
                'paint_settings': {

                    # Stroke styles
                    'color': "#FFFFFF,1.0",     # Hex color folowed by opacity
                    'stroke_width': 3,
                    'style': "stroke",
                    'stroke_cap': "round",
                    'stroke_join': "round",
                    'stroke_miter_limit': 10, 
                    'stroke_dash_pattern': None,

                    # Effects
                    'anti_alias': True,
                    'blur_image': int,
                    'blend_mode': "src_over",
                },               

                # Other canvas related settings that are not technically paint
                'canvas_settings':{
                    'erase_mode': False,                # Whether we're in erase mode or not
                    'saved_brushes': dict,              # Saved brushes the user has created that we can load
                    'current_brush_name': "stroke",   # Name of the currently selected brush, either default or custom. Just used for display purposes
                },

                # Settings the user can change in the settings view
                # Appearance settings
                'theme_mode': "dark",       # the apps theme mode, dark or light
                'theme_color': "blue",   # the color scheme of the app. Defaults to blue
                'change_name_colors_based_on_morality': True,   # If characters names change colors in char based on morality
                'workspaces_rail_order': [      # Order of the workspace rail
                    "content",
                    "canvas",
                    "characters",
                    "plotlines",
                    "world_building",
                    "planning",
                ],
                
                # App settings
                'confirm_item_delete': True,   # If we should confirm before deleting items

                # Widget settings
                'default_canvas_color': "primary",
                'default_canvas_board_color': "primary",
                'default_chapter_color': "primary",   # Default colors for new widgets
                'default_character_color': "primary",
                'default_character_connection_map_color': "primary", 
                'default_map_color': "primary",
                'default_note_color': "primary",
                'default_planning_color': "primary",
                'default_plotline_color': "primary",
                'default_world_color': "primary",
                'default_item_color': "primary",
                'default_chart_color': "primary",

                'default_category_color': "primary",    # Categories thrown in here

                'default_canvas_pin_location': "main",      # Default pin locations for new widgets (all in main for now)
                'default_canvas_board_pin_location': "main",
                'default_chapter_pin_location': "main",   
                #'default_character_pin_location': "left",
                'default_character_pin_location': "main",
                'default_character_connection_map_pin_location': "main",
                'default_map_pin_location': "main",
                #'default_note_pin_location': "right",
                'default_note_pin_location': "main",
                'default_planning_pin_location': "main",
                'default_plotline_pin_location': "main",
                #'default_world_pin_location': "right",
                'default_item_pin_location': "main",
                'default_object_pin_location': "main",
                #'default_item_pin_location': "right",
                'default_world_pin_location': "main",
                'default_chart_pin_location': "main",

                'active_character_template': "Default",             # Which template is being used for new characters for new stories - they default to this
                'active_world_template': "Default",                 # Which template is being used for new worlds for new stories - they default to this
                'show_empty_character_fields': True,                # If we show empty character fields in character widget or not
                'division_labels_direction': "bottom",              # If the division labels are on top of the plotline instead of below

                # Hold our default character templates
                'character_templates': {    
                    'Default': default_character_template_data_dict(),
                    # Fantasy/DnD
                },   
                'world_templates': {    # TODO
                    'Default': dict,
                }
            }, 
        )

        if is_new:
            self.p.run_task(self.save_dict)

    def before_update(self):
        print(f"Successful update for settings")
        return super().before_update()
        

    # Called whenever there are changes in our data
    async def save_dict(self):
        ''' Saves our current data to the json file '''

        print("Saved settings")

        try:
            
            # Save the data to the file (creates file if doesnt exist)
            with open(self.file_path, "w", encoding='utf-8') as f:   
                json.dump(self.data, f, indent=4)
        
        # Handle errors
        except Exception as e:
            print(f"Error saving widget to {self.file_path}: {e}") 
            print("Data that failed to save: ", self.data)

    # Called for little data changes
    def change_data(self, **kwargs):
        ''' Changes a key/value pair in our data and saves the json file '''
        # Called by:
        # app.settings.change_data(**{'key': value, 'key2': value2})
        # or
        # app.settings.change_data(key=value)

        try:
            for key, value in kwargs.items():
                self.data.update({key: value})

            self.p.run_task(self.save_dict)

        # Handle errors
        except Exception as e:
            print(f"Error changing settings data: {e}")


    async def _close_settings(self, e=None):
        ''' Closes the settings view and returns to the story or home view '''
        await self.p.push_route(self.story.route if self.story is not None else "/")

    async def page_closed(self, e=None):
        ''' Called when the page is closed. Saves any last changes to settings before exit '''

        if self.story is not None:
            for widget in self.story.widgets:
                if widget.save_counter > 0:
                    widget.save_counter = 15   # Will force a file write to widgets who have unwritten changes to their file
                    await widget.save_dict()
        
        


    def create_character_template(self, template_name: str, data: dict):
        ''' Creates a new character template with the given name '''
        from utils.safe_string_checker import return_safe_name

        print("Creating new character template: ", template_name, " with data: ", data)

        safe_key = return_safe_name(template_name)

        self.data['character_templates'][safe_key] = {
            'title': template_name,
            'template_data': data,
        }
        self.p.run_task(self.save_dict)
        

    # Called when the page is resized
    def page_resized(self, e=None):
        ''' This is set inside of app.load_settings() to be called whenever the page is resized. Saves the new page size to data/if its maximized'''
        from models.app import app  

        # Catch page resizing when app is initializing and ignore them
        if app.ignore_settings_change:      
            return
        
        # If we're minmized, save nothing and just return
        if self.p.window.minimized:
            return

        # If we maximized the page, just save that, not the size
        if self.p.window.maximized:
            self.data['page_is_maximized'] = True
            self.p.run_task(self.save_dict)
            return
        
        # If page not maximized or minimized, save the size
        else:
            self.data['page_is_maximized'] = False
            self.data['page_width'] = self.p.width
            self.data['page_height'] = self.p.height
            self.p.run_task(self.save_dict)
            return

        
    def _get_color_options(e=None, is_theme_dropdown: bool=False):
        ''' Adds our choices to the color scheme dropdown control'''
        # Create a list to hold our dropdown options
        options = []
        

        # Runs through our colors above and adds them to the dropdown
        for color in colors:
            if is_theme_dropdown:
                if color in ["white", "grey", "black", "primary"]:
                    continue   # Skip these colors for theme dropdown, as they are not supported
            
            options.append(
                ft.DropdownOption(
                    key=color.capitalize(),
                    content=ft.Text(
                        value=color.capitalize(),
                        color=color,
                    ),
                )
            )
        return options

    
        
    # Called when we select a new category of settings in our settings view
    def _settings_category_changed(self, e=None, template_name: str=None):
        ''' Determines which category is now active and changes our body container to match '''

        if e is None:
            idx = self.selected_index
        else:
            idx = e.control.selected_index 

        self.selected_index = idx   # Make sure they are syced

        match idx:
            case 0:
                self.body_container.content = self._load_appearance_settings()
            case 1:
                self.body_container.content = self._load_widgets_settings()
            case 2:
                self.body_container.content = self._load_story_settings()
            case 3:
                self.body_container.content = self._load_template_settings(template_name)
            case 4:
                self.body_container.content = self._load_resources_settings()
                
        try:
            self.update()
        except Exception as _:
            pass
        
    # Called when appearance settings category is selected
    def _load_appearance_settings(self) -> ft.Container:
        ''' Contains toggle for theme mode, and color scheme dropdown '''
        
        
        # Called when a dropdown option is selected. Saves our choice, and applies it to the page
        def _set_theme_color(e):
            ''' Saves our color scheme choice and applies it to the page '''

            # Save our color scheme choice to our objects data
            self.data['theme_color'] = e.control.value
            e.control.color = e.control.value   # Changes the dropdown text color to match the selected color

            # Applies this theme to our page, for both dark and light themes
            self.p.theme = ft.Theme(color_scheme_seed=self.data.get('theme_color', "blue"))
            self.p.dark_theme = ft.Theme(color_scheme_seed=self.data.get('theme_color', "blue"))

            # Save the updated settings to the JSON file and update the page
            self.p.run_task(self.save_dict)
            self.p.update()

        # Dropdown so app can change their color scheme
        theme_color_dropdown = ft.Dropdown(
            label="Theme Color", tooltip="Select the primary color scheme for the app",
            capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
            options=self._get_color_options(True),
            on_select=_set_theme_color,
            value=self.data.get('theme_color', "blue"),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            color=self.data.get('theme_color', None),
            dense=True, data="theme_color_dropdown",
        )


        # Called when theme switch is changed. Switches from dark to light theme, or reverse
        def _toggle_theme(e):
            ''' Changes our settings theme data from dark to light or reverse '''

            new_theme_mode = e.control.data   # Grabs the theme mode this button represents

            if new_theme_mode == self.data['theme_mode']:
                return   # No need to change anything if we're already on this theme
            
            else:
                if new_theme_mode == "dark":
                    e.control.border = ft.Border.all(2, ft.Colors.PRIMARY)
                    self.light_theme_button.border = ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT)
                else:
                    e.control.border = ft.Border.all(2, ft.Colors.PRIMARY)
                    self.dark_theme_button.border = ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT)

            self.data['theme_mode'] = new_theme_mode
            self.p.run_task(self.save_dict)
            self.p.theme_mode = self.data['theme_mode']
            self.p.update()

        def _set_default_category_color(e):
            ''' Sets the default color for new categories '''

            new_color = e.control.value    # Grabs the new color selected   

            self.data['default_category_color'] = new_color

            # Save our updated settings
            self.p.run_task(self.save_dict)
            e.control.color = new_color   # Changes the dropdown text color to match the selected color
            e.control.update()


            

        # Button that changes the theme from dark or light when clicked
        self.light_theme_button = ft.Container(
            content=ft.Icon(ft.Icons.LIGHT_MODE, color=ft.Colors.YELLOW_700), height=100, width=100, border_radius=10, data="light",
            border=ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT) if self.data['theme_mode'] == "dark" else ft.Border.all(2, ft.Colors.PRIMARY), 
            bgcolor=ft.Colors.WHITE, on_click=_toggle_theme, tooltip="Set light mode", ink=True
        )
        self.dark_theme_button = ft.Container(
            content=ft.Icon(ft.Icons.DARK_MODE, color=ft.Colors.WHITE), height=100, width=100, border_radius=10, data="dark",
            border=ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT) if self.data['theme_mode'] == "light" else ft.Border.all(2, ft.Colors.PRIMARY), 
            bgcolor=ft.Colors.GREY_900, on_click=_toggle_theme, tooltip="Set dark mode", ink=True
        )
        
        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column([
            ft.Row([
                ft.Text("Appearance", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                ft.Container(expand=True),   # Spacer to push title to left
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self._close_settings, 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings"
                )
            ]),
            ft.Text("Settings to change the interface visibility and comfort", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),

            ft.Container(height=10),    # Spacer
            ft.Divider(),
            ft.Container(height=10),    # Spacer

            ft.Text("Theme Mode", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),     # Theme headline
            ft.Container(height=10),    # Spacer

            ft.Row([self.light_theme_button, self.dark_theme_button], spacing=20),
            ft.Container(height=10),    # Spacer


            ft.Row([
                theme_color_dropdown,      # Change theme primary color dropdown   

                ft.Dropdown(
                    tooltip="Default color for new categories",
                    label="Default Folder Color",
                    capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                    options=self._get_color_options(), on_select=_set_default_category_color,
                    value=self.data.get('default_category_color', "primary"),
                    text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    color=self.data.get('default_category_color', "primary"),
                    dense=True, data="category",
                ),
            ]),   

            ft.TextButton(      # Reorder workspaces rail button
                "Reorder Workspaces", icon=ft.Icons.REORDER_ROUNDED,
                on_click=lambda e: self.workspaces_rail.toggle_reorder_rail(story=self.story),
                tooltip="Reorder the workspaces on the rail",
            ), 
        ])

        return content
    
    # Called when app settings category is selected
    def _load_widgets_settings(self) -> ft.Container:
        ''' Loads our account settings view '''

        def _set_default_widget_color(e):
            ''' Sets the default color for new widgets of a certain type '''

            widget_type = e.control.data   # Grabs the type of widget we're changing the default color for
            new_color = e.control.value    # Grabs the new color selected   

            match widget_type:
                case "chapter":
                    self.data['default_chapter_color'] = new_color
                case "canvas":
                    self.data['default_canvas_color'] = new_color
                case "canvas_board":
                    self.data['default_canvas_board_color'] = new_color
                case "note":
                    self.data['default_note_color'] = new_color
                case "character":
                    self.data['default_character_color'] = new_color
                case "plotline":
                    self.data['default_plotline_color'] = new_color
                case "map":
                    self.data['default_map_color'] = new_color
                case "planning":
                    self.data['default_planning_color'] = new_color
                case "character_connection_map":
                    self.data['default_character_connection_map_color'] = new_color
                case "world":
                    self.data['default_world_color'] = new_color

            # Save our updated settings
            self.p.run_task(self.save_dict)
            e.control.color = new_color   # Changes the dropdown text color to match the selected color
            e.control.update()

        def _toggle_show_empty_character_fields(e):
            ''' Toggles if we show empty character fields in character widget or not '''
            from models.app import app

            new_value = e.control.value   # Grabs the new value of the checkbox

            self.data['show_empty_character_fields'] = new_value

            # Save our updated settings
            self.p.run_task(self.save_dict)
            e.control.update()

            for story in app.stories.values():
                if story.route == self.data.get('active_story', ""):
                    for character in story.characters.values():
                        character.reload_widget()   # Reloads the character widget to show/hide empty fields
                    break

        # Called to add our templates to our dropdown
        def _load_character_templates() -> list[ft.DropdownOption]:
            ''' Loads our character templates into the expansion tile '''

            options = []
            for key, template_data in self.data.get('character_templates', {}).items():
                template_name = template_data.get('title', "Unnamed Template")
                options.append(ft.DropdownOption(template_name))

            options.append(
                ft.DropdownOption(
                    key="Create New Template", disabled=True, 
                    content=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="Create new character template (Coming Soon!)"),
                )
            )
            

            return options
        

        def _new_character_template_selected(e):
            if e.control.value == "Create New Template":
                self.p.open(new_character_connection_clicked(self.story))
                e.control.value = self.data.get('active_character_template')    # Resets the dropdown so we can select this again later
                e.control.update()

            else:
                self.change_data(active_character_template=e.control.value)

            

        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column([
            ft.Row([
                ft.Text("Widget Settings", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                ft.Container(expand=True),   # Spacer to push title to left
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self._close_settings, 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings"
                ),
            ]),
            ft.Text("Default Settings for widgets across all your stories.", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Container(height=10),    # Spacer

            ft.Divider(),
            
            ft.Column([

                ft.Container(height=10),    # Spacer
                ft.Text("Pin location and Color of newly created widgets (won't effect existing widgets)", theme_style=ft.TextThemeStyle.BODY_LARGE, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(height=2),
                ft.Row([
                    ft.Container(width=10),   # Spacer
                    ft.Text("Canvases", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new canvases",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_canvas_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_canvas_color', "primary"),
                        dense=True, data="canvas",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new canvases",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_canvas_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_chapter_pin_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer

                ft.Row([
                    ft.Container(width=10),   # Spacer  
                    ft.Text("Canvas Boards", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new canvas boards",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_canvas_board_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_canvas_board_color', "primary"),
                        dense=True, data="canvas_board",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new canvas boards",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_canvas_board_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_canvas_pin_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer

                ft.Row([
                    ft.Container(width=10),   # Spacer  
                    ft.Text("Chapters", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new chapters",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_chapter_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_chapter_color', "primary"),
                        dense=True, data="chapter",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new chapters",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_chapter_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_chapter_pin_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer

                ft.Row([
                    ft.Container(width=10),   # Spacer
                    ft.Text("Characters", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new characters",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_character_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_character_color', "primary"),
                        dense=True, data="character",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new character",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_character_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_character_pin_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer

                ft.Row([
                    ft.Container(width=10),   # Spacer
                    ft.Text("Character Connection Maps", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new Character Connection Map",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_character_connection_map_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_character_connection_map_color', "primary"),
                        dense=True, data="character_connection_map",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new Character Connection Maps",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_character_connection_map_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_character_connection_map_pin_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer


                ft.Row([
                    ft.Container(width=10),   # Spacer
                    ft.Text("Maps", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new maps",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_map_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_map_color', "primary"),
                        dense=True, data="map",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new maps",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_map_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_map_pin_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer

                ft.Row([
                    ft.Container(width=10),   # Spacer
                    ft.Text("Notes", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new notes",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_note_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_note_color', "primary"),
                        dense=True, data="note",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new notes",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_note_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_note_pin_location=e.control.value.lower()), 
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer

                ft.Row([
                    ft.Container(width=10),   # Spacer
                    ft.Text("Planning", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new planning widgets",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_planning_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_planning_color', "primary"),
                        dense=True, data="planning",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new planning widgets",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_planning_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_planning_pin_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer

                

                ft.Row([
                    ft.Container(width=10),   # Spacer
                    ft.Text("Plotlines", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new plotlines",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_plotline_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_plotline_color', "primary"),
                        dense=True, data="plotline",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new plotlines",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_plotline_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True,
                        on_select=lambda e: self.change_data(default_plotline_pin_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                ft.Container(height=0),    # Spacer

                ft.Row([
                    ft.Container(width=10),   # Spacer
                    ft.Text("Worlds", theme_style=ft.TextThemeStyle.LABEL_LARGE, width=100),
                    ft.Dropdown(
                        label="Color", tooltip="Default color for new World widgets",
                        capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                        options=self._get_color_options(), on_select=_set_default_widget_color,
                        value=self.data.get('default_world_color', "primary"),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        color=self.data.get('default_world_color', "primary"),
                        dense=True, data="world",
                    ),
                    ft.Dropdown(
                        label="Pin Location", tooltip="Default pin location for new World widgets",
                        capitalization= ft.TextCapitalization.SENTENCES,
                        options=[ft.DropdownOption("Left"), ft.DropdownOption("Right"), ft.DropdownOption("Main"), ft.DropdownOption("Top"), ft.DropdownOption("Bottom")],
                        value=self.data.get('default_world_pin_location', "main").capitalize(),
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD), dense=True,
                        on_select=lambda e: self.change_data(default_world_location=e.control.value.lower()),
                    ),
                    ft.Container(width=10),   # Spacer
                ]),
                
                ft.Divider(),
                ft.Text("Canvases", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer
                
                ft.Divider(),

                ft.Text("Canvas Boards", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer
                
                ft.Divider(),

                ft.Text("Chapters", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer
                
                ft.Divider(),


                ft.Text("Characters", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),     # Headling for theme colors
                ft.Container(height=10),    # Spacer

                ft.Row([
                    ft.Container(width=10),    # Spacer
                        ft.Checkbox(
                        label="Show Empty Character Fields", value=self.data.get('show_empty_character_fields', True),
                        on_change=_toggle_show_empty_character_fields, label_position=ft.LabelPosition.LEFT,
                        tooltip="If enabled, empty fields for characterls will be shown. When disabled, characters provide a simpler view and only shows information that has been filled out.",
                    ),
                ]),
                ft.Container(height=0),    # Spacer
                
                ft.Row([
                    ft.Container(width=10),    # Spacer
                    ft.Text("Character Templates", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                    ft.Dropdown(
                        label="Active Template", width=200,
                        #value=self.data.get('active_character_template', "None"),
                        value="Default",
                        #options=_load_character_templates(), 
                        options=[ft.DropdownOption("Default")],
                        on_select=_new_character_template_selected,
                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                        dense=True, tooltip="Select a character template to use when creating new characters",
                        capitalization= ft.TextCapitalization.SENTENCES,
                    ),
                    ft.IconButton(ft.Icons.MANAGE_SEARCH_OUTLINED, tooltip="Manage Character Templates (Coming Soon!)", disabled=True)
                ]),
                
                

                ft.Divider(),

                ft.Text("Character Connection Maps", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer
                
                ft.Divider(),

                ft.Text("Maps", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer
                
                ft.Divider(),

                ft.Text("Notes", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer
                
                ft.Divider(),

                ft.Text("Planning", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer
                
                ft.Divider(),

                ft.Text("Plotlines", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer

                ft.Divider(),

                ft.Text("Worlds", theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(height=10),    # Spacer
                
                ft.Container(expand=True, height=500)





            ], scroll="auto", expand=True),
            
        ])

        return content
    
    def _load_story_settings(self) -> ft.Container:
        ''' Loads our story settings view '''

        # Type - novel vs comic. Effects how new content is created

        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column([
            ft.Row([
                ft.Text("Story Settings", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                ft.Container(expand=True),   # Spacer to push close button to the right
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self._close_settings, 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings"
                )
            ]),            
            ft.Text(f"Settings for your current story: {self.story.title}", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Container(height=10),    # Spacer

            ft.Divider(),
            ft.Container(height=10),    # Spacer



        ])

        return content
    
    def _load_template_settings(self, selected_template: str = None):
        ''' Loads our resources settings view '''

        # Has resources to help writers, can re-run the tutorial view, examples, discord link, planned features
        # TODO: Use seleted template to auto load new templates data when creating them

        page = self.p

        
        # A template control that gets the entire template data so we can manipulate it and save it
        class TemplateCtrl(ft.Column):
            def __init__(self, name: str, **kwargs):
                super().__init__(**kwargs)

                
                self.scroll = "none"
                self.spacing = 0
                self.expand = True

                self.name = name        # Name of this template within our templates dict
                self.old_name = name     # Old name to check if we changed it for renaming our template key in our dict
                self.can_create_section = False     # State checking
                
                self.reload()

            # When clicking add new section
            async def _new_section_clicked(self, e=None):
                dlg = ft.AlertDialog(
                    title="Name Your Section",
                    content=TextField(),
                    actions=[
                        ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                        ft.TextButton("Create", on_click=self._add_section, style=ft.ButtonStyle(mouse_cursor="click")),
                    ]
                )

                self.page.show_dialog(dlg)

            

            # Called when we submit a new section name. Checks if we can create it and creates it if we can
            def _reorder_sections(self, e: ft.OnReorderEvent):
                old_index = e.old_index
                new_idx = e.new_index
                new_data = {}

                # Find our sections name that is getting moved based on old index
                for idx, name in enumerate(self.data.keys()):
                    if idx == old_index:
                        section_name = name
                section_data = self.data.get(section_name, None)        # Set its data as well

                # Remove the section from its old position
                self.data.pop(section_name)

                # Re-build our data dict based on new order
                for idx, name in enumerate(self.data.keys()):
                    # Adds the moved section to our new index, and adds the rest of the data where it should be
                    if idx == new_idx:
                        new_data[section_name] = section_data
                    new_data[name] = self.data[name]

                if new_idx >= len(self.data):   # If we move to the end of the list, add it there, since it won't be added in the loop
                    new_data[section_name] = section_data

                self.data = new_data
                character_templates[self.name] = self.data     # Update our existing templates with the new data

                self.reload()
                

            def _delete_section(self, section_name: str):
                pass

            def _add_section(self, section_name: str):
                pass

            def _update_section(self, section_name: str, new_data: dict):
                pass

            def _reset_template_data(self, e=None):
                self.data = default_character_template_data_dict()
                character_templates[self.name] = self.data
                self.reload()
                
            # Reloads our control visually based on our current data
            def reload(self):   

                #print("New Template data on reload---------------------------------------------")    

                #for key, value in self.data.items():
                    #print(f"{key}: {value}")

                #print("\n")        
                        
                # Set title and divider for this column
                self.controls = [
                    ft.Container(height=6),
                    ft.Row([
                        ft.Text(theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM, value=self.name),
                        ft.TextButton("Add Section", on_click=self._new_section_clicked, style=ft.ButtonStyle(mouse_cursor="click")),
                    ]),
                    ft.Container(height=6), 
                    ft.Divider(height=2, thickness=2),
                    ft.Container(height=6),
                    ft.ReorderableListView(
                        on_reorder=self._reorder_sections, padding=ft.Padding.only(right=10), expand=True,
                        show_default_drag_handles=False, 
                        
                        #footer=add new section button?
                    )
                ]

                idx = 0

                for section_name, section_data in self.data.items():
                    self.controls[-1].controls.append(
                        SectionCtrl(
                            name=section_name,  # Name of the section
                            template_name=self.name,   # Name of the template this section belongs to for easy access to update data
                            data=section_data,  # Data (dict) of the section
                            index=idx,          # Index for our reorderable list
                        )
                    )
                    
                    idx += 1

                try:
                    self.update()
                except Exception as _:
                    pass

        # Simple section class for each section in our template so we can remove and reorder them easily
        class SectionCtrl(ft.Container):
            def __init__(self, name: str, template_name: str, data: dict, index: int):
                super().__init__(data=data)
                self.name = name
                self.template_name = template_name  
                self.index = index

                self.border_radius = ft.BorderRadius.all(10)
                self.border = ft.Border.all(1, ft.Colors.ON_SURFACE_VARIANT)
                self.padding = ft.Padding.all(10)
                self.margin = ft.Margin.only(bottom=10, top=10)

                self.reload()

            def _reorder_items(self, e: ft.OnReorderEvent):
                old_index = e.old_index
                new_idx = e.new_index
                new_data = {}

                # Find our sections name that is getting moved based on old index
                for idx, key in enumerate(self.data.keys()):
                    if idx == old_index:
                        k = key
                value = self.data.get(k, None)        # Set its data as well

                # Remove the section from its old position
                self.data.pop(k)

                # Re-build our data dict based on new order
                for idx, name in enumerate(self.data.keys()):
                    # Adds the moved section to our new index, and adds the rest of the data where it should be
                    if idx == new_idx:
                        new_data[k] = value
                    new_data[name] = self.data[name]

                if new_idx >= len(self.data):   # If we move to the end of the list, add it there, since it won't be added in the loop
                    new_data[k] = value

                # Update our data, our parent TemplateCtrl's data, and the character_templates data
                self.data = new_data
                character_templates[self.template_name][self.name] = self.data     # Update our parents data

                self.reload()
                page.update()

                
            def reload(self):

                #print("NEW SECTION Data------------------------------------")
                #for key, value in self.data.items():
                    #print(f"{key}: {value}")
                #print("\n")

                self.content = ft.ReorderableDragHandle(
                    #sself.index,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(self.name, theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, tooltip="Remove this section from template"),
                        ], vertical_alignment=ft.CrossAxisAlignment.START, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        # Rest of section body here
                        ft.ReorderableListView(on_reorder=self._reorder_items)
                    ])
                )

                for key, value in self.data.items():
                    self.content.content.controls[1].controls.append(
                        ft.Row([
                            ft.Text(f"{key}: ", weight=ft.FontWeight.BOLD),
                            ft.Text(str(value))
                        ])
                    )

        
            
        # Called when clicking create template button or pressing enter in the text field
        def _create_new_template_clicked(e=None):
            ''' Determines if name is valid and creates the template if it is'''
            #nonlocal can_create_template

            def _check_template_name_unique(e):
                #nonlocal character_templates, edit_container, editing_current_template, new_template_tf, can_create_template
                name = e.control.value.strip() or ""
                is_unique = name not in character_templates.keys()
                
                if not is_unique:
                    e.control.error = "Template name already exists"
                    submit_button.disabled = True
                else:
                    e.control.error = None
                    submit_button.disabled = False
                    
                e.control.update()  
                submit_button.update()

            async def _create_new_template(e=None):
                #nonlocal character_templates, edit_container, editing_current_template, content

                name = new_template_tf.value.strip() or ""

                if can_create_template:

                    character_templates[name] = default_character_template_data_dict()       # Create a new empty template
                    self.data['character_templates'] = character_templates     # Update our main data dict with the new template
                    self.p.run_task(self.save_dict)
                    self.p.pop_dialog()
                    self._settings_category_changed(template_name=name)     # Reload our settings page to update the ui and load the new template we just created

                else: 
                    await new_template_tf.focus()

            can_create_template = False     # Checker if name is unique and we can create the template

            submit_button = ft.TextButton("Create", on_click=_create_new_template, disabled=True, style=ft.ButtonStyle(mouse_cursor="click"))

            new_template_tf = TextField(
                dense=True, expand=True, capitalization=ft.TextCapitalization.WORDS, 
                on_change=_check_template_name_unique, on_submit=_create_new_template, 
                autofocus=True
            )
            
            dlg = ft.AlertDialog(
                title=ft.Text("Name Your Template"),
                content=new_template_tf,
                actions=[
                    ft.TextButton("Cancel", style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click"), on_click=lambda _: self.p.pop_dialog()),
                    submit_button
                ],
            )

            self.p.show_dialog(dlg)


        def load_template(name: str = None) -> ft.Control:

            if name is None:
                return ft.Column(
                    [ft.Text("Select a template to start editing", expand=True, theme_style=ft.TextThemeStyle.HEADLINE_SMALL, text_align=ft.TextAlign.CENTER), ft.Container(expand=True)],
                    expand=True, scroll="auto", alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            
            # Load our name and data for the template we're loading/editing
            template_name, template_data = None, None
            for tn, td in character_templates.items():
                if tn == name:
                    template_name = tn
                    template_data = td
                    break
                    
            # Error handling
            if template_name is None or template_data is None:
                return
            

            # Set existing data. This is all data already in this template
            template_data_ctrl = TemplateCtrl(
                name=name,
                width=edit_container.width,
                data=template_data
            )

            return template_data_ctrl


        # Gets our template names as a column on the left side of our template settings view
        def _load_templates_names(type: str, selected_template_name: str=None) -> list[ft.Control]:

            controls = []

            copied_templates = character_templates if type == "character" else world_templates
        
            async def _rename_template_clicked(e):
                pass
                #new_name = e.control.data
                #pass


            async def _set_active_editing_template(e):
                #nonlocal character_templates, edit_container, editing_current_template, column

                type, name = e.control.data
                
                #editing_current_template = name
                e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
                for ctrl in controls:   
                    if isinstance(ctrl, ft.ListTile) and ctrl != e.control:
                        ctrl.bgcolor = "transparent"
                
                # Load the template into our edit container
                edit_container.content = load_template(name)
                edit_container.update()
                try:
                    self.update()
                except Exception as _:
                    pass
            

            # Delete the template
            async def _delete_template_clicked(e):
                type, name = e.control.data
                if type == "character":
                    if name in character_templates:
                        del character_templates[name]        # Remove it from our local data we're manipulating
                        self.data['character_templates'] = character_templates     # Update our main data dict with the new template list after deletion
                        await self.save_dict()                    # Save our data to our json file
                        self.body_container.content = self._load_template_settings()     # Reload our settings page to update the ui

                else:
                    if name in world_templates:
                        del world_templates[name]        # Remove it from our local data we're manipulating
                        self.data['world_templates'] = world_templates     # Update our main data dict with the new template list after deletion
                        await self.save_dict()                    # Save our data to our json file
                        self.body_container.content = self._load_template_settings()     # Reload our settings page to update the ui
                    
                
            
            # Create a nameplace for each template
            for template_name in copied_templates.keys():
                if template_name != "Default":
                    controls.append(
                        ft.ListTile(
                            title=ft.Text(
                                template_name, expand=True, overflow=ft.TextOverflow.ELLIPSIS,
                                style=ft.TextStyle(
                                    size=14,
                                    color=ft.Colors.ON_SURFACE,
                                    weight=ft.FontWeight.BOLD,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                )
                            ),
                            shape=ft.RoundedRectangleBorder(radius=6),
                            bgcolor=ft.Colors.TRANSPARENT if template_name != selected_template_name else ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                            dense=True,
                            content_padding=ft.Padding.only(left=10),
                            min_vertical_padding=0,
                            mouse_cursor=ft.MouseCursor.CLICK,
                            trailing=ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(
                                        "Rename Template", ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, ft.Colors.PRIMARY),
                                        #on_click=lambda e, name=template_name: _edit_template(name, e)
                                        data=(type, template_name), mouse_cursor=ft.MouseCursor.CLICK
                                    ),
                                    ft.PopupMenuItem(
                                        "Delete Template", ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR),
                                        on_click=_delete_template_clicked,
                                        data=(type, template_name), mouse_cursor=ft.MouseCursor.CLICK
                                    )
                                ],
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                menu_padding=ft.Padding.all(0),
                            ),
                            data=(type, template_name), on_click=_set_active_editing_template,
                        ),
                    )

            new_template_button = ft.TextButton(
                f"Create New {type.capitalize()} Template", #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, 
                on_click=_create_new_template_clicked, style=ft.ButtonStyle(mouse_cursor="click")
            )

            controls.append(new_template_button)

            return controls
        
        # Grab all our existing templates
        character_templates = self.data.get('character_templates', {}).copy()        # Copy our data for ez manipulation without saving until the end
        world_templates = self.data.get('world_templates', {}).copy()

        edit_container = ft.Container(
            expand=True, border_radius=ft.BorderRadius.all(10),
            content=load_template(), padding=ft.Padding.all(10), 
        )


        templates_names_column = ft.Column([], scroll="auto", width=240,  horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        templates_names_column.controls.append(ft.Text("Character Templates", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER))
        templates_names_column.controls.extend(_load_templates_names("character", selected_template))
        templates_names_column.controls.append(ft.Divider())
        templates_names_column.controls.append(ft.Text("World Templates", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER))
        templates_names_column.controls.extend(_load_templates_names("world", selected_template))
        
        # Sets our templates
        content = ft.Column([
            ft.Row([
                ft.Text("Templates", theme_style=ft.TextThemeStyle.HEADLINE_LARGE, expand=True),
                #ft.Container(expand=True),   # Spacer to push title to left
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self._close_settings, 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings"
                )
            ]),
            ft.Text(f"Edit your character and world templates", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Container(height=10),    # Spacer
            ft.Divider(),
            ft.Row(
                scroll="none", expand=True, vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[templates_names_column, ft.VerticalDivider(), edit_container, ft.Container(width=10)]
            ),

        ])

        return content

        
    
    def _load_resources_settings(self):
        ''' Loads our resources settings view '''

        # Has resources to help writers, can re-run the tutorial view, examples, discord link, planned features

        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column([
            ft.Row([
                ft.Text("Resources", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                ft.Container(expand=True),   # Spacer to push title to left
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self._close_settings, 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings"
                )
            ]),
            ft.Text(f"Resources to help with your masterpiece!", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),

            ft.Container(height=10),    # Spacer

            ft.Divider(),
            ft.Container(height=10),    # Spacer

        ])

        return content
    
    

        
    
    # Called when someone expands the drop down holding the color scheme options
    def reload_settings(self):
        ''' Reloads our settings view with updated data '''

        # Clear any current controls we have
        self.controls.clear()
        
        # Set our menubar
        menubar = create_menu_bar(self.p, self.story)   

        # Set our workspaces rail
        self.workspaces_rail = WorkspacesRail(self.p, self.story)  

        # Set the rail we use for different settings categories
        nav_rail = ft.NavigationRail(
            selected_index=self.selected_index,
            bgcolor="transparent",
            on_change=self._settings_category_changed,
            label_type=ft.NavigationRailLabelType.ALL,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.COLOR_LENS_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.COLOR_LENS_ROUNDED, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Appearance", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.Margin.only(bottom=20))
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.NOW_WIDGETS_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.NOW_WIDGETS_ROUNDED, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Widgets", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.Margin.only(bottom=20))
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.MENU_BOOK_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.PRIMARY),
                    disabled=self.story is None,   # Disable if no story is loaded
                    label=ft.Container(
                        margin=ft.Margin.only(bottom=20),
                        content=ft.Text(
                            "Story Settings", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE,
                            color=ft.Colors.OUTLINE if self.story is None else None
                        ),
                    )
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.FILE_PRESENT_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.FILE_PRESENT, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Templates", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.Margin.only(bottom=20))
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INFO_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.INFO_ROUNDED, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Resources", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.Margin.only(bottom=20))
                ),
            ],
        )

        nav_rail_container = ft.Container(
            bgcolor=ft.Colors.with_opacity(.5, ft.Colors.SURFACE),
            border_radius=ft.BorderRadius.only(top_left=20, bottom_left=20),
            padding=ft.Padding.all(20),
            content=nav_rail,
        )

        # Build the body of appearance view
        self.body_container = ft.Container(
            expand=True, 
            padding=ft.Padding.all(40),
            #content=self._load_appearance_settings()        # Default to appearance settings when settings are first opened
        )

        self._settings_category_changed()

        # View is like a column, so top down layout
        self.controls = [
            menubar,
            ft.Row(
                spacing=0, 
                expand=True,
                controls=[
                    self.workspaces_rail,
                    ft.VerticalDivider(thickness=2, width=2),
                    ft.Container(
                        ft.Container(
                            expand=True,
                            gradient=dark_gradient, 
                            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                            border_radius=ft.BorderRadius.all(20),
                            margin=ft.Margin.all(10),
                            content=ft.Row(
                                controls=[
                                    nav_rail_container,
                                    ft.VerticalDivider(thickness=2, width=2),   

                                    self.body_container
                                ],
                                spacing=0,
                            )
                        ), bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, expand=True
                    )
                ]
            ),  
        ]

