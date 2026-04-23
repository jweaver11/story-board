# Reference images for chapters or canvases .

'''
Simple mini widget that consists of a title, and a body that is a string
'''

import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle


# Class that holds our mini note objects inside images or chapters
class ReferenceImage(MiniWidget):
    
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
                'tag': "reference_image",
                'image': str,
                'collapsed': bool,
            },
        )

        self.bgcolor = ft.Colors.TRANSPARENT
        self.border = None
        self.padding = ft.Padding.only(right=11, bottom=8)
        self.margin = None
        self.shadow = None
        self.expand = False

        # Load our widget UI on start after we have loaded our data
        self.reload_mini_widget()

    def expand_mini_widget(self, e=None):
        ''' Shows our mini widget on the side of the document '''
        self.change_data(**{'collapsed': False})  # Change our data to not collapsed, which will trigger a reload
        self.reload_mini_widget()

    def collapse_mini_widget(self, e=None):
        self.change_data(**{'collapsed': True})  # Change our data to collapsed, which will trigger a reload
        self.reload_mini_widget()


    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_mini_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        async def _show_options_button(e=None):
            options_button.visible = True
            options_button.update()

        async def _hide_options_button(e=None):
            options_button.visible = False
            options_button.update()

        title_control = ft.GestureDetector(
            content=ft.Row([
                ft.Text(
                    f"{self.data['title']}", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), 
                    color=self.data.get('color', None), weight=ft.FontWeight.BOLD, expand=True,
                ),
                options_button := ft.IconButton(
                    icon=ft.Icons.MORE_VERT_ROUNDED,
                    visible=False,
                    on_click=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                    mouse_cursor=ft.MouseCursor.CLICK,
                ),
            ], height=35),
            #on_double_tap=self._rename_clicked,
            on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
            on_hover=self._set_menu_coords,
            on_enter=_show_options_button,
            on_exit=_hide_options_button,
            mouse_cursor="click", hover_interval=100,
        )

        image = ft.Image(
            self.data.get('image', ''),
            ft.Text("Error loading image"),
            fit=ft.BoxFit.COVER,
        )

        content = ft.Column(
            tight=True, 
            alignment=ft.MainAxisAlignment.START, #spacing=6,
            controls=[
                title_control,
                image,
            ]
        )
        
        self.content = content

        try:
            self.update()
        except Exception as _:
            pass