import flet as ft
from models.views.story import Story
import os
import json
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
from styles.snack_bar import SnackBar
from utils.new_canvas import new_canvas_alert_dlg
from models.app import app
from models.isolated_controls.expansion_tile import IsolatedExpansionTile
import asyncio
import flet_shadcn_ui as shad
from styles.text_fields import TextField
from styles.highlight_button import HighlightButton
from styles.tooltip import Tooltip



# Expansion tile for all sub directories (folders) in a directory
@ft.control
class RailFolder(ft.GestureDetector):


    def __init__(
        self, 
        full_path: str,                                         # Full path to this directory
        title: str,                                             # Title of this folder
        story: Story,                                           # Story reference for mouse positions and other logic
        is_expanded: bool = False,                              # Whether this directory is expanded or not
        color: str = "primary",                                 # Color of the folder icon
        created_at: float = 0,                                  # Creation timestamp of the folder
        notes: str = "",                                           # Notes for the folder
    ):
        
        # Reference for all our passed in data
        self.full_path = full_path
        self.title = title
        self.story = story
        self.color = color
        self.created_at = created_at
        self.is_expanded = is_expanded
        self.notes = notes

        # Set our text style
        self.text_style = ft.TextStyle(
            size=14,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.BOLD,
        )

        # Parent constructor
        super().__init__(
            mouse_cursor=ft.MouseCursor.CLICK,
            exclude_from_semantics=True, expand=True,
        )
        
        
    # Called when clicking off the textfield and after submission
    def on_new_item_blur(self, e=None):
        self.new_item_tf.visible = False
        self.new_item_tf.update()
        

    def new_items(self) -> list[shad.MenuItem]:
        return [
            
            shad.MenuItem(      # Folders
                leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY, size=20), content="Folder", 
                data="folder", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new folder to organize your story",
            ), 
            shad.MenuItem(      # Manuscripts
                leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY, size=20),
                content="Manuscript",
                data="manuscript", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new manuscript for text chapters or scenes in your story",
            ), 
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY, size=20), content="Character",
                data="character", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new character for your story."
            ),
            shad.MenuItem(      
                leading=ft.Icon(ft.Icons.LIBRARY_BOOKS_OUTLINED, ft.Colors.PRIMARY, size=20), content="Note", 
                data="note", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
            ), 
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.VIEW_KANBAN_OUTLINED, ft.Colors.PRIMARY, size=20), content="Kanban",
                data="kanban", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new Kanban board for your story."
            ), 
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY, size=20), content="Plotline",
                data="plotline", on_click=self.new_item_clicked, close_on_click=True, 
                tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Colors.PRIMARY, size=20), content="Plot Chart", 
                data="plot_chart", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="New Items and Equipment for your story", 
            ),  
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.STAR_OUTLINE_ROUNDED, ft.Colors.PRIMARY, size=20), content="Item", 
                data="item", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="New Items and Equipment for your story"
            ),  
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY, size=20), content="World",
                data="world", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new world for your story."
            ),
            shad.MenuItem(
                content="Map",
                leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY, size=20), 
                trailing=ft.Icon(
                    ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, size=14, 
                    tooltip="Drawing capabilities coming soon."),
                data="map", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.CupertinoIcons.COMPASS, ft.Colors.PRIMARY, size=20), content="Radar Chart",
                data="radar_chart", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new world for your story. Choose from templates or create a default world."
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.INSERT_CHART_OUTLINED_OUTLINED, ft.Colors.PRIMARY, size=20), content="Bar Chart",
                data="bar_chart", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new world for your story. Choose from templates or create a default world."
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.LINK_OUTLINED, ft.Colors.PRIMARY, size=20), content="Connection Map", 
                data="connection_map", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Visualize the connections between the characters in your story"
            ),  
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.WEB_OUTLINED, ft.Colors.PRIMARY, size=20), content="Web View", 
                data="web_view", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Embed external web content within your story"
            ),
            shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
            ft.Row(
                [
                    ft.Text(f"Comic", italic=True),
                    ft.Text("(coming soon)", italic=True, color=ft.Colors.OUTLINE)
                ], 
                alignment=ft.MainAxisAlignment.CENTER, margin=ft.Margin.only(bottom=4)
            ),
            shad.MenuItem(
                content="Canvas",
                leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY, size=20),
                data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new Canvas for sketching, drawing, or visual note taking",
                disabled=True
            ),
            shad.MenuItem(
                content="Canvas Board",
                leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY, size=20), 
                data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new Canvas Board to organize your panels and plan your story visually",
                disabled=True
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.SLIDESHOW_OUTLINED, ft.Colors.PRIMARY, size=20), content="Comic Preview", 
                data="comic_preview", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Preview the panels in your story as a comic strip",
                disabled=True
            ),
        ]


    # Called when right clicking over our expansion tile
    def menu_items(self) -> list[ft.Control]:
        ''' Returns our built in menu options all tree view rails have, and any additional ones passed in '''

        def toggle_new_popover(e=None):
            new_popover.open = not new_popover.open
            new_popover.update()

        def toggle_color_popover(e=None):
            color_popover.open = not color_popover.open
            color_popover.update()
            
        # Add our remaining built in options: rename, color change, delete
        return [
            new_popover := shad.Popover(
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, size=20),
                    content=ft.Row([ft.Text("New"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    on_click=toggle_new_popover,
                    close_on_click=False,
                ),
                ft.Column(self.new_items(), tight=True, spacing=0, width=180, height=min(500, ft.context.page.height * 0.5), scroll=ft.ScrollMode.AUTO)
            ),
            shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
            color_popover := shad.Popover(
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.color, size=20),
                    content=ft.Row([ft.Text("Color"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    trailing=ft.Icons.ARROW_RIGHT,
                    on_click=toggle_color_popover,
                    close_on_click=False,
                ),
                ft.Column(self._get_color_options(), tight=True, spacing=0, width=100, height=min(500, ft.context.page.height * 0.5), scroll=ft.ScrollMode.AUTO)
            ), 
            shad.Separator(margin=ft.Margin.symmetric(vertical=4)),

            # Rename the folder
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.color, size=20), 
                content=f"Rename {self.title}", 
                on_click=self.rename_clicked,
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.EDIT_NOTE_OUTLINED, self.color, size=20), 
                content="Open Notes", 
                on_click=self.toggle_notes,
            ),
            shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR, size=20), 
                content="Delete", 
                on_click=self._delete_clicked,
            ),
        ]
        

    # Called when expanding/collapsing the directory
    async def toggle_expand(self, e=None):
        ''' Makes sure our state and data match the updated expanded/collapsed state '''  
    
        await self.story.update_folder_data(
            full_path=self.full_path,
            key='is_expanded', value=self.expansion_tile.expanded
        )
    

    

       
    # Called when creating new folder or when additional menu items are clicked
    async def new_item_clicked(self, e: ft.Event[ft.Control]):
        ''' Shows the textfield for creating new item. Requires what type of item (folder, chapter, note, etc.) '''

        tag = str(e.control.data)
                
        # Make textfield visible, reset its value, and give it right data for logic
        self.new_item_tf.visible = True
        self.new_item_tf.value = None
        self.new_item_tf.data = tag
        self.new_item_tf.error = None
        self.new_item_tf.label = None
        self.new_item_tf.icon = None
        
        if tag == "canvas":
            self.page.show_dialog(new_canvas_alert_dlg(self.page, self.story, self.full_path))
            return

        hint_text = tag.capitalize().replace("_", " ").replace(":", " ") + " Name"

        # Expand and focus the tf (text field) for new item creation
        if self.expansion_tile.expanded == False:
            self.expansion_tile.expanded = True
            self.expansion_tile.update()
            await self.toggle_expand()

        self.new_item_tf.hint_text = hint_text
        self.new_item_tf.visible = True
        self.new_item_tf.update()
        await self.new_item_tf.focus()

    # Called whenever we submit a new item (Chapter, note, category, etc.) via enter key
    async def submit_item(self, e):
        ''' Sets our state to submitting, and creates new item if unique. Father is either Plotline or arc for creating mini widgets '''

        # Grab our title from the textfield
        title = self.new_item_tf.value or ""

        # Protect against empty titles. They break things
        if not title.strip():
            return
        
        tag = self.new_item_tf.data
            
        if tag == "folder":
            await self.story.create_folder(title, self.full_path)
        else:
            await self.story.create_widget(title, tag, self.full_path)

        self.page.pop_dialog()  
        

    # Called when rename button is clicked
    async def rename_clicked(self, e):

        # Track if our name is unique for checks, and if we're submitting or not
        self.is_unique = True
        self.are_submitting = False
       

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
                if new_name == self.title:
                    break

                # Give us our would-be path to compare
                new_key = os.path.normpath(self.full_path[:self.full_path.rfind("\\")+1] + new_name)
                new_key = new_key.rstrip()  # Remove trailing spaces for folder names
                
                if os.path.normcase(os.path.normpath(key)) == os.path.normcase(os.path.normpath(new_key)):
                    
                    self.is_unique = False

            # Give us our error text if not unique
            if not self.is_unique:
                text_field.error_text = "Folder name already exists"
            else:
                text_field.error_text = None

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
                self.story.tree_view_rail.reload_rail()
                self.page.pop_dialog()
                   
                
            # Otherwise make sure we show our error
            else:
                text_field.error = "Folder name already exists"
                await text_field.focus()                                  # Auto focus the textfield
                text_field.update()
                
        # Our text field that our functions use for renaming and referencing
        text_field = shad.Input(
            value=self.title, 
            autofocus=True, 
            on_submit=_submit_name,
            on_change=_name_check, 
        )

        dlg = shad.Dialog(
            title=f"Rename '{self.title}'",
            content=text_field,
            actions=[
                shad.Button("Cancel", on_click=lambda: self.page.pop_dialog(), color=ft.Colors.ERROR, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM),
                shad.Button("Submit", on_click=_submit_name, color=ft.Colors.PRIMARY, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM),
            ],
        )

        self.page.show_dialog(dlg)


    def _get_color_options(self, e=None) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        async def _change_icon_color(e):
            ''' Passes in our kwargs to the widget, and applies the updates '''
            color = e.control.data  

            # Change the data
            await self.story.update_folder_data(self.full_path, 'color', color)
            
            # Change our icon to match, apply the update
            self.story.tree_view_rail.reload_rail()

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                shad.MenuItem(
                    content=ft.Icon(ft.Icons.CIRCLE, color=color, size=20),
                    on_click=_change_icon_color, close_on_click=True, data=color,
                    expand=True
                )
            )

        return color_controls
       
    
    # Called when the delete button is clicked in the menu options
    async def _delete_clicked(self, e):
        ''' Deletes this file from the story '''

        def _delete_confirmed(e=None):
            ''' Deletes the widget after confirmation '''

            self.page.pop_dialog()
            self.story.delete_folder(self.full_path)

        # Append an overlay to confirm the deletion
        dlg = shad.Dialog(
            title=f"Are you sure you want to delete folder '{self.title}' forever?",
            actions=[
                shad.Button("Cancel", on_click=lambda: self.page.pop_dialog(), color=ft.Colors.ERROR, variant=shad.ButtonVariant.OUTLINE, size=shad.ButtonSize.SM),
                shad.Button(f"Delete {self.title}", on_click=_delete_confirmed, variant=shad.ButtonVariant.DESTRUCTIVE, size=shad.ButtonSize.SM),
            ]
        )
        self.page.show_dialog(dlg)
        

    # Called when a widget is dragged and dropped into this directory
    async def on_drag_accept(self, e: ft.DragTargetEvent):
        ''' Moves our widgets or folders into this directory from wherever they were '''
        
        draggable = e.page.get_control(e.src_id)

        # Check if the data is a RailFolder instance
        if isinstance(draggable.data, RailFolder):
            # Handle folder movement
            await self._move_folder(draggable.data, self.full_path)
            return

        # Otherwise treat as a widget (RailFile) - data contains the widget ID
        widget = self.story.get_widget_by_id(draggable.data)

        if widget is None:
            print("Error: Widget not found for drag accept")
            return

        # Call the move file using the new directory path
        await widget.move_file(new_directory=self.full_path)

    async def _move_folder(self, folder: 'RailFolder', new_parent_path: str):
        ''' Moves a folder and all its contents to a new parent directory '''

        new_folder_path = os.path.join(new_parent_path, os.path.basename(folder.full_path))
        try:
            if await self.story.move_folder(folder.full_path, new_folder_path):
                self.story.tree_view_rail.reload_rail()
        except (OSError, ValueError) as ex:
            return
            self.page.show_dialog(shad.Toast(f"Error moving folder: {ex}", variant=shad.ToastVariant.DESTRUCTIVE))

    async def toggle_notes(self, e=None):
        self.notes_popover.open = not self.notes_popover.open
        self.notes_popover.update()
        await self.notes_text.focus()

    # Called when we need to reload this directory tile
    def build(self):
        from utils.load_directory import load_directory_controls

        async def open_expansion_tile(e=None):
            self.expansion_tile.expanded = not self.expansion_tile.expanded
            self.expansion_tile.update()
            await self.toggle_expand()

        
        async def update_notes(e=None):
            self.notes = self.notes_text.value
            await self.story.update_folder_data(
                full_path=self.full_path,
                key='notes', value=self.notes
            )
            self.expansion_tile.title.tooltip = Tooltip(message=self.notes)
            self.expansion_tile.title.update()

        self.new_item_tf = ft.TextField(     
            hint_text="", data="",                 # Hint text and data tag for logic                      
            autofocus=True, dense=True,                 
            capitalization=ft.TextCapitalization.SENTENCES,     # Capitalize sentences for names
            visible=False,                                      # Hidden by default
            text_style=ft.TextStyle(
                size=14,
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),                         # Text style for consistency
            on_blur=self.on_new_item_blur,                      # Called when clicking off the textfield and after submitting
            on_submit=self.submit_item,                         # Called when enter is pressed and textfield is focused
            suffix_icon=ft.IconButton(
                ft.Icons.ADD_OUTLINED, ft.Colors.PRIMARY,
                on_click=self.submit_item,
                mouse_cursor="click",
            ),
        )

        self.notes_text = shad.Textarea(
            value=self.notes, on_blur=update_notes, width=300, autofocus=True,
            label=ft.Row([
                ft.Text(f"{self.title} Notes"), 
                shad.Button(
                    ft.Icon(ft.Icons.CLOSE, ft.Colors.OUTLINE, size=16), 
                    height=24, size=shad.ButtonSize.SM, variant=shad.ButtonVariant.GHOST, 
                    on_click=self.toggle_notes, gap=0
                )
            ], width=300, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            resizable=False,
        )

        self.notes_popover = shad.Popover(
            ft.IconButton(
                ft.Icons.EDIT_NOTE_OUTLINED, self.color, 20, height=24, width=24,
                on_click=self.toggle_notes, padding=0,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), padding=0),
                visible=False
            ),
            self.notes_text,
        )

        sub_folder_controls = load_directory_controls(
            story=self.story,
            directory=self.full_path,
        )

        if not sub_folder_controls:
            sub_folder_controls = [
                ft.Container(
                    ft.Text(f"Add items to {self.title}", color=ft.Colors.OUTLINE, italic=True, size=12), 
                    border=ft.Border.only(left=ft.BorderSide(width=2, color=ft.Colors.OUTLINE_VARIANT)),
                    padding=ft.Padding.only(left=6), height=29, alignment=ft.Alignment.CENTER_LEFT,
                    on_click=self.new_item_clicked, visible=False
                )
            ]

        # The expansiontile that will hold everything
        self.expansion_tile = IsolatedExpansionTile(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.FOLDER_OUTLINED, self.color),  # icon
                    ft.Text(value=self.title, weight=ft.FontWeight.BOLD, text_align="left", expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                    self.notes_popover, # Shows the popover for the textarea for the notes
                    shad.ContextMenu(   # CM for opening menu when right clicking title of expansion tile
                        HighlightButton(ft.Icon(ft.Icons.MORE_HORIZ, ft.Colors.ON_SURFACE_VARIANT)),
                        items=self.menu_items(),
                        open_on_tap=True,
                    ),
                    
                ], 
                expand=True, spacing=6, 
                tooltip=Tooltip(message=self.notes)
            ),
            dense=True, min_tile_height=0,
            collapsed_shape=ft.RoundedRectangleBorder(radius=4),
            visual_density=ft.VisualDensity.COMPACT,
            expanded=self.is_expanded,
            tile_padding=ft.Padding(6, 2, 6, 2),
            icon_color=self.color, adaptive=True,
            controls_padding=ft.Padding(20, 0, 0, 0),       # Keeps all sub children indented slightly
            expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
            shape=ft.RoundedRectangleBorder(radius=4),
            on_change=self.toggle_expand,
            controls=[self.new_item_tf] + sub_folder_controls,
            animation_style=ft.AnimationStyle(
                ft.Duration(milliseconds=100), ft.Duration(milliseconds=100), 
                ft.AnimationCurve.DECELERATE, ft.AnimationCurve.DECELERATE
            ),
        )    

        # Wrap in all in a drag target so we can drag to move widgets into different folders
        drag_target = ft.DragTarget(
            group="widgets",
            on_accept=self.on_drag_accept,
            content=ft.Container(
                content=self.expansion_tile,
                theme=ft.Theme(
                    hover_color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                    list_tile_theme=ft.ListTileTheme(min_vertical_padding=0),   # Clamp the padding on the tile down
                ),
                dark_theme=ft.Theme(
                    hover_color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                    list_tile_theme=ft.ListTileTheme(min_vertical_padding=0),   # Clamp the padding on the tile down
                ),
            ),
                
        )

        draggable = ft.Draggable(
            group="widgets",
            content=drag_target,
            data=self,  # Store reference to this RailFolder for identification
            content_feedback=ft.TextButton(
                ft.Row([
                    ft.Icon(ft.Icons.FOLDER_OUTLINED, self.color, expand=True), 
                    ft.Text(self.title, style=self.text_style, expand=True)
                ], expand=True)
            ),
        )

        
        
        # Set the content
        self.content = draggable
