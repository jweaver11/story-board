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

    def handle_submenu_open(e):
        pass
    def handle_submenu_close(e):
        pass
    def handle_submenu_hover(e):
        pass
    def handle_delete_click(e):
        # Should pop open dialog to confirm deletion, warning that it cannot be undone
        pass


    # Called when file -> new is clicked
    def handle_create_new_story_clicked(e):
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
                #ft.TextButton("Cancel", on_click=page.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                create_button,
            ],
        )
        
        # Add cancel button. Sometimes adding it ^^ first breaks and idk y
        dlg.actions.insert(0, ft.TextButton("Cancel", on_click=lambda e: page.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)))

        # Open our dialog in the overlay
        page.open(dlg)


    # Called when file -> open is clicked
    def handle_file_open_click(e):
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
        def open_selected_story(e):
            ''' Changes the route to the selected story '''

            #print("Open button clicked, selected story is: ", selected_story)

            if selected_story is not None:
                print("Opening story: ", selected_story)
                page.go(app.stories[selected_story].route)
                app.settings.story = app.stories[selected_story]  # Gives our settings widget the story reference it needs
                page.close(dlg)
                page.update()
            else:
                print("No story selected")

            page.close(dlg)
            page.update()

        open_button = ft.TextButton("Open", on_click=open_selected_story, disabled=True)


        # Our alert dialog that pops up when file -> open is clicked
        dlg = ft.AlertDialog(
            title=ft.Text(
                "What story would you like to open?",
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            content=ft.RadioGroup(
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=False, controls=get_stories_list()),
                on_change=change_selected_story
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                open_button,
            ]
        )

        # Opens our dialog
        page.open(dlg)

    def settings_clicked(e):
        ''' Goes to the settings page '''
        if page.route != "/settings":
            page.go("/settings")
        else:
            # Get the active story title and find its route
            active_story_title = app.settings.data.get('active_story', "/")
            if active_story_title != "/" and active_story_title in app.stories:
                page.go(app.stories[active_story_title].route)
            else:
                page.go("/")


    # Styling used by lots of menu bar items
    menubar_style = ft.ButtonStyle(
        bgcolor={ft.ControlState.HOVERED: ft.Colors.TRANSPARENT},
        shape=ft.RoundedRectangleBorder(radius=10),
        color=ft.Colors.PRIMARY
    )

    # Create our menu bar with submenu items
    menubar = ft.MenuBar(
        expand=True,
        style=ft.MenuStyle(     # Styling our menubar
            alignment=ft.alignment.center,
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
                    alignment=ft.alignment.center
                ), 
                style=menubar_style,    # styling for the button
                on_open=handle_submenu_open,    # Handle when a submenu is opened
                on_close=handle_submenu_close,  # Handle when a submenu is closed
                on_hover=handle_submenu_hover,  # Handle when a submenu is hovered
                controls=[      # The options shown inside of our button
                    ft.MenuItemButton(
                        content=ft.Text("New Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        # Options: Blank Story, From Template, but clicking also just creates blank
                        leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, color=ft.Colors.ON_SURFACE,),
                        style=menubar_style,
                        on_click=handle_create_new_story_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Open Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.MENU_BOOK_OUTLINED),
                        style=menubar_style,
                        on_click=handle_file_open_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Upload", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        # Options: story, chapter, map, drawing, character, note
                        leading=ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED),
                        style=menubar_style,
                        on_click=handle_file_open_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Export", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        # Options: story, chapter, map, drawing, character, note
                        leading=ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED),
                        style=menubar_style,
                        on_click=handle_file_open_click,
                    ),
                    
                    ft.MenuItemButton(
                        content=ft.Text("Settings", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED),
                        style=menubar_style,
                        on_click=settings_clicked,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Delete Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.DELETE_FOREVER_ROUNDED),
                        style=menubar_style,
                        on_click=handle_delete_click,
                    ),
                ],
            ),
        ], 
    )

    
        
    # Return our formatted menubar
    return ft.Container(
        border=ft.border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
        #bgcolor=ft.Colors.with_opacity(.4, ft.Colors.ON_INVERSE_SURFACE),
        

        content=ft.Row(
            spacing=None,
            controls=[
                menubar,    # Menubar on left
                ft.Container(expand=True),  # empty space in middle of menubar
                # Fix broken widgets button

                ft.TextButton("Feedback"),  # Feedback button
                ft.IconButton(icon=ft.Icons.SETTINGS_OUTLINED, on_click=settings_clicked),   # Settings button
                ft.TextButton("Account Name", icon=ft.Icons.ACCOUNT_CIRCLE_OUTLINED),  # apps account name         
            ]
        )
    )
