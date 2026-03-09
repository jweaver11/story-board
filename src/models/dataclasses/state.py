'''
State management model for our drawings
'''

class State:

    # Track our previous position for drawing
    x: float = 0.0
    y: float = 0.0

    # Shapes that we are currently drawing so we know what to save to data
    paths = [{'elements': [], 'paint': {}}]    # Paths
    points = []    # Points

    # Our list of captures for undo/redo
    undo_list = []
    redo_list = []
    # Each undo/redo item {'layer_name': "capture_str"}}    # Set that layer to a previous or now-future capture state

        