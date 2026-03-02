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
            #bgcolor=ft.Colors.SURFACE_CONTAINER,
            #margin=ft.Margin.all(0),
            #padding=ft.Padding.only(top=0, bottom=8, left=8, right=8),
            #on_size_change=self._get_size if data.get('pin_location', "main") != "main" else None,   # Only track size changes if we are not in the main pin, since main pin widgets have a different resizing behavior that causes issues with the sizing canvas
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
                    'key': f"{self.directory_path}\\{return_safe_name(self.title)}_tag",  # Unique key for this widget based on directory path + title
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

        # Canvas and state trackers for sizing our widget
        self.w: int = 0                                         # Width of our widget
        self.h: int = 0                                         # Height of our widget
        self.l: int = 0      # Values to pass into locations for left and top coordinates
        self.t: int = 0
        self.is_renaming: bool = False                          # Whether we are currently renaming this widget or not
        self.mini_widgets_displayed_overtop: bool = True        # If miniwidgets are displayed overtop the content inside the stack, or to the side (shrinking the content)
        self.force_size_render: bool = True                      # Forces a reload when widgets get their size for the first time, but not every time

        # UI ELEMENTS - Tab
        self.tabs: ft.Tabs = None # Tabs control to hold our tab. We only have one tab, but this is needed for it to render. Nests in self.content
        self.tab: ft.Tab = ft.Tab()  # Tab that holds our title and hide icon button. Nests inside of a ft.Tabs control
        self.icon: ft.Icon = None

        # UI ELEMENTS - Body                     
        self.header: ft.Control = None              # Optional header control to display above our body and mini widgets
        self.side_bar: ft.Control = None            # Optional side bar control to display to the side of our body

        # File picker
        self.file_picker = ft.FilePicker()  # File picker for uploading, saving, etc
    
        # Container that holds our main body content. Gets built in reload_widget of child classes
        self.body_container = ft.Container(expand=True, border_radius=ft.BorderRadius.all(10), padding=ft.Padding.all(16), on_size_change=self._get_size, size_change_interval=500) 

        # Holds our sizing canvas, body container, header, and mini widgets all under the tab
        self.master_stack: ft.Stack = ft.Stack(expand=True)   # Master stack that holds all our elements together. Gets added to our tab content in reload_widget
        self.mini_widgets = []                      # List of mini widgets that belong to this widget

        # Called at end of constructor for all child widgets to build their view (not here tho since we're not on page yet)
        #self.reload_widget()


    # Called whenever there are changes in our data
    def save_dict(self):
        ''' Saves our current data to the json file '''

        # TODO: Find matching widget type and save to normal data dict (not widget dict)

        try:

            # Protect on initialization from creating two files
            if self.data.get('tag', '') == '':
                return
            
            # Update our key
            self.data['key'] = f"{self.directory_path}\\{self.title}_{self.data.get('tag', '')}"
            
            # File path to save our json data to
            file_path = os.path.join(self.directory_path, f"{self.title}_{self.data.get('tag', '')}.json")

            # Create the directory if it doesn't exist. Catches errors from users deleting folders
            os.makedirs(self.directory_path, exist_ok=True)
            
            # Save the data to the file (creates file if doesnt exist)
            with open(file_path, "w", encoding='utf-8') as f:   
                json.dump(self.data, f, indent=4)
        
        # Handle errors
        except Exception as e:
            print(f"Error saving widget to {file_path}: {e}") 
            #print("Data that failed to save: ", self.data)

    # Called for little data changes
    def change_data(self, **kwargs):
        ''' Changes a key/value pair in our data and saves the json file '''
        # Called by:
        # widget.change_data(**{'key': value, 'key2': value2})

        try:
            for key, value in kwargs.items():
                self.data.update({key: value})

            self.save_dict()

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

            self.save_dict()

        # Handle errors
        except Exception as e:
            print(f"Error changing custom field {key}:{value} in widget {self.title}: {e}")

    # Called when moving widget files
    def delete_file(self) -> bool:
        ''' Deletes our widget's json file from the directory '''

        try:

            # File path to save our json data to
            old_file_path = os.path.join(self.directory_path, f"{self.title}_{self.data.get('tag', '')}.json")

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
    def move_file(self, new_directory: str) -> bool:
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
            self.save_dict()

            # Reload the rail to apply changes
            self.story.active_rail.display_active_rail(self.story)
            return True
        else:
            return False

    # Called when our canvas resizes
    async def _get_size(self, e: ft.LayoutSizeChangeEvent[ft.Container]):
        ''' Updates our w and h variables when sizing canvas resizes '''
        if e.width <= 0 or e.height <= 0:
            return 
        self.w = e.width
        self.h = e.height

        #print("New size for ", self.title, ": ", self.w, self.h)

        # Mini widgets won't show unless we re-render on launch since first render has no size reference to grab them with
        if self.force_size_render:
            self.force_size_render = False
            self._render_widget()
        
    # Called when renaming a widget
    def rename(self, title: str):
        ''' Renames our widget in live title, data, and json file '''
        
        # Hides the widget while renaming to make sure pointers are updated as well
        self.toggle_visibility() 

        # Save our old file path for renaming later
        old_file_path = os.path.join(self.directory_path, f"{self.title}_{self.data.get('tag', '')}.json")  
        old_key = f"{self.directory_path}\\{self.title}_{self.data.get('tag', '')}"  
                                                 
        # Update our live title, and associated data
        self.title = title.capitalize()                              
        self.data['title'] = self.title     
        self.data['key'] = f"{self.directory_path}\\{return_safe_name(self.title)}_{self.data.get('tag', '')}"  

        # Rename our json file so it doesnt just create a new one
        os.rename(old_file_path, self.data['key'] + ".json")  

        # Save our data to this new file
        self.save_dict()                                

        # Remove from our live dict wherever we are stored
        tag = self.data.get('tag', '')

        match tag:
            case "document":
                self.story.documents.pop(old_key, None)
                self.story.documents[self.data['key']] = self
            case "canvas":
                self.story.canvases.pop(old_key, None)
                self.story.canvases[self.data['key']] = self
            case "note":
                self.story.notes.pop(old_key, None)
                self.story.notes[self.data['key']] = self
            case "character":
                self.story.characters.pop(old_key, None)
                self.story.characters[self.data['key']] = self
            case "map":
                self.story.maps.pop(old_key, None)
                self.story.maps[self.data['key']] = self
            case "plotline":
                self.story.plotlines.pop(old_key, None)
                self.story.plotlines[self.data['key']] = self
                self.information_display.change_data(**{'title': self.title})   # Passes in our name change to the information display so it can update any references to this plotline
                self.information_display.reload_mini_widget(no_update=True)
            case "world":
                self.story.worlds.pop(old_key, None)
                self.story.worlds[self.data['key']] = self
            case "canvas_board":
                self.story.canvas_boards.pop(old_key, None)
                self.story.canvas_boards[self.data['key']] = self
            case "character_connection_map":
                self.story.character_connection_maps.pop(old_key, None)
                self.story.character_connection_maps[self.data['key']] = self

            case _:
                print(f"Unknown tag {tag} when renaming widget {self.title}")

        # Re-applies visibility to what it was before rename
        self.toggle_visibility()                

        # Reload our widget ui and rail to reflect changes 
        self.reload_widget()           
        self.story.active_rail.content.reload_rail()   



    # Called when a new mini note is created inside a widget
    def create_comment(self, title: str):
        ''' Creates a mini note inside an image or document '''
        from models.mini_widgets.comment import Comment

        self.mini_widgets.append(
            Comment(
                title=title, 
                owner=self, 
                father=self,
                page=self.p, 
                dictionary_path="mini_notes",
                data=None
            )
        )

        self.reload_widget()


    # Called when a draggable starts dragging.
    async def _start_drag(self, e: ft.DragStartEvent):
        ''' Shows our pin drag targets. Needs its own function or story is not initialized on first launch, causing crash '''
        self.story.workspace.show_pin_drag_targets()
        
    # Called when mouse enters the tab part of the widget
    async def _enter_tab(self, e: ft.PointerEvent):
        ''' Changes the hide icon button color slightly for more interactivity '''
        e.control.icon_color = ft.Colors.ON_SURFACE
        e.control.update()
        

    # Called when mouse hovers over the tab part of the widget
    async def _hover_tab(self, e: ft.PointerEvent):
        ''' Updates our mouse x/y state for opening menu at mouse position '''
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y
        

    # Called when mouse stops hovering over the tab part of the widget
    async def _exit_tab(self, e):
        ''' Reverts the color change of the hide icon button '''
        e.control.icon_color = ft.Colors.OUTLINE
        e.control.update()

    # Called when app clicks the hide icon in the tab
    def toggle_visibility(self, e=None, value: bool=None):
        ''' Hides the widget from our workspace and updates the json to reflect the change '''

        # If we want to specify we're visible or not, we can pass it in
        if value is not None:
            self.data['visible'] = value
        else:
            # Change our visibility data, save it, then apply it
            self.data['visible'] = not self.data['visible']

        # Make us not the active tab if we were the one
        if self.data.get('is_active_tab', False) and not self.data.get('visible'):
            self.data['is_active_tab'] = False

        # Save our changes and reload the UI
        self.save_dict()
       
        self.story.workspace.reload_workspace()     # No matter what we are getting rebuilt, so just reload teh workspace

    # Called when right clicking our tab
    def _get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            MenuOptionStyle(
                on_click=self._rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    expand=True, tooltip=f"Change {self.title}'s color",
                    padding=ft.Padding(0,0,0,0),
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.COLOR_LENS_OUTLINED), ft.Text("Color", weight=ft.FontWeight.BOLD)]),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    items=self._get_color_options()
                ),
                no_padding=True
            ),
            MenuOptionStyle(
                on_click=self._delete_clicked,
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
                text_field.error_text = error_text

            # Otherwise remove our error text
            else:
                text_field.error_text = None
                
            self.p.update()

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
                text_field.error_text = "Name already exists"
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
                ft.TextButton("Cancel", style=ft.ButtonStyle(ft.Colors.ERROR), on_click=lambda e: self.p.close(dlg)),
                rename_button   
            ]
        )

        # Clears our popup menu button and applies to the UI
        self.p.overlay.clear()
        self.p.show_dialog(dlg)
        
    
    # Called when color button is clicked
    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        async def _change_icon_color(color: str):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            self.change_data(**{'color': color})
            
            # Change our icon to match, apply the update
            self.story.active_rail.content.reload_rail()
            self.reload_widget()
            if self.data.get('pin_location', '') == 'main':
                self.story.workspace.reload_workspace()
            

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.PopupMenuItem(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=lambda e, col=color: self.p.run_task(_change_icon_color, col)
                )
            )

        return color_controls
    
    # Called when the delete button is clicked in the menu options
    def _delete_clicked(self, e):
        ''' Deletes this file from the story '''
        from models.app import app

        def _delete_confirmed(e=None):
            ''' Deletes the widget after confirmation '''

            #self.widget.story.close_menu_instant()
            self.p.pop_dialog()
            self.story.delete_widget(self) 
            self.story.active_rail.content.reload_rail()    # Reload the rail to reflect the deletion
            self.story.active_rail.update()
            self.story.workspace.reload_workspace()

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.title} forever? This cannot be undone!", weight=ft.FontWeight.BOLD),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog()),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ]
        )

        self.story.close_menu_instant()

        if app.settings.data.get('confirm_item_delete', False):
            self.p.show_dialog(dlg)
        else:
            _delete_confirmed()

    async def _open_file_picker(self, e=None):
        await self.fp.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])

        
    async def _set_active_tab(self, e=None):
        self.data['is_active_tab'] = True

        for w in self.story.widgets:
            if w != self:
                w.data['is_active_tab'] = False
                w.save_dict()

        self.save_dict()
        #self.story.workspace.reload_workspace()

    # Called when mouse hovers over the map
    async def _get_coords(self, e: ft.HoverEvent):
        ''' Sets our coordinate positions for menus and passing in new items '''
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y
        self.l = e.local_position.x
        self.t = e.local_position.y
    
    # Called at end of constructor
    def reload_tab(self):
        ''' Creates our tab for our widget that has the title and hide icon '''

        # Grabs our tag to determine the icon we'll use
        tag = self.data.get('tag', '')

        # Set our icon based on what type of widget we are using tag
        match tag:
            case "document": self.icon = ft.Icon(ft.Icons.DESCRIPTION_OUTLINED)
            case "canvas": self.icon = ft.Icon(ft.Icons.BRUSH_OUTLINED)
            case "canvas_board": self.icon = ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED)
            case "note": self.icon = ft.Icon(ft.Icons.COMMENT_OUTLINED)
            case "character": self.icon = ft.Icon(ft.Icons.PERSON_OUTLINE)
            case "character_connection_map": self.icon = ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED)
            case "plotline": self.icon = ft.Icon(ft.Icons.TIMELINE)
            case "map": self.icon = ft.Icon(ft.Icons.MAP_OUTLINED)
            case "world": self.icon = ft.Icon(ft.Icons.PUBLIC_OUTLINED)
            case _: self.icon = ft.Icon(ft.Icons.ERROR_OUTLINE)


        # Set the color and size
        self.icon.color = self.data.get('color', ft.Colors.PRIMARY)

        tab_text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True)

        # Initialize our tabs control that will hold our tab. We only have one tab, but this is needed for it to render
        

        # Our icon button that will hide the widget when clicked in the workspace
        hide_tab_icon_button = ft.IconButton(    # Icon to hide the tab from the workspace area
            scale=0.8,
            on_click=lambda e: self.toggle_visibility(),
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Hide",
        )


        # Tab that holds our widget title and 'body'.
        # Since this is a ft.Tab, it needs to be nested in a ft.Tabs control or it wont render.
        self.tab = ft.Tab(

            # Content of the tab itself. Has widgets name and hide widget icon, and functionality for dragging
            label=ft.Draggable(   # Draggable is the control so we can drag and drop to different pin locations
                group="widgets",    # Group for draggables (and receiving drag targets) to accept each other
                data=self.data['key'],  # Pass ourself through the data (of our tab, NOT our object) so we can move ourself around

                # Drag event utils
                on_drag_start=self._start_drag,    # Shows our pin targets when we start dragging

                # Content when we are dragging the follows the mouse
                content_feedback=ft.TextButton(self.title), # Normal text won't restrict its own size, so we use a button

                # The content of our draggable. We use a gesture detector so we have more events
                content=ft.GestureDetector(
                    ft.Row([self.icon, tab_text, hide_tab_icon_button]),
                    mouse_cursor=ft.MouseCursor.CLICK,
                    hover_interval=100,
                    on_enter=self._enter_tab,
                    on_hover=self._hover_tab,
                    on_exit=self._exit_tab,
                    on_secondary_tap=lambda e: self.story.open_menu(self._get_menu_options()),
                )
            )                    
        )
                         
    


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

        # Separate our mini widgets into left and right side lists
        left_mini_widgets = []
        right_mini_widgets = []

        

        # Go through our mini widgets and separate them into left and right lists based on their side location data
        for mw in self.mini_widgets:
            if mw.data.get('side_location', 'right') == 'left' and mw.data.get('visible', True) != False:
                left_mini_widgets.append(mw)
            elif mw.data.get('side_location', 'right') == 'right' and mw.data.get('visible', True) != False:
                right_mini_widgets.append(mw)
            else:
                right_mini_widgets.append(mw)   # Default to right side if no location specified, or if not visible (so they dont show at all)
            
        # If we show our mini widgets overtop the content, build them here. 
        if self.mini_widgets_displayed_overtop:     # Widgets: Plotline, Map, Character Connection Map, ...

            # Format a column to hold left and right side
            left_column = ft.Column(
                left_mini_widgets, spacing=4, tight=True, width=self.w * .3,
                top=50 if self.header is not None else 0, left=0, bottom=0, expand=True, 
            )
            right_column = ft.Column(
                right_mini_widgets, spacing=4, tight=True, width=self.w * .3, 
                top=50 if self.header is not None else 0, right=0, bottom=0, expand=True, 
            )

            # Add the columns so long as they are showing anything
            if len(left_mini_widgets) > 0:
                self.master_stack.controls.append(left_column)
                #print("Showing mw on left")
                #print("Left column width: ", left_column.width)
            if len(right_mini_widgets) > 0:
                self.master_stack.controls.append(right_column) 
                #print("Showing mw on right")
                #print("Right column width: ", right_column.width)
               
            
            
            # Set the tab content
            self.tab.content = self.master_stack  

        
        # Mini widgets that shrink the body container to make room for themselves
        else:       # Widgets: Canvas, document
            pass


        # If we have a header, add it to the stack. Headers are be immune to scrolling
        self.master_stack.controls.append(self.header) if self.header is not None else None


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

        try:

            # If we are in the main pin, our tab and master_stack are shown, so update those
            if self.data.get('pin_location', '') == 'main':

                self.master_stack.update()       
                self.tab.update()
                self.update()       # Crucial for sub controls to update through the tree to the page, even though we are technically not on it in main

            # If not in the main pin, we are directly on the page, so just update ourselves
            else:
                self.update()
        except Exception as e:
            pass
