'''
Class for showing all our characters laidd out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from models.app import app
import flet.canvas as cv
from models.dataclasses.canvas_state import State
import math
from styles.snack_bar import SnackBar
import asyncio
import base64
from io import BytesIO
from PIL import Image
from styles.text_fields import TextField


class CanvasBoard(Widget):
    # Constructor
    def __init__(self, name: str, directory_path: str, story: Story, data: dict={}, is_new: bool = False):

        # Parent class constructor
        super().__init__(
            title = name,  
            directory_path = directory_path, 
            story = story,   
            data = data,  
            is_new = is_new
        )

        # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                'tag': "canvas_board",
                'color': app.settings.data.get('widget_defaults', {}).get('canvas_board', {}).get('color'),

                # Our row data 
                'rows': [
                    {
                        'canvas_id': "",    # ID of the canvas we're attached to, if we're attached to one
                        'preview_capture': "",    # Base64 string of the preview capture if not attached to canvas
                        'sketch_capture': "",    # Base64 string of the sketch capture
                        'description': "",    # Description of the sketch
                        'height': 300,      # Height of the canvas
                        'width': 300,       # Width of the canvas
                        'dirty': False,      # State tracking - Whether this row's sketch has unsaved changes
                    }
                ],
            },
        )



        self.state: State = State()     # State model from tracking our drawing state
        self.active_path: cv.Path
        

    


    # Called when we click the canvas and don't initiate a drag
    async def add_shape(self, e: ft.TapEvent):
        ''' Adds a point to the canvas if we just clicked and didn't initiate a drag '''

        # Set our paint settings in case we need to change them
        paint_settings = app.settings.data.get('paint_settings', {}).copy()

        # Check if we're in tool mode, and what tool we're using
        if app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") != "draw":

            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            match tool_name:

                # Erase tool - make sure our paint settings don't break the drawing
                case "erase":
                    paint_settings['blend_mode'] = "clear"
                    paint_settings['blur_image'] = 0
                    paint_settings['style'] = "stroke"
        

        canvas: cv.Canvas = e.control.parent

        # Create the point using our paint settings and point mode
        point = cv.Points(
            points=[(e.local_position.x, e.local_position.y)],
            paint=ft.Paint(**paint_settings),
        )
        
        # Add point to the canvas and our state data
        canvas.shapes.append(point)
            
        # Need to save, as this function stands alone and no others will run after it
        await self.save_canvas(e)
        
    # Called when we start drawing on the canvas
    async def start_new_stroke(self, e: ft.DragStartEvent):
        ''' Set our initial starting x and y coordinates for the element we're drawing '''

        # Grab the canvas and paint settings
        canvas: cv.Canvas = e.control.parent
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        #paint_settings.style = ft.PaintingStyle.STROKE

        # Update state x and y coordinates
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

        # Clear and set our current path and state to match it
        self.active_path = cv.Path(elements=[], paint=ft.Paint(**paint_settings))

        # Check if we're in tool mode, and what tool we're using
        if app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") != "draw":

            tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
            match tool_name:

                # Erase tool - make sure our paint settings don't break the drawing
                case "erase":
                    paint_settings['blend_mode'] = "clear"
                    paint_settings['blur_image'] = 0
                    paint_settings['style'] = "stroke"
                    self.active_path.paint = ft.Paint(**paint_settings) # Make the active path match the paint

        # Move to our starting position for this element
        move_to_element = cv.Path.MoveTo(e.local_position.x, e.local_position.y)
        self.active_path.elements.append(move_to_element)

        # Add the path to the canvas so we can see it
        canvas.shapes.append(self.active_path)
        canvas.update()


        
    # Called when actively drawing on the canvas
    async def update_stroke(self, e: ft.DragUpdateEvent):
        ''' Creates our line to add to the canvas as we draw, and saves that paths data to self.state '''
        path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
        path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
        self.active_path.elements.append(path_element)
        self.active_path.update()

        self.state.x = e.local_position.x
        self.state.y = e.local_position.y

    # Called when we release the mouse to stop drawing a line
    async def save_canvas(self, e: ft.DragEndEvent):
        """ Saves our paths to our canvas data for storage """
        
        #print(e.control.parent.parent.parent.parent)
        row_idx = e.control.parent.parent.parent.parent.data
        cell_idx = 0
        canvas: cv.Canvas = e.control.parent

        # Grab old capture and add it to the undo list
        old_capture = self.data['rows'][row_idx][cell_idx].get('capture', "")
        if old_capture:
            self.data['rows'][row_idx][cell_idx]['undo_list'].append(old_capture)   
            self.data['rows'][row_idx][cell_idx]['redo_list'].clear()

        if len(self.data['rows'][row_idx][cell_idx]['undo_list']) > 30:   # Limit our undo/redo list to 30 items to save memory
            self.data['rows'][row_idx][cell_idx]['undo_list'].pop(0)
        
        try:
            await canvas.capture()
    
            capture = await canvas.get_capture()
            encoded_capture = base64.b64encode(capture).decode('utf-8')      # Requires encoding to save json

            # If capture failed, return
            if not encoded_capture:
                await canvas.clear_capture()
                return

            if encoded_capture:

                # Save the capture
                self.data['rows'][row_idx][cell_idx]['sketch_capture'] = encoded_capture
                self.update_data(**{'rows': self.data['rows']}) 

            # Must clear the capture or weird UI bugs
            await canvas.clear_capture()

            if len(canvas.shapes) > 20:   # Limit our canvas to 30 shapes to save memory, and clear the canvas if we exceed that
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, 300, 300))   # Re-add most reccent capture as the only shape on the canvas after clearing
                canvas.update()

            # Always re-render end of erase strokes, or they will appear broken. TEMPORARY FIX
            elif app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") == "tool" and app.settings.data.get('canvas_settings', {}).get('current_tool_name', "") == "erase":   
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, 300, 300))
                canvas.update()

            # Always re-render end of non-none blend mode strokes, or they will appear broken. TEMPORARY FIX
            elif app.settings.data.get('paint_settings', {}).get('blend_mode', "") is not None:   
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, 300, 300))
                canvas.update()

        except Exception as e:
            print("failed to save canvas", e)



    
    def build(self):
        
        
        super().build()

        # Called when we click to add a new row at the bottom of our rows
        async def create_row(e=None):
            ''' Adds an empty new row to our rows data and reloads the widget '''

            # Create a new row with default values of each cell
            new_row_dict = {
                'canvas_id': "",    # ID of the canvas we're attached to, if we're attached to one
                'preview_capture': "",    # Base64 string of the preview capture
                'sketch_capture': "",    # Base64 string of the sketch capture
                'description': "",    # Description of the sketch
                'height': 300,      # Height of the canvas
                'width': 300,       # Width of the canvas
                'dirty': False,      # State tracking - Whether this row's sketch has unsaved changes
            }
            
            # Add the new row to our rows data
            self.data['rows'].append(new_row_dict)
            self.update_data(**{'rows': self.data['rows']})  # Update our data so it saves the new row

            rows_column.controls.append(
                create_row_ctrl(
                    len(self.data.get('rows', [])) - 1,
                    self.data.get('rows', [])[-1]
                )
            )
            rows_column.update()
            await asyncio.sleep(0.05)   # Wait a moment for the new row to be added before scrolling to it
            await rows_column.scroll_to(-1, duration=600)

        
        

        # Creates a rows row ctrl for the body of our widget
        def create_row_ctrl(row_idx: int, row_data: dict) -> ft.Container: 

            # Update the width of this row sketch in data and in UI
            def update_width(e: ft.Event[ft.TextField]):
                new_width = int(e.control.value)
                row_idx = e.control.parent.parent.parent.parent.data
                # If new width is not withing size range
                if new_width < 200 or new_width > 300:
                    e.control.value = str(row_data.get('width', 300))
                    size_error_text.parent.visible = True
                    size_error_text.value = "*Width must be between 200 and 300 pixels*"
                    e.control.update()
                    size_error_text.parent.update()
                    return

                # Otherwise it is
                size_error_text.parent.visible = False
                self.data['rows'][row_idx]['width'] = new_width
                self.update_data(**{'rows': self.data['rows']})  # Update our data
                preview_image.width = new_width
                sketch_canvas.width = new_width
                row_ctrl.update()

            # Update the height of this row sketch in data and in UI
            def update_height(e: ft.Event[ft.TextField]):
                new_height = int(e.control.value)
                row_idx = e.control.parent.parent.parent.parent.data
                # If new height is not withing size range
                if new_height < 200 or new_height > 300:
                    e.control.value = str(row_data.get('height', 300))
                    size_error_text.parent.visible = True
                    size_error_text.value = "*Height must be between 200 and 300 pixels*"
                    e.control.update()
                    size_error_text.parent.update()
                    return

                # Otherwise it is
                size_error_text.parent.visible = False
                self.data['rows'][row_idx]['height'] = new_height
                self.update_data(**{'rows': self.data['rows']})  # Update our data
                preview_image.height = new_height
                sketch_canvas.height = new_height
                row_ctrl.update()

            # Hides the error text when selecting the checkmark button next to it
            def hide_error_text(e: ft.Event):
                size_error_text.parent.visible = False
                size_error_text.parent.update()

            # Updates a description for this row control in data
            def update_description(e: ft.Event[ft.TextField]):
                # Grab index positions and update data
                row_idx = e.control.parent.parent.parent.data
                self.data['rows'][row_idx]['description'] = e.control.value
                self.update_data(**{'rows': self.data['rows']})  # Update our data

            # Deletes this row from data and removes the row control from the rows_column
            def delete_row(e: ft.Event[ft.IconButton]):
                # Update data
                row_idx = e.control.parent.parent.data
                self.data['rows'].pop(row_idx)
                self.update_data(**{'rows': self.data['rows']})  # Update our data
                # Remove row from UI and update indices
                rows_column.controls.pop(row_idx)
                rows_column.update()
                update_indices() 
            def set_canvas_as_image(e: ft.Event[ft.MenuItemButton]):

                # Set the canvas id when selecting a canvas from the radio group
                def select_canvas(e: ft.Event[ft.RadioGroup]):
                    nonlocal canvas_id
                    canvas_id = e.data

                # Sets the canvas image from the returned canvas snapshot
                def set_canvas_image(e=None):
                    if canvas_id is None:
                        self.page.pop_dialog()
                        return
                    widget = self.story.get_widget_by_id(canvas_id)
                    if widget is None:
                        self.page.show_dialog(SnackBar("Canvas not found. Please try again."))
                        self.page.pop_dialog()
                        return
    
                    snapshot_str = widget.get_snapshot_string(quality="medium")
                    title = widget.data.get('title', 'Untitled')
                    if snapshot_str is None:
                        self.page.show_dialog(SnackBar("Failed to get canvas snapshot. Please try again."))
                        self.page.pop_dialog()
                        return

                    self.data['rows'][row_idx]['canvas_id'] = canvas_id
                    self.data['rows'][row_idx]['preview_capture'] = ""
                    self.update_data(**{'rows': self.data['rows']})  # Update our data
                    
                    preview_image.src = snapshot_str
                    preview_source_selector.content = f"Current Source: {title}"
                    preview_image.update()
                    preview_source_selector.update()
                    
                    self.page.pop_dialog()

                row_idx = e.control.parent.parent.parent.parent.parent.parent.data
                canvas_id: str = None
            
                dlg = ft.AlertDialog(
                    title=ft.Text("Set a Canvas as Image", weight=ft.FontWeight.BOLD),
                    content=ft.RadioGroup(
                        ft.Column([
                            ft.Radio(
                                label=widget.data.get('title', 'Untitled'),
                                value=id, mouse_cursor=ft.MouseCursor.CLICK,
                            ) for id, widget in self.story.widgets.items() if widget.data.get('tag', '') == "canvas"],
                        ),
                        on_change=select_canvas
                    ),
                    actions=[
                        ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                        ft.TextButton("Select", on_click=set_canvas_image, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click")),]
                )
                self.page.show_dialog(dlg)

            # Called when clicking our upload image button 
            async def upload_image(e: ft.Event[ft.MenuItemButton]):
                row_idx = e.control.parent.parent.parent.parent.parent.parent.data
    
                files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "webp"])
                if files:
    
                    file_path = files[0].path
                    try:
                        import base64
    
                        with open(file_path, "rb") as image_file:
                            # Downscale the image for better performance
                            img = Image.open(image_file).convert("RGBA")
                            new_width = max(1, img.width // 2)
                            new_height = max(1, img.height // 2)
                            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            output = BytesIO()
                            img.save(output, format="PNG")
                            encoded_string = base64.b64encode(output.getvalue()).decode('utf-8')
                            # Save to our data
                            self.data['rows'][row_idx]['preview_capture'] = f"data:image/{file_path.split('.')[-1]};base64,{encoded_string}"
                            self.data['rows'][row_idx]['canvas_id'] = ""   # Clear the canvas_id if we uploaded an image
                            self.update_data(**{'rows': self.data['rows']})  # Update our data
    
                        preview_image.src = encoded_string
                        preview_source_selector.content = "Set Preview Source"
                        preview_image.update()
                        preview_source_selector.update()
    
                    except Exception:
                        pass

            # Clears the canvas id and preview cap to set image to placeholder
            def clear_image(e: ft.Event[ft.MenuItemButton]):
                row_idx = e.control.parent.parent.parent.parent.parent.parent.data
                self.data['rows'][row_idx]['preview_capture'] = ""
                self.data['rows'][row_idx]['canvas_id'] = ""   # Clear the canvas_id if we cleared the image
                self.update_data(**{'rows': self.data['rows']})  # Update our data
                preview_image.src = "canvas_bg.png"
                preview_source_selector.content = "Set Preview Source"
                preview_image.update()
                preview_source_selector.update()

            # Set preview capture by canvas_id -> preview_capture -> default image
            if row_data.get('canvas_id'): preview_capture = self.story.get_widget_by_id(row_data.get('canvas_id')).get_snapshot_string(quality="low")
            elif row_data.get('preview_capture'): preview_capture = row_data.get('preview_capture', "")
            else: preview_capture = "canvas_bg.png"

            canvas_title = self.story.get_widget_by_id(row_data.get('canvas_id')).data.get('title', 'Untitled') if row_data.get('canvas_id') else ""
            
            row_ctrl = ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER, 
                margin=ft.Margin.only(right=10),
                spacing=20, expand=True,
                controls=[
                    ft.Container(
                        
                        ft.Column([
                            ft.MenuBar(
                                [
                                    preview_source_selector := ft.SubmenuButton(
                                        f"Current Source: {canvas_title}" if canvas_title else "Set Preview Source",
                                        [
                                            ft.MenuItemButton(
                                                ft.Text("Set Canvas", weight=ft.FontWeight.BOLD),
                                                close_on_click=True,
                                                leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, self.data.get('color', 'primary'),),
                                                on_click=set_canvas_as_image,
                                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                                
                                            ),
                                            ft.MenuItemButton(
                                                ft.Text("Upload Image", weight=ft.FontWeight.BOLD),
                                                close_on_click=True,
                                                leading=ft.Icon(ft.Icons.IMAGE_SEARCH_OUTLINED, self.data.get('color', 'primary'),),
                                                on_click=upload_image,
                                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                            ),
                                            ft.MenuItemButton(
                                                ft.Text("Clear Source", weight=ft.FontWeight.BOLD),
                                                close_on_click=True,
                                                leading=ft.Icon(ft.Icons.HIDE_IMAGE_OUTLINED, self.data.get('color', 'primary'),),
                                                on_click=clear_image,
                                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                            ),
                                        ],
                                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                                        style=ft.ButtonStyle(
                                            padding=ft.Padding.symmetric(vertical=0, horizontal=6), bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                                            alignment=ft.Alignment.CENTER, mouse_cursor=ft.MouseCursor.CLICK,
                                            shape=ft.RoundedRectangleBorder(radius=4),
                                        ),
                                        tooltip="Set the preview source to a canvas or upload an image.",
                                    ),
    
                                ],
                                style=ft.MenuStyle(
                                    bgcolor="transparent", shadow_color="transparent",
                                    shape=ft.RoundedRectangleBorder(radius=4),
                                    padding=ft.Padding.all(0)
                                ),
                            ),
                            ft.Container(
                                preview_image := ft.Image(   # Loads the str of the canvas we're connected to (if one) or loads the uploaded image
                                    preview_capture,
                                    width=row_data.get('width', 300), height=row_data.get('height', 300), fit=ft.BoxFit.FILL,
                                ),
                                image=ft.DecorationImage("canvas_bg.png", alignment=ft.Alignment.TOP_LEFT, repeat=ft.ImageRepeat.REPEAT),
                            ),
                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=300, alignment=ft.Alignment.BOTTOM_CENTER,
                        border_radius=ft.BorderRadius.all(4),
                    ),
                    

                    #ft.VerticalDivider(),
                    
                    ft.Container(   # Container that holds the sketch canvas and undo/redo buttons
                        ft.Column([
                            # Undo/Redo Buttons
                            ft.Row([
                                ft.IconButton(
                                    ft.Icons.UNDO, self.data.get('color', None), tooltip="Undo", mouse_cursor=ft.MouseCursor.CLICK, 
                                    data=row_idx, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                                    #on_click=self.undo,
                                ),
                                ft.IconButton(
                                    ft.Icons.REDO_OUTLINED, self.data.get('color', None), tooltip="Redo", mouse_cursor=ft.MouseCursor.CLICK, 
                                    data=row_idx, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                                    #on_click=self.redo,
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER), 
                            
                            # Contianer holding the sketch
                            ft.Container(
                                sketch_canvas := cv.Canvas(      # Canvas for drawing on
                                    content=ft.GestureDetector(
                                        mouse_cursor=ft.MouseCursor.PRECISE,
                                        on_pan_start=self.start_new_stroke,
                                        on_pan_update=self.update_stroke,
                                        on_pan_end=self.save_canvas,
                                        on_tap_up=self.add_shape,      # Handles so we can add points
                                        data=row_idx,
                                        drag_interval=10,
                                    ),
                                    width=row_data.get('width', 300), height=row_data.get('height', 300),
                                    shapes=[cv.Image(row_data.get('sketch_capture', ''), 0, 0, 300, 300)],
                                ), 
                                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                                border_radius=ft.BorderRadius.all(4),
                                opacity=0.99,
                            ),
                            
                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True), 
                        alignment=ft.Alignment.BOTTOM_CENTER,
                        width=300, #height=300,
                    ),
                    ft.Column([     # Column that holds the width/height textfields and description textfield
                        ft.Row([
                            ft.TextField(
                                str(row_data.get('width')), label="Width", dense=True, width=100, 
                                input_filter=ft.NumbersOnlyInputFilter(), on_blur=update_width,
                                label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=self.data.get('color', "primary")),
                                border_color=ft.Colors.OUTLINE_VARIANT
                            ), 
                            ft.TextField(
                                str(row_data.get('height')), label="Height", dense=True, width=100, 
                                input_filter=ft.NumbersOnlyInputFilter(), on_blur=update_height,
                                label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=self.data.get('color', "primary")),
                                border_color=ft.Colors.OUTLINE_VARIANT
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER, margin=ft.Margin.only(top=10)),
                        ft.Row([
                            size_error_text := ft.Text("", color=ft.Colors.ERROR, size=14, italic=True, weight=ft.FontWeight.W_500),
                            ft.IconButton(ft.Icons.CHECK_OUTLINED, self.data.get('color', None), mouse_cursor=ft.MouseCursor.CLICK, on_click=hide_error_text, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST),
                        ], alignment=ft.MainAxisAlignment.CENTER, visible=False),
                        
                        ft.TextField(
                            str(row_data.get('description', "")), 
                            dense=True, multiline=True,  
                            capitalization=ft.TextCapitalization.SENTENCES, smart_dashes_type=True,
                            data=row_idx,
                            on_blur=update_description,
                            expand=True, 
                            label="Description", 
                            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=self.data.get('color', "primary")),
                            border_color=ft.Colors.OUTLINE_VARIANT
                        )
                        
                    ], expand=True, alignment=ft.MainAxisAlignment.START),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, 
                        on_click=delete_row, data=row_idx, tooltip="Delete Row",
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
                    )
                ]
            )
                        
            return ft.Container(
                row_ctrl, 
                data=row_idx, #height=350, # Set data and height to 350, for uniform look
                border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                padding=ft.Padding.only(bottom=6), margin=ft.Margin.only(right=30, left=10)
            )
        
        

        # Updates the indices of our rows_column controls to match their new order
        def update_indices():
            for idx, ctrl in enumerate(rows_column.controls):
                ctrl.data = idx

        # Handles reordering rows
        def reorder_rows(e: ft.OnReorderEvent):
            ''' Reorders our rows data based on the new order of the rows_column controls '''
           
            # Update data
            row_data = self.data['rows'].pop(e.old_index)
            self.data['rows'].insert(e.new_index, row_data)
            self.update_data(**{'rows': self.data['rows']})  # Update our data so it saves the new order

            # Update controls and update indices to have new correct index
            rows_column.controls.insert(e.new_index, rows_column.controls.pop(e.old_index))
            rows_column.update()
            update_indices()

        self.description_tf.bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST
        
        # Labels for our rows data (columns)
        rows_labels = ft.Row(
            [
                ft.Text(
                    "Preview", style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")),
                    text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS, width=300,
                    tooltip="Preview of the canvas or image this sketch is attached to. Use for tracking progress or reference."
                ),
                ft.Text(
                    "Sketch", style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")),
                    text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS, width=300,
                    tooltip="Sketch for this panel in the story."
                ),
                ft.Text(
                    "Details", style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")),
                    text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS, expand=True,
                    tooltip="Details about this sketch, such as what it is, what it represents, or any other notes.\nSize of the sketch can be adjusted here, between 200 and 300 pixels.\nNotice: previews with different aspect ratios may look warped from the preview"
                ),
                ft.IconButton(ft.Icons.DELETE, opacity=0, disabled=True,)   # Spacer to match the delete button in the rows, but not clickable
            ], spacing=20, margin=ft.Margin.only(right=40, left=10))
        
        # Column that holds our rows data
        rows_column = ft.ReorderableListView(
            [create_row_ctrl(idx, row_data) for idx, row_data in enumerate(self.data.get('rows', []))], 
            scroll=ft.ScrollMode.AUTO, expand=True, on_reorder=reorder_rows
        )

        # Body of the tab, which is the content of flet container
        body = ft.Column(
            expand=True, scroll="none", spacing=0,
            controls=[                 
                
                rows_labels,
                ft.Divider(2, 2),
                        
                rows_column,
                
                ft.Row([
                    self.description_tf,
                    ft.Button(
                        "Add Row", bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                        on_click=create_row,
                        style=ft.ButtonStyle( mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=20)),
                    )
                ], spacing=0)

            ])
    
        self.content = body
       
            


