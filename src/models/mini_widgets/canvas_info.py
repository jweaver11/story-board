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
                'layers_expansion_tile_expanded': True,   

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

                # Layer info for our canvases
                'Layers': [{
                    'name': "Layer 1", 
                    'visible': True, 
                    'capture': "",   # Base64 string of capture of the layers drawing
                }],     # {'name': str, 'visible': bool, 'index': int, 'capture': str
                'Active Layer': 0,   # Index of our active layer we are drawing on
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

    async def _reorder_layers(self, e: ft.OnReorderEvent):
        new_index = e.new_index
        old_index = e.old_index
        layers = self.data.get('Layers', [])
        if new_index < 0 or old_index < 0 or new_index >= len(layers) or old_index >= len(layers):
            print("Invalid layer reorder indices: ", new_index, old_index)
            return
        layers.insert(new_index, layers.pop(old_index))
        self.data['Layers'] = layers
        
        await self.save_dict()
        self.widget.reload_widget()

    async def _delete_layer_clicked(self, e):

        async def _delete_layer_confirmed(e=None):
            for layer in self.data.get('Layers', []):
                if layer.get('name') == name:
                    self.data['Layers'].remove(layer)
                    break
            await self.save_dict()
            self.p.pop_dialog()
            self.widget.reload_widget()

        name = e.control.data   

        dlg = ft.AlertDialog(
            title=f"Delete {name}?",
            content=ft.Text(f"This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)),
                ft.TextButton("Delete", on_click=_delete_layer_confirmed, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
            ]
        )
        self.p.show_dialog(dlg)

    # Sets the new active layer
    async def _toggle_selected_layer_visibility(self, e):
        name = e.control.data
        for layer in self.data.get('Layers', []):
            if layer.get('name') == name:
                layer['visible'] = not layer.get('visible', True)
                await self.save_dict()
                self.widget.reload_widget()
                return
        

    # Sets a new active layer based on the layer we click on in the layers list
    async def _set_active_layer(self, e):
        for idx, layer in enumerate(self.data.get('Layers', [])):
            if layer.get('name') == e.control.data:
                self.data['Active Layer'] = idx
                await self.save_dict()
                self.widget.reload_widget()
                return
        
    # Creates a new layer
    async def _create_new_layer_clicked(self, e):

        async def _create_layer_confirmed(e=None):
            name = new_layer_tf.value or f"Layer {len(self.data.get('Layers', []))+1}"
            self.data['Layers'].append({'name': name, 'visible': True, 'capture': ""})
            await self.save_dict()
            self.p.pop_dialog()
            self.widget.reload_widget()

        new_layer_tf = ft.TextField(capitalization=ft.TextCapitalization.WORDS, on_submit=_create_layer_confirmed, autofocus=True)
        dlg = ft.AlertDialog(
            title="Layer Name",
            content=new_layer_tf,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                ft.TextButton("Create", on_click=_create_layer_confirmed, style=ft.ButtonStyle(mouse_cursor="click")),
            ]
        )
        self.p.show_dialog(dlg)
    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        #TODO: Layers, add reference images in the body
        #TODO: Layer option to upload an image
        # Option to export canvas as image file (png, jpg, etc). 
        # Add color_filter for both decoration image and container ?
        # Fill tool??
        # Manage saving so not at the end of every stroke.
        # Add undo/redo based on capture list
        # Remove old items from the undo/redo list after like 30 or so 
        # Height ad width just for exporting
        # Set dark and light transparent bg images for all canvases

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

        # Textfield of our canvas description
        description_tf = ft.TextField(
            expand=True, label="Description", value=self.data.get('Description', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}),   # When we click out of the text field, we save our changes
            focus_color=self.widget.data.get('color', None),
            cursor_color=self.widget.data.get('color', None),
            focused_border_color=self.widget.data.get('color', None),
            label_style=ft.TextStyle(color=self.widget.data.get('color', None)),
        )


        create_new_layer_button = ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, mouse_cursor="click",
            tooltip="Add new layer",
            on_click=self._create_new_layer_clicked
        )

        # Create our expansion tile to hold our layers
        layer_expansion_tile = ft.ExpansionTile(
            "Layers",
            [
                ft.ReorderableListView(on_reorder=self._reorder_layers, scroll="auto", expand=True, controls=[]),   # This will hold our layers and allow us to reorder them
                create_new_layer_button 
            ],
            leading=ft.Icons.LAYERS_OUTLINED,
            tile_padding=ft.Padding.symmetric(horizontal=6),
            expanded=self.data.get('layers_expansion_tile_expanded', True),
            on_change=lambda e: self.change_data(**{'layers_expansion_tile_expanded': e.control.expanded})
        )

        # Add each layer to the expansion tile
        for idx, layer in enumerate(self.data.get('Layers', [])):
            name = layer.get('name', f"Layer {idx+1}")
            visible = layer.get('visible', True)
            layer_tile = ft.ReorderableDragHandle(
                ft.ListTile(
                    name, expand=True,
                    leading=ft.IconButton(   # Toggle visibility button
                        ft.Icons.VISIBILITY if visible else ft.Icons.VISIBILITY_OFF, mouse_cursor="click",
                        on_click=self._toggle_selected_layer_visibility, data=name
                    ),  
                    trailing=ft.IconButton(     # Delete button
                        ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, mouse_cursor="click", data=name, on_click=self._delete_layer_clicked
                    ) if idx != 0 else None,    # Don't allow deleting the first layer
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if self.data.get('Active Layer', 0) == idx else None,  # Lighter bg for selected layer
                    on_click=self._set_active_layer, data=name,
                    content_padding=ft.Padding.only(right=30),
                )
            )
            layer_expansion_tile.controls[0].controls.append(layer_tile)

        
        
        content = ft.Column([
            ft.Container(height=1),  # Spacing 
            description_tf,
            layer_expansion_tile
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



        