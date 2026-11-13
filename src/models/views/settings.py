''' 
Model for our settings widget. Settings widget stores app and story settings, and displays them in a tab
A Settings object is created for every story
'''

import flet as ft
from models.views.story import Story
from constants import SETTINGS_FILE_PATH, APP_DATA_PATH
from styles.colors import colors, theme_colors
import os
import json
from view_components.menu_bar import MenuBar
from styles.snack_bar import SnackBar
from models.dataclasses.character_template import default_character_template_data
from models.dataclasses.item_template import default_item_template_data
from models.dataclasses.world_template import default_world_template_data
from models.dataclasses.templates import TEMPLATE_DEFAULTS, get_template
import asyncio
from styles.text_fields import SettingsTextField
import base64

 
class Settings(ft.View):

    # Constructor
    def __init__(
        self, 
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

        # Set attributes
        self.route = "/settings"   # Sets our route for our settings view
        self.story = story
        self.data = data
        self.selected_index = selected_index

        # If we're new, give default values for our data 
        if data is None or data == {}:
            self.data = {
                
                
                'is_first_launch': True,    # If this is the first time the app has been launched or not
                'sync_with_cloud_on_close': False,   # If the app should sync with Google Drive on close
                'sync_with_cloud_on_launch': False,   # If the app should sync with Google Drive on launch

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
                    'tree_view_rail_width': 250,  
                    'default_folder_color': "primary",    # Categories thrown in here
                    'show_canvas_rail': True,   # If the canvas rail is hidden or not
                    'rail_sort_method': "default",   # Method to sort items in the rail. Defaul lets OS decide, alphabetically, color, creation date
                },

                # Default settings for the newly created widgets. All have a color, but can have additional settings specific to each widget type.
                'widget_defaults': {
                    'manuscript': {
                        'color': "primary",
                        'export_file_type': ".docx"   # Default export file type for plotlines
                    },
                    'canvas': {
                        'color': "primary",
                        'use_standard_cursor': True,     # if the mouse cursor will reflect the current paint settings or not. False=standard cursor
                        'export_file_type': ".png"   # Default export file type for plotlines
                    },
                    'note': {
                        'color': "primary"
                    },
                    'character': {
                        'color': "primary"
                    },
                    'plotline': {
                        'color': "primary",
                        'show_division_labels': True,  # Whether to show each divisions label or not
                        'starting_division_count': 9,    # Default number of divisions for new plotlines
                        'plot_point_color': "white",   # Default color for new plot points
                        'export_file_type': ".json"   # Default export file type for plotlines
                    },
                    'canvas_board': {
                        'color': "primary",
                    },
                    'map': {
                        'color': "primary",
                        'draw_mode': False,   # If the map is in draw mode or not
                        'background_image': "map_bg_fantasy_dark.png",   # Default background image for new maps
                        'export_file_type': ".json"   # Default export file type for maps
                    },
                    'world': {
                        'color': "primary"
                    },
                    'item': {
                        'color': "primary"
                    },
                    'plot_chart': {
                        'color': "primary",
                        'node_color': "white",
                        'spider_web_view': False,   # If the plot chart is in spider web view or not
                        'export_file_type': ".json"   # Default export file type for plotlines
                    },
                    'comic_preview': {
                        'color': "primary",
                        'preview_direction': "vertical",            # Default direction for comic preview, can be vertical or horizontal
                        'preview_background_color': "#000000",  # Background color behind images
                        'preview_spacing': 0,                       # Spacing between images
                        'preview_scale': 2,                         # Scale of the images in the preview, 1 = 1:1, 2 = 2:1, etc. 
                        'filter_quality': "medium",                 # Filter quality for the images in the preview, can be low, medium, or high
                        'anti_aliasing': True,                  # Whether to use anti-aliasing when rendering the images in the preview
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
                        'color': "primary",
                        'export_file_type': ".json"   # Default export file type for plotlines
                    }
                },

                # Paint settings for our canvas drawings to use as default that users can change
                'paint_settings': {
                    'color': "#FFFFFF",     # Hex color folowed by opacity
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
                    #'capture_ratio': 1,                       # Ratio to capture the canvas. Higher means better quality -> worse performance
                    'current_control_mode': "draw",      # Either drawing, (use brush settings), tools (use built in tools), or text
                    'current_brush_name': "stroke",      # Name of the currently selected brush, either default or custom. Just used for display purposes
                    'current_tool_name': "erase",        # Current tool or shape being used

                   
                    'use_brush_smoothing': True,         # Uses cv.Path for constistant shapes if true, otherwise use cv.line
                    'stroke_smoothing_strength': 1,        # If stroke smoothing is enabled, how strong the smoothing is. 1 = low, 10 = high 0=off
                    'saved_brushes': dict(),             # Saved brushes the user has created that we can load
                    'saved_colors': list(),              # Saved colors the user has created that we can load [{'name': 'name_val', 'value': 'value']
                    'saved_text_settings': dict(),          # Saved text settings the user has created that we can load
                    # Other shape settings
                    #'use_paint_for_shapes': True,           # If True, shapes are black/white and use default paint settings rather than live brush settings
                    'rectangle_border_radius': 0,               # Border radius for rectangle shapes
                },
                'text_settings': {
                    'size': 14,
                    'weight': "normal",  # Options: None, w100, w200, w300, w400, w500, w600, w700, w800, w900, bold
                    'italic': False,
                    'decoration': None,  # Options: none, underline, overline, line_through
                    'decoration_color': None,
                    'decoration_thickness': 1,
                    'decoration_style': "solid",    # options: solid, wavy, double, dotted, dashed
                    'font_family': None,
                    'color': "#FFFFFF",  # Hex color folowed by opacity
                    'bgcolor': "#00000000",  # Background color for text shapes
                    'shadow': {
                        'blur_radius': 0,
                        'blur_style': 'normal', # Options: normal, solid, outer, inner
                        'color': "#00000000",
                        'offset': (0, 0),
                        'spread_radius': 0,
                    },   # Boxshad values
                    'foreground': None, # [list of gradients/color values] (ft.PaintLinearGradient, ft.PaintRadialGradient, ft.PaintGradient ft.PaintSweepGradient)
                    'letter_spacing': 0,
                    'word_spacing': 0,
                    'baseline': "alphabetic",  # How text is rendered - Options: alphabetic or ideographic
                },

                'character_template': default_character_template_data(),
                'world_template': default_world_template_data(),
                'item_template': default_item_template_data(),

            }
            
            
        
        

    
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

        try:
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            # Save the data to the file (creates file if doesnt exist)
            with open(SETTINGS_FILE_PATH, "w", encoding='utf-8') as f:   
                json.dump(self.data, f, indent=4)
        
        except Exception as e:
            print(f"Error saving settings to {SETTINGS_FILE_PATH}: {e}")

    async def close_settings(self, e=None):
        ''' Closes the settings view and returns to the story or home view '''
        await self.save_file()
        await self.page.push_route(self.story.route if self.story is not None else "/")

    async def save_story(self, e=None):
        ''' Called when the page is closed. Saves any dirty changes '''
        if self.story is not None:
            for widget in self.story.widgets.values():
                await widget.save_file()
            await self.story.save_file()
        await self.save_file()
        
    # Called when the page is resized
    def page_resized(self, e: ft.WindowEvent):
        ''' This is set inside of app.load_settings() to be called whenever the page is resized. Saves the new page size to data/if its maximized'''
        from models.app import app  

        # Catch page resizing when app is initializing and ignore them
        if app.ignore_settings_change == True:     
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
    def _settings_category_changed(self, e: ft.Event[ft.NavigationRail]=None, update: bool=True):
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
                self.body_container.content = self._load_template_settings()
            case 3:
                self.body_container.content = self._load_resources_settings()
            case 4:
                self.body_container.content = self._load_cloud_settings()
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


            ft.Switch(
                label="Show Canvas Rail", margin=ft.Margin.only(top=10),
                value=self.data.get('story', {}).get('show_canvas_rail', False), 
                on_change=lambda e: self.update_data(**{'story': {'show_canvas_rail': e.control.value}}),
                tooltip="Show or hide the canvas rail on the left side of the page. Turn off if you never plan on drawing",
            ),

        ])

        return content
    
    # Called when app settings category is selected
    def _load_widget_settings(self) -> ft.Container:
        ''' Loads our account settings view '''

        class Dropdown(ft.Dropdown):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.dense=True
                self.menu_style=ft.MenuStyle(alignment=ft.Alignment.CENTER_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4))
                self.fill_color=ft.Colors.SURFACE_CONTAINER_HIGHEST
                self.filled=True
                self.capitalization=ft.TextCapitalization.WORDS
                self.content_padding=ft.Padding.only(left=10)
                self.border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4)
                self.text_style=ft.TextStyle(weight=ft.FontWeight.BOLD)
                self.label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY)
                self.margin=ft.Margin.only(left=20)
                self.width=200

        class Switch(ft.Switch):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.adaptive=True
                self.margin=ft.Margin.only(left=20)

        class Button(ft.Button):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
                self.margin=ft.Margin.only(left=20)
                self.icon_color=ft.Colors.PRIMARY
                

        # Sets the color in data for each widget upon a change
        def set_default_widget_color(e: ft.Event[Dropdown]):
            new_color = e.control.value.lower()
            widget_tag = e.control.data
            self.update_data(**{'widget_defaults': {widget_tag: {'color': new_color}}})
            e.control.color = new_color
            e.control.update()
            

        def update_plotline_division_count(e: ft.Event[ft.TextField]):
            if not e.control.value:
                e.control.error = "Please enter a valid number"
                e.control.value = str(self.data.get('widget_defaults', {}).get('plotline', {}).get('starting_division_count', 9))
                e.control.update()
                return
            elif int(e.control.value) < 0 or int(e.control.value) > 30:
                e.control.error = "Maximum is 30"
                e.control.value = str(self.data.get('widget_defaults', {}).get('plotline', {}).get('starting_division_count', 9))
                e.control.update()
                return
            e.control.error = None
            new_count = int(e.control.value)
            self.update_data(**{'widget_defaults': {'plotline': {'starting_division_count': new_count}}})
            e.control.update()

        def update_plotline_pp_color(e: ft.Event[ft.Dropdown]):
            new_color = e.control.value.lower()
            self.update_data(**{'widget_defaults': {'plotline': {'plot_point_color': new_color}}})
            e.control.color = new_color
            e.control.update()

        async def update_map_bg_image(e: ft.Event[ft.Dropdown]):
            new_image = e.control.value
            if new_image == "upload_image":   # Wait for user to pick and image if uploading
                new_image = await get_uploaded_map_bg_image()
            if not new_image:   # If user canceled the upload, just return
                new_image = self.data.get('widget_defaults', {}).get('map', {}).get('background_image', "map_bg_fantasy_dark.png")
                e.control.value = self.data.get('widget_defaults', {}).get("map", {}).get('background_image', "map_bg_fantasy_dark.png")  # Reset the dropdown to the previous value
                e.control.update()
                return
            self.update_data(**{'widget_defaults': {'map': {'background_image': new_image}}})
            

        # Uploads an image and sets it as the background image for our map
        async def get_uploaded_map_bg_image():
            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:
                file_path = files[0].path
                try:
                    with open(file_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        return encoded_string
                except Exception:
                    pass

        # Sets the color in data for each widget upon a change
        def set_default_node_color(e: ft.Event[Dropdown]):
            new_color = e.control.value.lower()
            self.update_data(**{'widget_defaults': {'plot_chart': {'node_color': new_color}}})
            e.control.color = new_color
            e.control.update()

        def toggle_comic_preview_direction(e: ft.Event[ft.Button]):
            new_direction = "horizontal" if self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_direction', "vertical") == "vertical" else "vertical"
            self.update_data(**{'widget_defaults': {'comic_preview': {'preview_direction': new_direction}}})
            e.control.icon = ft.Icons.SWAP_VERT if new_direction == "vertical" else ft.Icons.SWAP_HORIZ
            e.control.update()

        # Sets the color in data for each widget upon a change
        def set_comic_preview_background_color(e: ft.Event[Dropdown]):
            new_color = e.control.value.lower()
            self.update_data(**{'widget_defaults': {'comic_preview': {'preview_background_color': new_color}}})
            e.control.color = new_color
            e.control.update()

        def toggle_plot_chart_spider_web_view(e: ft.Event):
            new_value = not self.data.get('widget_defaults', {}).get('plot_chart', {}).get('spider_web_view', False)
            self.data['widget_defaults']['plot_chart']['spider_web_view'] = new_value
            self.update_data(**{'widget_defaults': {'plot_chart': {'spider_web_view': new_value}}})
            if new_value:
                e.control.icon = ft.Icons.VERTICAL_DISTRIBUTE_OUTLINED
            else:
                e.control.icon = ft.Icons.SHOW_CHART
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
                ft.Text("Manuscript", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("manuscript")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('manuscript', {}).get('color', "primary")).capitalize(),
                    label="Default Manuscript Color", 
                    color=self.data.get('widget_defaults', {}).get('manuscript', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="manuscript",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                ft.Divider(),

                ft.Text("Canvas", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("canvas")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('canvas', {}).get('color', "primary")).capitalize(),
                    label="Default Canvas Color", 
                    color=self.data.get('widget_defaults', {}).get('canvas', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="canvas",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                Switch(
                    value=self.data.get('widget_defaults', {}).get('canvas', {}).get('use_standard_cursor', True),
                    label="Use Standard Mouse Cursor", 
                    tooltip="Whether to use a standard mouse cursor for Canvases or use a mouse cursor that reflects the current brush settings.",
                    on_change=lambda e: self.update_data(**{'widget_defaults': {'canvas': {'use_standard_cursor': e.control.value}}}),
                ),
                ft.Divider(),
                
                ft.Text("Note", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("note")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('note', {}).get('color', "primary")).capitalize(),
                    label="Default Note Color", 
                    color=self.data.get('widget_defaults', {}).get('note', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="note",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                ft.Divider(),

                ft.Text("Plotline", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("plotline")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('plotline', {}).get('color', "primary")).capitalize(),
                    label="Default Plotline Color",
                    color=self.data.get('widget_defaults', {}).get('plotline', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="plotline",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),

                

                SettingsTextField(    # Change the default number of divisions for new plotlines
                    label="Starting Division Count",
                    value=str(self.data.get('widget_defaults', {}).get('plotline', {}).get('starting_division_count', 4)),
                    tooltip="The default number of divisions for new plotlines.",
                    input_filter=ft.NumbersOnlyInputFilter(),
                    on_blur=update_plotline_division_count
                ),
                
                # Default plotpoint color
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('plotline', {}).get('plot_point_color', "primary")).capitalize(),
                    label="Default Plot Point Color", 
                    color=self.data.get('widget_defaults', {}).get('plotline', {}).get('plot_point_color', "primary"),
                    on_select=update_plotline_pp_color,
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                Switch(
                    value=self.data.get('widget_defaults', {}).get('plotline', {}).get('show_division_labels', True),
                    label="Show Division Labels",
                    tooltip="Whether to show each divisions label or not.",
                    on_change=lambda e: self.update_data(**{'widget_defaults': {'plotline': {'show_division_labels': e.control.value}}}),
                ),

                ft.Divider(),

                ft.Text("Canvas Board", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("canvas_board")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('canvas_board', {}).get('color', "primary")).capitalize(),
                    label="Default Canvas Board Color", 
                    color=self.data.get('widget_defaults', {}).get('canvas_board', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="canvas_board",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),


                ft.Divider(),

                # Map options
                ft.Text("Map", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("map")),

                # Default map color
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('map', {}).get('color', "primary")).capitalize(),
                    label="Default Map Color", 
                    color=self.data.get('widget_defaults', {}).get('map', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="map",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),

                

                # Set defualt background image for new maps
                Dropdown(
                    label="Default Background Image",
                    value=self.data.get('widget_defaults', {}).get("map", {}).get('background_image', "map_bg_fantasy_dark.png"),
                    on_select=update_map_bg_image,
                    color=ft.Colors.ON_SURFACE,
                    options=[
                        ft.DropdownOption(
                            key="map_bg_fantasy_dark.png",
                            text="Dark Fantasy",
                            content=ft.Text("Dark Fantasy", weight=ft.FontWeight.BOLD),
                            leading_icon=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY)
                        ),
                        ft.DropdownOption(
                            key="map_bg_fantasy_light.png",
                            text="Light Fantasy",
                            content=ft.Text("Light Fantasy", weight=ft.FontWeight.BOLD),
                            leading_icon=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY)
                        ),
                        ft.DropdownOption(
                            key="map_bg_scifi.png",
                            text="Sci-Fi",
                            content=ft.Text("Sci-Fi", weight=ft.FontWeight.BOLD),
                            leading_icon=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY)
                        ),
                        ft.DropdownOption(
                            key="map_bg_space.jpg",
                            text="Space",
                            content=ft.Text("Space", weight=ft.FontWeight.BOLD),
                            leading_icon=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY)
                        ),
                        ft.DropdownOption(
                            key="upload_image",
                            text="Upload Image",
                            content=ft.Text("Upload Image", weight=ft.FontWeight.BOLD),
                            leading_icon=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY)
                        )
                    ],
                ),
                # Map draw mode
                Switch(
                    value=self.data.get('widget_defaults', {}).get('map', {}).get('draw_mode', False),
                    label="Draw Mode",
                    on_change=lambda e: self.update_data(**{'widget_defaults': {'map': {'draw_mode': e.control.value}}}),

                ),

                ft.Divider(),

                
                # Item options
                ft.Text("Item", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("item")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('item', {}).get('color', "primary")).capitalize(),
                    label="Default Item Color", 
                    color=self.data.get('widget_defaults', {}).get('item', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="item",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                ft.Divider(),

                # Plot Chart Options
                ft.Text("Plot Chart", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("plot_chart")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('plot_chart', {}).get('color', "primary")).capitalize(),
                    label="Default Plot Chart Color", 
                    color=self.data.get('widget_defaults', {}).get('plot_chart', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="plot_chart",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                Dropdown(       # New Node Colors
                    value=str(self.data.get('widget_defaults', {}).get('plot_chart', {}).get('node_color', "white")).capitalize(),
                    label="Default Node Color", 
                    color=self.data.get('widget_defaults', {}).get('plot_chart', {}).get('node_color', "white"),
                    on_select=set_default_node_color,
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                Button(
                    content="Toggle Connector View",
                    icon=ft.Icons.VERTICAL_DISTRIBUTE_OUTLINED if self.data.get('spider_web_view', False) == True else ft.Icons.SHOW_CHART,
                    tooltip="Toggle between spider web connections and 3 line connections",
                    on_click=toggle_plot_chart_spider_web_view
                ),
                
                ft.Divider(),

                ft.Text("Comic Preview", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("comic_preview")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('comic_preview', {}).get('color', "primary")).capitalize(),
                    label="Default Comic Preview Color", 
                    color=self.data.get('widget_defaults', {}).get('comic_preview', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="comic_preview",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_background_color', "transparent")).capitalize(),   
                    label="Preview Background Color",
                    color=self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_background_color', "transparent"),
                    on_select=set_comic_preview_background_color,
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ], #+ [ft.MenuItemButton("Transparent", data="#00000000", on_click=set_comic_preview_background_color,)],
                    tooltip="Background color for transparent panels in the preview display, as well as between panels",
                ),
                Dropdown(
                    label="Panel Spacing",
                    value=str(self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_spacing', 0)),
                    on_select=lambda e: self.update_data(**{'widget_defaults': {'comic_preview': {'preview_spacing': int(e.control.value)}}}),
                    options=[
                        ft.DropdownOption(
                            key=str(i),
                            text=str(i),
                            content=ft.Text(str(i), weight=ft.FontWeight.BOLD),
                        ) for i in range(0, 21) if i % 2 == 0
                    ],
                    tooltip="Adjust the spacing between panels in the preview display.",
                ),
                Dropdown(
                    label="Preview Scaling",
                    value=str(self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_scale', 1)),
                    on_select=lambda e: self.update_data(**{'widget_defaults': {'comic_preview': {'preview_scale': int(e.control.value)}}}),
                    options=[
                        ft.DropdownOption(
                            key=str(i),
                            text=str(i),
                            content=ft.Text(str(i), weight=ft.FontWeight.BOLD),
                        ) for i in range(1, 6)
                    ],
                    tooltip="Adjust the scale of the preview display.",
                ),
                Dropdown(
                    label="Filter Quality",
                    value=str(self.data.get('widget_defaults', {}).get('comic_preview', {}).get('filter_quality', "medium")).capitalize(),
                    on_select=lambda e: self.update_data(**{'widget_defaults': {'comic_preview': {'filter_quality': e.control.value.lower()}}}),
                    options=[
                        ft.DropdownOption(
                            key=quality.capitalize(),
                            text=quality.capitalize(),
                            content=ft.Text(quality.capitalize(), weight=ft.FontWeight.BOLD),
                        ) for quality in ["low", "medium", "high"]
                    ],
                    tooltip="Adjust the filter quality of the preview display. This will affect performance and image quality.",
                ),
                Button(
                    "Preview Direction", 
                    ft.Icons.SWAP_VERT if self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_direction', "vertical") == "vertical" else ft.Icons.SWAP_HORIZ, 
                    tooltip="Swap the preview direction between vertical and horizontal.",
                    on_click=toggle_comic_preview_direction,
                ),
                Switch(
                    value=self.data.get('widget_defaults', {}).get('comic_preview', {}).get('anti_aliasing', True),
                    label="Anti-Aliasing",
                    tooltip="If anti aliasing should be used when rendering images in the preview. Will affect performance and image quality.",
                    on_change=lambda e: self.update_data(**{'widget_defaults': {'comic_preview': {'anti_aliasing': e.control.value}}})
                ),
                
                
                ft.Divider(),


                ft.Text("Character Relationship Map", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("character_relationship_map")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('character_relationship_map', {}).get('color', "primary")).capitalize(),
                    label="Default Character Relationship Map Color", 
                    color=self.data.get('widget_defaults', {}).get('character_relationship_map', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="character_relationship_map",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),

                ft.SubmenuButton(
                    f"Image Filter Quality: {self.data.get('filter_quality', 'medium').capitalize()}",
                    [
                        #ft.MenuItemButton("Low", data="low", on_click=set_comic_preview_filter_quality),
                        #ft.MenuItemButton("Medium", data="medium", on_click=set_comic_preview_filter_quality),
                        #ft.MenuItemButton("High", data="high", on_click=set_comic_preview_filter_quality),
                    ],
                    tooltip="Adjust the filter quality of the preview display. This will affect performance and image quality",
                    leading=ft.Icon(ft.Icons.PHOTO_FILTER_OUTLINED, self.data.get('color', ft.Colors.PRIMARY)),
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_LEFT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                    style=ft.ButtonStyle(alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                ),      
                ft.Divider(),

                ft.Text("Character", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("character")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('character', {}).get('color', "primary")).capitalize(),
                    label="Default Character Color", 
                    color=self.data.get('widget_defaults', {}).get('character', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="character",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                ft.Divider(),

                ft.Text("World", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("world")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('world', {}).get('color', "primary")).capitalize(),
                    label="Default World Color", 
                    color=self.data.get('widget_defaults', {}).get('world', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="world",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                ),
                ft.Divider(),

                ft.Text("Chart", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, key=ft.ScrollKey("chart")),
                Dropdown(
                    value=str(self.data.get('widget_defaults', {}).get('chart', {}).get('color', "primary")).capitalize(),
                    label="Default Chart Color", 
                    color=self.data.get('widget_defaults', {}).get('chart', {}).get('color', "primary"),
                    on_select=set_default_widget_color,
                    data="chart",
                    options=[
                        ft.DropdownOption(
                            key=color.capitalize(),
                            text=color.capitalize(),
                            content=ft.Text(color.capitalize(), color=color, weight=ft.FontWeight.BOLD),
                        ) for color in colors
                    ]
                )

                

            ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=16),
            
        ], expand=True)
            
        return content

    def _load_template_settings(self):
        types = ("character", "world", "item")
        editor = ft.Container(expand=True, padding=ft.Padding.all(10))

        def refresh():
            widget_type = types[rail.selected_index]
            template = get_template(self.data, widget_type)
            is_item = widget_type == "item"

            def redraw():
                refresh()
                editor.update()

            def move(values, old_index, new_index):
                if isinstance(values, dict):
                    entries = list(values.items())
                    entries.insert(new_index, entries.pop(old_index))
                    values.clear()
                    values.update(entries)
                else:
                    values.insert(new_index, values.pop(old_index))
                redraw()

            def order_buttons(values, index, label):
                return [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_UPWARD, tooltip=f"Move {label} up",
                        disabled=index == 0,
                        on_click=lambda e: move(values, index, index - 1),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ARROW_DOWNWARD, tooltip=f"Move {label} down",
                        disabled=index == len(values) - 1,
                        on_click=lambda e: move(values, index, index + 1),
                    ),
                ]

            def add_input(label, names, add):
                field = ft.TextField(
                    label=f"New {label}", dense=True, expand=True,
                    capitalization=ft.TextCapitalization.WORDS,
                )
                button = ft.TextButton("Add")
                row = ft.Row(visible=False, expand=True)

                async def show(e):
                    row.visible = True
                    show_button.visible = False
                    editor.update()
                    await field.focus()

                def cancel(e):
                    row.visible = False
                    show_button.visible = True
                    field.value = ""
                    field.error = None
                    editor.update()

                def submit(e):
                    name = (field.value or "").strip()
                    if not name or name in names():
                        field.error = "Name already exists or is empty"
                        field.update()
                        return
                    add(name)
                    redraw()

                field.on_submit = submit
                button.on_click = submit
                row.controls = [
                    field, button,
                    ft.TextButton("Cancel", on_click=cancel),
                ]
                show_button = ft.TextButton(f"Add {label}", on_click=show)
                return ft.Row([show_button, row], tight=True, spacing=0, expand=True)

            def field_list(fields):
                rows = []
                names = list(fields) if isinstance(fields, dict) else [field["title"] for field in fields]
                for index, name in enumerate(names):
                    def delete(e, name=name, index=index):
                        if isinstance(fields, dict):
                            del fields[name]
                        else:
                            fields.pop(index)
                        redraw()

                    rows.append(
                        ft.ReorderableDragHandle(
                            ft.Row([
                                ft.Text(name, expand=True),
                                
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,
                                    tooltip="Delete field", on_click=delete,
                                ),
                                ft.Container(width=48),
                            ],  spacing=0, margin=ft.Margin.only(left=10),), 
                            mouse_cursor=ft.MouseCursor.GRAB, expand=True,
                            key=str(index),
                        )
                    )

                if not rows:
                    return ft.Container(height=0)

                def reorder(e: ft.OnReorderEvent):
                    if e.old_index is None or e.new_index is None:
                        raise ValueError("Field reorder event is missing an index")
                    move(fields, e.old_index, e.new_index)

                return ft.ReorderableListView(
                    controls=rows, height=48 * len(rows), item_extent=48,
                    show_default_drag_handles=True, on_reorder=reorder,
                )

            def field_input(fields):
                def names():
                    return fields if isinstance(fields, dict) else [field["title"] for field in fields]

                def add(name):
                    if isinstance(fields, dict):
                        fields[name] = ""
                    else:
                        fields.append({"title": name, "content": ""})

                return add_input("Field", names, add)

            def reset(e):
                def confirm(e):
                    self.data[f"{widget_type}_template"] = TEMPLATE_DEFAULTS[widget_type]()
                    self.page.pop_dialog()
                    redraw()

                self.page.show_dialog(ft.AlertDialog(
                    title=ft.Text(f"Reset {widget_type.capitalize()} Template?"),
                    content=ft.Text("This replaces the current template with its defaults."),
                    actions=[
                        ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog()),
                        ft.TextButton("Reset", on_click=confirm),
                    ],
                ))

            controls = [
                ft.Row([
                    ft.Text(f"{widget_type.capitalize()} Template",
                            theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM, expand=True),
                    ft.TextButton("Reset to Defaults", on_click=reset),
                ]),
                ft.Divider(),
            ]
            if is_item:
                controls.append(field_list(template))
                controls.append(field_input(template))
            else:
                for index, (name, fields) in enumerate(template.items()):
                    def delete_section(e, name=name):
                        del template[name]
                        redraw()

                    controls.append(ft.Container(
                        border_radius=ft.BorderRadius.all(10),
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        margin=ft.Margin.all(2),
                        shadow=ft.BoxShadow(
                            blur_radius=2, #color=ft.Colors.with_opacity(0.18, ft.Colors.BLACK),
                            #offset=ft.Offset(0, 1),
                        ),
                        padding=ft.Padding.all(10),
                        content=ft.Column([
                            ft.Row([
                                ft.Text(name, theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                        weight=ft.FontWeight.BOLD,),
                                field_input(fields),
                                ft.Container(expand=True),
                                *order_buttons(template, index, "section"),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,
                                    tooltip="Delete section", on_click=delete_section,
                                ),
                            ]),
                            field_list(fields),
                        ], tight=True, spacing=0),
                    ))
                controls.append(add_input("Section", lambda: template, lambda name: template.update({name: {}})))

            editor.content = ft.Column(controls, scroll=ft.ScrollMode.AUTO, expand=True)

        def select(e):
            refresh()
            editor.update()

        rail = ft.NavigationRail(
            selected_index=0,
            bgcolor=ft.Colors.TRANSPARENT,
            label_type=ft.NavigationRailLabelType.ALL,
            on_change=select,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.PERSON_OUTLINED, label="Character"),
                ft.NavigationRailDestination(icon=ft.Icons.PUBLIC_OUTLINED, label="World"),
                ft.NavigationRailDestination(icon=ft.Icons.STAR_OUTLINE_ROUNDED, label="Item"),
            ],
        )
        refresh()
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
                [rail, ft.VerticalDivider(), editor, ft.Container(width=10)],
                scroll="none", expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ])

    
    def _load_resources_settings(self):
        ''' Loads our resources settings view '''

        async def _run_tutorial(e=None):
            await self.page.push_route("/tutorial")

        async def _discord_clicked(e=None):
            import webbrowser
            webbrowser.open("https://discord.gg/FMXPwxB5G3")

        
        content = ft.Column([
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
                        ft.TextSpan("Manuscript: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("The main widget for creating all novel-based stories. Similar to Microsoft Word or Google Docs, use the manuscript widget as a fully built text editor. Add your own comments, notes, and references to the side of any Manuscript!", style=ft.TextStyle(size=16))
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

    def _load_cloud_settings(self):
        from models.app import app
        from utils import google_drive

        

        async def _connect_clicked(e=None):
            if app.is_cloud_authenticated:
                await asyncio.to_thread(google_drive.disconnect)
                app.is_cloud_authenticated = False
                self.update_data(**{'sync_with_cloud_on_close': False, 'sync_with_cloud_on_launch': False})
                await self.save_file()
                self._settings_category_changed()
                self.page.show_dialog(SnackBar("Disconnected from Google Drive."))
                return
            try:
                self.page.show_dialog(SnackBar("Opening browser to connect your Google account..."))
                await asyncio.to_thread(google_drive.authenticate)
                app.is_cloud_authenticated = True
                self._settings_category_changed()
                self.page.show_dialog(SnackBar("Google account connected."))
            except Exception as ex:
                self.page.show_dialog(SnackBar(google_drive.describe_error(ex)))

        async def _run_with_route(route: str, work):
            ''' Shows the saving/pulling view while work() runs, then returns to settings with a result snackbar '''
            page = self.page    # Captured because this view unmounts while we are away
            await page.push_route(route)
            try:
                message = await work()
            except Exception as ex:
                message = google_drive.describe_error(ex)
            await page.push_route("/settings")
            page.show_dialog(SnackBar(message))

        async def _push_story_clicked(e=None):
            if self.story is None:
                return
            story = self.story

            async def work():
                await story.save_file()
                count = await asyncio.to_thread(google_drive.push_story, story.data.get('directory_path'))
                return f"Pushed story to Google Drive ({count} files)"
            await _run_with_route("/saving_to_cloud", work)

        async def _push_settings_clicked(e=None):
            async def work():
                await self.save_file()
                await asyncio.to_thread(google_drive.push_settings, self.data)
                return "Pushed settings to Google Drive"
            await _run_with_route("/saving_to_cloud", work)

        def _confirm(title: str, message: str, on_confirm):
            ''' Pulls overwrite local data, so ask first '''
            page = self.page

            async def _confirmed(e=None):
                page.pop_dialog()
                await on_confirm()
            page.show_dialog(ft.AlertDialog(
                modal=True, title=ft.Text(title), content=ft.Text(message),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda: page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click")),
                    ft.TextButton("Pull and overwrite local", on_click=_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                ],
            ))

        async def _do_pull_story():
            story = self.story

            async def work():
                count = await asyncio.to_thread(google_drive.pull_story, story.data.get('directory_path'))
                with open(story.data.get('file_path'), "r", encoding='utf-8') as f:
                    new_story = Story(story.data.get('title'), json.load(f))
                app.stories[story.data.get('id')] = new_story
                self.story = new_story
                return f"Pulled story from Google Drive ({count} files)"
            await _run_with_route("/pulling_from_cloud", work)

        async def _do_pull_settings():
            async def work():
                cloud_settings = await asyncio.to_thread(google_drive.pull_settings)
                cloud_settings['page'] = self.data.get('page', {})   # Window settings are device specific
                self.data = cloud_settings
                await self.save_file()
                return "Pulled settings from Google Drive"
            await _run_with_route("/pulling_from_cloud", work)

        async def _pull_story_clicked(e=None):
            if self.story is None:
                return
            _confirm(
                "Pull story from cloud?",
                f"This replaces the local version of '{self.story.data.get('title')}' with the one in your Google Drive.",
                _do_pull_story,
            )

        async def _pull_settings_clicked(e=None):
            _confirm(
                "Pull settings from cloud?",
                "This replaces your local settings (except window settings) with the ones in your Google Drive.",
                _do_pull_settings,
            )
        def _push_on_close_changed(e):
            value = bool(e.control.value)
            updates = {'sync_with_cloud_on_close': value}
            if not value:
                updates['sync_with_cloud_on_launch'] = False
            self.update_data(**updates)
            self._settings_category_changed()

        def _pull_on_launch_changed(e):
            self.update_data(**{'sync_with_cloud_on_launch': bool(e.control.value)})

        authed = app.is_cloud_authenticated
        
        connect_button = ft.IconButton(
            ft.Icons.CLOUD_DONE_OUTLINED if authed else ft.Icons.CLOUD_OFF_OUTLINED,
            icon_color=ft.Colors.PRIMARY,# if authed else ft.Colors.ERROR,
            on_click=_connect_clicked,  mouse_cursor="click", bgcolor=ft.Colors.SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
            tooltip="Connect to Google Drive" if not authed else "Disconnect from Google Drive"
        )

        story_title = self.story.data.get('title') if self.story else "None"
        has_story = authed and self.story is not None
        push_story_button = ft.IconButton(
            ft.CupertinoIcons.BOOK,
            icon_color=ft.Colors.PRIMARY if has_story else ft.Colors.ERROR,
            disabled=not has_story,
            on_click=_push_story_clicked, icon_size=50, mouse_cursor="click" if has_story else None, bgcolor=ft.Colors.SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
        )
        push_story_desc = (
            f"Push current story: {story_title} to cloud, overriding the existing version in the cloud." if has_story
            else ("Open a story to push it" if authed else "Connect to Google Drive first")
        )

        pull_story_button = ft.IconButton(
            ft.CupertinoIcons.BOOK,
            icon_color=ft.Colors.PRIMARY if has_story else ft.Colors.ERROR,
            disabled=not has_story,
            on_click=_pull_story_clicked, icon_size=50, mouse_cursor="click" if has_story else None, bgcolor=ft.Colors.SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
        )
        pull_story_desc = (
            f"Pull current story: {story_title} from cloud, overriding the existing local version." if has_story
            else ("Open a story to pull it" if authed else "Connect to Google Drive first")
        )

        push_settings_desc = "Push Story Board settings to cloud. These settings include: " if authed else "Connect to Google Drive first"
        push_settings_details = f"- Character and World Templates\n- Paint Brushes and Saved Font configurations\n- Widget defaults and other settings" if authed else ""

        push_settings_button = ft.IconButton(
            ft.Icons.SETTINGS_OUTLINED,
            icon_color=ft.Colors.PRIMARY if authed else ft.Colors.ERROR,
            disabled=not authed, on_click=_push_settings_clicked, icon_size=50, mouse_cursor="click" if authed else None, bgcolor=ft.Colors.SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
        )
        pull_settings_button = ft.IconButton(
            ft.Icons.SETTINGS_OUTLINED,
            icon_color=ft.Colors.PRIMARY if authed else ft.Colors.ERROR,
            disabled=not authed, on_click=_pull_settings_clicked, icon_size=50, mouse_cursor="click" if authed else None, bgcolor=ft.Colors.SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
        )
        pull_settings_desc = "Pull Story Board settings from cloud, overriding the existing local version." if authed else "Connect to Google Drive first"



        push_on_close_switch = ft.Switch(
            label="Push TO cloud on close", value=self.data.get('sync_with_cloud_on_close', False),
            disabled=not authed, on_change=_push_on_close_changed,
        )
        pull_on_launch_switch = ft.Switch(
            label="Pull FROM cloud on launch", value=self.data.get('sync_with_cloud_on_launch', False),
            disabled=not authed or not self.data.get('sync_with_cloud_on_close', False), on_change=_pull_on_launch_changed,
            tooltip="Requires 'Push TO cloud on close', otherwise unsynced progress would be lost on relaunch",
        )


        content = ft.Column([
            ft.Row([
                ft.Text("Cloud Settings", theme_style=ft.TextThemeStyle.HEADLINE_LARGE, expand=True),
                ft.IconButton(
                    ft.Icons.CLOSE_OUTLINED, on_click=self.close_settings, 
                    scale=1.5, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    mouse_cursor="click", tooltip="Close Settings"
                ) 
            ]),
            ft.Row([
                ft.Text(
                    "Configure your connection to google drive to enable cloud sync. Status: " + ("Connected" if authed else "Not Connected"),
                    theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ft.Container(connect_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4),
            ]),
            
            #ft.Container(height=10),    # Spacer
            ft.Divider(),
            

            ft.Column([
                
                
                ft.Row([
                    ft.Text("Push TO Cloud", expand=True, text_align=ft.TextAlign.CENTER, theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD),
                    ft.Text("Pull FROM Cloud", expand=True, text_align=ft.TextAlign.CENTER, theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                #ft.Divider(),
                ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Container(push_story_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4), 
                            ft.Text(push_story_desc, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Row([
                            ft.Container(push_settings_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4), 
                            ft.Text(push_settings_desc, weight=ft.FontWeight.BOLD),
                            #ft.Text(push_settings_details, italic=True)
                        ]),
                    ], expand=True),
                    ft.VerticalDivider(),
                    ft.Column([
                        ft.Row([
                            ft.Container(pull_story_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4), 
                            ft.Text(pull_story_desc, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Row([
                            ft.Container(pull_settings_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4), 
                            ft.Text(pull_settings_desc, weight=ft.FontWeight.BOLD),
                        ]),
                    ], expand=True)
                ], expand=True, spacing=30),
                #push_on_close_switch,
                #pull_on_launch_switch,
                
            ], scroll=ft.ScrollMode.AUTO, alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER, margin=ft.Margin.only(left=20, top=10, bottom=10), visible=authed),
            ft.Divider(visible=authed),
            ft.Text("Settings that get Synced:", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD, margin=ft.Margin.only(bottom=10, top=10), visible=authed),
            ft.Text(push_settings_details, italic=True, visible=authed)
        ], alignment=ft.MainAxisAlignment.START,  expand=True, spacing=0,)

        return content
    
    
    # Called when someone expands the drop down holding the color scheme options
    def build(self):
        ''' Reloads our settings view with updated data '''

        # Clear any current controls we have
        self.controls.clear()
        
        # Set our menubar
        menubar = MenuBar(self.story)

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
                ft.NavigationRailDestination(
                    icon=ft.Icons.CLOUD_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.CLOUD_ROUNDED, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Cloud", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE), margin=ft.Margin.only(bottom=20))
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

        



