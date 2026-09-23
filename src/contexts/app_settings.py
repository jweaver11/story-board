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
from ui.menu_bar import MenuBar
from styles.snack_bar import SnackBar
from models.dataclasses.character_template import default_character_template_data_dict
from styles.text_fields import TextField
from models.dataclasses.world_template import default_world_template_data_dict
import asyncio
from styles.text_fields import SettingsTextField
from dataclasses import dataclass, field, asdict
import base64
from contexts.contexts import AppContext, AppSettingsContext

@ft.observable
@dataclass
class AppSettings:

    is_first_launch: bool = True    # Checks if the app has been launched yet in order to greet the user

    # Page settings
    route: str = "stories/29ec449f-b5dd-46ec-bf63-db1e88627854"
    window_maximized: bool = True
    window_width: int = 0
    window_height: int = 0
    theme_mode: str = "dark"
    theme_color: str = "#A0CAFD"

    # Story settings
    show_drawing_controls: bool = True
    tree_view_rail_width: int = 250

    # Widget and folder Colors
    new_folder_color: str = "primary"
    new_manuscript_color: str = "primary"
    new_canvas_color: str = "primary"
    new_note_color: str = "primary"
    new_character_color: str = "primary"
    new_plotline_color: str = "primary"
    new_canvas_board_color: str = "primary"
    new_map_color: str = "primary"
    new_world_color: str = "primary"
    new_item_color: str = "primary"
    new_plot_chart_color: str = "primary"
    new_comic_preview_color: str = "primary"
    new_chart_color: str = "primary"
    new_character_relationship_map_color: str = "primary"

    # Widget export settings
    manuscript_export_file_type: str = ".docx"
    canvas_export_file_type: str = ".png"
    plotline_export_file_type: str = ".json"
    map_export_file_type: str = ".json"
    plot_chart_export_file_type: str = ".json"

    # Other widget settings
    canvas_use_custom_cursor: bool = False  # If the canvas uses a standard 
    plotline_starting_division_count: int = 9
    plotline_plot_point_color: str = "white"
    canvas_board_sketch_width: int = 300
    canvas_board_sketch_height: int = 300
    map_draw_mode: bool = False
    map_background_image: str = "map_bg_fantasy_dark.png"
    plot_chart_node_color: str = "white"
    plot_chart_spider_web_view: bool = False
    comic_preview_direction: str = "vertical"
    comic_preview_background_color: str = "#000000"
    comic_preview_spacing: int = 0
    comic_preview_scale: int = 2
    comic_preview_filter_quality: str = "medium"
    comic_preview_anti_aliasing: bool = True
    # Bar chart settings
    chart_show_labels: bool = True
    chart_rod_shape: str = "rounded"
    chart_rod_width: int = 30
    chart_rod_spacing: int = 4
    chart_stack_rods: bool = False
    chart_show_horizontal_grid_lines: bool = True
    chart_show_vertical_grid_lines: bool = False
    # Radar chart settings
    chart_make_chart_round: bool = True
    chart_tick_count: int = 2
    chart_show_tick_labels: bool = False
    chart_rotate_node_titles: bool = True

    # TODO: Finish rest of dict to dataclass
    # Create dataclass for contexts
    # Make contexts folder to store the dif contexts
    # Make sure sub dicts in dataclasses are set as additional dataclases

    #character_templates: dict = {}
    #world_templates: dict = {}
            
        
        

    
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

        self.data = {**self.data}

    
    # Called whenever there are changes in our data
    async def save_file(self):
        ''' Saves our current data to the json file '''

        try:
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            # Save the data to the file (creates file if doesnt exist)
            with open(SETTINGS_FILE_PATH, "w", encoding='utf-8') as f:   
                json.dump(asdict(self), f, indent=4)   # asdict() strips observable bookkeeping, unlike self.__dict__
        
        except Exception as e:
            print(f"Error saving settings to {SETTINGS_FILE_PATH}: {e}")

    async def close_settings(self, e=None):
        ''' Closes the settings view and returns to the story or home view '''
        return
        await self.save_file()
        #await self.page.push_route(self.story.route if self.story is not None else "/")

    async def save_story(self, e=None):
        ''' Called when the page is closed. Saves any dirty changes '''
        return
        await self.save_file()
        return
        if self.story is not None:
            for widget in self.story.widgets.values():
                await widget.save_file()
            await self.story.save_file()
        await self.save_file()
        
    def create_character_template(self, template_name: str, data: dict):
        ''' Creates a new character template with the given name '''
        from utils.safe_string_checker import return_safe_name

        safe_key = return_safe_name(template_name)

        self.data['character_templates'][safe_key] = {
            'title': template_name,
            'template_data': data,
        }
        self.update_data(**{'character_templates': self.data['character_templates']})
        

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