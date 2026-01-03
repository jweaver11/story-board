''' 
Master Story class that contains data and methods for the entire story 
Our story is an extended ft.View, meaning new routes can display the story object directly
The Story object creates widgets (characters, chapters, notes, etc.) objects that are stored inside of itself.
Stories contain metadata, ui elements, and all the widgets, as well as methods to create new widgets only
'''

import flet as ft
import os
import shutil
import json
from constants import data_paths
from handlers.verify_data import verify_data
from styles.snack_bar import SnackBar
from handlers.safe_string_checker import return_safe_name


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
        
        # Parent constructor
        super().__init__(
            route=return_safe_name(f"/{title}"),    # Sets our route for our new story
            padding=ft.padding.only(top=0, left=0, right=0, bottom=0),      # No padding for the page
            spacing=0,                                                      # No spacing between menubar and rest of page
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
                'directory_path': os.path.join(data_paths.stories_directory_path, self.route),
                'tag': "story",
                'selected_rail': "characters",
                'content_directory_path': os.path.join(data_paths.stories_directory_path, self.route, "content"),
                'top_pin_height': 200,
                'left_pin_width': 230,
                'main_pin_height': int,
                'right_pin_width': 230,
                'bottom_pin_height': 200,
                'created_at': str,
                'last_modified': str,
                

                'settings': {
                    'type': self.type,             # Novel or comic. Affects templates and default data for new content
                    'multi_planetary': bool,       # Whether the story will take place on multiple planets
                    'multi_timelines': bool,       # Whether the story will have multiple timelines (regression, multiverse, etc.)
                    'character_rail_sort_by': {
                        'method': "role",          # None, alphabeticaly, role, morality, age
                        'direction': "descending",       # ascending (top start low) or descending (top start high)
                    },
                },
                
                # Dict of all our categories INSIDE of basic story structure (content, characters, timelines)
                'folders': {
                    'path': {                   # Path to the category folder (used as the key, since all will be unique)
                        'name': str,            # Name of category just in case
                        'color': str,           # Color of that folder
                        'is_expanded': True     # Whether this folder is expanded in the tree view
                    }
                },            
                'is_new_story': True,      # Whether this story is newly created or loaded from storage

                # Paint settings for our canvas drawings to use as default that they will then change
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
                    'erase_mode': False,               # Whether we're in erase mode or not
                    'stroke_dash_pattern': [10, 15],
                }
            },
        )

        self.template = template
            
        # Declare our UI elements before we create them later. They are stored as objects so we can reload them when needed
        self.menubar: ft.Container = None     # Menu bar at top of page
        self.workspaces_rail: ft.Container = None      # Rail on left side showing our 6 workspaces
        self.active_rail: ft.Container = None    # Rail showing whichever workspace is selected
        self.workspace: ft.Container = None        # Main workspace area where our pins display our widgets

        # Our widgets objects. Keys are stored as directory paths + titles for uniqueness (example: c:\path\to\character\character_name)
        self.chapters: dict = {}        # Text based chapeters only
        self.notes: dict = {}           # Notes stored in our story
        self.canvases: dict = {}        # canvases by the user for comic chapters, or to store images (as backgrounds)
        self.characters: dict = {}      # Characters in the story
        self.timelines: dict = {}       # Timelines for our story
        self.maps: dict = {}            # Maps created inside of world building

        self.world_building: None = None      # World building widget that contains our maps, lore, governments, history, etc
        self.family_tree_view: None = None    # Family tree view widget for tracking character relationships

        # Store all our widgets above in a master list for easier rendering in the UI
        self.widgets: list = []    

        # Variables to store our mouse position for opening menus
        self.mouse_x: int = 0
        self.mouse_y: int = 0

        # State that we are not initialized yet, which will be changed at the end of startup method
        self.is_initialized = False
        # Called outside of constructor to avoid circular import issues, or it would be called here
        #self.startup() # Called when opening our active story to load all its data and build its view
        
        
    # Called from main when our program starts up. Needs a page reference, thats why not called here
    def startup(self):

        # Stories have required structures as well, so we verify they exist or we will error out
        # We also use this function to create most detailed structures from templates if newly created story
        self.verify_story_structure(self.template)  

        if self.data.get('is_new_story', True):
            print("New story created:", self.title)
            # Run logic here to initialize certain things

        # This also loads our canvas board images here, since they can be opened in either workspace
        self.load_content()

        # Everything we loaded above is a widget, but this just adds them all to self.widgets
        self.load_widgets()

        # Builds our view (menubar, rails, workspace) and adds it to the page
        self.build_view()

        # After the story has been loaded, make sure this is no longer a new story
        self.data['is_new_story'] = False 
        self.save_dict()

        # Declare the story loaded for loading purposes
        self.is_initialized = True


    # Called whenever there are changes in our data that need to be saved
    def save_dict(self):
        ''' Saves the data of our story to its JSON File, and all its folders as well '''

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

            self.save_dict()

        # Handle errors
        except Exception as e:
            print(f"Error changing data {key}:{value} for story {self.title}: {e}")
            

    # Called when a new story is created and not loaded with any data
    def verify_story_structure(self, template: str=None):
        ''' Creates our story folder structure inside of our stories directory '''


        # TODO: Try statements only when writing to files
        # On story first creation, add default folders inside content: chapters, notes, canvases, images
        # Inside characters: main, side, background

        try:


            # Sets our path to our story folder
            directory_path = os.path.join(data_paths.stories_directory_path, self.route)

            # Makes sure our content folder exists
            folder_path = os.path.join(directory_path, "content")
            os.makedirs(folder_path, exist_ok=True)     # Checks if they exist or not, so they won't be overwritten

            # Save our data
            self.save_dict()

            def _create_template_name():

                self.create_folder(
                    directory_path=self.data['content_directory_path'], 
                    name="Notes"
                )
                    
                # Using templates
                if template is not None:
                    pass

                # Create our folder to store our maps data files and their canvases
                maps_folders = [
                    "maps",
                    #"displays",
                ]
                for folder in maps_folders:
                    folder_path = os.path.join(directory_path, "world_building", folder)
                    os.makedirs(folder_path, exist_ok=True)

                # Set our sub folders inside of notes
                notes_folders = [
                    "Themes",
                    "Quotes",
                    "Research",
                ]

                # Create the sub folders inside of notes
                for folder in notes_folders:
                    folder_path = os.path.join(directory_path, "content", "Notes")

                    # Creates the sub folder using out path above
                    self.create_folder(
                        directory_path=folder_path, 
                        name=folder
                    )
                    
                
                # Create the path to the story's JSON file
                directory_path = os.path.join(data_paths.stories_directory_path, self.title) 

                # If multiplanetary, create the worlds folder
                if self.data['settings']['multi_planetary']:
                    worlds_folder_path = os.path.join(self.data['world_building_directory_path'], "maps")
                    self.create_folder(worlds_folder_path, name="Worlds")

        # Handle errors
        except Exception as e:
            print(f"Error verifying/creating story structure for {self.title}: {e}")

    # Called when a new folder/category is created.
    def create_folder(self, directory_path: str, name: str):
        ''' Creates a new category inside of our story structure for content organization '''
        #print("Creating folder at path:", directory_path)

        try:

            # Clean up name
            name = name.capitalize()    # Capitalize first letter
            name = name.rstrip()        # Remove trailing spaces

            # Create the full folder path
            folder_path = os.path.join(directory_path, name)

            # Make the folder in our storage if it doesn't already exist
            os.makedirs(folder_path, exist_ok=True) 
            # Add this folder to our folders data so we can save stuff like colors
            self.data['folders'].update({folder_path: {'name': name, 'color': "primary", 'is_expanded': True}})
            self.save_dict()

            self.active_rail.content.reload_rail()

        # Handle errors
        except Exception as e:
            print(f"Error creating folder: {e}")
        
    # Called when deleting a folder/category from our story
    def delete_folder(self, full_path: str):
        ''' Deletes a category from our story structure '''

        try:
            # Delete the folder from storage
            shutil.rmtree(full_path)

            # Remove it from data
            self.data['folders'].pop(full_path, None)

            self.save_dict()

            self.active_rail.content.reload_rail()

        # Handle errors
        except Exception as e:
            print(f"Error deleting folder: {e}")

    # Called when changing folder metadata, like color or is expanded or not
    def change_folder_data(self, full_path: str, key: str, value):
        ''' Changes our folder metadata inside of our story data '''
        #print("Changing folder data:", full_path, key, value)

        try:
            # Check if the folder exists in our data
            if full_path in self.data['folders']:
                self.data['folders'][full_path][key] = value
                self.save_dict()
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
            self.save_dict()

        # Go through each widget and update its directory path if it was in the renamed folder
        for widget in self.widgets:
            if widget.directory_path.startswith(old_path):
                # Update the directory path
                relative_path = widget.directory_path[len(old_path):]
                widget.directory_path = new_path + relative_path
                widget.save_dict()  # Save the updated widget data
                #print("Updated widget directory path to ", widget.title, " to ", widget.directory_path)
        

    # Called when deleting a widget from our story
    def delete_widget(self, widget) -> bool:
        ''' Deletes the object from our live story object and its reference in the pins.
        We then remove its storage file from our file storage as well. '''

        from models.widget import Widget

        # Called if file is successfully deleted. Then we remove the widget from its live storage
        def _delete_live_widget(widget: Widget):

            # Grab our widgets tag to see what type of object it is
            tag = widget.data.get('tag', None)

            match tag:
                case "chapter":
                    del self.chapters[widget.data.get('key', '')]
                case "canvas":
                    del self.canvases[widget.data.get('key', '')]
                case "note":
                    del self.notes[widget.data.get('key', '')]
                case "character":
                    del self.characters[widget.data.get('key', '')]
                case "timeline":
                    del self.timelines[widget.data.get('key', '')]
                case "map":
                    del self.maps[widget.data.get('key', '')]
                case "world_building":
                    self.world_building = None
                case "family_tree_view":
                    self.family_tree_view = None

                case _:
                    self.p.open(SnackBar(f"Error deleting widget: Unknown tag {tag}"))
                    return
            
            
            # Remove from our master widgets list so it won't be rendered anymore
            if widget in self.widgets:
                self.widgets.remove(widget)
        
        # If we successfully deleted the widget file, remove the live widget object as well
        if widget.delete_file():
            _delete_live_widget(widget)

            self.active_rail.content.reload_rail()
            self.workspace.reload_workspace()
            self.close_menu()

    # Called on story startup to load all our content objects
    def load_content(self):
        ''' Loads our content from our content folder inside of our story folder '''
        from models.widgets.note import Note
        from models.widgets.chapter import Chapter
        from models.widgets.canvas import Canvas
        from models.widgets.character import Character
        from models.widgets.timeline import Timeline   
        from models.widgets.map import Map
        from models.widgets.world_building import WorldBuilding
        from models.widgets.family_tree_view import FamilyTreeView

        # Check if the characters folder exists. Creates it if it doesn't. Exists in case people delete this folder
        if not os.path.exists(self.data['content_directory_path']):
            #print("Content folder does not exist, creating it.")
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
                        key = widget_data.get("key", None)
                        title = widget_data.get("title", filename.replace(".json", ""))
                        tag = widget_data.get("tag", "")

                        match tag:
                            case "chapter": 
                                self.chapters[key] = Chapter(title, self.p, dirpath, self, widget_data)
                            case "canvas":
                                self.canvases[key] = Canvas(title, self.p, dirpath, self, widget_data)
                            case "note":
                                self.notes[key] = Note(title, self.p, dirpath, self, widget_data)
                            case "character":
                                self.characters[key] = Character(title, self.p, dirpath, self, widget_data)
                            case "timeline":
                                self.timelines[key] = Timeline(title, self.p, dirpath, self, widget_data)
                            case "map":
                                self.maps[key] = Map(title, self.p, dirpath, self, widget_data)
                            case "world_building":
                                self.world_building = WorldBuilding(title, self.p, dirpath, self, widget_data)
                            case "family_tree_view":
                                self.widgets.append(FamilyTreeView(title, self.p, dirpath, self, widget_data))
                            case _:
                                print("content tag not valid. Tag: ", tag)
                            

                       

                            
                    # Handle errors if the path is wrong
                    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                        print(f"Error loading content from {filename}: {e}")


    # Called in startup after we have loaded all our live objects
    def load_widgets(self):
        ''' Loads all our widgets (characters, chapters, notes, etc.) into our master list of widgets '''

        # Clear our widgets list first to avoid duplicates
        self.widgets.clear() 

        # Add all our characters to the widgets list
        for character in self.characters.values():
            if character not in self.widgets:
                self.widgets.append(character)

        # Add all our chapters to the widgets list
        for chapter in self.chapters.values():
            if chapter not in self.widgets:
                self.widgets.append(chapter)

        for canvas in self.canvases.values():
            if canvas not in self.widgets:
                self.widgets.append(canvas)

        # Add our plotline to the widgets list
        for timeline in self.timelines.values():
            if timeline not in self.widgets:
                self.widgets.append(timeline)

        # Add our world building to the widgets list
        if self.world_building is not None:
            if self.world_building not in self.widgets:
                self.widgets.append(self.world_building)

        # Add all our maps to the widgets list
        for map in self.maps.values():
            if map not in self.widgets:
                self.widgets.append(map)

        # Add all our notes to the widgets list
        for note in self.notes.values():
            if note not in self.widgets:
                self.widgets.append(note)
        
    # Called to create a new widget based on tag (chapter, note, character, etc)
    def create_widget(self, title: str, tag: str=None, directory_path: str=None):
        ''' Creates our new widget based on the tag passed in and directory_path passed in'''
        from models.widgets.chapter import Chapter
        from models.widgets.note import Note
        from models.widgets.canvas import Canvas
        from models.widgets.character import Character
        from models.widgets.timeline import Timeline
        from models.widgets.map import Map

        if directory_path is None:
            directory_path = self.data.get('content_directory_path',  '')


        match tag:
            case "chapter":
                widget = Chapter(title, self.p, directory_path, self)
                key = widget.data.get('key', '')
                self.chapters[key] = widget
                self.widgets.append(self.chapters[key])

            case "note":
                widget = Note(title, self.p, directory_path, self)
                key = widget.data.get('key', '')
                self.notes[key] = widget
                self.widgets.append(self.notes[key])

            case "canvas":
                widget = Canvas(title, self.p, directory_path, self)
                key = widget.data.get('key', '')
                self.canvases[key] = widget
                self.widgets.append(self.canvases[key])

            case "character":
                widget = Character(title, self.p, directory_path, self)
                key = widget.data.get('key', '')
                self.characters[key] = widget
                self.widgets.append(self.characters[key])

            case "timeline":
                widget = Timeline(title, self.p, directory_path, self)
                key = widget.data.get('key', '')
                self.timelines[key] = widget
                self.widgets.append(self.timelines[key])

            case "map":
                widget = Map(title, self.p, directory_path, self)
                key = widget.data.get('key', '')
                self.maps[key] = widget
                self.widgets.append(self.maps[key])
     
            case _:
                print("Widget tag not valid. Tag:", tag)

        # Apply the UI changes
        self.active_rail.content.reload_rail()
        self.workspace.reload_workspace()



    # Called clicking outside the menu to close it
    def close_menu(self, e=None):
        ''' Closes our right click menu when clicking outside of it '''
        
        self.p.overlay.clear()
        self.p.update()

        

    # Called when we right click our object on the tree view
    def open_menu(self, menu_options: list):
        ''' Pops open our menu options when right clicking an object on a rail '''

        if len(menu_options) == 0:
            return

        page_width = self.p.width
        page_height = self.p.height

        # Adjust mouse positions if the menu would go off screen
        if self.mouse_x + 120 > page_width:
            self.mouse_x -= 120
            #print(f"Adjusted Mouse X: {self.mouse_x}")
        if self.mouse_y + 90 > page_height:
            self.mouse_y -= 50
            #print(f"Adjusted Mouse Y: {self.mouse_y}")

        # Our container that contains a column of our options. Need to use container for positioning
        menu = ft.Container(
            left=self.mouse_x,     # Positions the menu at the mouse location
            top=self.mouse_y,
            border_radius=ft.border_radius.all(4),
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            width=120,
            shadow=ft.BoxShadow(color=ft.Colors.BLACK, blur_radius=2, blur_style=ft.ShadowBlurStyle.NORMAL,),
            content=ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=menu_options
            ),
        )

        # Outside gesture detector to close the menu when clicking outside the menu container
        outside_detector = ft.GestureDetector(
            expand=True,
            on_tap=self.close_menu,
            on_secondary_tap=self.close_menu,
        )

        # Overlay is a stack, so add the detector, then the menu container
        self.p.overlay.append(outside_detector)
        self.p.overlay.append(menu)
        self.p.update()


    # Called when new story object is created, either by program or by being loaded from storage
    def build_view(self) -> list[ft.Control]:
        ''' Builds our 'view' (page) that consists of our menubar, rails, and workspace '''
        from ui.menu_bar import create_menu_bar
        from ui.workspaces_rail import WorkspacesRail
        from ui.active_rail import Active_Rail
        from ui.workspace import Workspace
        from models.app import app

        page = self.p

        page.title = f"{self.title}"

        # Clear our controls in our view before building it
        self.controls.clear()

        # Create our page elements as their own pages so they can update
        self.menubar = create_menu_bar(page, self)

        # Create our rails and workspace objects
        self.workspaces_rail = WorkspacesRail(page, self)  # Create our all workspaces rail
        self.active_rail = Active_Rail(page, self)  # Container stored in story for the active rails
        self.workspace = Workspace(page, self)  # Reference to our workspace object for pin locations
        self.workspace.reload_workspace()  # Load our workspace here instead of in the workspace constructor

        # Called when hovering over resizer to right of the active rail
        def show_horizontal_cursor(e: ft.HoverEvent):
            ''' Changes the cursor to horizontal when hovering over the resizer '''

            e.control.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT
            e.control.update()

        # Called when resizing the active rail by dragging the resizer
        def move_active_rail_divider(e: ft.DragUpdateEvent):
            ''' Responsible for altering the width of the active rail '''

            if (e.delta_x > 0 and self.active_rail.width < page.width/2) or (e.delta_x < 0 and self.active_rail.width > 100):
                self.active_rail.width += int(e.delta_x)    # Apply the change to our rail
                
            page.update()   # Apply our changes to the rest of the page

        # Called when app stops dragging the resizer to resize the active rail
        def save_active_rail_width(e: ft.DragEndEvent):
            ''' Saves our new width that will be loaded next time app opens the app '''

            app.settings.data['active_rail_width'] = self.active_rail.width
            app.settings.save_dict()

            print("Active rail width: " + str(self.active_rail.width))

        # The actual resizer for the active rail (gesture detector)
        active_rail_resizer = ft.GestureDetector(
            content=ft.Container(
                width=10,   # Total width of the GD, so its easier to find with mouse
                
                # Thin vertical divider, which is what the app will actually drag
                content=ft.VerticalDivider(thickness=2, width=2, color=ft.Colors.OUTLINE_VARIANT),     # Original
                padding=ft.padding.only(right=8),  # Push the 2px divider ^ to the right side
            ),
            on_hover=show_horizontal_cursor,    # Change our cursor to horizontal when hovering over the resizer
            on_pan_update=move_active_rail_divider, # Resize the active rail as app is dragging
            on_pan_end=save_active_rail_width,  # Save the resize when app is done dragging
            drag_interval=10,
        )

        


        # Save our 2 rails, divers, and our workspace container in a row
        row = ft.Row(
            spacing=0,  # No space between elements
            expand=True,  # Makes sure it takes up the entire window/screen

            controls=[
                self.workspaces_rail,  # Main rail of all available workspaces
                ft.VerticalDivider(width=2, thickness=2, color=ft.Colors.OUTLINE_VARIANT),     
                
                self.active_rail,    # Rail for the selected workspace
                active_rail_resizer,   # Divider between rail and work area
                
                self.workspace,    # Work area for pagelets
            ],
        )

        # Views render like columns, so we add elements top-down
        self.controls = [self.menubar, row]

        page.update()

    