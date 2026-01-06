'''
Simple mini widget that consists of a title, and a body that is a string
'''

import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data


# Class that holds our mini note objects inside images or chapters
class Comment(MiniWidget):
    
    # Constructor
    def __init__(self, title: str, owner: Widget, father, page: ft.Page, key: str, data: dict=None):

        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,   
            father=father,   
            page=page,          
            key=key,  
            data=data,          
        ) 

        verify_data(
            self,   # Pass in our object so we can access its data and change it
            {   # Pass in the required fields and their types``
                'tag': "comment",
                'content': str,
            },
        )


        # UI Controls
        self.title_control = ft.TextField(
            value=self.title,
            label=None,
        )

        self.content_control = ft.TextField(
            #value=self.data['content'],
            label="Body",
            expand=True,
            multiline=True,
        )

        # Load our widget UI on start after we have loaded our data
        self.reload_mini_widget()


    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_mini_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Our column that will display our header filters and body of our widget
        self.title_control = ft.TextButton(
            f"Hello from mini note: {self.title}",
            on_click=self.toggle_visibility,
        )

        self.content_control = ft.TextField(
            #value=self.data['content'],
            label="Body",
            expand=True,
            multiline=True,
        )

        self.content = ft.Column(
            spacing=6,
            controls=[self.title_control, self.content_control],
        )

        self.p.update()




        