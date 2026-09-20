'''
Our model for our app. Contains settings and stories, as well as methods to load them from files on startup (called in main)
'''

from models.views.story import Story, StoryView
from models.views.home import HomeView
from models.views.settings import SettingsView
from models.views.loading import LoadingView
import flet as ft
import os
import json
import asyncio
from utils.route_change import route_change
from constants import SETTINGS_FILE_PATH, STORIES_DIRECTORY_PATH
from dataclasses import dataclass
from models.views.settings import Settings

@ft.observable
@dataclass
class App:

    # Constructor
    def __init__(self):

        # Dict of all our stories.
        self.stories = {}
        self.ignore_settings_change = True  # Ignore settings changes when page is loading itself and saving incorrect changes

    # Called once from AppView, after a page exists (ft.context.page is only valid inside a Flet callback/render)
    def configure_page(self, settings, page: ft.Page):
        ''' Applies our loaded settings to the current page (title, theme, window size, fonts, event handlers) '''

        # Sets our app title
        page.title = "StoryBoard (alpha)"

        # Sets our themes and which one we use. Default to dark mode with blue
        page.theme = ft.Theme(color_scheme_seed=settings.data.get('page', {}).get('theme_color', "blue"))  
        page.dark_theme = ft.Theme(color_scheme_seed=settings.data.get('page', {}).get('theme_color', "blue")) 
        page.theme_mode = settings.data.get('page', {}).get('theme_mode', "dark")  # Default to dark mode
    
        # Sets the title of our app, padding, and maximizes the window
        #page.padding = ft.Padding.only(top=0, left=0, right=0, bottom=0)    

        # Set the window size as maximized or not
        if settings.data.get('page', {}).get('is_maximized', False):
            page.window.maximized = True
        else:

            width = settings.data.get('page', {}).get('width', 1920)
            height = settings.data.get('page', {}).get('height', 1080)
            left = settings.data.get('page', {}).get('left', 0)
            top = settings.data.get('page', {}).get('top', 0)
            if width is not None:
                page.window.width = width
            if height is not None:
                page.window.height = height
            if left is not None:
                page.window.left = left
            if top is not None:
                page.window.top = top


        # Set our logic when page window is resized
        page.on_resize = settings.page_resized

        # Intercept the close event BEFORE the window tears down so canvas.capture() still works.
        # prevent_close stops the OS from closing the window immediately; we close manually after saving.
        page.window.prevent_close = True

        # Intercept the close event BEFORE the window tears down so canvas.capture() still works.
        async def _on_window_event(e: ft.WindowEvent):
            if e.type == ft.WindowEventType.CLOSE:
                # Save the settings upon close if they have changed between last auto save and close
                if settings:
                    await settings.save_file()  

                # Save the story if it has unsaved widgets between last auto save and close
                if page.route.startswith("stories"):
                    story_id = page.route.split("/")[-1]
                    story = self.stories.get(story_id)
                    if story:
                        #settings.story.block_page()    # Block the page so we are loading
                        await settings.save_story()
                    
                page.window.prevent_close = False
                await page.window.destroy()

        # Set size and route change events
        page.window.on_event = _on_window_event
        #page.on_route_change = route_change 

        

        #print("Settings loaded with data: ", app.settings.data)
        page.fonts = {
            "Arial": None,
            "Open Sans": "/fonts/OpenSans-VariableFont_wdth,wght.ttf",
            "Pacifico": "/fonts/Pacifico-Regular.ttf",
            "Ibarra Real Nova": "/fonts/IbarraRealNova-VariableFont_wght.ttf",
            "Nunito": "/fonts/Nunito-VariableFont_wght.ttf",
            "Roboto": "/fonts/Roboto-VariableFont_wght.ttf",
        }       

        # Load our custom fonts
        for saved_font in settings.data.get('text_options', {}).get('fonts', []):
            font_name = saved_font.get('font_name')
            file_name = saved_font.get('file_name')
            if font_name and file_name:
                page.fonts[font_name] = f"/fonts/{file_name}"

        # Will load the most recent route. This loads the story if it was the last route
        page.navigate(settings.data.get('page', {}).get('route', None))


    # Called on app startup in main
    def load_stories(self):
        ''' Loads our saved stories from the json files in story folders within the stories directory. If none exist, do nothing '''

        # Create the stories directory if it doesnt exist already
        os.makedirs(STORIES_DIRECTORY_PATH, exist_ok=True)
            
        # Iterate through all items in the stories directory
        for story_folder in os.listdir(STORIES_DIRECTORY_PATH):

            story_directory = os.path.join(STORIES_DIRECTORY_PATH, story_folder)
            
                
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
                        story_id = story_data.get("id", file_path.replace(".json", ""))
                            
                        self.stories[story_id] = Story(story_title, story_data)
                        print("Loaded story:", story_id)

                        break
                    # Else, continue through the next story folder
                    else:
                        continue
                        
            except Exception as e:
                print(f"Error loading story {story_title}: {e}. May not be a directory")

        self.ignore_settings_change = False

    
    
    # Called when app creates a new story. Accepts our title, page reference, a template, and a type
    def create_new_story(self, title: str, page: ft.Page) -> Story:
        ''' Creates the new story object and has it run its 'startup' method. Changes route so our view displays the new story '''
        
        story = Story(title)
        page.run_task(story.save_file)  # Save it to data
        
        # Create a new story object and add it to our stories dict
        self.stories[story.data.get('id')] = story

        # Opens this new story as the active one on screen
        asyncio.create_task(page.push_route(story.route))
        self.settings.update_data(**{'page': {'route': story.route}})
        self.settings.story = story

