import flet as ft
from view_components.menu_bar import MenuBar
from contexts.contexts import AppContext, AppSettingsContext


# Called when creating our home view (No stories exist or none active)
@ft.component
def HomeView() -> ft.View: 
    ''' Creates a custom menu bar with new, open, and import new story buttons, and a create new story button in the middle'''
    
    def submit_new_story(e=None):
        ''' Creates a new story with the given title '''

        title = story_title_field.value.strip()  # Get the title from the text field and strip whitespace

        # Check if the title is unique
            #print("title is unique, story being created: ", title)
        app.create_story(title, page) # Needs the story object
        set_show_dlg(False)

    page = ft.context.page
    app = ft.use_context(AppContext)
    settings = ft.use_context(AppSettingsContext)

    story_title_field = ft.TextField(
        label="Story Title",
        autofocus=True,
        capitalization=ft.TextCapitalization.SENTENCES,
        on_submit=submit_new_story,
    )


        

    show_dlg, set_show_dlg = ft.use_state(False)

    ft.use_dialog(
        ft.AlertDialog(

            # Title of our dialog
            title=ft.Text("Create New Story"),

            # Main content is text box for user to input story title
            content=story_title_field,

            # Our two action buttons at the bottom of the dialog
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: set_show_dlg(False), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK)),
                ft.TextButton(
                    "Create", on_click=submit_new_story, 
                    style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor=ft.MouseCursor.CLICK)
                ),
            ],
        )
        if show_dlg
        else None
    )



    


    return ft.View(
            route="/",
            controls=[
                MenuBar(),

                # Row of workspaces rail to the left (None selected)
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    #bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    content=ft.FloatingActionButton(
                        "Create New Story",
                        ft.Icons.ADD_OUTLINED,
                        on_click=lambda: set_show_dlg(True),
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
    