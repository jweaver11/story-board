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
import base64
from io import BytesIO
from PIL import Image


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
                # Preview -> Ties to a specific Canvas and shows a preview of that Canvas in real time
                'matrix_labels': ["Preview", "Sketch", "Concept", "Notes"],   

                # Our main data matrix for this canvas board
                'matrix': [
                    [           # First row
                        {       # First Column
                            'preview_canvas_key': "",      # Key to the canvas we are tied too
                            'preview_canvas_title': "",    # Title of the canvas we're tied to, for easy reference
                            'preview_canvas_color': "",    # Color of the canvas we're tied to, for easy reference
                            "preview_canvas_snapshot": "",         # Snapshot of the canvas for previewing
                        },         
                        "",             # Sketch capture to be loaded into canvas
                        "",             # Concept description text
                        ""              # Notes for is row
                    ],      
                    [           # Second row
                        {       # First Column
                            'preview_canvas_key': "",      
                            'preview_canvas_title': "",    
                            'preview_canvas_color': "",    
                            "preview_canvas_snapshot": "",         
                        },         
                        "",   # Second column
                        "",      # Third column
                        ""      # Fourth column
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
    def _update_matrix_cell(self, e):
        ''' Updates a specific cell in our matrix data '''
        
        row = e.control.data.get('row')
        column = e.control.data.get('column')
        value = e.control.value

        if isinstance(value, str):
            self.data['matrix'][row][column] = value
            self.p.run_task(self.save_dict)


    # Called when we click the canvas and don't initiate a drag
    async def add_point(self, e: ft.TapEvent):
        ''' Adds a point to the canvas if we just clicked and didn't initiate a drag '''

        row = e.control.data.get('row')
        column = e.control.data.get('column')

        # Create the point using our paint settings and point mode
        point = cv.Points(
            points=[(e.local_position.x, e.local_position.y)],
            paint=ft.Paint(**app.settings.data.get('paint_settings', {})),
        )
        
        # Add point to the canvas and our state data
        e.control.parent.shapes.append(point)
        self.state.points.append((e.local_position.x, e.local_position.y, point.point_mode, point.paint.__dict__))

        # After dragging canvas widget, it loses page reference and can't update
        try:
            e.control.parent.update()
            
        except Exception as _:
            print("Failed to update e.control")
            
            
        # Save our canvas data
        self.save_canvas(row, column)
        
    # Called when we start drawing on the canvas
    async def start_drawing(self, e: ft.DragStartEvent):
        ''' Set our initial starting x and y coordinates for the element we're drawing '''

        # Grab our style so we can compare it
        style = str(app.settings.data.get('paint_settings', {}).get('style', 'stroke'))

        # Make a copy of our paint settings to modify it, since some of the styles are not built in
        safe_paint_settings = ft.Paint(ft.Colors.ON_SURFACE, stroke_width=2, stroke_cap=ft.StrokeCap.ROUND)

        # Copy of our paint settings for our state tracking and data storage (only erase mode needs this)
        state_paint_settings = ft.Paint(ft.Colors.ON_SURFACE, stroke_width=2, stroke_cap=ft.StrokeCap.ROUND)

        # Set either stroke or fill based on custom styles
        safe_stroke = 'fill' if style.endswith('fill') else 'stroke'
        safe_paint_settings['style'] = safe_stroke

        
        

        # Update state x and y coordinates
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

        # Clear and set our current path and state to match it
        self.current_path = cv.Path(elements=[], paint=ft.Paint(ft.Colors.ON_SURFACE, stroke_width=2, stroke_cap=ft.StrokeCap.ROUND))
        self.state.paths.clear()
        self.state.paths.append({'elements': list(), 'paint': state_paint_settings})

        # Set move to element at our starting position that the mouse is at for the path to start from
        move_to_element = cv.Path.MoveTo(e.local_position.x, e.local_position.y)

        # Add that element to current paths elements and our state paths
        self.current_path.elements.append(move_to_element)
        self.state.paths[0]['elements'].append((move_to_element.__dict__))

        #print(f"Starting drawing with style {style}")

        # If we're using lineto (straight lines), add that element to the current path and state right away
        if style == "lineto":
            line_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)
            self.current_path.elements.append(line_element)
            self.state.paths[0]['elements'].append((line_element.__dict__))

        elif style == "arc":
            arc_element = cv.Path.Arc(
                width=20,
                height=20,
                
                x=e.local_position.x,
                y=e.local_position.y,
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
                x=e.local_position.x,
                y=e.local_position.y,
                clockwise=True,
            )
            self.current_path.elements.append(arc_element)
            self.state.paths[0]['elements'].append((arc_element.__dict__))

        # Add the path to the canvas so we can see it
        e.control.parent.shapes.append(self.current_path)


        
    # Called when actively drawing on the canvas
    async def is_drawing(self, e: ft.DragUpdateEvent):
        ''' Creates our line to add to the canvas as we draw, and saves that paths data to self.state '''

        ft.Paint(ft.Colors.ON_SURFACE, stroke_width=2, stroke_cap=ft.StrokeCap.ROUND)
        

        #TODO: Add check here to reduce num of lines based on previous start and edn
        # Set the path element based on what kind of path we're adding, add it to our current path and our state paths
        path_element = cv.Path.LineTo(e.local_position.x, e.local_position.y)

        # Add the declared element to our current path and state paths
        self.current_path.elements.append(path_element)
        self.state.paths[0]['elements'].append((path_element.__dict__))  

        # After dragging canvas widget, it loses page reference and can't update
        try:
            # Page reference gets lost after dragging widget to new canvas, so we reset it and update
            self.current_path.update()
        except Exception as _:
            e.control.parent.update()
        

        # Update our state x and y for the next segment
        self.state.x, self.state.y = e.local_position.x, e.local_position.y
        

    # Called when we release the mouse to stop drawing a line
    async def save_canvas(self, e: ft.DragEndEvent):
        """ Saves our paths to our canvas data for storage """
        row = e.control.data.get('row')
        column = e.control.data.get('column')

        # Save our paths annd points to the correct cell in our matrix
        canvas_data = self.data['matrix'][row][column]
        canvas_data['paths'].extend(self.state.paths)
        canvas_data['points'].extend(self.state.points)

        self.p.run_task(self.save_dict)

        # Clear the current state, otherwise it constantly grows and lags the program
        self.state.paths.clear()
        self.state.points.clear()

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
                
                case _:
                    new_row.append("")

        self.story.blocker.visible = True
        self.story.blocker.update()
        await asyncio.sleep(0)

        # Add the new row to our matrix data
        self.data['matrix'].append(new_row)
        self.p.run_task(self.save_dict)

        self.story.workspace.reload_workspace()
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
            self.p.run_task(self.save_dict)

            self.story.workspace.reload_workspace()
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


            self.p.run_task(self.save_dict)
            
            self.story.workspace.reload_workspace()
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

            self.story.workspace.reload_workspace()

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
        await self.save_dict()

        self.story.workspace.reload_workspace()
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
        await self.save_dict()

        self.story.workspace.reload_workspace()

        self.story.blocker.visible = False
        self.story.blocker.update()
    


    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        description_container = ft.TextField(
            expand=True, value=self.data.get('description', ""), dense=True, multiline=True,
            capitalization=ft.TextCapitalization.SENTENCES, 
            on_blur=lambda e: self.p.run_task(self.change_data, **{'description': e.control.value}),
            border_color=ft.Colors.OUTLINE_VARIANT,                  
        
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
                        sketch_canvas = cv.Canvas(
                            content=ft.GestureDetector(
                                mouse_cursor=ft.MouseCursor.PRECISE,
                                on_pan_start=self.start_drawing,
                                on_pan_update=self.is_drawing,
                                on_pan_end=self.save_canvas,
                                on_tap_up=self.add_point,      # Handles so we can add points
                                drag_interval=10,
                                data={"row": idx, "column": sub_idx},
                            ),
                            width=200, height=200,
                            shapes=[ft.Image(cell, 0, 0, 200, 200)],
                        )
                        row_control.controls.append(
                            ft.Container(
                                ft.Column([
                                    ft.Container(height=40),
                                    ft.Container(
                                        sketch_canvas, border=ft.Border.all(1, ft.Colors.OUTLINE),
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
            
                ft.Row([
                    ft.Container(width=6), 
                    ft.Text("Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                ], spacing=0),
                ft.Container(height=10), 

                ft.Row([description_container]),
                ft.Container(height=10), 
                
                matrix_labels,
                ft.Divider(2, 2),
                        
                matrix_grid_view,
                ft.Container(height=10), 
                
                ft.Row([
                    ft.TextButton(
                        "Add New Row",
                        ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, 
                        on_click=self._new_row_clicked,
                        style=ft.ButtonStyle(self.data.get('color', ft.Colors.PRIMARY), icon_size=20, mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                    ),
                    ft.Container()
                ], vertical_alignment=ft.CrossAxisAlignment.START)
                

            ])
    

        self.body_container.content = body

        # TODO: Add undo-redo buttons like our canvas has for our sketches

        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


