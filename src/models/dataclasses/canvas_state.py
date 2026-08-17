'''
State management model for our drawings
'''
import flet as ft
from dataclasses import dataclass, field

@dataclass
class State:

    # Track our previous position for drawing
    x: float = field(default_factory=float)
    y: float = field(default_factory=float)

    # If we are currently manipulating a shape
    manipulating_shape: bool = field(default_factory=bool) 

    # Undo and Redo lists for our canvas actions
    undo_list: list = field(default_factory=list)      # [{'task_type': '', 'layer_id': '', 'data': ''}, {...}]
    redo_list: list = field(default_factory=list)       