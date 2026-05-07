'''
Class for showing all our characters laidd out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.app import app
import flet.canvas as cv
from models.dataclasses.canvas_state import State
import math
from styles.snack_bar import SnackBar
import asyncio
import base64
from io import BytesIO
from PIL import Image
from styles.text_field import TextField

MAX_SHAPES_BEFORE_CAPTURE = 30   # Prevent lag from too many paths on the canvas without being removed
MAX_UNDO_LIST_TASKS = 30         # Max number of undo tasks to store in our undo list before we start deleting old ones


class CanvasBoard(Widget):
    # Constructor
    def __init__(self, name: str, page: ft.Page, directory_path: str, story: Story, data: dict=None, is_rebuilt: bool = False):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Parent class constructor
        super().__init__(
            title = name,  
            page = page,   
            directory_path = directory_path, 
            story = story,   
            data = data,  
            is_rebuilt = is_rebuilt
        )

        self.body_container.padding = ft.Padding.only(bottom=10)

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                'tag': "canvas_board",
                'color': app.settings.data.get('default_canvas_board_color'),

                'summary': str, # Description of this canvas board. Some could be for chapters (multiple canvas) or just one board

                # Labels on the top part of our grid. Users can add onto these as needed
                # Preview -> Ties to a specific Canvas and shows a preview of that Canvas in real time
                'matrix_labels': ["Preview", "Sketch", "Concept", "Notes"],   

                # Our main data matrix for this canvas board
                'matrix': [
                    [                   # First row
                        {               # First Column
                            'preview_canvas_key': "",               # Key to the canvas we are tied too
                            'preview_canvas_title': "",             # Title of the canvas we're tied to, for easy reference
                            'preview_canvas_color': "",             # Color of the canvas we're tied to, for easy reference
                            "preview_canvas_snapshot": "",          # Snapshot of the canvas for previewing
                        },         
                        {
                            'capture': "",
                            'undo_list': [],
                            'redo_list': []
                        },             # Sketch capture to be loaded into canvas
                        "",             # Concept description text
                        ""              # Any other notes for this row
                    ],      
                    [               # Second row
                        {           # First Column
                            'preview_canvas_key': "",      
                            'preview_canvas_title': "",    
                            'preview_canvas_color': "",    
                            "preview_canvas_snapshot": "",         
                        },         
                        {
                            'capture': "",
                            'undo_list': [],
                            'redo_list': []
                        },          # Second column
                        "",         # Third column
                        ""          # Fourth column
                    ]
                ]
            },
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)


        self.state: State = State()     # State model from tracking our drawing state
        self.active_path = cv.Path(elements=[], paint=ft.Paint(**app.settings.data.get('paint_settings', {})))
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Called when making changes to the data in a matrix cell
    def _update_matrix_cell(self, e):
        ''' Updates a specific cell in our matrix data '''
        
        row = e.control.data.get('row')
        column = e.control.data.get('column')
        value = e.control.value

        if isinstance(value, str):
            self.data['matrix'][row][column] = value
            self.p.run_task(self.save_dict)


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
        try:
            canvas.update()
        except Exception:
            pass
            
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
        
        row = e.control.data.get('row')
        column = e.control.data.get('column')
        canvas: cv.Canvas = e.control.parent

        # Grab old capture and add it to the undo list
        old_capture = self.data['matrix'][row][column].get('capture', "")
        if old_capture:
            self.data['matrix'][row][column]['undo_list'].append(old_capture)   
            self.data['matrix'][row][column]['redo_list'].clear()

        if len(self.data['matrix'][row][column]['undo_list']) > 30:   # Limit our undo/redo list to 30 items to save memory
            self.data['matrix'][row][column]['undo_list'].pop(0)
        
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
                self.data['matrix'][row][column]['capture'] = encoded_capture
                await self.save_dict()     # Save our data with the new capture

            # Must clear the capture or weird UI bugs
            await canvas.clear_capture()

            if len(canvas.shapes) > 30:   # Limit our canvas to 30 shapes to save memory, and clear the canvas if we exceed that
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, 200, 200))   # Re-add most reccent capture as the only shape on the canvas after clearing
                canvas.update()

            # Always re-render end of erase strokes, or they will appear broken. TEMPORARY FIX
            elif app.settings.data.get('canvas_settings', {}).get('current_control_mode', "") == "tool" and app.settings.data.get('canvas_settings', {}).get('current_tool_name', "") == "erase":   
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, 200, 200))
                canvas.update()

            # Always re-render end of non-none blend mode strokes, or they will appear broken. TEMPORARY FIX
            elif app.settings.data.get('paint_settings', {}).get('blend_mode', "") is not None:   
                canvas.shapes.clear()
                canvas.shapes.append(cv.Image(encoded_capture, 0, 0, 200, 200))
                canvas.update()

        except Exception as e:
            print("failed to save canvas", e)

    # Called when undoing a stroke on the canvas
    async def undo(self, e):

        row = e.control.data.get('row')
        column = e.control.data.get('column')

        # If there's nothing to undo, return early
        if len(self.data['matrix'][row][column]['undo_list']) == 0:
            return

        canvas: cv.Canvas = e.control.parent.parent.parent.controls[-1].content  
                
        # Grab capture we are reverting our canvas too, as well as the one to add to our redo list
        undo_capture = self.data['matrix'][row][column]['undo_list'].pop()
        redo_capture = self.data['matrix'][row][column].get('capture', "")
        
        self.data['matrix'][row][column]['redo_list'].append(redo_capture)   # Add current capture to redo list before we change it
        self.data['matrix'][row][column]['capture'] = undo_capture

        canvas.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
        canvas.shapes.append(cv.Image(undo_capture, 0, 0, 200, 200))   # Re-add most reccent capture
        canvas.update()

        await self.save_dict()

    # Called when redoing a stroke on the canvas after a previous undo
    async def redo(self, e=None):
        row = e.control.data.get('row')
        column = e.control.data.get('column')

        # If there's nothing to redo, return early
        if len(self.data['matrix'][row][column]['redo_list']) == 0:
            return
        
        canvas: cv.Canvas = e.control.parent.parent.parent.controls[-1].content  

        previous_capture = self.data['matrix'][row][column].get('capture', "")  # What the capture currently is before re-doing
        new_capture = self.data['matrix'][row][column]['redo_list'].pop()   # Grab capture we are redoing to our canvas

        
        self.data['matrix'][row][column]['undo_list'].append(previous_capture)   # Add current capture to undo list before we change it
        self.data['matrix'][row][column]['capture'] = new_capture

        canvas.shapes.clear()   # Clear the current shapes so we can redraw with the new capture
        canvas.shapes.append(cv.Image(new_capture, 0, 0, 200, 200))   # Re-add most reccent capture
        canvas.update()

        

       
        

    # Called when we click to add a new row at the bottom of our matrix
    async def _new_row_clicked(self, e=None):
        ''' Adds an empty new row to our matrix data and reloads the widget '''

        # Create a new row with default values for each column
        new_row = []
        for label in self.data['matrix_labels']:
            match label:
                case "Preview":
                    new_row.append({
                        'preview_canvas_key': "",      
                        'preview_canvas_title': "",    
                        'preview_canvas_color': "",   
                        "preview_canvas_snapshot": "", 
                    })
                case "Sketch":
                    new_row.append({
                        'capture': "",
                        'undo_list': [],
                        'redo_list': []
                    })    
                
                case _:
                    new_row.append("")

        self.story.blocker.visible = True
        self.story.blocker.update()
        await asyncio.sleep(0)

        # Add the new row to our matrix data
        self.data['matrix'].append(new_row)
        await self.save_dict()     # Save our data with the new row

        #self.story.workspace.reload_workspace()
        self.reload_widget()
        self.story.blocker.visible = False
        self.story.blocker.update()

    async def _delete_row_clicked(self, e):
        ''' Deletes a specific row from our matrix data and reloads the widget '''

        row = e.control.data.get('row') 

        if 0 <= row < len(self.data['matrix']):
            self.story.blocker.visible = True
            self.story.blocker.update() 
            await asyncio.sleep(0)

            del self.data['matrix'][row]
            await self.save_dict()     # Save our data with the deleted row

            #self.story.workspace.reload_workspace()
            self.reload_widget()
            self.story.blocker.visible = False
            self.story.blocker.update()

    
    async def _delete_column_clicked(self, column: int):
        ''' Deletes a specific column from our matrix data and reloads the widget '''

        if 0 <= column < len(self.data['matrix_labels']):
            # Remove the label
            del self.data['matrix_labels'][column]

            # Remove the column from each row
            for row in self.data['matrix']:
                if 0 <= column < len(row):
                    del row[column]

            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)


            await self.save_dict()     # Save our data with the deleted row

            #self.story.workspace.reload_workspace()
            self.reload_widget()
            self.story.blocker.visible = False
            self.story.blocker.update()

    
    async def _show_refresh_button(self, e: ft.PointerEvent):

        gd = e.control
        for control in gd.content.controls:
            if not control.visible:
                control.visible = True
        gd.update()

    async def _hide_refresh_button(self, e: ft.PointerEvent):
        gd = e.control
        for control in gd.content.controls:
            if isinstance(control, cv.Canvas):
                continue
            if control.visible:
                control.visible = False
        gd.update()

    async def _connect_canvas_clicked(self, e):

        row = e.control.data.get('row')
        column = e.control.data.get('column')

        async def _set_new_canvas_key(e):
            nonlocal canvas_key
            canvas_key = e.data

        def _load_canvases() -> list[ft.Control]:
            canvases_list = []

            for widget in self.story.widgets:
                if widget.data['tag'] == 'canvas':
                    
                    canvases_list.append(
                        ft.Radio(
                            widget.title, value=widget.data['key'], 
                            toggleable=True, mouse_cursor=ft.MouseCursor.CLICK,
                            
                            label_style=ft.TextStyle(color=widget.data.get('color', None), weight=ft.FontWeight.BOLD)
                        )
                    )
            

            if len(canvases_list) == 0:
                canvases_list.append(ft.Text("No canvases found. Create one to get started", color=ft.Colors.ON_SURFACE_VARIANT, italic=True))

            return canvases_list

        async def _connect_confirmed(e=None):
            nonlocal canvas_key 
            canvas_color = "outline"
            for w in self.story.widgets:
                if w.data['key'] == canvas_key:
                    canvas_color = w.data.get('color', "outline")
                    canvas_title = w.title

            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            self.p.pop_dialog()
            await asyncio.sleep(0)

            # Set the new key to our data and save
            self.data['matrix'][row][column]['preview_canvas_key'] = canvas_key
            self.data['matrix'][row][column]['preview_canvas_title'] = canvas_title
            self.data['matrix'][row][column]['preview_canvas_color'] = canvas_color
            self.data['matrix'][row][column]['preview_canvas_snapshot'] = self._set_canvas_snapshot(canvas_key)
            await self.save_dict()     

            #self.story.workspace.reload_workspace()
            self.reload_widget()

            self.story.blocker.visible = False
            self.story.blocker.update()

        canvas_key = ""
        
        confirm_button = ft.TextButton("Confirm", on_click=_connect_confirmed, style=ft.ButtonStyle(mouse_cursor="click"))
        dlg = ft.AlertDialog(
            title=ft.Text("Choose a Canvas"),
            content=ft.RadioGroup(ft.Column(_load_canvases(), tight=True, scroll="auto"), on_change=_set_new_canvas_key),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                confirm_button
            ]
        )
        self.p.show_dialog(dlg)

    # Called to find a canvas and load a snapshot from all its layers
    def _set_canvas_snapshot(self, canvas_key: str) -> str:

        capture_list = []
        for widget in self.story.widgets:
            if widget.data['key'] == canvas_key:
                for layer in widget.data.get('canvas_data', {}).get('Layers', []):
                    if layer.get('capture', ""):
                        capture_list.append(layer['capture'])
                break

        
        if not capture_list:
            return ""

        images = []
        for capture in capture_list:
            try:
                image_bytes = base64.b64decode(capture)
                image = Image.open(BytesIO(image_bytes)).convert("RGBA")
                images.append(image)
            except Exception:
                continue

        if not images:
            return ""

        width, height = images[0].size
        merged = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        for image in images:
            if image.size != (width, height):
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            merged = Image.alpha_composite(merged, image)

        output = BytesIO()
        merged.save(output, format="PNG")
        return base64.b64encode(output.getvalue()).decode("utf-8")
    
    async def _refresh_preview(self, e):
        row = e.control.data.get('row')
        column = e.control.data.get('column')
        canvas_key = e.control.data.get('canvas_key')

        self.story.blocker.visible = True
        self.story.blocker.update()
        await asyncio.sleep(0)

        self.data['matrix'][row][column]['preview_canvas_snapshot'] = self._set_canvas_snapshot(canvas_key)
        await self.save_dict()     # Save our data with the deleted row

        #self.story.workspace.reload_workspace()
        self.reload_widget()
        self.story.blocker.visible = False
        self.story.blocker.update()
    

    async def _disconnect_canvas(self, e):

        row = e.control.data.get('row')
        column = e.control.data.get('column')

        self.story.blocker.visible = True
        self.story.blocker.update()
        await asyncio.sleep(0)

        # Remove the canvas key from our data and save
        self.data['matrix'][row][column]['preview_canvas_key'] = ""
        self.data['matrix'][row][column]['preview_canvas_snapshot'] = ""
        self.data['matrix'][row][column]['preview_canvas_title'] = ""
        self.data['matrix'][row][column]['preview_canvas_color'] = ""
        await self.save_dict()     # Save our data with the deleted row

        #self.story.workspace.reload_workspace()
        self.reload_widget()

        self.story.blocker.visible = False
        self.story.blocker.update()
    


    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        description_tf = TextField(
            expand=True, value=self.data.get('description', ""), dense=True, multiline=True,
            label="Description",
            capitalization=ft.TextCapitalization.SENTENCES, 
            on_blur=lambda e: self.p.run_task(self.change_data, **{'description': e.control.value}),
            hint_text="Description of the scope of this Canvas Board..."       
        )

        def _get_matrix_label_controls() -> list[ft.Control]:
            ''' Formats our labels insto text controls above our grid '''

            # Start with invisible button to keep spacing
            controls = [ft.IconButton(ft.Icons.ADD, opacity=0, disabled=True)]

            # Add each label as a text control
            for idx, label in enumerate(self.data['matrix_labels']):
                text_control = ft.Text(
                        label, style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")),
                        tooltip="Connect to one of your canvases and show a live preview of your progress!" if label == "Preview" else None,
                        width=225 if idx <= 1 else None,
                         
                        text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS
                    )
                
                if idx <= 1:
                    controls.append(text_control)
                else:
                    controls.append(ft.Container(text_control, alignment=ft.Alignment.CENTER, expand=True))

            controls.append(ft.IconButton(ft.Icons.ADD, opacity=0, disabled=True))
            controls.append(ft.Container(width=10))
                    
            return controls
        

        # Lays out our controls in a nice grid format
        def _get_matrix_data_controls() -> list[ft.Control]:

            # TODO: Popupmenubutton for connect/disconnect, hover/click to refresh

            controls = []

            # Go through each row in the matrix data
            for idx, row in enumerate(self.data['matrix']):
                
                # Establish a row control we will add our cells to
                row_control = ft.Row([ft.IconButton(ft.Icons.ADD, opacity=0, disabled=True)], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)

                # For each column (cell) in the row and add correct control based on its label
                for sub_idx, cell in enumerate(row):                    
                    
                    # Build a preview for a connectted canvas
                    # TODO: Wrap canvas in container that clicking refreshes
                    if sub_idx == 0:

                        # Other attributes about the canvas we're using
                        canvas_key = cell.get('preview_canvas_key', "")
                        canvas_title = cell.get('preview_canvas_title', "")
                        canvas_color = cell.get('preview_canvas_color', ft.Colors.OUTLINE)
                                
                        # Set a canvas just to display
                        preview_image = ft.Image(
                            cell.get('preview_canvas_snapshot', ""), ft.Text("Failed to grab preview snapshot"),
                            height=200, width=200, fit=ft.BoxFit.FILL, 
                        ) if cell.get('preview_canvas_snapshot', "") else ft.Container(
                            ft.Text("No Canvas Connected", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                            width=200, height=200, alignment=ft.Alignment.CENTER
                        )
                        

                        connected_canvas_button = ft.MenuBar([
                            ft.SubmenuButton(
                                canvas_title if canvas_title else ft.Text("Connect Canvas", color=ft.Colors.ON_SURFACE_VARIANT),
                                
                                [
                                    ft.MenuItemButton(
                                        "Connect Canvas", leading=ft.Icon(ft.Icons.LINK_OUTLINED),
                                        on_click=self._connect_canvas_clicked,
                                        data={"row": idx, "column": sub_idx},
                                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=10)),
                                    ),
                                    ft.MenuItemButton(
                                        "Refresh Preview", leading=ft.Icon(ft.Icons.REFRESH_OUTLINED),
                                        on_click=self._refresh_preview if canvas_key else None,
                                        data={"row": idx, "column": sub_idx, "canvas_key": canvas_key},
                                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=10)),
                                    ),
                                    ft.MenuItemButton(
                                        "Disconnect Canvas", leading=ft.Icon(ft.Icons.LINK_OFF_OUTLINED),
                                        on_click=self._disconnect_canvas if canvas_key else None,   
                                        data={"row": idx, "column": sub_idx},
                                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=10)),
                                    )
                                ],
                                style=ft.ButtonStyle(
                                    mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=10),
                                    color=canvas_color,
                                ),
                                menu_style=ft.MenuStyle(padding=ft.Padding.all(0)),
                            )
                        ], style=ft.MenuStyle(
                            visual_density=ft.VisualDensity.COMPACT, padding=0,
                            bgcolor="transparent", shadow_color="transparent",
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ))

                        preview_image_container = ft.Container(
                            preview_image, border=ft.Border.all(1, ft.Colors.OUTLINE),
                            bgcolor="surface", border_radius=ft.BorderRadius.all(6),
                            alignment=ft.Alignment.CENTER, width=200, height=200,
                        )
                        
                        row_control.controls.append(
                            ft.Container(
                                ft.Column([
                                    connected_canvas_button,
                                    preview_image_container,
                                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER), 
                                padding=ft.Padding.only(left=12, right=12, bottom=12), alignment=ft.Alignment.BOTTOM_CENTER,
                            )
                        )

                        # Build a sketch canvas for this row
                    elif sub_idx == 1:      # Sketch canvas for rough thumbnails
                        capture = cell.get('capture', "")
                        sketch_canvas = cv.Canvas(
                            content=ft.GestureDetector(
                                mouse_cursor=ft.MouseCursor.PRECISE,
                                on_pan_start=self.start_new_stroke,
                                on_pan_update=self.update_stroke,
                                on_pan_end=self.save_canvas,
                                on_tap_up=self.add_shape,      # Handles so we can add points
                                drag_interval=10,
                                data={"row": idx, "column": sub_idx},
                            ),
                            width=200, height=200,
                            shapes=[cv.Image(capture, 0, 0, 200, 200)],
                        )
                        row_control.controls.append(
                            ft.Container(
                                ft.Column([
                                    ft.Container(
                                        ft.Row([
                                            ft.IconButton(
                                                ft.Icons.UNDO, self.data.get('color', None), tooltip="Undo", mouse_cursor=ft.MouseCursor.CLICK, 
                                                data={"row": idx, "column": sub_idx},
                                                on_click=self.undo,
                                            ),
                                            ft.IconButton(
                                                ft.Icons.REDO_OUTLINED, self.data.get('color', None), tooltip="Redo", mouse_cursor=ft.MouseCursor.CLICK, 
                                                data={"row": idx, "column": sub_idx},
                                                on_click=self.redo,
                                            ),
                                        ], alignment=ft.MainAxisAlignment.CENTER), 
                                        height=40
                                    ),
                                    ft.Container(
                                        sketch_canvas, border=ft.Border.all(1, ft.Colors.OUTLINE),
                                        opacity=0.99,
                                        bgcolor="surface", border_radius=ft.BorderRadius.all(6),
                                    ),
                                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.END), 
                                padding=ft.Padding.only(left=12, right=12, bottom=12),
                            )
                        )
                        #preview_canvas.shapes.extend(self._load_canvas(idx, sub_idx))   # Load our saved canvas data into the canvas

                    # Build textfield for all other types of columns
                    else:     
                        row_control.controls.append(
                            ft.Container(
                                ft.Column([
                                    ft.TextField(
                                        str(cell), 
                                        dense=True, multiline=True, 
                                        capitalization=ft.TextCapitalization.SENTENCES, smart_dashes_type=True,
                                        data={"row": idx, "column": sub_idx},
                                        on_blur=self._update_matrix_cell, #expand=True,
                                        width=2000, height=225,
                                        border_color=ft.Colors.OUTLINE_VARIANT
                                    )], 
                                    scroll="auto", alignment=ft.MainAxisAlignment.START,
                                    
                                    expand=True,
                                ),
                            padding=ft.Padding.only(left=12, right=12, bottom=12),
                            expand=True,
                            )
                        )

                row_control.controls.append(
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, 
                        on_click=self._delete_row_clicked, data={"row": idx}, tooltip="Delete Row",
                        mouse_cursor=ft.MouseCursor.CLICK,
                    )
                )
                row_control.controls.append(ft.Container(width=10))

                controls.append(row_control)

                # Add divider under each row except the last one
                if idx < len(self.data['matrix']) - 1:
                    controls.append(ft.Divider(2, 2))
                    
            return controls
        
        # Labels for our matrix data (columns)
        matrix_labels = ft.Row(_get_matrix_label_controls(), spacing=0, scroll="none")

        matrix_grid_view = ft.Column(_get_matrix_data_controls(), spacing=0, scroll="auto", tight=True, expand=True)


        # Body of the tab, which is the content of flet container
        body = ft.Column(
            expand=True, scroll="none", spacing=0,
            controls=[                 
                
                matrix_labels,
                ft.Divider(2, 2),
                        
                matrix_grid_view,
                ft.Container(height=10),
                
                ft.Row([
                    ft.TextButton(
                        "Add New Row",
                        on_click=self._new_row_clicked,
                        style=ft.ButtonStyle(self.data.get('color', ft.Colors.PRIMARY), icon_size=20, mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                    ),
                    description_tf,
                    ft.Container(width=10)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

            ])
    

        self.body_container.content = body

        # Add choose file to preview options

        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


