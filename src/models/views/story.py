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
from styles.snack_bar import Snack_Bar
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

        self.title = title.title()      # Gives our story a title when its created
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
                'characters_directory_path': os.path.join(data_paths.stories_directory_path, self.route, "characters"),
                'timelines_directory_path': os.path.join(data_paths.stories_directory_path, self.route, "timelines"),
                'world_building_directory_path': os.path.join(data_paths.stories_directory_path, self.route, "world_building"),
                'maps_directory_path': os.path.join(data_paths.stories_directory_path, self.route, "world_building", "maps"),
                'planning_directory_path': os.path.join(data_paths.stories_directory_path, self.route, "planning"),
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

        
        
        

        # Stories have required structures as well, so we verify they exist or we will error out
        # We also use this function to create most detailed structures from templates if newly created story
        self.verify_story_structure(template)  
            
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
        self.world_building: None       # World building widget that contains our maps, lore, governments, history, etc
        self.maps: dict = {}            # Maps created inside of world building

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

        # This also loads our canvas board images here, since they can be opened in either workspace
        self.load_content()

        # Loads our characters from file storage into our characters list
        self.load_characters()

        # Loads our timeline from file storage, which holds our timelines
        self.load_timelines()

        # Load our world building objects from file storage
        self.load_world_building()

        # Loads our maps from file storage
        #self.load_maps()

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
            self.p.open(Snack_Bar(f"Error saving story data: {e}"))

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

    def update_canvas_data(self, **kwargs):
        ''' Changes a key/value pair in our canvas_data dict and saves the json file '''
        # Called by:
        # story.update_canvas_data(**{'key': value, 'key2': value2})

        try:
            for key, value in kwargs.items():
                self.data['canvas_data'].update({key: value})

            self.save_dict()

        # Handle errors
        except Exception as e:
            print(f"Error changing canvas_data {key}:{value} for story {self.title}: {e}")
            

    # Called when a new story is created and not loaded with any data
    def verify_story_structure(self, template: str=None):
        ''' Creates our story folder structure inside of our stories directory '''


        # TODO: Try statements only when writing to files
        # On story first creation, add default folders inside content: chapters, notes, canvases, images
        # Inside characters: main, side, background

        try:

            is_new_story = self.data.get('is_new_story', True)

            # Sets our path to our story folder
            directory_path = os.path.join(data_paths.stories_directory_path, self.route)

            # Set our workspace folder structure inside our story folder
            required_story_folders = [
                "content",
                "characters",
                "timelines",
                "world_building",
                "planning",
            ]

            # Create the workspace folder strucutre above
            for folder in required_story_folders:
                folder_path = os.path.join(directory_path, folder)
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
            
            # Based on its tag, it deletes it from our appropriate dict
            if tag == "chapter":
                if widget.data['key'] in self.chapters.keys():
                    del self.chapters[widget.data['key']]

            elif tag == "note":
                if widget.data['key'] in self.notes.keys():
                    del self.notes[widget.data['key']]

            elif tag == "character":
                if widget.data['key'] in self.characters.keys():
                    del self.characters[widget.data['key']]

            elif tag == "timeline":
                if widget.data['key'] in self.timelines.keys():
                    del self.timelines[widget.data['key']]

            elif tag == "map":
                if widget.data['key'] in self.maps.keys():
                    del self.maps[widget.data['key']]

            
            # Remove from our master widgets list so it won't be rendered anymore
            if widget in self.widgets:
                self.widgets.remove(widget)
        
        # Call our internal functions above
        try:
            # If we can delete the file, we remove the live object
            file_path = os.path.join(widget.directory_path, f"{widget.title}.json")
            if widget.delete_file(file_path):

                _delete_live_widget(widget)

                # Reload our workspace to apply the UI Change if was needed
                if widget.visible:
                    self.workspace.reload_workspace()

                self.active_rail.content.reload_rail()
                self.close_menu()

                print(f"Successfully deleted widget: {widget.title}")

        # Errors
        except Exception as e:
            print(f"Error deleting widget : {e}")
            return


    # Called on story startup to load all our content objects
    def load_content(self):
        ''' Loads our content from our content folder inside of our story folder '''
        from models.widgets.note import Note
        from models.widgets.chapter import Chapter
        from models.widgets.canvas import Canvas

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
                            content_data = json.load(f)
                        
                        # Extract the title from the data
                        content_key = content_data.get("key", None)
                        content_title = content_data.get("title", filename.replace(".json", ""))

                        # Check our tag to see what type of content it is, and load appropriately
                        if content_data.get("tag", "") == "chapter":
                            
                            self.chapters[content_key] = Chapter(content_title, self.p, dirpath, self, content_data)
                            #print("Chapter loaded")

                        elif content_data.get("tag", "") == "image":
                            print("image tag found, skipping for now")

                        elif content_data.get("tag", "") == "canvas":
                            self.canvases[content_key] = Canvas(content_title, self.p, dirpath, self, content_data)

                        elif content_data.get("tag", "") == "note":
                            self.notes[content_key] = Note(content_title, self.p, dirpath, self, content_data)
                            
                        # Error handling for invalid tags
                        else:
                            print("content tag not valid, skipping", content_data.get("tag", ""))
                            return

                            
                    # Handle errors if the path is wrong
                    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                        print(f"Error loading content from {filename}: {e}")

        # Load animations -- TBD in future if possible

    # Called as part of the startup method during program launch
    def load_characters(self):
        ''' Loads all our characters from our characters folder and adds them to the live story object'''
        from models.widgets.character import Character
        
        # Check if the characters folder exists. Creates it if it doesn't. Handles errors on startup
        if not os.path.exists(self.data['characters_directory_path']):
            #print("Characters folder does not exist, creating it.")
            os.makedirs(self.data['characters_directory_path'])    
            return
        
        # Iterate through all files in the characters folder
        #for filename in os.listdir(data_paths.characters_path):
        for dirpath, dirnames, filenames in os.walk(self.data['characters_directory_path']):
            for filename in filenames:

                # All our objects are stored as JSON
                if filename.endswith(".json"):
                    file_path = os.path.join(dirpath, filename)   
                    #print("dirpath = ", dirpath)
                    
                    try:
                        # Read the JSON file
                        with open(file_path, "r", encoding='utf-8') as f:
                            character_data = json.load(f)
                        
                        # Extract the title from the data
                        character_key = character_data.get("key", None)
                        character_title = character_data.get("title", filename.replace(".json", ""))    # TODO Add error handling
                            
                        # Create our character object using our loaded data
                        self.characters[character_key] = Character(character_title, self.p, dirpath, self, character_data)
                        #self.widgets.append(self.characters[character_title])  # Add to our master list of widgets in our story
                    # Handle errors if the path is wrong
                    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                        print(f"Error loading character from {filename}: {e}")

    def get_character_names(self) -> list:
        '''Return a sorted list of character names.

        Prefers in-memory loaded Character objects (self.characters), but will
        fall back to reading the filenames in the characters directory so names
        are available even if characters haven't been instantiated yet.
        '''
        names = []
        try:
            # Use loaded character objects first
            if isinstance(self.characters, dict) and len(self.characters) > 0:
                for c in self.characters.values():
                    try:
                        t = getattr(c, 'title', None)
                        if t:
                            names.append(t)
                    except Exception:
                        continue

            # Fall back to files on disk for any names not already included
            path = self.data.get('characters_directory_path')
            if path and os.path.exists(path):
                for fname in os.listdir(path):
                    if fname.endswith('.json') and not fname.endswith('_display.json'):
                        name = os.path.splitext(fname)[0]
                        if name and name not in names:
                            names.append(name)

        except Exception as e:
            print(f"Error getting character names: {e}")

        # Return unique, sorted names
        try:
            return sorted(list(dict.fromkeys(names)))
        except Exception:
            return names

        

    # Called on story startup to create our plotline object.
    def load_timelines(self):
        ''' Creates our timeline object, which in turn loads all our plotlines from storage '''
        from models.widgets.timeline import Timeline
 
        # Check if the plotline folder directory exists. Creates it if it doesn't. 
        # Handles errors on startup if people delete this folder, otherwise uneccessary
        if not os.path.exists(self.data['timelines_directory_path']):
            #print("Plotline folder does not exist, creating it.")
            os.makedirs(self.data['timelines_directory_path'])    
            return
        
        # Iterate through all files in the timelines folder
        for dirpath, dirnames, filenames in os.walk(self.data['timelines_directory_path']):
            for filename in filenames:

                # All our objects are stored as JSON
                if filename.endswith(".json"):
                    file_path = os.path.join(dirpath, filename)   
                    #print("dirpath = ", dirpath)
                    
                    try:
                        # Read the JSON file
                        with open(file_path, "r", encoding='utf-8') as f:
                            timeline_data = json.load(f)
                        
                        # Extract the title from the data
                        timeline_key = timeline_data.get("key", None)
                        timeline_title = timeline_data.get("title", filename.replace(".json", ""))    
                            
                        # Create our timeline object using our loaded data
                        self.timelines[timeline_key] = Timeline(timeline_title, self.p, dirpath, self, timeline_data)
                        
                    # Handle errors if the path is wrong
                    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                        print(f"Error loading timeline from {filename}: {e}")
            
        
        # Create our plotline object with no data if story is new, or loaded data if it exists already
        if len(self.timelines) == 0:
            key = self.data['timelines_directory_path'] + "\\" + "Timeline 1"
            self.timelines[key] = Timeline(
                title="Timeline 1", 
                page=self.p, 
                directory_path=dirpath, 
                story=self, 
                data=None
            )

    # Called on story startup to load all our world building widget
    def load_world_building(self):
        ''' Loads our world object from storage, or creates a new one if it doesn't exist '''
        from models.widgets.world_building import World_Building
 
        # Check if the plotline folder exists. Creates it if it doesn't. 
        if not os.path.exists(self.data['world_building_directory_path']):
            #print("Plotline folder does not exist, creating it.")
            os.makedirs(self.data['world_building_directory_path'])    
        
        # Construct the path to plotline.json
        world_building_json_path = os.path.join(self.data['world_building_directory_path'], 'World_Building.json')

        # Set data blank initially
        world_building_data = None
        
        # Attempt to open and read the plotline.json file. Sets our stored data if successful
        try:
            with open(world_building_json_path, 'r', encoding='utf-8') as file:
                world_building_data = json.load(file)
            
        except Exception as e:
            print("Error loading world building data: ", e)
          
        
        # Create our world object with no data if story is new, or loaded data if it exists already
        self.world_building = World_Building(
            "World_Building", 
            self.p, 
            self.data['world_building_directory_path'], 
            self, 
            world_building_data
        )

    # Called in constructor
    def load_maps(self):
        ''' Loads our world maps from our dict into our live object '''
        from models.widgets.map import Map
        
        try: 
            
            # Set the directory path to our maps
            map_dir_path = os.path.join(self.data['world_building_directory_path'], "maps")
            
            # Make sure it exists to handle errors
            if not os.path.exists(map_dir_path):
                os.makedirs(map_dir_path)    
                return
            
            # Iterate through all files in our maps folder
            for dirpath, dirnames, filenames in os.walk(map_dir_path):
                for filename in filenames:

                    # Go through our files, and don't include the display files
                    if filename.endswith(".json") and not filename.endswith("_display.json"):
                        file_path = os.path.join(dirpath, filename)   
                        #print("dirpath = ", dirpath)
                        
                        try:
                            # Read the JSON file
                            with open(file_path, "r", encoding='utf-8') as f:
                                map_data = json.load(f)
                            
                            # Extract the title from the data
                            map_key = map_data.get("key", None)
                            map_title = map_data.get("title", filename.replace(".json", ""))    
                                
                            # Create our Map widgets.
                            # TODO: Add in loading fathers? or get that from data inside of map constructor??
                            self.maps[map_key] = Map(
                                title=map_title, 
                                page=self.p, 
                                directory_path=dirpath, 
                                story=self, 
                                data=map_data
                            )
                            
                            
                        # Handle errors if the path is wrong
                        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                            print(f"Error loading map from {filename}: {e}")
                
            
            # If we have no maps, create a default one to get started
            if len(self.maps) == 0:
                #print("No world maps found, creating default world map")
                self.create_map(title="World Map", father=None, category="world")

            #print(f"Loaded {len(self.maps)} maps into story '{self.title}'")

        # Catch errors
        except Exception as e:
            print(f"Error loading maps: {e}")

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
        


    # Called to create a new chapter
    def create_chapter(self, title: str, directory_path: str=None):
        ''' Creates a new chapter object, saves it to our live story object, and saves it to storage'''
        from models.widgets.chapter import Chapter

        # If no path is passed in, construct the full file path for the chapter JSON file
        if directory_path is None:   # There SHOULD always be a path passed in, but this will catch errors
            directory_path = self.data['content_directory_path']

        # Set the key
        key = directory_path + "\\" + title

        # Save the new chapter and add it to the widget list
        self.chapters[key] = Chapter(title, self.p, directory_path, self)
        self.widgets.append(self.chapters[key])

        # Apply the UI changes
        self.active_rail.content.reload_rail()
        self.workspace.reload_workspace()

    # Called to create a note object
    def create_note(self, title: str, directory_path: str=None):
        ''' Creates a new note object, saves it to our live story object, and saves it to storage'''
        from models.widgets.note import Note

        # If no path is passed in, construct the full file path for the note JSON file
        if directory_path is None:   # There SHOULD always be a path passed in, but this will catch errors
            directory_path = self.data['content_directory_path']
           
        # Set the key
        key = directory_path + "\\" + title

        # Save our new note and add it to the widget list
        self.notes[key] = Note(title, self.p, directory_path, self)
        self.widgets.append(self.notes[key]) 

        # Apply the UI changes
        self.active_rail.content.reload_rail()
        self.workspace.reload_workspace()

    # Called to create a canvas object
    def create_canvas(self, title: str, directory_path: str=None, data: dict=None):
        ''' Creates a new note object, saves it to our live story object, and saves it to storage'''
        from models.widgets.canvas import Canvas

        # If no path is passed in, construct the full file path for the note JSON file
        if directory_path is None:   # There SHOULD always be a path passed in, but this will catch errors
            directory_path = self.data['content_directory_path']
           
        # Set the key
        key = directory_path + "\\" + title

        # Format our data if we have any
        if data is not None:
            new_data = {'canvas_meta': data}

        # Save our new note and add it to the widget list
        self.canvases[key] = Canvas(title, self.p, directory_path, self, new_data)
        self.widgets.append(self.canvases[key]) 

        # Apply the UI changes
        self.active_rail.content_rail.reload_rail()
        self.workspace.reload_workspace()


    # Called to create a new character
    def create_character(self, title: str, directory_path: str=None):
        ''' Creates a new character object, saves it to our live story object, and saves it to storage'''
        from models.widgets.character import Character

        # If no path is passed in, construct the full file path for the character JSON file
        if directory_path is None:
            directory_path = self.data['characters_directory_path'] # There SHOULD always be a path passed in, but this will catch errors

        # Set the key
        key = directory_path + "\\" + title
        
        # Save our new character and add it to the widget list
        self.characters[key] = Character(title, self.p, directory_path, self)
        self.widgets.append(self.characters[key])  

        # Apply the UI changes
        self.active_rail.content.reload_rail()
        self.workspace.reload_workspace()

    # Called to create a timeline object
    def create_timeline(self, title: str):
        ''' Creates a new timeline and updates the UI. Doesn't need a directory path since its always the same '''
        from models.widgets.timeline import Timeline

        dirpath = self.data['timelines_directory_path']

        # Set the key
        key = dirpath + "\\" + title

        # Save our new timeline and add it to the widget list
        self.timelines[key] = Timeline(title, self.p, dirpath, self)
        self.widgets.append(self.timelines[key])  

        # Apply the UI changes
        self.active_rail.content.reload_rail()
        self.workspace.reload_workspace()

    # Called to create a map object
    def create_map(self, title: str, directory_path: str=None, father: str=None, category: str=None):
        ''' Creates a new map object, saves it to our live story object, and saves it to storage'''
        from models.widgets.map import Map

        # Path to where all our maps are stored
        if directory_path is None:

            # If multi planetary, save it in our worlds folder
            if self.data['settings']['multi_planetary']:
                directory_path = os.path.join(self.data['world_building_directory_path'], "maps", "worlds")
            # Otherwise just save it in the maps folder
            else:
                directory_path = os.path.join(self.data['world_building_directory_path'], "maps")

        # Set the key
        key = directory_path + "\\" + title

        # Create our new map object in our maps dict
        self.maps[key] = Map(
            title=title, 
            page=self.p, 
            directory_path=directory_path, 
            story=self,
            father=father,
            category=category,
            data=None
        )

        # Add to our master list of widgets in our story
        self.widgets.append(self.maps[key]) 

        # Reload our UI's
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
        from ui.workspaces_rail import Workspaces_Rail
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
        self.workspaces_rail = Workspaces_Rail(page, self)  # Create our all workspaces rail
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

    