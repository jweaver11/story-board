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
from utils.verify_data import verify_data
from utils.safe_string_checker import return_safe_name
from styles.colors import dark_gradient
from styles.colors import colors
from styles.snack_bar import SnackBar
from styles.menu_option_style import MenuOptionStyle
import flet.canvas as cv
import asyncio



@ft.control
class Widget(ft.Container):
    
    # Constructor. All widgets require a title,  page reference, directory path, and story reference
    def __init__(
        self, 
        title: str,             # Title of our object
        page: ft.Page,          # Grabs a page reference for updates
        directory_path: str,    # Path to our directory that will contain our json file
        story: Story,           # Reference to our story object that owns this widget
        data: dict = None,       # Our data passed in if loaded (or none if new object)
        is_rebuilt: bool = True   # Whether to verify/create data fields or not. Set to false when rebuilding
    ):

        # Sets uniformity for all widgets
        super().__init__(
            expand=True, 
            data=data,                              # Sets our data. 
            border_radius=ft.BorderRadius.all(10),
            gradient=dark_gradient,
        )

        # Set our parameters we passed in (data set in super())
        self.title: str = title                     
        self.p: ft.Page = page                               
        self.directory_path: str = directory_path        
        self.story: Story = story                

        # Verifies this object has the required data fields, and creates them if not
        if not is_rebuilt:
            verify_data(
                self,   # Pass in our own data so the function can see the actual data we loaded
                {
                    #'key': f"{self.directory_path}\\{return_safe_name(self.title)}_tag",  # Unique key for this widget based on directory path + title
                    'title': self.title,                            # Title of our widget  
                    'directory_path': self.directory_path,          # Directory path to the file this widget's data is stored in
                    'tag': str,                                     # Tag to identify what type of widget this is
                    'pin_location': "main" if data is None else data.get('pin_location', "main"),       # Pin location this widget is rendered in the workspace (main, left, right, top, or bottom)
                    'index': 999,                                   # Index of this widget in its pin location (start at end)
                    'visible': True,                                # Whether this widget is visible in the workspace or not
                    'is_active_tab': True,                          # Whether this widget's tab is the active tab in the main pin
                    #'color': str,                                  # Color of the icon and tab divider for this widget. Child classes set this on creation  
                    'custom_fields': dict,                          # Dictionary for any custom fields the widget wants to store
                }
            )

        # Apply our visibility
        self.visible = self.data.get('visible', True)

        # State tracking for widgets
        self.w: int = 0          # Width of content space of the widget
        self.h: int = 0          # Height of content space of the widget
        self.l: int = 0          # Left position to pass into mini widgets
        self.t: int = 0          # Top position to pass into mini widgets
        self.skip_update = False                # Skips applying an update on resizes to prevent update loops
        self.ignore_update = False     # Return and ignore updates, such as when hiding??
        self.save_counter = 0      # Used to check how often we write saving to a file to prevent saving constantly

        # If widgets display info overtop content rather than next to it (plotline, map, canvas, etc.)
        self.mini_widgets_displayed_overtop: bool = True       # Widgets that set this false need to set their own mini widgets in reload_widget


        # UI ELEMENTS - Body                     
        self.header: ft.Control = None              # Optional header control to display above our body and mini widgets
        self.side_bar: ft.Control = None            # Optional side bar control to display to the side of our body  
    
        # Container that holds our main body content. Gets built in reload_widget of child classes
        self.body_container = ft.Container(
            expand=True, border_radius=ft.BorderRadius.all(10), padding=ft.Padding.all(16), 
            on_size_change=self._get_size, size_change_interval=500,
        ) 

        # Holds our sizing canvas, body container, header, and mini widgets all under the tab
        self.master_stack: ft.Stack = ft.Stack(expand=True)   # Master stack that holds all our elements together. Gets added to our tab content in reload_widget
        self.mini_widgets = []                      # List of mini widgets that belong to this widget

        # UI ELEMENTS - Tab
        self.tabs: ft.Tabs # Tabs control to hold our tab. We only have one tab, but this is needed for it to render. Nests in self.content
        self.tab: ft.Tab  # Tab that holds our title and hide icon button. Nests inside of a ft.Tabs control
        self.icon: ft.Icon
        self.tab_text: ft.Text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True)

        # Grabs our tag to determine the icon we'll use
        tag = self.data.get('tag', '')

        # Set our icon based on what type of widget we are using tag
        match tag:
            case "document": self.icon = ft.Icon(ft.Icons.DESCRIPTION_OUTLINED)
            case "canvas": self.icon = ft.Icon(ft.Icons.BRUSH_OUTLINED)
            case "canvas_board": self.icon = ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED)
            case "note": self.icon = ft.Icon(ft.Icons.LIBRARY_BOOKS_OUTLINED)
            case "character": self.icon = ft.Icon(ft.Icons.PERSON_OUTLINE)
            case "character_connection_map": self.icon = ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED)
            case "plotline": self.icon = ft.Icon(ft.Icons.TIMELINE)
            case "map": self.icon = ft.Icon(ft.Icons.MAP_OUTLINED)
            case "world": self.icon = ft.Icon(ft.Icons.PUBLIC_OUTLINED)
            case "object": self.icon = ft.Icon(ft.Icons.SHIELD_OUTLINED)
            case _: self.icon = ft.Icon(ft.Icons.ERROR_OUTLINE)


        # Set the color and size
        self.icon.color = self.data.get('color', ft.Colors.PRIMARY)

        tab_text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True)
        
        # Our icon button that will hide the widget when clicked in the workspace
        hide_tab_icon_button = ft.IconButton(    # Icon to hide the tab from the workspace area
            scale=0.8,
            on_click=self.hide_widget,
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Hide",
            mouse_cursor=ft.MouseCursor.CLICK,
        )


        self.tab_gd = ft.GestureDetector(
            ft.Row([self.icon, tab_text, hide_tab_icon_button]),
            mouse_cursor=ft.MouseCursor.CLICK,
            hover_interval=100,
            #on_enter=self._set_coords,
            on_hover=self._set_coords,
            #on_exit=self._exit_tab,
            on_secondary_tap=lambda _: self.story.open_menu(self._get_menu_options()),
        )

        # Tab that holds our widget title and 'body'.
        # Since this is a ft.Tab, it needs to be nested in a ft.Tabs control or it wont render.
        self.tab = ft.Tab(

            # Content of the tab itself. Has widgets name and hide widget icon, and functionality for dragging
            label=ft.Draggable(   # Draggable is the control so we can drag and drop to different pin locations
                group="widgets",    # Group for draggables (and receiving drag targets) to accept each other
                data=self.data.get('key', ""),  # Pass ourself through the data (of our tab, NOT our object) so we can move ourself around

                # Drag event utils
                on_drag_start=self._start_drag,    # Shows our pin targets when we start dragging

                # Content when we are dragging the follows the mouse
                content_feedback=ft.TextButton(self.title), # Normal text won't restrict its own size, so we use a button

                # The content of our draggable. We use a gesture detector so we have more events
                content=self.tab_gd
            )                    
        )

        # Tabs stuff
        self.tabs = ft.Tabs(
            expand=True,  
            length=1,
            selected_index=0,
            content=ft.Column([
                ft.TabBar(tabs=[self.tab]),     # Holds our tab at the top of the widget
                ft.TabBarView([self.master_stack], expand=True)# Holds our body
            ], expand=True),
            
        )   
        self.content = self.tabs

        # Called at end of constructor for all child widgets to build their view (not here tho since we're not on page yet)
        #self.reload_widget()

    def before_update(self):
        print(f"Successful update for widget {self.title}")
        return super().before_update()

    # Called whenever there are changes in our data
    async def save_dict(self) -> bool:
        ''' Saves our current data to the json file '''

        print(f"Saving widget: {self.title}")

        self.save_counter += 1      # Increiment the save counter

        # Check if we need to write to file so we're not making constant writes
        if self.save_counter >= 15:

            try:
                print("Saving widget to file: ", self.title)

                # Make sure our key is accurate if it changed (renamed or moved)
                self.data['key'] = f"{self.directory_path}\\{self.title}_{self.data.get('tag', '')}"

                # File path to save our json data to
                file_path = os.path.join(self.directory_path, f"{self.title}_{self.data.get('tag', '')}.json")

                # Create the directory if it doesn't exist. Catches errors from users deleting folders
                os.makedirs(self.directory_path, exist_ok=True)
                
                # Save the data to the file (creates file if doesnt exist)
                with open(file_path, "w", encoding='utf-8') as f:   
                    json.dump(self.data, f, indent=4)

                self.save_counter = 0   # Reset the save counter

                return True
            
            # Handle errors
            except Exception as e:
                print(f"Error saving widget to {file_path}: {e}") 
                print("Widget data that failed to save:\n")
                for key, value in self.data.items():
                    print(f"{key}: {value}")
                print("\n")
                return False

    # Called for little data changes
    def change_data(self, **kwargs):
        ''' Changes a key/value pair in our data and saves the json file '''
        # Called by:
        # widget.change_data(**{'key': value, 'key2': value2})

        try:
            for key, value in kwargs.items():
                self.data.update({key: value})

            self.p.run_task(self.save_dict)

        # Handle errors
        except Exception as e:
            print(f"Error changing data {key}:{value} in widget {self.title}: {e}")

    def change_custom_field(self, **kwargs):
        ''' Changes a key/value pair in our custom fields dictionary and saves the json file '''
        # Called by:
        # widget.change_custom_field(**{'key': value, 'key2': value2})

        try:
            for key, value in kwargs.items():
                self.data['custom_fields'].update({key: value})

            self.p.run_task(self.save_dict)

        # Handle errors
        except Exception as e:
            print(f"Error changing custom field {key}:{value} in widget {self.title}: {e}")

    # Called when moving widget files
    def delete_file(self) -> bool:
        ''' Deletes our widget's json file from the directory '''

        try:

            # File path to save our json data to
            old_file_path = os.path.normpath(os.path.join(self.data.get('key', "") + ".json"))

            # Delete the file if it exists
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
                return True 
            else:
                print(f"File {old_file_path} does not exist, cannot delete.")
                return False

        # Handle errors
        except Exception as e:
            self.p.show_dialog(SnackBar(f"Error deleting file {old_file_path}: {e}"))
            return False
        
    # Called when moving widget files
    async def move_file(self, new_directory: str) -> bool:
        ''' Deletes our old file and updates our directory, then saves the new file there '''

        if new_directory == self.data.get('directory_path', ''):
            return

        # New key to check for duplicates
        new_key = f"{new_directory}\\{self.title}_{self.data.get('tag', '')}"

        # Go through our widgtes. If any have the same key as our new key, we cannot move, so we return false
        for widget in self.story.widgets:

            # Skip ourselves
            if widget == self:
                continue

            # If this gets triggered, we cannot move since a widget with that name already exists in the target directory. Return out of function
            elif widget.data.get('key', '') == new_key:
                self.p.show_dialog(SnackBar(f"Cannot move {self.title}. A widget with that name already exists in the target directory."))
                return 
            
        # Delete our old file
        if self.delete_file():

            # If it was successful, update our directory path and key, then save our new file
            self.directory_path = new_directory
            self.data['directory_path'] = new_directory
            self.data['key'] = new_key
            self.p.run_task(self.save_dict)
            await asyncio.sleep(0.2)    # Make sure file has time to save before reload

            # Reload the rail to apply changes
            self.story.active_rail.reload_rail()
            return True
        else:
            return False

    # Called when our canvas resizes
    async def _get_size(self, e: ft.LayoutSizeChangeEvent[ft.Container]):
        ''' Updates our w and h when our widgets body container resizes. Widgets who need to run logic override this '''
        if e.width <= 0 or e.height <= 0:
            return 
        self.w = int(e.width)
        self.h = int(e.height)
        
    # Called when renaming a widget
    def rename(self, title: str):
        ''' Renames our widget in live title, data, and json file '''

        # Save our old file path for renaming later
        old_file_path = os.path.join(self.directory_path, f"{self.title}_{self.data.get('tag', '')}.json")  
                                                 
        # Update our live title, and associated data
        self.title = title.capitalize()                              
        self.data['title'] = self.title     
        self.data['key'] = f"{self.directory_path}\\{return_safe_name(self.title)}_{self.data.get('tag', '')}"  

        # Rename our json file so it doesnt just create a new one
        os.rename(old_file_path, self.data['key'] + ".json")  

        # Save our data to this new file
        self.p.run_task(self.save_dict)                                

        # Reload our widget ui and rail to reflect changes 
        self.reload_widget()           
        self.story.active_rail.content.reload_rail()   
        self.story.active_rail.update()

    def create_comment_clicked(self, e=None, side_location: str="left"):
        ''' Opens a dialog to input the mini widgets name, and creates it at that location '''

        # Checks that the name in the textfield does not match any of the existing mini widgets of that type, and updates visually to reflect
        async def _check_name_unique(e):
            name = new_item_tf.value.strip()
            submit_button.disabled = False
            new_item_tf.error = None
            if not name:
                submit_button.disabled = True
            elif tag == "comment" and name in self.comments.keys():
                submit_button.disabled = True
                new_item_tf.error = "Name must be unique"
                await new_item_tf.focus()
            
            else:
                submit_button.disabled = False
                new_item_tf.error = None

            
            new_item_tf.update()
            submit_button.update()
            
        # Create the nwew mini widget with the current text field value. Makes sure we passed checks first
        async def _create_new_mw(e):

            # Button is disabled if name is the same
            if submit_button.disabled:
                await new_item_tf.focus()
                return
            
            title = new_item_tf.value.strip()
            await self.create_comment(title, side_location)
            
            self.p.pop_dialog()   # Close the dialog
            await self.story.close_menu()       

        # Grab the type of mini widget we are creating
        tag = "comment"

        # Textfield for the name of the new mw
        new_item_tf = ft.TextField(
            label=f"Title", expand=True, on_change=_check_name_unique, autofocus=True,
            capitalization=ft.TextCapitalization.WORDS, on_submit=_create_new_mw
        )

        # Button for creating new mw. Can also press enter in the textfield
        submit_button = ft.TextButton("Create", on_click=_create_new_mw, disabled=True)

        # Dialog we open onto the page
        dlg = ft.AlertDialog(
            title=ft.Text(f"New {tag.replace('_', ' ').title()} Name"),
            content=new_item_tf,
            actions=[
                ft.TextButton("Cancel", style=ft.ButtonStyle(color=ft.Colors.ERROR), on_click=lambda e: self.p.pop_dialog()),
                submit_button
            ],
        )

        self.p.show_dialog(dlg)        # Open the dialog. If we do this first, it gets wiped from close_menu

    # Called when a new mini note is created inside a widget
    async def create_comment(self, title: str, side_location: str="left"):
        ''' Creates a mini note inside an image or document '''
        from models.mini_widgets.comment import Comment

        new_comment = Comment(
            title=title, 
            widget=self, 
            page=self.p, 
            key="comments",
            data={'side_location': side_location}
        )
        self.comments[title] = new_comment
        self.mini_widgets.append(
            new_comment
        )
        await new_comment.save_dict()

        self.reload_widget()

    def delete_comment(self, title: str):
        del self.comments[title]


    # Called when a draggable starts dragging.
    async def _start_drag(self, e: ft.DragStartEvent):
        ''' Shows our pin drag targets. Needs its own function or story is not initialized on first launch, causing crash '''
        self.story.workspace.show_pin_drag_targets() 

    # Called when mouse hovers over the tab part of the widget
    async def _set_coords(self, e: ft.PointerEvent):
        ''' Updates our mouse x/y state for opening menu at mouse position '''
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y
        

    # Called to hide the widget from the workspace
    async def hide_widget(self, e=None):
        ''' Hides this widget from the workspace but keeps it in the story and rail '''
        if not self.visible:
            return
        
        self.story.blocker.visible = True
        self.story.blocker.update()
        await asyncio.sleep(0)
             
        self.tab_gd.on_enter = None
        self.tab_gd.on_secondary_tap = None
        self.tab_gd.disabled = True
        self.tab_gd.update()
        await asyncio.sleep(0)  # Spaces update so the page won't batch them
        
        self.data['visible'] = False
        self.story.workspace.reload_workspace()   # Reload workspace to hide the widget and show the placeholder in its pin location
        await self.save_dict() 

        self.story.blocker.visible = False
        self.story.blocker.update()

    # Called to show the widget in the workspace
    async def show_widget(self, e=None):
        ''' Shows this widget in the workspace if it is hidden '''

        self.story.blocker.visible = True
        self.story.blocker.update()
        await asyncio.sleep(0)
        
        self.data['visible'] = True
        self.visible = True
        await self.save_dict()
        self.story.workspace.reload_workspace()   # Reload workspace to show the widget in its pin location
        
        if self.story.blocker.visible:
            self.story.blocker.visible = False
            self.story.blocker.update()
        

    # Called when right clicking our tab
    def _get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            MenuOptionStyle(
                on_click=self._rename_clicked,
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
                    self._get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    tooltip="Change this widget's color"
                ),
                no_padding=True, no_effects=True
            ),
            MenuOptionStyle(
                on_click=self.delete_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]
    
    def _rename_clicked(self, e):
        ''' Replaces our widget title with a text field to rename it '''
        from utils.check_widget_unique import check_widget_unique

        # Track if our name is unique for checks, and if we're submitting or not
        is_unique = True
        submitting = False

        # Grab our current name for comparison
        current_name = self.title.lower()

        # Called when clicking outside the input field to cancel renaming
        def _cancel_rename(e):
            ''' Puts our name back to static and unalterable '''

            # Grab our submitting state
            nonlocal submitting

            # Since this auto calls on submit, we need to check. If it is cuz of a submit, do nothing
            if submitting:
                submitting = not submitting     # Change submit status to False so we can de-select the textbox
                return
            

        # Called everytime a change in textbox occurs
        def _name_check(e):
            ''' Checks if the name is unique within its type of widget '''


            # Nonlocal variables
            nonlocal is_unique
            nonlocal submitting

            # Set submitting to false, and unique to True
            submitting = False
            is_unique = True

            # Grab out title and tag from the textfield, and set our new key to compare
            title = e.control.value
            if title.lower() == current_name:
                return

            # Generate our new key to compare. Requires normalization
            nk = self.directory_path + "\\" + title + "_" + e.control.data
            new_key = os.path.normpath(nk)

            error_text, is_unique = check_widget_unique(self.story, new_key)

            # If we are NOT unique, show our error text
            if not is_unique:
                text_field.error = error_text

            # Otherwise remove our error text
            else:
                text_field.error = None
                
            text_field.update()   # Update our text field to show error or not

        # Called when submitting our textfield.
        def _submit_name(e):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''          

            # Non local variables
            nonlocal is_unique, text_field, submitting, current_name
        
            name = text_field.value
            if name == current_name:
                self.p.pop_dialog()
                return

            # Set submitting to True
            submitting = True

            # If it is, call the rename function. It will do everything else
            if is_unique:
                self.rename(name)
                self.p.pop_dialog()
                
            # Otherwise make sure we show our error
            else:
                text_field.error = "Name already exists"
                text_field.focus()                                  # Auto focus the textfield
                
        # Our text field that our functions use for renaming and referencing
        text_field = ft.TextField(
            value=self.title, 
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
            on_change=_name_check,
            on_blur=_cancel_rename,
        )

        rename_button = ft.TextButton("Rename", on_click=_submit_name, style=ft.ButtonStyle(color=ft.Colors.PRIMARY))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Rename {self.title}", weight=ft.FontWeight.BOLD),
            content=text_field,
            actions=[
                ft.TextButton("Cancel", style=ft.ButtonStyle(ft.Colors.ERROR), on_click=lambda e: self.p.pop_dialog()),
                rename_button   
            ]
        )

        # Clears our popup menu button and applies to the UI
        self.story.close_menu_instant()
        self.p.show_dialog(dlg)
        
    
    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        async def _change_icon_color(e=None):
            ''' Passes in our kwargs to the widget, and applies the updates '''
            color = e.control.data

            # Change the data
            self.change_data(**{'color': color})

            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            
            # Change our icon to match, apply the update
            self.reload_widget()
            self.story.active_rail.reload_rail()   # Reload the rail to reflect the color change
            await self.story.close_menu()

            if self.story.blocker.visible:
                self.story.blocker.visible = False
                self.story.blocker.update()

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.MenuItemButton(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=_change_icon_color, close_on_click=True, data=color,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                )
            )

        return color_controls
    
    # Called when the delete button is clicked in the menu options
    def delete_clicked(self, e):
        ''' Deletes this file from the story '''
        from models.app import app

        async def _delete_confirmed(e=None):
            ''' Deletes the widget after confirmation '''
            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)

            self.p.pop_dialog()
            if self.delete_file():
                if self in self.story.widgets:
                    print("Deleted: ", self.title)
                    self.story.widgets.remove(self)   
            
            await asyncio.sleep(0)
            self.story.active_rail.reload_rail()    # Reload the rail to reflect the deletion
            self.story.workspace.reload_workspace()

            if self.story.blocker.visible:
                self.story.blocker.visible = False
                self.story.blocker.update()

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.title} forever? This cannot be undone!", weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click")),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
            ]
        )

        self.story.close_menu_instant()

        if app.settings.data.get('confirm_item_delete', False):
            self.p.show_dialog(dlg)
        else:
            _delete_confirmed()

        
    async def _set_active_tab(self, e=None):
        self.data['is_active_tab'] = True

        for w in self.story.widgets:
            if w != self:
                w.data['is_active_tab'] = False
                await w.save_dict()

        await self.save_dict()

    # Called when mouse hovers over the map
    async def _get_coords(self, e: ft.HoverEvent):
        ''' Sets our coordinate positions for menus and passing in new items '''
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y
        self.l = e.local_position.x
        self.t = e.local_position.y
    
    # Called at end of constructor
    def reload_tab(self, update: bool=False):
        ''' Creates our tab for our widget that has the title and hide icon '''

        # Set the color and size
        self.icon.color = self.data.get('color', ft.Colors.PRIMARY)

        self.tab_text.value = self.title

        if update:
            try:
                self.tab.update()
            except Exception as _:
                pass

    # Called by child classes at the end of their constructor, or when they need UI update to reflect changes
    def reload_widget(self):
        ''' Children build their own content of the widget in their own reload_widget functions '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        # Setting a header displayed OVERTOP our content we want to build
        self.header = ft.Row(height=50, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text("This is a header")])

        # Set the body_container content to the body of our widget
        self.body_container.content = ft.Container(expand=True, content=ft.Text(f"hello from: {self.title}"))

        # If we wanted to have a header ABOVE the content, and pushing the content down, set it as a column in the body container
        not_self_header = ft.Row(height=50, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text("This is a header")])
        self.body_container.content = ft.Column(controls=[not_self_header, self.body_container.content], expand=True, spacing=0)

        # Call Render widget to handle the rest of the heavy lifting
        self._render_widget()

    # Called when changes inside the widget require a reload to be reflected in the UI, like when adding mini widgets
    def _render_widget(self):

        # Clear out our master stack controls so we start fresh to re-render
        self.master_stack.controls.clear()

        # Add our sizing canvas and body container to the stack first
        self.master_stack.controls = [self.body_container]

        # If we have a header, add it to the stack. Headers are be immune to scrolling
        self.master_stack.controls.append(self.header) if self.header is not None else None

        try:

            # If we are in the main pin, our tab and master_stack are shown, so update those
            if self.data.get('pin_location', '') == 'main':

                self.master_stack.update()       
                self.tab.update()
                self.update()       # Crucial for sub controls to update through the tree to the page, even though we are technically not on it in main

            # If not in the main pin, we are directly on the page, so just update ourselves
            else:
                self.update()
        except Exception as _:
            pass