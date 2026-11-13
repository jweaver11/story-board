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
import utils.drawing as drawing
import os
import flet_shadcn_ui as shad
from styles.highlight_button import HighlightButton
from styles.colors import colors

MINIMUM_SEGMENT_DISTANCE = 2
MAX_SHAPES_BEFORE_CAPTURE = 50
MAX_UNDO_LIST_TASKS = 30
SKETCH_SIZE = (500, 500)


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

                # Our panels data 
                'panels': [
                    {
                        'canvas_id': "",    # ID of the canvas we're attached to, if we're attached to one. This will go grab the bytes of that canvas
                        'capture': "",    # Base64 string of the capture if not attached to canvas. Use this if no canvas_id is provided
                        'description': "",    # Description of the panel
                        'locked': False,    # Whether this panel is locked and cannot be drawn on
                        'dirty': False,      # State tracking - Whether this row's sketch has unsaved changes
                    }
                ],
            },
        )



        self.state: State = State()     # State model from tracking our drawing state
        self.active_path: cv.Path

        self.panels_row: ft.Row
        self.canvases_list: list[cv.Canvas] = []

    # Overwrite our standard save_file call since we have multiple files
    async def save_file(self):
        # Protect on creation
        #if not self.content:
            #return

        for i, panel_data in enumerate(self.data.get('panels', [])):
            # If a change has been made to the row, save that change.
            if panel_data.get('dirty', False) == True:
                canvas: cv.Canvas = self.canvases_list[i]
                if not isinstance(canvas, cv.Canvas):
                    print(canvas)
                    continue
                try:
                    await self.save_canvas(canvas)
                except RuntimeError as e:
                    print(f"Error saving row {i}: {e}")
                    return
                self.needs_file_write = True    # Mark our widget as dirty if we saved anything

        await super().save_file()   
    

    # Called when we release the mouse to stop drawing a line
    async def save_canvas(self, canvas: cv.Canvas):
        """ Saves our paths to our canvas data for storage """
        
        # Protect bad calls
        if canvas.visible == False:  
            return

        panel_idx = canvas.data
        panel_data = self.data.get('panels', [])[panel_idx]
        
                
        # Clear blend strokes must be captured with the stored image so they can remove
        # pixels from the existing layer instead of being alpha-composited on top of it.
        shapes = list(canvas.shapes)
        base_is_stored_image = shapes and isinstance(shapes[0], cv.Image) and shapes[0].data    # Marked as loaded
        new_strokes = shapes[1:] if base_is_stored_image else shapes
        has_clear_stroke = any(
            str(getattr(getattr(shape, 'paint', None), 'blend_mode', '')).lower().endswith('clear')
            for shape in new_strokes
        )
        capture_shapes = shapes if has_clear_stroke else new_strokes

        # Capture the appropriate layer content, then restore the original shapes to the canvas
        canvas.shapes[:] = capture_shapes
        canvas.update()

        await canvas.capture()
        new_bytes = await canvas.get_capture()
        await canvas.clear_capture()
        canvas.shapes[:] = shapes  # Restore the original shapes to the canvas
        canvas.update()

        # Error capturing new strokes (should be impossible)
        if not new_bytes:
            self.page.show_dialog(SnackBar(f"Error capturing new strokes for sketch."))
            return

        # A full capture already contains the erase result and must replace the old layer.
        if has_clear_stroke:
            result = Image.open(BytesIO(new_bytes)).convert("RGBA")
            if result.size != SKETCH_SIZE:
                result = result.resize(SKETCH_SIZE, Image.Resampling.LANCZOS)
            output = BytesIO()
            result.save(output, format="PNG")
            combined_bytes = output.getvalue()
            

            panel_data['dirty'] = False
            self.data.get('canvas_data', {}).get('layers', [])[panel_idx].update(panel_data)
            self.update_data(**{'panels': self.data.get('panels', [])})
            return combined_bytes

        # Load the existing layer capture
        str_bytes = panel_data.get('capture', None)
        existing_bytes = base64.b64decode(str_bytes.split(",")[1]) if str_bytes else None
        

        # If we have an existing capture, composite the new strokes onto it; otherwise, create a new base image
        if existing_bytes:
            base_img = Image.open(BytesIO(existing_bytes)).convert("RGBA")
            if base_img.size != SKETCH_SIZE:
                base_img = base_img.resize(SKETCH_SIZE, Image.Resampling.LANCZOS)
        else:
            base_img = Image.new("RGBA", SKETCH_SIZE, (0, 0, 0, 0))

        # Composite the new strokes onto the existing base — base pixels are never re-rendered through Flet
        delta_img = Image.open(BytesIO(new_bytes)).convert("RGBA")
        if delta_img.size != base_img.size: # Handle size errors (should be impossible)
            delta_img = delta_img.resize(base_img.size, Image.Resampling.LANCZOS)

        # Merge the two images together and add them to our in memory cache for the next save
        result = Image.alpha_composite(base_img, delta_img)
        output = BytesIO()
        result.save(output, format="PNG")
        combined_bytes = output.getvalue()
        str_img = f"data:image/png;base64,{base64.b64encode(combined_bytes).decode('utf-8')}"

        panel_data['capture'] = str_img
        panel_data['dirty'] = False
        self.data.get('panels', [])[panel_idx] = panel_data
        self.update_data(**{'panels': self.data.get('panels', [])})  # Update our data so it saves the new row

        return combined_bytes   # Return our now updated bytes


    async def add_point(self, e: ft.TapEvent):
        paint_settings = app.settings.data.get('paint_settings', {}).copy()
        
        # Grab our canvas
        canvas: cv.Canvas = e.control.parent
        await drawing.draw_point(canvas, e.local_position)
        self.current_path = cv.Points(points=[(e.local_position.x, e.local_position.y)], paint=ft.Paint(**paint_settings))
        await self.end_stroke(e)   # Force a stroke end since it wont have pan end events

    # Adds our initial stroke (cv.Shape) to the canvas with correct settings
    def start_stroke(self, e: ft.DragStartEvent):

        # Grab our canvas and update state
        canvas: cv.Canvas = e.control.parent

        drawing.start_stroke(canvas=canvas, current_position=e.local_position, prev_position=ft.Offset(self.state.x, self.state.y))
        # Update our state x and y coordinates
        self.state.x, self.state.y = e.local_position.x, e.local_position.y

    # Updates the current stroke shape on the canvas depending on our settings
    def update_stroke(self, e: ft.DragUpdateEvent):

        # Grab canvas and catch errors
        canvas: cv.Canvas =  e.control.parent

        drawing.update_stroke(canvas=canvas, current_position=e.local_position, prev_position=ft.Offset(self.state.x, self.state.y))
        self.state.x = e.local_position.x
        self.state.y =  e.local_position.y


    async def handle_tap(self, e: ft.TapEvent):
        await self.add_point(e)
        
    async def handle_pan_start(self, e: ft.DragStartEvent):
        self.start_stroke(e)

    async def handle_pan_update(self, e: ft.DragUpdateEvent):
        self.update_stroke(e)

    async def handle_pan_end(self, e: ft.DragEndEvent):
        await self.end_stroke(e)

    # Ends the current stroke (cv.Shape) and marks that layer as dirty for saving, and saves if we hit max shape count
    async def end_stroke(self, e: ft.DragEndEvent[ft.Control]):
        """ Saves our paths to our canvas data for storage """
        canvas: cv.Canvas = e.control.parent
        if not canvas.visible:  
            return

        # Flag this row as dirty so we know to save it later
        panel_idx = e.control.data

        # Manually flag as dirty so we don't rewrite every single panels src at the end of one stroke
        self.data.get('panels', [])[panel_idx]['dirty'] = True
        self.needs_file_write = True
        
        
        # If we have too many shapes on the canvas, flatten them into the layer's PNG file
        if len(canvas.shapes) > MAX_SHAPES_BEFORE_CAPTURE:
            self.story.block_page()     # Block page to prevent other events whil we do this one
            panel_data = self.data['panels'][panel_idx]
            await self.save_canvas(canvas)  # Save the current canvas added shapes to its bytes stored in memory
            canvas.shapes.clear()
            #canvas.shapes.append(cv.Image(self.layer_bytes.get(layer_id), 0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT, data=layer_id))
            canvas.update()
            self.story.unblock_page()   # Unblock page
            self.state.undo_list.clear()
            #self.undo_button.disabled = True
            #self.undo_button.icon_color = ft.Colors.OUTLINE_VARIANT
            #self.undo_button.update()
            self.state.redo_list.clear()
            #self.redo_button.disabled = True
            #self.redo_button.icon_color = ft.Colors.OUTLINE_VARIANT
            #self.redo_button.update()
        else:
            pass
            #self.add_undo_task({
                #'task_type': 'path_stroke',
                #'layer_id': layer_data.get('name', ''),
                #'data': self.current_path if self.current_path else self.current_tool
            #})

        # Add stroke to undo list
        #if self.current_path is not None:
        

        # Else add shape/text
        #else:
            #self.add_undo_task({
                #'task_type': 'tool',
                #'layer_id': layer_data.get('name', ''),
                #'data': self.current_tool
            #})

    
    def build(self):
        
        
        super().build()

        # Called when we click to add a new row at the bottom of our panels
        async def create_panel(e=None):
            ''' Adds an empty new row to our panels data and reloads the widget '''

            # Create a new row with default values of each cell
            new_row_dict = {
                'canvas_id': "",   
                'capture': "",    
                'description': "",   
                'dirty': False,     
            }
            
            # Add the new row to our panels data
            self.data['panels'].append(new_row_dict)
            self.update_data(**{'panels': self.data['panels']})  # Update our data so it saves the new row

            self.panels_row.controls = build_panel_row()
            self.panels_row.update()
            await asyncio.sleep(0.05)   # Wait a moment for the new row to be added before scrolling to it
            await self.panels_row.parent.scroll_to(-1, duration=600)

        async def check_dirty(panel_idx: int):
            is_dirty = self.data['panels'][panel_idx].get('dirty', False)
            if is_dirty == True:
                # Perform any actions needed when the panel is dirty
                await self.save_canvas(self.canvases_list[panel_idx])

        
        async def move_panel(e: ft.Event[ft.Control], offset: int):
                        
            panels = self.data.get('panels', [])
            idx = int(e.control.data)
            await check_dirty(idx)
            target = idx + offset
            if offset == 0 or not 0 <= idx < len(panels) or not 0 <= target < len(panels):
                return

            panels[idx], panels[target] = panels[target], panels[idx]
            self.update_data(**{'panels': panels})

            self.panels_row.controls = build_panel_row()
            self.panels_row.update()

        async def move_panel_up(e):
            await move_panel(e, -1)

        async def move_panel_down(e):
            await move_panel(e, 1)

        # Creates a panels row ctrl for the body of our widget
        def build_panel_ctrl(panel_idx: int, panel_data: dict) -> ft.Container: 

            def load_image() -> bytes | str:
                if panel_data.get('canvas_id'):
                    widget = self.story.get_widget_by_id(panel_data['canvas_id'])
                    if widget:
                        return widget.get_snapshot_bytes(quality="medium")
                return panel_data.get('capture')

            # Updates a description for this row control in data
            def update_description(e: ft.Event[ft.TextField]):
                # Grab index positions and update data
                panel_idx = e.control.data
                self.data['panels'][panel_idx]['description'] = e.control.value
                self.update_data(**{'panels': self.data['panels']})  # Update our data

            # Deletes this row from data and removes the row control from the panels_column
            def delete_panel(e: ft.Event[ft.IconButton]):
                # Update data
                panel_idx = e.control.data
                self.data.get('panels', []).pop(panel_idx)
                self.update_data(**{'panels': self.data['panels']})  # Update our data
                # Remove row from UI and update indices
                self.panels_row.controls = build_panel_row()
                self.panels_row.update()
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
                        self.page.pop_dialog()
                        self.page.show_dialog(SnackBar("Canvas not found. Please try again."))
                        return
                    snapshot_str = widget.get_snapshot_string(quality="medium")
                    title = widget.data.get('title', 'Untitled')
                    if not snapshot_str:
                        self.page.pop_dialog()
                        self.page.show_dialog(SnackBar("Empty Canvas cannot be made as the image"))
                        return
                    self.data['panels'][panel_idx]['canvas_id'] = canvas_id
                    self.data['panels'][panel_idx]['capture'] = ""
                    self.update_data(**{'panels': self.data['panels']})  # Update our data
                    
                    self.panels_row.controls = build_panel_row()
                    self.panels_row.update()
                    
                    self.page.pop_dialog()

                panel_idx = e.control.data
                canvas_id: str = None
            
                dlg = ft.AlertDialog(
                    title=ft.Text("Set a Canvas as Image", weight=ft.FontWeight.BOLD),
                    content=ft.RadioGroup(
                        ft.Column([
                            ft.Radio(
                                label=widget.data.get('title', 'Untitled'),
                                value=id, mouse_cursor=ft.MouseCursor.CLICK,
                            ) for id, widget in self.story.widgets.items() if widget.data.get('tag', '') == "canvas"
                            ],
                            tight=True,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        on_change=select_canvas
                    ),
                    actions=[
                        ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click", color=ft.Colors.ERROR)),
                        ft.TextButton("Select", on_click=set_canvas_image, style=ft.ButtonStyle(color=ft.Colors.PRIMARY, mouse_cursor="click")),
                    ]
                )
                self.page.show_dialog(dlg)

            # Called when clicking our upload image button 
            async def upload_image(e: ft.Event[ft.MenuItemButton]):
                panel_idx = e.control.data
    
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
                            self.data['panels'][panel_idx]['capture'] = f"data:image/{file_path.split('.')[-1]};base64,{encoded_string}"
                            self.data['panels'][panel_idx]['canvas_id'] = ""   # Clear the canvas_id if we uploaded an image
                            self.update_data(**{'panels': self.data['panels']})  # Update our data
    
                        self.panels_row.controls = build_panel_row()
                        self.panels_row.update()
    
                    except Exception:
                        pass

            # Clears the canvas id and preview cap to set image to placeholder
            def clear_canvas(e: ft.Event[ft.MenuItemButton]):
                panel_idx = e.control.data
                self.data['panels'][panel_idx]['capture'] = ""
                self.data['panels'][panel_idx]['canvas_id'] = ""   # Clear the canvas_id if we cleared the image
                self.update_data(**{'panels': self.data['panels']})  # Update our data
                self.panels_row.controls = build_panel_row()
                self.panels_row.update()

            # Set preview capture by canvas_id -> capture -> default image
            if panel_data.get('canvas_id'): capture = self.story.get_widget_by_id(panel_data.get('canvas_id')).get_snapshot_string(quality="low")
            elif panel_data.get('capture'): capture = panel_data.get('capture', "")
            else: capture = "canvas_bg.png"

            def toggle_color_popover(e: ft.Event[ft.Control]):
                color_popover.open = not color_popover.open
                color_popover.update()

            async def set_panel_color(e: ft.Event[ft.Control]):
                color_popover.open = False
                color_popover.update()
                color = e.control.data
                canvas: cv.Canvas = self.canvases_list[panel_idx]
                canvas.shapes = [cv.Rect(0, 0, SKETCH_SIZE[0], SKETCH_SIZE[1], paint=ft.Paint(color))]
                canvas.update()
                await canvas.capture()
                b: bytes = await canvas.get_capture()
                await canvas.clear_capture()
                capture = base64.b64encode(b).decode("utf-8")

                self.data['panels'][panel_idx]['canvas_id'] = ""
                self.data['panels'][panel_idx]['capture'] = capture
                self.update_data(**{'panels': self.data['panels']})
                canvas.update()

            async def toggle_lock_panel(e: ft.Event[ft.Control]):
                self.data['panels'][panel_idx]['locked'] = not self.data['panels'][panel_idx].get('locked', False)
                self.update_data(**{'panels': self.data['panels']})
                self.panels_row.controls = build_panel_row()
                self.panels_row.update()
                

            panel_options_cm = ft.Container(
                bgcolor=ft.Colors.SURFACE, shape=ft.BoxShape.CIRCLE,
                content=shad.ContextMenu(
                    HighlightButton(ft.Icon(ft.Icons.MORE_VERT_OUTLINED, ft.Colors.PRIMARY), is_round=True, use_padding=True),
                    [
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.ARROW_UPWARD_OUTLINED, ft.Colors.PRIMARY, size=20),
                            content="Move Up",
                            on_click=move_panel_up, data=panel_idx
                        ),
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.ARROW_DOWNWARD_OUTLINED, ft.Colors.PRIMARY, size=20),
                            content="Move Down",
                            on_click=move_panel_down, data=panel_idx,
                        ),
                        shad.MenuItem(
                            leading=ft.Icon(ft.Icons.LOCK_OUTLINED if not panel_data.get('locked') else ft.Icons.LOCK_OPEN_OUTLINED, ft.Colors.PRIMARY, size=20),
                            content="Lock Panel" if not panel_data.get('locked') else "Unlock Panel",
                            on_click=toggle_lock_panel, data=panel_idx, tooltip="asdf"
                        ),
                        shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                        shad.MenuItem(
                            "Set Canvas",
                            leading=ft.Icon(ft.Icons.BRUSH_OUTLINED, ft.Colors.PRIMARY, size=20),
                            on_click=set_canvas_as_image, data=panel_idx
                        ),
                        shad.MenuItem(
                            "Upload Image",
                            leading=ft.Icon(ft.Icons.IMAGE_SEARCH_OUTLINED, ft.Colors.PRIMARY, size=20),
                            on_click=upload_image, data=panel_idx,
                        ),
                        shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                        color_popover := shad.Popover(
                            shad.MenuItem(
                                leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, ft.Colors.PRIMARY, size=20),
                                content=ft.Row([ft.Text("Set Color"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                trailing=ft.Icons.ARROW_RIGHT,
                                on_click=toggle_color_popover,
                                close_on_click=False,
                            ),
                            ft.Column([
                                shad.MenuItem(
                                    content=ft.Icon(ft.Icons.CIRCLE, color=color, size=20),
                                    on_click=set_panel_color, close_on_click=True, data=color,
                                    expand=True
                                ) for color in colors
                            ] + [shad.MenuItem(
                            content=ft.Icon(ft.Icons.CIRCLE_OUTLINED, color="#00000000", size=20),
                            on_click=set_panel_color, close_on_click=True, data="#00000000",
                            expand=True
                        )], tight=True, spacing=0, width=100)
                        ), 
                        shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                        shad.MenuItem(
                            "Clear Panel",
                            leading=ft.Icon(ft.Icons.HIDE_IMAGE_OUTLINED, ft.Colors.PRIMARY, size=20),
                            on_click=clear_canvas, data=panel_idx
                        ),
                        shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
                        shad.MenuItem(
                            "Delete Panel",
                            leading=ft.Icon(ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, size=20),
                            on_click=delete_panel, data=panel_idx
                        ),
                    ],
                    open_on_tap=True
                )
            )
            
            sketch_canvas = cv.Canvas(      # Canvas for drawing on
                content=ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.PRECISE,
                    on_pan_start=self.handle_pan_start,
                    on_pan_update=self.handle_pan_update,
                    on_pan_end=self.handle_pan_end,
                    on_tap_up=self.handle_tap,      # Handles so we can add points
                    data=panel_idx,
                    drag_interval=5,                    
                ),
                shapes=[
                    cv.Image(load_image(), 0, 0, 500, 500)  # Load the src for sketch. Will be tied to a canvas, or set src
                ],
                data=panel_idx
            )
            self.canvases_list.append(sketch_canvas)
            description_tf = ft.TextField(
                str(panel_data.get('description', "")), 
                dense=True, multiline=True,  
                capitalization=ft.TextCapitalization.SENTENCES,
                data=panel_idx, bgcolor=ft.Colors.SURFACE, 
                on_blur=update_description,
                width=500, margin=ft.Margin.only(top=10), 
                label="Description", 
                suffix_icon=panel_options_cm,
                label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY),
                border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
            )
                        
            return ft.Container(
                ft.Column([
                    #ft.Row([undo_button, panel_options_cm, redo_button], width=500, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(
                        sketch_canvas,  
                        bgcolor=ft.Colors.SURFACE, 
                        border_radius=6,
                        width=SKETCH_SIZE[0], height=SKETCH_SIZE[1],
                        tooltip="Drawing disabled while panel is tied to a canvas" if panel_data.get('canvas_id') else None,
                        ignore_interactions=True if panel_data.get('locked') else False
                    ),
                    description_tf
                ], spacing=0, tight=True),
                data=panel_idx, padding=10,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
            )

        def build_panel_row() -> list[ft.Control]:
            self.canvases_list.clear()
            ctrls = [build_panel_ctrl(idx, panel_data) for idx, panel_data in enumerate(self.data.get('panels', []))]
            ctrls.append(
                ft.IconButton(
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY, 30,
                    on_click=create_panel,
                    tooltip="Add Panel",
                    mouse_cursor=ft.MouseCursor.CLICK,
                    bgcolor=ft.Colors.SURFACE,
                    margin=ft.Margin.only(left=10)
                )
            )
            return ctrls

        self.description_tf.bgcolor = ft.Colors.SURFACE
        self.description_tf.margin = ft.Margin.only(left=6, right=6, bottom=6)
        self.description_tf.label = "Scope"

        self.panels_row = ft.Row(build_panel_row(), spacing=0, run_spacing=0, expand=True, wrap=True)
        
        # Body of the tab, which is the content of flet container
        body = ft.Column(
            expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[                 
                ft.Column([self.panels_row], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO),
                ft.Row([self.description_tf], spacing=0)
            ])
    
        self.content = body
       
            


# TODO: Set color as background.