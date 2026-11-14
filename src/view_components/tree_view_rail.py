'''
UI model for our active rail, which is stored at app.active_story.active_rail
Keeps consistent styling and width between different workspace rails, 
And gives us the correct rail on startup based on selected workspace
'''

import flet as ft
from models.app import app
from models.views.story import Story
from utils.load_directory import load_directory_controls
from styles.menu_option_style import MenuOptionStyle
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.list_view import IsolatedListView
from utils.new_canvas import new_canvas_alert_dlg
from styles.snack_bar import SnackBar
import os
import flet_shadcn_ui as shad


# Class is created in main on program startup
class ActiveRail(ft.Container):
    
    # Constructor
    def __init__(self, story: Story):
    
        self.story = story  # Store the story reference
  
        # Consistent styling for all our rails
        super().__init__(
            alignment=ft.Alignment.TOP_CENTER,
            padding=ft.Padding.only(top=10, bottom=10),
            width=app.settings.data.get('story', {}).get('active_rail_width', 250),
            animate_size=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            bgcolor=ft.Colors.SURFACE,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            visible=not ft.context.page.platform.is_mobile()
        )
        
    # Reload our rail on startup
    def build(self):
        self.reload_rail(update=False)
        
    # Called when a new workspace is selected
    def reload_rail(self, update: bool=True):
        ''' Reloads the active rail based on the selected workspace in workspaces_rail '''

        self.content = ContentRail(self.story)
        if update:
            self.update()
        return





