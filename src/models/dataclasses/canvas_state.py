'''
State management model for our drawings
'''
import flet as ft
import flet.canvas as cv

class State:

    # Track our previous position for drawing
    x: float = 0.0
    y: float = 0.0

    undo_list: list[cv.Path] = []       # [{'task_type': '', 'layer_name': '', 'data': ''}, {...}]
    redo_list: list[cv.Path] = []        