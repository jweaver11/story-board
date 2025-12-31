""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail



# TODO:Overall goal: Plan out how to manage and develop the story. Mostly useful for companies, but users can use it too
# Create tasks pertaining to parts of the story
# Ability to add/import employees, and delegate them to tasks
# -- Can see employees tasks

# Class is created in main on program startup
class Planning_Rail(Rail):
    # Constructor
    def __init__(self, page: ft.Page, story: Story):
        
        # Initialize the parent Rail class first
        super().__init__(
            page=page,
            story=story,
            directory_path=story.data.get('content_directory_path', '')
        )

        # Reload the rail on start
        self.reload_rail()
        
    # Reload the rail whenever we need
    def reload_rail(self) -> ft.Control:
        ''' Reloads planning, useful when switching stories '''

        # Build the content of our rail
        self.content = ft.Column(
            controls=[
                ft.Text("Planning Rail is under construction"),
            ]
        )

        # Apply our update
        self.p.update()
        

