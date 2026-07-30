""" WIP """

import flet as ft
import os
from models.views.story import Story
from ui.rails.rail import Rail
from utils.tree_view import load_directory_data
from styles.menu_option_style import MenuOptionStyle
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.list_view import IsolatedListView
import math



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
                        ft.MenuItemButton(      # Documents
                            content=ft.Row([
                                ft.Text("Document"), 
                                ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                        tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                            leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY), 
                            data="document", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new document for text chapters or scenes in your story",
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
                            ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                    [
                        
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True, 
            )
        ]

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
                    ft.MenuItemButton(      # Documents
                        content=ft.Row([
                            ft.Text("Document"), 
                            ft.Icon(ft.Icons.ERROR_OUTLINE_OUTLINED, ft.Colors.OUTLINE, scale=0.8, 
                                    tooltip="This feature is still in early development and may not work as expected. Proceed with caution.")], spacing=6),
                        leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY),
                        data="document", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new document for text chapters or scenes in your story",
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
                        leading=ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, ft.Colors.PRIMARY), content="Import File(s)", 
                        on_click=self.story.import_files_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="Import file(s) to create new widgets.", 
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.DOWNLOAD_OUTLINED, ft.Colors.PRIMARY), content="Export Widget(s)", 
                        on_click=self.story.export_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                        tooltip="Export parts of your story.", disabled=True
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
        
        
        
        

