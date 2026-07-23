''' 
Model for our settings widget. Settings widget stores app and story settings, and displays them in a tab
A Settings object is created for every story
'''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from styles.colors import colors, theme_colors
import os
import json
from styles.colors import dark_gradient
from ui.menu_bar import create_menu_bar
from ui.workspaces_rail import WorkspacesRail
from models.dataclasses.character_template import default_character_template_data_dict
from styles.text_fields import TextField
from models.dataclasses.world_template import default_world_template_data_dict
import asyncio

 
class Settings(ft.View):

    # Constructor
    def __init__(
        self, 
        page: ft.Page, 
        file_path: str, 
        story: Story = None, 
        data: dict = None,
        selected_index: int = 0,   # Which folder to show when opening settings. 0 = Appearance, 1 = Widgets, 2 = Templates, 3 = Resources
    ):
        
        # Constructor the parent widget class
        super().__init__(
            route=f"/settings",                                      # Sets our route for our new story
            padding=ft.Padding.all(0),      # No padding for the page
            spacing=0,                                                   # No spacing between menubar and rest of page
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH
        )

        #self.page = page   # Grabs our original page, as sometimes the reference gets lost. with all the UI changes that happen. p.update() always works
        self.route = "/settings"   # Sets our route for our settings view
        self.story = story
        self.file_path = file_path
        self.data = data
        self.selected_index = selected_index

        # If we're new, give default values for our data 
        if data is None or data == {}:
            self.data.update({
                
                
                'is_first_launch': True,    # If this is the first time the app has been launched or not

                # Settings about the page
                'page': {
                    'route': "/",           # Route to our active story
                    'is_maximized': True,   # If the page is maximized or not
                    'width': int(),          # Last known page width
                    'height': int(),          # Last known page height
                    'theme_mode': "dark",       # the apps theme mode, dark or light
                    'theme_color': "#A0CAFD",   # the color scheme of the app. Defaults to blue
                },

                # Settings about story details
                'story': {
                    'workspaces_rail_is_collapsed': False,
                    'active_rail_width': 250,  
                    'default_folder_color': "primary",    # Categories thrown in here
                    'workspaces_rail_order': [      # Order of the workspace rail 
                        "content",
                        "canvas",
                        "plot",
                        "characters",
                        "world_building",
                    ],
                },

                # Default settings for the newly created widgets. All have a color, but can have additional settings specific to each widget type.
                'widget_defaults': {
                    'document': {
                        'color': "primary"
                    },
                    'canvas': {
                        'color': "primary"
                    },
                    'note': {
                        'color': "primary"
                    },
                    'character': {
                        'color': "primary"
                    },
                    'plotline': {
                        'color': "primary"
                    },
                    'canvas_board': {
                        'color': "primary"
                    },
                    'map': {
                        'color': "primary"
                    },
                    'world': {
                        'color': "primary"
                    },
                    'item': {
                        'color': "primary"
                    },
                    'plot_chart': {
                        'color': "primary"
                    },
                    'comic_preview': {
                        'color': "primary",
                        'preview_direction': "vertical",            # Default direction for comic preview, can be vertical or horizontal
                        'preview_background_color': "#00000000",  # Background color behind images
                        'preview_spacing': 0,                       # Spacing between images
                        'preview_scale': 2,                         # Scale of the images in the preview, 1 = 1:1, 2 = 2:1, etc. 
                        'filter_quality': "medium",                 # Filter quality for the images in the preview, can be low, medium, or high
                        'use_anti_aliasing': True,                  # Whether to use anti-aliasing when rendering the images in the preview
                    },
                    'chart': {
                        'color': "primary",
                        # Bar chart settings
                        'show_labels': True,           
                        'rod_shape': "rounded",          
                        'rod_width': 30,     
                        'rod_spacing': 4,    
                        'stack_rods': False,      
                        'show_horizontal_grid_lines': True,
                        'show_vertical_grid_lines': False,
                        # Radar chart settings
                        'make_chart_round': True,   # If chart is round or polygon based on nodes
                        'tick_count': 2,    # Number of lines between the center and outer edge of the chart
                        'show_tick_labels': False,      # Whether to show the labels for each tick line or not
                        'rotate_node_titles': True,    # Whether to keep our titles flat and not rotate them with the chart or not
                    },
                    'character_relationship_map': {
                        'color': "primary"
                    }
                },

                # Paint settings for our canvas drawings to use as default that users can change
                'paint_settings': {
                    'color': "#FFFFFF,1.0",     # Hex color folowed by opacity
                    'stroke_width': 3,          # Size of the strokees
                    'style': "stroke",          # style of the strokes. Either stroke or fill
                    'stroke_cap': "round",      # Each end of the strokes shape
                    'stroke_join': "round",     # How corners between strokes are drawn
                    'stroke_miter_limit': 10, 
                    'stroke_dash_pattern': None,         # If we should use dashed lines, and the pattern for them
                    'anti_alias': True,     # Use anti aliasing for smoother strokes or not
                    'blur_image': 0,        # How much blur to apply to the stroke
                    'blend_mode': None,     # Any blend mode to apply to the stroke, or None for normal
                },               

                # Other canvas and drawing settings outside of the brushes paint
                'canvas_settings':{
                    # Brush vs tool mode settings
                    'current_control_mode': "draw",      # Either drawing (use brush settings), or tools (use built in tools)
                    'current_brush_name': "stroke",      # Name of the currently selected brush, either default or custom. Just used for display purposes
                    'current_tool_name': "erase",        # Current tool or shape being used
                    'saved_brushes': dict(),             # Saved brushes the user has created that we can load
                    'use_brush_smoothing': True,         # Uses cv.Path for constistant shapes if true, otherwise use cv.line
                    'path_smoothing_strength': 1,        # If stroke smoothing is enabled, how strong the smoothing is. 1 = low, 10 = high 0=off
                    # Text and shape settings
                    'use_paint_for_shapes': True,           # If True, shapes are black/white and use default paint settings rather than live brush settings
                    'text_shape_size': 24,                # Font size for text shapes
                    'text_shape_font': "Arial",              # Font family for text shapes
                    'text_shape_color': "#FFFFFF",          # Font color for text shapes
                    'text_shape_shadow_color': "#00000000",
                    'text_shape_bold': False,                   # If text shapes are bold or not
                    'text_shape_italic': False,                 # If text shapes are italic or not  
                    'text_shape_decoration': "None",              # If text shapes are underlined or not
                    'text_shape_letter_spacing': 0,                    # Letter spacing for text shapes
                    'text_shape_word_spacing': 0,                      # Word spacing for text shapes
                    'rectangle_border_radius': 0,               # Border radius for rectangle shapes
                },

                # Hold our default character templates
                'character_templates': {    
                    'Default': default_character_template_data_dict(),
                },   
                'world_templates': {    
                    'Default': default_world_template_data_dict(),
                },
            })
            page.run_task(self.save_file)


    def before_update(self):
        #print(f"Successful update for settings")
        return super().before_update()
    

    # Called for little data changes
    def update_data(self, **kwargs):
        ''' Changes a key/value pair in our data and saves the json file '''

        # Allow updating of nested dicts without overriding the entire dict
        def _merge_data(target: dict, updates: dict):
            for key, value in updates.items():
                current_value = target.get(key)
                if isinstance(current_value, dict) and isinstance(value, dict):
                    _merge_data(current_value, value)
                else:
                    target[key] = value

        _merge_data(self.data, kwargs)  # Merge the new data into the existing data

    
    # Called whenever there are changes in our data
    async def save_file(self):
        ''' Saves our current data to the json file '''

        print("Saved settings to file")

        try:
            
            # Save the data to the file (creates file if doesnt exist)
            with open(self.file_path, "w", encoding='utf-8') as f:   
                json.dump(self.data, f, indent=4)
        
        except Exception as e:
            print(f"Error saving widget to {self.file_path}: {e}") 
            print("Data that failed to save: ", self.data)

    async def close_settings(self, e=None):
        ''' Closes the settings view and returns to the story or home view '''
        await self.save_file()
        await self.page.push_route(self.story.route if self.story is not None else "/")

    async def save_story(self, e=None):
        ''' Called when the page is closed. Saves any dirty changes '''
        if self.story is not None:
            for widget in self.story.widgets.values():
                await widget.save_file()
        await self.save_file()
        await asyncio.sleep(0.1)
        
    def create_character_template(self, template_name: str, data: dict):
        ''' Creates a new character template with the given name '''
        from utils.safe_string_checker import return_safe_name

        safe_key = return_safe_name(template_name)

        self.data['character_templates'][safe_key] = {
            'title': template_name,
            'template_data': data,
        }
        self.update_data(**{'character_templates': self.data['character_templates']})
        #self.page.run_task(self.save_file)
        

    # Called when the page is resized
    def page_resized(self, e: ft.WindowEvent):
        ''' This is set inside of app.load_settings() to be called whenever the page is resized. Saves the new page size to data/if its maximized'''
        from models.app import app  

        # Catch page resizing when app is initializing and ignore them
        if app.ignore_settings_change:      
            return
        
        # If we're minmized, save nothing and just return
        if e.page.window.minimized:
            return

        # If we maximized the page, just save that, not the size
        if e.page.window.maximized:
            self.update_data(**{'page': {'is_maximized': True}})
            return
        
        # If page not maximized or minimized, save the size
        else:
            self.update_data(**{
                'page': {
                    'is_maximized': False,
                    'width': e.page.width,
                    'height': e.page.height,
                    'left': e.page.window.left,
                    'top': e.page.window.top,
                }
            })
            
            return

        
    

    
        
    # Called when we select a new folder of settings in our settings view
    def _settings_category_changed(self, e: ft.Event[ft.NavigationRail]=None, template_name: str=None, template_type: str=None, update: bool=True):
        ''' Determines which folder is now active and changes our body container to match '''

        if e is None:
            idx = self.selected_index
            
        else:
            idx = e.control.selected_index 

        self.selected_index = idx   # Make sure they are syced

        match idx:
            case 0:
                self.body_container.content = self._load_appearance_settings()
            case 1:
                self.body_container.content = self._load_widget_settings()
            case 2:
                self.body_container.content = self._load_template_settings(template_name, template_type)
            case 3:
                self.body_container.content = self._load_resources_settings()
            case _:
                self.body_container.content = self._load_appearance_settings()
                
        if update:
            self.update()
        
    # Called when appearance settings folder is selected
    def _load_appearance_settings(self) -> ft.Container:
        ''' Contains toggle for theme mode, and color scheme dropdown '''
        
        
        # Called when a dropdown option is selected. Saves our choice, and applies it to the page
        async def _set_theme_color(e: ft.Event[ft.Dropdown]):
            ''' Saves our color scheme choice and applies it to the page '''

            # Save our color scheme choice to our objects data
            new_color_key = e.control.value.lower()
            new_color = theme_colors.get(new_color_key, "#A0CAFD")  # Default to blue if not found
            self.update_data(**{'page': {'theme_color': new_color}})
            
            e.control.color = new_color   # Changes the dropdown text color to match the selected color

            # Applies this theme to our page, for both dark and light themes
            self.page.theme.color_scheme_seed = new_color
            self.page.dark_theme.color_scheme_seed = new_color

            # Save the updated settings to the JSON file and update the page
            self.page.update()

        # Dropdown so app can change their color scheme
        theme_color_dropdown = ft.Dropdown(
            label="Theme Color", tooltip="Select the primary color scheme for the app",
            capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
            options=[
                ft.DropdownOption(
                    key=key.capitalize(),
                    content=ft.Text(
                        value=key.capitalize(),
                        color=color_value,
                        weight=ft.FontWeight.BOLD,
                    ),
                ) for key, color_value in theme_colors.items()
            ],
            on_select=_set_theme_color,
            value=str(self.data.get('page', {}).get('theme_color', "blue")),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            color=self.data.get('page', {}).get('theme_color', None),
            dense=True, data="theme_color_dropdown",
        )


        # Called when theme switch is changed. Switches from dark to light theme, or reverse
        def _toggle_theme(e):
            ''' Changes our settings theme data from dark to light or reverse '''

            new_theme_mode = e.control.data   # Grabs the theme mode this button represents

            if new_theme_mode == self.data.get('page', {}).get('theme_mode', "dark"):
                return   # No need to change anything if we're already on this theme
            
            else:
                if new_theme_mode == "dark":
                    e.control.border = ft.Border.all(2, ft.Colors.PRIMARY)
                    self.light_theme_button.border = ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT)
                else:
                    e.control.border = ft.Border.all(2, ft.Colors.PRIMARY)
                    self.dark_theme_button.border = ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT)

            self.update_data(**{'page': {'theme_mode': new_theme_mode}})
            self.page.theme_mode = new_theme_mode
            self.page.update()

        def _set_default_folder_color(e: ft.Event[ft.Dropdown]):
            ''' Sets the default color for new categories '''

            new_color = e.control.value    # Grabs the new color selected   

            self.update_data(**{'story': {'default_folder_color': new_color}})

            # Save our updated settings
            e.control.color = new_color   # Changes the dropdown text color to match the selected color
            e.control.update()


            

        # Button that changes the theme from dark or light when clicked
        self.light_theme_button = ft.Container(
            content=ft.Icon(ft.Icons.LIGHT_MODE, color=ft.Colors.YELLOW_700), height=100, width=100, border_radius=10, data="light",
            border=ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT) if self.data.get('page', {}).get('theme_mode', "dark") == "dark" else ft.Border.all(2, ft.Colors.PRIMARY), 
            bgcolor=ft.Colors.WHITE, on_click=_toggle_theme, tooltip="Set light mode", ink=True
        )
        self.dark_theme_button = ft.Container(
            content=ft.Icon(ft.Icons.DARK_MODE, color=ft.Colors.WHITE), height=100, width=100, border_radius=10, data="dark",
            border=ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT) if self.data.get('page', {}).get('theme_mode', "dark") == "light" else ft.Border.all(2, ft.Colors.PRIMARY), 
            bgcolor=ft.Colors.GREY_900, on_click=_toggle_theme, tooltip="Set dark mode", ink=True
        )
        
        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column([
            ft.Row([
                ft.Text("Appearance", theme_style=ft.TextThemeStyle.HEADLINE_LARGE, expand=True),
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self.close_settings, 
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
                    tooltip="Default color for new Folders",
                    label="Default Folder Color",
                    capitalization= ft.TextCapitalization.SENTENCES,    # Capitalize our options
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            content=ft.Text(
                                value=color.capitalize(),
                                color=color,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ) for color in colors
                    ],
                    on_select=_set_default_folder_color,
                    value=self.data.get('story', {}).get('default_folder_color', "primary"),
                    text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    color=self.data.get('story', {}).get('default_folder_color', "primary"),
                    dense=True, data="folder",
                ),
            ]),   
        ])

        return content
    
    # Called when app settings category is selected
    def _load_widget_settings(self) -> ft.Container:
        ''' Loads our account settings view '''

        # Sets the color in data for each widget upon a change
        def set_default_widget_color(e: ft.Event[ft.MenuItemButton], widget_tag: str):
            color_str = e.control.data
            self.update_data(**{'widget_defaults': {widget_tag: {'color': color_str}}})
            e.control.parent.trailing.color = color_str
            e.control.parent.update()
            

        # Gives a default color changer for each widget
        def create_default_color_selector(widget_tag: str) -> ft.MenuBar:
            return ft.MenuBar(
                [
                    ft.SubmenuButton(
                        f"Default Color",
                        [
                            ft.MenuItemButton(
                                color.capitalize(), True, data=color, style=ft.ButtonStyle(color, mouse_cursor="click"),
                                on_click=lambda e: set_default_widget_color(e, widget_tag),
                            ) for color in colors
                        ],
                        trailing=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('widget_defaults', {}).get(widget_tag, {}).get('color', "#FFFFFF")),
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                        style=ft.ButtonStyle(
                            alignment=ft.Alignment.CENTER, mouse_cursor="click",
                            shape=ft.RoundedRectangleBorder(radius=4), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
                        ),
                    )
                ],
                style=ft.MenuStyle(
                    bgcolor="transparent", shadow_color="transparent",
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                )
            )
        
        # Adjusts the spacing between panels in the preview display
        async def adjust_comic_preview_spacing(e: ft.Event):
            new_spacing = int(e.control.data)
            self.update_data(**{'widget_defaults': {'comic_preview': {'preview_spacing': new_spacing}}})
            e.control.parent.content = f"Preview Spacing: {str(new_spacing)}"
            e.control.parent.update()
            print(new_spacing)
            
        # Adjusts the scaling of the preview display
        async def adjust_comic_preview_scaling(e: ft.Event):
            new_scaling = int(e.control.data)
            self.update_data(**{'widget_defaults': {'comic_preview': {'preview_scale': new_scaling}}})
            e.control.parent.content = f"Preview Scaling: {str(new_scaling)}"
            e.control.parent.update()
            print(new_scaling)
            

        # Sets the background color of the preview display
        async def set_comic_preview_background_color(e: ft.Event):
            new_color = e.control.data
            self.update_data(**{'widget_defaults': {'comic_preview': {'preview_background_color': new_color}}})
            e.control.parent.leading.color = new_color
            e.control.parent.update()
            print(new_color)
            

        # Sets the filter quality of the preview display
        async def set_comic_preview_filter_quality(e: ft.Event):
            new_quality = str(e.control.data)
            self.update_data(**{'widget_defaults': {'comic_preview': {'filter_quality': new_quality}}})
            e.control.parent.content = f"Filter Quality: {new_quality.capitalize()}"
            e.control.parent.update()
            print(new_quality)
            
        async def toggle_comic_preview_anti_aliasing(e: ft.Event):
            new_value = not self.data.get('widget_defaults', {}).get('comic_preview', {}).get('use_anti_aliasing', True)
            self.update_data(**{'widget_defaults': {'comic_preview': {'use_anti_aliasing': new_value}}})
            e.control.content = f"Anti-Aliasing: {str(new_value)}"
            e.control.update()

        async def toggle_comic_preview_direction(e: ft.Event):
            if self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_direction') == "vertical":
                new_value = "horizontal"
            else:
                new_value = "vertical"
            self.update_data(**{'widget_defaults': {'comic_preview': {'preview_direction': new_value}}})
            e.control.content = f"Preview Direction: {str(new_value)}"
            e.control.icon = ft.Icons.SWAP_VERT if new_value == "vertical" else ft.Icons.SWAP_HORIZ
            e.control.update()  


        # Sets our widgets content. May need a 'reload_widget' method later, but for now this works
        content=ft.Column([
            ft.Row([
                ft.Text("Widget Default Settings", theme_style=ft.TextThemeStyle.HEADLINE_LARGE, expand=True),
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self.close_settings, 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings"
                ),
            ]),
            ft.Text("Default Settings for new widgets across all your stories.", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Container(height=10),    # Spacer

            ft.Divider(),
            
            

            ft.Column([
                ft.Text("Document", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("document")),
                create_default_color_selector("document"),
                ft.Divider(),

                ft.Text("Canvas", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("canvas")),
                create_default_color_selector("canvas"),
                ft.Divider(),
                
                ft.Text("Note", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("note")),
                create_default_color_selector("note"),
                ft.Divider(),

                ft.Text("Character", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("character")),
                create_default_color_selector("character"),
                ft.Divider(),

                ft.Text("Plotline", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("plotline")),
                create_default_color_selector("plotline"),
                ft.Divider(),

                ft.Text("Canvas Board", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("canvas_board")),
                create_default_color_selector("canvas_board"),
                ft.Divider(),

                ft.Text("World", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("world")),
                create_default_color_selector("world"),
                ft.Divider(),

                ft.Text("Item", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("item")),
                create_default_color_selector("item"),
                ft.Divider(),

                ft.Text("Plot Chart", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("plot_chart")),
                create_default_color_selector("plot_chart"),
                ft.Divider(),

                ft.Text("Comic Preview", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("comic_preview")),
                create_default_color_selector("comic_preview"),
                
                ft.Button(
                    "Swap Preview Direction", 
                    ft.Icons.SWAP_VERT if self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_direction', "vertical") == "vertical" else ft.Icons.SWAP_HORIZ, 
                    ft.Colors.PRIMARY,
                    tooltip="Swap the preview direction between vertical and horizontal.",
                    on_click=toggle_comic_preview_direction,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                ),
                
                ft.Button(
                    f"Anti-Aliasing: {self.data.get('widget_defaults', {}).get('use_anti_aliasing', True)}",
                    ft.Icons.ANIMATION_OUTLINED, 
                    ft.Colors.PRIMARY,
                    tooltip="If anti aliasing should be used when rendering images in the preview. Will affect performance and image quality.",
                    on_click=toggle_comic_preview_anti_aliasing,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor=ft.MouseCursor.CLICK),
                ),
                ft.SubmenuButton(
                    f"Change Background Color",
                    [
                        ft.MenuItemButton(
                            ft.Icon(ft.Icons.CIRCLE, color), data=color,
                            on_click=set_comic_preview_background_color,
                        ) for color in colors
                    ] + [ft.MenuItemButton("Transparent", data="#00000000", on_click=set_comic_preview_background_color,)],
                    tooltip="Adjust the scale of the preview display.",
                    leading=ft.Icon(ft.Icons.SCALE_OUTLINED, self.data.get('preview_background_color', "#00000000")),
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                    style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                ),
                ft.SubmenuButton(
                    f"Preview Spacing: {self.data.get('preview_spacing', 0)}",
                    [
                        ft.MenuItemButton(
                            str(i), data=i,
                            on_click=adjust_comic_preview_spacing,
                        ) for i in range(0, 21) if i % 2 == 0
                    ],
                    tooltip="Adjust the spacing between panels in the preview display.",
                    leading=ft.Icon(ft.Icons.SPACE_BAR_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                    style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                ),
                
                ft.SubmenuButton(
                    f"Preview Scaling: {self.data.get('preview_scale', 0)}",
                    [
                        ft.MenuItemButton(
                            str(i), data=i,
                            on_click=adjust_comic_preview_scaling,
                        ) for i in range(1, 6)
                    ],
                    tooltip="Adjust the scale of the preview display.",
                    leading=ft.Icon(ft.Icons.CROP_FREE_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                    style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                ),
                
                ft.SubmenuButton(
                    f"Image Filter Quality: {self.data.get('filter_quality', 'medium').capitalize()}",
                    [
                        ft.MenuItemButton("Low", data="low", on_click=set_comic_preview_filter_quality),
                        ft.MenuItemButton("Medium", data="medium", on_click=set_comic_preview_filter_quality),
                        ft.MenuItemButton("High", data="high", on_click=set_comic_preview_filter_quality),
                    ],
                    tooltip="Adjust the filter quality of the preview display. This will affect performance and image quality",
                    leading=ft.Icon(ft.Icons.PHOTO_FILTER_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                    style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                ),      
                ft.Divider(),

                ft.Text("Chart", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("chart")),
                create_default_color_selector("chart"),
                ft.Divider(),

                ft.Text("Character Relationship Map", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("character_relationship_map")),
                create_default_color_selector("character_relationship_map"),

            ], expand=True, scroll=ft.ScrollMode.AUTO),
            
        ], expand=True)
            
        return content
    
    def _load_template_settings(self, selected_template: str = None, selected_type: str = None):
        ''' Loads our template settings view for editing character and world templates '''

        page = self.page

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
            self.page.run_task(self.save_file)

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
                self.section_ctrl: SectionCtrl = section_ctrl
                self.field_name   = field_name
                self.padding      = ft.Padding.symmetric(vertical=2, horizontal=2)
                self._render()

            def _render(self):
                self.content = ft.ReorderableDragHandle(
                    content=ft.Row(
                        [
                            ft.Text(self.field_name, theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE_OUTLINED,
                                icon_color=ft.Colors.ERROR,
                                tooltip="Delete field",
                                #icon_size=18,
                                on_click=lambda e, k=self.field_name: self.section_ctrl._delete_field(k),
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, padding=ft.Padding.all(0)),
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
                self.margin        = ft.Margin.only(bottom=4, top=4)

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
                        spacing=0,
                        #show_default_drag_handles=False,
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
                                    ft.Button(
                                        "Add Field", on_click=self._new_field_clicked,
                                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                    ),
                                    ft.Button(
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
                        ft.Button(
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
                    self.page.pop_dialog()
                    # Auto-select the newly created template
                    self._settings_category_changed(template_name=safe, template_type=ttype)

            tf = ft.TextField(
                dense=True, expand=True,
                capitalization=ft.TextCapitalization.WORDS,
                on_change=_check, on_submit=_do_create, autofocus=True,
            )
            add_btn = ft.TextButton(
                "Create", on_click=_do_create, disabled=True,
                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
            )
            self.page.show_dialog(ft.AlertDialog(
                title=ft.Text(f"Name Your {ttype.capitalize()} Template"),
                content=tf,
                actions=[
                    ft.TextButton(
                        "Cancel", on_click=lambda _: self.page.pop_dialog(),
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
                    self.page.pop_dialog()
                    return
                if safe not in templates and safe.lower() != "default":
                    data = templates.pop(old_name)
                    templates[safe] = data
                    _sync_and_save()
                    self.page.pop_dialog()
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
            self.page.show_dialog(ft.AlertDialog(
                title=ft.Text("Rename Template"),
                content=tf,
                actions=[
                    ft.TextButton(
                        "Cancel", on_click=lambda _: self.page.pop_dialog(),
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
                        shape=ft.RoundedRectangleBorder(radius=4),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
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
                    ft.Icons.CLOSE_OUTLINED, on_click=self.close_settings,
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

        async def _run_tutorial(e=None):
            await self.page.push_route("/tutorial")

        async def _discord_clicked(e=None):
            import webbrowser
            webbrowser.open("https://discord.gg/mGn6zXrJJV")

        
        content=ft.Column([
            ft.Row([
                ft.Text("Resources", theme_style=ft.TextThemeStyle.HEADLINE_LARGE, expand=True),
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self.close_settings, 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings"
                ) 
            ]),
             ft.Row([
                #ft.Text(f"Resources about Story Board!", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(
                    ft.Text("Click here to Run Tutorial\t", color=ft.Colors.PRIMARY, theme_style=ft.TextThemeStyle.BODY_MEDIUM, weight=ft.FontWeight.W_500), 
                    on_click=_run_tutorial,
                ),
                ft.Text("Join our", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT, ),
                ft.Container(
                    ft.Text("Discord", color=ft.Colors.PRIMARY, theme_style=ft.TextThemeStyle.BODY_MEDIUM, weight=ft.FontWeight.W_500),
                    on_click=_discord_clicked,
                ),
                ft.Text("to be part of our community and see upcoming features!", theme_style=ft.TextThemeStyle.BODY_MEDIUM,),
            ], spacing=8), # Link
            
            

            ft.Container(height=10),    # Spacer

            ft.Divider(),
            ft.Container(height=10),    # Spacer


            ft.Text("Widget Descriptions", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD),
            #ft.Container(height=10),

            ft.Column([
                ft.Text(
                    spans=[
                        ft.TextSpan("Document: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("The main widget for creating all novel-based stories. Similar to Microsoft Word or Google Docs, use the document widget as a fully built text editor. Add your own comments, notes, and references to the side of any document!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Canvas: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("The main widget for creating all comic-based stories. This widget allows illustrators to watch their ideas come to life on the Canvas. Create your own drawing masterpiece or upload exported files from another drawing app!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Note: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget for all your ideas, themes, research, etc. Don't let the magic fade, save it here!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Character: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget for all the characters in your story. Flesh out your characters physical look, personality, origin, arcs, etc!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Plotline: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget for visualizing the progression of your story. Create multiple plotlines for arcs, sub arcs, plot points, or regression & multi-timeline stories. Connect events on your plotline to a map and watch your world change over time!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Canvas Board: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget for planning out comic-based chapters for your story. Describe and sketch out your ideas for all you panels ahead of time. Connect them to an existing canvas in your story to see how progress is coming along!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("World: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget to describe your world(s) for your story. Plan out the lore, history, governments, factions, power systems, etc. You can create templates for your worlds, and connect them to existing maps!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Map: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget to visualize locations in your story. Create a map for worlds, countries, cities, dungeons, etc. Connect locations on your map to other maps for a connected feel to your story!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Item: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget for all items, weapons, armor, and MacGuffins in your story!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Plot Chart: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget for fleshing out plotlines in your story in a node to connection based format.", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Comic Preview: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget for comic-based stories for visualizing all your canvases (and external drawings you want to see), in a nice, scrollable vertical or horizontal format. See how your chapter comes together visually before you present it to the world!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Chart: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget for visualizing power systems and other ideas in a chart format. Supports manipulation of bar and radar charts, with implicit animations!", style=ft.TextStyle(size=16))
                    ],
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("Character Relationship Map: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("A widget to visualize how your characters connect to each other within a story. See family trees, friends, enemies, guilds, etc.", style=ft.TextStyle(size=16))
                    ],
                ),
                
            ], spacing=24, scroll=ft.ScrollMode.AUTO, expand=True, alignment=ft.MainAxisAlignment.START, margin=ft.Margin.only(left=20, top=10)),

        ], alignment=ft.MainAxisAlignment.START, expand=True)

        return content
    
    
    # Called when someone expands the drop down holding the color scheme options
    def build(self):
        ''' Reloads our settings view with updated data '''

        # Clear any current controls we have
        self.controls.clear()
        
        # Set our menubar
        menubar = create_menu_bar(self.page, self.story)   

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
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            padding=ft.Padding.all(10),
            content=nav_rail,
        )

        # Build the body of appearance view
        self.body_container = ft.Container(
            expand=True, 
            padding=ft.Padding.all(40),
            #content=self._load_appearance_settings()        # Default to appearance settings when settings are first opened
        )

        self._settings_category_changed(update=False)

        # View is like a column, so top down layout
        self.controls = [
            menubar,
            ft.Container(
                ft.Row(
                    [
                        nav_rail_container,
                        ft.VerticalDivider(thickness=2, width=2),   

                        self.body_container
                    ],
                    spacing=0, expand=True
                ),
                expand=True,
            )
            
        ]



