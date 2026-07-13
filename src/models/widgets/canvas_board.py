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
    def __init__(self, name: str, directory_path: str, story: Story, data: dict=None, is_new: bool = False):

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
                'show_sidebar': False,      # Flag false since we won't use it

                'summary': str(), # Description of this canvas board. Some could be for chapters (multiple canvas) or just one board

                # Labels on the top part of our grid. Users can add onto these as needed
                # Preview -> Ties to a specific Canvas and shows a preview of that Canvas in real time

                # Our main data matrix for this canvas board
                'matrix': [
                    [                   # First row
                        {               # First Cell
                            'sketch_capture': "",                       # Capture of the sketch
                            'undo_list': list(),                        # Capture list of undo actions
                            'redo_list': list()                         # Capture list of redo actions
                        },             
                        "",              # Second Cell - Concept description text
                    ],      
                    [               # Second row      
                        {           # First Cell
                            'sketch_capture': "",
                            'undo_list': list(),
                            'redo_list': list()
                        },          # Second cell
                        "",         # Third cell
                    ]
                ]
            },
        )



        self.state: State = State()     # State model from tracking our drawing state
        self.active_path = cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))
        

    # Called when making changes to the data in a matrix cell
    def update_description_cell(self, e: ft.Event):
        ''' Updates a specific cell in our matrix data '''
        # Grab index positions
        row_idx = e.control.data
        cell_idx = 1       # Descriptions are always second
        value = e.control.value

        # Update data
        self.data['matrix'][row_idx][cell_idx] = value
        self.update_data(**{'matrix': self.data.get('matrix')})


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
        
        row_idx = e.control.data
        cell_idx = 0
        canvas: cv.Canvas = e.control.parent

        # Grab old capture and add it to the undo list
        old_capture = self.data['matrix'][row_idx][cell_idx].get('capture', "")
        if old_capture:
            self.data['matrix'][row_idx][cell_idx]['undo_list'].append(old_capture)   
            self.data['matrix'][row_idx][cell_idx]['redo_list'].clear()

        if len(self.data['matrix'][row_idx][cell_idx]['undo_list']) > 30:   # Limit our undo/redo list to 30 items to save memory
            self.data['matrix'][row_idx][cell_idx]['undo_list'].pop(0)
        
        try:
            await canvas.capture()
    
            capture = await canvas.get_capture()
            encoded_capture = base64.b64encode(capture).decode('utf-8')      # Requires encoding to save json

            # If capture failed, return
            if not encoded_capture:
                await canvas.clear_capture()
                return

            if encoded_capture:

                # Save the capture, but we don't use it until a reload_widget is called
                self.data['matrix'][row_idx][cell_idx]['sketch_capture'] = encoded_capture
                self.update_data(**{'matrix': self.data['matrix']}) 

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

    # Called when undoing a stroke on the canvas
    async def undo(self, e: ft.Event):

        row_idx = e.control.data
        cell_idx = 0

        # If there's nothing to undo, return early
        if len(self.data['matrix'][row_idx][cell_idx]['undo_list']) == 0:
            return

        canvas: cv.Canvas = e.control.parent.parent.parent.controls[-1].content  
                
        # Grab capture we are reverting our canvas too, as well as the one to add to our redo list
        undo_capture = self.data['matrix'][row_idx][cell_idx]['undo_list'].pop()
        redo_capture = self.data['matrix'][row_idx][cell_idx].get('capture', "")
        
        self.data['matrix'][row_idx][cell_idx]['redo_list'].append(redo_capture)   # Add current capture to redo list before we change it
        self.data['matrix'][row_idx][cell_idx]['capture'] = undo_capture

        canvas.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
        canvas.shapes.append(cv.Image(undo_capture, 0, 0, 300, 300))   # Re-add most reccent capture
        canvas.update()

        self.update_data(**{'matrix': self.data['matrix']})  # Update our data so it saves the undo/redo lists  

    # Called when redoing a stroke on the canvas after a previous undo
    async def redo(self, e=None):
        row_idx = e.control.data
        cell_idx = 0

        # If there's nothing to redo, return early
        if len(self.data['matrix'][row_idx][cell_idx]['redo_list']) == 0:
            return
        
        canvas: cv.Canvas = e.control.parent.parent.parent.controls[-1].content  

        previous_capture = self.data['matrix'][row_idx][cell_idx].get('capture', "")  # What the capture currently is before re-doing
        new_capture = self.data['matrix'][row_idx][cell_idx]['redo_list'].pop()   # Grab capture we are redoing to our canvas

        
        self.data['matrix'][row_idx][cell_idx]['undo_list'].append(previous_capture)   # Add current capture to undo list before we change it
        self.data['matrix'][row_idx][cell_idx]['capture'] = new_capture

        canvas.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
        canvas.shapes.append(cv.Image(new_capture, 0, 0, 300, 300))   # Re-add most reccent capture
        canvas.update()
        

    # Called when we click to add a new row at the bottom of our matrix
    async def create_row(self, e: ft.Event=None):
        ''' Adds an empty new row to our matrix data and reloads the widget '''

        # Create a new row with default values of each cell
        new_row = [
            {
                'sketch_capture': "",    
                'undo_list': list(),
                'redo_list': list()
            },
            ""
        ]
        
        # Add the new row to our matrix data
        self.data['matrix'].append(new_row)
        self.update_data(**{'matrix': self.data['matrix']})  # Update our data so it saves the new row

        self.reload_widget()
        

    async def delete_row(self, e: ft.Event):
        ''' Deletes a specific row from our matrix data and reloads the widget '''

        row = e.control.data

        if 0 <= row < len(self.data['matrix']):
            

            del self.data['matrix'][row]
            self.update_data(**{'matrix': self.data['matrix']})  # Update our data so it saves the deleted row

            self.reload_widget()
    
    def build(self):
        self.padding = ft.Padding.only(left=10, top=10, bottom=10)
        super().build()

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Downscales images for preview to improve performance
        def downscale_image(image_str: str) -> str:

            try:
                image_bytes = base64.b64decode(image_str)
                img = Image.open(BytesIO(image_bytes))
                if img.mode in ("P", "PA"):  # palette images with transparency must go via RGBA
                    img = img.convert("RGBA")
                has_alpha = img.mode in ("RGBA", "LA")
                if not has_alpha:
                    img = img.convert("RGB")
                max_dim = 2160  # cap at 4K height; anything larger is not visible anyway
                if img.width > max_dim or img.height > max_dim:
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                output = BytesIO()
                if has_alpha:
                    img.save(output, format="PNG", optimize=True)
                else:
                    img.save(output, format="JPEG", quality=92, optimize=True)
                image_str = base64.b64encode(output.getvalue()).decode("utf-8")
            except Exception:
                pass 
            return image_str


        description_tf = TextField(
            expand=True, value=self.data.get('description', ""), dense=True, multiline=True,
            label="Description",
            capitalization=ft.TextCapitalization.SENTENCES, 
            on_blur=lambda e: self.update_data(**{'description': e.control.value}),
            hint_text="Description of the scope of this Canvas Board..."       
        )

        

        # Lays out our controls in a nice grid format
        def _get_matrix_data_controls() -> list[ft.Control]:

            controls = []

            # Go through each row in the matrix data
            for row_idx, row_data in enumerate(self.data['matrix']):
                
                # Establish a row control we will add our cells to
                row_control = ft.Row([],  vertical_alignment=ft.CrossAxisAlignment.CENTER, margin=ft.Margin.only(right=10))

                # For each column (cell) in the row and add correct control based on its label
                for cell_idx, cell in enumerate(row_data):                    
                    
                    # Load sketches
                    if cell_idx == 0:
                        
                        capture = cell.get('sketch_capture', "")
                        sketch_canvas = cv.Canvas(
                            content=ft.GestureDetector(
                                mouse_cursor=ft.MouseCursor.PRECISE,
                                on_pan_start=self.start_new_stroke,
                                on_pan_update=self.update_stroke,
                                on_pan_end=self.save_canvas,
                                on_tap_up=self.add_shape,      # Handles so we can add points
                                data=row_idx,
                            ),
                            #width=300, height=300,
                            shapes=[cv.Image(capture, 0, 0, 300, 300)],
                        )
                        row_control.controls.append(
                            ft.Container(
                                ft.Column([
                                    # Undo/Redo Buttons
                                    ft.Row([
                                        ft.IconButton(
                                            ft.Icons.UNDO, self.data.get('color', None), tooltip="Undo", mouse_cursor=ft.MouseCursor.CLICK, 
                                            data=row_idx, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                                            on_click=self.undo,
                                        ),
                                        ft.IconButton(
                                            ft.Icons.REDO_OUTLINED, self.data.get('color', None), tooltip="Redo", mouse_cursor=ft.MouseCursor.CLICK, 
                                            data=row_idx, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                                            on_click=self.redo,
                                        ),
                                    ], alignment=ft.MainAxisAlignment.CENTER), 
                                    
                                    # Contianer holding the sketch
                                    ft.Container(
                                        sketch_canvas, 
                                        width=300, height=300,
                                        bgcolor=ft.Colors.BLACK, border_radius=ft.BorderRadius.all(4),
                                        #opacity=0.99,
                                    ),
                                    
                                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True), 
                            )
                        )

                    # Build textfield for all other types of columns
                    else:     
                        row_control.controls.append(
                            ft.TextField(
                                str(cell), 
                                dense=True, multiline=True,  
                                capitalization=ft.TextCapitalization.SENTENCES, smart_dashes_type=True,
                                data=row_idx,
                                on_blur=self.update_description_cell, #expand=True,
                                expand=True,
                                border_color=ft.Colors.OUTLINE_VARIANT
                            )
                        )
                           

                row_control.controls.append(
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, 
                        on_click=self.delete_row, data=row_idx, tooltip="Delete Row",
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST
                    )
                )

                controls.append(row_control)

                # Add divider under each row except the last one
                if row_idx < len(self.data['matrix']) - 1:
                    controls.append(ft.Divider())
                    
            return controls
        
        # Labels for our matrix data (columns)
        matrix_labels = ft.Row(
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
        

        matrix_grid_view = ft.Column(_get_matrix_data_controls(), spacing=0, scroll="auto", tight=True, expand=True)


        # Body of the tab, which is the content of flet container
        body = ft.Column(
            expand=True, scroll="none", spacing=0,
            controls=[                 
                
                matrix_labels,
                ft.Divider(),
                        
                matrix_grid_view,
                
                ft.Row([ 
                    description_tf,
                    ft.Button(
                        "Add Row", bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                        on_click=self.create_row,
                        style=ft.ButtonStyle( mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=20)),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, margin=ft.Margin.only(right=10))

            ])
    
        self.body_container.content = body

        self._render_widget()
       
            


