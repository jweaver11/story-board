'''
State management model for our drawings
'''
import flet as ft
import flet.canvas as cv

class State:

    # Track our previous position for drawing
    x: float = 0.0
    y: float = 0.0

    # If we are currently manipulating a shape
    manipulating_shape: bool = False    

    # Undo and Redo lists for our canvas actions
    undo_list: list[cv.Path] = []       # [{'task_type': '', 'layer_id': '', 'data': ''}, {...}]
    redo_list: list[cv.Path] = []        