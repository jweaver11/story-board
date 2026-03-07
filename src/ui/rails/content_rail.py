""" WIP """

import flet as ft
import os
from models.views.story import Story
from ui.rails.rail import Rail
from utils.tree_view import load_directory_data
from styles.menu_option_style import MenuOptionStyle
from utils.alert_dialogs.new_canvas import new_canvas_alert_dlg
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.list_view import IsolatedListView
import math



# Class is created in main on program startup
class ContentRail(Rail):

    # Constructor
    def __init__(self, page: ft.Page, story: Story):
        
        # Initialize the parent Rail class first
        super().__init__(
            page=page,
            story=story,
            directory_path=story.data.get('content_directory_path', '')
        )

        self.top_row_buttons = [
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
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ), 
                    ft.MenuItemButton(      # Documents
                        leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY), content="Document", 
                        data="document", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new document for text chapters or scenes in your story",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ), 
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Canvas",
                        data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                    ),
                    ft.MenuItemButton(      
                        leading=ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                        data="note", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ), 
                    ft.SubmenuButton(
                        ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), ft.Text("Character", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                        self.get_template_options("character"), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="Create a new character for your story. Choose from templates or create a default character."
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                        data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), content="Canvas Board",
                        data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                        data="map", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                    ),
                    ft.SubmenuButton(
                        ft.Row([ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), ft.Text("World", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                        self.get_template_options("world"), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="Create a new world for your story. Choose from templates or create a default world."
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, ft.Colors.PRIMARY), content="Object", 
                        data="object", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="New Objects or Items for your story"
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Connection Map", 
                        data="character_connection_map", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="Visualize the connections between the characters in your story"
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.PERSONAL_VIDEO_ROUNDED, ft.Colors.PRIMARY), content="Video", 
                        data="video", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="New video references for your story"
                    ),  # TODO: NEEDS TO JUST USE UPLOAD VIDEO, not actually craate one
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.PRIMARY),
                    padding=ft.Padding.all(8), shape=ft.BoxShape.CIRCLE,
                    width=40, height=40, alignment=ft.Alignment.CENTER
                ),
                [     
                    ft.MenuItemButton(      # Folders
                        leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY), content="Folder", 
                        data="folder", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new folder to organize your story",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ), 
                    ft.MenuItemButton(      # Documents
                        leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY), content="Document", 
                        data="document", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new document for text chapters or scenes in your story",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ), 
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Canvas",
                        data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                    ),
                    ft.MenuItemButton(      
                        leading=ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                        data="note", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ), 
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), content="Character", 
                        data="character", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new character for your story. Choose from templates or create a default character.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                        data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), content="Canvas Board",
                        data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                        data="map", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                    ),
                    
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), content="World", 
                        data="world", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new world for your story. Choose from templates or create a default world.",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, ft.Colors.PRIMARY), content="Object", 
                        data="object", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="New Objects or Items for your story"
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Connection Map", 
                        data="character_connection_map", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="Visualize the connections between the characters in your story"
                    ),  
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.PERSONAL_VIDEO_ROUNDED, ft.Colors.PRIMARY), content="Video", 
                        data="video", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                        tooltip="New video references for your story"
                    ),
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
        ]

        self.reload_rail()

    async def on_will_accepts(self, e):
        ''' Changes our rails background to a transparent color on hover '''
        e.control.content.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE_VARIANT)
        e.control.content.update()

    async def leave_rail(self, e):  
        ''' Changes our rails background back to normal when not hovering '''
        e.control.content.bgcolor = ft.Colors.with_opacity(0.0, ft.Colors.ON_SURFACE)
        e.control.content.update()


    # Called to return our list of menu options for the content rail
    def get_menu_options(self) -> list[ft.Control]:

        return [
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True)], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        ft.MenuItemButton(      # Folders
                            leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY), content="Folder", 
                            data="folder", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new folder to organize your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(      # Documents
                            leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY), content="Document", 
                            data="document", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new document for text chapters or scenes in your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Canvas",
                            data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                        ),
                        ft.MenuItemButton(      
                            leading=ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                            data="note", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ), 
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), ft.Text("Character", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("character"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                            tooltip="Create a new character for your story. Choose from templates or create a default character."
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                            data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                            tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), content="Canvas Board",
                            data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                            data="map", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                        ),
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), ft.Text("World", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("world"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                            tooltip="Create a new world for your story. Choose from templates or create a default world."
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, ft.Colors.PRIMARY), content="Object", 
                            data="object", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                            tooltip="New Objects or Items for your story"
                        ),  
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Connection Map", 
                            data="character_connection_map", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                            tooltip="Visualize the connections between the characters in your story"
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.PERSONAL_VIDEO_ROUNDED, ft.Colors.PRIMARY), content="Video", 
                            data="video", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                            tooltip="New video references for your story"
                        ),
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True
            ),

            # Upload options
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.PRIMARY), ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True)], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        ft.MenuItemButton(      # Folders
                            leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, ft.Colors.PRIMARY), content="Folder", 
                            data="folder", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new folder to organize your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(      # Documents
                            leading=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, ft.Colors.PRIMARY), content="Document", 
                            data="document", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new document for text chapters or scenes in your story",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY), content="Canvas",
                            data="canvas", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Canvas for sketching drawing, or visual note taking",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                        ),
                        ft.MenuItemButton(      
                            leading=ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED, ft.Colors.PRIMARY), content="Note", 
                            data="note", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new note for Ideas, Themes, Research, Points of Interest, etc.",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ), 
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.PERSON_OUTLINED, ft.Colors.PRIMARY), content="Character", 
                            data="character", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new character for your story. Choose from templates or create a default character.",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                            data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                            tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Colors.PRIMARY), content="Canvas Board",
                            data="canvas_board", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Canvas Board to organize your canvases and plan your story visually",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                            data="map", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True
                        ),
                        
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), content="World", 
                            data="world", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new world for your story. Choose from templates or create a default world.",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, ft.Colors.PRIMARY), content="Object", 
                            data="object", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                            tooltip="New Objects or Items for your story"
                        ),  
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.FAMILY_RESTROOM_OUTLINED, ft.Colors.PRIMARY), content="Character Connection Map", 
                            data="character_connection_map", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                            tooltip="Visualize the connections between the characters in your story"
                        ),  
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.PERSONAL_VIDEO_ROUNDED, ft.Colors.PRIMARY), content="Video", 
                            data="video", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), disabled=True,
                            tooltip="New video references for your story"
                        ),
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True
            )
        ]
        

    # Reload the rail whenever we need
    def reload_rail(self) -> ft.Control:
        ''' Reloads the content rail '''

        menubar = ft.MenuBar(
            self.top_row_buttons,
            #expand=True,
            style=ft.MenuStyle(
                bgcolor="transparent", shadow_color="transparent",
                shape=ft.RoundedRectangleBorder(radius=10),
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
                ft.Container(height=6),
                self.new_item_textfield
            ],
        )


        # Load our content directory data into the rail
        load_directory_data(
            page=self.p,
            story=self.story,
            directory=self.directory_path,
            rail=self,
            column=content,
        )

        
        # Add container to the bottom to make sure the drag target and gesture detector fill the rest of the space
        content.controls.append(ft.Container(expand=True))


        # Wrap the gd in a drag target so we can move characters here
        dt = ft.DragTarget(
            group="widgets", on_will_accept=self.on_will_accepts, on_leave=self.leave_rail,
            content=ft.Container(content=content, bgcolor=ft.Colors.with_opacity(0, ft.Colors.ON_SURFACE), border_radius=ft.BorderRadius.all(8)),     # Our content is the content we built above
            on_accept=lambda e: self.on_drag_accept(e, self.directory_path)
        )
        

        # Gesture detector to put on top of stack on the rail to pop open menus on right click
        menu_gesture_detector = ft.GestureDetector(
            content=dt,
            expand=True,
            on_hover=self.on_hovers,
            on_secondary_tap=lambda e: self.story.open_menu(self.get_menu_options()),
            hover_interval=20,
        )

        self.controls = [
            header,
            ft.Divider(),
            menu_gesture_detector
        ]
        
        
        # Apply our update
        try:
            self.update()
        except Exception as _:
            pass
        

