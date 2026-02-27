'''
State management model for our drawings
'''


class State:

    # Costructor
    def __init__(self, capture_list: list=[]):

        # Track our previous position for drawing
        self.x: float = 0.0
        self.y: float = 0.0

        # Shapes that we are currently drawing so we know what to save to data
        self.paths = [{'elements': [], 'paint': {}}]    # Paths

        self.points = []    # Points

        # Our list of captures for undo/redo
        self.capture_list = capture_list

        # List of recent changes from undo in case user wants to redo them
        redo_list = []