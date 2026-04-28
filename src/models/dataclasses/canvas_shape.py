''' 
Shapes added to the canvas that the user can drag, edit, and resize. This class is removed from the canvas
after editing is done, and the shape is then painted onto the canvas
'''

import flet as ft
import flet.canvas as cv
import math
from models.app import app

class CanvasShape(ft.Container):

    def __init__(self, shape_type: str, left=0, top=0):
        super().__init__(
            left=left,
            top=top,
            rotate=ft.Rotate(0),
            animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            animate_rotation=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            animate_size=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        )

        self.shape_type = shape_type

        # State management for rotation and resizing
        self._prev_mouse_angle = 0
        self._local_center_x: float = 0.0
        self._local_center_y: float = 0.0
        self._width = 200         # Width of actual shape excluding tools to rotate
        self._height = 200        # Height of actual shape excluding tools to rotate
        self.manipulate_action: str = "move"


        self.rotate_handle: ft.GestureDetector
        self.canvas: cv.Canvas


        
    # Setup initial rotation position
    async def _rotate_start(self, e: ft.DragStartEvent):
        self._local_center_x = self.canvas.width / 2
        self._local_center_y = 24 + self.canvas.height / 2  # ≈ 124
        self._prev_mouse_angle = math.atan2(
            e.local_position.y - self._local_center_y,
            e.local_position.x - self._local_center_x
        )


    # Rotates the shape based on the mouse movement.  
    async def _rotate(self, e: ft.DragUpdateEvent):
        current_angle = math.atan2(
            e.local_position.y - self._local_center_y,
            e.local_position.x - self._local_center_x
        )
        delta = current_angle - self._prev_mouse_angle
        if delta > math.pi:
            delta -= 2 * math.pi
        elif delta < -math.pi:
            delta += 2 * math.pi
        self.rotate.angle += delta

        # Check if we're near 90 degree increments and snap to them if we are
        if self.rotate.angle:
            pass

        self._prev_mouse_angle = current_angle
        self.update()

    # Returns the correct cursor for the given angle of rotation for visual feedback when hovering over edges to resize
    def _cursor_for_angle(self, angle: float) -> ft.MouseCursor:
        """Maps a screen-space drag direction (radians) to the best resize cursor."""
        norm = angle % math.pi
        if norm < 0:
            norm += math.pi

        if norm < math.pi / 8 or norm >= 7 * math.pi / 8:
            return ft.MouseCursor.RESIZE_LEFT_RIGHT           # ↔
        elif norm < 3 * math.pi / 8:
            return ft.MouseCursor.RESIZE_UP_LEFT_DOWN_RIGHT   # ↘↖  (\)
        elif norm < 5 * math.pi / 8:
            return ft.MouseCursor.RESIZE_UP_DOWN              # ↕
        else:
            return ft.MouseCursor.RESIZE_UP_RIGHT_DOWN_LEFT   # ↙↗  (/)

    # Sets the mouse cursor depending on where the mouse is hovering
    async def _set_manipulation_action(self, e: ft.PointerEvent):

        angle = self.rotate.angle

        # If we're near left edge
        if e.local_position.x < 20:
            e.control.mouse_cursor = self._cursor_for_angle(angle)
            e.control.update()
            self.manipulate_action = "resize_left"
            return
        # If we're near right edge
        if e.local_position.x > self.canvas.width - 20:
            e.control.mouse_cursor = self._cursor_for_angle(angle)
            e.control.update()
            self.manipulate_action = "resize_right"
            return
            
        # If we're near top edge
        if e.local_position.y < 20:
            e.control.mouse_cursor = self._cursor_for_angle(angle + math.pi / 2)
            e.control.update()
            self.manipulate_action = "resize_top"
            return
        # If we're near bottom edge
        if e.local_position.y > self.canvas.height - 20:
            e.control.mouse_cursor = self._cursor_for_angle(angle + math.pi / 2)
            e.control.update()
            self.manipulate_action = "resize_bottom"
            return

        # If we didn't return early, we're in the middle of the shape, so we should be dragging to move
        e.control.mouse_cursor = ft.MouseCursor.MOVE
        self.manipulate_action = "move"
        e.control.update()

    # Either drag or resize us based on where the user is manipulating
    async def _manipulate(self, e: ft.DragUpdateEvent):

        match self.manipulate_action:
            
            # Resizing from the left edge
            case "resize_left":   # right edge stays fixed
                angle = self.rotate.angle
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                dx = e.local_delta.x
                self.canvas.width = max(20, self.canvas.width - dx)

                # Update whichever shape is inside of this container
                match self.shape_type:
                    case "rectangle":
                        self.shape.width = self.canvas.width
                        self.shape.height = self.canvas.height


                self.left += dx / 2 * (cos_a + 1)
                self.top  += dx / 2 * sin_a
                self.canvas.update()
                self.update()

            # Resizing from the right edge
            case "resize_right": 
                angle = self.rotate.angle
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                dx = e.local_delta.x
                self.canvas.width = max(20, self.canvas.width + dx)

                # Update whichever shape is inside of this container
                match self.shape_type:
                    case "rectangle":
                        self.shape.width = self.canvas.width
                        self.shape.height = self.canvas.height


                self.left += dx / 2 * (cos_a - 1)
                self.top  += dx / 2 * sin_a
                self.canvas.update()
                self.update()

            # Resizing from the top edge
            case "resize_top":    # bottom edge stays fixed
                angle = self.rotate.angle
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                dy = e.local_delta.y
                self.canvas.height = max(20, self.canvas.height - dy)

                # Update whichever shape is inside of this container
                match self.shape_type:
                    case "rectangle":
                        self.shape.width = self.canvas.width
                        self.shape.height = self.canvas.height

                        
                self.left -= dy / 2 * sin_a
                self.top  += dy / 2 * (cos_a + 1)
                self.canvas.update()
                self.update()

            # Resizing from the bottom edge
            case "resize_bottom": # top edge stays fixed
                angle = self.rotate.angle
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                dy = e.local_delta.y
                self.canvas.height = max(20, self.canvas.height + dy)

                # Update whichever shape is inside of this container
                match self.shape_type:
                    case "rectangle":
                        self.shape.width = self.canvas.width
                        self.shape.height = self.canvas.height
                        

                        
                self.left -= dy / 2 * sin_a
                self.top  += dy / 2 * (cos_a - 1)
                self.canvas.update()
                self.update()

            # Moving
            case "move": 
                angle = self.rotate.angle
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                self.left += e.local_delta.x * cos_a - e.local_delta.y * sin_a
                self.top  += e.local_delta.x * sin_a + e.local_delta.y * cos_a
                self.update()

    


    def build(self):

        # TODO: Can rotate built in:
        # BUG: Shape not showing up when touching border
        # Arc
        # ArcTo?
        # Circle?
        # Oval
        # Half Circle
        # Rectangle
        # Triangle
        # Text
        # Text Box's (x4)

        cv.Path.Rect
        cv.Path.Arc
        cv.Path.ArcTo
        cv.Path.CubicTo
        cv.Path.QuadraticTo
        cv.Path.Oval
        

        match self.shape_type:
            case "rectangle":
                self.shape = cv.Rect(0, 0, 200, 200, paint=ft.Paint(**app.settings.data.get('paint_settings', {})))

        #shape = None

        self.canvas = cv.Canvas(
            shapes=[self.shape],      # Shape we built depending on the tool being used
            content=ft.GestureDetector(
                #ft.Container(expand=True, ),
                on_pan_update=self._manipulate,     # Handles resizing and dragging
                on_hover=self._set_manipulation_action,
                expand=True, mouse_cursor=ft.MouseCursor.MOVE,
                drag_interval=10, hover_interval=50
            ),
            margin=ft.Margin.all(10),
            width=200, height=200,
        )

        # How we will rotate the shape
        self.rotate_handle = ft.GestureDetector(
            ft.Icon(ft.Icons.ROTATE_RIGHT_OUTLINED, ft.Colors.PRIMARY), 
            mouse_cursor=ft.MouseCursor.CLICK if self.page.platform == ft.PagePlatform.WINDOWS else ft.MouseCursor.GRAB,
            on_pan_start=self._rotate_start,
            on_pan_update=self._rotate, 
            drag_interval=20,
            expand=True
        )
        
        
        self.content = ft.Column(
            [
                self.rotate_handle,
                ft.VerticalDivider(),
                ft.Container(
                    self.canvas, 
                    expand=True, #padding=ft.Padding.all(10), 
                    border=ft.Border.all(2, ft.Colors.RED)
                )
            ], 
            tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0
        )

    
    

