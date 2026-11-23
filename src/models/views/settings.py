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
from models.dataclasses.character_template import default_character_template_data
from models.dataclasses.item_template import default_item_template_data
from models.dataclasses.world_template import default_world_template_data
from models.dataclasses.templates import TEMPLATE_DEFAULTS, get_template
import asyncio
import base64
import flet_shadcn_ui as shad
from flet_color_pickers import ColorPicker
from styles.highlight_button import HighlightButton
from styles.card import Card
 
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
                    'rail_sort_method': "alphabetical",   # Method to sort items in the rail. Defaul lets OS decide, alphabetically, color, creation date
                },

                # Default settings for the newly created widgets. All have a color, but can have additional settings specific to each widget type.
                'widget_defaults': {
                    'manuscript': {
                        'color': "primary",
                        'export_file_type': ".docx"   # Default export file type for plotlines
                    },
                    'canvas': {
                        'color': "primary",
                        'export_file_type': ".png"   # Default export file type for plotlines
                    },
                    'note': {
                        'color': "primary",
                        'card_size': "medium"
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
                        'locked': False,   # If the map is in draw mode or not
                        'background_image_type': "default",   # Type of background image, can be default, custom, etc.
                        'background_color': None,
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
                        'view_mode': "curved",   # If the plot chart is in spider web view or not
                        'export_file_type': ".json"   # Default export file type for plotlines
                    },
                    'comic_preview': {
                        'color': "primary",
                        'preview_direction': "vertical",            # Default direction for comic preview, can be vertical or horizontal
                        'preview_scale': 2,                         # Scale of the images in the preview, 1 = 1:1, 2 = 2:1, etc. 
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
                    'connection_map': {
                        'color': "primary",
                        'view_mode': "curved",   # If the connection map is in straight, zigzag, or curved view
                        'export_file_type': ".json"   # Default export file type for plotlines
                    },
                    'web_view': {
                        'color': "primary",
                    },
                    'kanban': {
                        'color': "primary",
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
            
            # Applies this theme to our page, for both dark and light themes
            self.page.theme.color_scheme_seed = new_color
            self.page.dark_theme.color_scheme_seed = new_color

            # Save the updated settings to the JSON file and update the page
            self.page.update()

        


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

        # Button that changes the theme from dark or light when clicked
        self.light_theme_button = ft.Container(
            content=ft.Icon(ft.Icons.LIGHT_MODE, color=ft.Colors.YELLOW_700), height=100, width=100, border_radius=10, data="light",
            border=ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT) if self.data.get('page', {}).get('theme_mode', "dark") == "dark" else ft.Border.all(2, ft.Colors.PRIMARY), 
            bgcolor=ft.Colors.WHITE, on_click=_toggle_theme, tooltip="Set light mode", ink=True
        )
        self.dark_theme_button = ft.Container(
            content=ft.Icon(ft.Icons.DARK_MODE, color=ft.Colors.WHITE), height=100, width=100, border_radius=10, data="dark",
            border=ft.Border.all(2, ft.Colors.ON_SURFACE_VARIANT) if self.data.get('page', {}).get('theme_mode', "dark") == "light" else ft.Border.all(2, ft.Colors.PRIMARY), 
            bgcolor=ft.Colors.BLACK, on_click=_toggle_theme, tooltip="Set dark mode", ink=True
        )
        # Dropdown so app can change their color scheme
        theme_color_dropdown = shad.Select(
            #label="Theme Color", description="Select the primary color scheme for the app",
            options=[
                shad.SelectOption(
                    value=color, text=name.capitalize()
                ) for name, color in theme_colors.items()
            ],
            on_change=_set_theme_color,
            value=self.data.get('page', {}).get('theme_color', "default"),
        )

        folder_color_dropdown = shad.Select(
            #label="Default Folder Color", description="Select the default color for new folders",
            options=[
                shad.SelectOption(
                    value=color, text=color.capitalize()
                ) for color in colors
            ],
            on_change=_set_default_folder_color,
            value=self.data.get('story', {}).get('default_folder_color', "primary"),
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
                Card("Theme Color", "Select the primary theme color", theme_color_dropdown),      # Change theme primary color dropdown   
                Card("Default Folder Color", "Select the default color for new folders", folder_color_dropdown),      # Change theme primary color dropdown   
            ]),  


            Card(
                "Show Drawing Controls",
                description="Show or hide the drawing controls on the left side of the page. Turn off if you never plan on drawing",
                content=shad.Switch(
                    #label="Show Drawing Controls", #margin=ft.Margin.only(top=10),
                    value=self.data.get('story', {}).get('show_canvas_rail', False), 
                    on_change=lambda e: self.update_data(**{'story': {'show_canvas_rail': e.control.value}}),
                    sublabel="Show or hide the drawing controls on the left side of the page. Turn off if you never plan on drawing",
                ),
            )

        ])

        return content
    
    # Called when app settings category is selected
    def _load_widget_settings(self) -> ft.Container:
        ''' Loads our account settings view '''
                

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
        def set_default_widget_color(e: ft.Event[shad.Select]):
            new_color = e.control.value.lower()
            widget_tag = e.control.data
            self.update_data(**{'widget_defaults': {widget_tag: {'color': new_color}}})
            e.control.color = new_color
            e.control.update()
            

        def update_plotline_division_count(e: ft.Event[shad.Input]):
            if not e.control.value or not e.control.value.isdigit() or int(e.control.value) < 0 or int(e.control.value) > 30:
                e.control.error_text = "Please enter a valid number between 0 and 30"
                e.control.value = str(self.data.get('widget_defaults', {}).get('plotline', {}).get('starting_division_count', 9))
                e.control.update()
                return
            
            e.control.error_text = None
            new_count = int(e.control.value)
            self.update_data(**{'widget_defaults': {'plotline': {'starting_division_count': new_count}}})
            e.control.update()

        def update_plotline_pp_color(e: ft.Event[ft.Dropdown]):
            new_color = e.control.value.lower()
            self.update_data(**{'widget_defaults': {'plotline': {'plot_point_color': new_color}}})
            e.control.color = new_color
            e.control.update()

        async def update_map_bg_image(e: ft.Event[ft.Dropdown]):
            def change_color(e: ft.Event[ft.Event]):
                nonlocal color, new_image_type
                color = e.data
            def save_and_close(e: ft.Event[ft.Control]):
                nonlocal color
                self.update_data(**{'widget_defaults': {'map': {'background_image': None}}})
                self.update_data(**{'widget_defaults': {'map': {'background_color': color}}})
                self.update_data(**{'widget_defaults': {'map': {'background_image_type': "color"}}})
                self.page.pop_dialog()
                
            new_image = e.control.value
            new_image_type = None

            if new_image == "color":
                color = self.data.get('widget_defaults', {}).get('map', {}).get('background_color', ft.Colors.PRIMARY)
                color_picker = ColorPicker(
                    color,
                    on_color_change=change_color, width=512, color_picker_width=152    # Fixed width of shad dialog
                )
                dlg = shad.Dialog(
                    content=color_picker,
                    title="Set Background to a Color",
                    description="This will overwrite its current background image",
                    actions=[
                        shad.Button("Cancel", on_click=lambda: self.page.pop_dialog(), color=ft.Colors.ERROR, size=shad.ButtonSize.SM, variant=shad.ButtonVariant.OUTLINE),
                        shad.Button("Set Color", on_click=save_and_close, color=ft.Colors.PRIMARY, size=shad.ButtonSize.SM, variant=shad.ButtonVariant.OUTLINE),
                    ], 
                    
                )
                self.page.show_dialog(dlg)
                return
            if new_image == "custom_image":   # Wait for user to pick and image if uploading
                new_image = await get_uploaded_map_bg_image()
                new_image_type = "custom_image"
                if not new_image:
                    return
            if not new_image:   # If user canceled the upload, just return
                new_image = self.data.get('widget_defaults', {}).get('map', {}).get('background_image', "map_bg_fantasy_dark.png")
                e.control.value = self.data.get('widget_defaults', {}).get("map", {}).get('background_image', "map_bg_fantasy_dark.png")  # Reset the dropdown to the previous value
                e.control.update()
                return
            self.update_data(**{'widget_defaults': {'map': {'background_image': new_image}}})
            self.update_data(**{'widget_defaults': {'map': {'background_image_type': new_image_type if new_image_type else new_image}}})
            

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
        def set_default_node_color(e: ft.Event[shad.Select]):
            new_color = e.control.value.lower()
            self.update_data(**{'widget_defaults': {'plot_chart': {'node_color': new_color}}})
            e.control.color = new_color
            e.control.update()

        def toggle_comic_preview_direction(e: ft.Event[ft.Button]):
            new_direction = "horizontal" if self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_direction', "vertical") == "vertical" else "vertical"
            self.update_data(**{'widget_defaults': {'comic_preview': {'preview_direction': new_direction}}})
            e.control.icon = ft.Icons.SWAP_VERT if new_direction == "vertical" else ft.Icons.SWAP_HORIZ
            e.control.update()

        def set_widget_view_mode(e: ft.Event[shad.Select]):
            new_value = e.control.value
            widget_tag = e.control.data or "plot_chart"
            self.data['widget_defaults'][widget_tag]['view_mode'] = new_value
            self.update_data(**{'widget_defaults': {widget_tag: {'view_mode': new_value}}})

        def update_note_card_size(e: ft.Event[shad.Select]):
            new_size = e.control.value.lower()
            self.update_data(**{'widget_defaults': {'note': {'card_size': new_size}}})
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

            #ft.Container(height=10),    # Spacer
            

            ft.Column([
                ft.Text("Default Colors", theme_style=ft.TextThemeStyle.TITLE_LARGE, margin=ft.Margin.only(bottom=10)),
                ft.Row([
                
                Card(content=shad.Select(
                        label="Manuscript", data="manuscript",
                        options=[
                            shad.SelectOption(
                                value=color, text=color.capitalize()
                            ) for color in colors
                        ],
                        on_change=set_default_widget_color,
                        value=self.data.get('widget_defaults', {}).get('manuscript', {}).get('color', "primary").capitalize(),
                    ),
                ),

                Card(content=shad.Select(
                    label="Character", data="character",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('character', {}).get('color', "primary").capitalize(),
                ),
                ),

                Card(content=shad.Select(
                    label="Note", data="note",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('note', {}).get('color', "primary").capitalize(),
                ),
                ),
                Card(content=shad.Select(
                    label="Plotline", data="plotline",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('plotline', {}).get('color', "primary").capitalize(),
                ),
                ),
                Card(content=shad.Select(
                    label="Plot chart", data="plot_chart",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('plot_chart', {}).get('color', "primary").capitalize(),
                ),
                ),
                Card(content=shad.Select(
                    label="Item", data="item",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('item', {}).get('color', "primary").capitalize(),
                ),
                ),
                Card(content=shad.Select(
                    label="World", data="world",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('world', {}).get('color', "primary").capitalize(),
                ),
                ),
                Card(content=shad.Select(
                    label="Map", data="map",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('map', {}).get('color', "primary").capitalize(),
                ),
                ),
                Card(content=shad.Select(
                    label="Radar Chart", data="chart",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('chart', {}).get('color', "primary").capitalize(),
                ),
                ),
                Card(content=shad.Select(
                    label="Connection Map", data="connection_map",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('connection_map', {}).get('color', "primary").capitalize(),
                ),
                ),

                Card(content=shad.Select(
                    label="Canvas", data="canvas",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('canvas', {}).get('color', "primary").capitalize(),
                ),
                ),
                Card(content=shad.Select(
                    label="Canvas Board", data="canvas_board",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('canvas_board', {}).get('color', "primary").capitalize(),
                ),
                ),

                Card(content=shad.Select(
                    label="Comic Preview", data="comic_preview",
                    options=[
                        shad.SelectOption(
                            value=color, text=color.capitalize()
                        ) for color in colors
                    ],
                    on_change=set_default_widget_color,
                    value=self.data.get('widget_defaults', {}).get('comic_preview', {}).get('color', "primary").capitalize(),
                ),
                ),
            ], wrap=True, max_width=1000, spacing=20, run_spacing=20),

            ft.Divider(),
            ft.Text("Widget Defaults", theme_style=ft.TextThemeStyle.TITLE_LARGE, margin=ft.Margin.only(bottom=10)),

            ft.Row([      
                Card(
                    "Comic Preview",
                    "Default settings for new comic previews.",
                    content=ft.Column([
                        
                        shad.Select(
                            label="Preview Scale",
                            description="Scale of the preview display for new comic previews.",
                            options=[
                                shad.SelectOption(
                                    value=str(i), text=str(i)
                                ) for i in range(1, 6)
                            ],
                            on_change=lambda e: self.update_data(**{'widget_defaults': {'comic_preview': {'preview_scale': int(e.control.value)}}}),
                            value=str(self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_scale', 1)),
                        ),

                        shad.Select(
                            label="Preview Direction",
                            description="Direction of the preview display for new comic previews.",
                            options=[
                                shad.SelectOption(
                                    value="vertical", text="Vertical"
                                ),
                                shad.SelectOption(
                                    value="horizontal", text="Horizontal"
                                )
                            ],
                            on_change=lambda e: self.update_data(**{'widget_defaults': {'comic_preview': {'preview_direction': e.control.value}}}),
                            value=self.data.get('widget_defaults', {}).get('comic_preview', {}).get('preview_direction', "vertical"),
                        ),

                        shad.Select(
                            label="Image Quality",
                            description="Quality of the images for new comic previews.",
                            options=[
                                shad.SelectOption(
                                    value="low", text="Low"
                                ),
                                shad.SelectOption(
                                    value="medium", text="Medium"
                                ),
                                shad.SelectOption(
                                    value="high", text="High"
                                )
                            ],
                            on_change=lambda e: self.update_data(**{'widget_defaults': {'comic_preview': {'image_quality': e.control.value}}}),
                            value=self.data.get('widget_defaults', {}).get('comic_preview', {}).get('image_quality', "medium"),
                        ),

                        shad.Switch(
                            label="Anti-Aliasing",
                            sublabel="If anti aliasing should be used when rendering images for new comic previews.",
                            value=self.data.get('widget_defaults', {}).get('comic_preview', {}).get('anti_aliasing', True),
                            on_change=lambda e: self.update_data(**{'widget_defaults': {'comic_preview': {'anti_aliasing': e.control.value}}})
                        )
                        
                    ], margin=ft.Margin.only(top=10), spacing=20),
                ),   

                Card(
                    "Plotline",
                    "Default settings for new plotlines.",
                    content=ft.Column([
                        shad.Input(    # Change the default number of divisions for new plotlines
                            label="Division Count",
                            value=str(self.data.get('widget_defaults', {}).get('plotline', {}).get('starting_division_count', 4)),
                            description="The starting number of divisions for new plotlines.",
                            on_blur=update_plotline_division_count,
                            width=350, keyboard_type=ft.KeyboardType.NUMBER,
                        ),
                        shad.Switch(
                            value=self.data.get('widget_defaults', {}).get('plotline', {}).get('show_division_labels', True),
                            label="Show Labels",
                            sublabel="If the time label and division numbers are shown for new plotlines.",
                            on_change=lambda e: self.update_data(**{'widget_defaults': {'plotline': {'show_division_labels': e.control.value}}}),
                        ),
                    ], margin=ft.Margin.only(top=10), spacing=20),
                ), 

                Card(
                    "Map",
                    "Default settings for new maps.",
                    content=ft.Column([
                        # Set defualt background image for new maps
                        shad.Select(
                            label="Default Background Image",
                            value=self.data.get('widget_defaults', {}).get("map", {}).get('background_image_type', "map_bg_fantasy_dark.png"),
                            on_change=update_map_bg_image,
                            options=[
                                shad.SelectOption(value="map_bg_fantasy_dark.png", text="Dark Fantasy"),
                                shad.SelectOption(value="map_bg_fantasy_light.png", text="Light Fantasy"),
                                shad.SelectOption(value="map_bg_scifi.png", text="Sci-Fi"),
                                shad.SelectOption(value="map_bg_space.jpg", text="Space"),
                                shad.SelectOption(value="custom_image", text="Custom Image"),
                                shad.SelectOption(value="color", text="Color"),
                            ],
                        ),
                        # Map draw mode
                        shad.Switch(
                            value=self.data.get('widget_defaults', {}).get('map', {}).get('locked', False),
                            label="Locked", sublabel="If new maps start locked in order to prevent drawing.",
                            on_change=lambda e: self.update_data(**{'widget_defaults': {'map': {'locked': e.control.value}}}),
                            visible=False,
                        ),
                    ], margin=ft.Margin.only(top=10), spacing=20),
                ),
         
                Card(
                    "Plot Chart",
                    "Default settings for new plot charts.",
                    content=shad.Select(
                        label="View Mode",
                        value=self.data.get('widget_defaults', {}).get("plot_chart", {}).get('view_mode', "curved"),
                        on_change=set_widget_view_mode,
                        data="plot_chart",
                        options=[
                            shad.SelectOption(value="curved", text="Curved"),
                            shad.SelectOption(value="zigzag", text="ZigZag"),
                            shad.SelectOption(value="straight", text="Straight"),
                        ],
                    ),
                ),
                Card(
                    "Connection Map",
                    "Default settings for new connection maps.",
                    content=shad.Select(
                        label="View Mode",
                        value=self.data.get('widget_defaults', {}).get("connection_map", {}).get('view_mode', "curved"),
                        on_change=set_widget_view_mode,
                        data="connection_map",
                        options=[
                            shad.SelectOption(value="curved", text="Curved"),
                            shad.SelectOption(value="zigzag", text="ZigZag"),
                            shad.SelectOption(value="straight", text="Straight"),
                        ],
                    ),
                ),
                Card(
                    "Note",
                    "Default settings for new notes.",
                    content=ft.Column([
                        shad.Select(
                            label="Default Note Card Size",
                            value=self.data.get('widget_defaults', {}).get("note", {}).get('card_size', "medium"),
                            on_change=update_note_card_size,
                            options=[
                                shad.SelectOption(value="small", text="Small"),
                                shad.SelectOption(value="medium", text="Medium"),
                                shad.SelectOption(value="large", text="Large"),
                            ],
                        ),
                    ], margin=ft.Margin.only(top=10), spacing=20),
                ),

            ], wrap=True, vertical_alignment=ft.CrossAxisAlignment.START, spacing=20, run_spacing=20),
            ], scroll=ft.ScrollMode.AUTO, margin=ft.Margin.only(left=20), expand=True)
            
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
                #self.page.run_task(editor.content.scroll_to, -1)    # Scroll to bottom to maintain position


            def move(values, old_index, new_index):
                if isinstance(values, dict):
                    entries = list(values.items())
                    entries.insert(new_index, entries.pop(old_index))
                    values.clear()
                    values.update(entries)
                else:
                    values.insert(new_index, values.pop(old_index))
                redraw()

            def add_input(label, names, add, extra_menu_items=None, use_button=False):
                def cancel(e):
                    field.visible = False
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

                field = ft.TextField(
                    label=f"New {label}", dense=True, #expand=True,
                    capitalization=ft.TextCapitalization.WORDS, bgcolor=ft.Colors.SURFACE,
                    on_blur=cancel, on_submit=submit, visible=False, autofocus=True,
                    suffix_icon=ft.IconButton(
                        ft.Icons.ADD_OUTLINED, ft.Colors.PRIMARY,
                        on_click=submit,
                        mouse_cursor="click",
                    ),
                )

                async def show(e):
                    field.visible = True
                    editor.update()
                    await field.focus()

                
                
                if use_button:
                    action_control = ft.Container(
                        ft.Button(
                            f"New {label}",
                            icon_color=ft.Colors.PRIMARY,
                            on_click=show, bgcolor=ft.Colors.SURFACE,
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4), text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=20)),
                        ),
                        border_radius=4,
                    )
                else:
                    menu_items = [
                        shad.MenuItem(f"New {label}", ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, 20), on_click=show),
                    ]
                    if extra_menu_items:
                        menu_items.extend(extra_menu_items)
                    action_control = shad.ContextMenu(
                        HighlightButton(ft.Icon(ft.Icons.MORE_VERT, ft.Colors.PRIMARY), use_padding=True, is_round=True),
                        menu_items,
                        open_on_tap=True,
                    )
                return ft.Row([action_control, field], tight=True, spacing=0, expand=True)

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

            def field_input(fields, section_menu_items=None, use_button=False):
                def names():
                    return fields if isinstance(fields, dict) else [field["title"] for field in fields]

                def add(name):
                    if isinstance(fields, dict):
                        fields[name] = ""
                    else:
                        fields.append({"title": name, "content": ""})

                return add_input("Field", names, add, section_menu_items, use_button=use_button)

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
                    ft.TextButton("Reset to Default", on_click=reset),
                ]),
                ft.Divider(),
            ]
            if is_item:
                controls.append(ft.Container(
                    content=field_list(template),
                    border_radius=ft.BorderRadius.all(4),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    margin=ft.Margin.all(2),
                    padding=ft.Padding.all(10),
                ))
                controls.append(field_input(template, use_button=True))
            else:
                for index, (name, fields) in enumerate(template.items()):
                    def delete_section(e, name=name):
                        del template[name]
                        redraw()

                    section_menu_items = [
                        shad.MenuItem(
                            "Move Up",
                            ft.Icon(ft.Icons.ARROW_UPWARD, ft.Colors.PRIMARY, 20),
                            on_click=lambda e, index=index: move(template, index, index - 1),
                            disabled=index == 0,
                        ),
                        shad.MenuItem(
                            "Move Down",
                            ft.Icon(ft.Icons.ARROW_DOWNWARD, ft.Colors.PRIMARY, 20),
                            on_click=lambda e, index=index: move(template, index, index + 1),
                            disabled=index == len(template) - 1,
                        ),
                        shad.Separator(ft.Margin.symmetric(vertical=4)),
                        shad.MenuItem(
                            "Delete Section",
                            ft.Icon(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, 20),
                            on_click=delete_section,
                        ),
                    ]

                    controls.append(ft.Container(
                        border_radius=ft.BorderRadius.all(4),
                        #border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        margin=ft.Margin.all(2),
                        
                        padding=ft.Padding.all(10),
                        content=ft.Column([
                            ft.Row([
                                ft.Text(name, theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                        weight=ft.FontWeight.BOLD,),
                                field_input(fields, section_menu_items),
                                ft.Container(expand=True),
                            ]),
                            field_list(fields),
                        ], tight=True, spacing=0),
                    ))
                controls.append(add_input(
                    "Section", lambda: template,
                    lambda name: template.update({name: {}}),
                    use_button=True,
                ))

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
                "Edit your character, world, and item template",
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
                #ft.Text(f"Resources about StoryBoard!", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(
                    ft.Text("Click here to Run Tutorial", color=ft.Colors.PRIMARY, theme_style=ft.TextThemeStyle.BODY_MEDIUM, weight=ft.FontWeight.W_500), 
                    on_click=_run_tutorial,
                ),
                ft.Container(
                    ft.IconButton(
                        ft.Icons.SCHOOL_OUTLINED,
                        icon_color=ft.Colors.PRIMARY,
                        on_click=_run_tutorial,  mouse_cursor="click", bgcolor=ft.Colors.SURFACE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                        tooltip="Click here to run the tutorial"
                    ),
                    border_radius=4, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                ),
                ft.Text("Join our", theme_style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT, ),
                ft.Container(
                    ft.Text("Discord", color=ft.Colors.PRIMARY, theme_style=ft.TextThemeStyle.BODY_MEDIUM, weight=ft.FontWeight.W_500),
                    on_click=_discord_clicked,
                ),
                ft.Container(
                    ft.IconButton(
                        ft.Icons.DISCORD,
                        icon_color=ft.Colors.PRIMARY,
                        on_click=_discord_clicked,  mouse_cursor="click", bgcolor=ft.Colors.SURFACE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                        tooltip="Click here to join our Discord"
                    ),
                    border_radius=4, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                ),
                ft.Text("to be part of our community and see upcoming features!", theme_style=ft.TextThemeStyle.BODY_MEDIUM,),
            ], spacing=8, wrap=True), # Link
            
            


            ft.Divider(),
            ft.Container(height=10),    # Spacer


            #ft.Text("Widgets", theme_style=ft.TextThemeStyle.TITLE_LARGE, margin=ft.Margin.only(left=20)),

            ft.Column([
                
                Card(
                    "Manuscript",
                    "The main widget for creating all novel-based stories. Similar to Microsoft Word or Google Docs, use the manuscript widget as a fully built text editor",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Character",
                    "A widget for all the characters in your story. Flesh out your characters physical look, personality, origin, arcs, etc!",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Note",
                    "A widget for all your ideas, themes, research, etc. Don't let the magic fade, save it here!",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Plotline",
                    "A widget for visualizing the progression of your story. Create multiple plotlines for arcs, sub arcs, plot points, or regression & multi-timeline stories.",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Plot Chart",
                    "A widget for fleshing out plotlines in your story in a node to connection based format.",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Item",
                    "A widget for all items, weapons, armor, and MacGuffins in your story!",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "World",
                    "A widget to describe your world(s) for your story. Plan out the lore, history, governments, factions, power systems, etc. You can create templates for your worlds, and connect them to existing maps!",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Map",
                    "A widget to visualize locations in your story. Create a map for worlds, countries, cities, dungeons, etc. Connect locations on your map to other maps for a connected feel to your story!",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Chart",
                    "A widget for visualizing power systems and other ideas in a chart format. Supports manipulation of bar and radar charts, with implicit animations!",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Connection Map",
                    "A widget to visualize how your characters connect to each other within a story. See family trees, friends, enemies, guilds, etc.",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Canvas",
                    "The main widget for creating all comic-based stories. This widget allows illustrators to watch their ideas come to life on the Canvas. Create your own drawing masterpiece or upload exported files from another drawing app!",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Canvas Board",
                    "A widget for planning out comic-based chapters for your story. Describe and sketch out your ideas for all you panels ahead of time. Connect them to an existing canvas in your story to see how progress is coming along!",
                    width=ft.context.page.width * 0.7
                ),
                Card(
                    "Comic Preview",
                    "A widget for comic-based stories for visualizing all your canvases (and external drawings you want to see), in a nice, scrollable vertical or horizontal format. See how your chapter comes together visually before you present it to the world!",
                    width=ft.context.page.width * 0.7
                ),
            ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True, alignment=ft.MainAxisAlignment.START,),

        ], alignment=ft.MainAxisAlignment.START, expand=True)

        return content

    def _load_cloud_settings(self):
        from models.app import app
        from utils import google_drive

        

        async def _connect_clicked(e=None):
            if app.is_cloud_authenticated:
                try:
                    await asyncio.to_thread(google_drive.disconnect)
                except (OSError, google_drive.SecureStorageError) as ex:
                    self.page.show_dialog(shad.Toast(google_drive.describe_error(ex)))
                    return
                app.is_cloud_authenticated = False
                self.update_data(**{'sync_with_cloud_on_close': False, 'sync_with_cloud_on_launch': False})
                await self.save_file()
                self._settings_category_changed()
                self.page.show_dialog(shad.Toast("Disconnected from Google Drive."))
                return
            try:
                self.page.show_dialog(shad.Toast("Opening browser to connect your Google account..."))
                await asyncio.to_thread(google_drive.authenticate)
                app.is_cloud_authenticated = True
                self._settings_category_changed()
                self.page.show_dialog(shad.Toast("Google account connected."))
            except Exception as ex:
                self.page.show_dialog(shad.Toast(google_drive.describe_error(ex)))

        async def _run_with_route(route: str, work):
            ''' Shows the saving/pulling view while work() runs, then returns to settings with a result shad.Toast '''
            page = self.page    # Captured because this view unmounts while we are away
            await page.push_route(route)
            try:
                message = await work()
            except Exception as ex:
                message = google_drive.describe_error(ex)
            await page.push_route("/settings")
            page.show_dialog(shad.Toast(message))

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
                "This replaces your local settings and character, world, and item templates with the ones in your Google Drive. Window settings are kept.",
                _do_pull_settings,
            )

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
            icon_color=ft.Colors.PRIMARY if has_story else ft.Colors.OUTLINE_VARIANT,
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
            icon_color=ft.Colors.PRIMARY if has_story else ft.Colors.OUTLINE_VARIANT,
            disabled=not has_story,
            on_click=_pull_story_clicked, icon_size=50, mouse_cursor="click" if has_story else None, bgcolor=ft.Colors.SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
        )
        pull_story_desc = (
            f"Pull current story: {story_title} from cloud, overriding the existing local version." if has_story
            else ("Open a story to pull it" if authed else "Connect to Google Drive first")
        )

        push_settings_desc = "Push StoryBoard settings to cloud. These settings include: "

        push_settings_button = ft.IconButton(
            ft.Icons.SETTINGS_OUTLINED,
            icon_color=ft.Colors.PRIMARY if authed else ft.Colors.OUTLINE_VARIANT,
            disabled=not authed, 
            on_click=_push_settings_clicked, icon_size=50, mouse_cursor="click" if authed else None, bgcolor=ft.Colors.SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
        )
        pull_settings_button = ft.IconButton(
            ft.Icons.SETTINGS_OUTLINED,
            icon_color=ft.Colors.PRIMARY if authed else ft.Colors.OUTLINE_VARIANT,
            disabled=not authed, on_click=_pull_settings_clicked, icon_size=50, mouse_cursor="click" if authed else None, bgcolor=ft.Colors.SURFACE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
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
            

            ft.Column(
                [

                    Card(
                        "Push To Cloud",
                        "Push your local settings from this device to the cloud.",
                        ft.Column([
                            ft.Row([
                                ft.Container(push_story_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4), 
                                ft.Text(f"Push Story '{self.story.data.get('title', "") if self.story else "None"}'")
                            ], tight=True),
                            ft.Row([
                                ft.Container(push_settings_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4), 
                                ft.Text(f"Push Settings")
                            ], tight=True),
                        ], margin=ft.Margin.only(top=10)),
                        width=400
                    ),
                    Card(
                        "Pull From Cloud",
                        "Pull your settings from the cloud to this device.",
                        ft.Column([
                            ft.Row([
                                ft.Container(pull_story_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4), 
                                ft.Text(f"Pull Story '{self.story.data.get('title', "") if self.story else "None"}'")
                            ], tight=True),
                            ft.Row([
                                ft.Container(pull_settings_button, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT), border_radius=4), 
                                ft.Text(f"Pull Settings")
                            ], tight=True),
                        ], margin=ft.Margin.only(top=10)),
                        width=400
                    ),
                    #ft.Divider(),
                    Card(
                        "Settings that get Synced",
                        f"- Appearance, Widget, and Template Settings\n- Paint Brushes and Saved Font configurations\n",
                        width=400
                    )
                
                ], 
                scroll=ft.ScrollMode.AUTO, spacing=20,
                visible=authed, 
                alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.START, margin=ft.Margin.only(top=10, bottom=10)
            ),
            
        ], alignment=ft.MainAxisAlignment.START, expand=True, spacing=0)

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
                    label=ft.Container(ft.Text("Appearance", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE)),
                    padding=ft.Padding.only(top=20)
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.NOW_WIDGETS_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.NOW_WIDGETS_ROUNDED, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Widgets", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE)),
                    padding=ft.Padding.only(top=20)
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.FILE_PRESENT_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.FILE_PRESENT, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Templates", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE)),
                    padding=ft.Padding.only(top=20)
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.INFO_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.INFO_ROUNDED, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Resources", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE)),
                    padding=ft.Padding.only(top=20)
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.CLOUD_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.CLOUD_ROUNDED, color=ft.Colors.PRIMARY),
                    label=ft.Container(ft.Text("Cloud", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE)),
                    padding=ft.Padding.only(top=20)
                ),
            ],
        )

        nav_rail_container = ft.Container(
            bgcolor=ft.Colors.SURFACE,
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

        


# Standard styling for most text fields we use
@ft.control
class SettingsTextField(ft.TextField):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Default styles
        self.label_style = ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY)
        self.dense = True
        self.text_style=ft.TextStyle(size=14)
        self.multiline=False
        self.capitalization=ft.TextCapitalization.SENTENCES
        self.bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4)
        #self.margin=ft.Margin.only(left=20)
        #self.width=200
