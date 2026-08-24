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

async def paint_tool_on_canvas(canvas: cv.Canvas, tool: CanvasShape):
    if not canvas.visible or not canvas:
        return

    # Grab our text and account for border, and add it to the canvas
    if tool.shape_type == "text":
        # Align our text to account for size of our layer canvas
        text_shape: cv.Text = tool.cv_shape
        text_shape.x += tool.left + 2
        text_shape.y += tool.top + 2
        canvas.shapes.append(text_shape)
        await end_stroke(canvas=canvas)
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

    

async def end_stroke(canvas: cv.Canvas):
    return