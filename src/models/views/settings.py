''' 
Model for our settings widget. Settings widget stores app and story settings, and displays them in a tab
A Settings object is created for every story
'''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from handlers.verify_data import verify_data
from styles.colors import colors
import os
import json
from styles.colors import dark_gradient
from ui.menu_bar import create_menu_bar
from ui.workspaces_rail import WorkspacesRail

 
class Settings(ft.View):

    # Constructor
    def __init__(
        self, 
        page: ft.Page, 
        file_path: str, 
        story: Story = None, 
        data: dict = None
    ):
        
        # Constructor the parent widget class
        super().__init__(
            route=f"/settings",                                      # Sets our route for our new story
            padding=ft.padding.only(top=0, left=0, right=0, bottom=0),      # No padding for the page
            spacing=0,                                                      # No spacing between menubar and rest of page
        )

        self.title = "settings"   # Title of our settings widget

        self.p = page   # Grabs our original page, as sometimes the reference gets lost. with all the UI changes that happen. p.update() always works
        self.story = story
        self.file_path = file_path
        self.data = data

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Settings the app uses and users do not directly change in the settings view
                'active_story': "/",    # Route to our active story
                'workspaces_rail_is_collapsed': bool,  # If the all workspaces rail is collapsed or not
                'workspaces_rail_is_reorderable': bool,  # If the all workspaces rail is reorderable or not
                'active_rail_width': 200,  # Width of our active rail that we can resize
                'page_is_maximized': True,   # If the window is maximized or not
                'page_width': int,     # Last known page width
                'page_height': int,    # Last known page height

                # Settings the user can change in the settings view
                # Appearance settings
                'theme_mode': "system",       # the apps theme mode, dark or light
                'theme_color': "blue",   # the color scheme of the app. Defaults to blue
                'change_name_colors_based_on_morality': True,   # If characters names change colors in char based on morality
                'workspaces_rail_order': [      # Order of the workspace rail
                    "content",
                    "characters",
                    "timelines",
                    "maps",
                    "canvas",
                    "planning",
                ],
                'default_chapter_color': "primary",   # Default colors for new widgets
                'default_canvas_color': "primary",
                'default_note_color': "primary",
                'default_character_color': "primary",
                'default_timeline_color': "primary",
                'default_map_color': "primary",
                'default_planning_color': "primary",
                'default_family_tree_color': "primary", 
                'default_world_building_color': "primary",
                
                # App settings
                'confirm_item_delete': True,   # If we should confirm before deleting items
            },
        )
        

        


    # Called whenever there are changes in our data
    def save_dict(self):
        ''' Saves our current data to the json file '''

        try:

            # Set our file path
            

            # Create the directory if it doesn't exist. Catches errors from users deleting folders
            #os.makedirs(self.file_path, exist_ok=True)
            
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

        try:
            for key, value in kwargs.items():
                self.data.update({key: value})
                print("Changed settings data:", key, "to", value)

            self.save_dict()

        # Handle errors
        except Exception as e:
            print(f"Error changing data {key}:{value} in widget {self.title}: {e}")

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
        
    # Called when we select a new category of settings in our settings view
    def _settings_category_changed(self, e):
        ''' Determines which category is now active and changes our body container to match '''

        if e.control.selected_index == 0:   # Appearance settings
            self.body_container.content = self._load_appearance_settings()
        
        elif e.control.selected_index == 1:   # App settings
            self.body_container.content = self._load_app_settings()
        
        elif e.control.selected_index == 2:   # Account settings
            self.body_container.content = self._load_account_settings()
        
        elif e.control.selected_index == 3:   # Story settings
            self.body_container.content = self._load_story_settings()

        self.p.update()
        
    # Called when appearance settings category is selected
    def _load_appearance_settings(self) -> ft.Container:
        ''' Contains toggle for theme mode, and color scheme dropdown '''
        
        
        def _get_theme_color_options():
            ''' Adds our choices to the color scheme dropdown control'''


            # Create a list to hold our dropdown options
            options = []

            # Runs through our colors above and adds them to the dropdown
            for color in colors:
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
        self.theme_color_dropdown = ft.Dropdown(
            label="Theme Color",
            capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
            options=_get_theme_color_options(),
            on_change=_set_theme_color,
            value=self.data.get('theme_color', "blue"),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            color=self.data.get('theme_color', None),
            dense=True,
        )


        # Called when theme switch is changed. Switches from dark to light theme, or reverse
        def toggle_theme(e):
            ''' Changes our settings theme data from dark to light or reverse '''

            # Change theme mode data, and the icon to match
            if self.data['theme_mode'] == "dark":   # Check which theme we're on
                self.data['theme_mode'] = "light"   # change the theme mode so we can save it
                self.theme_button.icon = ft.Icons.DARK_MODE # Change the icon of theme button
            elif self.data['theme_mode'] == "light":
                self.data['theme_mode'] = "dark"
                self.theme_button.icon = ft.Icons.LIGHT_MODE
            
            # Theme is set to system by default, this checks for that
            else:  
                
                if self.p.theme_mode == ft.ThemeMode.DARK:
                    self.data['theme_mode'] = "dark"
                    self.theme_button.icon = ft.Icons.LIGHT_MODE
                else:
                    self.data['theme_mode'] = "light"
                    self.theme_button.icon = ft.Icons.DARK_MODE
               
            # Save the updated settings to the JSON file, apply to the page and update
            self.save_dict()
            self.p.theme_mode = self.data['theme_mode']
            self.p.update()
            
        

        # Icon of the theme button that changes depending on if we're dark or light mode
        self.theme_icon = ft.Icons.DARK_MODE if self.p.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE

        # Button that changes the theme from dark or light when clicked
        self.theme_button = ft.TextButton(text="Toggle theme mode", icon=self.theme_icon, on_click=toggle_theme)
        
        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column(
            spacing=20,
            controls=[
                ft.Row([
                    ft.Text("Appearance", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ft.Container(expand=True),   # Spacer to push title to left
                    ft.IconButton(
                        ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                        scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
                    )
                ]),
                ft.Divider(),
                
                self.theme_button,
                self.theme_color_dropdown,
                
            ]
        )

        return content
    
    def _load_app_settings(self):
        ''' Loads our app settings view '''


        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column(
            spacing=20,
            controls=[
                ft.Row([
                    ft.Text("Application Settings", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ft.Container(expand=True),   # Spacer to push title to left
                    ft.IconButton(
                        ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                        scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
                    )
                ]),
                ft.Divider(),
                
                ft.TextButton(
                    "Reorder Workspaces", 
                    icon=ft.Icons.REORDER_ROUNDED,
                    #on_click=lambda e: story.all_workspaces_rail.toggle_rail_reorderable(),
                    on_click=lambda e: self.workspaces_rail.toggle_reorder_rail(story=self.story)
                ),
            ]
        )

        return content
    
    # TOP HIDDEN FOLDER NOT HIDING
    
    def _load_account_settings(self):
        ''' Loads our account settings view '''

        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column(
            spacing=20,
            controls=[
                ft.Row([
                    ft.Text("Account Settings", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ft.Container(expand=True),   # Spacer to push title to left
                    ft.IconButton(
                        ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                        scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
                    )
                ]),
                ft.Divider(),
            ]
        )

        return content
    
    def _load_story_settings(self):
        ''' Loads our story settings view '''

        # Type - novel vs comic. Effects how new content is created

        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column(
            spacing=20,
            controls=[
                ft.Row([
                    ft.Text(f"{self.story.title} Settings", theme_style=ft.TextThemeStyle.HEADLINE_LARGE),
                    ft.Container(expand=True),   # Spacer to push close button to the right
                    ft.IconButton(
                        ft.Icons.CLOSE_OUTLINED, on_click=lambda e: self.p.go(self.story.route if self.story is not None else "/"), 
                        scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT
                    )
                ]),
                ft.Divider(),
            ]
        )

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
            selected_index=0,
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
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.PRIMARY),
                    label="App Settings",
                    label_content=ft.Container(ft.Text("App Settings", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.margin.only(bottom=20))
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ACCOUNT_CIRCLE_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, color=ft.Colors.PRIMARY),
                    label="Account",
                    label_content=ft.Container(ft.Text("Account", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.margin.only(bottom=20))
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
            padding=ft.padding.all(20),
            content=self._load_appearance_settings()        # Default to appearance settings when settings are first opened
        )

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



        # OPTION TO NOT HAVE CHARACTERS SEX CHANGE COLORS?
        # Option to change where certain widgets default display to in pins
        # NOTE: Add is_first_launch check to run a tutorial



        
    
        
