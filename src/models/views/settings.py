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
from models.dataclasses.world_template import default_world_template_data_dict

 
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
                    'stroke_width': 3,          # Size of the strokees
                    'style': "stroke",          # style of the strokes. Either stroke or fill
                    'stroke_cap': "round",      # Each end of the strokes shape
                    'stroke_join': "round",     # How corners between strokes are drawn
                    'stroke_miter_limit': 10, 
                    'stroke_dash_pattern': None,         # If we should use dashed lines, and the pattern for them

                    # Effects
                    'anti_alias': True,
                    'blur_image': int,
                    'blend_mode': "src_over",
                },               

                # Other canvas and drawing settings outside of the brushes paint
                'canvas_settings':{
                    'current_control_mode': "draw",      # Either drawing (use brush settings), or tools (use built in tools)
                    'current_brush_name': "stroke",      # Name of the currently selected brush, either default or custom. Just used for display purposes
                    'current_tool_name': "erase",        # Current tool or shape being used
                    'saved_brushes': dict,              # Saved brushes the user has created that we can load
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
                'division_labels_direction': "bottom",              # If the division labels are on top of the plotline instead of below

                # Hold our default character templates
                'character_templates': {    
                    'Default': default_character_template_data_dict(),
                },   
                'world_templates': {    
                    'Default': default_world_template_data_dict(),
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

    async def save_story(self, e=None):
        ''' Called when the page is closed. Saves any last changes to settings before exit '''

        if self.story is not None:
            for widget in self.story.widgets:
                if widget.save_counter > 0:
                    widget.save_counter = 1000   # Will force a file write to widgets who have unwritten changes to their file
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
    def _settings_category_changed(self, e=None, template_name: str=None, template_type: str=None):
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
                self.body_container.content = self._load_template_settings(template_name, template_type)
            case 3:
                self.body_container.content = self._load_resources_settings()
                
        try:
            self.update()
        except Exception:
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
                
                
            ], scroll="auto", expand=True),
            
        ])

        return content
    
    def _load_template_settings(self, selected_template: str = None, selected_type: str = None):
        ''' Loads our template settings view for editing character and world templates '''

        page = self.p

        # Grab all our existing templates.  These are mutated in place by the nested helpers
        # so changes are visible across all closures that share these references.
        character_templates: dict = self.data.get('character_templates', {}).copy()
        world_templates: dict     = self.data.get('world_templates',     {}).copy()

        def _get_templates(ttype: str) -> dict:
            return character_templates if ttype == "character" else world_templates

        def _sync_and_save():
            ''' Pushes local template dicts back to settings data and writes to disk '''
            self.data['character_templates'] = character_templates
            self.data['world_templates']     = world_templates
            self.p.run_task(self.save_dict)

        # Declared early so inner helpers that need it can reference it via closure
        edit_container = ft.Container(
            expand=True,
            border_radius=ft.BorderRadius.all(10),
            padding=ft.Padding.all(10),
        )

        # ── FieldItem ──────────────────────────────────────────────────────────
        class FieldItem(ft.Container):
            ''' A single draggable field row inside a SectionCtrl '''

            def __init__(self, section_ctrl, field_name: str):
                super().__init__(key=field_name)
                self.section_ctrl = section_ctrl
                self.field_name   = field_name
                self.padding      = ft.Padding.symmetric(vertical=2, horizontal=2)
                self._render()

            def _render(self):
                self.content = ft.ReorderableDragHandle(
                    content=ft.Row(
                        [
                            ft.Text(self.field_name, expand=True, theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.ERROR,
                                tooltip="Delete field",
                                icon_size=18,
                                on_click=lambda e, k=self.field_name: self.section_ctrl._delete_field(k),
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )

        # ── SectionCtrl ────────────────────────────────────────────────────────
        class SectionCtrl(ft.Container):
            ''' One section card inside a TemplateCtrl '''

            def __init__(self, name: str, template_name: str, template_type: str, data: dict):
                super().__init__(key=name, data=data)
                self.name          = name
                self.template_name = template_name
                self.template_type = template_type

                self.border_radius = ft.BorderRadius.all(10)
                self.border        = ft.Border.all(1, ft.Colors.ON_SURFACE_VARIANT)
                self.padding       = ft.Padding.all(10)
                self.margin        = ft.Margin.only(bottom=8, top=8)

                # Wired by TemplateCtrl after construction
                self._delete_callback = None

                self.reload()

            # ── helpers ──────────────────────────────────────────────────────
            def _tmpl(self) -> dict:
                return _get_templates(self.template_type)

            def _persist(self):
                self._tmpl()[self.template_name][self.name] = self.data
                _sync_and_save()

            # ── field reordering ─────────────────────────────────────────────
            def _reorder_items(self, e: ft.OnReorderEvent):
                old_idx = e.old_index
                new_idx = e.new_index
                new_data: dict = {}

                k = None
                for i, key in enumerate(self.data.keys()):
                    if i == old_idx:
                        k = key
                if k is None:
                    return

                value = self.data.pop(k)

                for i, name in enumerate(self.data.keys()):
                    if i == new_idx:
                        new_data[k] = value
                    new_data[name] = self.data[name]

                if new_idx >= len(self.data):
                    new_data[k] = value

                self.data = new_data
                self._persist()
                self.reload()
                try:
                    self.update()
                except Exception:
                    pass

            # ── field creation ───────────────────────────────────────────────
            def _new_field_clicked(self, e=None):
                sec = self

                def _check(e):
                    name = e.control.value.strip()
                    if not name or name in sec.data:
                        e.control.error = "Name already exists or is empty"
                        add_btn.disabled = True
                    else:
                        e.control.error = None
                        add_btn.disabled = False
                    e.control.update()
                    add_btn.update()

                async def _do_add(e=None):
                    name = field_tf.value.strip()
                    if name and name not in sec.data:
                        sec._add_field(name)
                        page.pop_dialog()

                field_tf = TextField(
                    dense=True, expand=True,
                    capitalization=ft.TextCapitalization.WORDS,
                    on_change=_check, on_submit=_do_add, autofocus=True,
                )
                add_btn = ft.TextButton(
                    "Add", on_click=_do_add, disabled=True,
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                )
                page.show_dialog(ft.AlertDialog(
                    title=ft.Text("Name Your Field"),
                    content=field_tf,
                    actions=[
                        ft.TextButton(
                            "Cancel", on_click=lambda _: page.pop_dialog(),
                            style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK),
                        ),
                        add_btn,
                    ],
                ))

            def _add_field(self, field_name: str):
                self.data[field_name] = ""
                self._persist()
                self.reload()
                try:
                    self.update()
                except Exception:
                    pass

            def _delete_field(self, field_name: str):
                if field_name in self.data:
                    del self.data[field_name]
                    self._persist()
                    self.reload()
                    try:
                        self.update()
                    except Exception:
                        pass

            # ── section deletion ─────────────────────────────────────────────
            def _on_delete_clicked(self, e):
                if self._delete_callback:
                    self._delete_callback(self.name)

            # ── render ───────────────────────────────────────────────────────
            def reload(self):
                field_items = [FieldItem(section_ctrl=self, field_name=k) for k in self.data.keys()]

                fields_view = (
                    ft.ReorderableListView(
                        controls=field_items,
                        on_reorder=self._reorder_items,
                        show_default_drag_handles=False,
                        #shrink_wrap=True,
                    )
                    if field_items
                    else ft.Container(
                        content=ft.Text(
                            "No fields yet — click 'Add Field' to add one.",
                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        padding=ft.Padding.symmetric(vertical=4),
                    )
                )

                self.content = ft.ReorderableDragHandle(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        self.name,
                                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                    ft.TextButton(
                                        "Add Field", on_click=self._new_field_clicked,
                                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                    ),
                                    ft.TextButton(
                                        "Delete Section",
                                        on_click=self._on_delete_clicked,
                                        style=ft.ButtonStyle(
                                            color=ft.Colors.ERROR,
                                            mouse_cursor=ft.MouseCursor.CLICK,
                                        ),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Divider(),
                            fields_view,
                        ],
                        spacing=4,
                    )
                )

        # ── TemplateCtrl ───────────────────────────────────────────────────────
        class TemplateCtrl(ft.Column):
            ''' Editable view for a single template '''

            def __init__(self, name: str, template_type: str, **kwargs):
                super().__init__(**kwargs)
                self.scroll        = "auto"
                self.spacing       = 0
                self.expand        = True
                self.name          = name
                self.template_type = template_type
                self.reload()

            def _tmpl(self) -> dict:
                return _get_templates(self.template_type)

            def _persist(self):
                self._tmpl()[self.name] = self.data
                _sync_and_save()

            # ── section reordering ───────────────────────────────────────────
            def _reorder_sections(self, e: ft.OnReorderEvent):
                old_idx = e.old_index
                new_idx = e.new_index
                new_data: dict = {}

                section_name = None
                for i, name in enumerate(self.data.keys()):
                    if i == old_idx:
                        section_name = name
                if section_name is None:
                    return

                section_data = self.data.pop(section_name)

                for i, name in enumerate(self.data.keys()):
                    if i == new_idx:
                        new_data[section_name] = section_data
                    new_data[name] = self.data[name]

                if new_idx >= len(self.data):
                    new_data[section_name] = section_data

                self.data = new_data
                self._persist()
                self.reload()

            # ── section creation ─────────────────────────────────────────────
            def _new_section_clicked(self, e=None):
                ctrl = self

                def _check(e):
                    name = e.control.value.strip()
                    if not name or name in ctrl.data:
                        e.control.error = "Name already exists or is empty"
                        add_btn.disabled = True
                    else:
                        e.control.error = None
                        add_btn.disabled = False
                    e.control.update()
                    add_btn.update()

                async def _do_create(e=None):
                    name = sec_tf.value.strip()
                    if name and name not in ctrl.data:
                        ctrl._add_section(name)
                        page.pop_dialog()

                sec_tf = TextField(
                    dense=True, expand=True,
                    capitalization=ft.TextCapitalization.WORDS,
                    on_change=_check, on_submit=_do_create, autofocus=True,
                )
                add_btn = ft.TextButton(
                    "Create", on_click=_do_create, disabled=True,
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                )
                page.show_dialog(ft.AlertDialog(
                    title=ft.Text("Name Your Section"),
                    content=sec_tf,
                    actions=[
                        ft.TextButton(
                            "Cancel", on_click=lambda _: page.pop_dialog(),
                            style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK),
                        ),
                        add_btn,
                    ],
                ))

            def _add_section(self, section_name: str):
                self.data[section_name] = {}
                self._persist()
                self.reload()

            def _delete_section(self, section_name: str):
                if section_name in self.data:
                    del self.data[section_name]
                    self._persist()
                    self.reload()

            # ── render ───────────────────────────────────────────────────────
            def reload(self):
                section_controls = []
                for section_name, section_data in self.data.items():
                    # Guard against stale dict-type values from old world template defaults
                    if not isinstance(section_data, dict):
                        section_data = {}
                        self.data[section_name] = section_data

                    sc = SectionCtrl(
                        name=section_name,
                        template_name=self.name,
                        template_type=self.template_type,
                        data=section_data,
                    )
                    sc._delete_callback = self._delete_section
                    section_controls.append(sc)

                sections_view = (
                    ft.ReorderableListView(
                        controls=section_controls,
                        on_reorder=self._reorder_sections,
                        padding=ft.Padding.only(right=10),
                        expand=True,
                        show_default_drag_handles=False,
                    )
                    if section_controls
                    else ft.Container(
                        content=ft.Text(
                            "No sections yet — click 'Add Section' to create one.",
                            theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        padding=ft.Padding.all(20),
                        expand=True,
                    )
                )

                self.controls = [
                    ft.Container(height=6),
                    ft.Row([
                        ft.Text(
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                            value=self.name,
                            expand=True,
                        ),
                        ft.TextButton(
                            "Add Section", on_click=self._new_section_clicked,
                            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                        ),
                    ]),
                    ft.Container(height=6),
                    ft.Divider(),
                    ft.Container(height=6),
                    sections_view,
                ]

                try:
                    self.update()
                except Exception:
                    pass

        # ── load_template ──────────────────────────────────────────────────────
        def load_template(name: str = None, ttype: str = None) -> ft.Control:
            if name is None or ttype is None:
                return ft.Column(
                    [
                        ft.Text(
                            "Select a template to start editing",
                            expand=True,
                            theme_style=ft.TextThemeStyle.HEADLINE_SMALL,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(expand=True),
                    ],
                    expand=True, scroll="auto",
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )

            templates = _get_templates(ttype)
            template_data = templates.get(name)
            if template_data is None:
                return load_template()

            return TemplateCtrl(
                name=name,
                template_type=ttype,
                width=edit_container.width,
                data=template_data,
            )

        # ── create template dialog ─────────────────────────────────────────────
        def _create_new_template_clicked(ttype: str, e=None):
            from utils.safe_string_checker import return_safe_name
            templates = _get_templates(ttype)

            def _check(e):
                raw  = e.control.value.strip()
                safe = return_safe_name(raw)
                ok   = bool(safe) and safe not in templates and safe.lower() != "default"
                e.control.error   = None if ok else ("Name is taken or invalid")
                add_btn.disabled  = not ok
                e.control.update()
                add_btn.update()

            async def _do_create(e=None):
                from utils.safe_string_checker import return_safe_name
                raw  = tf.value.strip()
                safe = return_safe_name(raw)
                if safe and safe not in templates and safe.lower() != "default":
                    if ttype == "character":
                        templates[safe] = default_character_template_data_dict()
                    else:
                        templates[safe] = default_world_template_data_dict()
                    _sync_and_save()
                    self.p.pop_dialog()
                    # Auto-select the newly created template
                    self._settings_category_changed(template_name=safe, template_type=ttype)

            tf = TextField(
                dense=True, expand=True,
                capitalization=ft.TextCapitalization.WORDS,
                on_change=_check, on_submit=_do_create, autofocus=True,
            )
            add_btn = ft.TextButton(
                "Create", on_click=_do_create, disabled=True,
                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
            )
            self.p.show_dialog(ft.AlertDialog(
                title=ft.Text(f"Name Your {ttype.capitalize()} Template"),
                content=tf,
                actions=[
                    ft.TextButton(
                        "Cancel", on_click=lambda _: self.p.pop_dialog(),
                        style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK),
                    ),
                    add_btn,
                ],
            ))

        # ── rename template dialog ─────────────────────────────────────────────
        def _rename_template_clicked(ttype: str, old_name: str, e=None):
            from utils.safe_string_checker import return_safe_name
            templates = _get_templates(ttype)

            def _check(e):
                raw  = e.control.value.strip()
                safe = return_safe_name(raw)
                same = safe == old_name
                ok   = bool(safe) and (same or (safe not in templates and safe.lower() != "default"))
                e.control.error  = None if ok else "Name is taken or invalid"
                save_btn.disabled = not ok
                e.control.update()
                save_btn.update()

            async def _do_rename(e=None):
                from utils.safe_string_checker import return_safe_name
                raw  = tf.value.strip()
                safe = return_safe_name(raw)
                if not safe or safe == old_name:
                    self.p.pop_dialog()
                    return
                if safe not in templates and safe.lower() != "default":
                    data = templates.pop(old_name)
                    templates[safe] = data
                    _sync_and_save()
                    self.p.pop_dialog()
                    self._settings_category_changed(template_name=safe, template_type=ttype)

            tf = TextField(
                value=old_name,
                dense=True, expand=True,
                capitalization=ft.TextCapitalization.WORDS,
                on_change=_check, on_submit=_do_rename, autofocus=True,
            )
            save_btn = ft.TextButton(
                "Save", on_click=_do_rename,
                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
            )
            self.p.show_dialog(ft.AlertDialog(
                title=ft.Text("Rename Template"),
                content=tf,
                actions=[
                    ft.TextButton(
                        "Cancel", on_click=lambda _: self.p.pop_dialog(),
                        style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK),
                    ),
                    save_btn,
                ],
            ))

        # ── template names sidebar ─────────────────────────────────────────────
        def _load_templates_names(ttype: str, selected_template_name: str = None) -> list[ft.Control]:
            controls: list = []
            templates = _get_templates(ttype)

            async def _set_active(e):
                t, name = e.control.data
                e.control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
                for ctrl in controls:
                    if isinstance(ctrl, ft.ListTile) and ctrl != e.control:
                        ctrl.bgcolor = ft.Colors.TRANSPARENT
                edit_container.content = load_template(name, t)
                edit_container.update()

            async def _delete_template(e):
                t, name = e.control.data
                tmpl = _get_templates(t)
                if name in tmpl:
                    del tmpl[name]
                    _sync_and_save()
                    self.body_container.content = self._load_template_settings()
                    self.body_container.update()

            for template_name in templates.keys():
                if template_name == "Default":
                    continue
                controls.append(
                    ft.ListTile(
                        title=ft.Text(
                            template_name,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            style=ft.TextStyle(
                                size=14,
                                color=ft.Colors.ON_SURFACE,
                                weight=ft.FontWeight.BOLD,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ),
                        shape=ft.RoundedRectangleBorder(radius=6),
                        bgcolor=ft.Colors.TRANSPARENT,
                        dense=True,
                        content_padding=ft.Padding.only(left=10),
                        min_vertical_padding=0,
                        mouse_cursor=ft.MouseCursor.CLICK,
                        trailing=ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(
                                    "Rename Template",
                                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, ft.Colors.PRIMARY),
                                    on_click=lambda e, t=ttype, n=template_name: _rename_template_clicked(t, n),
                                    data=(ttype, template_name),
                                    mouse_cursor=ft.MouseCursor.CLICK,
                                ),
                                ft.PopupMenuItem(
                                    "Delete Template",
                                    ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR),
                                    on_click=_delete_template,
                                    data=(ttype, template_name),
                                    mouse_cursor=ft.MouseCursor.CLICK,
                                ),
                            ],
                            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                            menu_padding=ft.Padding.all(0),
                        ),
                        data=(ttype, template_name),
                        on_click=_set_active,
                    )
                )

            controls.append(
                ft.TextButton(
                    f"Create New {ttype.capitalize()} Template",
                    on_click=lambda e, t=ttype: _create_new_template_clicked(t, e),
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                )
            )
            return controls

        # ── assemble the view ──────────────────────────────────────────────────
        edit_container.content = (
            load_template(selected_template, selected_type)
            if selected_template is not None
            else load_template()
        )

        templates_names_column = ft.Column(
            [], scroll="auto", width=240,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        templates_names_column.controls.append(
            ft.Text("Character Templates", theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                    weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        )
        templates_names_column.controls.extend(_load_templates_names("character", selected_template if selected_type == "character" else None))
        templates_names_column.controls.append(ft.Divider())
        templates_names_column.controls.append(
            ft.Text("World Templates", theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                    weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        )
        templates_names_column.controls.extend(_load_templates_names("world", selected_template if selected_type == "world" else None))

        return ft.Column([
            ft.Row([
                ft.Text("Templates", theme_style=ft.TextThemeStyle.HEADLINE_LARGE, expand=True),
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self._close_settings,
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings",
                ),
            ]),
            ft.Text(
                "Edit your character and world templates",
                theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Container(height=10),
            ft.Divider(),
            ft.Row(
                scroll="none", expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    templates_names_column,
                    ft.VerticalDivider(),
                    edit_container,
                    ft.Container(width=10),
                ],
            ),
        ])

        
    
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
                            #gradient=dark_gradient, 
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
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

