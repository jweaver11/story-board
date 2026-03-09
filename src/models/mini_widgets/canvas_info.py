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
                'left': 40,     # Position of our button
                'top': 40,
                'alignment': None,      # Saved alignment of our button for easier resizing

                'drawing_mode': True,

                # Canvas info
                'Description': str,
                "Width": None,
                "Height": None,
                "Aspect Ratio": None,      # Used over height and width if set
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

    # Called to toggle our drawing mode on/off
    def _toggle_drawing_mode(self, e=None):
        ''' Toggles our drawing mode on/off '''

        # Change our data value for drawing mode and save it
        self.data['drawing_mode'] = not self.data.get('drawing_mode', False)
        self.p.run_task(self.save_dict)

        e.control.icon = ft.Icons.DRAW_OUTLINED if not self.data['drawing_mode'] else ft.Icons.DONE

        # If we entered drawing mode, show our drawing canvas rail. Otherwise, go back to the previous rail
        if self.data.get('drawing_mode', False):
            self.widget.story.workspaces_rail.change_workspace(None, self.widget.story, force_rail="canvas")
            self.widget.canvas.content.mouse_cursor = ft.MouseCursor.PRECISE
        else:
            
            self.widget.canvas.content.mouse_cursor = ft.MouseCursor.CLICK

        self.widget.canvas.content.update()

    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        #TODO: Layers, add reference images in the body

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

        # Create our header
        header = ft.Row([
            ft.IconButton(
                ft.Icons.DRAW_OUTLINED if not self.data.get('drawing_mode') else ft.Icons.DONE,
                tooltip="Enter Drawing Mode" if not self.data.get('drawing_mode') else "Exit Drawing Mode",
                on_click=self._toggle_drawing_mode,
            ),
            # Undo and redo buttons
            ft.PopupMenuButton(
                icon=ft.Icons.IMAGE_ASPECT_RATIO_OUTLINED, tooltip="Set the background of your canvas. If one is set, it will be exported with the canvas",
                menu_padding=ft.Padding.all(0), 
                #on_cancel=self._set_color,
                items=[
                    #ft.PopupMenuItem("None", on_click=self._set_canvas_background, tooltip="No background"),
                    #ft.PopupMenuItem("Color", on_click=self._set_canvas_background, tooltip="Set a solid color background"),
                    #ft.PopupMenuItem("Image", on_click=self._set_canvas_background, tooltip="Set an image as the background"),
                ]
            ),
           
            # Button to hide markers
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
            header,
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



        