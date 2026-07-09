import flet as ft
from models.views.story import Story
from styles.snack_bar import SnackBar
import asyncio
from utils.tutorial import run_tutorial

# Called whenever a new story is laoded
async def route_change(e: ft.RouteChangeEvent) -> Story:
    ''' Handles changing our page view based on the new route '''
    from models.app import app
    from models.views.home import create_home_view
    from models.views.loading import create_loading_view

    # Grabs our page from the event for easier reference
    page: ft.Page = e.page

    # Clear our views and any existing overlay controls
    page.views.clear()
    page.overlay.clear()

    
    match page.route:
        case "/":
            # Append the view manually since its just a function to return the view
            page.views.append(create_home_view(page))
            page.update()
            return
        case "/home":
            # Append the view manually since its just a function to return the view
            page.views.append(create_home_view(page))
            page.update()
            return
        case "/settings":
            #app.settings.reload_settings()
            page.views.append(app.settings)
            page.update()
            return
        case "/loading":
            page.views.append(create_loading_view(page))
            page.update()
            return
        case "/tutorial":
            tutorial_story = Story("Tutorial Story")
            page.views.append(tutorial_story)
            page.update()
            # Add tutorial elements to the overlay
            page.overlay.extend(run_tutorial(tutorial_story))
            page.update()
            return
        case _:
            # Otherwise its a story route, so we need to find which one it is      
            # new_story = None    # Set new story to none intially to handle routes that don't match any stories

            # Run through our stories and see which ones route matches our new route
            for story in app.stories.values():
                # If it matches, set our new story 
                if story.route == page.route:
                    new_story = story
                    app.settings.update_data(**{'page': {'route': story.route}})
                    app.settings.story = story

                    app.settings.story = new_story  # Gives our settings widget the story reference it needs
                    page.views.append(new_story)
                    page.update() 
                    return
                
            
            # If theres an error loading the story, go to home view
            page.views.append(create_home_view(page))
            page.update()
            page.show_dialog(SnackBar(f"Error loading story for route: {page.route}"))     
            return