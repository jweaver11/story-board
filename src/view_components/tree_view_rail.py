""" WIP """

import flet as ft
import os
from models.views.story import Story
from view_components.rail import Rail
from utils.tree_view import load_directory_data
from styles.menu_option_style import MenuOptionStyle
import math
from contexts.app_settings import AppSettingsContext
#from contexts.contexts import AppSettingsContext



# Class is created in main on program startup
class ContentRail(Rail):

    # Constructor
    def __init__(self, story: Story):
        
        # Initialize the parent Rail class first
        super().__init__(story=story)

        

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

# Reload the rail whenever we need
@ft.component
def TreeViewRail(story) -> ft.Control:
    ''' Reloads the content rail. `settings` is passed explicitly (not just read off `app`) so this
    component subscribes to the Settings observable itself and re-renders when binder_rail_width changes '''

    

    app_settings = ft.use_context(AppSettingsContext)

    # Called when new category button or menu option is clicked
    async def new_item_clicked(e: ft.Event[ft.Control]):
        ''' Handles setting our textfield for new category creation '''
        print("New item clicked")

        set_creating_item(True)
        set_new_item_hint("")
        set_new_item_data(e.control.data)   # Sets the tag

            
        tag = e.control.data
        
        
        # Make textfield visible, reset its value, and give it right data for logic
        #self.new_item_textfield.visible = True
        #self.new_item_textfield.value = None
        #self.new_item_textfield.data = tag
       # self.new_item_textfield.label = None

        # See how to set our hint depending on situation
        match tag:
            case "character_relationship_map":
                set_new_item_hint("Character Relationship Map Title")
        
            case "character" | "folder" | "item" | "object":
                set_new_item_hint(f"{tag.capitalize()} Name")
                if tag == "character":
                    template_name = str(e.control.content)
                    set_new_item_label(template_name)

            case "canvas":
                #await self.story.close_menu()
                #self.page.show_dialog(new_canvas_dlg(self.page, self.story))
                return
                        
            case "canvas_board":
                set_new_item_hint("Canvas Board Title")
            case "world":
                set_new_item_hint("World Title")
                template_name = str(e.control.content)
                set_new_item_label(f"{template_name}")
            case "comic_preview":
                set_new_item_hint("Comic Preview Title")
            case "plot_chart":
                set_new_item_hint("Plot Chart Title")
            # Charts
            case _:
                if ":" in tag:
                    set_new_item_hint(f"{tag.split(':')[0].capitalize()} Title")
                else:
                    set_new_item_hint(f"{tag.capitalize()} Title")
        
        #await self.story.close_menu()

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
                    data="folder", on_click=new_item_clicked, close_on_click=True,
                    tooltip="Create a new folder to organize your story",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ), 
                ft.MenuItemButton(      # Manuscripts
                    content=ft.Row([
                        ft.Text("Manuscript"), 
                        ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, visible=False, 
                                tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                    leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY),
                    data="manuscript", on_click=new_item_clicked, close_on_click=True,
                    tooltip="Create a new manuscript for text chapters or scenes in your story",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ), 
                ft.MenuItemButton(
                    content=ft.Row([
                        ft.Text("Canvas"), 
                        ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                    leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY),
                    data="canvas", on_click=new_item_clicked, close_on_click=True,
                    tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                
                ft.MenuItemButton(      
                    leading=ft.Icon(ft.Icons.LIBRARY_BOOKS_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                    data="note", on_click=new_item_clicked, close_on_click=True,
                    tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ), 
                ft.MenuItemButton(
                    leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                    data="plotline", on_click=new_item_clicked, close_on_click=True, 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                    tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                ),
                ft.MenuItemButton(
                    content=ft.Row([
                        ft.Text("Canvas Board"), 
                        ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                    leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), 
                    data="canvas_board", on_click=new_item_clicked, close_on_click=True,
                    tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                ft.MenuItemButton(
                    content=ft.Row([
                        ft.Text("Map"), 
                        ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                    leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), 
                    data="map", on_click=new_item_clicked, close_on_click=True,
                    tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                
                ft.MenuItemButton(
                    leading=ft.Icon(ft.Icons.STAR_OUTLINE_ROUNDED, ft.Colors.PRIMARY), content="Item", 
                    data="item", on_click=new_item_clicked, close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="New Items and Equipment for your story"
                ),  
                ft.MenuItemButton(
                    leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Colors.PRIMARY), content="Plot Chart", 
                    data="plot_chart", on_click=new_item_clicked, close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="New Items and Equipment for your story", 
                ),  
                ft.MenuItemButton(
                    leading=ft.Icon(ft.Icons.SLIDESHOW_OUTLINED, ft.Colors.PRIMARY), content="Comic Preview", 
                    data="comic_preview", on_click=new_item_clicked, close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                    tooltip="Preview the canvases in your story as a comic strip",
                ),
                
                ft.MenuItemButton(
                    leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Relationship Map", 
                    data="character_relationship_map", on_click=new_item_clicked, close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Visualize the connections between the characters in your story"
                ),  
                ft.SubmenuButton(
                    ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), ft.Text("Character", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                    #self.get_template_options("character"), 
                    expand=True,
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Create a new character for your story. Choose from templates or create a default character."
                ),
                ft.SubmenuButton(
                    ft.Row([ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), ft.Text("World", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                    #self.get_template_options("world"), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Create a new world for your story. Choose from templates or create a default world."
                ),
                ft.SubmenuButton(
                    ft.Row([ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, ft.Colors.PRIMARY), ft.Text("Chart", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                    #self.get_template_options("chart"), 
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
                    #on_click=self.story.import_folder_clicked, close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Import all files within a folder to create new widgets.", 
                ),  
                ft.MenuItemButton(
                    leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY), content="Import Widget(s)", 
                    #on_click=self.story.import_files_clicked, close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                    tooltip="Import file(s) to create new widgets.", 
                ),  
                ft.MenuItemButton(
                    leading=ft.Icon(ft.Icons.DOWNLOAD_OUTLINED, ft.Colors.PRIMARY), content="Export Widget(s)", 
                    #on_click=self.story.handle_export, close_on_click=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                    tooltip="Export parts of your story.",
                ),
            ],
            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
            style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            tooltip="Import or Export",
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

    # Called whenever we submit a new item (Chapter, note, category, etc.) via enter key
    async def submit_item(e: ft.Event[ft.TextField]):
        ''' Sets our state to submitting, and creates new item if unique. Father is either Plotline or arc for creating mini widgets '''
        # Grab our title from the textfield
        title = e.control.value

        # Protect against empty titles. They break things
        if not title or title.strip() == "":
            return
        
        tag = e.control.data    # Tag of widget
        if ":" in tag:
            tag, chart_type = tag.split(":")

        # Creating new folders
        if tag == "folder":
            await story.create_folder(name=title)

        # All other cases are widgets
        else:
            # Create the widget and reload all our rails
            await story.create_widget(title, tag, chart_type=chart_type if tag == "chart" else None)
        

    creating_item, set_creating_item = ft.use_state(False)
    creating_canvas, set_creating_canvas = ft.use_state(False)

    new_item_hint, set_new_item_hint = ft.use_state("")
    new_item_data, set_new_item_data = ft.use_state("")
    new_item_label, set_new_item_label = ft.use_state("")


    new_item_textfield = ft.TextField(     
        label=new_item_label,
        hint_text=new_item_hint, 
        data=new_item_data,                 # Hint text and data tag for logic                      
        autofocus=True, dense=True,                 
        capitalization=ft.TextCapitalization.WORDS,     # Capitalize sentences for names
        visible=creating_item,                                      # Hidden by default
        text_style=ft.TextStyle(size=14, color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),                         # Text style for consistency
        on_submit=submit_item,                         # Called when enter is pressed and textfield is focused
        key="new_item_textfield",
        on_blur=lambda: set_creating_item(False),
    )
    
                

    # Build the content of our rail
    content = ft.ListView(
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        expand=True,
        controls=[
            ft.Container(new_item_textfield, margin=ft.Margin.only(left=10, right=10, top=6))
        ],
    ) 


    # Load our content directory data into the rail
    #load_directory_data(
        #story=story,
        #directory=story.data.get('content_directory_path'),
        #rail=self,
        #column=content,
    #)

    
    # Add container to the bottom to make sure the drag target and gesture detector fill the rest of the space
    content.controls.append(ft.Container(expand=True))


    # Wrap the gd in a drag target so we can move characters here
    dt = ft.DragTarget(
        group="widgets", #on_will_accept=self._highlight_rail, on_leave=self._stop_highlight_rail,
        content=content,     # Our content is the content we built above
        #on_accept=lambda e: self.move_widget_file(e, self.story.data.get('content_directory_path'))
    )
    

    # Gesture detector to put on top of stack on the rail to pop open menus on right click
    menu_gesture_detector = ft.GestureDetector(
        content=dt,
        expand=True,
        #on_hover=self._set_menu_coords,
        #on_secondary_tap=lambda: self.story.open_menu(self.get_new_item_menu_options()),  
        on_tap=lambda e: print("Menu gesture detector tapped"),
        hover_interval=20,
    )

    # Use state to manage the width of the tree view rail during drag operations
    tree_view_rail_width, set_tree_view_rail_width = ft.use_state(app_settings.tree_view_rail_width)

    # Update the width of the tree view rail when dragging left and right
    def resize_tree_view_rail(e: ft.DragUpdateEvent):
        new_width = max(130, min(tree_view_rail_width + int(e.local_delta.x), 600))     # Clamp the width between 0 and 600
        set_tree_view_rail_width(new_width)

    # Save the final width to data when done dragging. If we do this while dragging, we update an ft.observable too much and trigger re-renders
    def save_tree_view_rail_width(e: ft.DragEndEvent=None):
        app_settings.tree_view_rail_width = tree_view_rail_width

    # Resizer/right boarder for the tree rail. Dragging resizes the tree view rail
    @ft.component
    def ActiveRailResizer() -> ft.GestureDetector:
        return ft.GestureDetector(
            content=ft.Container(
                width=10,   # Total width of the GD, so its easier to find with mouse
                content=ft.VerticalDivider(2, 2),     
                padding=ft.Padding.only(left=8), 
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
            ),
            # Stable key so re-renders (triggered while dragging) patch this control in place
            # instead of remounting it, which would drop the in-progress pan gesture.
            key="tree_view_rail_resizer",   # Set a key so re-renders view this control as the same instance, so our drag is not interrupted
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,  
            on_pan_update=resize_tree_view_rail,    # Resize the active rail as app is dragging
            on_pan_end=save_tree_view_rail_width,   # Save the resize when app is done dragging
            drag_interval=20,
        )

    
    # Return our build rail
    return ft.Container(
        ft.Row([
            ft.Column([
                header,
                ft.Divider(thickness=2, leading_indent=8),
                menu_gesture_detector
            ], expand=True, spacing=0, margin=ft.Margin.only(top=10, bottom=10)),
            ActiveRailResizer(),
        ], spacing=0),
        width=tree_view_rail_width,     # Set the width based on the settings, but will adjust when dragged without triggering a full re-render
        #key="tree_view_rail_container",
        alignment=ft.Alignment.TOP_CENTER,
        padding=ft.Padding.only(left=8),
        animate_size=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),  # Animate the drag so it looks nice
        animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    
    
    
    
    

