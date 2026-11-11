''' 
Class for our menubar, which will hold our file options, drawing controls, and setting shortcut
'''

import flet as ft
from models.app import app
from models.views.story import Story
from styles.snack_bar import SnackBar
from styles.text_fields import TextField
from flet_color_pickers import ColorPicker
import math
import flet.canvas as cv
from utils.safe_string_checker import return_safe_name
import os
import json
import asyncio
import shutil
import stat
from constants import STORIES_DIRECTORY_PATH
from styles.snack_bar import SnackBar
from utils import google_drive
import flet_shadcn_ui as shad



class MenuBar(ft.Container):
    def __init__(self, story: Story = None):

        self.story = story

        super().__init__(
            border=ft.Border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
            bgcolor=ft.Colors.SURFACE,
        )

    def is_isolated(self):
        return True


    def build(self):

        class Dropdown(ft.Dropdown):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.border_color=ft.Colors.OUTLINE_VARIANT
                self.menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4))
                self.label_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, italic=True)
                self.margin=ft.Margin.only(top=8, left=4, right=4)
                self.dense=True

        class Switch(ft.Switch):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.adaptive=True
                self.label_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, italic=True)
                #self.margin=ft.Margin.only(top=8, left=4, right=4)
                
    
    
        # Called when file -> new is clicked
        def handle_create_story(e):
            ''' Opens a dialog to create a new story. Checks story is unique or not '''
    
    
            
    
            async def submit_new_story(e=None):
                ''' Creates a new story with the given title '''
    
                title = story_title_field.value.strip()
    
                app.create_new_story(title, ft.context.page) # Needs the story object
                ft.context.page.pop_dialog()
    
    
            
    
            # Create a reference to the text field so we can access its value
            story_title_field = ft.TextField(
                label="Story Title",
                autofocus=True, capitalization=ft.TextCapitalization.WORDS,
                on_submit=submit_new_story,
            )
        
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
                    ft.TextButton("Cancel", on_click=lambda: ft.context.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    ft.TextButton(
                        "Create Story", on_click=submit_new_story, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)
                    )
                ],
            )
    
            # Open our dialog in the overlay
            ft.context.page.show_dialog(dlg)

        
    
    
        # Called when file -> open is clicked
        async def handle_open_story(e=None):
            ''' Opens a dialog to open an existing story '''
    
            #print("Open Story Clicked")
    
            selected_story = None
    
            # Called when a new story text button is clicked
            def change_selected_story(e):
                ''' Changes our selected story variable '''
    
                nonlocal selected_story
                selected_story = e.control.value
                open_button.disabled = False
                open_button.style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click")
                open_button.update()
                cloud_warning.visible = selected_story.startswith("cloud:")
                cloud_warning.update()

            cloud_stories = []
            cloud_warning = ft.Text(
                "Warning: Opening a cloud story will overwrite the local version on this device, if one exists.",
                visible=False, italic=True, color=ft.Colors.ERROR, size=12, width=300,
            )
            cloud_column = ft.Column(tight=True, controls=[])
    
            # Returns a list of all story titles available to open
            def get_stories_list() -> ft.Control:
                ''' Returns a list of all story titles available to open '''
    
                # List of our story choices
                
    
                # Set style for our options
                style = ft.TextStyle(
                    size=14,
                    color=ft.Colors.ON_SURFACE,
                    weight=ft.FontWeight.BOLD,
                )
                ctrls = [ft.Text("Local Stories", style=style)]
                
    
                # Use something better than radio in future, but for now this works
                for story in app.stories.values():
                    ctrls.append(ft.Radio(expand=False, value=f"local:{story.data.get('id')}", label=story.data.get('title'), label_style=style, mouse_cursor=ft.MouseCursor.CLICK))

                if app.is_cloud_authenticated == True:
                    ctrls.append(ft.Divider())
                    ctrls.append(ft.Text("Cloud Stories", style=style))
                    cloud_column.controls = [ft.ProgressRing(width=24, height=24, stroke_width=3)]
                    ctrls.append(cloud_column)
                    ctrls.append(cloud_warning)
    
                return ctrls

            async def load_cloud_stories():
                ''' Fills in the cloud section once the metadata has been read, so the dialog itself opens immediately '''
                nonlocal cloud_stories
                style = ft.TextStyle(size=14, color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)
                try:
                    # Only reads each cloud story's metadata file, not the whole cloud
                    cloud_stories = await asyncio.to_thread(google_drive.list_cloud_stories)
                except Exception as ex:
                    cloud_column.controls = [ft.Text(google_drive.describe_error(ex), color=ft.Colors.ERROR, size=12)]
                    try:
                        cloud_column.update()
                    except Exception:
                        pass
                    return

                if not cloud_stories:
                    cloud_column.controls = [ft.Text("No stories found in the cloud.", color=ft.Colors.OUTLINE, size=12)]
                else:
                    cloud_column.controls = [
                        ft.Radio(
                            expand=False, value=f"cloud:{s['id']}", label_style=style, mouse_cursor=ft.MouseCursor.CLICK,
                            label=s['title'],
                        ) for s in cloud_stories
                    ]
                try:
                    cloud_column.update()
                except Exception:
                    pass    # Dialog was closed before the cloud finished loading
    
    
            # Called when the 'open' button is clicked in the bottom right of the dialog
            async def open_selected_story(e=None):
                ''' Changes the route to the selected story '''

                if selected_story is None:
                    ft.context.page.pop_dialog()
                    return

                source, _, story_id = selected_story.partition(":")

                if source == "cloud":
                    title = next((s['title'] for s in cloud_stories if s['id'] == story_id), "this story")
                    if story_id in app.stories:
                        _confirm_cloud_action(
                            "Overwrite local story?",
                            f"'{title}' also exists on this device. Opening the cloud version replaces the local version, and local changes will be lost."
                            "\n\nAre you sure you want to proceed?",
                            "Confirm",
                            lambda: pull_story_from_cloud(story_id), "Opening from Google Drive...", "Opened from Google Drive",
                        )
                    else:
                        await _run_cloud_action(lambda: pull_story_from_cloud(story_id), "Opening from Google Drive...", "Opened from Google Drive")
                    return

                await ft.context.page.push_route(app.stories[story_id].route)
                app.settings.story = app.stories[story_id]  # Gives our settings widget the story reference it needs
                ft.context.page.pop_dialog()
                ft.context.page.update()

    
            open_button = ft.TextButton("Open", on_click=open_selected_story, disabled=True, style=ft.ButtonStyle(mouse_cursor="click"))
    
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
                    content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=False, tight=True, controls=get_stories_list()),
                    on_change=change_selected_story
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: ft.context.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    open_button,
                ]
            )
    
            # Opens our dialog
            ft.context.page.show_dialog(dlg)

            if app.is_cloud_authenticated == True:
                await load_cloud_stories()

        def handle_rename_story(e: ft.Event=None):


            async def rename_story(e=None):
                story = self.story
                story.rename(title_tf.value)

                # Keep the cloud copy in step, but only if this story is already saved there
                if app.is_cloud_authenticated == True:
                    try:
                        await story.save_file()
                        if await asyncio.to_thread(google_drive.push_story_if_in_cloud, story.data.get('directory_path')):
                            ft.context.page.show_dialog(SnackBar("Renamed in Google Drive too."))
                    except Exception as ex:
                        ft.context.page.show_dialog(SnackBar(f"Renamed locally, but the cloud copy was not updated: {google_drive.describe_error(ex)}"))

            title_tf = ft.TextField(
                value=self.story.data.get('title', ''),
                autofocus=True, capitalization=ft.TextCapitalization.WORDS,
                on_submit=rename_story,
            )

            rename_controls = [title_tf]
            if app.is_cloud_authenticated == True:
                rename_controls.append(ft.Text(
                    "If this story is saved in your Google Drive, the cloud copy will be renamed too.",
                    italic=True, size=12, color=ft.Colors.ERROR,
                ))

            dlg = ft.AlertDialog(
                
                # Title of our dialog
                title=ft.Text(
                    f"Rename {self.story.data.get('title', '')}", 
                    color=ft.Colors.ON_SURFACE,
                    weight=ft.FontWeight.BOLD,
                ),
    
                # Main content is text box for user to input story title
                content=ft.Column(tight=True, width=320, controls=rename_controls),
    
                # Our two action buttons at the bottom of the dialog
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: ft.context.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    ft.TextButton("Rename", on_click=rename_story,style=ft.ButtonStyle(mouse_cursor="click")),
                ],
            )
    
            # Open our dialog in the overlay
            ft.context.page.show_dialog(dlg)

        def toggle_show_canvas_rail(e: ft.Event[ft.MenuItemButton]):
            ''' Toggles the visibility of the canvas rail on the left side of the page '''
            new_value = not app.settings.data.get('story', {}).get('show_canvas_rail', False)
            app.settings.update_data(**{'story': {'show_canvas_rail': new_value}})
            if new_value:
                e.control.leading.icon = ft.Icons.VISIBILITY_OUTLINED
            else:
                e.control.leading.icon = ft.Icons.VISIBILITY_OFF_OUTLINED
            if self.story is not None:
                if new_value:
                    self.story.canvas_rail.width = 78
                else:
                    self.story.canvas_rail.width = 0
                self.story.canvas_rail.update()
            e.control.update()

        async def handle_settings_clicked(e=None):
            ''' Goes to the settings page '''
            if ft.context.page.route != "/settings":
                await ft.context.page.push_route("/settings")
            else:
                # Get the active story title and find its route
                if self.story is not None:
                    await ft.context.page.push_route(self.story.route)
                else:
                    await ft.context.page.push_route("/")

        async def handle_delete_story(e=None):

            async def confirm_delete(e=None):
                try:
                    ft.context.page.pop_dialog()

                    story_id = self.story.data.get('id')
                    delete_cloud = delete_from_cloud_switch.value and app.is_cloud_authenticated == True

                    # Local delete first, so the UI doesn't wait on the network
                    title = app.delete_story(story_id)

                    await ft.context.page.push_route("/loading")
                    ft.context.page.title = "Story Board (alpha)"
                    ft.context.page.update()
                    await asyncio.sleep(0.2)

                    if not delete_cloud:
                        ft.context.page.show_dialog(SnackBar(f"{title} deleted successfully."))
                        await ft.context.page.push_route("/")
                        return

                    page = ft.context.page
                    async def delete_cloud_copy():
                        try:
                            await asyncio.to_thread(google_drive.delete_story, story_id)
                            page.show_dialog(SnackBar(f"{title} deleted successfully (also removed from Google Drive)."))
                        except Exception as ex:
                            page.show_dialog(SnackBar(f"{title} deleted locally, but the cloud copy could not be deleted: {google_drive.describe_error(ex)}"))
                    page.run_task(delete_cloud_copy)

                except Exception as e:
                    ft.context.page.show_dialog(SnackBar(f"Error deleting story: {e}"))
                await ft.context.page.push_route("/")
                page.update()
                

            delete_text = "Are you sure you want to delete this story? This action cannot be undone!"

            dlg = ft.AlertDialog(
                title=ft.Text(f"Delete {self.story.data.get('title', 'Story')}?", weight=ft.FontWeight.BOLD),
                content=ft.Column([
                    ft.Text(delete_text),
                    delete_from_cloud_switch := ft.Switch(
                        label="Delete from cloud as well",
                        value=app.is_cloud_authenticated == True,
                        visible=app.is_cloud_authenticated == True,
                    )
                ], tight=True),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda: ft.context.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    ft.TextButton("DELETE FOREVER", on_click=confirm_delete,style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.RED)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            ft.context.page.show_dialog(dlg)
            

        def highlight(e):
            e.control.content.bgcolor = ft.Colors.with_opacity(0.25, ft.Colors.BLUE_400)
            e.control.update()

        def unhighlight(e):
            e.control.content.bgcolor = None
            e.control.update()
    
        # Create our menu bar with submenu items
        file_options = shad.ContextMenu(
            open_on_tap=True,
            content=ft.GestureDetector(
                ft.Container(ft.Icon(ft.Icons.MENU_OUTLINED, ft.Colors.PRIMARY), border_radius=6, padding=8),
                on_enter=highlight, on_exit=unhighlight, mouse_cursor=ft.MouseCursor.CLICK
            ), 
            items=[      # The options shown inside of our button
                shad.MenuItem(
                    "New Story",
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, ft.Colors.PRIMARY, size=20),
                    on_click=handle_create_story,
                ),
                shad.MenuItem(
                    "Open Story",
                    leading=ft.Icon(ft.CupertinoIcons.BOOK, ft.Colors.PRIMARY, size=20),
                    on_click=handle_open_story,
                ),
                shad.MenuItem(
                    "Rename Story",
                    leading=ft.Icon(ft.Icons.EDIT_OUTLINED, ft.Colors.PRIMARY, size=20),
                    disabled=self.story is None,
                    on_click=handle_rename_story,
                ),
                shad.MenuItem(
                    "Drawing Controls", 
                    leading=ft.Icon(
                        ft.Icons.VISIBILITY_OUTLINED if app.settings.data.get('story', {}).get('show_canvas_rail', False) else ft.Icons.VISIBILITY_OFF_OUTLINED,
                        ft.Colors.PRIMARY, size=20
                    ),
                    disabled=self.story is None,
                    on_click=toggle_show_canvas_rail,
                ),
                shad.MenuItem(
                    "Export",
                    leading=ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED, ft.Colors.PRIMARY, size=20),
                    disabled=self.story is None,
                    tooltip="Export widgets from your story into other formats.",
                    on_click=self.story.handle_export,
                ),
                shad.MenuItem(
                    "Settings",
                    leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY, size=20),
                    on_click=handle_settings_clicked,
                ),
                shad.MenuItem(
                    "Delete Story", 
                    leading=ft.Icon(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR, size=20),
                    disabled=self.story is None,
                    on_click=handle_delete_story,
                ),
            ],
        )







        # DRAW MODE STUFFF -----------------------------------------------------


        async def handle_connect_clicked(e=None):
            ''' Opens the browser so the user can connect their Google account '''
            #if is_connecting:
               # return
            #set_is_connecting(True)
            if app.is_cloud_authenticated == True:
                return
            try:
                ft.context.page.show_dialog(SnackBar("Opening browser to connect your Google account..."))
                await asyncio.to_thread(google_drive.authenticate)
                app.is_cloud_authenticated = True
                ft.context.page.show_dialog(SnackBar("Google account connected."))
                set_cloud_button()
                self.cloud_button.update()
            except Exception as ex:
                ft.context.page.show_dialog(SnackBar(google_drive.describe_error(ex)))
            #finally:
                #set_is_connecting(False)

        async def _run_cloud_action(action, busy_text: str, done_text: str, restart_after: bool = False):
            #set_is_connecting(True)
            ft.context.page.pop_dialog()
            try:
                if restart_after:
                    # Leave the story view first so its components unmount (and flush any saves) BEFORE the files are replaced
                    ft.context.page.navigate("/loading")
                    await asyncio.sleep(0.3)

                count = await action()

                if restart_after:
                    app.stories.clear()
                    app.settings.story = None
                    await app.load_previous_story(ft.context.page)

                ft.context.page.show_dialog(SnackBar(f"{done_text} ({count - 1} files)"))
            except Exception as ex:
                ft.context.page.show_dialog(SnackBar(google_drive.describe_error(ex)))
                if restart_after:
                    await ft.context.page.push_route("/")
            #finally:
                #set_is_connecting(False)

        def _confirm_cloud_action(title: str, message: str, confirm_label: str, action, busy_text: str, done_text: str, restart_after: bool = False):
            ft.context.page.show_dialog(ft.AlertDialog(
                modal=True,
                title=title,
                content=ft.Text(message, size=16),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda: ft.context.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                    ft.TextButton(
                        confirm_label, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click"),
                        on_click=lambda: ft.context.page.run_task(_run_cloud_action, action, busy_text, done_text, restart_after),
                    ),
                ],
            ))

        def handle_push_clicked(e=None):
            if self.story is None:
                ft.context.page.show_dialog(SnackBar("No story is open to push."))
                return
            story = self.story
            async def push_action():
                page = ft.context.page
                await page.push_route("/pushing_to_cloud")
                try:
                    return await app.push_story_cloud(story)
                finally:
                    await page.push_route(story.route)
            _confirm_cloud_action(
                "Push to Google Drive?",
                f"This saves {story.data.get('title', '')} to your Google Drive from your current device."
                "\nThis will overwrite the existing cloud, so make sure this device has the most up-to-date version of your story."
                "\n\nAre you sure you want to proceed?",
                "Confirm", push_action, "Pushing to Google Drive...", "Pushed to Google Drive",
            )

        async def pull_story_from_cloud(story_id: str) -> int:
            ''' Replaces the local copy of a story with its cloud copy and opens it '''
            # Leave the story view first so its components unmount (and flush any saves) BEFORE the files are replaced
            await ft.context.page.push_route("/pulling_from_cloud")
            await asyncio.sleep(0.3)
            old_story = app.stories.get(story_id)
            try:
                story = await app.pull_story_cloud(story_id)
            except Exception:
                if old_story is not None:
                    await ft.context.page.push_route(old_story.route)
                else:
                    await ft.context.page.push_route("/")
                raise
            app.settings.story = story
            await ft.context.page.push_route(story.route)
            return len([f for _, _, files in os.walk(story.data.get('directory_path')) for f in files])

        def handle_pull_clicked(e=None):
            if self.story is None:
                ft.context.page.show_dialog(SnackBar("No story is open to pull."))
                return
            story_id = self.story.data.get('id')
            async def pull_action():
                return await pull_story_from_cloud(story_id)
            _confirm_cloud_action(
                "Pull from cloud?",
                f"This pulls {self.story.data.get('title', '')} from your Google Drive to this device.\nThis will overwrite any local data, so make sure the cloud has the latest version." 
                "\n\nAre you sure you want to proceed?",
                "Confirm", pull_action, "Pulling from Google Drive...", "Pulled from Google Drive",
            )

        def set_cloud_button() -> list[ft.PopupMenuItem]:
            if app.is_cloud_authenticated == True:
                self.cloud_button.icon = ft.Icon(ft.Icons.CLOUD_DONE_OUTLINED, ft.Colors.PRIMARY)
                self.cloud_button.items = [
                    ft.PopupMenuItem(
                        ft.Text(
                                spans=[
                                    ft.TextSpan("Push to Google Drive\n"),
                                    ft.TextSpan(
                                        "Saves current story to your Google Drive, overwriting any existing cloud data. Use this as a backup, or to pick up where you left off on another device.",
                                        style=ft.TextStyle(color=ft.Colors.OUTLINE, size=12), expand=True, 
                                    ),
                                ],
                                width=220   # Bind the width, since popupmenuitems styling are jacked up otherwise.
                            ),
                        icon=ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, ft.Colors.PRIMARY), on_click=handle_push_clicked,
                        padding=10,
                        disabled=not self.story
                    ),
                    ft.PopupMenuItem(ft.Divider(), height=10, disabled=True),
                    ft.PopupMenuItem(
                        ft.Text(
                            spans=[
                                ft.TextSpan("Pull from Google Drive\n"),
                                ft.TextSpan(
                                    "Pull the current story from your Google Drive to this device. This will overwrite any local data, so make sure the cloud has the latest version.", 
                                    style=ft.TextStyle(color=ft.Colors.OUTLINE, size=12)
                                )
                            ],
                            width=220   # Bind the width, since popupmenuitems styling are jacked up otherwise.
                        ), 
                        ft.Icon(ft.Icons.CLOUD_DOWNLOAD_OUTLINED, ft.Colors.PRIMARY), 
                        on_click=handle_pull_clicked, expand=True, padding=10,
                        disabled=not self.story
                    )
                ]
            else:
                self.cloud_button.icon = ft.Icon(ft.Icons.CLOUD_OUTLINED, ft.Colors.PRIMARY)
                self.cloud_button.items = [
                    ft.PopupMenuItem(
                        ft.Text(
                            spans=[
                                ft.TextSpan("Connect to Google Drive\n"),
                                ft.TextSpan(
                                    "Connect your device to Google Drive to enable cloud sync.", 
                                    style=ft.TextStyle(color=ft.Colors.OUTLINE, size=12)
                                )
                            ],
                            width=220   # Bind the width, since popupmenuitems styling are jacked up otherwise.
                        ), 
                        ft.Icon(ft.Icons.CLOUD_DOWNLOAD_OUTLINED, ft.Colors.PRIMARY), 
                        on_click=handle_connect_clicked, expand=True, padding=10
                    )
                ]

        

        self.cloud_button = ft.PopupMenuButton(
            icon=ft.Icons.CLOUD_DONE_OUTLINED if app.is_cloud_authenticated == True else ft.Icons.CLOUD_OUTLINED,
            icon_color="primary",
            tooltip="Google Drive options",
            #disabled=is_connecting,
            #items=get_cloud_sync_
            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
            menu_padding=0
        )
        
        set_cloud_button()


        self.content = ft.Row(
            spacing=0, visible=not self.page.platform.is_mobile(),
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            margin=ft.Margin.only(left=10),
            controls=[
                file_options,    # File options button
                ft.Row([        # Row that has alpha text, info button, and settings button
                    ft.Text(
                        "Alpha", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, 
                        tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nJoin the Discord (Settings -> Resources) to suggest your features and report bugs"
                    ),  # Feedback button
                    ft.Icon(
                        ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, 
                        tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nJoin the Discord (Settings -> Resources) to suggest your features and report bugs"
                    ),
                    self.cloud_button,
                    ft.IconButton(ft.Icons.SETTINGS_OUTLINED, "primary", on_click=handle_settings_clicked, mouse_cursor=ft.MouseCursor.CLICK),   # Settings button
                ], tight=True, spacing=0)
            ]
        )

        self.page.appbar = ft.AppBar(
            file_options,
            title=self.story.data.get('title') if self.story else "Story Board",
            actions=[
                ft.Text(
                    "Alpha", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, 
                    tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nJoin the Discord (Settings -> Resources) to suggest your features and report bugs"
                ),  # Feedback button
                ft.Icon(
                    ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, 
                    tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nJoin the Discord (Settings -> Resources) to suggest your features and report bugs"
                ),
                self.cloud_button,
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, "primary", on_click=handle_settings_clicked, mouse_cursor=ft.MouseCursor.CLICK),   # Settings button
            ]
        ) if self.page.platform.is_mobile() else None