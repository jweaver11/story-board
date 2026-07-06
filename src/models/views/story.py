''' 
Master Story class that contains data and methods for the entire story 
Our story is an extended ft.View, meaning new routes can display the story object directly
The Story object creates widgets (characters, documents, notes, etc.) objects that are stored inside of itself.
Stories contain metadata, ui elements, and all the widgets, as well as methods to create new widgets only
'''

import flet as ft
import os
import shutil
import json
from constants import data_paths
from styles.snack_bar import SnackBar
from utils.safe_string_checker import return_safe_name
import asyncio


 
class Story(ft.View):

    # Constructor.
    def __init__(
        self, 
        title: str,             # Title of our story
        page: ft.Page,          # Page reference for updating UI elements
        data: dict=None,        # Data to load our story with (if any)
        type: str=None          # Type of story (novel, comic, etc.)
    ):
        
        # Parent constructor
        super().__init__(
            route=return_safe_name(f"/{title}_story"),    # Sets our route for our new story
            padding=ft.Padding.all(0),      # No padding for the page
            spacing=0,                                                      # No spacing between menubar and rest of page
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
        )  

        self.title = title              # Gives our story a title when its created
        self.data = data                # Sets our data (if any) passed in. New stories just have none
        self.type = type                # Type of story, novel or comic. Affects how templates for creating new content will work

        # Verifies this object has the required data fields, and creates them if not
        if data is None:
            self.data = {
                'title': self.title,
                'directory_path': os.path.join(data_paths.stories_directory_path, return_safe_name(f"/{title}_story")),
                'tag': "story",
                'selected_rail': "content",
                'workspace_selected_index': 0,   # Index of the selected widget in the main pin, used for switching between tabs in the main pin
                'content_directory_path': os.path.join(data_paths.stories_directory_path, return_safe_name(f"/{title}_story"), "content"),
                
                'created_at': str(),
                'last_modified': str(),

                # Sort methods for our specialized rails
                'character_rail_sort_method': "Index",
                'character_rail_sort_direction': "Ascending",

                'plotline_rail_sort_method': "Index",
                'plotline_rail_sort_direction': "Ascending",

                'world_building_rail_sort_method': "Index",
                'world_building_rail_sort_direction': "Ascending",
                
                # Dict of all our categories INSIDE of basic story structure (content, characters, plotlines)
                'folders': {
                    'path': {                   # Path to the category folder (used as the key, since all will be unique)
                        'name': str(),            # Name of category just in case
                        'color': str(),           # Color of that folder
                        'is_expanded': True     # Whether this folder is expanded in the tree view
                    }
                },            
            }
        

        # Variables to store our mouse position for opening menus
        self.mouse_x: int = 0
        self.mouse_y: int = 0

        # State that we are not initialized yet, which will be changed at the end of startup method
        self.is_initialized = False
            
        # Declare our UI elements before we create them later. They are stored as objects so we can reload them when needed
        self.menubar: ft.Container     # Menu bar at top of page
        self.workspaces_rail: ft.Container      # Rail on left side showing our 6 workspaces
        self.active_rail: ft.Container    # Rail showing whichever workspace is selected
        self.workspace: ft.Container       # Main workspace area where our pins display our widgets

        self.menu: ft.Container         # Container that sits in the overlay and gets menu options passed into it
        self.outside_menu_detector: ft.GestureDetector      # Sets under the menu to handle closing and opening the menu

        # Block the app from any interactions during rebuilds
        self.blocker = ft.Container(
            ft.Row([ft.ProgressRing(width=100, height=100)], alignment=ft.MainAxisAlignment.CENTER), 
            expand=True, visible=False, blur=5, left=0, right=0, top=0, bottom=0
        )
        
        # Store all our widgets above in a master list for easier rendering in the UI
        self.widgets: dict = {} 

          
    # Isolates stories from page.update calls. Needed for keeping performance when opening menus
    def is_isolated(self): 
        return True
    
    # Updates data for this widget and marks it as dirty for the next file save
    def update_data(self, **kwargs):
        
        # Allow updating of nested dicts without overriding the entire dict
        def _merge_data(target: dict, updates: dict):
            for key, value in updates.items():
                current_value = target.get(key)
                if isinstance(current_value, dict) and isinstance(value, dict):
                    _merge_data(current_value, value)
                else:
                    target[key] = value

        _merge_data(self.data, kwargs)  # Merge the new data into the existing data

        self.page.run_task(self.save_file)  # Save the updated data to the file

    # Called whenever there are changes in our data that need to be saved
    async def save_file(self):
        ''' Saves the data of our story to its JSON File, and all its folders as well '''

        #print("Saved story to file: ", self.title)
        self.data['directory_path'] = os.path.join(data_paths.stories_directory_path, self.route)   # Make sure our directory path is updated
        file_path = os.path.join(self.data['directory_path'], f"{self.route}.json") # Make sure our file path is updated

        try:

            # Create the directory if it doesn't exist. Catches errors from users deleting folders
            os.makedirs(self.data['directory_path'], exist_ok=True)
            
            # Save the data to the file (creates file if doesnt exist)
            with open(file_path, "w", encoding='utf-8') as f:   
                json.dump(self.data, f, indent=4)
        
        # Handle errors
        except Exception as e:
            self.page.show_dialog(SnackBar(f"Error saving story data: {e}"))

    # Get widget object by its unique ID.
    def get_widget_by_id(self, id: str) -> ft.Control:
        return self.widgets.get(id, None)

    # Called when a new folder/category is created.
    async def create_folder(self, directory_path: str, name: str):
        ''' Creates a new category inside of our story structure for content organization '''
        from models.app import app

        try:

            # Clean up name
            name = name.capitalize()    # Capitalize first letter
            name = name.rstrip()        # Remove trailing spaces

            # Create the full folder path
            folder_path = os.path.join(directory_path, name)

            # Make the folder in our storage if it doesn't already exist
            os.makedirs(folder_path, exist_ok=True) 

            # Add this folder to our folders data so we can save stuff like colors
            self.data['folders'].update({folder_path: {'name': name, 'color': app.settings.data.get('default_category_color', "primary"), 'is_expanded': True}})
            self.update_data(**{'folders': self.data['folders']})

            self.active_rail.reload_rail()

        # Handle errors
        except Exception as e:
            print(f"Error creating folder: {e}")
        
    # Called when deleting a folder/category from our story
    def delete_folder(self, full_path: str):
        ''' Deletes a category from our story structure '''

        try:
            # Normalize once for path-boundary prefix matching
            full_norm = os.path.normcase(os.path.normpath(full_path))

            # Delete the folder from storage
            shutil.rmtree(full_path)


            # Delete any widgets that were in this folder or its sub-folders.
            # Iterate a copy so removing items mid-loop doesn't skip entries.
            for widget_id, widget in list(self.widgets.items()):
                widget_dir = widget.data.get('directory_path')
                if not widget_dir:
                    continue

                widget_dir_norm = os.path.normcase(os.path.normpath(widget_dir))
                if widget_dir_norm == full_norm or widget_dir_norm.startswith(full_norm + os.sep):
                    self.widgets.pop(widget_id, None)            

            # Remove this folder and every sub-folder from story data
            for folder_path in list(self.data['folders'].keys()):
                folder_norm = os.path.normcase(os.path.normpath(folder_path))
                if folder_norm == full_norm or folder_norm.startswith(full_norm + os.sep):
                    self.data['folders'].pop(folder_path, None)

            # Save AFTER all data has been cleaned up so nothing orphaned persists
            self.update_data(**{'folders': self.data['folders']})   

            #self.blocker.visible = True
            #self.blocker.update()
            #self.page.run_task(asyncio.sleep, 0)

            self.active_rail.reload_rail()
            self.workspace.reload_workspace()
            self.close_menu_instant()
            #self.blocker.visible = False
            #self.blocker.update()

        # Handle errors
        except Exception as e:
            print(f"Error deleting folder: {e}")

    # Called when changing folder metadata, like color or is expanded or not
    async def change_folder_data(self, full_path: str, key: str, value):
        ''' Changes our folder metadata inside of our story data '''
        #print("Changing folder data:", full_path, key, value)

        try:
            # Check if the folder exists in our data
            if full_path in self.data.get('folders', {}):
                self.data['folders'][full_path][key] = value
                self.update_data(**{'folders': self.data['folders']})
                #print("Changed folder data:", full_path, key, value)
            else:
                print(f"Folder {full_path} not found in story data.")

        # Handle errors
        except Exception as e:
            print(f"Error changing folder data: {e}")

    def rename_folder(self, old_path: str, new_path: str):
        ''' Renames the folder/category in our story structure '''

        # Does the actual renaming
        os.rename(old_path, new_path)

        # Normalize once for path-boundary prefix matching (avoids matching 'chapters_extra' when looking for 'chapters')
        old_norm = os.path.normcase(os.path.normpath(old_path))

        # Go through each widget and update its directory path if it was in the renamed folder
        for widget in self.widgets.values():
            widget_dir_norm = os.path.normcase(os.path.normpath(widget.data.get('directory_path')))
            if widget_dir_norm == old_norm or widget_dir_norm.startswith(old_norm + os.sep):
                # Compute the new directory using relpath so casing differences don't break the slice
                relative = os.path.relpath(widget.data.get('directory_path'), old_path)
                widget.update_data(**{'directory_path': new_path if relative == '.' else os.path.join(new_path, relative)})

        # Update sub-folder keys BEFORE renaming the top-level key so we never match the already-renamed entry
        for folder in self.data['folders'].copy():
            folder_norm = os.path.normcase(os.path.normpath(folder))
            # Only touch genuine sub-folders, not the top-level folder itself
            if folder_norm != old_norm and folder_norm.startswith(old_norm + os.sep):
                relative = os.path.relpath(folder, old_path)
                new_folder_path = os.path.join(new_path, relative)
                folder_data = self.data['folders'].pop(folder)
                self.data['folders'][new_folder_path] = folder_data

        # Now rename the top-level folder entry
        if old_path in self.data['folders']:
            self.data['folders'][old_path]['name'] = os.path.basename(new_path)
            self.data['folders'][new_path] = self.data['folders'].pop(old_path)

        self.page.run_task(self.save_file)
        
    # Called every 5 minutes to save our widgets that need file writes
    async def save_widgets_to_file(self):
        for widget in self.widgets.values():
            await widget.save_file()

    # Wrapper function to call save widgets to file every 5 minutes
    async def _periodic_save_widget(self):
        '''Runs our periodic task every 5 minutes until this view unmounts.'''
        while self._periodic_worker_running:
            
            # Save dirty widgets every 5 minutes 
            for _ in range(300):
                if not self._periodic_worker_running:
                    break
                await asyncio.sleep(1)

            await self.save_widgets_to_file()

    def did_mount(self):        

        self._periodic_worker_running = True
        self.page.run_task(self._periodic_save_widget)  # Start the periodic task in the background

    def will_unmount(self):
        # Stop the periodic worker when this view leaves the page.
        self._periodic_worker_running = False

    # Called on story startup to load all our content objects
    def load_widgets(self):
        ''' Loads our content from our content folder inside of our story folder '''
        from models.widgets.document import Document
        from models.widgets.note import Note
        from models.widgets.canvas import Canvas
        from models.widgets.canvas_board import CanvasBoard
        from models.widgets.character import Character
        from models.widgets.plotline import Plotline
        from models.widgets.map import Map
        from models.widgets.character_connection_map import CharacterConnectionMap
        from models.widgets.world import World
        from models.widgets.item import Item
        from models.widgets.chart import Chart
        from models.widgets.comic_preview import ComicPreview
        from models.widgets.plot_chart import PlotChart

        # If we are being re-loaded after settings or another story, clear our content so we can load it fresh
        self.widgets.clear()
        
        # Check if the characters folder exists. Creates it if it doesn't. Exists in case people delete this folder
        if not os.path.exists(self.data['content_directory_path']):
            try:
                os.makedirs(self.data['content_directory_path'])    
            except Exception:
                pass
            return  # Since this didn't exist, there is no content

        # Loads all files inside the content directory and its sub folders
        for dirpath, dirnames, filenames in os.walk(self.data['content_directory_path']):
            for filename in filenames:

                # All our objects are stored as JSON, so if not we skip
                if filename.endswith(".json"):
                    file_path = os.path.join(dirpath, filename)   
                    
                    try:

                        # Read the JSON file and set our data
                        with open(file_path, "r", encoding='utf-8') as f:
                            widget_data = json.load(f)
                        
                        # Extract the title, directory, and unique widget id
                        tag = widget_data.get("tag", "")
                        dir_path = widget_data.get("directory_path", "")
                        id = widget_data.get("id", "")

                        widget = None

                        match tag:
                            case "document": 
                                widget = Document(     # Create the object in its dict
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "canvas":
                                widget = Canvas(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "canvas_board":
                                widget = CanvasBoard(
                                    widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "note":
                                widget = Note(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "character":
                                widget = Character(
                                    widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "plotline":
                                widget = Plotline(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "map":
                                widget = Map(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "world":
                                widget = World(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "character_connection_map":
                                widget = CharacterConnectionMap(
                                    widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "item":
                                widget = Item(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "chart":
                                widget = Chart(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "comic_preview":
                                widget = ComicPreview(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )

                            case "plot_chart":
                                widget = PlotChart(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case _:
                                print("Widget tag not valid Tag: ", tag)

                        if widget is not None and id != "":
                            self.widgets[id] = widget
                            
                    # Handle errors if the path is wrong
                    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                        print(f"Error loading content from {filename}: {e}")

        # Reload all ccm's, since they need all characters loaded to work
        # TODO: Just put all these into a list so when we build later, we actually create them here
        for widget in self.widgets.values():
            if widget.data.get('tag', "") == "character_connection_map" and widget.data.get('visible', False):
                widget.reload_widget()

    async def import_folder_clicked(self, e: ft.Event):
        dir_path = e.control.data or self.data.get('content_directory_path',  '')

        folder_path = await ft.FilePicker().get_directory_path()
        if not folder_path:
            self.page.show_dialog(SnackBar("No folder selected."))
            return  
        


    async def import_files_clicked(self, e: ft.Event):
        from models.widget import Widget
        #from utils.import_util import import_widgets

        # TODO: Go through each file. Make sure a widget with that name/key doesnt already exist in that directory
        # Otherwise, figure out what type of widget it should be and add it to story

        dir_path = e.control.data or self.data.get('content_directory_path',  '')

        files = await ft.FilePicker().pick_files(allow_multiple=True, allowed_extensions=["jpg", "jpeg", "png", "webp", "json", "txt", "pdf", "docx", "md"])
        #if files:
            #widgets: list[Widget] = import_widgets([file.path for file in files], dir_path)

            # Check if widget exists already in story
            
            

    # Opens the dialog to export
    async def export_clicked(self, e=ft.Event):
        # TODO: Save an export path to auto open with save files. Users cannot name their files
        # Export file types for canvas and document have dif settings
        dlg = ft.AlertDialog(
            title="Export"
        )

        self.page.show_dialog(dlg)

        
    # Called to create a new widget based on tag (document, note, character, etc)
    async def create_widget(self, title: str, tag: str, directory_path: str=None, data: dict=None, chart_type: str="bar"):
        ''' Creates our new widget based on the tag passed in and directory_path passed in'''
        from models.widgets.document import Document
        from models.widgets.note import Note
        from models.widgets.canvas import Canvas
        from models.widgets.canvas_board import CanvasBoard
        from models.widgets.character import Character
        from models.widgets.plotline import Plotline
        from models.widgets.map import Map
        from models.widgets.character_connection_map import CharacterConnectionMap
        from models.widgets.item import Item
        from models.widgets.world import World
        from models.widgets.chart import Chart
        from models.widgets.comic_preview import ComicPreview
        from models.widgets.plot_chart import PlotChart
        from models.app import app

        #if not self.blocker.visible:
            #self.blocker.visible = True
            #self.blocker.update()
            #await asyncio.sleep(0)   # Wait for blocker to update before creating the new item, which will update the UI again

        if directory_path is None:
            directory_path = self.data.get('content_directory_path',  '')

        widget = None

        match tag:
            case "document":
                widget = Document(title, directory_path, self, data, True)
            case "note":
                widget = Note(title, directory_path, self, data, True)
            case "canvas":
                d = {'canvas_data': data} if data is not None else None
                widget = Canvas(title,  directory_path, self, d, True)
            case "character":
                if app.settings.data.get('active_character_template', "None") != "None":
                    data = app.settings.data['character_templates'].get(app.settings.data['active_character_template'], {}).copy()
                    data = {'character_data': data}
                widget = Character(title, directory_path, self, data, True)
            case "plotline":
                widget = Plotline(title, directory_path, self, data, True)
            case "map":
                widget = Map(title, directory_path, self, data, True)
            case "character_connection_map":
                widget = CharacterConnectionMap(title, directory_path, self, data, True)
            case "world":
                widget = World(title, directory_path, self, data, True)
            case "canvas_board":
                widget = CanvasBoard(title, directory_path, self, data, True)   
            case "item":
                widget = Item(title, directory_path, self, data, True)  
            case "chart":
                widget = Chart(title, directory_path, self, data, True, type=chart_type)
            case "comic_preview":
                widget = ComicPreview(title, directory_path, self, data, True)
            case "plot_chart":
                widget = PlotChart(title, directory_path, self, data, True)
            case _:
                self.page.show_dialog(SnackBar(f"Error creating widget {title}: Invalid tag {tag}"))

        # Force a file write for newly created widgets
        if widget is not None:
            widget.needs_file_write = True
            await widget.save_file()
        
        # Save our widget to our widgets list
        self.widgets[widget.data['id']] = widget        

        # Finish tasks creating widget to make sure the file has enough time to save
        self.update_data(**{'workspace_selected_index': len(self.workspace.main_pin)})  
        self.workspace.reload_workspace()

        # Apply the UI changes
        if self.data.get('selected_rail', "content") != "canvas":
            self.active_rail.reload_rail()
    
        # Unhide the blocker
        #if self.blocker.visible:
            #self.blocker.visible = False
            #self.blocker.update()


    def rebuild_widget(self, widget) -> ft.Control:
        ''' Delcares the widget as a new object to refresh its page reference. '''
        from models.widgets.document import Document
        from models.widgets.note import Note
        from models.widgets.canvas import Canvas
        from models.widgets.canvas_board import CanvasBoard
        from models.widgets.character import Character
        from models.widgets.plotline import Plotline
        from models.widgets.map import Map
        from models.widgets.character_connection_map import CharacterConnectionMap
        from models.widgets.world import World
        from models.widgets.item import Item
        from models.widgets.chart import Chart
        from models.widgets.comic_preview import ComicPreview
        from models.widgets.plot_chart import PlotChart

        tag = widget.data.get('tag', None)
        new_widget = None
        match tag:
            case "document":
                new_widget = Document(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case "canvas":
                new_widget = Canvas(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case "note":
                new_widget = Note(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case "character":
                new_widget = Character(
                    widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case "plotline":
                new_widget = Plotline(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case "map":
                new_widget = Map(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case "world":
                new_widget = World(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case "character_connection_map":
                new_widget = CharacterConnectionMap(
                    widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case "canvas_board":
                new_widget = CanvasBoard(
                    widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )

            case "item":
                new_widget = Item(
                    widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )

            case "chart":
                new_widget = Chart(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
            case "comic_preview":
                new_widget = ComicPreview(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )

            case "plot_chart":
                new_widget = PlotChart(
                    title=widget.data.get('title', 'Untitled Document'),
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_new=widget.is_new
                )
                
            case _:
                self.page.show_dialog(SnackBar(f"Error rebuilding widget {widget.title}: Invalid tag {tag}"))

        

        self.widgets[new_widget.data.get('id')] = new_widget

        return new_widget


    # Called clicking outside the menu to close it
    async def close_menu(self, e=None):
        ''' Closes our right click menu when clicking outside of it '''
        
        if self.menu.visible:
            self.menu.visible = False
            self.menu.update()
        if self.close_menu_detector.visible:
            self.close_menu_detector.visible = False
            self.close_menu_detector.update()

    def close_menu_instant(self, e=None):
        ''' Closes our right click menu when clicking outside of it '''
       
        if self.menu.visible:
            self.menu.visible = False
            self.menu.update()
        if self.close_menu_detector.visible:
            self.close_menu_detector.visible = False
            self.close_menu_detector.update()
 
    # Called to open a right click menu in the page overlay
    def open_menu(self, menu_options: list):
        ''' Sets our menu and close menu detector to visible, sets their content and position '''

        # Skip if no options to show, cuz why bother
        if len(menu_options) == 0:
            return
        
        # If we already have a menu open, close it before opening the new menu
        if self.menu.visible:
            self.close_menu_instant()

        # Adjust mouse positions if the menu would go off screen
        if self.mouse_x + 160 > self.page.width:
            self.mouse_x -= 160
        if self.mouse_y + 230 > self.page.height:
            self.mouse_y -= 115

        # Set the content and position
        self.menu.content.controls = menu_options
        self.menu.left = self.mouse_x
        self.menu.top = self.mouse_y

        # Set visible
        self.menu.visible = True
        self.close_menu_detector.visible = True
        self.close_menu_detector.update()
        self.menu.update()

        

    # Builds our view
    def build(self) -> list[ft.Control]:
        ''' Builds our 'view' (page) that consists of our menubar, rails, and workspace '''
        from ui.menu_bar import create_menu_bar
        from ui.workspaces_rail import WorkspacesRail
        from ui.active_rail import ActiveRail
        from ui.workspace import Workspace
        from models.app import app
        from models.isolated_controls.row import IsolatedRow

        # Called when resizing the active rail by dragging the resizer
        async def move_active_rail_divider(e: ft.DragUpdateEvent):
            ''' Responsible for altering the width of the active rail '''
            self.workspace.is_resizing = True

            self.active_rail.width += int(e.local_delta.x)    # Apply the change to our rail
            if self.active_rail.width < 250:
                self.active_rail.width = 250
            elif self.active_rail.width > 600:
                self.active_rail.width = 600
            self.active_rail.update()


        # Called when app stops dragging the resizer to resize the active rail
        async def save_active_rail_width(e: ft.DragEndEvent):
            ''' Saves our new width that will be loaded next time app opens the app '''
            self.workspace.is_resizing = False

            app.settings.data['active_rail_width'] = self.active_rail.width
            await app.settings.save_file()

        # Load our widgets
        self.load_widgets() 

        self.page.title = f"{self.title}"   # Set our page title

        # Create our menubar, workspaces rail, active rail, and workspace objects
        self.menubar = create_menu_bar(self.page, self)
        self.workspaces_rail = WorkspacesRail(self.page, self) 
        self.workspace = Workspace(self.page, self)  
        self.active_rail = ActiveRail(self.page, self) 


        # The actual resizer for the active rail (gesture detector)
        active_rail_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,   # Total width of the GD, so its easier to find with mouse
                content=ft.VerticalDivider(2, 2),     # Original
                padding=ft.Padding.only(left=8),  # Push the 2px divider ^ to the right side
                bgcolor=ft.Colors.SURFACE
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,  # Show horizontal resize cursor when hovering over the resizer
            on_pan_update=move_active_rail_divider, # Resize the active rail as app is dragging
            on_pan_end=save_active_rail_width,  # Save the resize when app is done dragging
            #drag_interval=30,
        )

        

        # Views render like columns, so we add elements top-down
        self.controls = [
            self.menubar,
            IsolatedRow([
                
                self.workspaces_rail,
                self.active_rail,
                active_rail_resizer,
                self.workspace
            ], spacing=0, expand=True)
        ]


        # Our container that sits on top of the self.page overlay when right clicking options. Starts invisible
        self.menu = ft.Container(
            left=self.mouse_x, top=self.mouse_y,   # Positions the menu at the mouse location
            border_radius=4, visible=False,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            width=160, #border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            shadow=ft.BoxShadow(0, 0.25, offset=ft.Offset(0, 0.25), ),
            content=ft.Column(
                spacing=0,
                controls=[]
            ),
        )

        # Outside gesture detector to close the menu when clicking outside the menu container
        self.close_menu_detector = ft.GestureDetector(
            expand=True, visible=False,
            on_tap_down=self.close_menu,
            on_secondary_tap_down=self.close_menu,
        )
        

        # Overlay is a stack, so add the detector, then the menu container
        self.page.overlay.append(self.close_menu_detector)
        self.page.overlay.append(self.menu)
        self.page.overlay.append(self.blocker)   # Add our blocker to the overlay as well, so it sits on top of everything when visible

        # Apply everything to the self.page
        self.page.update()

        self.is_initialized = True


    # Only called after loading the tutorial story
    async def create_tutorial_content(self):
        from models.widgets.document import Document
        from models.widgets.note import Note
        from models.widgets.canvas import Canvas
        from models.widgets.canvas_board import CanvasBoard
        from models.widgets.character import Character
        from models.widgets.plotline import Plotline
        from models.widgets.map import Map
        from models.widgets.character_connection_map import CharacterConnectionMap
        from models.widgets.world import World
        from models.widgets.item import Item
        from models.widgets.chart import Chart
        from models.widgets.comic_preview import ComicPreview
        from models.widgets.plot_chart import PlotChart

        # Clear out content folder to reset tutorial content
        folder_path = self.data.get('content_directory_path')
        if os.path.exists(folder_path) and os.path.isdir(folder_path):  
            shutil.rmtree(folder_path)   

        # Create a default folder and widget for each widget
        await self.create_folder(self.data.get('content_directory_path'), "Folder")
        await self.create_widget("Document", "document", self.data.get('content_directory_path'))
        await self.create_widget("Note", "note", self.data.get('content_directory_path'))
        await self.create_widget("Character", "character", self.data.get('content_directory_path'))
        await self.create_widget("Character Connection Map", "character_connection_map", self.data.get('content_directory_path'))
        await self.create_widget("World", "world", self.data.get('content_directory_path'))
        # await self.create_widget("Canvas", "canvas", self.data.get('content_directory_path'))
        # await self.create_widget("Plotline", "plotline", self.data.get('content_directory_path'))
        # await self.create_widget("Map", "map", self.data.get('content_directory_path'))
        # await self.create_widget("Canvas Board", "canvas_board", self.data.get('content_directory_path'))
        # await self.create_widget("Item", "item", self.data.get('content_directory_path'))
        # await self.create_widget("Radar Chart", "chart", self.data.get('content_directory_path'))
        # await self.create_widget("Bar Chart", "chart", self.data.get('content_directory_path'), chart_type="bar")
        # await self.create_widget("Comic Preview", "comic_preview", self.data.get('content_directory_path'))
        # await self.create_widget("Plot Chart", "plot_chart", self.data.get('content_directory_path'))
        
        # Reload rail to apply
        self.active_rail.reload_rail()
        
       
