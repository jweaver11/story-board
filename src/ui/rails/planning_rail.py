""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from models.isolated_controls.column import IsolatedColumn



# TODO:Overall goal: Plan out how to manage and develop the story. Mostly useful for companies, but users can use it too
# Add worlds, canvas board, notes, characters?, plotlines?, maps?
# Create tasks pertaining to parts of the story
# Ability to add/import employees, and delegate them to tasks
# -- Can see employees tasks

# Class is created in main on program startup
class PlanningRail(Rail):
    # Constructor
    def __init__(self, story: Story):
        
        # Initialize the parent Rail class first
        super().__init__(story=story)


        
    # Reload the rail whenever we need
    def build(self) -> ft.Control:
        ''' Reloads planning, useful when switching stories '''

        # Build the content of our rail
        self.controls = [
            #header,
            #ft.Divider(),
            ft.Text("Coming Soon")
            #menu_gesture_detector
        ]
        

        
        

