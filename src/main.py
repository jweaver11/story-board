'''
The main file to run the application.
Initializes the app, settings, page data, and renders our UI onto the page
'''

import flet as ft
from models.app import app
from utils.route_change import route_change
from models.views.home import create_home_view
from models.views.loading import create_loading_view



# Main function
def main(page: ft.Page):

    # Set loading view here if we want to use one
    # Our loading view while we setup the app
    page.views.append(create_loading_view(page))
    page.update()

    # Set our route change function to be called on route changes
    page.on_route_change = route_change 

    # Load settings and previous story (if one exists)
    app.load_settings(page)             
    app.load_previous_story(page)       # If a previous story was loaded, we load its route/view here

    # If route is default/home (No story was loaded), create a view for that
    if page.route == "/":
        
        page.views.append(create_home_view(page))   # Simple view so we just use a function, not a class
        page.update()

# Runs the app
ft.app(main)