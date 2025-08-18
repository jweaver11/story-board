''' Menu bar at the top of the page '''
import flet as ft
from models.user import user
from handlers.render_widgets import remove_drag_targets
from handlers.render_widgets import render_widgets
from ui.story_manager import create_new_story_dialog, create_load_story_dialog, save_current_story

def create_menu_bar(page: ft.Page):
    
    # Handler logic for each menu item clicked
    def handle_menu_item_click(e):
        print(f"{e.control.content.value}.on_click")
        page.open(
            ft.SnackBar(content=ft.Text(f"{e.control.content.value} was clicked!"))
        )
        page.update()

    def handle_new_story_click(e):
        """Handle New Story menu item click"""
        dialog = create_new_story_dialog(page)
        page.open(dialog)

    def handle_save_story_click(e):
        """Handle Save Story menu item click"""
        save_current_story(page)

    def handle_file_open_click(e):
        """Handle Open Story menu item click"""
        dialog = create_load_story_dialog(page)
        page.open(dialog)


    # Handlers called automatically for submenu events
    def handle_submenu_open(e):
        print(f"{e.control.content.content.value}.on_open")

    def handle_submenu_close(e):
        print(f"{e.control.content.content.value}.on_close")

    def handle_submenu_hover(e):
        print(f"{e.control.content.content.value}.on_hover")

    menubar_style = ft.ButtonStyle(
        bgcolor={ft.ControlState.HOVERED: ft.Colors.TRANSPARENT},
    )



    # Create our menu bar with submenu items
    menubar = ft.MenuBar(
       # Format menubar
        expand=True,
        style=ft.MenuStyle(
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.TRANSPARENT,
            shadow_color=ft.Colors.TRANSPARENT,
            mouse_cursor={
                ft.ControlState.HOVERED: ft.MouseCursor.WAIT,
                ft.ControlState.DEFAULT: ft.MouseCursor.ZOOM_OUT,
            },
        ),
        controls=[
            # Parent submenu item with child items on hover
            ft.SubmenuButton(
                content=ft.Container(
                    content=ft.Text("File", weight=ft.FontWeight.BOLD),
                    alignment=ft.alignment.center
                ),
                style=menubar_style,
                on_open=handle_submenu_open,
                on_close=handle_submenu_close,
                on_hover=handle_submenu_hover,
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text("New", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.ADD_CIRCLE_ROUNDED,),
                        style=menubar_style,
                        on_click=handle_new_story_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Save", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.SAVE),
                        style=menubar_style,
                        on_click=handle_save_story_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Save as", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.SAVE_AS),
                        style=menubar_style,
                        on_click=handle_menu_item_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Open", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.FOLDER_OPEN),
                        style=menubar_style,
                        on_click=handle_file_open_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Import", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.UPLOAD_FILE),
                        style=menubar_style,
                        on_click=handle_menu_item_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Export", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.DOWNLOAD),
                        style=menubar_style,
                        on_click=handle_menu_item_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Quit", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.EXIT_TO_APP),
                        style=menubar_style,
                        on_click=lambda e: page.window.close(),
                    ),
                ],
            ),
            ft.SubmenuButton(
                content=ft.Container(
                    content=ft.Text("Edit", weight=ft.FontWeight.BOLD),
                    alignment=ft.alignment.center
                ),
                style=menubar_style,
                on_open=handle_submenu_open,
                on_close=handle_submenu_close,
                on_hover=handle_submenu_hover,
                controls=[
                    ft.MenuItemButton(
                        content=ft.Text("Copy", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.INFO),
                        style=menubar_style,
                        on_click=handle_menu_item_click,
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Paste", weight=ft.FontWeight.BOLD),
                        leading=ft.Icon(ft.Icons.INFO),
                        style=menubar_style,
                        on_click=handle_menu_item_click,
                    ),
                ],
            ),
        ], 
    )

    def settings_clicked(e):
        user.settings.visible = not user.settings.visible
        render_widgets(page)  # Re-render the page to show/hide settings
        page.update()

    # Create our container for the menu bar
    menubar_container = ft.Container(
        border=ft.border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.ON_INVERSE_SURFACE),
        #border_radius=ft.border_radius.all(4),  # 4px radius on all corners

        content=ft.Row(
            spacing=None,
            controls=[
                menubar,    # Menubar on left
                ft.Container(expand=True),  # empty space in middle of menubar
                # Fix broken widgets button
                ft.IconButton(icon=ft.Icons.BUILD_ROUNDED, on_click=lambda e: remove_drag_targets(), tooltip="Click if broken"),
                ft.TextButton("Feedback"),  # Feedback button
                ft.IconButton(icon=ft.Icons.SETTINGS_OUTLINED, on_click=settings_clicked),   # Settings button
                ft.TextButton("Account Name", icon=ft.Icons.ACCOUNT_CIRCLE_OUTLINED),  # users account name
            ]))



    return menubar_container