# Class is created in main on program startup
@ft.control
class ContentRail(ft.Column):

    # Constructor
    def __init__(self, story: Story):
        
        # Initialize the parent Rail class first
        super().__init__(spacing=0)
        
        self.story = story

        # Textfield for creating new items (sub-categories, chapters, notes, characters, etc.)
        self.new_item_textfield = ft.TextField(     
            hint_text="", data="",                 # Hint text and data tag for logic                      
            autofocus=True, dense=True,                 
            capitalization=ft.TextCapitalization.WORDS,     # Capitalize sentences for names
            visible=False,                                      # Hidden by default
            text_style=ft.TextStyle(
                size=14,
                color=ft.Colors.ON_SURFACE,
                weight=ft.FontWeight.BOLD,
            ),                         # Text style for consistency
            on_blur=self.on_new_item_blur,                      # Called when clicking off the textfield and after submitting
            on_submit=self.submit_item,                         # Called when enter is pressed and textfield is focused
            icon=None,
            suffix_icon=ft.IconButton(
                ft.Icons.ADD_OUTLINED, ft.Colors.PRIMARY,
                on_click=self.submit_item,
                mouse_cursor="click",
            ),
        )
        

    # Returns a list of template options
    def get_template_options(self, widget_type: str) -> list[ft.Control]:
        ''' Returns a list of template options when right clicking empty space in the rail '''

        template_options = []

        if widget_type == "chart":
            template_options = [
                ft.MenuItemButton(
                    "Bar", data=f"{widget_type}:bar", 
                    on_click=self.new_item_clicked, leading=ft.Icon(ft.Icons.INSERT_CHART_OUTLINED_OUTLINED, ft.Colors.PRIMARY),
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4))
                ),
                ft.MenuItemButton(
                    "Radar", data=f"{widget_type}:radar", 
                    on_click=self.new_item_clicked, leading=ft.Icon(ft.CupertinoIcons.COMPASS, ft.Colors.PRIMARY),
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4))
                ),
            ]

        return template_options
    
    # Called when a widget is dragged and dropped into this directory
    def move_widget_file(self, e: ft.DragTargetEvent, new_directory: str):
        ''' Moves our widgets or folders into this directory from wherever they were '''

        draggable = e.page.get_control(e.src_id)
        self.stop_highlight_rail()

        # Import RailFolder here to avoid circular imports
        from styles.rail_folder import RailFolder

        # Check if the data is a RailFolder instance
        if isinstance(draggable.data, RailFolder):
            # Handle folder movement
            self.page.run_task(self._move_folder_to_directory, draggable.data, new_directory)
            return

        # Otherwise treat as a widget (RailFile) - data contains the widget ID
        widget = self.story.get_widget_by_id(draggable.data)

        if widget is None:
            print("Error, file not found.")
            return

        self.page.run_task(widget.move_file, new_directory)

    # Helper method to move a folder to a new directory
    async def _move_folder_to_directory(self, folder, new_directory: str):
        ''' Moves a folder and all its contents to a new directory '''
        
        # Prevent moving a folder into itself or its children
        if new_directory.startswith(folder.full_path):
            self.page.show_dialog(shad.Toast("Cannot move a folder into itself or its subfolders", variant=shad.ToastVariant.DESTRUCTIVE))
            return
        
        # Prevent moving a folder to its current location
        if new_directory == os.path.dirname(folder.full_path):
            return
        
        # Get the folder name
        folder_name = os.path.basename(folder.full_path)
        new_folder_path = os.path.join(new_directory, folder_name)
        
        try:
            # Move the folder using shutil
            import shutil
            shutil.move(folder.full_path, new_folder_path)
            
            # Update folder metadata in story data to maintain state
            await self.story.move_folder(folder.full_path, new_folder_path)
            
            # Reload the rail to reflect the changes
            self.story.tree_view_rail.reload_rail()
            
        except Exception as ex:
            print(f"Error moving folder: {str(ex)}")


    # Called when new category button or menu option is clicked
    async def new_item_clicked(self, e: ft.Event):
        ''' Handles setting our textfield for new category creation '''

            
        tag = e.control.data
        
        
        # Make textfield visible, reset its value, and give it right data for logic
        self.new_item_textfield.visible = True
        self.new_item_textfield.value = None
        self.new_item_textfield.data = tag
        self.new_item_textfield.error = None
        self.new_item_textfield.label = None
        self.new_item_textfield.icon = None


        match tag:
            case "character_relationship_map":
                self.new_item_textfield.hint_text = "Character Relationship Map Title"
            
            case "plot_point": 
                self.new_item_textfield.hint_text = "Plot Point Title"
            case "character" | "folder" | "item" | "object":
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Name"
                if tag == "character":
                    template_name = str(e.control.content)
                    self.new_item_textfield.label = template_name

            case "canvas":
                await self.story.close_menu()
                self.page.show_dialog(new_canvas_alert_dlg(self.page, self.story))
                return
                        
            case "canvas_board":
                self.new_item_textfield.hint_text = "Canvas Board Title"
            case "world":
                self.new_item_textfield.hint_text = "World Title"
                template_name = str(e.control.content)
                self.new_item_textfield.label = f"{template_name}"
            case "comic_preview":
                self.new_item_textfield.hint_text = "Comic Preview Title"
            case "plot_chart":
                self.new_item_textfield.hint_text = "Plot Chart Title"
            case _:
                if ":" in tag:
                    self.new_item_textfield.hint_text = f"{tag.split(':')[0].capitalize()} Title"
                else:
                    self.new_item_textfield.hint_text = f"{tag.capitalize()} Title"

        # Open the textfield early since we have to wait for async close menu
        self.new_item_textfield.update()
        await self.new_item_textfield.focus()
        
        await self.story.close_menu()


    # Called when clicking off the textfield and after submission
    def on_new_item_blur(self, e):
        self.new_item_textfield.visible = False
        self.new_item_textfield.update()


    # Called whenever we submit a new item (Chapter, note, category, etc.) via enter key
    async def submit_item(self, e):
        ''' Sets our state to submitting, and creates new item if unique. Father is either Plotline or arc for creating mini widgets '''

        # Grab our title from the textfield
        title = self.new_item_textfield.value

        # Protect against empty titles. They break things
        if title is None or title.strip() == "":
            return
        
        tag = self.new_item_textfield.data
        if ":" in tag:
            tag, chart_type = tag.split(":")
            
        
        if tag == "folder":
            await self.story.create_folder(name=title)
        else:
            await self.story.create_widget(title, tag, chart_type=chart_type if tag == "chart" else None)

        self.page.pop_dialog()  

            
    # Called when new character button or menu option is clicked
    def new_canvas_clicked(self, e: ft.Event=None):
        ''' Handles setting our textfield for new character creation '''

        # Close the menu (if ones is open), which will update the page as well
        self.story.close_menu_instant()   
        self.page.show_dialog(new_canvas_alert_dlg(self.page, self.story))

    # Called every time the mouse moves over our rail
    async def _set_menu_coords(self, e: ft.PointerEvent):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.story.mouse_x = e.global_position.x 
        self.story.mouse_y = e.global_position.y
        

    def highlight_rail(self, _=None):
        ''' Changes our rails background to a transparent color on hover '''
        self.highlight_container.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE_VARIANT)
        self.highlight_container.update()

    def stop_highlight_rail(self, _=None):  
        ''' Changes our rails background back to normal when not hovering '''
        self.highlight_container.bgcolor = ft.Colors.with_opacity(0.0, ft.Colors.ON_SURFACE)
        self.highlight_container.update()


    async def change_sort_method(self, e: ft.Event[ft.MenuItemButton]):
        sort_method = e.control.data
        app.settings.update_data(**{'story': {'rail_sort_method': sort_method}})
        self.story.tree_view_rail.reload_rail()

    def new_item_options(self) -> list[ft.Control]:
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
                content=ft.Row([
                    ft.Text("Map"), 
                    ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.ERROR, scale=0.8, 
                            tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY, size=20), 
                data="map", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
            ),
            
            shad.MenuItem(
                leading=ft.Icon(ft.CupertinoIcons.COMPASS, ft.Colors.PRIMARY, size=20), content="Radar Chart",
                data="chart:radar", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new world for your story. Choose from templates or create a default world."
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.INSERT_CHART_OUTLINED_OUTLINED, ft.Colors.PRIMARY, size=20), content="Bar Chart",
                data="chart:bar", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new world for your story. Choose from templates or create a default world."
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY, size=20), content="Character Relationship Map", 
                data="character_relationship_map", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Visualize the connections between the characters in your story"
            ),  
            shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
            ft.Row([ft.Text(f"Comic", italic=True)], alignment=ft.MainAxisAlignment.CENTER, margin=ft.Margin.only(bottom=4)),
            shad.MenuItem(
                content=ft.Row([
                    ft.Text("Canvas"), 
                    ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.ERROR, scale=0.8, 
                            tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY, size=20),
                data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new Canvas for sketching, drawing, or visual note taking",
            ),
            shad.MenuItem(
                content=ft.Row([
                    ft.Text("Canvas Board"), 
                    ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.ERROR, scale=0.8, 
                            tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY, size=20), 
                data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Create a new Canvas Board to organize your panels and plan your story visually",
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.SLIDESHOW_OUTLINED, ft.Colors.PRIMARY, size=20), content="Comic Preview", 
                data="comic_preview", on_click=self.new_item_clicked, close_on_click=True,
                tooltip="Preview the panels in your story as a comic strip",
            ),
        ]


    def sort_options(self) -> list[ft.Control]:
        return [
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.SORT_OUTLINED, ft.Colors.PRIMARY, size=20), content="Default", 
                on_click=self.change_sort_method, close_on_click=True, data="default", 
                tooltip="Let your Operating System decide the order.", 
            ),  
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.SORT_BY_ALPHA_OUTLINED, ft.Colors.PRIMARY, size=20), content="Alphabetical", 
                on_click=self.change_sort_method, close_on_click=True, data="alphabetical", 
            ),  
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.SORT_BY_ALPHA_OUTLINED, ft.Colors.PRIMARY, size=20), content="Alphabetical Reversed", 
                on_click=self.change_sort_method, close_on_click=True, data="alphabetical_reversed", 
            ),  
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY, size=20), content="Color", 
                on_click=self.change_sort_method, close_on_click=True, data="color",
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY, size=20), content="Color Reversed", 
                on_click=self.change_sort_method, close_on_click=True, data="color_reversed",
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.UPDATE_OUTLINED, ft.Colors.PRIMARY, size=20), content="Creation Date", 
                on_click=self.change_sort_method, close_on_click=True, data="creation_date",
            ),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.UPDATE_OUTLINED, ft.Colors.PRIMARY, size=20), content="Creation Date Reversed", 
                on_click=self.change_sort_method, close_on_click=True, data="creation_date_reversed",
            ),
        ]
    
    # Reload the rail whenever we need
    def build(self) -> ft.Control:
        ''' Reloads the content rail '''

        def highlight(e):
            e.control.content.bgcolor = ft.Colors.with_opacity(0.25, ft.Colors.BLUE_400)
            e.control.update()

        def unhighlight(e):
            e.control.content.bgcolor = None
            e.control.update()

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER, spacing=20,
            controls=[
                shad.ContextMenu(
                    ft.GestureDetector(
                        ft.Container(ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), border_radius=6, padding=6),
                        on_enter=highlight, on_exit=unhighlight, mouse_cursor=ft.MouseCursor.CLICK
                    ),
                    open_on_tap=True,
                    items=self.new_item_options(),
                ),
                shad.ContextMenu(
                    ft.GestureDetector(
                        ft.Container(ft.Icon(ft.Icons.SORT_OUTLINED, ft.Colors.PRIMARY), border_radius=6, padding=6),
                        on_enter=highlight, on_exit=unhighlight, mouse_cursor=ft.MouseCursor.CLICK
                    ),
                    open_on_tap=True,
                    items=self.sort_options(),
                ),
            ]
        )
                 

        # Build the content of our rail
        content = IsolatedListView(
            scroll=ft.ScrollMode.AUTO,
            spacing=0, 
            expand=True,
            controls=[
                ft.Container(self.new_item_textfield, margin=ft.Margin.only(left=10, right=10, top=6))
            ],
        )
        
        # Load our content directory data into the rail
        content.controls.extend(
            load_directory_controls(
                story=self.story,
                directory=self.story.data.get('content_directory_path'),
                in_base_directory=True,
            )
        )

        
        # Add container to the bottom to make sure the drag target and gesture detector fill the rest of the space
        content.controls.append(
            ft.Container(
                shad.ContextMenu(
                    ft.Container(expand=True, height=1000), # Force CM to work until bottom of page
                    expand=True,
                    items=self.new_item_options()
                )
            )
        )


        # Wrap the gd in a drag target so we can move characters here
        dt = ft.DragTarget(
            group="widgets", on_will_accept=self.highlight_rail, on_leave=self.stop_highlight_rail,
            content=content,     # Our content is the content we built above
            on_accept=lambda e: self.move_widget_file(e, self.story.data.get('content_directory_path')),
            expand=True
        )

        self.highlight_container = ft.Container(dt, border_radius=6, expand=True)
   
        self.controls = [
            header,
            ft.Divider(thickness=2, leading_indent=8),
            self.highlight_container,
        ]
        