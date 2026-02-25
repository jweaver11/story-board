""" WIP """

import flet as ft
import os
from models.views.story import Story
from ui.rails.rail import Rail
from utils.tree_view import load_directory_data
from styles.menu_option_style import MenuOptionStyle
from utils.alert_dialogs.new_canvas import new_canvas_alert_dlg
from models.isolated_controls.column import IsolatedColumn
import threading
import asyncio


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
            ft.PopupMenuButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="New", menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        "Category", icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                        on_click=self.new_item_clicked, data="category"
                    ),
                    ft.PopupMenuItem(
                        "Document", icon=ft.Icons.NOTE_ADD_OUTLINED,
                        on_click=self.new_item_clicked, data="document"
                    ),
                    ft.PopupMenuItem(
                        "Canvas", icon=ft.Icons.BRUSH_OUTLINED,
                        on_click=self.new_canvas_clicked, data="canvas"
                    ),
                    ft.PopupMenuItem(
                        "Canvas Board", icon=ft.Icons.SPACE_DASHBOARD_OUTLINED,
                        on_click=self.new_item_clicked, data="canvas_board"
                    ),
                    ft.PopupMenuItem(
                        "Note", ft.Icons.NOTE_ALT_OUTLINED,
                        on_click=self.new_item_clicked, data="note"
                    ),
                    ft.PopupMenuItem(
                        "Character", icon=ft.Icons.PERSON_OUTLINED,
                        on_click=self.new_item_clicked, data="character"
                    ),  
                    ft.PopupMenuItem(
                        "Character Connection Map", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
                        on_click=self.new_item_clicked, data="character_connection_map"
                    ),
                    ft.PopupMenuItem(
                        "Plotline", icon=ft.Icons.TIMELINE_OUTLINED,
                        on_click=self.new_item_clicked, data="plotline"
                    ),
                    ft.PopupMenuItem(
                        "Map", icon=ft.Icons.MAP_OUTLINED,
                        on_click=self.new_item_clicked, data="map"
                    ),
                    ft.PopupMenuItem(
                        "World", icon=ft.Icons.PUBLIC_OUTLINED,
                        on_click=self.new_item_clicked, data="world"
                    ),
                ]
            ),
            ft.PopupMenuButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload", menu_padding=0,
                items=[
                    ft.PopupMenuItem("Canvas", icon=ft.Icons.BRUSH_OUTLINED),
                    ft.PopupMenuItem("Canvas Board", icon=ft.Icons.SPACE_DASHBOARD_OUTLINED),
                    ft.PopupMenuItem("Document", icon=ft.Icons.NOTE_ADD_OUTLINED),
                    ft.PopupMenuItem("Character", icon=ft.Icons.PERSON_OUTLINED),
                    ft.PopupMenuItem("Character Connection Map", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED),
                    ft.PopupMenuItem("Image", icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED),
                    ft.PopupMenuItem("Map", icon=ft.Icons.MAP_OUTLINED),
                    ft.PopupMenuItem("Note", icon=ft.Icons.NOTE_ALT_OUTLINED),
                    ft.PopupMenuItem("Plotline", icon=ft.Icons.TIMELINE_OUTLINED),
                    ft.PopupMenuItem("World", icon=ft.Icons.PUBLIC_OUTLINED),
                ]
            ),
        ]

    async def on_will_accepts(self, e):
        ''' Changes our rails background to a transparent color on hover '''
        e.control.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
        e.control.content.update()

    async def leave_rail(self, e):  
        ''' Changes our rails background back to normal when not hovering '''
        e.control.content.bgcolor = ft.Colors.with_opacity(0.0, ft.Colors.ON_SURFACE)
        e.control.content.update()


    # Called to return our list of menu options for the content rail
    def get_menu_options(self) -> list[ft.Control]:
            
        # Builds our buttons that are our options in the menu
        return [
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6),
                    ),
                    tooltip="New", menu_padding=0, expand=True, padding=ft.Padding.all(0),
                    items=[
                        ft.PopupMenuItem(
                            "Category", icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                            on_click=self.new_item_clicked, data="category"
                        ),
                        ft.PopupMenuItem(
                            "Document", icon=ft.Icons.NOTE_ADD_OUTLINED,
                            on_click=self.new_item_clicked, data="document"
                        ),
                        ft.PopupMenuItem(
                            "Canvas", icon=ft.Icons.BRUSH_OUTLINED,
                            on_click=self.new_item_clicked, data="canvas"
                        ),
                        ft.PopupMenuItem(
                            "Canvas Board", icon=ft.Icons.SPACE_DASHBOARD_OUTLINED,
                            on_click=self.new_item_clicked, data="canvas_board"
                        ),
                        ft.PopupMenuItem(
                            "Note", ft.Icons.NOTE_ALT_OUTLINED,
                            on_click=self.new_item_clicked, data="note"
                        ),
                        ft.PopupMenuItem(
                            "Character", icon=ft.Icons.PERSON_OUTLINED,
                            on_click=self.new_item_clicked, data="character"
                        ),  
                        ft.PopupMenuItem(
                            "Character Connection Map", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED,
                            on_click=self.new_item_clicked, data="character_connection_map"
                        ),
                        ft.PopupMenuItem(
                            "Plotline", icon=ft.Icons.TIMELINE_OUTLINED,
                            on_click=self.new_item_clicked, data="plotline"
                        ),
                        ft.PopupMenuItem(
                            "Map", icon=ft.Icons.MAP_OUTLINED,
                            on_click=self.new_item_clicked, data="map"
                        ),
                        ft.PopupMenuItem(
                            "World Building", icon=ft.Icons.PUBLIC_OUTLINED,
                            on_click=self.new_item_clicked, data="world_building"
                        ),
                    ]
                ),
                no_padding=True
            ),
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED), ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),]),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6),
                    ),
                    tooltip="Upload", menu_padding=0,
                    items=[
                        ft.PopupMenuItem("Image", icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,),
                        ft.PopupMenuItem("Document", icon=ft.Icons.NOTE_ADD_OUTLINED,),
                        ft.PopupMenuItem("Canvas", icon=ft.Icons.BRUSH_OUTLINED,),
                        ft.PopupMenuItem("Note", icon=ft.Icons.NOTE_ALT_OUTLINED,),
                        ft.PopupMenuItem("Character", icon=ft.Icons.PERSON_OUTLINED,),
                        ft.PopupMenuItem("Family Tree", icon=ft.Icons.FAMILY_RESTROOM_OUTLINED),
                        ft.PopupMenuItem("Plotline", icon=ft.Icons.TIMELINE_OUTLINED,),
                        ft.PopupMenuItem("Map", icon=ft.Icons.MAP_OUTLINED,),
                        ft.PopupMenuItem("World Building", icon=ft.Icons.PUBLIC_OUTLINED,),
                    ]
                ),
                no_padding=True
            )
        ]
        

    # Reload the rail whenever we need
    def reload_rail(self) -> ft.Control:
        ''' Reloads the content rail '''

        # Depending on story type, we can have different content creation options
        # Categories get colors as well??
        # Creating a document for comics creates a folder to store images and drawings
        # Creating a document for novels creates a text document for writing, and allows
        # Right clicking allows to upload

        # TODO: Should be 2 buttons: New and upload. Each has all those options
        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=self.top_row_buttons
        )
                 

        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[]
        )

        # Load our content directory data into the rail
        load_directory_data(
            page=self.p,
            story=self.story,
            directory=self.directory_path,
            rail=self,
            column=content,
            #additional_directory_menu_options=self.get_menu_options()
        )

        content.controls.append(ft.Container(height=6)) # Padding

        # Append our hiddent textfields for creating new categories, documents, and notes
        content.controls.append(self.new_item_textfield)

        # Add container to the bottom to make sure the drag target and gesture detector fill the rest of the space
        content.controls.append(ft.Container(expand=True))


        # Wrap the gd in a drag target so we can move characters here
        dt = ft.DragTarget(
            group="widgets", on_will_accept=self.on_will_accepts, on_leave=self.leave_rail,
            content=ft.Container(content=content, bgcolor=ft.Colors.with_opacity(0, ft.Colors.ON_SURFACE)),     # Our content is the content we built above
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

        

        self.content = IsolatedColumn(
            spacing=0,
            expand=True,
            controls=[
                header,
                ft.Divider(),
                menu_gesture_detector
            ]
        )
        #self.content = content
        
        # Apply our update
        self.p.update()
        

