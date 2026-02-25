import flet as ft
from models.views.story import Story
import os
import json
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
from styles.snack_bar import SnackBar
from utils.check_widget_unique import check_widget_unique
from utils.check_folder_content import return_folder_content
import asyncio
from models.app import app

# Expansion tile for all sub directories (folders) in a directory
class TreeViewDirectory(ft.GestureDetector):

    def __init__(
        self, 
        full_path: str,                                         # Full path to this directory
        title: str,                                             # Title of this folder
        story: Story,                                           # Story reference for mouse positions and other logic
        page: ft.Page,                                          # Page reference for overlay menu
        rail: ft.Control,                                       # Reference to the rail this directory is in
        is_expanded: bool = False,                              # Whether this directory is expanded or not
        color: str = "primary",                                 # Color of the folder icon
        father: 'TreeViewDirectory' = None,                     # Optional parent directory tile, if there is one
        additional_menu_options: list[ft.Control] = None,       # Additional menu options when right clicking a category, depending on the rail
    ):
        
        # Reference for all our passed in data
        self.full_path = full_path
        self.title = title
        self.story = story
        self.p = page
        self.father = father
        self.color = color
        self.is_expanded = is_expanded  
        self.rail = rail
        self.additional_menu_options = additional_menu_options

        # State tracking variables
        self.are_submitting = False
        self.item_is_unique = True

        # Set our text style
        self.text_style = ft.TextStyle(
            size=14,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.BOLD,
        )

        # Textfield for creating new items (sub-categories, chapters, notes, characters, etc.)
        self.new_item_textfield = ft.TextField(  
            hint_text="Sub-Category Name",          
            #data="category",                                       # Data for logic routing on submit
            on_submit=self.new_item_textfield_submit,               # Called when enter is pressed
            autofocus=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=self.on_new_item_blur,
            on_change=self.on_new_item_change,
            visible=False,
            text_style=self.text_style,
            dense=True
        )

        # Parent constructor
        super().__init__(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_secondary_tap=lambda e: self.story.open_menu(self.get_menu_options()),
        )

        self.expansion_tile: ft.ExpansionTile = None

        # Reload our directory tile to set up initial UI
        self.reload()

    # Called when right clicking over our expansion tile
    def get_menu_options(self) -> list[ft.Control]:
        ''' Returns our built in menu options all tree view rails have, and any additional ones passed in '''
   
        # Add our remaining built in options: rename, color change, delete
        return [
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", weight=ft.FontWeight.BOLD)]),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    tooltip="New", menu_padding=0,
                    items=[
                        ft.PopupMenuItem(
                            text="Category", icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                            on_click=self.new_item_clicked, data="category"
                        ),
                        ft.PopupMenuItem(
                            text="Chapter", icon=ft.Icons.NOTE_ADD_OUTLINED,
                            on_click=self.new_item_clicked, data="chapter"
                        ),
                        ft.PopupMenuItem(
                            text="Canvas", icon=ft.Icons.BRUSH_OUTLINED,
                            on_click=self.new_item_clicked, data="canvas"
                        ),
                        ft.PopupMenuItem(
                            "Note", ft.Icons.NOTE_ALT_OUTLINED,
                            on_click=self.new_item_clicked, data="note"
                        ),
                        ft.PopupMenuItem(
                            text="Character", icon=ft.Icons.PERSON_OUTLINED,
                            on_click=self.new_item_clicked, data="character"
                        ),  
                        ft.PopupMenuItem(
                            text="Family Tree", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
                            on_click=self.new_item_clicked, data="family_tree"
                        ),
                        ft.PopupMenuItem(
                            text="Plotline", icon=ft.Icons.TIMELINE_OUTLINED,
                            on_click=self.new_item_clicked, data="plotline"
                        ),
                        ft.PopupMenuItem(
                            text="Map", icon=ft.Icons.MAP_OUTLINED,
                            on_click=self.new_item_clicked, data="map"
                        ),
                        ft.PopupMenuItem(
                            text="World Building", icon=ft.Icons.PUBLIC_OUTLINED,
                            on_click=self.new_item_clicked, data="world_building"
                        ),
                    ]
                ),
                no_padding=True
            ),
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    ft.Container(
                        ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED), ft.Text("Upload", weight=ft.FontWeight.BOLD)]),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    tooltip="Upload", menu_padding=0,
                    items=[
                        ft.PopupMenuItem(text="Image", icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,),
                        ft.PopupMenuItem(text="Chapter", icon=ft.Icons.NOTE_ADD_OUTLINED,),
                        ft.PopupMenuItem(text="Canvas", icon=ft.Icons.BRUSH_OUTLINED,),
                        ft.PopupMenuItem(text="Note", icon=ft.Icons.NOTE_ALT_OUTLINED,),
                        ft.PopupMenuItem(text="Character", icon=ft.Icons.PERSON_OUTLINED,),
                        ft.PopupMenuItem(text="Family Tree", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED),
                        ft.PopupMenuItem(text="Plotline", icon=ft.Icons.TIMELINE_OUTLINED,),
                        ft.PopupMenuItem(text="Map", icon=ft.Icons.MAP_OUTLINED,),
                        ft.PopupMenuItem(text="World Building", icon=ft.Icons.PUBLIC_OUTLINED,),
                    ]
                ),
                no_padding=True
            ),
            # Rename button
            MenuOptionStyle(
                on_click=self.rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),

            # Color changing popup menu
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    expand=True,
                    tooltip="Change category color",
                    padding=None,
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=self.color), ft.Text("Color",  weight=ft.FontWeight.BOLD),]),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    items=self.get_color_options()
                ),
                no_padding=True
            ),
        
            # Delete button
            MenuOptionStyle(
                on_click=lambda e: self._delete_clicked(e),
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            ),
        ]

        # Return our menu options list
        

    # Called when expanding/collapsing the directory
    async def toggle_expand(self, e=None):
        ''' Makes sure our state and data match the updated expanded/collapsed state '''

        self.is_expanded = not self.is_expanded

        self.story.change_folder_data(
            full_path=self.full_path,
            key='is_expanded', value=self.is_expanded
        )

       
    # Called when creating new category or when additional menu items are clicked
    async def new_item_clicked(self, e=None):
        ''' Shows the textfield for creating new item. Requires what type of item (category, chapter, note, etc.) '''

        # Clear out any previous value
        self.new_item_textfield.value = None

        tag = e.control.data

        # Make our textfield visible and set values
        self.new_item_textfield.visible = True
        self.new_item_textfield.data = tag

        match tag:
            case "family_tree":
                self.new_item_textfield.hint_text = "Family Tree Name"
            case "world_building":
                self.new_item_textfield.hint_text = "World Building Name"
            case "character" | "category":
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Name"
            case _:
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Title"


        # Check our expanded state. Rebuild if needed
        if self.is_expanded == False:
            
            await self.toggle_expand()
            self.reload()
            
            
        # Close the menu, which will also update the page
        await asyncio.sleep(.3)
        await self.story.close_menu()

    # Called when clicking off the textfield and after submission
    def on_new_item_blur(self, e):
        ''' Handles if we need to hide our textfield or re-focus it based on submissions '''
        
        # Check if we're submitting, or normal blur
        if self.are_submitting:

            # Change submitting to false
            self.are_submitting = False     

            # If our item is unique, hide the textfield and update
            if self.item_is_unique:
                e.control.visible = False
                e.control.value = None
                e.control.error_text = None
                self.p.update()
                return
            
            # Otherwise its not unique, re-focus our textfield
            else:
                e.control.visible = True
                e.control.focus()
        
        # If we're not submitting, just hide the textfield and reset values
        else:
            e.control.visible = False
            e.control.value = None
            e.control.error_text = None
            self.p.update()


    # Called whenever our user inputs a new key into one of our textfields for new items
    def on_new_item_change(self, e):
        ''' Checks if our title is unique within its directory (default in this case) '''

        # Start out assuming we are unique
        self.item_is_unique = True

        # Grab out title and tag from the textfield, and set our new key to compare
        title = e.control.value
        tag = e.control.data

        # Generate our new key to compare. Requires normalization
        nk = self.full_path + "\\" + title + "_" + e.control.data
        new_key = os.path.normpath(nk)

        if tag == "category":
            new_key = os.path.normcase(os.path.normpath(self.full_path + "\\" + title))
            new_key = new_key.rstrip()  # Remove trailing spaces for folder names
            for key in self.story.data['folders'].keys():
                
                # Path comparisons require normalization
                if os.path.normcase(os.path.normpath(key)) == new_key:
                    self.item_is_unique = False
                    error_text = "Category must be unique."
                    break

        # Not a category, so we check the widget
        else:
            error_text, self.item_is_unique = check_widget_unique(self.story, new_key)

        # If we are NOT unique, show our error text
        if not self.item_is_unique:
            #print("Setting error text:", error_text)
            e.control.error_text = error_text

        # Otherwise remove our error text
        else:
            e.control.error_text = None
            
        self.p.update()

            
    def new_item_textfield_submit(self, e):

        self.are_submitting = True

        title = self.new_item_textfield.value
        tag = self.new_item_textfield.data

        if self.item_is_unique:
            match tag:
                case "category":
                    self.story.create_folder(directory_path=self.full_path, name=title)
                case "chapter" | "canvas" | "note" | "character" | "plotline" | "map":
                    self.story.create_widget(directory_path=self.full_path, title=title, tag=tag)
                
                case _:
                    self.p.open(SnackBar(f"Error creating new item: Unknown type '{tag}'"))
        else:
            self.new_item_textfield.focus()                                  
            self.p.update()

    def category_submit(self, e):
        # Get our name and check if its unique
        name = e.control.value

        # Set submitting to True
        self.are_submitting = True

        # If it is, call the rename function. It will do everything else
        if self.item_is_unique:
            self.story.create_folder(
                directory_path=self.full_path,
                name=name,
            )
            
        # Otherwise make sure we show our error
        else:
            self.new_item_textfield.focus()                                  # Auto focus the textfield
            self.p.update()

    # Called when rename button is clicked
    async def rename_clicked(self, e):

        # Track if our name is unique for checks, and if we're submitting or not
        self.is_unique = True
        self.are_submitting = False

        # Called when clicking outside the input field to cancel renaming
        def _cancel_rename(e):
            ''' Puts our name back to static and unalterable '''

            # Since this auto calls on submit, we need to check. If it is cuz of a submit, do nothing
            if self.are_submitting:
                self.are_submitting = not self.are_submitting     # Change submit status to False so we can de-select the textbox
                return
            
            # Otherwise we're not submitting (just clicking off the textbox), so we cancel the rename
            else:

                self.story.active_rail.content.reload_rail()
       

        # Called everytime a change in textbox occurs
        def _name_check(e):
            ''' Checks if the name is unique within its type of widget '''

            nonlocal text_field

            # Grab the new name
            new_name = text_field.value.rstrip()

             # Set submitting to false, and unique to True
            self.are_submitting = False
            self.is_unique = True

            for key in self.story.data['folders'].keys():

                # If there is no change, skip the checks
                if new_name.capitalize() == self.title:
                    break

                # Give us our would-be path to compare
                new_key = self.full_path + "\\" + new_name
                new_key = new_key.rstrip()  # Remove trailing spaces for folder names
                
                if os.path.normcase(os.path.normpath(key)) == os.path.normcase(os.path.normpath(new_key)):
                    self.is_unique = False
           

            # Give us our error text if not unique
            if not self.is_unique:
                e.control.error_text = "Category name already exists"
            else:
                e.control.error_text = None

            e.control.update()


        # Called when submitting our textfield.
        def _submit_name(e):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''

            nonlocal text_field

            # Get our name and check if its unique
            new_name = text_field.value
            
            # Set submitting to True
            self.are_submitting = True

            # If it is, call the rename function. It will do everything else
            if self.is_unique:

                new_path = self.full_path[:self.full_path.rfind("\\")+1] + new_name
                
                self.story.rename_folder(
                    old_path=self.full_path,
                    new_path=new_path
                )


                self.story.active_rail.content.reload_rail()
                
                
            # Otherwise make sure we show our error
            else:
                text_field.error_text = "Name already exists"
                text_field.focus()                                  # Auto focus the textfield
                self.p.update()
                
        # Our text field that our functions use for renaming and referencing
        text_field = ft.TextField(
            value=self.title, expand=True, dense=True,
            autofocus=True, 
            capitalization=ft.TextCapitalization.WORDS,
            text_size=14, text_style=self.text_style,
            on_submit=_submit_name,
            on_change=_name_check, 
            on_blur=_cancel_rename,
        )

        # Replaces our name text with a text field for renaming
        self.content.content.title = text_field

        # Clears our popup menu button and applies to the UI
        await self.story.close_menu()

    def get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        async def _change_icon_color(e):
            ''' Passes in our kwargs to the widget, and applies the updates '''
            color = e.control.data

            # Change the data
            self.story.change_folder_data(self.full_path, 'color', color)
            self.color = color
            
            # Change our icon to match, apply the update
            self.story.active_rail.content.reload_rail()
            await asyncio.sleep(.3)
            await self.story.close_menu()      

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.PopupMenuItem(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    data=color, on_click=_change_icon_color
                )
            )

        return color_controls
    
    # Called when the delete button is clicked in the menu options
    def _delete_clicked(self, e):
        ''' Deletes this file from the story '''

        def _delete_confirmed(e=None):
            ''' Deletes the widget after confirmation '''

            self.p.close(dlg)
            self.story.delete_folder(self.full_path)

        # Called to add our folder contents to the confirmation dialog
        def _return_folder_content() -> ft.Control:
            ''' Returns our folder/directories sub-folders and widgets so users are aware of what all they're deleting '''

            column = ft.Column([
                ft.Text("This will also delete the following items:", weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
            ])

            return_folder_content(self.full_path, self.story, column)
            
            # If empty folder, make the dialog smaller by returning None
            return None if column.controls.__len__() == 1 else column
            

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Column([ft.Text(f"Are you sure you want to delete folder {self.title} forever?", weight=ft.FontWeight.BOLD), ft.Divider(height=2, thickness=2)]),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            content=_return_folder_content(),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.close(dlg)),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ]
        )

        self.story.close_menu_instant()

        if app.settings.data.get('confirm_item_delete', False):
            self.p.open(dlg)
        else:
            _delete_confirmed()

    # Called when a widget is dragged and dropped into this directory
    def on_drag_accept(self, e):
        ''' Moves our widgets into this directory from wherever they were '''
        
        # Load our data (draggables can't just pass in simple data for some reason)
        event_data = json.loads(e.data)
        
        # Grab our draggable from the event
        draggable = e.page.get_control(event_data.get("src_id"))
            
        # Grab our key and set the widget
        widget_key = draggable.data

        widget = None

        for w in self.story.widgets:
            if w.data.get('key', "") == widget_key:
                widget = w
                break

        if widget is None:
            print("Error: Widget not found for drag accept")
            return

        # Call the move file using the new directory path
        widget.move_file(new_directory=self.full_path)



    # Called when we need to reload this directory tile
    def reload(self):
        self.expansion_tile = ft.ExpansionTile(
            title=ft.Row([
                ft.Icon(ft.Icons.FOLDER_OUTLINED, color=self.color),
                ft.Text(value=self.title, weight=ft.FontWeight.BOLD, text_align="left")
            ]),
            dense=True,
            visual_density=ft.VisualDensity.COMPACT,
            expanded=self.is_expanded,
            tile_padding=ft.Padding(0, 0, 0, 0),
            controls_padding=ft.Padding(10, 0, 0, 0),       # Keeps all sub children indented
            maintain_state=True,
            expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
            adaptive=True, bgcolor="transparent",
            shape=ft.RoundedRectangleBorder(),
            on_change=self.toggle_expand,
            controls=[self.new_item_textfield], 
        )

        # Re-adds our content controls so we can keep states
        if self.content is not None:        # Protects against first loads
            if self.content.content.controls is not None:
                for control in self.content.content.controls:
                    if control != self.new_item_textfield:      # Don't re-add our textfield, its already there
                        self.expansion_tile.controls.append(control)

        # Wrap in all in a drag target so we can drag to move widgets into different folders
        drag_target = ft.DragTarget(
            group="widgets",
            on_accept=self.on_drag_accept,
            content=self.expansion_tile,
        )
        
        # Set the content
        self.content = drag_target