# Called on app startup in main
def load_settings():
    ''' Loads our settings from a JSON file into our rendered settings control. If none exist, creates default settings '''
    

    # Should just look for our settings file to load our data from. Settings should do all other logic

    # Path to our settings file
    

    # Create settings.json with empty dict if it doesn't exist
    if not os.path.exists(SETTINGS_FILE_PATH):
        os.makedirs(os.path.dirname(SETTINGS_FILE_PATH), exist_ok=True)  # Ensure directory exists
        with open(SETTINGS_FILE_PATH, "w", encoding='utf-8') as f:
            json.dump({}, f)
    
    try:
        # Read the JSON file
        with open(SETTINGS_FILE_PATH, "r", encoding='utf-8') as f:
            settings_data = json.load(f)

    # If no file exists, create one with default settings
    except(FileNotFoundError):
        print("Settings file not found, creating default settings.")
        settings_data = None  # If there's an error, we will create default settings
            
    # Other errors
    except Exception as e:
        print(f"Error loading settings {SETTINGS_FILE_PATH}: {e}")
        settings_data = None  # If there's an error, we will create default settings

    # Sets our app settings to our loaded settings. If none were loaded (I.E. first launch), Settings with create its own defaults
    return Settings(data=settings_data)

# View for errors, should be impossible
@ft.component
def ErrorView() -> ft.View:
    return ft.View(
        [ft.Text("An error has occurred.")]
    )

# Handles a view for a story, and loads that story and returns its view
# Only called when route starts with 'stories/'
@ft.component
def StoryRoute(app, settings) -> ft.View:

    # Grab current route and extract the story ID from it
    current_route = ft.context.page.route
    story_id = current_route.split("/")[-1]  

    print("Story Route called:", current_route)

    # See where the story exists in the apps dictionary, and return its view
    if story_id in app.stories:
        story = app.stories[story_id]
        #ft.context.page.overlay = []
        return StoryView(app, settings, story)
    
    # Return errors
    return ft.View(
        [ft.Text("Error loading story")]
    )

@ft.component
def AppView() -> list[ft.Control]:

    # Give us an app and settings object globally
    app, _ = ft.use_state(App())
    settings, _ = ft.use_state(load_settings())
    page = ft.context.page  # Grab the page so we can configure it

    # use_state subscribes AppView to every change on app/settings (both @ft.observable), so
    # running these directly in the render body re-navigates and re-scans stories on EVERY
    # settings/app mutation anywhere in the app (e.g. each pixel of a drag). Run them once on mount instead.
    def _initialize():
        app.load_stories()  # Load all stories based on the current settings
        app.configure_page(settings, page)  # Will load last route based on settings

    ft.use_effect(_initialize, dependencies=[])

    # Set thr router to handle routing for the app
    return ft.Router(
        [
            ft.Route(index=True, component=lambda: HomeView(app, settings)),
            ft.Route("loading", component=LoadingView),
            ft.Route("settings", component=lambda: SettingsView(app, settings, None)),
            #ft.Route(path="tutorial", component=lambda: TutorialView()),
            ft.Route("stories/:story_id", component=lambda: StoryRoute(app, settings))
        ],
        not_found=ErrorView(),
        manage_views=True
    )

# OLD -- PHASE OUT
app = App()


