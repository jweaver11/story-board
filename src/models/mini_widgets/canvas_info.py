'''
The Canvas Information display mini widget so our canvases have unique data to display
Without always taking up drawing space
'''



import flet as ft
from models.widget import Widget
from models.mini_widget import MiniWidget
from utils.verify_data import verify_data


class CanvasInformationDisplay(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        widget: Widget,                  
        page: ft.Page, 
        key: str,                       
        data: dict = None               
    ):
        
        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True
        

        # Parent constructor
        super().__init__(
            title=title,           
            widget=widget, 
            page=page,              
            data=data,              
            key=key     
        ) 

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our object so we can access its data and change it
            {   
                'title': self.title,          # Title of the mini widget, should match the object title
                'tag': "canvas_information_display",        

                # Undo and re-do state tracking for captures
                'undo_list': list,
                'redo_list': list,

                # Background can be an image, color, or left empty for transparent. 
                'background': None,             # We display it using a container, but manually create it when exporting
                'bg_type': None,            # "color", "image", or None so we know how to display it
                'bg_blend_mode': "src_over",    # Blend mode for background. Starts default src_over (none)

                # Canvas info
                'Description': str,
                "Width": None,
                "Height": None,
                "aspect_ratio": None,      # Used over height and width if set
                'Is Locked': False, # Lock state tracking. When locked, no changes can be made (no drawing)
                'Layers': [], #??
            },
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)

        # Reloads the information display of the canvas
        self.reload_mini_widget()

    # Called when saving changes in our mini widgets data to the widgetS json file
    async def save_dict(self):
        ''' Saves our current data to the widgetS json file using this objects dictionary path '''

        try:
            # Our data is correct, so we update our immidiate parents data to match
            self.widget.data[self.key] = self.data

            # Recursively updates the parents data until widget=widget (widget), which saves to file
            await self.widget.save_dict()

        except Exception as e:
            print(f"Error saving mini widget data to {self.title}: {e}")


    async def hide_mini_widget(self, e=None):
        if not self.visible:
            return
        self.data['visible'] = False
        await self.save_dict()
        self.visible = False
        self.update()

    async def show_mini_widget(self, e=None):
        if self.visible:
            return
        self.data['visible'] = True
        await self.save_dict()
        self.visible = True
        self.update()

    #
    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        #TODO: Layers, add reference images in the body
        #TODO: Layer option to upload an image
        # Option to export canvas as image file (png, jpg, etc). 
        # Add color_filter for both decoration image and container ?
        # Fill tool??
        # Little Info Display Button in the bottom right that can be dragged around and shows canvas info display
        # Manage saving so not at the end of every stroke.
        # Add undo/redo based on capture list
        # Remove old items from the undo/redo list after like 30 or so 
        # Open drawings and maps in their own window to not lag?????
        # Always use aspect ratio when renderng canvas, height and width are just for exporting them

        title_control = ft.Row([
            ft.Icon(ft.Icons.BRUSH, self.widget.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD, selectable=True, overflow=ft.TextOverflow.FADE),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}",
                mouse_cursor=ft.MouseCursor.CLICK,
                on_click=self.hide_mini_widget,
            ),
        ])

        

        description_tf = ft.TextField(
            expand=True, label="Description", value=self.data.get('Description', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}),   # When we click out of the text field, we save our changes
            focus_color=self.widget.data.get('color', None),
            cursor_color=self.widget.data.get('color', None),
            focused_border_color=self.widget.data.get('color', None),
            label_style=ft.TextStyle(color=self.widget.data.get('color', None)),
        )
        
        content = ft.Column([
            ft.Container(height=1),  # Spacing 
            description_tf
        ], expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START)

        
        column = ft.Column([
            title_control,
            ft.Divider(height=2, thickness=2),
            content
        ], expand=True, scroll="none", tight=True, alignment=ft.MainAxisAlignment.START)
        
        self.content = column

        try:
            self.update()
        except Exception as _:
            pass



        