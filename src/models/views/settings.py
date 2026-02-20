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
        
        # Constructor the parent widget class
        super().__init__(
            route=f"/settings",                                      # Sets our route for our new story
            padding=ft.padding.only(top=0, left=0, right=0, bottom=0),      # No padding for the page
            spacing=0,                                                      # No spacing between menubar and rest of page
        )

        self.p = page   # Grabs our original page, as sometimes the reference gets lost. with all the UI changes that happen. p.update() always works
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
                'active_rail_width': 200,  # Width of our active rail that we can resize
                'page_is_maximized': True,   # If the window is maximized or not
                'page_width': int,     # Last known page width
                'page_height': int,    # Last known page height
                'is_first_launch': True,    # If this is the first time the app has been launched or not

                # Paint settings for our canvas drawings to use as default that users can change
                'paint_settings': {

                    # Stroke styles
                    'color': "#FFFFFF,1.0" if self.p.theme_mode == "dark" else "#000000,1.0",     # Hex color folowed by opacity
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
                    "characters",
                    "plotlines",
                    "world_building",
                    "canvas",
                    "planning",
                ],
                
                # App settings
                'confirm_item_delete': True,   # If we should confirm before deleting items

                # Widget settings
                'default_canvas_color': "primary",
                'default_canvas_board_color': "orange",
                'default_chapter_color': "primary",   # Default colors for new widgets
                'default_character_color': "primary",
                'default_character_connection_map_color': "primary", 
                'default_map_color': "primary",
                'default_note_color': "primary",
                'default_planning_color': "primary",
                'default_plotline_color': "primary",
                'default_world_color': "primary",

                'default_category_color': "primary",    # Categories thrown in here

                'default_canvas_pin_location': "main",      # Default pin locations for new widgets
                'default_canvas_board_pin_location': "main",
                'default_chapter_pin_location': "main",   
                'default_character_pin_location': "left",
                'default_character_connection_map_pin_location': "main",
                'default_map_pin_location': "main",
                'default_note_pin_location': "right",
                'default_planning_pin_location': "main",
                'default_plotline_pin_location': "main",
                'default_world_pin_location': "right",

                'active_character_template': "Default",             # Which template is being used for new characters for new stories - they default to this
                'active_world_template': "Default",                 # Which template is being used for new worlds for new stories - they default to this
                'show_empty_character_fields': True,                # If we show empty character fields in character widget or not
                'division_labels_direction': "bottom",              # If the division labels are on top of the plotline instead of below

                # Hold our default character templates
                'character_templates': {    
                    'Default': default_character_template_data_dict(),
                    'Detailed': {'Detailed Data': {'title': "Detailed", 'Strengths': str, 'Weaknesses': str, 'Deceased': str}} | default_character_template_data_dict(), 
                    'Shonen': {'Shonen Data': {'title': "Shonen", 'Abilities': "Super Strength, Enhanced Healing"}} | default_character_template_data_dict(),
                    'Alien': {'Template Data': {'title': "Alien", 'Species': "Unknown", 'Home Planet': "Unknown"}} | default_character_template_data_dict(),
                    # Fantasy/DnD
                },   
                'world_templates': {    # TODO
                    'Default': dict,
                }
            }, 
        )
        

    # Called whenever there are changes in our data
    def save_dict(self):
        ''' Saves our current data to the json file '''

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

            self.save_dict()

        # Handle errors
        except Exception as e:
            print(f"Error changing settings data: {e}")


    def create_character_template(self, template_name: str, data: dict):
        ''' Creates a new character template with the given name '''
        from utils.safe_string_checker import return_safe_name

        print("Creating new character template: ", template_name, " with data: ", data)

        safe_key = return_safe_name(template_name)

        self.data['character_templates'][safe_key] = {
            'title': template_name,
            'template_data': data,
        }
        self.save_dict()
        

    # Called when the page is resized
    def _page_resized(self, e=None):
        ''' This is set inside of app.load_settings() to be called whenever the page is resized. Saves the new page size to data/if its maximized'''

        # If we're minmized, save nothing and just return
        if self.p.window.minimized:
            return

        # If we maximized the page, just save that, not the size
        if self.p.window.maximized:
            self.data['page_is_maximized'] = True
            self.save_dict()
            return
        
        # If page not maximized or minimized, save the size
        else:
            self.data['page_is_maximized'] = False
            self.data['page_width'] = self.p.width
            self.data['page_height'] = self.p.height
            self.save_dict()
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
    def _settings_category_changed(self, e=None):
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
                self.body_container.content = self._load_template_settings()
            case 4:
                self.body_container.content = self._load_resources_settings()
                

        self.p.update()
        
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
            self.save_dict()
            self.p.update()

        # Dropdown so app can change their color scheme
        theme_color_dropdown = ft.Dropdown(
            label="Theme Color", tooltip="Select the primary color scheme for the app",
            capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
            options=self._get_color_options(True),
            on_change=_set_theme_color,
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
                    e.control.border = ft.border.all(2, ft.Colors.PRIMARY)
                    self.light_theme_button.border = ft.border.all(2, ft.Colors.ON_SURFACE_VARIANT)
                else:
                    e.control.border = ft.border.all(2, ft.Colors.PRIMARY)
                    self.dark_theme_button.border = ft.border.all(2, ft.Colors.ON_SURFACE_VARIANT)

            self.data['theme_mode'] = new_theme_mode
            self.save_dict()
            self.p.theme_mode = self.data['theme_mode']
            self.p.update()

        def _set_default_category_color(e):
            ''' Sets the default color for new categories '''

            new_color = e.control.value    # Grabs the new color selected   

            self.data['default_category_color'] = new_color

            # Save our updated settings
            self.save_dict()
            e.control.color = new_color   # Changes the dropdown text color to match the selected color
            e.control.update()


            

        # Button that changes the theme from dark or light when clicked
        self.light_theme_button = ft.Container(
            content=ft.Icon(ft.Icons.LIGHT_MODE, color=ft.Colors.YELLOW_700), height=100, width=100, border_radius=10, data="light",
            border=ft.border.all(2, ft.Colors.ON_SURFACE_VARIANT) if self.data['theme_mode'] == "dark" else ft.border.all(2, ft.Colors.PRIMARY), 
            bgcolor=ft.Colors.WHITE, on_click=_toggle_theme, tooltip="Set light mode", ink=True
        )
        self.dark_theme_button = ft.Container(
            content=ft.Icon(ft.Icons.DARK_MODE, color=ft.Colors.WHITE), height=100, width=100, border_radius=10, data="dark",
            border=ft.border.all(2, ft.Colors.ON_SURFACE_VARIANT) if self.data['theme_mode'] == "light" else ft.border.all(2, ft.Colors.PRIMARY), 
            bgcolor=ft.Colors.GREY_900, on_click=_toggle_theme, tooltip="Set dark mode", ink=True
        )
        
        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column([
            ft.Row([
                ft.Text("Appearance", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                ft.Container(expand=True),   # Spacer to push title to left
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
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
                    options=self._get_color_options(), on_change=_set_default_category_color,
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
            self.save_dict()
            e.control.color = new_color   # Changes the dropdown text color to match the selected color
            e.control.update()

        def _toggle_show_empty_character_fields(e):
            ''' Toggles if we show empty character fields in character widget or not '''
            from models.app import app

            new_value = e.control.value   # Grabs the new value of the checkbox

            self.data['show_empty_character_fields'] = new_value

            # Save our updated settings
            self.save_dict()
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
                    ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_chapter_pin_location=e.control.value.lower()),
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_canvas_pin_location=e.control.value.lower()),
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_chapter_pin_location=e.control.value.lower()),
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_character_pin_location=e.control.value.lower()),
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_character_connection_map_pin_location=e.control.value.lower()),
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_map_pin_location=e.control.value.lower()),
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_note_pin_location=e.control.value.lower()), 
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_planning_pin_location=e.control.value.lower()),
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_plotline_pin_location=e.control.value.lower()),
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
                        options=self._get_color_options(), on_change=_set_default_widget_color,
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
                        on_change=lambda e: self.change_data(default_world_location=e.control.value.lower()),
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
                        on_change=_new_character_template_selected,
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
                    ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
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

                # Ctrl for creating a new section
                self.new_section_tf = ft.TextField(
                    label="New Section Name", visible=False, dense=True, autofocus=True,  capitalization=ft.TextCapitalization.WORDS,
                    on_change=self._check_section_name_unique, on_submit=self._new_section_submit,
                    on_blur=self._blur_new_section_tf
                )
                self.scroll = "none"
                self.spacing = 0
                self.expand = True

                self.name = name        # Name of this template within our templates dict
                self.old_name = name     # Old name to check if we changed it for renaming our template key in our dict
                self.can_create_section = False     # State checking
                
                self.reload()

            # When clicking add new section
            def _new_section_submit(self, e):
                if not self.new_section_tf.visible:
                    self.new_section_tf.visible = True
                    self.new_section_tf.update()
                    return

                # If we are visible, use this as a submit button
                section_name = self.new_section_tf.value.strip() or ""  
                if section_name != "":
                    if self.can_create_section:
                        # Create new section here and reload
                        pass

            # When typing in new section field. Makes sure all sections are unique or they will override each other
            def _check_section_name_unique(self, e):
                name = e.control.value.strip() or ""
                if name == "":
                    self.new_section_tf.error_text = "Section name cannot be empty"
                    self.new_section_tf.update()
                    return
                
                for key in self.data.keys():
                    if key == name:   # Check if any existing section matches this name 
                        self.can_create_section = False
                        self.new_section_tf.error_text = "Section name must be unique"
                        self.new_section_tf.update()
                        return
                self.can_create_section = True

            # Hide the textfield to add a new section and reset its value and error state
            def _blur_new_section_tf(self, e):
                self.new_section_tf.visible = False
                self.new_section_tf.value = ""
                self.new_section_tf.error_text = None
                self.new_section_tf.update()

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
                existing_templates[self.name] = self.data     # Update our existing templates with the new data
                self.reload()
                

            def _delete_section(self, section_name: str):
                pass

            def _add_section(self, section_name: str):
                pass

            def _update_section(self, section_name: str, new_data: dict):
                pass

            def _reset_template_data(self, e=None):
                self.data = default_character_template_data_dict()
                existing_templates[self.name] = self.data
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
                        ft.IconButton(ft.Icons.REFRESH_OUTLINED, ft.Colors.ERROR, tooltip="Reset template data to defaults", on_click=self._reset_template_data),
                        ft.TextField(self.name, label="Active Template", dense=True),
                        ft.Container(expand=True),
                        ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, tooltip="Add new Section to template", on_click=self._new_section_submit),
                        self.new_section_tf,
                        ft.Container(width=10, height=44),
                    ], vertical_alignment=ft.CrossAxisAlignment.END),
                    ft.Container(height=6), 
                    ft.Divider(height=2, thickness=2),
                    ft.Container(height=6),
                    ft.ReorderableListView(
                        on_reorder=self._reorder_sections, padding=ft.padding.only(right=10), expand=True,
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


                page.update()

        # Simple section class for each section in our template so we can remove and reorder them easily
        class SectionCtrl(ft.Container):
            def __init__(self, name: str, template_name: str, data: dict, index: int):
                super().__init__(data=data)
                self.name = name
                self.template_name = template_name  
                self.index = index

                self.border_radius = ft.border_radius.all(10)
                self.border = ft.border.all(1, ft.Colors.ON_SURFACE_VARIANT)
                self.padding = ft.padding.all(10)
                self.margin = ft.margin.only(bottom=10, top=10)

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

                # Update our data, our parent TemplateCtrl's data, and the existing_templates data
                self.data = new_data
                existing_templates[self.template_name][self.name] = self.data     # Update our parents data

                self.reload()
                page.update()

                
            def reload(self):

                #print("NEW SECTION Data------------------------------------")
                #for key, value in self.data.items():
                    #print(f"{key}: {value}")
                #print("\n")

                self.content = ft.ReorderableDraggable(
                    self.index,
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

        async def _save_and_close(e):
            pass

        
            
        # Called when clicking create template button or pressing enter in the text field
        def _new_template_clicked(e=None):
            ''' Determines if name is valid and creates the template if it is'''
            nonlocal can_create_template

            def _check_template_name_unique(e):
                nonlocal existing_templates, edit_container, editing_current_template, new_template_tf, can_create_template
                name = e.control.value.strip() or ""
                is_unique = name not in existing_templates.keys()
                can_create_template = is_unique and name != ""

                if not is_unique:
                    e.control.error_text = "Template name already exists"
                    submit_button.disabled = True
                else:
                    e.control.error_text = None
                    submit_button.disabled = False
                    
                self.p.update()

            def _create_new_template(name: str):
                nonlocal existing_templates, edit_container, editing_current_template, content

                name = new_template_tf.value.strip() or ""

                if can_create_template:

                    existing_templates[name] = default_character_template_data_dict()       # Create a new empty template
                    self.data['character_templates'] = existing_templates     # Update our main data dict with the new template
                    self.save_dict()
                    self.p.close(dlg)
                    self._settings_category_changed()

                else: 
                    new_template_tf.focus()

            can_create_template = False     # Checker if name is unique and we can create the template

            new_template_tf = ft.TextField(
                label="Template Name", dense=True, expand=True, capitalization=ft.TextCapitalization.WORDS, 
                on_change=_check_template_name_unique, on_submit=_create_new_template, autofocus=True
            )
            submit_button = ft.TextButton("Create", on_click=_create_new_template, disabled=True)

            
            dlg = ft.AlertDialog(
                title=ft.Text("Name Your Template"),
                content=new_template_tf,
                actions=[
                    ft.TextButton("Cancel", style=ft.ButtonStyle(color=ft.Colors.ERROR), on_click=lambda e: self.p.close(dlg)),
                    submit_button
                ],
            )

            self.p.open(dlg)


        def load_template(name: str = None) -> ft.Control:

            if name is None:
                return ft.Column(
                    [ft.Text("Select a template to start editing", expand=True, theme_style=ft.TextThemeStyle.HEADLINE_SMALL, text_align=ft.TextAlign.CENTER), ft.Container(expand=True)],
                    expand=True, scroll="auto", alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            
            # Load our name and data for the template we're loading/editing
            template_name, template_data = None, None
            for tn, td in existing_templates.items():
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


        # Gets our template names as a column on the left side of the dialog
        def _get_template_names() -> ft.Column:
            nonlocal existing_templates, edit_container, editing_current_template
            column = ft.Column([], width=200)


            def _edit_template(name: str, e):
                nonlocal existing_templates, edit_container, editing_current_template, column
                
                editing_current_template = name
                e.control.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE_VARIANT)
                for ctrl in column.controls:   
                    if isinstance(ctrl, ft.Container) and ctrl != e.control:
                        ctrl.bgcolor = "transparent"
                
                # Load the template into our edit container
                edit_container.content = load_template(name)
                edit_container.update()
                self.p.update()
            

            # Delete the template
            def _delete_template(name: str):
                nonlocal existing_templates, edit_container, editing_current_template
                if name in existing_templates:
                    del existing_templates[name]        # Remove it from our local data we're manipulating
                    for ctrl in column.controls:        # Remove it visually
                        if isinstance(ctrl, ft.Container) and ctrl.content and isinstance(ctrl.content, ft.Row) and ctrl.content.controls and isinstance(ctrl.content.controls[0], ft.Text) and ctrl.content.controls[0].value == name:
                            column.controls.remove(ctrl)
                            break

                    if editing_current_template == name:     # If we're currently editing this template, reset our edit container
                        edit_container.content = load_template()
                        editing_current_template = ""

                    self.p.update()
                
            
            # Create a nameplace for each template
            for template_name in existing_templates.keys():
                if template_name != "Default":
                    column.controls.append(
                        ft.Container(
                            ft.Row([
                                ft.Text(
                                    template_name, theme_style=ft.TextThemeStyle.LABEL_LARGE, expand=True,
                                    tooltip=f"Edit {template_name}", overflow=ft.TextOverflow.ELLIPSIS, 
                                ),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, tooltip="Delete Template", on_click=lambda e, name=template_name: _delete_template(name))
                            ]),
                            on_click=lambda e, name=template_name: _edit_template(name, e), padding=ft.padding.only(left=6), border_radius=6
                        )
                    )

            new_template_button = ft.TextButton("Create New Template", ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, on_click=_new_template_clicked)

            
                
            column.controls.append(
            
                ft.Row([
                    new_template_button,
                    #new_template_tf,
                    #ft.IconButton(ft.Icons.ADD, on_click=_new_template_clicked),
                ], alignment=ft.MainAxisAlignment.CENTER)
                
            )

            return column
        
        # Grab all our existing templates
        existing_templates = self.data.get('character_templates', {}).copy()        # Copy our data for ez manipulation without saving until the end
        editing_current_template: str = ""
        can_create_template = False     # Check if we can create a template based on unique name or not

        edit_container = ft.Container(
            #width=page.width * .5 - 222, height=page.height * .7,
            expand=True, border_radius=ft.border_radius.all(10),
            content=load_template(), padding=ft.padding.all(10), #border=ft.border.all(1, ft.Colors.ON_SURFACE_VARIANT)
        )
        
        
        # Sets our templates
        content = ft.Column([
            ft.Row([
                ft.Text("Templates", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                ft.Container(expand=True),   # Spacer to push title to left
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
                )
            ]),
            ft.Text(f"Edit your character and world templates", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Container(height=10),    # Spacer
            ft.Divider(),
            ft.Row(
                scroll="none", expand=True, vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[_get_template_names(), ft.VerticalDivider(width=2), edit_container, ft.Container(width=10)]
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
                    ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
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
        menubar = create_menu_bar(self.p)   

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
                    label="Appearance",
                    label_content=ft.Container(ft.Text("Appearance", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.margin.only(bottom=20))
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.NOW_WIDGETS_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.NOW_WIDGETS_ROUNDED, color=ft.Colors.PRIMARY),
                    label="Widgets",
                    label_content=ft.Container(ft.Text("Widgets", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.margin.only(bottom=20))
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.MENU_BOOK_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.PRIMARY),
                    label="Story Settings",
                    disabled=self.story is None,   # Disable if no story is loaded
                    label_content=ft.Container(
                        margin=ft.margin.only(bottom=20),
                        content=ft.Text(
                            "Story Settings", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE,
                            color=ft.Colors.OUTLINE if self.story is None else None
                        ),
                    )
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.FILE_PRESENT_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.FILE_PRESENT, color=ft.Colors.PRIMARY),
                    label="Templates",
                    label_content=ft.Container(ft.Text("Templates", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.margin.only(bottom=20))
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INFO_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.INFO_ROUNDED, color=ft.Colors.PRIMARY),
                    label="Resources",
                    label_content=ft.Container(ft.Text("Resources", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.margin.only(bottom=20))
                ),
            ],
        )

        nav_rail_container = ft.Container(
            bgcolor=ft.Colors.with_opacity(.5, ft.Colors.SURFACE),
            border_radius=ft.border_radius.only(top_left=20, bottom_left=20),
            padding=ft.padding.all(20),
            content=nav_rail,
        )

        # Build the body of appearance view
        self.body_container = ft.Container(
            expand=True, 
            padding=ft.padding.all(40),
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
                        expand=True,
                        gradient=dark_gradient, border_radius=20,
                        margin=ft.margin.all(10),
                        content=ft.Row(
                            controls=[
                                nav_rail_container,
                                ft.VerticalDivider(thickness=2, width=2),   

                                self.body_container
                            ],
                            spacing=0,
                        )
                    ),
                ]
            ),  
        ]

