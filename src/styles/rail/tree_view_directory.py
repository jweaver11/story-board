import flet as ft
from models.views.story import Story
import os
import json
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
from styles.snack_bar import SnackBar
from utils.check_widget_unique import check_widget_unique
from utils.check_folder_content import return_folder_content
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
        additional_menu_options: list[ft.Control] = None,       # Additional menu options when right clicking a folder, depending on the rail
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

        # Textfield for creating new items (sub-categories, documents, notes, characters, etc.)
        self.new_item_textfield = ft.TextField(  
            hint_text="Sub-folder Name",          
            #data="folder",                                       # Data for logic routing on submit
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
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.color), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True)], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        ft.MenuItemButton(      # Folders
                            leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY), content="Folder", 
                            data="folder", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new folder to organize your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        ), 
                        ft.MenuItemButton(      # Documents
                            leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY), content="Document", 
                            data="document", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new document for text chapters or scenes in your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        ), 
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Canvas",
                            data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True
                        ),
                        ft.MenuItemButton(      
                            leading=ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                            data="note", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        ), 
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), ft.Text("Character", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("character"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10),),
                            tooltip="Create a new character for your story. Choose from templates or create a default character."
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                            data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True,
                            tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), content="Canvas Board",
                            data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                            data="map", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True
                        ),
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), ft.Text("World", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("world"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10)),
                            tooltip="Create a new world for your story. Choose from templates or create a default world."
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, ft.Colors.PRIMARY), content="Object", 
                            data="object", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True,
                            tooltip="New Objects or Items for your story"
                        ),  
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Connection Map", 
                            data="character_connection_map", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True,
                            tooltip="Visualize the connections between the characters in your story"
                        ),
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                    
                ),
                no_padding=True, no_effects=True
            ),

            # Upload options
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, self.color), ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True)], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        ft.MenuItemButton(      # Folders
                        leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY), content="Folder", 
                        data="folder", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new folder to organize your story",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ), 
                    ft.MenuItemButton(      # Documents
                        leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY), content="Document", 
                        data="document", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new document for text chapters or scenes in your story",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ), 
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Canvas",
                        data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True
                    ),
                    ft.MenuItemButton(      
                        leading=ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                        data="note", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ), 
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), content="Character", 
                        data="character", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new character for your story. Choose from templates or create a default character.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                        data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True,
                        tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), content="Canvas Board",
                        data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                        data="map", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True
                    ),
                    
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), content="World", 
                        data="world", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new world for your story. Choose from templates or create a default world.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, ft.Colors.PRIMARY), content="Object", 
                        data="object", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True,
                        tooltip="New Objects or Items for your story"
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Connection Map", 
                        data="character_connection_map", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), disabled=True,
                        tooltip="Visualize the connections between the characters in your story"
                    ),  
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                ),
                no_padding=True, no_effects=True
            ),

        
            # Delete button
            MenuOptionStyle(
                on_click=self.rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.color),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        
                    ), 
                ]),
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.color), 
                        ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self._get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10)),
                    tooltip="Change this folder's color"
                ),
                no_padding=True, no_effects=True
            ),
            MenuOptionStyle(
                on_click=self._delete_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]

        # Return our menu options list
        

    # Called when expanding/collapsing the directory
    async def toggle_expand(self, e=None):
        ''' Makes sure our state and data match the updated expanded/collapsed state '''
    
        self.expansion_tile.expanded = not self.expansion_tile.expanded

        self.story.change_folder_data(
            full_path=self.full_path,
            key='is_expanded', value=self.expansion_tile.expanded
        )

    def get_template_options(self, widget_type: str) -> list[ft.Control]:
        ''' Returns a list of template options when right clicking empty space in the rail '''


        template_options = []

        if widget_type == "character":
            
            for name, template in app.settings.data.get('character_templates', {}).items():
                template_options.append(
                    ft.MenuItemButton(name, data=widget_type, on_click=self.new_item_clicked)
                )

        # Add add button to bottom that opens the settings to the template section
        # Add templates label at the top that is disabled

        elif widget_type == "world":
            for name, template in app.settings.data.get('world_templates', {}).items():
                template_options.append(
                    ft.MenuItemButton(name, data=widget_type, on_click=self.new_item_clicked)
                )

        else:
            template_options = [
                ft.MenuItemButton("Blank", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Research", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Theme", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Idea", data=widget_type, on_click=self.new_item_clicked),
            ]
        return template_options

       
    # Called when creating new folder or when additional menu items are clicked
    async def new_item_clicked(self, e=None):
        ''' Shows the textfield for creating new item. Requires what type of item (folder, chapter, note, etc.) '''

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
            case "character" | "folder":
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Name"
            case _:
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Title"


        # Check our expanded state. Rebuild if needed
        if self.is_expanded == False:
            
            await self.toggle_expand()
            self.expansion_tile.update()
            self.update()
        else:
            self.expansion_tile.update()
            self.update()
            
            
            
        # Close the menu, which will also update the page
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
                e.control.error = None
                self.update()
                return
            
            # Otherwise its not unique, re-focus our textfield
            else:
                e.control.visible = True
                e.control.focus()
        
        # If we're not submitting, just hide the textfield and reset values
        else:
            e.control.visible = False
            e.control.value = None
            e.control.error = None
            self.update()


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

        if tag == "folder":
            new_key = os.path.normcase(os.path.normpath(self.full_path + "\\" + title))
            new_key = new_key.rstrip()  # Remove trailing spaces for folder names
            for key in self.story.data['folders'].keys():
                
                # Path comparisons require normalization
                if os.path.normcase(os.path.normpath(key)) == new_key:
                    self.item_is_unique = False
                    error_text = "folder must be unique."
                    break

        # Not a folder, so we check the widget
        else:
            error_text, self.item_is_unique = check_widget_unique(self.story, new_key)

        # If we are NOT unique, show our error text
        if not self.item_is_unique:
            #print("Setting error text:", error_text)
            e.control.error = error_text

        # Otherwise remove our error text
        else:
            e.control.error = None
            
        e.control.update()

            
    def new_item_textfield_submit(self, e):

        self.are_submitting = True

        title = self.new_item_textfield.value
        tag = self.new_item_textfield.data

        if self.item_is_unique:
            match tag:
                case "folder":
                    self.story.create_folder(directory_path=self.full_path, name=title)
                case _:
                    self.story.create_widget(directory_path=self.full_path, title=title, tag=tag)
                
        else:
            self.new_item_textfield.focus()                                  
            self.update()

    def folder_submit(self, e):
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
            self.update()

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
                self.story.active_rail.update()
       

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
                new_key = os.path.normpath(self.full_path[:self.full_path.rfind("\\")+1] + new_name)
                new_key = new_key.rstrip()  # Remove trailing spaces for folder names
                
                if os.path.normcase(os.path.normpath(key)) == os.path.normcase(os.path.normpath(new_key)):
                    
                    self.is_unique = False

           

            # Give us our error text if not unique
            if not self.is_unique:
                text_field.error = "Folder name already exists"
            else:
                text_field.error = None

            text_field.update()


        # Called when submitting our textfield.
        async def _submit_name(e):
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
                self.story.active_rail.update()
                
                
            # Otherwise make sure we show our error
            else:
                text_field.error = "Folder name already exists"
                await text_field.focus()                                  # Auto focus the textfield
                text_field.update()
                
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
        self.expansion_tile.title = text_field
        self.update()

        # Clears our popup menu button and applies to the UI
        await self.story.close_menu()

    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        def _change_icon_color(color: str):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            # Change the data
            self.story.change_folder_data(self.full_path, 'color', color)
            self.color = color
            
            # Change our icon to match, apply the update
            self.story.active_rail.content.reload_rail()
            self.story.active_rail.update()
            self.story.close_menu_instant() 

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.MenuItemButton(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=lambda e, col=color: _change_icon_color(col), close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                )
            )

        return color_controls
       

        
    
    # Called when the delete button is clicked in the menu options
    def _delete_clicked(self, e):
        ''' Deletes this file from the story '''

        def _delete_confirmed(e=None):
            ''' Deletes the widget after confirmation '''

            self.p.pop_dialog()
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
            title=ft.Text(f"Are you sure you want to delete folder {self.title} forever?", weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            content=_return_folder_content(),
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

    # Called when a widget is dragged and dropped into this directory
    def on_drag_accept(self, e):
        ''' Moves our widgets into this directory from wherever they were '''
        
        draggable = e.page.get_control(e.src_id)
            
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
            title=ft.Text(value=self.title, weight=ft.FontWeight.BOLD, text_align="left"),
            leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, color=self.color),
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





