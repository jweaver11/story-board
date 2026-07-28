import flet as ft
from ui.menu_bar import create_menu_bar
from styles.colors import dark_gradient
from utils.check_story_unique import story_is_unique


# Called when creating our home view (No stories exist or none active)
def create_home_view(page: ft.Page) -> ft.View: 
    ''' Creates a custom menu bar with new, open, and import new story buttons, and a create new story button in the middle'''
    from models.app import app

    menubar = create_menu_bar(page)   


    # Called when giant new story button is clicked
    async def create_new_story_button_clicked(e):
        ''' Opens a dialog to create a new story. Checks story is unique or not '''
        #print("New Story Clicked")

        # Variable to track if the title is unique
        is_unique = True


        def submit_new_story(e=None):
            ''' Creates a new story with the given title '''

            # Import our variable if it is unique or nah
            nonlocal is_unique, story_title_field

            title = story_title_field.value.strip()  # Get the title from the text field and strip whitespace

            # Check if the title is unique
                #print("title is unique, story being created: ", title)
            app.create_new_story(title, page) # Needs the story object
            dlg.open = False
            page.update()
            
        # Create a reference to the text field so we can access its value
        story_title_field = ft.TextField(
            label="Story Title",
            autofocus=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_submit=submit_new_story,
        )

        create_button = ft.Button(
            "Create", on_click=submit_new_story, 
            disabled=True, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor=ft.MouseCursor.CLICK)
        )
            
        # The dialog that will pop up whenever the new story button is clicked
        dlg = ft.AlertDialog(

            # Title of our dialog
            title=ft.Text("Create New Story"),

            # Main content is text box for user to input story title
            content=story_title_field,

            # Our two action buttons at the bottom of the dialog
            actions=[
                ft.Button("Cancel", on_click=lambda _: page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK)),
                create_button,
            ],
        )

        # Open our dialog in the overlay
        dlg.open = True
        page.overlay.append(dlg)
        page.update()


    return ft.View(
        route="/",
        controls=[
            menubar,

            # Row of workspaces rail to the left (None selected)
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                #bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                content=ft.FloatingActionButton(
                    "Create New Story",
                    ft.Icons.ADD_OUTLINED,
                    on_click=create_new_story_button_clicked,
                    scale=1.5,
                    mouse_cursor=ft.MouseCursor.CLICK,
                    shape=ft.RoundedRectangleBorder(radius=10),  
                ),
            ),
        ],
        spacing=0,                                             # No spacing between menubar and rest of page
        padding=ft.Padding.all(0), 
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH
    )