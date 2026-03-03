''' 
UI element for our Menu bar at the top of the page (file, edit, etc)
Holds our settings icon, feedback, and account name as well
'''

import flet as ft
from models.app import app
from models.views.story import Story
from utils.check_story_unique import story_is_unique
from styles.snack_bar import SnackBar



# Called in main to create menu bar if no story exists, or by a story to create menu bar for that story
def create_menu_bar(page: ft.Page, story: Story = None) -> ft.Container:


    def _rename_clicked(e):
        # Should pop open dialog to rename current story
        pass


    # Called when file -> new is clicked
    def _create_new_story_clicked(e):
        ''' Opens a dialog to create a new story. Checks story is unique or not '''


        # Variable to track if the title is unique
        is_unique = True

        def submit_new_story(e):
            ''' Creates a new story with the given title '''

            # Import our variable if it is unique or nah
            nonlocal is_unique

            if isinstance(e, ft.TextField):
                #print("Received the text field. title is e.value")
                title = e.value
            else:
                #print("received the event, title is e.control.value")
                title = e.control.value

            print(title)

            for story in app.stories.values():
                if story.title == title:
                    is_unique = False
                    break

            # Check if the title is unique
            if is_unique:
                #print("title is unique, story being created: ", title)
                app.create_new_story(title, page, "default") # Needs the story object
                dlg.open = False
                page.update()
            else:
                #print("Title not unique, no story created")
                story_title_field.error_text = "Title must be unique"
                story_title_field.focus()   # refocus the text field since the title was not unique
                page.update()


        # Called everytime the user enters a new letter in the text box
        def textbox_value_changed(e):
            ''' Called when the text in the text box changes '''

            nonlocal is_unique

            is_unique = story_is_unique(e.control.value, e.control)

            if is_unique and e.control.value.strip() != "":
                create_button.disabled = False
            else:
                create_button.disabled = True
                
            page.update()


        # Create a reference to the text field so we can access its value
        story_title_field = ft.TextField(
            label="Story Title",
            autofocus=True, capitalization=ft.TextCapitalization.SENTENCES,
            on_submit=submit_new_story,
            on_change=textbox_value_changed,
        )

        create_button = ft.TextButton("Create", on_click=lambda e: submit_new_story(story_title_field), disabled=True)

            
        # The dialog that will pop up whenever the new story button is clicked
        dlg = ft.AlertDialog(

            # Title of our dialog
            title=ft.Text(
                "Create New Story", 
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),

            # Main content is text box for user to input story title
            content=story_title_field,

            # Our two action buttons at the bottom of the dialog
            actions=[
                ft.TextButton("Cancel", on_click=page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                create_button,
            ],
        )
        
        # Add cancel button. Sometimes adding it ^^ first breaks and idk y
        dlg.actions.insert(0, ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR)))

        # Open our dialog in the overlay
        page.show_dialog(dlg)


    # Called when file -> open is clicked
    def _open_clicked(e):
        ''' Opens a dialog to open an existing story '''

        #print("Open Story Clicked")

        selected_story = None

        # Called when a new story text button is clicked
        def change_selected_story(e):
            ''' Changes our selected story variable '''

            nonlocal selected_story
            selected_story = e.control.value
            open_button.disabled = False
            open_button.style=ft.ButtonStyle(color=ft.Colors.ON_SURFACE)
            page.update()

        # Returns a list of all story titles available to open
        def get_stories_list() -> ft.Control:
            ''' Returns a list of all story titles available to open '''

            # List of our story choices
            stories = []

            # Set style for our options
            style = ft.TextStyle(
                size=14,
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            )

            # Use something better than radio in future, but for now this works
            for story in app.stories.values():
                stories.append(
                    ft.Radio(expand=False, value=story.title, label=story.title, label_style=style)
                )

            # Return our list of stories
            return stories


        # Called when the 'open' button is clicked in the bottom right of the dialog
        async def open_selected_story(e=None):
            ''' Changes the route to the selected story '''

            #print("Open button clicked, selected story is: ", selected_story)

            if selected_story is not None:
                print("Opening story: ", selected_story)
                await page.push_route(app.stories[selected_story].route)
                app.settings.story = app.stories[selected_story]  # Gives our settings widget the story reference it needs
                page.pop_dialog()
                page.update()
            else:
                print("No story selected")

            page.pop_dialog()
            page.update()

        open_button = ft.TextButton("Open", on_click=open_selected_story, disabled=True)


        # Our alert dialog that pops up when file -> open is clicked
        dlg = ft.AlertDialog(
            title=ft.Text(
                "What story would you like to open?",
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            content=ft.RadioGroup(
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=False, controls=get_stories_list()),
                on_change=change_selected_story
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                open_button,
            ]
        )

        # Opens our dialog
        page.show_dialog(dlg)

    async def _settings_clicked(e=None):
        ''' Goes to the settings page '''
        if page.route != "/settings":
            await page.push_route("/settings")
            print("Pushed settings route")
        else:
            # Get the active story title and find its route
            if story is not None:
                

                await page.push_route(story.route)
                print("Pushing story route: ", story.route)
            else:
                await page.push_route("/")
                print("Pushing home route")


    # Styling used by lots of menu bar items
    menubar_style = ft.ButtonStyle(
        #bgcolor={ft.ControlState.HOVERED: ft.Colors.TRANSPARENT},
        shape=ft.RoundedRectangleBorder(radius=10),
        color=ft.Colors.PRIMARY
    )

    # Create our menu bar with submenu items
    menubar = ft.MenuBar(
        expand=True,
        style=ft.MenuStyle(     # Styling our menubar
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.TRANSPARENT,
            shadow_color=ft.Colors.TRANSPARENT,
            mouse_cursor={
                ft.ControlState.HOVERED: ft.MouseCursor.WAIT,
                ft.ControlState.DEFAULT: ft.MouseCursor.ZOOM_OUT,
            },
        ),
        controls=[  # The controls shown in our menu bar from left to right
            ft.SubmenuButton(   # Button that opens a subment
                content=ft.Container(
                    content=ft.Text("File", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),     # Content of subment button
                    alignment=ft.Alignment.CENTER
                ), 
                #style=menubar_style,    # styling for the button
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10),),
                menu_style=ft.MenuStyle(padding=ft.Padding.all(0)),
                
                controls=[      # The options shown inside of our button
                    ft.MenuItemButton(
                        content=ft.Text("New Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        # Options: Blank Story, From Template, but clicking also just creates blank
                        leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, color=ft.Colors.ON_SURFACE,),
                        style=menubar_style,
                        on_click=_create_new_story_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Open Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.MENU_BOOK_OUTLINED),
                        style=menubar_style,
                        on_click=_open_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Rename Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.EDIT_OUTLINED),
                        style=menubar_style,
                        on_click=_rename_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Upload", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        # Options: story, chapter, map, drawing, character, note
                        leading=ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED),
                        style=menubar_style,
                        on_click=_open_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Export", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        # Options: story, chapter, map, drawing, character, note
                        leading=ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED),
                        style=menubar_style,
                        on_click=_open_clicked,
                    ),
                    
                    ft.MenuItemButton(
                        content=ft.Text("Settings", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED),
                        style=menubar_style,
                        on_click=_settings_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Delete Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.DELETE_FOREVER_ROUNDED),
                        style=menubar_style,
                        #on_click=_delete_clicked,
                    ),
                ],
            ),
        ], 
    )

    
        
    # Return our formatted menubar
    return ft.Container(
        border=ft.Border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        content=ft.Row(
            spacing=0,
            controls=[
                menubar,    # Menubar on left
                ft.Container(expand=True),  # empty space in middle of menubar
                # Fix broken widgets button

                ft.Text(
                    "Beta", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, 
                    tooltip="Storyboard is currently in beta. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                ),  # Feedback button
                ft.Icon(ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, tooltip="Storyboard is currently in beta. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."),
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, "primary", on_click=_settings_clicked, mouse_cursor=ft.MouseCursor.CLICK),   # Settings button
            ]
        )
    )
