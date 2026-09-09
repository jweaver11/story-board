''' 
Class for our menubar, which will hold our file options, drawing controls, and setting shortcut
'''

import flet as ft
from models.app import app
from models.views.story import Story
from utils.check_story_unique import story_is_unique
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



class MenuBar(ft.Container):
    def __init__(self, story: Story = None):

        self.story = story

        super().__init__(
            border=ft.Border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
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
    
                app.create_new_story(title, self.page) # Needs the story object
                self.page.pop_dialog()
    
    
            
    
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
                    ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    ft.TextButton(
                        "Create Story", on_click=submit_new_story, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)
                    )
                ],
            )
    
            # Open our dialog in the overlay
            self.page.show_dialog(dlg)

        
    
    
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
                    stories.append(ft.Radio(expand=False, value=story.data.get('id'), label=story.data.get('title'), label_style=style, mouse_cursor=ft.MouseCursor.CLICK))
    
                # Return our list of stories
                return stories
    
    
            # Called when the 'open' button is clicked in the bottom right of the dialog
            async def open_selected_story(e=None):
                ''' Changes the route to the selected story '''
    
                #print("Open button clicked, selected story is: ", selected_story)
    
                if selected_story is not None:
                    await self.page.push_route(app.stories[selected_story].route)
                    app.settings.story = app.stories[selected_story]  # Gives our settings widget the story reference it needs
                    self.page.pop_dialog()
                    self.page.update()
                else:
                    print("No story selected")
    
                self.page.pop_dialog()
                self.page.update()
    
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
                    ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    open_button,
                ]
            )
    
            # Opens our dialog
            self.page.show_dialog(dlg)

        def handle_rename_story(e: ft.Event=None):


            async def rename_story(e=None):
                self.story.rename(title_tf.value)
                
                

            title_tf = ft.TextField(
                value=self.story.data.get('title', ''),
                autofocus=True, capitalization=ft.TextCapitalization.WORDS,
                on_submit=rename_story,
            )

            dlg = ft.AlertDialog(
                
                # Title of our dialog
                title=ft.Text(
                    f"Rename {self.story.data.get('title', '')}", 
                    color=ft.Colors.ON_SURFACE,
                    weight=ft.FontWeight.BOLD,
                ),
    
                # Main content is text box for user to input story title
                content=title_tf,
    
                # Our two action buttons at the bottom of the dialog
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    ft.TextButton("Rename", on_click=rename_story,style=ft.ButtonStyle(mouse_cursor="click")),
                ],
            )
    
            # Open our dialog in the overlay
            self.page.show_dialog(dlg)

        async def handle_import_story(e=None):
            """Import a complete story export into the app's story directory."""
            destination_path = None

            try:
                folder_path = await ft.FilePicker().get_directory_path()
                if not folder_path:
                    return

                folder_path = os.path.normpath(folder_path)
                content_source_path = os.path.join(folder_path, "content")
                story_files = [
                    item for item in os.listdir(folder_path)
                    if item.lower().endswith(".json")
                    and os.path.isfile(os.path.join(folder_path, item))
                ]

                if not os.path.isdir(content_source_path) or len(story_files) != 1:
                    raise ValueError(
                        "The selected folder must contain a content folder and one story JSON file."
                    )

                story_file_name = story_files[0]
                story_file_path = os.path.join(folder_path, story_file_name)
                with open(story_file_path, "r", encoding="utf-8") as story_file:
                    story_data = json.load(story_file)

                story_id = story_data.get("id")
                if not story_id or story_file_name != f"{story_id}.json":
                    raise ValueError("The story JSON file name must match the story id.")
                if os.path.basename(story_id) != story_id or os.path.normpath(story_id) != story_id:
                    raise ValueError("The story id must be a simple folder name.")

                os.makedirs(STORIES_DIRECTORY_PATH, exist_ok=True)
                candidate_destination_path = os.path.join(STORIES_DIRECTORY_PATH, story_id)
                if os.path.exists(candidate_destination_path):
                    raise FileExistsError(
                        f"A story with id '{story_id}' already exists."
                    )
                destination_path = candidate_destination_path

                old_content_path = os.path.normpath(
                    story_data.get("content_directory_path", content_source_path)
                )
                new_content_path = os.path.join(destination_path, "content")

                story_data.update({
                    "directory_path": destination_path,
                    "content_directory_path": new_content_path,
                    "canvas_directory_path": os.path.join(destination_path, "canvas"),
                    "file_path": os.path.join(destination_path, f"{story_id}.json"),
                })

                rebased_folders = {}
                for old_path, folder_data in story_data.get("folders", {}).items():
                    old_path = os.path.normpath(old_path)
                    try:
                        relative_path = os.path.relpath(old_path, old_content_path)
                    except ValueError:
                        continue
                    if relative_path == os.pardir or relative_path.startswith(os.pardir + os.sep):
                        continue
                    new_path = os.path.normpath(os.path.join(new_content_path, relative_path))
                    rebased_folders[new_path] = folder_data.copy()
                story_data["folders"] = rebased_folders

                shutil.copytree(folder_path, destination_path)

                imported_story = Story(story_data.get("title", story_id), story_data)

                for dirpath, _, _ in os.walk(new_content_path):
                    if os.path.normpath(dirpath) == os.path.normpath(new_content_path):
                        continue
                    await imported_story.create_folder(
                        name=os.path.basename(dirpath),
                        update=False,
                        full_path=dirpath,
                    )

                for dirpath, _, filenames in os.walk(new_content_path):
                    for filename in filenames:
                        if not filename.lower().endswith(".json"):
                            continue

                        widget_path = os.path.join(dirpath, filename)
                        try:
                            with open(widget_path, "r", encoding="utf-8") as widget_file:
                                widget_data = json.load(widget_file)
                        except (json.JSONDecodeError, OSError):
                            continue

                        if "tag" not in widget_data or "id" not in widget_data:
                            continue

                        widget_data["directory_path"] = dirpath
                        with open(widget_path, "w", encoding="utf-8") as widget_file:
                            json.dump(widget_data, widget_file, indent=4)

                await imported_story.save_file()
                app.stories[story_id] = imported_story
                app.settings.story = imported_story
                await self.page.push_route(imported_story.route)
                self.page.update()

            except OSError as error:
                self.page.show_dialog(SnackBar(f"Error importing story: {error}"))
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                if destination_path and os.path.isdir(destination_path):
                    shutil.rmtree(destination_path, ignore_errors=True)
                self.page.show_dialog(SnackBar(f"Error importing story: {error}"))
            

        async def handle_export_story(e=None):
            """Export the story directory contents into a selected folder."""
            folder_path = await ft.FilePicker().get_directory_path()
            story_dir_path = self.story.data.get("directory_path")

            if not folder_path or not story_dir_path:
                return

            source_path = os.path.abspath(os.path.normpath(story_dir_path))
            destination_path = os.path.abspath(os.path.normpath(folder_path))
            if source_path == destination_path:
                return

            try:
                shutil.copytree(
                    source_path,
                    destination_path,
                    dirs_exist_ok=True,
                )
            except OSError as error:
                self.page.show_dialog(SnackBar(f"Error exporting story: {error}"))
    
        

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
            if self.page.route != "/settings":
                await self.page.push_route("/settings")
            else:
                # Get the active story title and find its route
                if self.story is not None:
                    await self.page.push_route(self.story.route)
                else:
                    await self.page.push_route("/")

        async def handle_delete_story(e=None):

            async def confirm_delete(e=None):
                try:

                    story_id = self.story.data.get('id')
                    deleted_id = app.stories.pop(story_id)
                    app.settings.story = None                    

                    story_dir_path = self.story.data.get('directory_path')
                    full_norm = os.path.normcase(os.path.normpath(story_dir_path))
                    
                    # Delete the folder from storage
                    shutil.rmtree(full_norm)

                    ft.context.page.pop_dialog()
                    await ft.context.page.push_route("/")
                    ft.context.page.show_dialog(SnackBar(f"{self.story.data.get('title', 'Story')} deleted successfully."))

                    ft.context.page.title = "Story Board (alpha)"
                    ft.context.page.update()

                except Exception as e:
                    ft.context.page.show_dialog(SnackBar(f"Error deleting story: {e}"))
                


            dlg = ft.AlertDialog(
                title=ft.Text(f"Delete {self.story.data.get('title', 'Story')}?", weight=ft.FontWeight.BOLD),
                content=ft.Text("Are you sure you want to delete this story? This action cannot be undone!"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                    ft.TextButton("DELETE FOREVER", on_click=confirm_delete,style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.RED)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            ft.context.page.show_dialog(dlg)

            
    
        # Create our menu bar with submenu items
        file_options = ft.MenuBar(
            #expand=True,
            style=ft.MenuStyle(     # Styling our menubar
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.TRANSPARENT,
                shadow_color=ft.Colors.TRANSPARENT,
                padding=ft.Padding.all(0)
            ),
            controls=[  # The controls shown in our menu bar from left to right
                ft.SubmenuButton(   # Button that opens a subment
                    content=ft.Container(
                        content=ft.Text("File", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),     # Content of subment button
                        alignment=ft.Alignment.CENTER
                    ), 
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    menu_style=ft.MenuStyle(padding=ft.Padding.all(0)),
                    
                    controls=[      # The options shown inside of our button
                        ft.MenuItemButton(
                            content=ft.Text("New Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, ft.Colors.PRIMARY),
                            close_on_click=True,
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=handle_create_story,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Open Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            leading=ft.Icon(ft.CupertinoIcons.BOOK, ft.Colors.PRIMARY),
                            close_on_click=True,
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=handle_open_story,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Rename Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            leading=ft.Icon(ft.Icons.EDIT_OUTLINED, ft.Colors.PRIMARY),
                            close_on_click=True, disabled=self.story is None,
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=handle_rename_story,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Import Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            tooltip="Import a folder containing an exported story from Story Board on another device.",
                            leading=ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.PRIMARY),
                            close_on_click=True,
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=handle_import_story,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Export Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            leading=ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED, ft.Colors.PRIMARY),
                            close_on_click=True, disabled=self.story is None,
                            tooltip="Export's your story to a folder on your device. Allows for easy import to Story Board on another device.",
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=handle_export_story,
                        ),
                        
                        ft.MenuItemButton(
                            content=ft.Text("Toggle Canvas Rail", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            leading=ft.Icon(
                                ft.Icons.VISIBILITY_OUTLINED if app.settings.data.get('story', {}).get('show_canvas_rail', False) else ft.Icons.VISIBILITY_OFF_OUTLINED,
                                ft.Colors.PRIMARY
                            ),
                            close_on_click=True, 
                            disabled=self.story is None,
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=toggle_show_canvas_rail,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Settings", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY),
                            close_on_click=True, 
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=handle_settings_clicked,
                        ),
                        ft.MenuItemButton(
                            content=ft.Text("Delete Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                            leading=ft.Icon(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR),
                            close_on_click=True, disabled=self.story is None,
                            style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                            on_click=handle_delete_story,
                        ),
                    ],
                ),
            ], 
        )







        # DRAW MODE STUFFF -----------------------------------------------------



        
        

        # Create our menu bar with submenu items
        drawing_controls = ft.MenuBar(
            #expand=True,
            visible=self.page.platform.is_mobile(),
            style=ft.MenuStyle(     # Styling our menubar
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.TRANSPARENT,
                shadow_color=ft.Colors.TRANSPARENT,
            ),
            controls=[  # Segment button of draw mode, brush options, and dropdown of saved brushes with option to save current
                
                ft.Container()
            ], 
        )

        self.content = ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                file_options,    # File options button

                drawing_controls,   # Main drawing controls

                ft.Row([        # Row that has alpha text, info button, and settings button
                    ft.Text(
                        "Alpha", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, 
                        tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nJoin the Discord (Settings -> Resources) to suggest your features and report bugs"
                    ),  # Feedback button
                    ft.Icon(
                        ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, 
                        tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nJoin the Discord (Settings -> Resources) to suggest your features and report bugs"
                    ),
                    ft.IconButton(ft.Icons.SETTINGS_OUTLINED, "primary", on_click=handle_settings_clicked, mouse_cursor=ft.MouseCursor.CLICK),   # Settings button
                ], tight=True, spacing=0)
            ]
        )