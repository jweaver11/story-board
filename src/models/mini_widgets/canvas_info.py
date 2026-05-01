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
from styles.text_field import TextField
import base64




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

                # Undo and redo list
                'undo_list': [],    
                'redo_list': [],
                # Each undo/redo item {'layer_name': "", 'capture': ""} 

                # Background can be an image, color, or left empty for transparent. 
                #'background': None,             # We display it using a container, but manually create it when exporting
                #'bg_type': None,                # "color", "image", or None so we know how to display it

                # Canvas info
                'Description': str,
                "width": None,              # Resolution size used for exporting
                "height": None,
                "aspect_ratio": None,       # Actually used for displaying the canvas, and we scale up when exporting
                'Is Locked': False,         # Lock state tracking. When locked, no changes can be made (no drawing)

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

        self.visible = True     # Always set to visible, the parent will choose to add it or not

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
        

    async def _set_layer_content(self, e):

        await self.widget.story.close_menu()

        layer_name, type = e.control.data

        # Grab the layer this is. Set its capture as color or image

        # Set a color as the background
        if type == "color":

            async def _color_change(e):     # Set the color to the picked one
                color_picker.color = e.data

            async def _set_color_confirmed(e=None):

                for layer in self.data.get('Layers', []):
                    if layer.get('name') == layer_name:
                        for ctrl in self.widget.layer_stack.controls:
                            if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas) and ctrl.data == layer_name:
                                ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                                ctrl.content.shapes.append(cv.Color(color_picker.color))   # Re-add empty images so it can capture
                                ctrl.content.update()
                                await self.widget.save_canvas(canvas=ctrl.content)  
                                break
                        break

                self.p.pop_dialog()
                

            color_picker = ColorPicker(
                self.data.get('background', ft.Colors.PRIMARY) if self.data.get('bg_type') == "color" else ft.Colors.PRIMARY,
                on_color_change=_color_change
            )
            dlg = ft.AlertDialog(
                ft.Column([color_picker], tight=True, expand=False),
                title=f"Set {layer_name} to a Color",
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                    ft.TextButton("Set", on_click=_set_color_confirmed, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)),
                ]
            )
            self.p.show_dialog(dlg)

        # If its not a color, its an image
        else:
            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
            if files:

                file_path = files[0].path
                try:
                    

                    with open(file_path, "rb") as image_file:
                        print("Opened file")
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        for layer in self.data.get('Layers', []):
                            if layer.get('name') == layer_name:
                                print("Found layer: ", layer_name)
                                for ctrl in self.widget.layer_stack.controls:
                                    if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas) and ctrl.data == layer_name:
                                        print("Set image")
                                        ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                                        ctrl.content.shapes.append(cv.Image(f"{encoded_string}", 0, 0, self.widget.canvas_width, self.widget.canvas_height))   # Re-add empty images so it can capture
                                        ctrl.content.update()
                                        await self.widget.save_canvas(canvas=ctrl.content)
                                        break
                                break
                    self.p.pop_dialog()

                except Exception as _:
                    pass   

    async def _set_layer_blur(self, e):
        await self.widget.story.close_menu()

        layer_name = e.control.data
        #capture = None
        for layer in self.data.get('Layers', []):
            if layer.get('name') == layer_name:
                if layer.get('capture', "") == "":
                    
                    self.p.show_dialog(SnackBar("Layer must have existing content to set blur"))
                    return
                capture = layer.get('capture', "")
                break

        if capture is None:
            self.p.show_dialog(SnackBar("Error finding layer capture for blur"))
            return
        
        # Updates the visual canvas with new blur amount
        async def _blur_amount_changed(e):
            blur_amount = e.control.value
            active_preview_image.paint.blur_image = blur_amount
            active_preview_image.update()

        # Apply that level of blur to the layer
        async def _apply_blur(e=None):

            for layer in self.data.get('Layers', []):
                if layer.get('name') == layer_name:
                    for ctrl in self.widget.layer_stack.controls:
                        if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, cv.Canvas) and ctrl.data == layer_name:
                            ctrl.content.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
                            ctrl.content.shapes.append(cv.Image(capture, 0, 0, self.widget.canvas_width, self.widget.canvas_height, paint=ft.Paint(blur_image=blur_strength_slider.value)))
                            ctrl.content.update()
                            await self.widget.save_canvas(canvas=ctrl.content)  
                            break
                    break

            self.p.pop_dialog()
        
        blur_strength_slider = ft.Slider(1, "{value}", min=0, max=50, on_change=_blur_amount_changed)
        
        
        preview_canvas = ft.Container(
            cv.Canvas(
                #shapes=[preview_image], 
                shapes=[],
                
                expand=True,
                width=self.widget.canvas_width / 2, height=self.widget.canvas_height / 2
            ),
            image=ft.DecorationImage("dark_mode_transparent_background.jpg", fit=ft.BoxFit.FILL) 
        )

        active_preview_image = None

        # Add the entire canvas to the preview, but mark the active layer we will change blur of
        for layer in self.data.get('Layers', []):
            if layer.get('name') == layer_name:
                active_preview_image = cv.Image(layer.get('capture', ""), 0, 0, self.widget.canvas_width / 2, self.widget.canvas_height / 2, paint=ft.Paint(blur_image=1))
                preview_canvas.content.shapes.append(active_preview_image)
                continue
            preview_canvas.content.shapes.append(cv.Image(layer.get('capture', ""), 0, 0, self.widget.canvas_width / 2, self.widget.canvas_height / 2))
               
        if active_preview_image is None:
            self.p.show_dialog(SnackBar("Error finding layer capture for blur"))
            return

        dlg = ft.AlertDialog(
            ft.Column([
                preview_canvas, 
                blur_strength_slider,
                ft.Text("Adjust Blur Strength", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            title=f"Set Blur for {layer_name}",
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                ft.TextButton("Apply", on_click=_apply_blur, style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.PRIMARY)),
            ]
        )
        self.p.show_dialog(dlg)     

    # Called when we reorder our layers list and updates to new positions
    async def _reorder_layers(self, e: ft.OnReorderEvent):
        new_index = e.new_index
        old_index = e.old_index
        if new_index == old_index:
            return
        
        layers = self.data.get('Layers', [])
        if new_index < 0 or old_index < 0 or new_index >= len(layers) or old_index >= len(layers):
            self.p.show_dialog(SnackBar(f"Invalid layer reorder indices. New index: {new_index}, -- Old Index: {old_index}"))
            return
        layers.insert(new_index, layers.pop(old_index))
        self.data['Layers'] = layers
        
        await self.save_dict()

        self.widget.story.blocker.visible = True
        self.widget.story.blocker.update()
        await asyncio.sleep(0)

        self.widget.reload_widget()
        self.widget.story.blocker.visible = False
        self.widget.story.blocker.update()

    # Called when deleting a layer
    async def _delete_layer_clicked(self, e):

        
        name = e.control.data 

        if len(self.data.get('Layers', [])) <= 1:
            self.p.show_dialog(SnackBar(f"A canvas must have at least one layer. {name} was NOT deleted"))
            return

        async def _delete_layer_confirmed(e=None):
            for layer in self.data.get('Layers', []):
                if layer.get('name') == name:
                    self.data['Layers'].remove(layer)
                    self.data['Active Layer'] = -1  
                    break
            
            for task in self.data['undo_list'][:]:   # Remove any undo tasks related to this layer
                if task.get('layer_name') == name:
                    self.data['undo_list'].remove(task)
            for task in self.data['redo_list'][:]:   # Remove any redo tasks related to this layer
                if task.get('layer_name') == name:
                    self.data['redo_list'].remove(task)

            await self.save_dict()

            self.widget.story.blocker.visible = True
            self.widget.story.blocker.update()
            await asyncio.sleep(0)
            self.p.pop_dialog()

            self.widget.reload_widget()
            self.widget.story.blocker.visible = False
            self.widget.story.blocker.update()

          

        dlg = ft.AlertDialog(
            title=f"Delete {name}? This action cannot be undone.",
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
                    
                    self.data['Active Layer'] = -1 
                            

                layer['visible'] = not layer.get('visible', True)
                
                await self.save_dict()

                # Update that canvases visibility and edit our icon to match
                for ctrl in self.widget.layer_stack.controls:
                    if isinstance(ctrl, ft.Container) and ctrl.data == name:
                        ctrl.visible = layer['visible']
                        ctrl.update()
                   
                self.reload_mini_widget()   # Just reload to reset the order in the UI
                return
        
        

    # Sets a new active layer based on the layer we click on in the layers list
    async def _set_active_layer(self, e):
        

        # Make sure we paint any open tool on the canvas before switching, or it'll be painted on the new layer instead
        if self.widget.manipulating_shape:
            self.widget.manipulating_shape = False  
            await self.widget.paint_tool_on_canvas()

        layer_name = e.control.data

        for idx, layer in enumerate(self.data.get('Layers', [])):
            if layer.get('name') == layer_name:

                # Error catch for setting an invisible layer as active
                if layer.get('visible', True) == False:
                    for ctrl in self.widget.layer_stack.controls:
                        if isinstance(ctrl, ft.Container) and ctrl.data == layer_name:
                            ctrl.visible = True
                            ctrl.update()
                    

                self.data['Active Layer'] = idx
                layer['visible'] = True   # Make sure layer is visible when we set it to active
                await self.save_dict()

                reorderable_list = e.control.parent.parent    # Grab expansion tile

                for ctrl in reorderable_list.controls:   # Loop through layers and update bg color to show active layer
                    if isinstance(ctrl, ft.ReorderableDragHandle):
                        if ctrl.data == layer_name:
                            ctrl.content.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
                            ctrl.content.leading.icon = ft.Icons.VISIBILITY
                        else:
                            ctrl.content.bgcolor = None
                        ctrl.content.update()  # Update each layer control to reflect bg color change

                for ctrl in self.widget.layer_stack.controls:
                    if isinstance(ctrl, ft.Container) and ctrl.data == layer_name:
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
            await asyncio.sleep(0)

            name = new_layer_tf.value or f"Layer {len(self.data.get('Layers', []))+1}"
            self.data['Layers'].append({'name': name, 'visible': True, 'capture': ""})
            await self.save_dict()
            self.p.pop_dialog()

            self.widget.reload_widget()
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
            await asyncio.sleep(0)

            new_name = rename_layer_tf.value or f"Layer {len(self.data.get('Layers', []))+1}"
            for layer in self.data.get('Layers', []):
                if layer.get('name') == old_name:
                    layer['name'] = new_name
                    break

            for task in self.data['undo_list']:   # Update any undo tasks related to this layer
                if task.get('layer_name') == old_name:
                    task['layer_name'] = new_name
            for task in self.data['redo_list']:   # Update any redo tasks related to this layer
                if task.get('layer_name') == old_name:
                    task['layer_name'] = new_name
            await self.save_dict()
            self.p.pop_dialog()

            self.widget.reload_widget()
            if self.widget.story.blocker.visible:
                self.widget.story.blocker.visible = False
                self.widget.story.blocker.update()
            

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

        # If there's nothing to undo, return early
        #if len(self.widget.state.undo_list) == 0:
            #return
        if len(self.data['undo_list']) == 0:
            return
                
        # Grab the task we're going to carry out and its name and capture
        #task = self.widget.state.undo_list.pop()    
        task = self.data['undo_list'].pop()
        layer_name = task.get('layer_name', None)
        capture = task.get('capture', None)

        # Set data back to old capture state
        for layer in self.data.get('Layers', []):
            if layer.get('name', None) == layer_name:
                previous_capture = layer.get('capture', None)   # Grab current capture of the layer and add it to the redo list
                #self.widget.state.redo_list.append({'layer_name': layer_name, 'capture': previous_capture}) 
                self.data['redo_list'].append({'layer_name': layer_name, 'capture': previous_capture})
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
        #if len(self.widget.state.redo_list) == 0:
            #return
        if len(self.data['redo_list']) == 0:
            return
           
        # Most recent task we want to redo
        #task = self.widget.state.redo_list.pop()   
        task = self.data['redo_list'].pop() 
        layer_name = task.get('layer_name', None)
        capture = task.get('capture', None)

        # Set data back to old capture state
        for layer in self.data.get('Layers', []):
            if layer.get('name', None) == layer_name:
                previous_capture = layer.get('capture', None)   # Grab current capture of the layer and add it to undo list
                #self.widget.state.undo_list.append({'layer_name': layer_name, 'capture': previous_capture})
                self.data['undo_list'].append({'layer_name': layer_name, 'capture': previous_capture})
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
       
        

        title_control = ft.Row([
            #ft.Icon(ft.Icons.BRUSH, self.widget.data.get('color', None)),
     
            ft.Text(
                f"\t{self.data['title']}", theme_style=ft.TextThemeStyle.TITLE_LARGE, 
                weight=ft.FontWeight.BOLD, color=self.widget.data.get('color', None),
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
                on_click=self.widget._toggle_show_info,
            ),
        ], spacing=0)

        # Textfield of our canvas description
        description_tf = TextField(
            expand=True, label="Description", value=self.data.get('Description', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_blur=lambda e: self.change_data(**{'Description': e.control.value}),   # When we click out of the text field, we save our changes
            label_style=ft.TextStyle(color=self.widget.data.get('color', None)),
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
                ft.ReorderableListView(on_reorder=self._reorder_layers, scroll="auto", reverse=True, expand=True, controls=[], show_default_drag_handles=False),   # This will hold our layers and allow us to reorder them
                create_new_layer_button 
            ],
            leading=ft.Icons.LAYERS_OUTLINED,
            #tile_padding=ft.Padding.symmetric(horizontal=6),
            expanded=self.data.get('layers_expansion_tile_expanded', True),
            on_change=lambda e: self.change_data(**{'layers_expansion_tile_expanded': e.control.expanded})
        )

        # Add each layer to the expansion tile
        for idx, layer in enumerate(self.data.get('Layers', [])):
            name = layer.get('name', f"Layer {idx+1}")
            visible = layer.get('visible', True)
            layer_tile = ft.ReorderableDragHandle(
                ft.ListTile(
                    ft.Text(name, expand=True), #expand=True,
                    leading=ft.IconButton(   # Toggle visibility button
                        ft.Icons.VISIBILITY if visible else ft.Icons.VISIBILITY_OFF, mouse_cursor="click",
                        on_click=self._toggle_selected_layer_visibility, data=name
                    ),  
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST if self.data.get('Active Layer', 0) == idx else None,  # Lighter bg for selected layer
                    on_click=self._set_active_layer, data=name,
                    trailing=ft.PopupMenuButton(
                        data=name, menu_padding=ft.Padding.all(0),
                        style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                        items=[
                            ft.PopupMenuItem(
                                "Set Color", ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.widget.data.get('color', ft.Colors.PRIMARY)),
                                on_click=self._set_layer_content, 
                                tooltip="Set this layer to a solid color. This will overwrite any drawings on the layer currently." if visible else
                                "Layer must be visible to set color",
                                data=(name, "color"),
                                mouse_cursor="click",
                                disabled=not visible 
                            ),
                            
                            ft.PopupMenuItem(
                                "Set Image", ft.Icon(ft.Icons.IMAGE_OUTLINED, self.widget.data.get('color', ft.Colors.PRIMARY)), 
                                on_click=self._set_layer_content, 
                                tooltip="Upload an image for this layer. This will overwrite any drawings on the layer currently." if visible else
                                "Layer must be visible to set image", 
                                data=(name, "image"),
                                mouse_cursor="click",
                                disabled=not visible
                            ),
                            ft.PopupMenuItem(
                                "Set Blur", ft.Icon(ft.Icons.BLUR_ON_OUTLINED, self.widget.data.get('color', ft.Colors.PRIMARY)), 
                                on_click=self._set_layer_blur, 
                                tooltip="Set the blur only for existing content on this layer. Useful for backgrounds and effects. " \
                                "Will NOT effect any future content drawn on this layer" if visible else
                                "Layer must be visible to set image", 
                                data=name,
                                mouse_cursor="click",
                                disabled=not visible
                            ),
                            
                            ft.PopupMenuItem(
                                "Rename", ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.widget.data.get('color', ft.Colors.PRIMARY)),
                                data=name, on_click=self._rename_layer_clicked,
                                mouse_cursor="click",
                            ),
                            
                            ft.PopupMenuItem(
                                "Delete", ft.Icon(ft.Icons.DELETE_OUTLINED, ft.Colors.ERROR),  
                                tooltip="Delete this layer. This action cannot be undone.",
                                data=name, on_click=self._delete_layer_clicked,
                                mouse_cursor="click",
                            )
                        ],
                        
                    ),
                ), 
                data=name
            )
            layer_expansion_tile.controls[0].controls.append(layer_tile)

        notes_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Notes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.widget.data.get('color', None), selectable=True),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, self.widget.data.get('color', "primary"), tooltip="Add Note",
                on_click=self._new_note_clicked,
                mouse_cursor="click"
            )
        ], spacing=0)

        notes_column = self._build_notes_column()
        
        content = ft.Column([
            ft.Container(height=1),  # Spacing 
            description_tf,

            export_button,

            layer_expansion_tile,

            notes_label,
            ft.Container(notes_column, margin=ft.Margin.symmetric(horizontal=20)),
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



        