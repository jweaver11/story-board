'''
The main file to run the application.
Initializes the app, settings, page data, and renders our UI onto the page
'''

import flet as ft
from models.app import app
from utils.route_change import route_change
from models.views.home import create_home_view
from models.views.loading import create_loading_view
from models.views.welcome import create_welcome_view, animate_welcome_text


# Main function
async def main(page: ft.Page):
    
    # Load settings and previous story (if one exists)
    app.load_settings(page)  
 
    # Either welcome to storyboard view, or our loading view
    if app.settings.data.get("is_first_launch", True):
        # Create the view and add it the page
        welcome_view = create_welcome_view(page)
        page.views.append(welcome_view)     # Add welcome view to the page
        page.update()

        # Grab our text and begin animating it
        text = welcome_view.controls[1]   
        await animate_welcome_text(text)  

        # Grab our progress ring and show it
        progress_ring = welcome_view.controls[2]
        progress_ring.opacity = 1.0
        progress_ring.update()

        # Make sure we don't run the welcome view again
        app.settings.data["is_first_launch"] = False
        app.settings.save_dict()

    # Otherwise they are not new to storyboard, show our loading view
    else:
        page.views.append(create_loading_view(page))
        page.update()
 
    # Set our route change function to be called on route changes
    page.on_route_change = route_change 
 
    # If a previous story was loaded, we load its route/view here
    app.load_previous_story(page)       
 
    # I no story was loaded, Give us a basic home view
    if page.route == "/":
        page.views.append(create_home_view(page))   # Simple view so we just use a function, not a class
        page.update()

# Runs the app
ft.app(main)