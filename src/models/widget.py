'''
An extended flet container that is the parent class of all our story objects. A widget is essentially a tab
Handles uniform UI, and has some functionality all objects need for easy data use.
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



class Widget(ft.Container):
    
    # Constructor. All widgets require a title,  page reference, directory path, and story reference
    def __init__(
        self, 
        title: str,             # Title of our object
        page: ft.Page,          # Grabs a page reference for updates
        directory_path: str,    # Path to our directory that will contain our json file
        story: Story,           # Reference to our story object that owns this widget
        data: dict = None       # Our data passed in if loaded (or none if new object)
    ):

        # Sets uniformity for all widgets
        super().__init__(
            expand=True, 
            data=data,                              # Sets our data. 
            border_radius=ft.border_radius.all(10),
            gradient=dark_gradient,
            margin=ft.margin.all(0),
            padding=ft.padding.only(top=0, bottom=8, left=8, right=8),
        )

    
        # Set our parameters
        self.title: str = title                     
        self.p: ft.Page = page                               
        self.directory_path: str = directory_path        
        self.story: Story = story                

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_tag",  # Unique key for this widget based on directory path + title
                'title': self.title,                            # Title of our widget  
                'directory_path': self.directory_path,          # Directory path to the file this widget's data is stored in
                'tag': str,                                     # Tag to identify what type of widget this is
                'pin_location': "main" if data is None else data.get('pin_location', "main"),       # Pin location this widget is rendered in the workspace (main, left, right, top, or bottom)
                'index': int,                                   # Index of this widget in its pin location
                'visible': True,                                # Whether this widget is visible in the workspace or not
                'is_active_tab': True,                          # Whether this widget's tab is the active tab in the main pin
                'custom_fields': dict,                          # Dictionary for any custom fields the widget wants to store
            },
        )


        # Apply our visibility
        self.visible = self.data['visible'] 

        # Tracks variable to see if we should outline the widget where it is displayed
        self.focused = False

        # UI ELEMENTS - Tab
        self.tabs: ft.Tabs = ft.Tabs() # Tabs control to hold our tab. We only have one tab, but this is needed for it to render. Nests in self.content
        self.tab: ft.Tab = ft.Tab()  # Tab that holds our title and hide icon. Nests inside of a ft.Tabs control
        self.icon: ft.Icon = ft.Icon()
        self.tab_text: ft.Text = ft.Text()
        self.hide_tab_icon_button: ft.IconButton = ft.IconButton()    # 'X' icon button to hide widget from workspace'

        # UI ELEMENTS - Body                   
        self.mini_widgets: list = []   

        # Currently active mini widget being focused on
        self.active_mini_widget: ft.Control = None

        # Column for displaying our mini widgets on the left, right, or both sides of our body
        self.mini_widgets_row: ft.Row = ft.Column(spacing=4)  
        
        self.body_container: ft.Container = ft.Container(expand=True)  # Stack to hold our body content, with mini widgets overlaid on top

        self.master_stack: ft.Stack = ft.Stack(expand=True)

        # Called at end of constructor for all child widgets to build their view (not here tho since we're not on page yet)
        #self.reload_widget()

    # Called whenever there are changes in our data
    def save_dict(self):
        ''' Saves our current data to the json file '''

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
            print("Data that failed to save: ", self.data)

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
            self.p.open(SnackBar(f"Error deleting file {old_file_path}: {e}"))
            return False
        
    # Called when moving widget files
    def move_file(self, new_directory: str):
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
                self.p.open(SnackBar(f"Cannot move {self.title}. A widget with that name already exists in the target directory."))
                return 
            
        # Delete our old file
        if self.delete_file():

            # If it was successful, update our directory path and key, then save our new file
            self.directory_path = new_directory
            self.data['directory_path'] = new_directory
            self.data['key'] = new_key
            self.save_dict()

            # Reload the rail to apply changes
            self.story.active_rail.content.reload_rail()


    # Called when renaming a widget
    def rename(self, title: str):
        ''' Renames our widget in live title, data, and json file '''
        
        # Hides the widget while renaming to make sure pointers are updated as well
        self.toggle_visibility() 

        # Save our old file path for renaming later
        old_file_path = os.path.join(self.directory_path, f"{self.title}_{self.data.get('tag', '')}.json")  
        old_key = f"{self.directory_path}\\{self.title}"  
                                                 
        # Update our live title, and associated data
        self.title = title.capitalize()                              
        self.data['title'] = self.title     
        self.data['key'] = f"{self.directory_path}\\{return_safe_name(self.title)}_{self.data.get('tag', '')}"  

        # Rename our json file so it doesnt just create a new one
        os.rename(old_file_path, self.data['key'] + ".json")  

        # Save our data to this new file
        self.save_dict()                                

        # Remove from our live dict wherever we are stored
        tag = self.data['tag']

        # Delete our old live saved object, and add the new one
        if tag == "chapter":
            self.story.chapters.pop(old_key, None)
            self.story.chapters[self.data['key']] = self
        elif tag == "canvas":
            self.story.canvases.pop(old_key, None)
            self.story.canvases[self.data['key']] = self
        elif tag == "note":
            self.story.notes.pop(old_key, None)
            self.story.notes[self.data['key']] = self
        elif tag == "character":
            self.story.characters.pop(old_key, None)
            self.story.characters[self.data['key']] = self
        elif tag == "map":
            self.story.maps.pop(old_key, None)
            self.story.maps[self.data['key']] = self  
        elif tag == "timeline":
            self.story.timelines.pop(old_key, None)
            self.story.timelines[self.data['key']] = self


        # Re-applies visibility to what it was before rename
        self.toggle_visibility()                

        # Reload our widget ui and rail to reflect changes 
        self.reload_widget()           
        self.set_active_tab()              
        self.story.active_rail.content.reload_rail()   

    # Called on many actions to make this the active tab if in the main pin
    def set_active_tab(self):
        ''' Sets this widgets tab as the active tab in the main pin'''

        self.data['is_active_tab'] = True
        self.save_dict()

        # Deactivate all other widgets in main pin
        for widget in self.story.widgets:
            if widget != self and widget.data['pin_location'] == "main" and widget.visible:
                widget.data['is_active_tab'] = False
                widget.save_dict()

        # Reload the workspace to reflect changes
        self.story.workspace.reload_workspace()


    # Called when a new mini note is created inside a widget
    def create_comment(self, title: str):
        ''' Creates a mini note inside an image or chapter '''
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
    async def start_drag(self, e: ft.DragStartEvent):
        ''' Shows our pin drag targets. Needs its own function or story is not initialized on first launch, causing crash '''
        self.story.workspace.show_pin_drag_targets()
        
    # Called when mouse enters the tab part of the widget
    async def enter_tab(self, e):
        ''' Changes the hide icon button color slightly for more interactivity '''
        self.hide_tab_icon_button.icon_color = ft.Colors.ON_SURFACE
        try:
            self.page = self.p
            self.update()
        except:
            self.p.update()

    # Called when mouse hovers over the tab part of the widget
    async def hover_tab(self, e):
        ''' Updates our mouse x/y state for opening menu at mouse position '''
        self.story.mouse_x = e.global_x
        self.story.mouse_y = e.global_y

    # Called when mouse stops hovering over the tab part of the widget
    async def stop_hover_tab(self, e):
        ''' Reverts the color change of the hide icon button '''
        self.hide_tab_icon_button.icon_color = ft.Colors.OUTLINE
        self.page = self.p
        self.update()
        

    # Called when app clicks the hide icon in the tab
    def toggle_visibility(self, e=None, value: bool=None):
        ''' Hides the widget from our workspace and updates the json to reflect the change '''

        # If we want to specify we're visible or not, we can pass it in
        if value is not None:
            self.data['visible'] = value
            self.visible = value
        
        else:
            # Change our visibility data, save it, then apply it
            self.data['visible'] = not self.data['visible']
            self.visible = self.data['visible']

        # Save our changes and reload the UI
        self.save_dict()
        self.reload_widget()

        # Protect first launch
        if self.story.workspace is not None:
            self.story.workspace.reload_workspace()

    # Called when right clicking our tab
    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            MenuOptionStyle(
                #on_click=self._rename_clicked,
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
                    expand=True, tooltip="Change this item's color",
                    padding=ft.Padding(0,0,0,0),
                    content=ft.Row(
                        expand=True,
                        controls=[
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=ft.Colors.PRIMARY),
                            ft.Text("Color", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True), 
                        ]
                    ),
                    items=self._get_color_options()
                ),
            ),
            MenuOptionStyle(
                #on_click=_self.delete_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]
    
    # Called when color button is clicked
    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        def _change_icon_color(color: str):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            self.change_data(**{'color': color})
            
            # Change our icon to match, apply the update
            self.story.active_rail.content.reload_rail()
            self.reload_widget()
            

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.PopupMenuItem(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=lambda e, col=color: _change_icon_color(col)
                )
            )

        return color_controls
    
    # Called at end of constructor
    def reload_tab(self):
        ''' Creates our tab for our widget that has the title and hide icon '''

        # Grabs our tag to determine the icon we'll use
        tag = self.data.get('tag', '')

        # Set our icon based on what type of widget we are using tag
        match tag:
            case "chapter": self.icon = ft.Icon(ft.Icons.DESCRIPTION_OUTLINED)
            case "canvas": self.icon = ft.Icon(ft.Icons.BRUSH_OUTLINED)
            case "canvas_board": self.icon = ft.Icon(ft.Icons.DASHBOARD_OUTLINED)
            case "note": self.icon = ft.Icon(ft.Icons.COMMENT_OUTLINED)
            case "character": self.icon = ft.Icon(ft.Icons.PERSON_OUTLINE)
            case "family_tree": self.icon = ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED)
            case "timeline": self.icon = ft.Icon(ft.Icons.TIMELINE_ROUNDED)
            case "map": self.icon = ft.Icon(ft.Icons.MAP_OUTLINED)
            case "world_building": self.icon = ft.Icon(ft.Icons.PUBLIC_OUTLINED)
            case _: self.icon = ft.Icon(ft.Icons.ERROR_OUTLINE)


        # Set the color and size
        self.icon.color = self.data.get('color', ft.Colors.PRIMARY)

        self.tab_text = ft.Text(
            weight=ft.FontWeight.BOLD, # Make the text bold
            theme_style=ft.TextThemeStyle.TITLE_MEDIUM,     # Set to a built in theme (mostly for font size)
            value=self.title,   # Set the text to our title
        )

        # Initialize our tabs control that will hold our tab. We only have one tab, but this is needed for it to render
        self.tabs = ft.Tabs(
            selected_index=0, animation_duration=0,
            padding=ft.padding.all(0), label_padding=ft.padding.all(0),
            mouse_cursor=ft.MouseCursor.BASIC, divider_color=ft.Colors.TRANSPARENT,
            indicator_color = ft.Colors.with_opacity(0.7, self.data.get('color', ft.Colors.PRIMARY)),
        )

        # Our icon button that will hide the widget when clicked in the workspace
        self.hide_tab_icon_button = ft.IconButton(    # Icon to hide the tab from the workspace area
            scale=0.8,
            on_click=lambda e: self.toggle_visibility(),
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Hide",
        )

        self.tab_title_color = ft.Colors.PRIMARY  # The color of the title in our tab and the divider under it

        # Tab that holds our widget title and 'body'.
        # Since this is a ft.Tab, it needs to be nested in a ft.Tabs control or it wont render.
        # We do this so we can use tabs in the main pin area, but still show as a container in other pin areas
        self.tab = ft.Tab(

            # Initialize the content. This will be our content of the body of the widget
            #content=ft.Stack(), 
            

            # Content of the tab itself. Has widgets name and hide widget icon, and functionality for dragging
            tab_content=ft.Draggable(   # Draggable is the control so we can drag and drop to different pin locations
                group="widgets",    # Group for draggables (and receiving drag targets) to accept each other
                data=self.data['key'],  # Pass ourself through the data (of our tab, NOT our object) so we can move ourself around

                # Drag event utils
                on_drag_start=self.start_drag,    # Shows our pin targets when we start dragging

                # Content when we are dragging the follows the mouse
                content_feedback=ft.TextButton(self.title), # Normal text won't restrict its own size, so we use a button

                # The content of our draggable. We use a gesture detector so we have more events
                content=ft.GestureDetector(

                    # Change mouse cursor to the selector cursor when hovering over the tab
                    mouse_cursor=ft.MouseCursor.CLICK,

                    # Event utils for hovering and stop hovering over tab
                    
                    on_enter=self.enter_tab,
                    on_hover=self.hover_tab,
                    on_exit=self.stop_hover_tab,
                    on_secondary_tap=lambda e: self.story.open_menu(self.get_menu_options()),

                    # Content of the gesture detector. This has our actual title and hide icon
                    content=ft.Row([
        
                        self.icon,

                        # The text control that holds our title of the object
                        self.tab_text,

                        # Our icon button that hides the widget when clicked
                        self.hide_tab_icon_button, 
                    ])
                )
            )                    
        )


    # Called by child classes at the end of their constructor, or when they need UI update to reflect changes
    def reload_widget(self):
        ''' Children build their own content of the widget in their own reload_widget functions '''

        # TODO Have option in the mini_widget column to show on mini widgets on right vs left side of widget

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        # Set the body container.content to whatever control you build in the child
        self.body_container.content = ft.Container(expand=True, content=ft.Text(f"hello from: {self.title}"))
            
        # Call Render widget to handle the rest of the heavy lifting
        self._render_widget()

    # Called when changes inside the widget require a reload to be reflected in the UI, like when adding mini widgets
    def _render_widget(self, header: ft.Control = None):
        ''' 
        Takes the 'reload_widget' content and builds the full UI with mini widgets and tab around it 
        header parameter is any part of the body of the widget to be above mini widgets or info displays
        '''

        

        # Set ratio for our body container and mini widgets
        self.body_container.expand = 6
        self.body_container.border_radius = ft.border_radius.all(10)
        self.body_container.padding = ft.padding.all(6)


        

        # Put our mini widgets on the right side
       # row = ft.Row(expand=True, spacing=0, controls=[self.body_container])

        self.master_stack.controls = [self.body_container]

        for mini_widget in self.mini_widgets:

            # Spacing on either left or right of mini widget
            spacing_container = ft.Container(
                ignore_interactions=True,
                expand=6,
            )

            # Row to put our mini widget into
            row = ft.Row(
                spacing=0,
                expand=True,
                tight=False,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    spacing_container,
                    #mini_widget,
                ]
            )

            # Depending if we should be rendered on left or right side
            if mini_widget.data.get('side_location', 'right') == 'right':
                row.controls.append(mini_widget)
            else:
                row.controls.insert(0, mini_widget)

            self.master_stack.controls.append(row)     

        header_container = ft.Container(padding=ft.padding.all(6), content=header) if header is not None else ft.Container(height=0)
        col = ft.Column([
            header_container,
            self.master_stack
        ])   
            
        
        # BUILD OUR TAB CONTENT - Our tab content holds the row of our body and mini widgets containers
        self.tab.content = col  # We add this in combo with our 'tabs' later
        
        # Add our tab to our tabs control so it will render. Set our widgets content to our tabs control and update the page
        self.tabs.tabs = [self.tab]

        self.content = self.tabs

        # First launch is less effecient since page isnt assigned yet
        try:
            self.page = self.p
            self.update()
        except:
            self.p.update()
