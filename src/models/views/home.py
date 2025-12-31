import flet as ft
from ui.menu_bar import create_menu_bar
from styles.colors import dark_gradient
from handlers.check_story_unique import story_is_unique


# Called when creating our home view (No stories exist or none active)
def create_home_view(page: ft.Page) -> ft.View: 
    ''' Creates a custom menu bar with neww, open, and import new story buttons, and a create new story button in the middle'''
    from models.app import app

    menubar = create_menu_bar(page)   


    # Called when giant new story button is clicked
    def create_new_story_button_clicked(e):
        ''' Opens a dialog to create a new story. Checks story is unique or not '''
        #print("New Story Clicked")

        # Variable to track if the title is unique
        is_unique = True

        # Called by clicking off the dialog or cancel button
        def close_dialog(e):
            ''' Closes the dialog '''
            dlg.open = False
            page.update()

        def submit_new_story(e):
            ''' Creates a new story with the given title '''

            # Import our variable if it is unique or nah
            nonlocal is_unique

            if isinstance(e, ft.TextField):
                title = e.value
            else:
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
        def check_story_title_unique(e):
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
            autofocus=True,
            capitalization=ft.TextCapitalization.WORDS,
            on_submit=submit_new_story,
            on_change=check_story_title_unique,
        )

        create_button = ft.TextButton("Create", on_click=lambda e: submit_new_story(story_title_field), disabled=True)
            
        # The dialog that will pop up whenever the new story button is clicked
        dlg = ft.AlertDialog(

            # Title of our dialog
            title=ft.Text("Create New Story"),

            # Main content is text box for user to input story title
            content=story_title_field,

            # Our two action buttons at the bottom of the dialog
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                create_button,
            ],
        )

        # Open our dialog in the overlay
        dlg.open = True
        page.overlay.append(dlg)
        page.update()


    return ft.View(
        "/",
        [
            menubar,

            # Row of workspaces rail to the left (None selected)
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                gradient=dark_gradient,
                content=ft.FloatingActionButton(
                    content=ft.Row([ft.Container(expand=True), ft.Icon(ft.Icons.ADD_OUTLINED), ft.Text("Create New Story", theme_style=ft.TextThemeStyle.BODY_LARGE), ft.Container(expand=True)], alignment=ft.alignment.center),
                    on_click=create_new_story_button_clicked,
                    width=200,
                    height=100,
                    shape=ft.RoundedRectangleBorder(radius=10),  
                ),
            ),
        ],
        padding=ft.padding.only(top=0, left=0, right=0, bottom=0),      # No padding for the page
        spacing=0,                                                      # No spacing between menubar and rest of page
    )