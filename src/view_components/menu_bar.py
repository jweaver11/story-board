''' 
Class for our menubar, which will hold our file options, drawing controls, and setting shortcut
'''

import flet as ft
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
from contexts.constants import STORIES_DIRECTORY_PATH
from styles.snack_bar import SnackBar
from dataclasses import dataclass
from view_components.drawing_controls_rail import DrawingControls
from contexts.contexts import AppContext, AppSettingsContext
import asyncio

    

@ft.component
def MenuBar(story: Story=None):

    # Grab our contexts
    page = ft.context.page
    app = ft.use_context(AppContext)
    app_settings = ft.use_context(AppSettingsContext)
    

    # Declare our state variables for our dialogs
    show_new_story_dlg, set_show_new_story_dialog = ft.use_state(False)
    show_open_story_dlg, set_show_open_story_dialog = ft.use_state(False)
    show_rename_story_dlg, set_show_rename_story_dialog = ft.use_state(False)
    show_delete_story_dlg, set_show_delete_story_dialog = ft.use_state(False)

    selected_story_id, set_selected_story_id = ft.use_state("")   # Selected radio value for opening stories


    # State for showing or hiding the drawing controls rail
    show_drawing_controls, set_show_drawing_controls = ft.use_state(app_settings.show_drawing_controls)


    # Called when file -> new is clicked
    def build_new_story_dlg() -> ft.AlertDialog:
        ''' Opens a dialog to create a new story. Checks story is unique or not '''

        # Creates the new story with the given title
        async def submit_new_story(_):
            title = new_story_title.value.strip()
            if not title:
                set_show_new_story_dialog(False)
                return
            page.pop_dialog()   # Force the dialog close before re-routing
            set_show_new_story_dialog(False)    # I dunno, i just like the state being accurate, but this does nothing
            app.create_story(title, app_settings)

        # Set the title for the new story
        new_story_title = ft.TextField(label="Story Title", autofocus=True, capitalization=ft.TextCapitalization.WORDS,on_submit=submit_new_story)

        # Return the dialog
        return ft.AlertDialog(
            title=ft.Text("Create New Story", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
            content=new_story_title,
            # Cancel and create buttons
            actions=[
                ft.TextButton("Cancel", on_click=lambda: set_show_new_story_dialog(False), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                ft.TextButton(
                    "Create Story", on_click=submit_new_story, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)
                )
            ],
            # Handle clicks outside dialog area. Doesn't actually dismiss the dialog, but makes sure state matches
            on_dismiss=lambda _: set_show_new_story_dialog(False),  
        )

    # Called when file -> open is clicked
    def build_open_story_dlg() -> ft.AlertDialog:
        ''' Opens a dialog to open an existing story '''
        
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
                stories.append(ft.Radio(expand=False, value=story.id, label=story.title, label_style=style, mouse_cursor=ft.MouseCursor.CLICK))

            # Return our list of stories
            return stories


        # Called when the 'open' button is clicked in the bottom right of the dialog
        def open_selected_story(_):
            ''' Changes the route to the selected story '''

            page.pop_dialog()
            set_show_open_story_dialog(False)

            # If we have a selected story, navigate to it, and set our settings context to match
            if selected_story_id:
                story = app.stories[selected_story_id]
                page.navigate(story.route)
                app_settings.route = story.route

        # Our alert dialog that pops up when file -> open is clicked
        return ft.AlertDialog(
            title=ft.Text(
                "What story would you like to open?",
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            content=ft.RadioGroup(
                value=selected_story_id,
                content=ft.Column(scroll=ft.ScrollMode.AUTO, expand=False, tight=True, controls=get_stories_list()),
                on_change=lambda e: set_selected_story_id(e.control.value),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda: set_show_open_story_dialog(False), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                ft.TextButton(
                    "Open", on_click=open_selected_story, disabled=not selected_story_id, 
                    style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click")
                    if selected_story_id 
                    else 
                    ft.ButtonStyle(mouse_cursor="click"),
                )
            ],
            on_dismiss=lambda: set_show_open_story_dialog(False),
        )

    def build_rename_story_dlg() -> ft.AlertDialog:

        def rename_story(_):
            story.title = title_tf.value
            set_show_rename_story_dialog(False)

        title_tf = ft.TextField(
            value=story.title,
            autofocus=True, capitalization=ft.TextCapitalization.WORDS,
            on_submit=rename_story,
        )

        return ft.AlertDialog(
            # Title of our dialog
            title=ft.Text(
                f"Rename {story.title}", 
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),

            # Main content is text box for user to input story title
            content=title_tf,

            # Our two action buttons at the bottom of the dialog
            actions=[
                ft.TextButton("Cancel", on_click=lambda: set_show_rename_story_dialog(False), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                ft.TextButton(
                    "Rename", on_click=rename_story, 
                    style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)
                    if title_tf.value.strip() or title_tf.value != story.title
                    else 
                    ft.ButtonStyle(mouse_cursor="click"),
                ),
            ],
            on_dismiss=lambda: set_show_rename_story_dialog(False),
        )


    # Create dialogs for stories. Could be all one use_dialog function, but this looks nicer
    ft.use_dialog(build_new_story_dlg() if show_new_story_dlg else None)
    ft.use_dialog(build_open_story_dlg() if show_open_story_dlg else None)
    ft.use_dialog(build_rename_story_dlg() if show_rename_story_dlg else None)


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
            
            page.navigate(imported_story.route)
            app_settings.route = imported_story.route

        except OSError as error:
            print(f"Error importing story: {error}")
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            if destination_path and os.path.isdir(destination_path):
                shutil.rmtree(destination_path, ignore_errors=True)
            print(f"Error importing story: {error}")
        

    async def handle_export_story(e=None):
        """Export the story directory contents into a selected folder."""
        folder_path = await ft.FilePicker().get_directory_path()
        story_dir_path = story.directory_path

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
            print(f"Error exporting story: {error}")

    
    # Updates whether to show drawing controls or not
    def toggle_show_drawing_controls(e: ft.Event[ft.MenuItemButton]):
        ''' Toggles the visibility of the canvas rail on the left side of the page '''
       
        new_value = not show_drawing_controls
        set_show_drawing_controls(new_value)
        app_settings.show_drawing_controls = new_value

    async def handle_settings_clicked(e=None):
        ''' Goes to the settings page '''
        
        if page.route != "/settings":
            page.navigate("/settings")
        else:
            # Get the active story title and find its route
            if story is not None:
                page.navigate(story.route)
            else:
                page.navigate("/")

        print("Change route to: ", page.route)


    async def build_delete_story_dlg(e=None):

        async def confirm_delete(e=None):
            try:

                app.stories.pop(story.id)

                full_norm = os.path.normcase(os.path.normpath(story.directory_path))
                
                # Delete the folder from storage
                shutil.rmtree(full_norm)

                #ft.context.page.pop_dialog()
                ft.context.page.navigate("/")
                #ft.context.page.show_dialog(SnackBar(f"{story.title} deleted successfully."))

                ft.context.page.title = "Story Board (alpha)"
                #ft.context.page.update()

            except Exception as e:
                ft.context.page.show_dialog(SnackBar(f"Error deleting story: {e}"))

            set_show_delete_story_dialog(False)
            


        return ft.AlertDialog(
            title=ft.Text(f"Delete {story.title}?", weight=ft.FontWeight.BOLD),
            content=ft.Text("Are you sure you want to delete this story? This action cannot be undone!"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda: page.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
                ft.TextButton("DELETE FOREVER", on_click=confirm_delete,style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        

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
                    #content=ft.Text("File", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),     # Content of subment button
                    content=ft.Icon(ft.Icons.MENU, ft.Colors.PRIMARY),
                    alignment=ft.Alignment.CENTER
                ), 
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                menu_style=ft.MenuStyle(padding=ft.Padding.all(0)),
                #width=40,
                controls=[      # The options shown inside of our button
                    ft.MenuItemButton(
                        content=ft.Text("New Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_ROUNDED, ft.Colors.PRIMARY),
                        close_on_click=True,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=lambda: set_show_new_story_dialog(True),
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Open Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.CupertinoIcons.BOOK, ft.Colors.PRIMARY),
                        close_on_click=True,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=lambda: set_show_open_story_dialog(True),
                    ),
                    ft.MenuItemButton(
                        content=ft.Text("Rename Story", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(ft.Icons.EDIT_OUTLINED, ft.Colors.PRIMARY),
                        close_on_click=True, disabled=not story,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=lambda: set_show_rename_story_dialog(True),
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
                        close_on_click=True, disabled=story is None,
                        tooltip="Export's your story to a folder on your device. Allows for easy import to Story Board on another device.",
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=handle_export_story,
                    ),
                    
                    ft.MenuItemButton(
                        content=ft.Text("Hide Drawing Controls" if show_drawing_controls else "Show Drawing Controls", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),
                        leading=ft.Icon(
                            ft.Icons.VISIBILITY_OUTLINED if show_drawing_controls else ft.Icons.VISIBILITY_OFF_OUTLINED,
                            ft.Colors.PRIMARY
                        ),
                        close_on_click=True, 
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=toggle_show_drawing_controls,
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
                        close_on_click=True, disabled=story is None,
                        style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4),),
                        on_click=lambda: set_show_delete_story_dialog(True),
                    ),
                ],
            ),
        ], 
    )



    return ft.Container(
        ft.Row(
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                file_options,    # File options button

                ft.Row(controls=DrawingControls(app_settings, story), alignment=ft.MainAxisAlignment.CENTER, visible=show_drawing_controls),


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
        ),
        border = ft.Border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
        bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST,
        #padding=ft.Padding.only(left=10)
    )