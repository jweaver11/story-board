'''
UI model for our active rail, which is stored at app.active_story.active_rail
Keeps consistent styling and width between different workspace rails, 
And gives us the correct rail on startup based on selected workspace
'''

import flet as ft
from models.app import app
from models.views.story import Story
from utils.tree_view import load_directory_data
from styles.menu_option_style import MenuOptionStyle
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.list_view import IsolatedListView
from utils.new_canvas import new_canvas_alert_dlg
from styles.snack_bar import SnackBar



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
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
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
        )
        

        # State variables used for our UI to track logic
        self.item_is_unique = True          # If the new folder, chapter, note, etc. title is unique within its directory
        self.are_submitting = False         # If we are currently submitting this item

    # Returns a list of template options
    def get_template_options(self, widget_type: str) -> list[ft.Control]:
        ''' Returns a list of template options when right clicking empty space in the rail '''

        template_label = ft.Text("Templates", italic=True, color=ft.Colors.ON_SURFACE_VARIANT)

        template_options = []

        if widget_type == "character":
            
            for name, template in app.settings.data.get('character_templates', {}).items():
                template_options.append(
                    ft.MenuItemButton(
                        name, data=widget_type, on_click=self.new_item_clicked, 
                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4))
                    )
                )
            #template_options.insert(0, template_label)
            #template_options.insert(1, ft.Divider(2, 2))

        # Add add button to bottom that opens the settings to the template section
        # Add templates label at the top that is disabled

        elif widget_type == "world":
            for name, template in app.settings.data.get('world_templates', {}).items():
                template_options.append(
                    ft.MenuItemButton(
                        name, data=widget_type, on_click=self.new_item_clicked, 
                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4))
                    )
                )
            #template_options.insert(0, template_label)

        elif widget_type == "chart":
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
        ''' Moves our widgets into this directory from wherever they were '''

        draggable = e.page.get_control(e.src_id)

        widget = self.story.get_widget_by_id(draggable.data)

        if widget is None:
            self.page.show_dialog(SnackBar("Error, file not found."))
            return

        self.page.run_task(widget.move_file, new_directory)


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

        # Change our submitting state
        self.are_submitting = True

        # Grab our title from the textfield
        title = e.control.value

        # Protect against empty titles. They break things
        if title is None or title.strip() == "":
            return
        
        tag = e.control.data
        if ":" in tag:
            tag, chart_type = tag.split(":")
            
        # If our new title unique (check from on_new_item_change), create the new item
        if self.item_is_unique:

            
            match tag:
                # New categories
                case "folder":
                    # Create our new category
                    await self.story.create_folder(name=title)

                # All other cases are widgets
                case _:
                    # Create the widget and reload all our rails
                    await self.story.create_widget(title, tag, chart_type=chart_type if tag == "chart" else None)

            self.page.pop_dialog()   # Close the textfield dialog

            
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
        

    async def _highlight_rail(self, e):
        ''' Changes our rails background to a transparent color on hover '''
        e.control.content.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE_VARIANT)
        e.control.content.update()

    async def _stop_highlight_rail(self, e):  
        ''' Changes our rails background back to normal when not hovering '''
        e.control.content.bgcolor = ft.Colors.with_opacity(0.0, ft.Colors.ON_SURFACE)
        e.control.content.update()


    # Called to return our list of menu options for the content rail
    def get_new_item_menu_options(self) -> list[ft.Control]:

        # TODO: Add warning icon and tooltip next to doc and canvas (not working)

        return [
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(4), shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                    [
                        ft.MenuItemButton(      # Folders
                            leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY), content="Folder", 
                            data="folder", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new folder to organize your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(      # Manuscripts
                            content=ft.Row([
                                ft.Text("Manuscript"), 
                                ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, visible=False,
                                        tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                            leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY), 
                            data="manuscript", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new manuscript for text chapters or scenes in your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            trailing=ft.Icon(ft.Icons.WARNING_OUTLINED, ft.Colors.ERROR, tooltip="This feature is still in development and may not work as expected. Proceed with caution."),
                        ), 
                        ft.MenuItemButton(
                            content=ft.Row([
                                ft.Text("Canvas"), 
                                ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                        tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                            leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY),
                            data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                            trailing=ft.Icon(ft.Icons.WARNING_OUTLINED, ft.Colors.ERROR, tooltip="This feature is still in development and may not work as expected. Proceed with caution."),
                        ),
                        
                        ft.MenuItemButton(      
                            leading=ft.Icon(ft.Icons.LIBRARY_BOOKS_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                            data="note", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                            data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                        ),
                        ft.MenuItemButton(
                            content=ft.Row([
                                ft.Text("Canvas Board"), 
                                ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                        tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                            leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), 
                            data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            content=ft.Row([
                                ft.Text("Map"), 
                                ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                        tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                            leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), 
                            data="map", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        ),
                        
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.STAR_OUTLINE_ROUNDED, ft.Colors.PRIMARY), content="Item", 
                            data="item", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                            tooltip="New Items and Equipment for your story"
                        ),  
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Colors.PRIMARY), content="Plot Chart", 
                            data="plot_chart", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                            tooltip="New Items and Equipment for your story", 
                        ), 
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.SLIDESHOW_OUTLINED, ft.Colors.PRIMARY), content="Comic Preview", 
                            data="comic_preview", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                            tooltip="Preview the canvases in your story as a comic strip",
                        ), 
                        
                        
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Relationship Map", 
                            data="character_relationship_map", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="Visualize the connections between the characters in your story"
                        ),
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), ft.Text("Character", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("character"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="Create a new character for your story. Choose from templates or create a default character."
                        ),
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), ft.Text("World", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("world"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="Create a new world for your story. Choose from templates or create a default world."
                        ),
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, ft.Colors.PRIMARY), ft.Text("Chart", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("chart"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="New Charts for your story"
                        ), 
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True
            ),

            # Upload options
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.IMPORT_EXPORT_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("Import", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                    [
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY), content="Folder", 
                            on_click=self.story.import_folder_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                            tooltip="Import a Folder into the Story's root directory",
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY), content="Widget(s)", 
                            on_click=self.story.import_files_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                            tooltip="Import Widget files into the Story's root directory",
                        ),
                        
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True, 
            )
        ]

    async def change_sort_method(self, e: ft.Event[ft.MenuItemButton]):
        sort_method = e.control.data
        app.settings.update_data(**{'story': {'rail_sort_method': sort_method}})
        self.parent.reload_rail()

    # Reload the rail whenever we need
    def build(self) -> ft.Control:
        ''' Reloads the content rail '''

        top_row_buttons = [
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, "primary"),
                    padding=ft.Padding.all(8), shape=ft.BoxShape.CIRCLE,
                    width=40, height=40, alignment=ft.Alignment.CENTER
                ),
                [
                    ft.MenuItemButton(      # Folders
                        leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY), content="Folder", 
                        data="folder", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new folder to organize your story",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ), 
                    ft.MenuItemButton(      # Manuscripts
                        content=ft.Row([
                            ft.Text("Manuscript"), 
                            ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, visible=False, 
                                    tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                        leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY),
                        data="manuscript", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new manuscript for text chapters or scenes in your story",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ), 
                    ft.MenuItemButton(
                        content=ft.Row([
                            ft.Text("Canvas"), 
                            ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                    tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                        leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY),
                        data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),
                    
                    ft.MenuItemButton(      
                        leading=ft.Icon(ft.Icons.LIBRARY_BOOKS_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                        data="note", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ), 
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                        data="plotline", on_click=self.new_item_clicked, close_on_click=True, 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                        tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                    ),
                    ft.MenuItemButton(
                        content=ft.Row([
                            ft.Text("Canvas Board"), 
                            ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                    tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                        leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), 
                        data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),
                    ft.MenuItemButton(
                        content=ft.Row([
                            ft.Text("Map"), 
                            ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                    tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                        leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), 
                        data="map", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),
                    
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.STAR_OUTLINE_ROUNDED, ft.Colors.PRIMARY), content="Item", 
                        data="item", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="New Items and Equipment for your story"
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Colors.PRIMARY), content="Plot Chart", 
                        data="plot_chart", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="New Items and Equipment for your story", 
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SLIDESHOW_OUTLINED, ft.Colors.PRIMARY), content="Comic Preview", 
                        data="comic_preview", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                        tooltip="Preview the canvases in your story as a comic strip",
                    ),
                    
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Relationship Map", 
                        data="character_relationship_map", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="Visualize the connections between the characters in your story"
                    ),  
                    ft.SubmenuButton(
                        ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), ft.Text("Character", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                        self.get_template_options("character"), 
                        expand=True,
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="Create a new character for your story. Choose from templates or create a default character."
                    ),
                    ft.SubmenuButton(
                        ft.Row([ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), ft.Text("World", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                        self.get_template_options("world"), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="Create a new world for your story. Choose from templates or create a default world."
                    ),
                    ft.SubmenuButton(
                        ft.Row([ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, ft.Colors.PRIMARY), ft.Text("Chart", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                        self.get_template_options("chart"), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="New Charts for your story"
                    ), 
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.IMPORT_EXPORT_OUTLINED, ft.Colors.PRIMARY),
                    padding=ft.Padding.all(8), shape=ft.BoxShape.CIRCLE,
                    width=40, height=40, alignment=ft.Alignment.CENTER
                ),
                [
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.DRIVE_FOLDER_UPLOAD_OUTLINED, ft.Colors.PRIMARY), content="Import Folder", 
                        on_click=self.story.import_folder_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="Import all files within a folder to create new widgets.", 
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY), content="Import Widget(s)", 
                        on_click=self.story.import_files_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="Import file(s) to create new widgets.", 
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.DOWNLOAD_OUTLINED, ft.Colors.PRIMARY), content="Export Widget(s)", 
                        on_click=self.story.handle_export, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                        tooltip="Export parts of your story.",
                    ),
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                tooltip="Import or Export",
            ),
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.SORT_OUTLINED, ft.Colors.PRIMARY),
                    padding=ft.Padding.all(8), shape=ft.BoxShape.CIRCLE,
                    width=40, height=40, alignment=ft.Alignment.CENTER,
                ),
                [
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SORT_OUTLINED, ft.Colors.PRIMARY), content="Default", 
                        on_click=self.change_sort_method, close_on_click=True, data="default", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="Let your Operating System decide the order. Windows is alphabetical, Mac is by creation date", 
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SORT_BY_ALPHA_OUTLINED, ft.Colors.PRIMARY), content="Alphabetical", 
                        on_click=self.change_sort_method, close_on_click=True, data="alphabetical", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SORT_BY_ALPHA_OUTLINED, ft.Colors.PRIMARY), content="Alphabetical Reversed", 
                        on_click=self.change_sort_method, close_on_click=True, data="alphabetical_reversed", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY), content="Color", 
                        on_click=self.change_sort_method, close_on_click=True, data="color",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY), content="Color Reversed", 
                        on_click=self.change_sort_method, close_on_click=True, data="color_reversed",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.UPDATE_OUTLINED, ft.Colors.PRIMARY), content="Creation Date", 
                        on_click=self.change_sort_method, close_on_click=True, data="creation_date",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.UPDATE_OUTLINED, ft.Colors.PRIMARY), content="Creation Date Reversed", 
                        on_click=self.change_sort_method, close_on_click=True, data="creation_date_reversed",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                    ),
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                tooltip="Change how you sort your story's content.",
            ),
        ]

        menubar = ft.MenuBar(
            top_row_buttons,
            #expand=True,
            style=ft.MenuStyle(
                bgcolor="transparent", shadow_color="transparent",
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.Padding.all(0)
            ),
        )

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[menubar]
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
        load_directory_data(
            story=self.story,
            directory=self.story.data.get('content_directory_path'),
            rail=self,
            column=content,
        )

        
        # Add container to the bottom to make sure the drag target and gesture detector fill the rest of the space
        content.controls.append(ft.Container(expand=True))


        # Wrap the gd in a drag target so we can move characters here
        dt = ft.DragTarget(
            group="widgets", on_will_accept=self._highlight_rail, on_leave=self._stop_highlight_rail,
            content=content,     # Our content is the content we built above
            on_accept=lambda e: self.move_widget_file(e, self.story.data.get('content_directory_path'))
        )
        

        # Gesture detector to put on top of stack on the rail to pop open menus on right click
        menu_gesture_detector = ft.GestureDetector(
            content=dt,
            expand=True,
            on_hover=self._set_menu_coords,
            on_secondary_tap=lambda: self.story.open_menu(self.get_new_item_menu_options()),  
            hover_interval=20,
        )

        self.controls = [
            header,
            ft.Divider(thickness=2, leading_indent=8),
            menu_gesture_detector
        ]
        
        
        
        


        