'''
State management model for our drawings
'''
import flet as ft

class State:

    # Track our previous position for drawing
    x: float = 0.0
    y: float = 0.0