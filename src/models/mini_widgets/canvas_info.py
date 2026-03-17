'''
The Canvas Information display mini widget so our canvases have unique data to display
Without always taking up drawing space
'''



import flet as ft
from models.widget import Widget
from models.mini_widget import MiniWidget
from utils.verify_data import verify_data
import asyncio
from styles.snack_bar import SnackBar
from flet_color_pickers import ColorPicker
import flet.canvas as cv




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

                # Canvas info
                'Description': str,
                "width": None,              # Resolution size used for exporting
                "height": None,
                "aspect_ratio": None,       # Actually used for displaying the canvas, and we scale up when exporting
                'Is Locked': False, # Lock state tracking. When locked, no changes can be made (no drawing)

                # Layer info for our canvases
                'Layers': [
                    {
                        'name': "Background",       
                        'visible': True, 
                        'capture': "",   # Base64 string of capture of the layers drawing
                    },
                    {
                        'name': "Layer 1", 
                        'visible': True, 
                        'capture': "",   # Base64 string of capture of the layers drawing
                    }
                ],     # {'name': str, 'visible': bool, 'index': int, 'capture': str
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
        self.widget.story.blocker.visible = True
        self.widget.story.blocker.update()
        await asyncio.sleep(0.1)
        self.data['visible'] = False
        await self.save_dict()
        self.visible = False
        self.update()
        self.widget.story.blocker.visible = False
        self.widget.story.blocker.update()
        await self.widget.story.close_menu()   

    async def show_mini_widget(self, e=None):
        await self.widget.story.close_menu()
        if self.visible:
            return
        self.widget.story.blocker.visible = True
        self.widget.story.blocker.update()
        await asyncio.sleep(0.1)
        self.data['visible'] = True
        await self.save_dict()
        self.visible = True
        self.update()
        self.widget.story.blocker.visible = False
        self.widget.story.blocker.update()

        

    async def _set_background(self, e):

        await self.widget.story.close_menu()

        type = e.control.data

        # TODO: Create a new background layer when this is clicked

        # Set a color as the background
        if type == "color":

            async def _color_change(e):     # Set the color to the picked one
                color_picker.color = e.data
                print(color_picker.color)

            async def _set_confirmed(e=None):

                self.data['background'] = color_picker.color
                self.data['bg_type'] = "color"

                await self.save_dict()
                self.p.pop_dialog()

                self.widget.story.blocker.visible = True
                self.widget.story.blocker.update()
                await asyncio.sleep(0.1)

                self.widget.story.workspace.reload_workspace()
                self.widget.story.blocker.visible = False
                self.widget.story.blocker.update()

            color_picker = ColorPicker(
                self.data.get('background', ft.Colors.PRIMARY) if self.data.get('bg_type') == "color" else ft.Colors.PRIMARY,
                on_color_change=_color_change
            )
            dlg = ft.AlertDialog(
                ft.Column([color_picker], tight=True, expand=False),
                title=f"Set background color for {self.title}",
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                    ft.TextButton("Set", on_click=_set_confirmed, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)),
                ]
            )
            self.p.show_dialog(dlg)

        # If its not a color, its an image
        else:
            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:

                file_path = files[0].path
                try:
                    import base64

                    with open(file_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        # Save to our data
                        self.data['background'] = f"{encoded_string}"
                        self.data['bg_type'] = "image"
                        await self.save_dict()
                        await asyncio.sleep(0.1)

                        self.widget.story.blocker.visible = True
                        self.widget.story.blocker.update()
                        await asyncio.sleep(0)

                        # Works ways faster than reloading the widgetfor some reason
                        self.widget.story.workspace.reload_workspace()

                        self.widget.story.blocker.visible = False
                        self.widget.story.blocker.update()

                except Exception as _:
                    pass

    async def _set_layer_blur(self, e):
        #blur_strength = e.control.value
        name = e.control.data



        #self.data['bg_blur'] = blur_strength
        #await self.save_dict()

        # TODO: Update the blur of first shape on bg layer
        #self.widget.layer_stack.controls[0].blur = self.data.get('bg_blur', 0)   # Set the blur of our background layer, which is always at index 0
        #self.widget.layer_stack.controls[0].update()

        #self.widget.story.blocker.visible = True
        #self.widget.story.blocker.update()
        #await asyncio.sleep(0)

        #self.widget.story.workspace.reload_workspace()
        #self.widget.story.blocker.visible = False
        #self.widget.story.blocker.update()

    async def _clear_background(self, e):
        
        self.widget.story.blocker.visible = True
        self.widget.story.blocker.update()
        await asyncio.sleep(0)
        await self.widget.story.close_menu()
        self.data['background'] = None
        self.data['bg_type'] = None
        await self.save_dict()

        

        #self.widget.reload_widget()
        self.widget.story.workspace.reload_workspace()
        self.widget.story.blocker.visible = False
        self.widget.story.blocker.update()

    # Called when we reorder our layers list and updates to new positions
    async def _reorder_layers(self, e: ft.OnReorderEvent):
        new_index = e.new_index
        old_index = e.old_index
        if new_index == old_index:
            return
        if new_index == 0 or old_index == 0:   # Don't allow reordering the background layer
            self.reload_mini_widget()   # Just reload to reset the order in the UI
            self.p.show_dialog(SnackBar("Background layer cannot be reordered"))
            return
        layers = self.data.get('Layers', [])
        if new_index < 0 or old_index < 0 or new_index >= len(layers) or old_index >= len(layers):
            print("Invalid layer reorder indices: ", new_index, old_index)
            return
        layers.insert(new_index, layers.pop(old_index))
        self.data['Layers'] = layers
        
        await self.save_dict()

        self.widget.story.blocker.visible = True
        self.widget.story.blocker.update()
        await asyncio.sleep(0)

        #self.widget.reload_widget()
        self.widget.story.workspace.reload_workspace()
        await asyncio.sleep(0.1)
        self.widget.story.blocker.visible = False
        self.widget.story.blocker.update()

    # Called when deleting a layer
    async def _delete_layer_clicked(self, e):

        async def _delete_layer_confirmed(e=None):
            for layer in self.data.get('Layers', []):
                if layer.get('name') == name:
                    self.data['Layers'].remove(layer)
                    break
            await self.save_dict()
            

            self.widget.story.blocker.visible = True
            self.widget.story.blocker.update()
            await asyncio.sleep(0)
            self.p.pop_dialog()
            await asyncio.sleep(0.1)

            #self.widget.reload_widget()
            self.widget.story.workspace.reload_workspace()
            self.widget.story.blocker.visible = False
            self.widget.story.blocker.update()

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

        for idx, layer in enumerate(self.data.get('Layers', [])):
            if layer.get('name') == name:

                # Can't hide active layer, show snackbar
                if idx == self.data.get('Active Layer', 0) and layer.get('visible', True):
                    self.p.show_dialog(SnackBar("Cannot hide active layer"))
                    return
                layer['visible'] = not layer.get('visible', True)
                await self.save_dict()

                # Update that canvases visibility and edit our icon to match
                for ctrl in self.widget.layer_stack.controls:
                    if isinstance(ctrl, ft.Container) and ctrl.data == name:
                        ctrl.visible = layer['visible']
                        e.control.icon = ft.Icons.VISIBILITY if layer['visible'] else ft.Icons.VISIBILITY_OFF   
                        e.control.update()
                        ctrl.update()

                return
        

    # Sets a new active layer based on the layer we click on in the layers list
    async def _set_active_layer(self, e):
        for idx, layer in enumerate(self.data.get('Layers', [])):
            if layer.get('name') == e.control.data:

                # Error catch for setting an invisible layer as active
                if layer.get('visible', True) == False:
                    self.p.show_dialog(SnackBar("Cannot make a hidden layer the active layer"))
                    return

                self.data['Active Layer'] = idx
                layer['visible'] = True   # Make sure layer is visible when we set it to active
                await self.save_dict()

                reorderable_list = e.control.parent.parent    # Grab expansion tile

                for ctrl in reorderable_list.controls:   # Loop through layers and update bg color to show active layer
                    if isinstance(ctrl, ft.ReorderableDragHandle):
                        if ctrl.data == e.control.data:
                            ctrl.content.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH
                            ctrl.content.leading.icon = ft.Icons.VISIBILITY
                        else:
                            ctrl.content.bgcolor = None
                        ctrl.content.update()  # Update each layer control to reflect bg color change

                for ctrl in self.widget.layer_stack.controls:
                    if isinstance(ctrl, ft.Container) and ctrl.data == e.control.data:
                        ctrl.ignore_interactions = False   # Active layer can interact
                        ctrl.update()
                    elif isinstance(ctrl, ft.Container):
                        if ctrl.ignore_interactions == False:
                            ctrl.ignore_interactions = True    # Non active layers can't interact
                            ctrl.update()
                return
        
    # Creates a new layer
    async def _create_new_layer_clicked(self, e):

        async def _check_name_unique(e):
            name = new_layer_tf.value
            for layer in self.data.get('Layers', []):
                if layer.get('name') == name:
                    new_layer_tf.error = "Layer name must be unique"
                    new_layer_tf.update()
                    create_button.disabled = True
                    create_button.update()
                    return False
                
            new_layer_tf.error = None
            new_layer_tf.update()
            create_button.disabled = False
            create_button.update()
            return True

        async def _create_layer_confirmed(e=None):
            self.widget.story.blocker.visible = True
            self.widget.story.blocker.update()
            await asyncio.sleep(0.1)

            name = new_layer_tf.value or f"Layer {len(self.data.get('Layers', []))+1}"
            self.data['Layers'].append({'name': name, 'visible': True, 'capture': ""})
            await self.save_dict()
            self.p.pop_dialog()
            await asyncio.sleep(0.1)

            #self.widget.reload_widget()
            self.widget.story.workspace.reload_workspace()
            self.widget.story.blocker.visible = False
            self.widget.story.blocker.update()

        new_layer_tf = ft.TextField(capitalization=ft.TextCapitalization.WORDS, on_submit=_create_layer_confirmed, on_change=_check_name_unique, autofocus=True)
        create_button = ft.TextButton("Create", on_click=_create_layer_confirmed, style=ft.ButtonStyle(mouse_cursor="click"), disabled=True)
        dlg = ft.AlertDialog(
            title="Layer Name",
            content=new_layer_tf,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                create_button
            ]
        )
        self.p.show_dialog(dlg)

    async def _rename_layer_clicked(self, e):

        async def _check_name_unique(e):
            name = rename_layer_tf.value
            if name == old_name:
                rename_layer_tf.error = None
                rename_layer_tf.update()
                rename_button.disabled = False
                rename_button.update()
                return True
            for layer in self.data.get('Layers', []):
                if layer.get('name') == name:
                    rename_layer_tf.error = "Layer name must be unique"
                    rename_layer_tf.update()
                    rename_button.disabled = True
                    rename_button.update()
                    return False
                
            rename_layer_tf.error = None
            rename_layer_tf.update()
            rename_button.disabled = False
            rename_button.update()
            return True
        
        async def _rename_layer_confirmed(e=None):
            self.widget.story.blocker.visible = True
            self.widget.story.blocker.update()
            await asyncio.sleep(0.1)

            new_name = rename_layer_tf.value or f"Layer {len(self.data.get('Layers', []))+1}"
            for layer in self.data.get('Layers', []):
                if layer.get('name') == old_name:
                    layer['name'] = new_name
                    break
            await self.save_dict()
            self.p.pop_dialog()
            await asyncio.sleep(0.1)

            #self.widget.reload_widget()
            self.widget.story.workspace.reload_workspace()
            await asyncio.sleep(0.1)
            #self.widget.story.blocker.visible = False
            #self.widget.story.blocker.update()

        old_name = e.control.data

        rename_layer_tf = ft.TextField(old_name, capitalization=ft.TextCapitalization.WORDS, on_submit=_rename_layer_confirmed, on_change=_check_name_unique, autofocus=True)
        rename_button = ft.TextButton("Rename", on_click=_rename_layer_confirmed, style=ft.ButtonStyle(mouse_cursor="click"), disabled=True)

        dlg = ft.AlertDialog(
            title="Layer Name",
            content=rename_layer_tf,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                rename_button
            ]
        )
        self.p.show_dialog(dlg)

    # Called when undoing a stroke on the canvas
    async def undo(self, e=None):
        if len(self.widget.state.undo_list) == 0:
            return
        
        # Hitting undo needs to grab current state of canvas and add that to redo list
        
        # Grab the task we're going to carry out and its name and capture
        task = self.widget.state.undo_list.pop()    
        layer_name = task.get('layer_name', None)
        capture = task.get('capture', None)


        # Set data back to old capture state
        for layer in self.data.get('Layers', []):
            if layer.get('name', None) == layer_name:
                previous_capture = layer.get('capture', None)   # Grab current capture of the layer and add it to the redo list
                self.widget.state.redo_list.append({'layer_name': layer_name, 'capture': previous_capture}) 
                layer['capture'] = capture     
                await self.save_dict()
                break

        # Set canvas back to old capture state
        for ctrl in self.widget.layer_stack.controls:
            if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas) and ctrl.data == layer_name:
                ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                ctrl.content.shapes.append(cv.Image(capture, 0, 0, self.widget.canvas_width, self.widget.canvas_height))   # Re-add most reccent capture
                try:
                    self.widget.story.blocker.visible = True
                    self.widget.story.blocker.update()
                    await asyncio.sleep(0)
                    ctrl.content.update()
                    self.widget.story.blocker.visible = False
                    self.widget.story.blocker.update()
                except Exception as _:
                    if self.widget.story.blocker.visible:
                        self.widget.story.blocker.visible = False
                        self.widget.story.blocker.update()
                break

    # Called when redoing a stroke on the canvas after a previous undo
    async def redo(self, e=None):
        if len(self.widget.state.redo_list) == 0:
            return
           
        # Most recent task we want to redo
        task = self.widget.state.redo_list.pop()    
        layer_name = task.get('layer_name', None)
        capture = task.get('capture', None)

        # Set data back to old capture state
        for layer in self.data.get('Layers', []):
            if layer.get('name', None) == layer_name:
                previous_capture = layer.get('capture', None)   # Grab current capture of the layer and add it to undo list
                self.widget.state.undo_list.append({'layer_name': layer_name, 'capture': previous_capture})
                layer['capture'] = capture     # Set the capture of the layer to the one from our undo task
                await self.save_dict()
                break

        for ctrl in self.widget.layer_stack.controls:
            if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas) and ctrl.data == layer_name:
                ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                ctrl.content.shapes.append(cv.Image(capture, 0, 0, self.widget.canvas_width, self.widget.canvas_height))   # Re-add most reccent capture
                try:
                    self.widget.story.blocker.visible = True
                    self.widget.story.blocker.update()
                    await asyncio.sleep(0)
                    ctrl.content.update()
                    self.widget.story.blocker.visible = False
                    self.widget.story.blocker.update()
                except Exception as _:
                    if self.widget.story.blocker.visible:
                        self.widget.story.blocker.visible = False
                        self.widget.story.blocker.update()
                break

        
        
    
    # Called when reloading our mini widget UI
    def reload_mini_widget(self):
       
        # Manage saving so not at the end of every stroke.
        # Add undo/redo based on capture list
        # Remove old items from the undo/redo list after like 30 or so 
        # Height ad width just for exporting
        # Set dark and light transparent bg images for all canvases

        title_control = ft.Row([
            ft.Icon(ft.Icons.BRUSH, self.widget.data.get('color', None)),
            
            ft.GestureDetector(
                ft.Text(f"\t\t{self.data['title']}\t\t", weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.FADE),
                on_double_tap=self.widget._rename_clicked,
                on_tap=self.widget._rename_clicked,
                on_secondary_tap=lambda e: self.widget.story.open_menu(self.widget._get_menu_options()),
                mouse_cursor="click", hover_interval=500,
                tooltip=f"Rename {self.title}"
            ),
            ft.IconButton(
                ft.Icons.UNDO, self.widget.data.get('color', None), tooltip="Undo", mouse_cursor=ft.MouseCursor.CLICK, 
                on_click=self.undo, #disabled=True if len(self.widget.state.undo_list) == 0 else False
            ),
            ft.IconButton(
                ft.Icons.REDO_OUTLINED, self.widget.data.get('color', None), tooltip="Redo", mouse_cursor=ft.MouseCursor.CLICK, 
                on_click=self.redo, #disabled=True if len(self.widget.state.redo_list) == 0 else False
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}",
                mouse_cursor=ft.MouseCursor.CLICK,
                on_click=self.hide_mini_widget,
            ),
        ], spacing=0)

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


        # Set and clear bg buttons
        
        edit_bg_options = ft.MenuBar(
            [
                ft.SubmenuButton(
                    "Set Background",
                    [
                        ft.TextButton(     # Set a color
                            "Color\t\t", ft.Icons.COLOR_LENS_OUTLINED, 
                            self.data.get('background', "primary") if self.data.get('bg_type') == "color" else ft.Colors.PRIMARY,
                            tooltip="Set background as a color", data="color",
                            on_click=self._set_background, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ON_SURFACE)
                        ),
                        ft.TextButton(      # Set an image
                            "Image", ft.Icons.IMAGE_OUTLINED, 
                            self.data.get('background', "primary") if self.data.get('bg_type') == "color" else ft.Colors.PRIMARY,
                            tooltip="Set background as an image", data="image",
                            on_click=self._set_background, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ON_SURFACE)
                        ),
                        ft.TextButton(  # Clear background
                            "Clear\t\t", ft.Icons.HIDE_IMAGE_OUTLINED,
                            self.data.get('background', "primary") if self.data.get('bg_type') == "color" else ft.Colors.PRIMARY,
                            tooltip="Clear/Reset background",
                            on_click=self._clear_background, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ON_SURFACE)
                        ),
                    ],
                    trailing=ft.Icon(
                        ft.Icons.INFO_OUTLINE, ft.Colors.ON_SURFACE, scale=.6,
                        tooltip="Setting/Clearing your background will NOT affect any drawing already done on the background layer."
                    ),
                    style=ft.ButtonStyle(mouse_cursor="click"),
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0))
                )
            ], style=ft.MenuStyle(mouse_cursor="click", padding=ft.Padding.all(0))
        )

        export_button = ft.TextButton(
            "Export", ft.Icons.FILE_DOWNLOAD_OUTLINED, tooltip="Export canvas as image",
            on_click=self.widget.export_canvas_clicked, style=ft.ButtonStyle(mouse_cursor="click")
        )

           


        # Button for creating new layers
        create_new_layer_button = ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, mouse_cursor="click",
            tooltip="Add new layer",
            on_click=self._create_new_layer_clicked
        )

        # Create our expansion tile to hold our layers
        layer_expansion_tile = ft.ExpansionTile(
            "Layers",
            [
                ft.ReorderableListView(on_reorder=self._reorder_layers, scroll="auto", expand=True, controls=[], show_default_drag_handles=False),   # This will hold our layers and allow us to reorder them
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
                    trailing=ft.PopupMenuButton(     # Delete button
                        data=name, menu_padding=ft.Padding.all(0),
                        style=ft.ButtonStyle(mouse_cursor="click"),
                        tooltip=f"{name} options",
                        items=[
                            ft.PopupMenuItem(
                                ft.Row([ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED), ft.Text("Rename")]), data=name,
                                mouse_cursor=ft.MouseCursor.CLICK, on_click=self._rename_layer_clicked, 
                            ),
                            #ft.PopupMenuItem(
                                #ft.Row([ft.Icon(ft.Icons.BLUR_ON_OUTLINED), ft.Text("Blur Strength")]), data=name, 
                                #mouse_cursor=ft.MouseCursor.CLICK, on_click=self._set_layer_blur,
                            #),
                            ft.PopupMenuItem(
                                ft.Row([ft.Icon(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR), ft.Text("Delete")]), data=name, 
                                on_click=self._delete_layer_clicked, mouse_cursor=ft.MouseCursor.CLICK, 
                            )
                        ]
                    ) if idx != 0 else None,    # Don't allow deleting the first layer
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH if self.data.get('Active Layer', 0) == idx else None,  # Lighter bg for selected layer
                    on_click=self._set_active_layer, data=name,
                    #content_padding=ft.Padding.only(right=30),
                ), data=name
            )
            layer_expansion_tile.controls[0].controls.append(layer_tile)

        
        
        content = ft.Column([
            ft.Container(height=1),  # Spacing 
            description_tf,

            ft.Row([edit_bg_options, export_button], ft.MainAxisAlignment.SPACE_EVENLY, wrap=True),

            

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



        