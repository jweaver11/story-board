'''
Class for showing all our characters laidd out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.app import app
import flet.canvas as cv
from models.dataclasses.state import State
import math
from styles.snack_bar import SnackBar
import asyncio


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

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                'tag': "canvas_board",
                'color': app.settings.data.get('default_canvas_board_color'),

                'summary': str, # Description of this canvas board. Some could be for chapters (multiple canvas) or just one board

                # Labels on the top part of our grid. Users can add onto these as needed
                'matrix_labels': ["Preview", "Sketch", "Concept"],   # Preview -> Ties to a specific Canvas and shows a preview of that Canvas in real time

                # Our main data matrix for this canvas board
                'matrix': [
                    [           # First row
                        {       # Preview. This will key to a specific canvas later and show a live preview
                            'canvas_key': "",      # Key to the canvas we are tied too
                            "snapshot": [],         # Snapshot of the canvas for previewing
                        },         
                        {           # Sketch canvas data
                            'paths': [],            # All our shapes, lines, dashed lines, curves, etc.
                            'shadow_paths': [],     # All paths but with shadows
                            'points': [],           # All our points
                        }, 
                        ""           # Concept description text
                    ],      
                    [           # Second row
                        {
                            'canvas_key': "",
                            "snapshot": [],
                        },         
                        {
                            'paths': [],            # All our shapes, lines, dashed lines, curves, etc.
                            'shadow_paths': [],     # All paths but with shadows
                            'points': [],           # All our points
                        }, 
                        ""
                    ]
                ]
            },
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)


        self.state: State = State()     # State model from tracking our drawing state
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Called when making changes to the data in a matrix cell
    def _update_matrix_cell(self, row: int, column: int, value):
        ''' Updates a specific cell in our matrix data '''
        

        if isinstance(value, str):
            self.data['matrix'][row][column] = value
            self.p.run_task(self.save_dict)

    # Called on launch to load our drawing from data into our canvas
    def _load_canvas(self, row: int, column: int) -> list:
        """Loads our drawing from our saved map drawing file."""

        # Clear our canvas, and load our shapes stored in data
        shapes = []
        
        

        #print("Data to load: ", self.data['matrix'][row][column])

        # Loading points
        for point in self.data['matrix'][row][column].get('points', []):
            px, py, point_mode, paint_settings = point
            shapes.append(
                cv.Points(
                    points=[(px, py)],
                    point_mode=point_mode,
                    paint=ft.Paint(**paint_settings),
                )
            )

        # Loading our paths, which most of the drawing
        for path in self.data['matrix'][row][column].get('paths', []):
            
            elements = path.get('elements', [])         # List of the elements in this path
            paint_settings = path.get('paint', {})      # Paint settings for this path

            # Grab our style for simple logic
            style = path.get('paint', {}).get('style', 'stroke')

            # Make a copy of our paint settings to modify for drawing
            safe_paint_settings = path.get('paint', {}).copy()

            # If in erase mode, we have to set blur_image to 0 and
            if safe_paint_settings.get('blend_mode', 'src_over') == 'clear':
                safe_paint_settings['blur_image'] = 0

            # Set stroke or fill based on custom styles
            safe_stroke = 'fill' if style.endswith('fill') else 'stroke'
            safe_paint_settings['style'] = safe_stroke

            new_path = cv.Path(elements=[], paint=ft.Paint(**safe_paint_settings))   # Set a new path for this path with our paint settings

            # Iterate through each element for its type, and create a new path element based on that
            for element in elements:

                # MoveTo just has x and y
                if element['type'] == 'moveto':
                    new_path.elements.append(cv.Path.MoveTo(element['x'], element['y']))

                # Lineto jjust has x and y
                elif element['type'] == 'lineto':
                    new_path.elements.append(cv.Path.LineTo(element['x'], element['y']))

                elif element['type'] == 'arc':
                    new_path.elements.append(
                        cv.Path.Arc(
                            width=element['width'],
                            height=element['height'],
                            x=element['x'],
                            y=element['y'],
                            start_angle=element['start_angle'],
                            sweep_angle=element['sweep_angle'],
                        )
                    )
                        

                # QuadraticTo has cp1x, cp1y, x, y, w
                elif element['type'] == 'arcto':
                    new_path.elements.append(
                        cv.Path.ArcTo(
                            radius=element['radius'],
                            rotation=element['rotation'],
                            large_arc=element['large_arc'],
                            x=element['x'],
                            y=element['y'],
                        )
                    )

                
                else:
                    print("Unknown path element type while loading: ", element)
                    self.p.show_dialog(SnackBar(f"Error loading {self.title}"))

            shapes.append(new_path)

        return shapes


        # Called when we click the canvas and don't initiate a drag
    def add_point(self, row: int, column: int, e: ft.TapEvent):
        ''' Adds a point to the canvas if we just clicked and didn't initiate a drag '''

        # Create the point using our paint settings and point mode
        point = cv.Points(
            points=[(e.local_x, e.local_y)],
            paint=ft.Paint(**app.settings.data.get('paint_settings', {})),
        )
        
        # Add point to the canvas and our state data
        e.control.parent.shapes.append(point)
        self.state.points.append((e.local_x, e.local_y, point.point_mode, point.paint.__dict__))

        # After dragging canvas widget, it loses page reference and can't update
        try:
            e.control.parent.update()
            
        except Exception as ex:
            print("Failed to update e.control")
            self.p.update()
            
            
        # Save our canvas data
        self.save_canvas(row, column)
        
    # Called when we start drawing on the canvas
    async def start_drawing(self, e: ft.DragStartEvent):
        ''' Set our initial starting x and y coordinates for the element we're drawing '''

        # Grab our style so we can compare it
        style = str(app.settings.data.get('paint_settings', {}).get('style', 'stroke'))

        # Make a copy of our paint settings to modify it, since some of the styles are not built in
        safe_paint_settings = app.settings.data.get('paint_settings', {}).copy()

        # Copy of our paint settings for our state tracking and data storage (only erase mode needs this)
        state_paint_settings = app.settings.data.get('paint_settings', {}).copy()

        # Set either stroke or fill based on custom styles
        safe_stroke = 'fill' if style.endswith('fill') else 'stroke'
        safe_paint_settings['style'] = safe_stroke

        # Check if we're in erase mode or not. If we are, set blend mode to clear and blur image to 0
        if self.story.data.get('canvas_settings', {}).get('erase_mode', False):
            safe_paint_settings['blend_mode'] = "clear"
            safe_paint_settings['blur_image'] = 0
            state_paint_settings['blend_mode'] = "clear"
            state_paint_settings['blur_image'] = 0
        

        # Update state x and y coordinates
        self.state.x, self.state.y = e.local_x, e.local_y

        # Clear and set our current path and state to match it
        self.current_path = cv.Path(elements=[], paint=ft.Paint(**safe_paint_settings))
        self.state.paths.clear()
        self.state.paths.append({'elements': list(), 'paint': state_paint_settings})

        # Set move to element at our starting position that the mouse is at for the path to start from
        move_to_element = cv.Path.MoveTo(e.local_x, e.local_y)

        # Add that element to current paths elements and our state paths
        self.current_path.elements.append(move_to_element)
        self.state.paths[0]['elements'].append((move_to_element.__dict__))

        #print(f"Starting drawing with style {style}")

        # If we're using lineto (straight lines), add that element to the current path and state right away
        if style == "lineto":
            line_element = cv.Path.LineTo(e.local_x, e.local_y)
            self.current_path.elements.append(line_element)
            self.state.paths[0]['elements'].append((line_element.__dict__))

        elif style == "arc":
            arc_element = cv.Path.Arc(
                width=20,
                height=20,
                
                x=e.local_x,
                y=e.local_y,
                start_angle=math.pi,
                sweep_angle=-math.pi,
            )
            self.current_path.elements.append(arc_element)
            self.state.paths[0]['elements'].append((arc_element.__dict__))

        # Else if we're using arcto, add that element to the current path and state right away
        elif style == 'arcto' or style == 'arctofill':
            arc_element = cv.Path.ArcTo(
                radius=12,
                rotation=0,
                large_arc=False,
                x=e.local_x,
                y=e.local_y,
                clockwise=True,
            )
            self.current_path.elements.append(arc_element)
            self.state.paths[0]['elements'].append((arc_element.__dict__))

        # Add the path to the canvas so we can see it
        e.control.parent.shapes.append(self.current_path)


        
    # Called when actively drawing on the canvas
    async def is_drawing(self, e: ft.DragUpdateEvent):
        ''' Creates our line to add to the canvas as we draw, and saves that paths data to self.state '''

        # Grab our style so we can compare it
        style = str(app.settings.data.get('paint_settings', {}).get('style', 'stroke'))


        # Handle lineto (Straight lines). Grab the element we created on start drawing, update its data
        if style == "lineto":
            
            # Set the element and its data
            line_element = self.current_path.elements[-1]
            line_dict = line_element.__dict__

            # Update the elements position
            line_element.x = e.local_x
            line_element.y = e.local_y

            # Update the dict to match
            line_dict['x'] = line_element.x
            line_dict['y'] = line_element.y

            # Update the page and return early
            try:
                # Page reference gets lost after dragging widget to new canvas, so we reset it and update
                e.control.parent.update()
            except Exception as ex:
                print("Failed to update e.control")
                self.p.update()
            return
        
        if style == "arc" or style == "arcfill":
            
            # Set the element and its data
            arc_element = self.current_path.elements[-1]
            arc_dict = arc_element.__dict__

        

            # Swap directions of arc depending if we drag up or down from starting point
            if e.local_y - self.state.y >= 0:   # Dragging down
                arc_element.sweep_angle = -math.pi
                arc_element.height = abs(self.state.y - e.local_y)
                arc_element.y = self.state.y - (arc_element.height / 2)
                
            else:       # Dragging up
                
                arc_element.sweep_angle = math.pi
                arc_element.height = abs(e.local_y - self.state.y)
                arc_element.y = abs(self.state.y - (arc_element.height / 2))

            arc_element.width = abs(e.local_x - self.state.x) 
        
            # Update the page and return early
            try:
                # Page reference gets lost after dragging widget to new canvas, so we reset it and update
                e.control.parent.update()   
            except Exception as ex:
                print("Failed to update e.control")
                self.p.update()


            return
        
        # Handle arcs
        if style == 'arcto' or style == 'arctofill':
            
            arc_element = self.current_path.elements[-1]
            arc_dict = arc_element.__dict__

            arc_element.x = e.local_x
            arc_element.y = e.local_y
        

            arc_dict['x'] = arc_element.x
            arc_dict['y'] = arc_element.y

            # Update the page and return early
            try:
                # Page reference gets lost after dragging widget to new canvas, so we reset it and update
                e.control.parent.update()
            except Exception as ex:
                print("Failed to update e.control")
                self.p.update()
            return
        
        
        # If its not one of our custom styles, use free-draw stroke, which is constantly adding line_to segements
        else:

            #TODO: Add check here to reduce num of lines based on previous start and edn
            # Set the path element based on what kind of path we're adding, add it to our current path and our state paths
            path_element = cv.Path.LineTo(e.local_x, e.local_y)

            # Add the declared element to our current path and state paths
            self.current_path.elements.append(path_element)
            self.state.paths[0]['elements'].append((path_element.__dict__))  

            # After dragging canvas widget, it loses page reference and can't update
            try:
                # Page reference gets lost after dragging widget to new canvas, so we reset it and update
                e.control.parent.update()
            except Exception as ex:
                print("Failed to update e.control")
                self.p.update()
            

            # Update our state x and y for the next segment
            self.state.x, self.state.y = e.local_x, e.local_y

    def _on_canvas_resize(self, e: cv.CanvasResizeEvent):
        ''' Called when our canvas resizes '''

        #print("Canvas resized to: ", e.width, e.height)
        

    # Called when we release the mouse to stop drawing a line
    def save_canvas(self, row: int, column: int):
        """ Saves our paths to our canvas data for storage """

        # Save our paths annd points to the correct cell in our matrix
        canvas_data = self.data['matrix'][row][column]
        canvas_data['paths'].extend(self.state.paths)
        canvas_data['points'].extend(self.state.points)

        self.p.run_task(self.save_dict)

        # Clear the current state, otherwise it constantly grows and lags the program
        self.state.paths.clear()
        self.state.points.clear()

    # Called when we click to add a new row at the bottom of our matrix
    def _new_row_clicked(self, e=None):
        ''' Adds an empty new row to our matrix data and reloads the widget '''

        # Create a new row with default values for each column
        new_row = []
        for label in self.data['matrix_labels']:
            match label:
                case "Preview":
                    new_row.append("")    # Empty string for canvas key
                case "Sketch":
                    new_row.append({
                        'paths': [],
                        'shadow_paths': [],
                        'points': [],
                    })
                case "Concept" | _:
                    new_row.append("")

        # Add the new row to our matrix data
        self.data['matrix'].append(new_row)
        self.p.run_task(self.save_dict)

        # Reload our widget to reflect changes
        self.reload_widget()

    def _delete_row_clicked(self, row: int):
        ''' Deletes a specific row from our matrix data and reloads the widget '''

        if 0 <= row < len(self.data['matrix']):
            del self.data['matrix'][row]
            self.p.run_task(self.save_dict)
            self.reload_widget()

    def _new_column_clicked(self, e=None):  
        ''' Adds a new column to our matrix data and reloads the widget '''

        def _create_field(e): #show in edit view
            '''Called when user confirms the field name'''
            
            if field_name_input.value:
                self.data['matrix_labels'].append(field_name_input.value)
            
            for row in self.data['matrix']:
                row.append("")   # Default empty string for new column
            
            # Save and reload
            self.p.run_task(self.save_dict)
            self.p.pop_dialog()
            self.reload_widget()
        
        # Create a dialog to ask for the field name
        field_name_input = ft.TextField(
            label="Field Name", hint_text=f"New Column Label",
            autofocus=True, capitalization=ft.TextCapitalization.SENTENCES,
            on_submit=_create_field,     # Closes the overlay when submitting
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Create New Column"),
            content=field_name_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.p.pop_dialog(), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
                ft.TextButton("Create", on_click=_create_field),
            ],
        )
        
        self.p.show_dialog(dlg)

    def _delete_column_clicked(self, column: int):
        ''' Deletes a specific column from our matrix data and reloads the widget '''

        if 0 <= column < len(self.data['matrix_labels']):
            # Remove the label
            del self.data['matrix_labels'][column]

            # Remove the column from each row
            for row in self.data['matrix']:
                if 0 <= column < len(row):
                    del row[column]

            self.p.run_task(self.save_dict)
            self.reload_widget()
    
    async def _show_preview_buttons(self, e: ft.PointerEvent):

        gd = e.control
        for control in gd.content.controls:
            if not control.visible:
                control.visible = True
        gd.update()

    async def _hide_preview_buttons(self, e: ft.PointerEvent):
        gd = e.control
        for control in gd.content.controls:
            if isinstance(control, cv.Canvas):
                continue
            if control.visible:
                control.visible = False
        gd.update()

    def _connect_canvas_clicked(self, row: int, column: int):

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

            self.story.blocker.visible = True
            self.story.blocker.update()
            await asyncio.sleep(0)
            self.p.pop_dialog()

            # Set the new key to our data and save
            self.data['matrix'][row][column]['canvas_key'] = canvas_key
            self.data['matrix'][row][column]['snapshot'] = self._set_canvas_snapshot(canvas_key)
            await self.save_dict()

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
    def _set_canvas_snapshot(self, canvas_key: str) -> list:

        capture_list = []
        for widget in self.story.widgets:
            if widget.data['key'] == canvas_key:
                for layer in widget.data.get('canvas_data', {}).get('Layers', []):
                    if layer.get('capture', ""):
                        capture_list.append(layer['capture'])
                break

        return capture_list
    


    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        description_container = ft.Container(            # For Summary
            padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(5), expand=True,
            border=ft.Border.all(2, ft.Colors.OUTLINE), margin=ft.Margin.only(right=19),
            content=ft.TextField(
                expand=True, value=self.data.get('description', ""), dense=True, multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES, 
                on_blur=lambda e: self.change_data(**{'description': e.control.value}),
                border=ft.InputBorder.NONE,                  
            ),
        )

        def _get_label_controls() -> list[ft.Control]:
            ''' Formats our labels insto text controls above our grid '''
            controls = [ft.Container(width=38)]

            for idx, label in enumerate(self.data['matrix_labels']):
                controls.append(
                    ft.Container(
                        ft.Text(
                            label, style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")), selectable=True,
                            tooltip="Connect to one of your canvases and show a live preview of your progress!" if label == "Preview" else None,
                        ),
                        alignment=ft.Alignment.CENTER, margin=ft.Margin.symmetric(horizontal=12),    
                        width=201 if idx <=1 else None,
                        expand=True if idx > 1 else False,
                    )
                )

                if idx == len(self.data['matrix_labels']) - 1:
                    controls.append(
                        ft.IconButton(
                            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, 
                            on_click=self._new_column_clicked,
                            tooltip="Add new column",
                        )
                    )
                    controls.append(ft.Container(width=12))
                    
            return controls
        

        # Lays out our controls in a nice grid format
        def _get_grid_controls() -> list[ft.Control]:

            controls = []
            for idx, row in enumerate(self.data['matrix']):
                
                # Establish a row control we will add our cells to
                row_control = ft.Row(spacing=0, expand=True, controls=[ft.Container(width=38)], height=180)

                for sub_idx, cell in enumerate(row):

                    # Check our index against our label
                    label = self.data['matrix_labels'][sub_idx]

                    # Depending on our label, the content of our container will be differnt.
                    # Either image with preview of canvas, sketch canvas, or text area for concept
                    match label:
                        case "Preview":     # Preview of the canvas we're tied too

                            canvas = cv.Canvas(
                                height=180, width=180
                            )
                            for capture in cell.get('snapshot', []):
                                canvas.shapes.append(
                                    cv.Image(capture, 0, 0, 200, 200)
                                )
                            widget_key = cell.get('canvas_key', "")
                            for widget in self.story.widgets:
                                if widget.data['key'] == widget_key:
                                    canvas_title = widget.title
                                    canvas_color = widget.data.get('color', None)
                                    break
                            row_control.controls.append(
                                ft.Column([
                                    ft.Text(canvas_title if canvas_title else "", color=canvas_color if canvas_color else None, height=20),
                                    ft.Container(
                                        ft.GestureDetector(
                                            ft.Stack([
                                                # Canvas preview
                                                canvas if cell.get('canvas_key', "") else ft.Container(ignore_interactions=True, height=180, width=180), 


                                                
                                                # Connect button to tie this cell to a specific canvas
                                                ft.TextButton(
                                                    "Connect Canvas", top=10,
                                                    style=ft.ButtonStyle(color=ft.Colors.ON_SURFACE, mouse_cursor=ft.MouseCursor.CLICK),
                                                    visible=False, on_click=lambda e, r=idx, c=sub_idx: self._connect_canvas_clicked(r, c)
                                                ),
                                            
                                                # Refresh the preview button
                                                ft.IconButton(
                                                    ft.Icons.REFRESH, ft.Colors.PRIMARY,
                                                    tooltip="Refresh preview", #on_click=lambda e, r=idx, c=sub_idx: self.reload_widget()
                                                    mouse_cursor="click",
                                                    visible=False,
                                                ) if cell.get('canvas_key', "") else ft.Container(ignore_interactions=True),   # Only show refresh button if we're already tied to a canvas

                                                # Disconnect the canvas button
                                                ft.TextButton(
                                                    "Disconnect Canvas", bottom=10,
                                                    style=ft.ButtonStyle(color=ft.Colors.ON_SURFACE, mouse_cursor=ft.MouseCursor.CLICK),
                                                    visible=False,
                                                ) if cell.get('canvas_key', "") else ft.Container(ignore_interactions=True),
                                            ], alignment=ft.Alignment.CENTER),
                                            on_enter=self._show_preview_buttons, on_exit=self._hide_preview_buttons
                                            
                                        ),
                                        alignment=ft.Alignment.CENTER,
                                        margin=ft.Margin.only(bottom=12, left=12, right=12),
                                        border_radius=ft.BorderRadius.all(6),
                                        width=180,  height=180,
                                        border=ft.Border.all(1, ft.Colors.OUTLINE),
                                    )
                                ], spacing=0)
                            )
                        case "Sketch":      # Sketch canvas for rough thumbnails
                            canvas = cv.Canvas(
                                content=ft.GestureDetector(
                                    mouse_cursor=ft.MouseCursor.PRECISE,
                                    on_pan_start=self.start_drawing,
                                    on_pan_update=self.is_drawing,
                                    on_pan_end=lambda e, r=idx, c=sub_idx: self.save_canvas(r, c),
                                    on_tap_up=lambda e, r=idx, c=sub_idx: self.add_point(r, c, e),      # Handles so we can add points
                                    drag_interval=10, expand=True
                                ),
                                expand=True, width=180,
                                #resize_interval=100,
                                shapes=[], #on_resize=self._on_canvas_resize, 
                            )
                            row_control.controls.append(
                                ft.Container(
                                    canvas, margin=ft.Margin.all(12), #border=ft.border.all(1, ft.Colors.OUTLINE),
                                    bgcolor="surface", border_radius=ft.BorderRadius.all(6),
                                    alignment=ft.Alignment.TOP_CENTER, 
                                )
                            )
                            canvas.shapes.extend(self._load_canvas(idx, sub_idx))   # Load our saved canvas data into the canvas

                        case "Concept" | _:     # Text description of the idea and any custom fields they added
                            row_control.controls.append(
                                ft.Container(
                                    ft.TextField(
                                        str(cell), focused_border_color=self.data.get('color', None), cursor_color=self.data.get('color', None),
                                        dense=True, multiline=True, expand=True, #border=ft.InputBorder.NONE,
                                        capitalization=ft.TextCapitalization.SENTENCES, smart_dashes_type=True,
                                        on_blur=lambda e, r=idx, c=sub_idx: self._update_matrix_cell(r, c, e.control.value)
                                    ), 
                                    expand=True, margin=ft.Margin.all(12), alignment=ft.Alignment.TOP_CENTER,
                                )
                            )
                        
                    # Add a divider between columns except for last one
                    if sub_idx != len(row) - 1:
                        row_control.controls.append(ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.OUTLINE))
                    else:
                        row_control.controls.append(
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,
                                tooltip="Delete row",
                                on_click=lambda e, r=idx: self._delete_row_clicked(r),
                            )
                        )
                        row_control.controls.append(ft.Container(width=12))  # Spacing at end
                   
                # Add our row control
                controls.append(row_control)

                # Add a divider between rows except for last one, we add the 'add row' button
                if idx != len(self.data.get('matrix', [])) - 1: 
                    controls.append(ft.Divider(height=1, thickness=1, leading_indent=50, trailing_indent=50, color=ft.Colors.OUTLINE))
                else:

                    # Declare a row for our add and delete buttons
                    row = ft.Row(
                        spacing=0, expand=True,
                        controls=[
                            ft.IconButton(
                                ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, 
                                on_click=self._new_row_clicked,
                                tooltip="Add new row",
                            ), 
                            ft.Container(width=448),     # Spacer over the first two columns, so we don't delete them
                          
                        ], 
                    )
                    
                    sub_row = ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_AROUND, expand=True, spacing=0,
                        controls=[]
                    )

                    # Add delete buttons under each column that is custom (not preview, sketch, or concept)
                    if len(self.data['matrix_labels']) > 3:
                        
                        for i in range(len(self.data['matrix_labels']) - 2):
                            if i == 0:
                                sub_row.controls.append(ft.Container(width=38))
                            
                            else:
                                sub_row.controls.append(
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.ERROR,
                                    tooltip="Delete column", expand=False, width=38,
                                    on_click=lambda e, c=(i + 2): self._delete_column_clicked(c),
                                )
                            )

                            
                    else:
                        sub_row.controls.append(ft.Container(expand=True))

                    row.controls.append(sub_row)
                    # Spacing at the end
                    row.controls.append(ft.Container(width=50))
                    

                    # Add our row to the bottom
                    controls.append(row)

                    

            return controls

        

        # Body of the tab, which is the content of flet container
        body = ft.Container(
            expand=True,               
            padding=6,                 
            content=ft.Column(
                spacing=0, expand=True, scroll="auto", 
                controls=[                 
                
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Container(height=10),

                    ft.Row([description_container]),
                    ft.Container(height=10),

                    ft.Row(_get_label_controls(), expand=True, spacing=0)
            ])
        )    


        body.content.controls.extend(_get_grid_controls())

        self.body_container.content = body

        # TODO: Add undo-redo buttons like our canvas has for our sketches

        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


