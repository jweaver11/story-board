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
                        'preview_capture': "",    # Base64 string of the preview capture
                        'sketch_capture': "",    # Base64 string of the sketch capture
                        'description': "",    # Description of the sketch
                        'height': 300,      # Height of the canvas
                        'width': 300,       # Width of the canvas
                    }
                ],
            },
        )



        self.state: State = State()     # State model from tracking our drawing state
        self.active_path: cv.Path
        

    # Called when making changes to the data in a rows cell
    def update_description_cell(self, e: ft.Event):
        ''' Updates a specific cell in our rows data '''
        # Grab index positions
        row_idx = e.control.data
        cell_idx = 1       # Descriptions are always second
        value = e.control.value

        # Update data
        self.data['rows'][row_idx][cell_idx] = value
        self.update_data(**{'rows': self.data.get('rows')})


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

        # After dragging canvas widget, it loses page reference and can't update, so the exception handles that.
        #self._render_widget()
            
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
        async def create_row(e: ft.Event=None):
            ''' Adds an empty new row to our rows data and reloads the widget '''

            # Create a new row with default values of each cell
            new_row_dict = {
                'canvas_id': "",    # ID of the canvas we're attached to, if we're attached to one
                'sketch_capture': "",    # Base64 string of the sketch capture
                'description': "",    # Description of the sketch
                'height': 300,      # Height of the canvas
                'width': 300,       # Width of the canvas
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
            await rows_column.scroll_to(-1, duration=600)
        

        # Creates a rows row ctrl for the body of our widget
        def create_row_ctrl(row_idx: int, row_data: dict) -> ft.Container: 
            sketch_canvas = cv.Canvas(      # Canvas for drawing on
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
            )
            row_ctrl = ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER, 
                margin=ft.Margin.only(right=10),
                controls=[
                    ft.Container(
                        ft.Image(   # Loads the str of the canvas we're connected to (if one) or loads the uploaded image
                            self.story.get_widget_by_id(
                                row_data.get('canvas_id')
                            ).get_snapshot_string(quality="low") if row_data.get('canvas_id') else row_data.get('preview_capture', ""),
                            ft.Text("Error"),
                            width=row_data.get('width', 300), height=row_data.get('height', 300), fit=ft.BoxFit.FILL,
                        ),
                        width=300, height=300, alignment=ft.Alignment.CENTER
                    ),

                    ft.VerticalDivider(),
                    
                    ft.Container(
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
                                sketch_canvas, 
                                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, 
                                border_radius=ft.BorderRadius.all(4),
                                opacity=0.99,
                            ),
                            
                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True), 
                        data=row_idx,
                        width=300, height=300, alignment=ft.Alignment.CENTER
                    ),
                    ft.Column([
                        ft.Row([ft.TextField("Width", dense=True, expand=True), ft.TextField("Height", dense=True, expand=True)]),
                        ft.TextField(
                            str(row_data.get('description', "")), 
                            dense=True, multiline=True,  
                            capitalization=ft.TextCapitalization.SENTENCES, smart_dashes_type=True,
                            data=row_idx,
                            on_blur=self.update_description_cell, #expand=True,
                            expand=True, label="Description", 
                            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=self.data.get('color', "primary")),
                            border_color=ft.Colors.OUTLINE_VARIANT
                        )
                    ], expand=True),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, 
                        on_click=delete_row, data=row_idx, tooltip="Delete Row",
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
                    )
                ]
            )
            
            # TODO: 
            # Load all rows
            # Make uploaded images lower quality to save performance
            # Load sketches
                        
            return ft.Container(
                row_ctrl, 
                #border=ft.Border.only(bottom=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)) if row_idx < len(self.data['rows']) - 1 else None,
                #padding=ft.Padding.only(bottom=10) if row_idx < len(self.data['rows']) - 1 else None,
                height=300,
            )
        
        async def delete_row(e: ft.Event):
            ''' Deletes a specific row from our rows data and reloads the widget '''

            row_idx = e.control.data

            if 0 <= row_idx < len(self.data['rows']):
                

                del self.data['rows'][row_idx]
                self.update_data(**{'rows': self.data['rows']})  # Update our data so it saves the deleted row

                rows_column.controls.pop(row_idx)
                rows_column.update()
                update_indices()

        def update_indices():
            for idx, ctrl in enumerate(rows_column.controls):
                row_ctrl: ft.Row = ctrl.content     # Our row control, which should have 3 controls itself
                row_ctrl.controls[0].data = idx     # Container that holds undo, redo, and canvas
                row_ctrl.controls[1].data = idx     # Description tf
                row_ctrl.controls[2].data = idx     # Delete button

        self.description_tf.bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST
        self.padding = ft.Padding.only(left=10, top=10)
        
        # Labels for our rows data (columns)
        rows_labels = ft.Row(
            [
                ft.Text(
                    "Sketch", style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")),
                    text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS, width=300,
                ),
                ft.Text(
                    "Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")),
                    text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS, expand=True
                )
            ],
            spacing=0, scroll="none"
        )
        
        # Column that holds our rows data
        rows_column = ft.Column(
            [], 
            spacing=0, scroll="auto", tight=True, expand=True
        )
        # Go through our data and add a new row
        for row_idx, row_data in enumerate(self.data['rows']):
            rows_column.controls.append(create_row_ctrl(row_idx, row_data))
            

        # Body of the tab, which is the content of flet container
        body = ft.Column(
            expand=True, scroll="none", spacing=0,
            controls=[                 
                
                rows_labels,
                ft.Divider(),
                        
                rows_column,
                
                ft.Row([ 
                    self.description_tf,
                    ft.Button(
                        "Add Row", bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                        on_click=create_row,
                        style=ft.ButtonStyle( mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=20)),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, margin=ft.Margin.only(right=10))

            ])
    
        self.content = body
       
            


