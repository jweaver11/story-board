''' View for our tutorial page '''
import flet as ft
import asyncio
from styles.snack_bar import SnackBar


def create_tutorial_view(page: ft.Page) -> ft.View:
    from models.app import app

    async def _end_tutorial_clicked(e: ft.Event=None):
        ''' Ends the tutorial and routes to the home page '''

        await app.load_previous_story(page)
        page.show_dialog(SnackBar("You can access the tutorial anytime in Settings -> Resources", duration=7000))

    # Load the previous tutorial step
    async def _previous_tutorial_step(e: ft.Event=None):
        nonlocal tutorial_step
        if tutorial_step > 0:
            tutorial_step -= 1
            await load_tutorial_step()

    # Load the next tutorial step
    async def _next_tutorial_step(e: ft.Event=None):
        nonlocal tutorial_step
        tutorial_step += 1
        await load_tutorial_step()
       

    # Give us the actual content of the current tutorial step
    async def load_tutorial_step():
        nonlocal tutorial_step

        if previous_tip_button.disabled:
            previous_tip_button.disabled = False
            previous_tip_button.icon_color = ft.Colors.PRIMARY
            previous_tip_button.update()
        if next_tip_button.disabled:
            next_tip_button.disabled = False
            next_tip_button.icon_color = ft.Colors.PRIMARY
            next_tip_button.update()
            
        match tutorial_step:
            case 0:
                previous_tip_button.disabled = True 
                previous_tip_button.icon_color = ft.Colors.OUTLINE_VARIANT
                previous_tip_button.update()
                tutorial_tip.value = "This is the menu bar, where you can access app settings, account settings, and more!"
                workspaces_rail.visible = False
                workspaces_rail_divider.visible = False
                active_rail.visible = False
                active_rail_divider.visible = False
                workspace.visible = False
                tutorial_tip_container.left = 50
                tutorial_tip_container.top = 10
                tutorial_arrow.left = 20
                tutorial_arrow.top = 10
                workspaces_rail.update()
                workspaces_rail_divider.update()
                active_rail.update()
                active_rail_divider.update()
                workspace.update()
            case 1:
                tutorial_tip.value = "You can also open the settings from here"
                tutorial_tip_container.left = page.width - tutorial_tip_container.width - 50
                tutorial_arrow.left = page.width - 32
            case 2:
                tutorial_tip.value = "This is the active rail, where you can manage your active story and its scenes!"
                workspaces_rail.visible = True
                workspaces_rail_divider.visible = True
                workspaces_rail.update()
                workspaces_rail_divider.update()
            case 3:
                tutorial_tip.value = "This is the workspace, where you can see your story and edit it!"
            case _:
                tutorial_tip.value = "That's the end of the tutorial! Feel free to explore on your own :)"
        tutorial_tip_container.update()
        tutorial_arrow.update()

    menubar = ft.Container(
        border=ft.Border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
        bgcolor=ft.Colors.SURFACE,
        content=ft.Row(
            spacing=0,
            controls=[
                ft.MenuBar(
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
                            style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                            menu_style=ft.MenuStyle(padding=ft.Padding.all(0)),
                        
                        ),
                    ], 
                ),   
                ft.Container(expand=True),  # empty space in middle of menubar
                # Fix broken widgets button

                ft.Text(
                    "Alpha", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, 
                    tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                ),  # Feedback button
                ft.Icon(
                    ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, 
                    tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                ),
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, "primary", mouse_cursor=ft.MouseCursor.CLICK, disabled=True),   # Settings button
            ]
        )
    )
    workspaces_rail = ft.Container()
    active_rail = ft.Container()
    workspace = ft.Container(expand=True)

    tutorial_tip = ft.Text("This is the Menu Bar. Create new stories, change settings, and export your content here.", expand=True, size=16, text_align=ft.TextAlign.CENTER)
        
    tutorial_tip_format = ft.Column([
        tutorial_tip,
        ft.Row([
            ft.TextButton("Exit Tutorial", on_click=_end_tutorial_clicked, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), expand=True),
            previous_tip_button := ft.IconButton(ft.Icons.UNDO, ft.Colors.OUTLINE_VARIANT, on_click=_previous_tutorial_step, mouse_cursor=ft.MouseCursor.CLICK, disabled=True),
            next_tip_button := ft.IconButton(ft.Icons.REDO, ft.Colors.PRIMARY, on_click=_next_tutorial_step, mouse_cursor=ft.MouseCursor.CLICK),
        ], alignment=ft.MainAxisAlignment.END)
    ])
    tutorial_tip_container = ft.Container(
        tutorial_tip_format, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, padding=ft.Padding.all(10), border_radius=10, width=300, height=300,
        alignment=ft.Alignment.TOP_CENTER, animate_position=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT), left=50, top=10
    )
    tutorial_arrow = ft.Icon(ft.Icons.ARROW_UPWARD, color=ft.Colors.PRIMARY, scale=1.5, left=20, top=10, animate_position=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT))
    tutorial_step = 0

    # Build custom workspaced rail and active rail and workspace. 
    # Only show workspaces railt to start, then active, then workspace

    return ft.View(
        route="/tutorial",
        controls=[
            menubar,
            ft.Stack([
                ft.Row([
                    workspaces_rail,
                    workspaces_rail_divider := ft.Divider(2, 2),

                    active_rail,
                    active_rail_divider := ft.Divider(2, 2),
                    workspace,
                ], spacing=0, expand=True),
                tutorial_tip_container, tutorial_arrow
            ], expand=True),
        ],
        padding=ft.Padding.all(0), 

    )