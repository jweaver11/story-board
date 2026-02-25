'''
Our model for our app. Contains settings and stories, as well as methods to load them from files on startup (called in main)
'''

from models.views.story import Story
import flet as ft
import os
import json
from models.widget import Widget


class App:

    # Constructor
    def __init__(self):

        # Declares settings and workspace rail here, but we create/load them later in main
        self.settings: Widget = ft.Container()
        
        # Dict of all our stories.
        self.stories = {}

    # Called on app startup in main
    def load_settings(self, page: ft.Page):
        ''' Loads our settings from a JSON file into our rendered settings control. If none exist, creates default settings '''
        from models.views.settings import Settings
        from models.app import app
        from constants import data_paths

        # Should just look for our settings file to load our data from. Settings should do all other logic

        # Path to our settings file
        settings_file_path = os.path.join(data_paths.app_data_path, "settings.json")

        # Create settings.json with empty dict if it doesn't exist
        if not os.path.exists(settings_file_path):
            with open(settings_file_path, "w", encoding='utf-8') as f:
                json.dump({}, f)
        
        try:
            # Read the JSON file
            with open(settings_file_path, "r", encoding='utf-8') as f:
                settings_data = json.load(f)

        # If no file exists, create one with default settings
        except(FileNotFoundError):
            print("Settings file not found, creating default settings.")
            settings_data = None  # If there's an error, we will create default settings
                
        # Other errors
        except Exception as e:
            print(f"Error loading settings {settings_file_path}: {e}")
            settings_data = None  # If there's an error, we will create default settings

        # Sets our app settings to our loaded settings. If none were loaded (I.E. first launch), Settings with create its own defaults
        app.settings = Settings(page=page, file_path=settings_file_path, data=settings_data)


        ''' Page styling '''

        # Sets our app title
        page.title = "StoryBoard"

        # Sets our themes and which one we use. Default to dark mode with blue
        page.theme = ft.Theme(color_scheme_seed=app.settings.data.get('theme_color', "blue"))    
        page.dark_theme = ft.Theme(color_scheme_seed=app.settings.data.get('theme_color', "blue"))   
        page.theme_mode = app.settings.data.get('theme_mode', 'dark')      
    
        # Sets the title of our app, padding, and maximizes the window
        page.padding = ft.padding.only(top=0, left=0, right=0, bottom=0)    

        # Set the window size as maximized or not
        if app.settings.data.get('page_is_maximized', True):
            page.window.maximized = app.settings.data.get('page_is_maximized', True)
        else:
            page.window.width = app.settings.data.get('page_width')
            page.window.height = app.settings.data.get('page_height')

        # Set our logic when page window is resized
        page.on_resized = app.settings._page_resized


      # Called on app startup in main
    async def load_previous_story(self, page: ft.Page):
        ''' Loads our saved stories from the json files in story folders within the stories directory. If none exist, do nothing '''
        
        from constants import data_paths
        from models.app import app
        
        # Create the stories directory if it doesnt exist already
        os.makedirs(data_paths.stories_directory_path, exist_ok=True)
            
        # Iterate through all items in the stories directory
        for story_folder in os.listdir(data_paths.stories_directory_path):

            story_directory = os.path.join(data_paths.stories_directory_path, story_folder)
                
            # Look for JSON files within this story folder (ignore subdirectories)
            try:
                
                # Check every item (folder and file) in this story folder
                for item in os.listdir(story_directory):

                    # Check for the story json data file. If it is, we'll load our story around this file data
                    if item.endswith(".json"):

                        # Set the file path to this json file so we can open it
                        file_path = os.path.join(story_directory, item)

                        # Read the JSON file
                        with open(file_path, "r", encoding='utf-8') as f:
                            # Set our data to be passed into our objects
                            story_data = json.load(f)

                        # Our story title is the same as the folder
                        story_title = story_data.get("title", file_path.replace(".json", ""))
                            
                        app.stories[story_title] = Story(story_title, page, data=story_data)

                        break
                    # Else, continue through the next story folder
                    else:
                        continue
                        
            except Exception as e:
                print(f"Error loading story {story_title}: {e}. May not be a directory")
            

        # Initialize and load all our stories data and UI elements
        for story in app.stories.values():
            
            # Sets our active story to the page route. The route change function will load the stories data and UI
            if story.route == app.settings.data.get('active_story', None):
                app.settings.story = story  # Gives our settings widget the story reference it needs
                await page.push_route(story.route)
                return
                
            
        # Give us home view if no stories were active
        #print("Page route is: ", page.route)
        await page.push_route("/home")

    
    
    # Called when app creates a new story. Accepts our title, page reference, a template, and a type
    def create_new_story(self, title: str, page: ft.Page, template: str) -> Story:
        ''' Creates the new story object and has it run its 'startup' method. Changes route so our view displays the new story '''

        # TODO: Add a type to accept for novel/comic
        
        story = Story(title.title(), page, data=None, template=template)
        
        # Create a new story object and add it to our stories dict
        self.stories[title.title()] = story

        print("new story route:", story.route)

        # Opens this new story as the active one on screen
        page.go(story.route)
        self.settings.data['active_story'] = story.route
        self.settings.story = story
        self.settings.save_dict()

        
    
# Sets our global app object that main uses and some functions call
app = App()

