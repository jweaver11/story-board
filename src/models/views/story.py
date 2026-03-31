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
from utils.verify_data import verify_data
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
        template: str=None,     # Template to use when creating new story (sci-fi, fantasy, etc.)
        type: str=None          # Type of story (novel, comic, etc.)
    ):
        
        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True
        
        # Parent constructor
        super().__init__(
            route=return_safe_name(f"/{title}_story"),    # Sets our route for our new story
            padding=ft.Padding.only(top=0, left=0, right=0, bottom=0),      # No padding for the page
            spacing=0,                                                      # No spacing between menubar and rest of page
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
        )  

        self.title = title              # Gives our story a title when its created
        self.p = page                   # Reference to our page object for updating UI elements
        self.data = data                # Sets our data (if any) passed in. New stories just have none
        self.template = template        # Template for our story (sci-fi, fantasy, etc.)
        self.type = type                # Type of story, novel or comic. Affects how templates for creating new content will work

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,           # Pass in our own data so the function can see the actual data we loaded
            {
                'title': self.title,
                'directory_path': os.path.join(data_paths.stories_directory_path, return_safe_name(f"/{title}_story")),
                'tag': "story",
                'selected_rail': "content",
                'content_directory_path': os.path.join(data_paths.stories_directory_path, return_safe_name(f"/{title}_story"), "content"),
                'top_pin_height': 200,
                'left_pin_width': 230,
                'main_pin_height': int,
                'right_pin_width': 230,
                'bottom_pin_height': 200,
                'created_at': str,
                'last_modified': str,
                'connections': [],    # Connections between characters, places, items, etc. Since they are between multiple widgets, I stuck them here
                
                'settings': {
                    'type': self.type,             # Novel or comic. Affects templates and default data for new content
                    'active_character_template': str,    # Which template is being used for new characters
                    'multi_planetary': bool,       # Whether the story will take place on multiple planets
                    'multi_plotlines': bool,       # Whether the story will have multiple plotlines (regression, multiverse, etc.)
                    'character_rail_sort_by': "Role",
                },
                
                # Dict of all our categories INSIDE of basic story structure (content, characters, plotlines)
                'folders': {
                    'path': {                   # Path to the category folder (used as the key, since all will be unique)
                        'name': str,            # Name of category just in case
                        'color': str,           # Color of that folder
                        'is_expanded': True     # Whether this folder is expanded in the tree view
                    }
                },            
                'is_new_story': True,      # Whether this story is newly created or loaded from storage

            },
        )

        if is_new:
            page.run_task(self.save_dict)

        self.template = template

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
        self.widgets: list = []    

        
        # Called outside of constructor to avoid circular import issues, or it would be called here
        #self.startup() # Called when opening our active story to load all its data and build its view
        
    # Isolates stories from page.update calls. Needed for keeper performance when opening menus
    def is_isolated(self): 
        return True
    
    # Called from main when our program starts up. Needs a page reference, thats why not called here
    def startup(self):

        # Stories have required structures as well, so we verify they exist or we will error out
        # We also use this function to create most detailed structures from templates if newly created story
        self.verify_story_structure(self.template)  

        if self.data.get('is_new_story', True):
            print("New story created:", self.title)
            # Run logic here to initialize certain things


        self.load_widgets() 

        # Builds our view (menubar, rails, workspace) and adds it to the page
        self.build_view()

        # After the story has been loaded, make sure this is no longer a new story
        if self.data.get('is_new_story', True):
            self.data['is_new_story'] = False 
            self.p.run_task(self.save_dict)

        # Declare the story loaded for loading purposes
        self.is_initialized = True


    # Called whenever there are changes in our data that need to be saved
    async def save_dict(self):
        ''' Saves the data of our story to its JSON File, and all its folders as well '''

        print("Saved story: ", self.title)

        try:
            # Makes sure our directory path is always right. 
            self.data['directory_path'] = os.path.join(data_paths.stories_directory_path, self.route)
                
            # Our file path we store our data in
            file_path = os.path.join(self.data['directory_path'], f"{self.route}.json")

            # Create the directory if it doesn't exist. Catches errors from users deleting folders
            os.makedirs(self.data['directory_path'], exist_ok=True)
            
            # Save the data to the file (creates file if doesnt exist)
            with open(file_path, "w", encoding='utf-8') as f:   
                json.dump(self.data, f, indent=4)
        
        # Handle errors
        except Exception as e:
            self.p.open(SnackBar(f"Error saving story data: {e}"))

    # Called for little data changes
    def change_data(self, **kwargs):
        ''' Changes a key/value pair in our data and saves the json file '''
        # Called by:
        # story.change_data(**{'key': value, 'key2': value2})

        try:
            for key, value in kwargs.items():
                self.data.update({key: value})

            self.p.run_task(self.save_dict)

        # Handle errors
        except Exception as e:
            print(f"Error changing data {key}:{value} for story {self.title}: {e}")
            

    # Called when a new story is created and not loaded with any data
    def verify_story_structure(self, template: str=None):
        ''' Creates our story folder structure inside of our stories directory '''


        # TODO: Try statements only when writing to files
        # On story first creation, add default folders inside content: documents, notes, canvases, images
        # Inside characters: main, side, background

        try:


            # Sets our path to our story folder
            directory_path = os.path.join(data_paths.stories_directory_path, self.route)

            # Makes sure our content folder exists
            folder_path = os.path.join(directory_path, "content")
            os.makedirs(folder_path, exist_ok=True)     # Checks if they exist or not, so they won't be overwritten

            # Save our data
            self.p.run_task(self.save_dict)

            def _create_template_name():

                pass

        # Handle errors
        except Exception as e:
            print(f"Error verifying/creating story structure for {self.title}: {e}")

    # Called when a new folder/category is created.
    def create_folder(self, directory_path: str, name: str):
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
            self.p.run_task(self.save_dict)


            self.active_rail.reload_rail()

        # Handle errors
        except Exception as e:
            print(f"Error creating folder: {e}")
        
    # Called when deleting a folder/category from our story
    def delete_folder(self, full_path: str):
        ''' Deletes a category from our story structure '''

        try:
            # Delete the folder from storage
            shutil.rmtree(full_path)

            # TODO: Delete this folder and all sub folders and widgets inside of this folder

            # Remove it from data
            self.data['folders'].pop(full_path, None)

            self.p.run_task(self.save_dict)

            for widget in self.widgets:
                if widget.directory_path.startswith(full_path):
                    print("Deleting widget ", widget.title, " in deleted folder")
                    widget.delete_file()
                    if widget in self.widgets:
                        self.widgets.remove(widget)

            # Delete any sub folders from inside our storhy data. Technically not needed
            for folder in self.data['folders'].copy():
                if folder.startswith(full_path):
                    print("Deleting folder ", folder, " in deleted folder")
                    self.data['folders'].pop(folder, None)

            self.blocker.visible = True
            self.blocker.update()
            self.p.run_task(asyncio.sleep, 0)

            self.active_rail.reload_rail()
            self.workspace.reload_workspace()
            self.close_menu_instant()
            self.blocker.visible = False
            self.blocker.update()

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
                await self.save_dict()
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

        
        # Update the old key in our folders data
        if old_path in self.data['folders']:
            #print("Updating old path in story data")
            self.data['folders'][new_path] = self.data['folders'].pop(old_path)
            self.p.run_task(self.save_dict)


        # Go through each widget and update its directory path if it was in the renamed folder
        for widget in self.widgets:
            if widget.directory_path.startswith(old_path):
                # Update the directory path
                relative_path = widget.directory_path[len(old_path):]
                widget.directory_path = new_path + relative_path
                widget.data['directory_path'] = widget.directory_path  # Update its data
                widget.data['key'] = f"{widget.directory_path}\\{return_safe_name(self.title)}_{self.data.get('tag', '')}"
                self.p.run_task(widget.save_dict)  # Save the updated widget data

        # Go through each folder, and if its a sub folder change it to match our new parent path
        for folder in self.data['folders'].copy():
            if folder.startswith(old_path):
                relative_path = folder[len(old_path):]
                new_folder_path = new_path + relative_path
                self.data['folders'][new_folder_path] = self.data['folders'].pop(folder)

        self.p.run_task(self.save_dict)
        

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
        #from models.widgets.object import Object

        # If we are being re-loaded after settings or another story, clear our content so we can load it fresh
        self.widgets.clear()
        
        # Check if the characters folder exists. Creates it if it doesn't. Exists in case people delete this folder
        if not os.path.exists(self.data['content_directory_path']):
            os.makedirs(self.data['content_directory_path'])    
            return

        # Loads all files inside the content directory and its sub folders
        for dirpath, dirnames, filenames in os.walk(self.data['content_directory_path']):
            for filename in filenames:

                # PHASE OUT, CHAPS WILL BE LOADED FROM WIDGET DATA
                if filename.endswith("_text.json"):
                    continue

                # All our objects are stored as JSON
                if filename.endswith(".json"):
                    file_path = os.path.join(dirpath, filename)   
                    
                    try:

                        # Read the JSON file and set our data
                        with open(file_path, "r", encoding='utf-8') as f:
                            widget_data = json.load(f)
                        
                        # Extract the title from the data
                        tag = widget_data.get("tag", "")
                        dir_path = widget_data.get("directory_path", "")

                        widget = None

                        match tag:
                            case "document": 
                                widget = Document(     # Create the object in its dict
                                    title=widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "canvas":
                                widget = Canvas(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "canvas_board":
                                widget = CanvasBoard(
                                    widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "note":
                                widget = Note(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "character":
                                widget = Character(
                                    widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "plotline":
                                widget = Plotline(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "map":
                                widget = Map(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "world":
                                widget = World(
                                    title=widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case "character_connection_map":
                                widget = CharacterConnectionMap(
                                    widget_data.get('title', 'Untitled Document'),
                                    page=self.p,
                                    directory_path=dir_path,
                                    story=self,
                                    data=widget_data,
                                )
                            case _:
                                print("Widget tag not valid Tag: ", tag)

                        if widget is not None:
                            self.widgets.append(widget)
                            
        
                            
                    # Handle errors if the path is wrong
                    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                        print(f"Error loading content from {filename}: {e}")

        
    # Called to create a new widget based on tag (document, note, character, etc)
    async def create_widget(self, title: str, tag: str=None, directory_path: str=None, data: dict=None):
        ''' Creates our new widget based on the tag passed in and directory_path passed in'''
        from models.widgets.document import Document
        from models.widgets.note import Note
        from models.widgets.canvas import Canvas
        from models.widgets.canvas_board import CanvasBoard
        from models.widgets.character import Character
        from models.widgets.plotline import Plotline
        from models.widgets.map import Map
        from models.widgets.character_connection_map import CharacterConnectionMap
        from models.widgets.world import World
        from models.mini_widgets.arc import Arc
        from models.mini_widgets.plot_point import PlotPoint
        #from models.widgets.object import Object

        from models.app import app

        if not self.blocker.visible:
            self.blocker.visible = True
            self.blocker.update()
            await asyncio.sleep(0)   # Wait for blocker to update before creating the new item, which will update the UI again

        if directory_path is None:
            directory_path = self.data.get('content_directory_path',  '')

        widget = None

        match tag:
            case "document":
                widget = Document(title, self.p, directory_path, self, data)
            case "note":
                widget = Note(title, self.p, directory_path, self, data)
            case "canvas":
                d = {'canvas_data': data} if data is not None else None
                widget = Canvas(title, self.p, directory_path, self, d)
            case "character":
                if app.settings.data.get('active_character_template', "None") != "None":
                    data = app.settings.data['character_templates'].get(app.settings.data['active_character_template'], {}).copy()
                    data = {'character_data': data}
                widget = Character(title, self.p, directory_path, self, data)
            case "plotline":
                widget = Plotline(title, self.p, directory_path, self, data)
            case "map":
                widget = Map(title, self.p, directory_path, self, data)
            case "character_connection_map":
                widget = CharacterConnectionMap(title, self.p, directory_path, self, data)
            case "world":
                widget = World(title, self.p, directory_path, self, data)
            case "canvas_board":
                widget = CanvasBoard(title, self.p, directory_path, self, data)     
            case _:
                self.p.show_dialog(SnackBar(f"Error creating widget {title}: Invalid tag {tag}"))

        
        

        # Force a file save and write
        if widget is not None:
            widget.save_counter = 100
            await widget.save_dict()
            self.widgets.append(widget)

        # Finish tasks creating widget to make sure the file has enough time to save
        self.workspace.reload_workspace()
        await asyncio.sleep(0.2)   

        # Apply the UI changes
        self.active_rail.reload_rail()
        
    
        # Unhide the blocker
        if self.blocker.visible:
            self.blocker.visible = False
            self.blocker.update()


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
        from models.mini_widgets.arc import Arc
        from models.mini_widgets.plot_point import PlotPoint

        tag = widget.data.get('tag', None)
        new_widget = None
        match tag:
            case "document":
                new_widget = Document(
                    title=widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case "canvas":
                new_widget = Canvas(
                    title=widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case "note":
                new_widget = Note(
                    title=widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case "character":
                new_widget = Character(
                    widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case "plotline":
                new_widget = Plotline(
                    title=widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case "map":
                new_widget = Map(
                    title=widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case "world":
                new_widget = World(
                    title=widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case "character_connection_map":
                new_widget = CharacterConnectionMap(
                    widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case "canvas_board":
                new_widget = CanvasBoard(
                    widget.data.get('title', 'Untitled Document'),
                    page=self.p,
                    directory_path=widget.data.get('directory_path', self.data['content_directory_path']),
                    story=self,
                    data=widget.data,
                    is_rebuilt=True
                )
                
            case _:
                self.p.show_dialog(SnackBar(f"Error rebuilding widget {widget.title}: Invalid tag {tag}"))

        for w in self.widgets:
            if w.data.get('key', None) == widget.data.get('key', None):
                self.widgets.remove(w)
                break

        self.widgets.append(new_widget)
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
       
        self.menu.visible = False
        self.close_menu_detector.visible = False
        self.close_menu_detector.update()
        self.menu.update()
 
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
        if self.mouse_x + 160 > self.p.width:
            self.mouse_x -= 160
        if self.mouse_y + 230 > self.p.height:
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

        

    # Called when new story object is created, either by program or by being loaded from storage
    def build_view(self) -> list[ft.Control]:
        ''' Builds our 'view' (page) that consists of our menubar, rails, and workspace '''
        from ui.menu_bar import create_menu_bar
        from ui.workspaces_rail import WorkspacesRail
        from ui.active_rail import Active_Rail
        from ui.workspace import Workspace
        from models.app import app
        from models.isolated_controls.row import IsolatedRow

        page = self.p

        page.title = f"{self.title}"

        # Clear our controls in our view before building it
        self.controls.clear()

        # Create our page elements as their own pages so they can update
        self.menubar = create_menu_bar(page, self)

        # Create our rails and workspace objects
        self.workspaces_rail = WorkspacesRail(page, self)  # Create our all workspaces rail
        
        self.workspace = Workspace(page, self)  # Reference to our workspace object for pin locations
        self.active_rail = Active_Rail(page, self)  # Container stored in story for the active rails

        

        # Called when resizing the active rail by dragging the resizer
        async def move_active_rail_divider(e: ft.DragUpdateEvent):
            ''' Responsible for altering the width of the active rail '''
            self.workspace.is_resizing = True

            active_rail_stack.width += int(e.local_delta.x)    # Apply the change to our rail
            if active_rail_stack.width < 210:
                active_rail_stack.width = 210
            elif active_rail_stack.width > page.width / 2:
                active_rail_stack.width = page.width / 2
            active_rail_stack.update()

        # Called when app stops dragging the resizer to resize the active rail
        async def save_active_rail_width(e: ft.DragEndEvent):
            ''' Saves our new width that will be loaded next time app opens the app '''
            self.workspace.is_resizing = False

            app.settings.data['active_rail_width'] = active_rail_stack.width
            await app.settings.save_dict()

        # The actual resizer for the active rail (gesture detector)
        active_rail_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,   # Total width of the GD, so its easier to find with mouse
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                # Thin vertical divider, which is what the app will actually drag
                content=ft.VerticalDivider(2, 2),     # Original
                padding=ft.Padding.only(right=8),  # Push the 2px divider ^ to the right side
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,  # Show horizontal resize cursor when hovering over the resizer
            on_pan_update=move_active_rail_divider, # Resize the active rail as app is dragging
            on_pan_end=save_active_rail_width,  # Save the resize when app is done dragging
            drag_interval=50,
        )

        # Isolates the row containing our active rail resizing doesnt lag heckin bac
        iso_row = IsolatedRow([self.active_rail, active_rail_resizer], spacing=0)
        active_rail_stack = ft.Stack(     # Stick it in a stack (or any control with 'controls' property) that we can update
            [iso_row], 
            width=app.settings.data.get('active_rail_width', 200),
            animate_size=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        )   


        # Save our 2 rails, divers, and our workspace container in a row
        row = IsolatedRow(
            spacing=0,  # No space between elements
            expand=True,  # Makes sure it takes up the entire window/screen

            controls=[
                self.workspaces_rail,  # Main rail of all available workspaces
                ft.VerticalDivider(2, 2),     
                
                # OLD
                #self.active_rail,    # Rail for the selected workspace
                #active_rail_resizer,   # Divider between rail and work area

                # Holds our active rail container and resizer
                #ft.Container(width=6),
                active_rail_stack,
                
                self.workspace,    # Work area for widgets
            ],
        )

        # Views render like columns, so we add elements top-down
        self.controls = [self.menubar, row]


        # Our container that sits on top of the page overlay when right clicking options. Starts invisible
        self.menu = ft.Container(
            left=self.mouse_x, top=self.mouse_y,   # Positions the menu at the mouse location
            border_radius=ft.BorderRadius.all(10), visible=False,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            width=160, border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            shadow=ft.BoxShadow(color=ft.Colors.OUTLINE_VARIANT, blur_radius=4, blur_style=ft.BlurStyle.OUTER),
            content=ft.Column(
                spacing=0,
                controls=[]
            ),
        )

        # Outside gesture detector to close the menu when clicking outside the menu container
        self.close_menu_detector = ft.GestureDetector(
            expand=True, visible=False,
            on_tap_down=self.close_menu,
            #on_secondary_tap=lambda _: self.open_menu()
            on_secondary_tap_down=self.close_menu,
        )
        

        # Overlay is a stack, so add the detector, then the menu container
        self.p.overlay.append(self.close_menu_detector)
        self.p.overlay.append(self.menu)
        self.p.overlay.append(self.blocker)   # Add our blocker to the overlay as well, so it sits on top of everything when visible

        # Apply everything to the page
        page.update()
