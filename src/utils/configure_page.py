import flet as ft


# Called once from AppView, after a page exists (ft.context.page is only valid inside a Flet callback/render)
def configure_page(app, settings, page: ft.Page):
    ''' Applies our loaded settings to the current page (title, theme, window size, fonts, event handlers) '''

    # Sets our app title
    page.title = "StoryBoard (alpha)"

    # Sets our themes and which one we use. Default to dark mode with blue
    page.theme = ft.Theme(color_scheme_seed=settings.theme_color)  
    page.dark_theme = ft.Theme(color_scheme_seed=settings.theme_color) 
    page.theme_mode = settings.theme_mode  
    # Sets the title of our app, padding, and maximizes the window
    #page.padding = ft.Padding.only(top=0, left=0, right=0, bottom=0)    

    # Set the window size as maximized or not
    if settings.window_maximized:
        page.window.maximized = True
    else:

        width = settings.window_width
        height = settings.window_height

        if width is not None:
            page.window.width = width
        if height is not None:
            page.window.height = height

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

                # TODO: Check other contexts and save them

            # Save the story if it has unsaved widgets between last auto save and close
            if page.route.startswith("stories"):
                story_id = page.route.split("/")[-1]
                story = app.stories.get(story_id)
                if story:
                    #settings.story.block_page()    # Block the page to show us loading the saves
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
        #"Pacifico": "/fonts/Pacifico-Regular.ttf",
        #"Ibarra Real Nova": "/fonts/IbarraRealNova-VariableFont_wght.ttf",
        #"Nunito": "/fonts/Nunito-VariableFont_wght.ttf",
        "Roboto": "/fonts/Roboto-VariableFont_wght.ttf",
    }       

    page.navigate(settings.route)
    return

    # Load our custom fonts
    for saved_font in settings.data.get('text_options', {}).get('fonts', []):
        font_name = saved_font.get('font_name')
        file_name = saved_font.get('file_name')
        if font_name and file_name:
            page.fonts[font_name] = f"/fonts/{file_name}"

    # Will load the most recent route. This loads the story if it was the last route
    page.navigate(settings.data.get('page', {}).get('route', None))