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
                # Preview -> Ties to a specific Canvas and shows a preview of that Canvas in real time
                'matrix_labels': ["Preview", "Sketch", "Concept"],   

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
                        ""              # Concept description text
                    ],      
                    [           # Second row
                        {       # First Column
                            'preview_canvas_key': "",      
                            'preview_canvas_title': "",    
                            'preview_canvas_color': "",    
                            "preview_canvas_snapshot": "",         
                        },         
                        "",   # Second column
                        ""      # Third column
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
            self.p.update()
            
            
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

        # Check if we're in erase mode or not. If we are, set blend mode to clear and blur image to 0
        if self.story.data.get('canvas_settings', {}).get('erase_mode', False):
            safe_paint_settings['blend_mode'] = "clear"
            safe_paint_settings['blur_image'] = 0
            state_paint_settings['blend_mode'] = "clear"
            state_paint_settings['blur_image'] = 0
        

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
                        "preview_canvas_snapshot": [],     
                    })    
                
                case "Concept" | "Sketch" | _:
                    new_row.append("")

        # Add the new row to our matrix data
        self.data['matrix'].append(new_row)
        self.p.run_task(self.save_dict)

        # Reload our widget to reflect changes
        self.reload_widget()

    async def _delete_row_clicked(self, e):
        ''' Deletes a specific row from our matrix data and reloads the widget '''

        row = e.control.data.get('row') 

        if 0 <= row < len(self.data['matrix']):
            del self.data['matrix'][row]
            self.p.run_task(self.save_dict)
            self.reload_widget()

    async def _new_column_clicked(self, e=None):  
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

            # Start with invisible button to keep spacing
            controls = [ft.IconButton(ft.Icons.ADD, opacity=0, disabled=True)]

            # Add each label as a text control
            for idx, label in enumerate(self.data['matrix_labels']):
                controls.append(
                    ft.Text(
                        label, style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")), selectable=True,
                        tooltip="Connect to one of your canvases and show a live preview of your progress!" if label == "Preview" else None,
                        width=250, text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS
                    )
                )
                if idx < len(self.data['matrix_labels']) - 1:
                    controls.append(ft.Container(width=1)) # Spacing between labels
                elif idx == len(self.data['matrix_labels']) - 1:
                    controls.append(ft.Container(expand=True)) # Push new column button to the end

            # Add button for new columns
            controls.append(
                ft.IconButton(
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, 
                    on_click=self._new_column_clicked,
                    tooltip="Add new column",
                )
            )
            controls.append(ft.Container(width=10)) # Spacing away from scroll bar
                    
            return controls
        

        # Lays out our controls in a nice grid format
        def _get_grid_controls() -> list[ft.Control]:

            # TODO: Popupmenubutton for connect/disconnect, hover/click to refresh

            controls = []

            # Go through our "rows" in the matrix data
            for idx, row in enumerate(self.data['matrix']):
                
                # Establish a row control we will add our cells to
                row_control = ft.Row([ft.IconButton(ft.Icons.ADD, opacity=0, disabled=True)], spacing=0, height=250, vertical_alignment=ft.CrossAxisAlignment.CENTER)

                # For each cell in the row
                for sub_idx, cell in enumerate(row):

                    # Match our cell for which column it should be under
                    label = self.data['matrix_labels'][sub_idx]

                    match label:

                        # Build a preview for a connectted canvas
                        # TODO: Wrap canvas in container that clicking refreshes
                        case "Preview":     
                                
                            # Set a canvas just to display
                            preview_image = ft.Image(
                                cell.get('snapshot', ""), ft.Text("Failed to grab preview snapshot"),
                                height=200, width=200, fit=ft.BoxFit.COVER, #border_radius=ft.BorderRadius.all(6),
                            ) if cell.get('snapshot', "") else ft.Container(
                                #ft.Text("No Canvas Connected", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                                #border=ft.Border.all(1, ft.Colors.OUTLINE), border_radius=ft.BorderRadius.all(6),
                               width=200, height=200, alignment=ft.Alignment.TOP_CENTER
                            )
                            # Other attributes about the canvas we're using
                            canvas_key = cell.get('canvas_key', "")
                            canvas_title = cell.get('canvas_title', "")
                            canvas_color = cell.get('canvas_color', ft.Colors.OUTLINE)

                            connected_canvas_button = ft.PopupMenuButton(
                                canvas_title if canvas_title else ft.Text("No Canvas Connected", color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
                                [
                                    ft.PopupMenuItem(
                                        "Connect Canvas", ft.Icons.LINK_OUTLINED,
                                        on_click=lambda e, r=idx, c=sub_idx: self._connect_canvas_clicked(r, c),
                                        mouse_cursor=ft.MouseCursor.CLICK,
                                    ),
                                    ft.PopupMenuItem(
                                        "Refresh Preview", ft.Icons.REFRESH_OUTLINED,
                                        #on_click=lambda e, r=idx, c=sub_idx: self._refresh_preview(r, c),
                                        mouse_cursor=ft.MouseCursor.CLICK,
                                    ),
                                    ft.PopupMenuItem(
                                        "Disconnect Canvas", ft.Icons.LINK_OFF_OUTLINED,
                                        #on_click=lambda e, r=idx, c=sub_idx: self._disconnect_canvas(r, c),
                                        mouse_cursor=ft.MouseCursor.CLICK,
                                    )
                                ],
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK)
                            )

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
                                    padding=ft.Padding.all(12), width=250, height=250, alignment=ft.Alignment.BOTTOM_CENTER
                                )
                            )

                        # Build a sketch canvas for this row
                        case "Sketch":      # Sketch canvas for rough thumbnails
                            sketch_canvas = cv.Canvas(
                                content=ft.GestureDetector(
                                    mouse_cursor=ft.MouseCursor.PRECISE,
                                    on_pan_start=self.start_drawing,
                                    on_pan_update=self.is_drawing,
                                    on_pan_end=lambda e, r=idx, c=sub_idx: self.save_canvas(r, c),
                                    on_tap_up=lambda e, r=idx, c=sub_idx: self.add_point(r, c, e),      # Handles so we can add points
                                    drag_interval=10, expand=True
                                ),
                                expand=True, width=200, height=200,
                                shapes=[ft.Image(cell, 0, 0, 200, 200)],
                            )
                            row_control.controls.append(
                                ft.Container(
                                    ft.Container(
                                        sketch_canvas, border=ft.Border.all(1, ft.Colors.OUTLINE),
                                        bgcolor="surface", border_radius=ft.BorderRadius.all(6),
                                        #alignment=ft.Alignment.TOP_CENTER, #width=200, height=200,
                                    ), padding=ft.Padding.all(12), width=250, height=250, alignment=ft.Alignment.BOTTOM_CENTER
                                )
                            )
                            #preview_canvas.shapes.extend(self._load_canvas(idx, sub_idx))   # Load our saved canvas data into the canvas

                        # Build either textfield for all other types of columns
                        case "Concept" | _:     
                            row_control.controls.append(
                                ft.Container(
                                    ft.TextField(
                                        str(cell), #focused_border_color=self.data.get('color', None), cursor_color=self.data.get('color', None),
                                        dense=True, multiline=True, #expand=True, #border=ft.InputBorder.NONE,
                                        capitalization=ft.TextCapitalization.SENTENCES, smart_dashes_type=True,
                                        on_blur=lambda e, r=idx, c=sub_idx: self._update_matrix_cell(r, c, e.control.value)
                                    ), 
                                    padding=ft.Padding.all(12), width=250, height=250
                                )
                            )
                        
                    # Add a divider between columns except for last one
                    if sub_idx != len(row) - 1:
                        row_control.controls.append(ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.OUTLINE))
                        
                    else:
                        row_control.controls.append(ft.Container(expand=True)) # Push delete button to the end
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
            


