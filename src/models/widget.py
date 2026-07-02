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
import uuid



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
        super().__init__(data=data, on_size_change=self._set_size, size_change_interval=500)
        self.title: str = title                     
        self.story: Story = story   
        self.is_new = is_new 

        # Give us default data if we're new. Child class will for a file save
        if self.is_new == True:
            self.data = {
                'id': str(uuid.uuid4()),       # Unique ID for each widget
                'title': title,                            # Title of our widget  
                'directory_path': directory_path,          # Directory path to the file this widget's data is stored in
                'tag': str(),                                     # Tag to identify what type of widget this is
                'index': 999,                  # Index of this widget in the workspace (start at end)
                'rail_index': 999,                 # Index of this widget in the rail for sorting (start at end)
                'visible': True,                  # Whether this widget is visible in the workspace or not
                'color': "primary",                   # Color of this widget's tab and icon in workspace and on rail
                'notes': list(),          # Several widgets have notes
            } 

        # Apply our visibility
        self.visible = self.data.get('visible', True)

        # State tracking for widgets
        self.w: int = 0          # Width of content space of the widget
        self.h: int = 0          # Height of content space of the widget
        
        # State tracking
        self.skip_update = False                # Skips applying an update on resizes to prevent update loops
        self.ignore_update = False     # Return and ignore updates, such as when hiding??
        self.needs_file_write: bool = False        # Whether we need to write to file or not. Set to true when data changes, and false when saved

        # If widgets display info overtop content rather than next to it (plotline, map, canvas, etc.)
        self.mini_widgets_displayed_overtop: bool = True       # Widgets that set this false need to set their own mini widgets in reload_widget
        self.no_render_mini_widgets: bool = False           # If we should let the widget render its own mini widgets, or have it handled here


        # UI ELEMENTS - Body                  
        self.mini_widgets_wrapper = ft.Column(expand=1, spacing=0)   # Container that holds our active mini widget. We can add/remove it without having to rebuild

        # Container that holds our main body content. Gets built in reload_widget of child classes
        self.body_container = ft.Container(
            expand=3, #border_radius=ft.BorderRadius.all(10), 
            #padding=ft.Padding.all(16), 
            on_size_change=self._set_size, size_change_interval=500, clip_behavior=ft.ClipBehavior.NONE
        ) 

        # Holds our sizing canvas, body container, header, and mini widgets all under the tab
        self.master_stack: ft.Stack = ft.Stack(expand=True)   # Master stack that holds all our elements together. Gets added to our tab content in reload_widget
        self.mini_widgets = []                      # List of mini widgets that belong to this widget

        # UI ELEMENTS - Tab
        self.tabs: ft.Tabs # Tabs control to hold our tab. We only have one tab, but this is needed for it to render. Nests in self.content
        self.icon: ft.Icon
        self.tab_text: ft.Text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True)

        # Grabs our tag to determine the icon we'll use
        tag = self.data.get('tag', '')
        match tag:
            case "document": icon = ft.Icons.DESCRIPTION_OUTLINED
            case "canvas": icon = ft.Icons.BRUSH_OUTLINED
            case "canvas_board": icon = ft.Icons.SPACE_DASHBOARD_OUTLINED
            case "note": icon = ft.Icons.LIBRARY_BOOKS_OUTLINED
            case "character": icon = ft.Icons.PERSON_OUTLINE
            case "character_connection_map": icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case "plotline": icon = ft.Icons.TIMELINE
            case "map": icon = ft.Icons.MAP_OUTLINED
            case "world": icon = ft.Icons.PUBLIC_OUTLINED
            case "item": icon = ft.Icons.STAR_OUTLINE_ROUNDED
            case "chart": icon = ft.Icons.INSERT_CHART_OUTLINED
            case "comic_preview": icon = ft.Icons.SLIDESHOW_OUTLINED
            case _: icon = ft.Icons.ERROR_OUTLINE


        # Create our icon, text, and hide_button for the tab
        self.icon = ft.Icon(icon, color=self.data.get('color', ft.Colors.PRIMARY))
        tab_text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True)
        hide_tab_icon_button = ft.IconButton(    
            scale=0.8,
            on_click=self.hide_widget,
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Hide",
            mouse_cursor=ft.MouseCursor.CLICK,
        )

        # GD to hold tab elements and open menus
        self.tab_gd = ft.GestureDetector(
            ft.Row([self.icon, tab_text, hide_tab_icon_button]),
            mouse_cursor=ft.MouseCursor.CLICK,
            hover_interval=100,
            on_hover=self.set_mouse_coords,
            on_secondary_tap=lambda: self.story.open_menu(self._get_menu_options()),
            #on_secondary_tap_down=lambda e: print(e)
        )

        # Create the tab itself
        self.tab = ft.Tab(self.tab_gd)

        # Tabs stuff
        self.tabs = ft.Tabs(
            expand=True,  
            length=1,
            selected_index=0,
            content=ft.Column([
                ft.TabBar(tabs=[self.tab], indicator_color=self.data.get('color', ft.Colors.ON_SURFACE_VARIANT)),     # Holds our tab at the top of the widget
                ft.TabBarView([self.master_stack], expand=True, clip_behavior=ft.ClipBehavior.NONE)# Holds our body
            ], expand=True, spacing=0),
        )   


        # TODO: Use this in future for mini widgets:
        self.mini_widgets_container = ft.Container(
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.symmetric(horizontal=10),
            shadow=ft.BoxShadow(0, 1), 
            bgcolor=ft.Colors.SURFACE,
            width=0, 
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            on_animation_end=self.set_mini_widgets_container_expand,
        )
        

    # Temp to improve performance
    def before_update(self):
        #print(f"Widget Update: {self.title}")
        return super().before_update()

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
            print("Saving widget to file: ", self.title)

            file_path = f"{self.data.get('directory_path')}\\{self.data.get('id')}.json"

            try:
                os.makedirs(self.data.get('directory_path'), exist_ok=True)     # Make sure directory exists still
                
                # Save our json data to the file
                with open(file_path, "w", encoding='utf-8') as f:   
                    json.dump(self.data, f, indent=4)

                self.needs_file_write = False   # Mark as clean
                self.is_new = False   # Mark as not new anymore
            except Exception as e:
                print(f"Error saving widget {self.title} to file: {e}")
                self.page.show_dialog(SnackBar(f"Error saving widget {self.title} to file: {e}"))
            
    # Called when moving widget files
    async def delete_file(self) -> bool:
        ''' Deletes our widget's json file from the directory '''

        try:

            # File path to save our json data to
            old_file_path = os.path.normpath(f"{self.data.get('directory_path')}\\{self.data.get('id')}.json")

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

    # Called when our widget resizes so we can track size 
    async def _set_size(self, e: ft.LayoutSizeChangeEvent[ft.Container]):
        self.w = e.width
        self.h = e.height
   

    # Called when mouse hovers over the tab part of the widget
    async def set_mouse_coords(self, e: ft.PointerEvent):
        ''' Updates our mouse x/y state for opening menu at mouse position '''
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y

    # Auto called after mwc is shown, and sets its expand for auto sizing
    async def set_mini_widgets_container_expand(self, e: ft.Event):

        if self.mini_widgets_container.width > 0:
            self.mini_widgets_container.expand = 1
            self.mini_widgets_container.update()

        

    # Animates to show our mini widgets container
    async def show_mini_widgets_container(self, e: ft.Event=None):
        
        # Sets our width and removes auto sizing so we can animate to a width of 1/4 of the widget - button offset
        self.mini_widgets_container.width = self.w / 4 - 15  
        self.mini_widgets_container.expand = None
        self.mini_widgets_container.update()
        

    # Animates to hide our mini widgets container
    async def hide_mini_widgets_container(self, e: ft.Event=None):
        
        # Get rid of expand (auto sizing) since it prevents animation, and set width to 1/4 of widget - button offset
        self.mini_widgets_container.expand = None
        self.mini_widgets_container.width = self.w / 4 - 15  
        self.mini_widgets_container.update()

        # Forces seperate UI Updates that prevent animation from being skipped
        await asyncio.sleep(0.01)  
        
        # Run animation to width of 0
        self.mini_widgets_container.width = 0
        self.mini_widgets_container.update()
        

    # Called to hide the widget from the workspace
    async def hide_widget(self, e=None):
        ''' Hides this widget from the workspace but keeps it in the story and rail '''
        if not self.visible:
            return
        
        #self.story.blocker.visible = True
        #self.story.blocker.update()
        #await asyncio.sleep(0)  # Spaces update so the page won't batch them
        
        self.update_data(**{'visible': False})

        self.story.workspace.reload_workspace()   # Reload workspace to hide the widget and show the placeholder in its pin location

        #self.story.blocker.visible = False
        #self.story.blocker.update()

    # Called to show the widget in the workspace
    async def show_widget(self, e=None):
        ''' Shows this widget in the workspace if it is hidden '''

        #self.story.blocker.visible = True
        #self.story.blocker.update()
        #await asyncio.sleep(0)
        
        self.visible = True
        self.update_data(**{'visible': True, 'index': 999})
        self.story.update_data(**{'workspace_selected_index': len(self.story.workspace.main_pin)}) 

        await self.save_file()  # We lose state tracking upon being shown since we get rebuilt, so force a save

        self.story.workspace.reload_workspace()   # Reload workspace to show the widget in its pin location
        
        #if self.story.blocker.visible:
            #self.story.blocker.visible = False
            #self.story.blocker.update()
        

    # Called when right clicking our tab
    def _get_menu_options(self) -> list[ft.Control]:

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
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
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
    
    # Shows the info column on the side of our chart or not
    async def _toggle_show_info(self, e=None):
        self.update_data(**{'show_info': not self.data.get('show_info', True)})
        self.reload_widget()
        await self.story.close_menu()
    
    async def rename_clicked(self, e: ft.Event):
        ''' Replaces our widget title with a text field to rename it '''

        await self.story.close_menu()   # Close the menu so it doesn't interfere with the dialog

        # Called when submitting our textfield.
        async def _submit_name(e: ft.Event):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''          

            name = text_field.value.strip()

            #self.story.blocker.visible = True
            #self.story.blocker.update()
            #await asyncio.sleep(0)
                                                    
            # Update our live title, and associated data
            self.title = name.capitalize()                              
            self.update_data(**{'title': name.capitalize()})   # Update our data with the new title and key
            await self.save_file()  # Force a file save
                    
            self.story.active_rail.reload_rail()  
            self.story.workspace.reload_workspace()   # Reload workspace to update tab title and sorting if needed 
            #if self.story.blocker.visible:
                #self.story.blocker.visible = False
                #self.story.blocker.update()
            e.page.pop_dialog()
                
            
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
            on_blur=lambda: e.page.pop_dialog(),
        )

        rename_button = ft.TextButton("Rename", on_click=_submit_name, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click"))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Rename {self.title}", weight=ft.FontWeight.BOLD),
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

            #self.story.blocker.visible = True
            #self.story.blocker.update()
            #await asyncio.sleep(0)
            
            # Change our icon to match, apply the update
            if hasattr(self, 'information_display'):
                if self.information_display.visible:
                    self.information_display.reload_mini_widget()
            #self.reload_widget()
            self.story.workspace.reload_workspace()   # Reload workspace to update tab color
            self.story.active_rail.reload_rail()   # Reload the rail to reflect the color change
            await self.story.close_menu()

            #if self.story.blocker.visible:
                #self.story.blocker.visible = False
                #self.story.blocker.update()

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
    def delete_clicked(self, e: ft.Event):
        ''' Deletes this file from the story '''
        from models.app import app

        async def _delete_confirmed(e=ft.Event):
            ''' Deletes the widget after confirmation '''
            #self.story.blocker.visible = True
            #self.story.blocker.update()
            #await asyncio.sleep(0)

            
            if await self.delete_file():
                self.story.widgets.pop(self.data.get('id', ''), None)   # Remove ourselves from the story's widgets
                
            self.story.active_rail.reload_rail()    # Reload the rail to reflect the deletion
            self.story.workspace.reload_workspace()

            #if self.story.blocker.visible:
                #self.story.blocker.visible = False
                #self.story.blocker.update()
            e.page.pop_dialog()

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.title} forever? This cannot be undone!", weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda: e.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click")),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
            ]
        )

        self.story.close_menu_instant()

        if app.settings.data.get('confirm_item_delete', False):
            e.page.show_dialog(dlg)
        else:
            _delete_confirmed()

    # Called when mouse hovers over the map
    async def _get_coords(self, e: ft.PointerEvent):
        ''' Sets our coordinate positions for menus and passing in new items '''
        self.story.mouse_x = e.global_position.x
        self.story.mouse_y = e.global_position.y
        self.l = e.local_position.x
        self.t = e.local_position.y
    
    # Called at end of constructor
    def create_tab(self, update: bool=False):
        ''' Creates our tab for our widget that has the title and hide icon '''

        # TODO: Change to create_tab and only called in build

        # Re-resolve the icon name based on the current tag.
        # New widgets have tag="" at Widget.__init__ time (before child verify_data runs),
        # so create_tab corrects it the first time reload_widget is called.
        tag = self.data.get('tag', '')
        match tag:
            case "document": self.icon.icon = ft.Icons.DESCRIPTION_OUTLINED
            case "canvas": self.icon.icon = ft.Icons.BRUSH_OUTLINED
            case "canvas_board": self.icon.icon = ft.Icons.SPACE_DASHBOARD_OUTLINED
            case "note": self.icon.icon = ft.Icons.LIBRARY_BOOKS_OUTLINED
            case "character": self.icon.icon = ft.Icons.PERSON_OUTLINE
            case "character_connection_map": self.icon.icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case "plotline": self.icon.icon = ft.Icons.TIMELINE
            case "map": self.icon.icon = ft.Icons.MAP_OUTLINED
            case "world": self.icon.icon = ft.Icons.PUBLIC_OUTLINED
            case "item": self.icon.icon = ft.Icons.STAR_OUTLINE_ROUNDED
            case "chart": self.icon.icon = ft.Icons.INSERT_CHART_OUTLINED
            case "comic_preview": self.icon.icon = ft.Icons.SLIDESHOW_OUTLINED
            case "plot_chart": self.icon.icon = ft.Icons.ACCOUNT_TREE_OUTLINED

        # Set our color and text if title changed
        self.icon.color = self.data.get('color', ft.Colors.PRIMARY)
        self.tab_text.value = self.title

        # Chart stuff for future
        #if self.data.get('type', "") == "bar":
            #self.icon.icon = ft.Icons.INSERT_CHART_OUTLINED
        #else:
            #self.icon.icon = ft.CupertinoIcons.COMPASS

        if update:
            try:
                self.tab.update()
            except Exception as _:
                pass


    # Called by child classes at the end of their constructor, or when they need UI update to reflect changes
    def reload_widget(self):
        ''' Children build their own content of the widget in their own reload_widget functions '''

        # TODO: Build tab then have it update correctly

        # Rebuild out tab to reflect any changes
        self.create_tab()

        # Setting a header displayed OVERTOP our content we want to build
        self.header = ft.Row(height=50, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text("This is a header")])

        # Set the body_container content to the body of our widget
        self.body_container.content = ft.Container(expand=True, content=ft.Text(f"hello from: {self.title}"))

        # If we wanted to have a header ABOVE the content, and pushing the content down, set it as a column in the body container
        not_self_header = ft.Row(height=50, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text("This is a header")])
        self.body_container.content = ft.Column(controls=[not_self_header, self.body_container.content], expand=True, spacing=0)

        self._render_widget()
    
     # Called when changes inside the widget require a reload to be reflected in the UI, like when adding mini widgets
    def _render_widget(self):

        # Clear out our master stack controls so we start fresh to re-render
        self.master_stack.controls.clear()

        self.mini_widgets_wrapper.visible = False   # Set false for widgets that dont use this or dont have any mini widgets
        if not self.no_render_mini_widgets:
            
            self.mini_widgets_wrapper.controls = [mw for mw in self.mini_widgets]
            
            # Check if any mini widgets are visible, so we show the wrapper or not
            for mw in self.mini_widgets_wrapper.controls:
                if mw.visible:
                    self.mini_widgets_wrapper.visible = True
                    break


        # Add our sizing canvas and body container to the stack first
        self.master_stack.controls = [
            ft.Row([
                self.body_container, 
                self.mini_widgets_wrapper
            ], spacing=0, expand=True)
        ]

        self.content = self.master_stack

        try:

            
            self.update()
        except Exception as _:
            pass