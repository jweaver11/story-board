import flet as ft
from view_components.menu_bar import MenuBar
from styles.colors import dark_gradient
import flet_shadcn_ui as shad



# Called when creating our home view (No stories exist or none active)
def create_home_view(page: ft.Page) -> ft.View: 
    ''' Creates a custom menu bar with new, open, and import new story buttons, and a create new story button in the middle'''
    from models.app import app

    menubar = MenuBar()


    # Called when file -> new is clicked
    def handle_create_story(e):
        ''' Opens a dialog to create a new story. Checks story is unique or not '''

        if page.route == "/tutorial":
            return page.show_dialog(shad.Toast("Action not possible during tutorial", variant=shad.ToastVariant.DESTRUCTIVE))
        

        async def submit_new_story(e=None):
            ''' Creates a new story with the given title '''

            title = story_title_field.value.strip()

            app.create_new_story(title, ft.context.page, template=template.value) # Needs the story object
            ft.context.page.pop_dialog()

        # Create a reference to the text field so we can access its value
        story_title_field = shad.Input(
            label="Story Title",
            autofocus=True,
            on_submit=submit_new_story,
        )
    
        # The dialog that will pop up whenever the new story button is clicked
        dlg = shad.Dialog(

            # Title of our dialog
            title="Create New Story", 

            # Main content is text box for user to input story title
            content=ft.Column([
                story_title_field,
                shad.Separator(),
                #ft.Text("Templates", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.W_500),
                template :=shad.RadioGroup(
                    [
                        shad.Radio("blank", "Blank", "An empty story with no initial content."),
                        shad.Radio("default", "Default", "A story with basic structure and widgets.")
                    ],
                    "default",
                    label="Templates"
                )
            ]),

            # Our two action buttons at the bottom of the dialog
            actions=[
                shad.Button("Cancel", on_click=lambda: ft.context.page.pop_dialog(), color=ft.Colors.ERROR, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM),
                shad.Button("Create Story", on_click=submit_new_story, color=ft.Colors.PRIMARY, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM)
            ],
        )

        # Open our dialog in the overlay
        ft.context.page.show_dialog(dlg)


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
                    on_click=handle_create_story,
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