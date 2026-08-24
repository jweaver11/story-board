import flet as ft
import math
import flet.canvas as cv
from models.canvas_shapes.canvas_shape import CanvasShape
from styles.snack_bar import SnackBar
from io import BytesIO
from PIL import Image
import asyncio
from styles.menu_option_style import MenuOptionStyle
from models.dataclasses.canvas_shape import CanvasShape    
from styles.text_fields import TextField
import time
import uuid
import os
from PIL import Image, ImageDraw, ImageTk, ImageColor
from models.app import app
from collections import deque

async def paint_tool_on_canvas(canvas: cv.Canvas, tool: CanvasShape, end_stroke_callback):
    if not canvas.visible or not canvas:
        return

    # Grab our text and account for border, and add it to the canvas
    if tool.shape_type == "text":
        # Align our text to account for size of our layer canvas
        text_shape: cv.Text = tool.cv_shape
        text_shape.x += tool.left + 2
        text_shape.y += tool.top + 2
        canvas.shapes.append(text_shape)
        await end_stroke_callback(canvas=canvas)
        #await end_stroke(canvas=canvas)
        return

    # Non-text below -OLD
    return

    await tool.canvas.capture()
    shape_capture = await tool.canvas.get_capture()

    if not shape_capture:
        ft.context.page.show_dialog(SnackBar("Error capturing shape."))
        return

    # Grab the image and rotate
    shape_img = Image.open(BytesIO(shape_capture)).convert("RGBA")
    angle = tool.rotate.angle
    angle_degrees = -math.degrees(angle)
    rotated = shape_img.rotate(angle_degrees, expand=True, resample=Image.Resampling.BICUBIC)

    # Set rotation (with border padding)
    rotation_cx = tool.left + (tool.canvas.width + 4) / 2
    rotation_cy = tool.top + (tool.canvas.height + 4) / 2
    paste_x = int(rotation_cx - rotated.width / 2)
    paste_y = int(rotation_cy - rotated.height / 2)


    output = BytesIO()
    rotated.save(output, format="PNG")
    stamped_bytes = output.getvalue()

    canvas.shapes.append(cv.Image(stamped_bytes, paste_x, paste_y))
    await end_stroke(canvas=canvas)
    canvas.update()


# Updates any tools that have not yet been painted onto a canvas with the current paint and text settings
def update_tool_preview(tool: CanvasShape):
    canvas_settings = app.settings.data.get('canvas_settings', {}).copy()
    paint_settings = app.settings.data.get('paint_settings', {}).copy()
    text_settings = app.settings.data.get('text_settings', {}).copy()

    tool.paint = ft.Paint(**paint_settings)
    if tool.shape_type == "text":
        tool.cv_shape.style = ft.TextStyle(**text_settings)
        decoration = text_settings.get('decoration', None)
        match decoration:
            case "underline":
                tool.cv_shape.style.decoration = ft.TextDecoration.UNDERLINE
            case "overline":
                tool.cv_shape.style.decoration = ft.TextDecoration.OVERLINE
            case "line-through":
                tool.cv_shape.style.decoration = ft.TextDecoration.LINE_THROUGH

        tool.cv_shape.style.shadow = ft.BoxShadow(
            blur_radius=text_settings.get('shadow', {}).get('blur_radius', 0),
            color=text_settings.get('shadow', {}).get('color', None),
            offset=ft.Offset(
                text_settings.get('shadow', {}).get('offset_x', 0),
                text_settings.get('shadow', {}).get('offset_y', 0)
            ),
        )
    elif tool.shape_type == "rectangle":
        tool.cv_shape.border_radius = ft.BorderRadius.all(canvas_settings.get('rectangle_border_radius', 0))
    else:
        for shape in tool.canvas.shapes:
            shape.paint = ft.Paint(**paint_settings)
    tool.update()

# Draws a point on the canvas with the current paint settings
async def draw_point(canvas: cv.Canvas, position: ft.Offset):
    if not canvas.visible:
        return
    paint_settings = app.settings.data.get('paint_settings', {}).copy()

    # Check if we're in erase mode so we can adjust paint settings to not error out
    control_mode = app.settings.data.get('canvas_settings', {}).get('current_control_mode', "")
    tool_name = app.settings.data.get('canvas_settings', {}).get('current_tool_name', "")
    if control_mode == "tool":
        if tool_name == "erase":
            paint_settings['blend_mode'] = "clear"
            paint_settings['blur_image'] = 0    # Must have no blur
            paint_settings['style'] = "stroke"  # Must use stroke

    # Add the point and updaet
    canvas.shapes.append(cv.Points(points=[(position.x, position.y)], paint=ft.Paint(**paint_settings)))
    canvas.update()

