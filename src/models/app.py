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
from contexts.constants import SETTINGS_FILE_PATH, STORIES_DIRECTORY_PATH
from dataclasses import dataclass, field
from models.views.settings import AppSettings
from contexts.contexts import AppContext, AppSettingsContext, PaintContext, DrawingContext, TextContext
from utils.context_loader import load_app_settings, load_paint_settings, load_drawing_settings, load_text_settings
from utils.configure_page import configure_page
from utils.stories_loader import load_stories


@ft.observable
@dataclass
class App:

    # Dict of all our stories.
    stories: dict[Story] = field(default_factory=dict)
    ignore_settings_change: bool = True  # Ignore settings changes when page is loading itself and saving incorrect changes based on premature event firings

    
    # Called when app creates a new story. Accepts our title, page reference, a template, and a type
    def create_story(self, title: str) -> Story:
        ''' Creates the new story object and has it run its 'startup' method. Changes route so our view displays the new story '''

        settings = ft.use_context(settings)     # Grab our context
        story = Story(title)    # Create our story
        ft.context.page.run_task(story.save_file)  # Save story to data

        # Create a new story object and add it to our stories dict
        self.stories[story.id] = story

        # Load our new route and set the settings route so it saves to data
        ft.context.page.navigate(story.route)
        settings.route = story.route

# View for errors, should be impossible
@ft.component
def ErrorView() -> ft.View:
    return ft.View(
        [ft.Text("An error has occurred within the router")]
    )

# Handles a view for a story, and loads that story and returns its view
# Only called when route starts with 'stories/'
@ft.component
def StoryRoute() -> ft.View:

    # Grab current route and extract the story ID from it
    current_route = ft.context.page.route
    app = ft.use_context(AppContext)
    story_id = current_route.split("/")[-1]  

    # See where the story exists in the apps dictionary, and return its view
    if story_id in app.stories:
        story = app.stories[story_id]

        #ft.context.page.overlay = []

        # Returns our story view with needed contexts
        return StoryView(story)
    
    # Return errors
    return ft.View(
        [ft.Text("Error loading story")]
    )

@ft.component
def AppView() -> list[ft.Control]:

    # Give us an app and settings state objects that we will attach to our context.
    app, _ = ft.use_state(App())
    settings, _ = ft.use_state(load_app_settings())

    
    paint_settings, _ = ft.use_state(load_paint_settings())
    drawing_settings, _ = ft.use_state(load_drawing_settings())
    text_settings, _ = ft.use_state(load_text_settings())


    #print(settings.route)
    
    page = ft.context.page  # Grab the page so we can configure it easier

    # Load our stories into the app dict, and configure the page
    def _initialize():
        load_stories(app)  # Load all stories based on the current settings
        configure_page(app, settings, page)  # Will load last route based on settings

    ft.use_effect(_initialize, dependencies=[])

    # Build the router that will handle which view to display based on the current route
    @ft.component
    def build_router():


        return ft.Router(
            [
                ft.Route(index=True, component=HomeView),
                ft.Route("loading", component=LoadingView),
                ft.Route("settings", component=SettingsView),
                #ft.Route(path="tutorial", component=lambda: TutorialView()),
                ft.Route("stories/:story_id", component=StoryRoute)
            ],
            not_found=ErrorView(),
            manage_views=True
        )

    # Set the context available fore each component
    return AppContext(
        app,
        lambda: AppSettingsContext(
            settings, 
            lambda: PaintContext(
                paint_settings,
                lambda: DrawingContext(
                    drawing_settings,
                    lambda: TextContext(
                        text_settings,
                        build_router
                    )
                )
            )
        )
    )