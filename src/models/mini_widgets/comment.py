'''
Simple mini widget that consists of a title, and a body that is a string
'''

import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle


# Class that holds our mini note objects inside images or chapters
class Comment(MiniWidget):
    
    # Constructor
    def __init__(self, title: str, widget: Widget, page: ft.Page, key: str, data: dict=None):

        # Parent constructor
        super().__init__(
            title=title,        
            widget=widget,   
            page=page,          
            key=key,  
            data=data,          
        ) 

        verify_data(
            self,   # Pass in our object so we can access its data and change it
            {   # Pass in the required fields and their types``
                'tag': "comment",
                'content': str,
                'collapsed': bool,
            },
        )

        self.visible = True
        self.padding=ft.Padding.only(left=8, right=8, bottom=8)
        self.animate=ft.Animation(200, ft.AnimationCurve.DECELERATE)

        # Load our widget UI on start after we have loaded our data
        self.reload_mini_widget()

    def expand_mini_widget(self, e=None):
        ''' Shows our mini widget on the side of the document '''
        self.change_data(**{'collapsed': False})  # Change our data to not collapsed, which will trigger a reload
        self.reload_mini_widget()

    def collapse_mini_widget(self, e=None):
        self.change_data(**{'collapsed': True})  # Change our data to collapsed, which will trigger a reload
        self.reload_mini_widget()

    def _get_menu_options(self) -> list[ft.Control]:

        # Color, rename
        return [
            MenuOptionStyle(
                on_click=self._rename_clicked,
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
                    self._get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    tooltip="Change this widget's color"
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


    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_mini_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        title_control = ft.Row([
            ft.GestureDetector(
                ft.Text(f"\t{self.data['title']}", weight=ft.FontWeight.BOLD, tooltip=f"Rename {self.title}", expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                on_double_tap=self._rename_clicked,
                on_tap=self._rename_clicked,
                on_secondary_tap=lambda e: self.widget.story.open_menu(self._get_menu_options()),
                mouse_cursor="click", on_enter=self._set_menu_coords, 
            ),
            
            ft.GestureDetector(
                ft.IconButton(
                    ft.Icons.EXPAND_LESS if self.data.get('collapsed', False) else ft.Icons.EXPAND_MORE,
                    ft.Colors.OUTLINE, mouse_cursor="click",
                    tooltip=f"Collapse {self.title}" if not self.data.get('collapsed', False) else f"Expand {self.title}",
                    on_click=self.expand_mini_widget if self.data.get('collapsed', False) else self.collapse_mini_widget,
                ),
                on_secondary_tap=lambda e: self.widget.story.open_menu(self._get_menu_options()),
                on_enter=self._set_menu_coords, 
            ),
        ], spacing=0, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        content_tf = ft.TextField(
            self.data['content'], expand=True, 
            multiline=True, on_blur=lambda e: self.change_data(**{'content': e.control.value}),
            focused_border_color=self.data.get('color', ft.Colors.PRIMARY),
            cursor_color=self.data.get('color', ft.Colors.PRIMARY),
            dense=True, capitalization=ft.TextCapitalization.SENTENCES
        )

        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, spacing=6,
            controls=[
                ft.Container(height=1),  # Little padding
                content_tf,
            ]
        )

        column = ft.Column([
            title_control,
        ], expand=True, scroll="none", tight=True, alignment=ft.MainAxisAlignment.START, spacing=0)


        # If we are not collapsed, show the content, otherwise just show the title
        if not self.data.get('collapsed', False):
            self.padding=ft.Padding.only(left=8, right=8, bottom=8)
            column.controls.append(ft.Divider(height=2, thickness=2))
            column.controls.append(content)
        else:
            self.padding=ft.Padding.only(left=8, right=8)
        
        self.content = column

        try:
            self.update()
        except Exception as _:
            pass




        