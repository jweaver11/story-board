'''
An extended flet Canvas that acts as a size aware container that is the parent class of all our story objects. 
A widget is essentially a tab Handles uniform UI, and has some functionality all objects need for easy data use.
Every widget has its own json file
Only Widgets create mini widgets
'''

import flet as ft
from models.views.story import Story
import os
import json
from styles.colors import dark_gradient
from styles.colors import colors
from styles.snack_bar import SnackBar
from styles.menu_option_style import MenuOptionStyle
import flet.canvas as cv
import asyncio
import uuid
from styles.text_fields import TextField



@ft.control
class Widget(ft.Container):
    
    # Constructor. All widgets require a title,  page reference, directory path, and story reference
    def __init__(
        self, 
        title: str,             # Title of our widget
        directory_path: str,    # Path to our directory that will contain our json file
        story: Story,           # Reference to our story object that owns this widget
        data: dict = None,       # Our data passed in if loaded (or none if new object)
        is_new: bool = False   # Whether to verify/create data fields or not. Set to false when rebuilding
    ):

        # Parent constructor to set data and other attributes
        super().__init__(
            data=data, 
            on_size_change=self._set_size, 
            size_change_interval=50
        )
        
        self.is_new: bool = is_new 

        # Give us default data if we're new. Child class will for a file save
        if self.is_new == True:
            self.data = {
                'id': str(uuid.uuid4()),       # Unique ID for each widget
                'title': title,                            # Title of our widget  
                'directory_path': directory_path,          # Directory path to the file this widget's data is stored in
                'tag': str(),                              # Tag to identify what type of widget this is
                'index': 999,                  # Index of this widget in the workspace (start at end)
                'rail_index': 999,                 # Index of this widget in the rail for sorting (start at end)
                'visible': True,                  # Whether this widget is visible in the workspace or not
                'color': "primary",                   # Color of this widget's tab and icon in workspace and on rail
                'image_base64': str(),                 # Base64 string of the image for this widget, if it has one
                'show_sidebar': False,               # Whether to show the sidebar. Widgets that use it set to True in their own data
                'notes': list(),          # Several widgets have notes
                'description': str(),
            } 

        # Set title and story references
        self.story: Story = story   
        
        # Apply our visibility
        self.visible = self.data.get('visible', True)

        # State tracking for widgets
        self.w: int = 0          # Width of content space of the widget
        self.h: int = 0          # Height of content space of the widget
        self.needs_file_write: bool = False        # Whether we need to write to file or not. Set to true when data changes, and false when saved  
                       
        # Sidebar controls
        self.sidebar_title: ft.Text       # Title of the sidebar for this widget that sits in the header
        self.sidebar_header: ft.Row       # Header that is shared by all widgets using the sidebar. Gives them a title, open settings button, and close button
        self.sidebar_body: ft.Column      # Column that holds the header and any other content for the sidebar
        self.sidebar: ft.Container      # Container on right side of widgets to hold mini widgets or sidebar info
        self.show_sidebar_button: ft.IconButton     # Button to show the sidebar when it is hidden. Only shows when sidebar is hidden
        self.sidebar_notes_label: ft.Row
        self.sidebar_notes_column: ft.Column

        # Other shared controls
        self.description_tf: TextField      # Description of this widget textfield. Mostly used in sidebar, but can be used in body
        self.select_image_button: ft.GestureDetector    # Button certain widgets use when they have an image to represent them (world, character, item, etc.)

    # Updates data for this widget and marks it as dirty for the next file save
    def update_data(self, **kwargs):
        
        # Allow updating of nested dicts without overriding the entire dict
        def _merge_data(target: dict, updates: dict):
            for key, value in updates.items():
                current_value = target.get(key)
                if isinstance(current_value, dict) and isinstance(value, dict):
                    _merge_data(current_value, value)
                else:
                    target[key] = value

        _merge_data(self.data, kwargs)  # Merge the new data into the existing data

        # Mark widget as dirty for file write
        if self.needs_file_write == False:
            self.needs_file_write = True

    # Writes our current data to the correct json file if we are dirty
    async def save_file(self):
        if self.needs_file_write:
            print("Saving widget to file: ", self.data.get('title', 'Untitled'))

            file_path = os.path.join(self.data.get('directory_path'), f"{self.data.get('id')}.json")

            try:
                os.makedirs(self.data.get('directory_path'), exist_ok=True)     # Make sure directory exists still
                
                # Save our json data to the file
                with open(file_path, "w", encoding='utf-8') as f:   
                    json.dump(self.data, f, indent=4)

                self.needs_file_write = False   # Mark as clean
                self.is_new = False   # Mark as not new anymore
            except Exception as e:
                print(f"Error saving widget {self.data.get('title', 'untitled')} to file: {e}")
            
    # Called when moving widget files
    async def delete_file(self) -> bool:
        ''' Deletes our widget's json file from the directory '''

        try:

            # File path to save our json data to
            old_file_path = os.path.join(self.data.get('directory_path'), f"{self.data.get('id')}.json")

            # Delete the file if it exists
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
                return True 
            else:
                print(f"File {old_file_path} does not exist, cannot delete.")
                return False

        # Handle errors
        except Exception as e:
            self.page.show_dialog(SnackBar(f"Error deleting file {old_file_path}: {e}"))
            return False
        
    # Called when moving widget files
    async def move_file(self, new_directory: str) -> bool:
        ''' Deletes our old file and updates our directory, then saves the new file there '''

        if new_directory == self.data.get('directory_path', ''):
            return
    
        # Delete our old file
        if await self.delete_file():

            # If it was successful, update our directory path and key, then save our new file
            
            self.update_data(**{'directory_path': new_directory})
            await self.save_file()

            # Reload the rail to apply changes
            self.story.active_rail.reload_rail()
            return True
        else:
            return False
        
    # Called when mouse hovers over the tab part of the widget
    def set_mouse_coords(self, e: ft.PointerEvent):
        ''' Updates our mouse x/y state for opening menu at mouse position '''
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y

    # Called when our widget resizes so we can track size 
    async def _set_size(self, e: ft.LayoutSizeChangeEvent[ft.Container]):
        self.w = e.width
        self.h = e.height
        await self._set_sidebar_size()  # Adjusts our sidebar size

    # Adjust our sidebars size if visible whenever we resize
    async def _set_sidebar_size(self):
        if self.data.get('show_sidebar', False) == True:
            self.sidebar.width = self.w / 4 
            self.sidebar.update()

    # Animates to show our mini widgets container
    async def show_sidebar(self, e: ft.Event=None):
        # If we're already showing, return early
        if self.data.get('show_sidebar', True):
            return
        
        # Update data
        self.update_data(**{'show_sidebar': True})
 
        # Make button hiddent and seperate update to prevent animation from being skipped
        self.show_sidebar_button.visible = False
        self.show_sidebar_button.update()
        
        # Set our sidebar's width
        self.sidebar.width = self.w / 4 
        self.sidebar.update()   
        
        
    # Animates to hide our mini widgets container
    async def hide_sidebar(self, e: ft.Event=None):
        # If we're already hidden, return early
        if not self.data.get('show_sidebar', True):
            return
        
        # Update data
        self.update_data(**{'show_sidebar': False})
        
        # Show the button to show the sidebar again, and update it so it shows before the animation starts
        self.show_sidebar_button.visible = True
        self.show_sidebar_button.update()

        # Run animation to width of 0
        self.sidebar.width = 0
        self.sidebar.update()

    # Opens the widget settings menu for the current widget and scrolls to that section
    async def open_widget_settings(self, e: ft.Event=None):
        from models.app import app
        app.settings.selected_index = 1
        widget_type = self.data.get('tag', '')
        await self.page.push_route("/settings")

        # Scroll to this specific widget
        await app.settings.body_container.content.scroll_to(scroll_key=widget_type, duration=1200)


    # Options when setting the image of a widget. Either upload, set a canvas, or clear image
    def set_widget_image_options(self) -> list[ft.Control]:

        # Called when clicking our upload image button 
        async def upload_image(e: ft.Event):
            await self.story.close_menu()   # Close menu

            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:

                file_path = files[0].path
                try:
                    import base64

                    with open(file_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        # Save to our data
                        self.update_data(**{'image_base64': f"{encoded_string}"})

                    # Update the image in our widget
                    self.select_image_button.content.icon = ft.Container(
                        ft.Image(
                            src=self.data.get('image_base64', ""),
                            width=150,
                            height=150,
                            fit=ft.BoxFit.FILL,
                        ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                    )
                    self.select_image_button.update()

                except Exception:
                    pass

        # Sets a canvas as our image
        async def set_canvas_as_image(e: ft.Event):
            await self.story.close_menu()   # Close menu

        # Resets our image to nothing and our button to the placeholder
        async def clear_image(e: ft.Event):
            await self.story.close_menu()   # Close menu
            self.update_data(**{'image_base64': ""})
            self.select_image_button.content.icon = ft.Icons.IMAGE_OUTLINED
            self.select_image_button.update()

        # Build the options
        return [
            MenuOptionStyle(
                on_click=upload_image,
                content=ft.Row([
                    ft.Icon(ft.Icons.IMAGE_SEARCH_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text("Upload Image", weight=ft.FontWeight.BOLD), 
                ]),
            ),
            MenuOptionStyle(
            on_click=set_canvas_as_image,
                content=ft.Row([
                    ft.Icon(ft.Icons.BRUSH_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text("Set Canvas (WIP)", weight=ft.FontWeight.BOLD), 
                ], tooltip="Set a canvas as the image for this widget"),
            ),
            MenuOptionStyle(
                on_click=clear_image,
                content=ft.Row([
                    ft.Icon(ft.Icons.HIDE_IMAGE_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text("Clear Image", weight=ft.FontWeight.BOLD), 
                ]),
            ),
        ]
        

    

    # Called to show the widget in the workspace
    async def show_widget(self, e=None):
        ''' Shows this widget in the workspace if it is hidden '''

        # If we're already visible, focus our tab
        if self.data.get('visible', False) == True:
            await self.story.workspace.tabs.move_to(self.data.get('index', 0), animation_duration=100)  # Select the new widget tab
            self.story.update_data(**{'workspace_selected_index': self.data.get('index', 0)})
            return
        
        # Update our data to be visible
        self.update_data(**{'visible': True})  
        await self.save_file()  # We lose state tracking upon being shown since we get rebuilt, so force a save to maintain data

        await self.story.workspace.add_widget_to_workspace(self)  # Adds ourselves to the workspace and focus our tab
       
    # Called to hide the widget from the workspace
    async def hide_widget(self, e=None):
        ''' Hides this widget from the workspace but keeps it in the story and rail '''
        # Skip if already hidden (should be impossible)
        if not self.visible:
            return
        
        self.update_data(**{'visible': False})
        await self.story.workspace.remove_widget_from_workspace(self)
        

    # Called when right clicking our tab
    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            MenuOptionStyle(
                on_click=self.rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        
                    ), 
                ]),
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")), 
                        ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self.get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Change this widget's color"
                ),
                no_padding=True, no_effects=True
            ),
            #MenuOptionStyle(
                #on_click=self.delete_clicked,
                #content=ft.Row([
                    #ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    #ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                #]),
            #)
        ]
    
    
    async def rename_clicked(self, e: ft.Event):
        ''' Replaces our widget title with a text field to rename it '''

        await self.story.close_menu()   # Close the menu so it doesn't interfere with the dialog

        # Called when submitting our textfield.
        async def _submit_name(e: ft.Event):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''          

            name = text_field.value.strip()
                                                    
            # Update our live title, and associated data
            self.update_data(**{'title': name.capitalize()})   # Update our data with the new title and key
            await self.save_file()  # Force a file save
                    
            if self.story.data.get("selected_rail", "content") != "canvas":
                self.story.active_rail.reload_rail()   # Reload the rail to reflect the name change

            if self.data.get('visible', False) == True:
                await self.story.workspace.update_widget_tab_title(self.data.get('index'), self.data.get('title'))  # Update the title of the tab in the workspace if we're visible
            
            e.page.pop_dialog()
                
            
        # Our text field that our functions use for renaming and referencing
        text_field = ft.TextField(
            value=self.data.get('title', ''), 
            dense=True, capitalization=ft.TextCapitalization.WORDS,
            focus_color=self.data.get('color', ft.Colors.PRIMARY),
            border_color=self.data.get('color', ft.Colors.PRIMARY),
            autofocus=True, 
            data=self.data.get('tag', ''),
            text_style=ft.TextStyle(
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            on_submit=_submit_name,
            on_blur=lambda: e.page.pop_dialog(),
        )

        rename_button = ft.TextButton("Rename", on_click=_submit_name, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click"))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Rename {self.data.get('title', '')}", weight=ft.FontWeight.BOLD),
            content=text_field,
            actions=[
                ft.TextButton("Cancel", style=ft.ButtonStyle(ft.Colors.ERROR, mouse_cursor="click"), on_click=lambda: e.page.pop_dialog()),
                rename_button   
            ]
        )

        e.page.show_dialog(dlg)
        
    
    def get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        async def _change_icon_color(e=None):
            ''' Passes in our kwargs to the widget, and applies the updates '''
            color = e.control.data

            # Update the data
            self.update_data(**{'color': color})
            await self.save_file()  # Force a file save to persist the color change
            
            if self.data.get('visible', False) == True:
                await self.story.workspace.update_widget_tab_color(self.data.get('index'), self.data.get('color'))  # Update the color of the tab in the workspace if we're visible

            if self.story.data.get("selected_rail", "content") != "canvas":
                self.story.active_rail.reload_rail()   # Reload the rail to reflect the color change
            await self.story.close_menu()

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.MenuItemButton(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=_change_icon_color, close_on_click=True, data=color,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click")
                )
            )

        return color_controls
    
    # Called when the delete button is clicked in the menu options
    def delete_clicked(self, e: ft.Event):
        ''' Deletes this file from the story '''
        from models.app import app

        async def _delete_confirmed(_=ft.Event):
            ''' Deletes the widget after confirmation '''
            
            if await self.delete_file():
                self.story.widgets.pop(self.data.get('id', ''), None)   # Remove ourselves from the story's widgets
                
            self.story.active_rail.reload_rail()    # Reload the rail to reflect the deletion

            if self.data.get('visible', False) == True:
                await self.story.workspace.remove_widget_from_workspace(self)  # Remove ourselves from the workspace if we were visible

            e.page.pop_dialog()

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.data.get('title', '')} forever? This cannot be undone!", weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda: e.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click")),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
            ]
        )

        self.story.close_menu_instant()

        e.page.show_dialog(dlg)
        

    # Called when mouse hovers over the map
    async def _get_coords(self, e: ft.PointerEvent):
        ''' Sets our coordinate positions for menus and passing in new items '''
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y
        self.l = e.local_position.x
        self.t = e.local_position.y

    
        

    # Called in constructor to build our sidebar controls
    def build_sidebar(self):

        # Create a new note in data, then add it to the column
        async def create_new_note(e: ft.Event):
            self.data.get('notes', []).append("")
            self.update_data(**{'notes': self.data.get('notes', [])})
            self.sidebar_notes_column.controls.append(
                create_new_note_ctrl(
                    note_idx = len(self.data.get('notes', [])) - 1,
                    note_value = self.data.get('notes', [])[-1]
                )
            )
            self.sidebar_notes_column.update()
            
        # Returns a textfield of the note control
        def create_new_note_ctrl(note_idx: int, note_value: str) -> TextField:
            return TextField(
                note_value, data=note_idx, expand=True,
                suffix_icon=ft.IconButton(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR, on_click=delete_note, mouse_cursor=ft.MouseCursor.CLICK)
            )

        # Deletes the note from data and then the column and updates the indices
        async def delete_note(e: ft.Event):
            note_idx = e.control.parent.data
            self.data.get('notes', []).pop(note_idx)
            self.update_data(**{'notes': self.data.get('notes', [])})
            self.sidebar_notes_column.controls.pop(note_idx)
            self.sidebar_notes_column.update()
            update_note_indices()

        # Updates all our notes ctrls (textfields) data to be accurate after an index was deleted
        def update_note_indices():
            for idx, ctrl in enumerate(self.sidebar_notes_column.controls):
                ctrl.data = idx

        # Title that sits in the header
        self.sidebar_title = ft.Text(
            f"{self.data.get('title', '')}", theme_style=ft.TextThemeStyle.TITLE_LARGE, 
            color=self.data.get('color', None), weight=ft.FontWeight.BOLD)

        # Header that is shared by all widgets using the sidebar. Gives them a title, open settings button, and close button
        self.sidebar_header = ft.Row([
            self.sidebar_title,    # Title of widget
            
            ft.Container(expand=True),      # Spacer
            ft.IconButton(          # Close/Collapse the sidebar
                ft.Icons.CLOSE, self.data.get('color', ft.Colors.PRIMARY), on_click=self.hide_sidebar,
                mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                tooltip="Collapse Sidebar"
            ),
        ], spacing=0)

        # Where we build the different content in each sidebar
        self.sidebar_body = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

        # The label for Notes with a new note button and textfield
        self.sidebar_notes_label = ft.Row([
            ft.Text("Notes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, self.data.get('color', "primary"), 
                tooltip="Add Note",
                on_click=create_new_note,
                mouse_cursor="click"
            ),
            
        ], spacing=0)

        self.sidebar_notes_column = ft.Column(
            [create_new_note_ctrl(idx, value) for idx, value in enumerate(self.data.get('notes', []))]
        )

        # Button to show the sidebar when it is hidden. Only shows when sidebar is hidden
        self.show_sidebar_button = ft.IconButton(
            ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
            on_click=self.show_sidebar, 
            mouse_cursor=ft.MouseCursor.CLICK,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            visible=not self.data.get('show_sidebar', True),
            tooltip="Show Sidebar",
            #style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
        )

        # Container on right side of widgets to hold mini widgets or sidebar info
        self.sidebar = ft.Container(
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.all(10),
            shadow=ft.BoxShadow(0, 1), 
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            width=0, # Start collapsed, and when we are built it will expand if needed
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            content=ft.Column([     # Holds our header seperated by the body
                self.sidebar_header, 
                ft.Divider(),
                self.sidebar_body,
            ], expand=True, spacing=0)
        )

        

        # OLD
        #ft.IconButton(      # Open the settings fo this type of widget
            #ft.Icons.SETTINGS_OUTLINED, self.data.get('color', ft.Colors.PRIMARY),
            #on_click=self.open_widget_settings, 
            #mouse_cursor=ft.MouseCursor.CLICK,
            #tooltip=f"Open Settings for {self.data.get('tag', '').capitalize()} widgets."
        #),


    # Builds functionality for widget
    def build(self):
        self.build_sidebar()

        self.select_image_button = ft.GestureDetector(
            ft.IconButton(
                ft.Container(
                    ft.Image(
                        src=self.data.get('image_base64', ""),
                        width=150,
                        height=150,
                        fit=ft.BoxFit.FILL,
                    ), shape=ft.BoxShape.CIRCLE, clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                ) if self.data.get('image_base64', '') else ft.Icons.IMAGE_OUTLINED, 
                self.data.get('color'), icon_size=150,
                tooltip="Upload an Image for this widget", mouse_cursor=ft.MouseCursor.CLICK,
                on_click=lambda: self.story.open_menu(self.set_widget_image_options()), 
            ),
            on_hover=self.set_mouse_coords,
            hover_interval=100
        )

        # Description textfield we use in the sidebar
        self.description_tf = ft.TextField(
            value=self.data.get('description', ''), label="Description",
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_color=ft.Colors.TRANSPARENT,
            margin=ft.Margin.only(top=4),
            focused_border_color=ft.Colors.PRIMARY,
            multiline=True, dense=True, expand=True, 
            on_blur=lambda e: self.update_data(**{'description': e.control.value}),
            capitalization=ft.TextCapitalization.SENTENCES,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY) 
        )   