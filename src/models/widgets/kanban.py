''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from styles.text_fields import TextField
import asyncio
from models.dataclasses.item_template import default_item_template_data


class Kanban(Widget):

    # Constructor
    def __init__(self, title: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      
            directory_path = directory_path,    
            story = story,                     
            data = data,
            is_new = is_new
        )

         # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget data
                'tag': "kanban",             # Tag to identify what type of object this is
                #'color': app.settings.data.get('widget_defaults', {}).get('item', {}).get('color'),

            },
        )

    def build(self):

        super().build()

        self.description_tf.bgcolor = ft.Colors.SURFACE

        self.content = ft.Column(
            [
                ft.Container(expand=True),
                self.description_tf
            ], 
            expand=True, spacing=0, alignment=ft.MainAxisAlignment.END
        )