# Creates an initial stroke path on the canvas depending on current paint settings
def start_stroke(canvas: cv.Canvas, current_position: ft.Offset, prev_position: ft.Offset=None):
    if not canvas.visible:
        ft.context.page.show_dialog(SnackBar("Set an active layer to draw on."))
        return

    # Grab paint settings
    paint_settings = app.settings.data.get('paint_settings', {}).copy()
    canvas_settings = app.settings.data.get('canvas_settings', {}).copy()

    # Check if we're in tool mode, and what tool we're using
    if canvas_settings.get('current_control_mode', "") == "tool":
        tool_name = canvas_settings.get('current_tool_name', "")

        # Erase tool - Update the paint settings and create a normal path
        if tool_name == "erase":
            paint_settings['blend_mode'] = "clear"
            paint_settings['blur_image'] = 0
            paint_settings['style'] = "stroke"
            current_path = cv.Path(elements=[cv.Path.MoveTo(current_position.x, current_position.y)], paint=ft.Paint(**paint_settings))

        # Line tool - Create a path using one straight line element that we'll update differently
        elif tool_name == "line":                
            paint_settings['style'] = "stroke"
            current_path = cv.Path(elements=[cv.Path.MoveTo(current_position.x, current_position.y)], paint=ft.Paint(**paint_settings))
            line_element = cv.Path.LineTo(prev_position.x, prev_position.y)
            current_path.elements.append(line_element)

        # Add our tool path to the canvas and return
        canvas.shapes.append(current_path)
        canvas.update()
        return
    
    # Brush smoothing - use a normal path
    if canvas_settings.get('use_brush_smoothing', False) == True or paint_settings.get('style', "") == "stroke_fill":
        canvas.shapes.append(cv.Path(elements=[cv.Path.MoveTo(current_position.x, current_position.y)], paint=ft.Paint(**paint_settings)))

    # No brush smoothing, just add a line element to the canvas
    else: 
        if not prev_position:
            return
        canvas.shapes.append(cv.Line(prev_position.x, prev_position.y, current_position.x, current_position.y, paint=ft.Paint(**paint_settings)))

    canvas.update()     # Apply the update

# Updates our current stroke path on the canvas with a new line element
def update_stroke(canvas: cv.Canvas, current_position: ft.Offset, prev_position: ft.Offset=None):
    # TODO: Handle Stroke smoothing

    # Catch errors
    if not canvas.visible:
        return
    if not canvas.shapes:
        return

    # Grab current path
    current_path = canvas.shapes[-1] if canvas.shapes and len(canvas.shapes) > 1 else None # Trips if drawing but havnt finished capture
    if not current_path:
        return

    canvas_settings = app.settings.data.get('canvas_settings', {}).copy()

    # Check if we're in tool mode, and what tool we're using
    if canvas_settings.get('current_control_mode', "") == "tool":
        tool_name = canvas_settings.get('current_tool_name', "")
        match tool_name:

            # Erase tool - Add another smooth line to the path
            case "erase":
                path_element = cv.Path.LineTo(current_position.x, current_position.y)
                current_path.elements.append(path_element)

            # Line tool - Update our straight line element to the current mouse position
            case "line":
                # Set the element and update its position
                line_element = current_path.elements[-1]
                line_element.x = current_position.x
                line_element.y = current_position.y
        # Update state and return
        current_path.update()
        

    # Otherwise we're in draw mode
    else:
        paint_settings = app.settings.data.get('paint_settings', {}).copy()

        # If using path smoothing or stroke_fill, update the path with a new line element
        if canvas_settings.get('use_brush_smoothing', False) == True or paint_settings.get('style', "") == "stroke_fill": 
            path_element = cv.Path.LineTo(current_position.x, current_position.y)
            current_path.elements.append(path_element)
            current_path.update()

        # Non-smooth drawing, add another line
        else: 
            canvas.shapes.append(cv.Line(prev_position.x, prev_position.y, current_position.x, current_position.y, paint=current_path.paint))
            canvas.update()