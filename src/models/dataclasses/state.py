'''
State management model for our drawings
'''


class State:

    # Costructor
    def __init__(self):

        # Track our previous position for drawing
        self.x: float = float()
        self.y: float = float()

        # Shapes that we are currently drawing so we know what to save to data
        self.paths = [{'elements': list(), 'paint': dict()}]    # Paths

        self.points = []    # Points

        # Our list of recent changes so we can undo them
        undo_list = []

        # List of recent changes from undo in case user wants to redo them
        redo_list = []