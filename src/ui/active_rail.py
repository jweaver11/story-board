'''
UI model for our active rail, which is stored at app.active_story.active_rail
Keeps consistent styling and width between different workspace rails, 
And gives us the correct rail on startup based on selected workspace
'''

import flet as ft
from models.app import app
from models.views.story import Story
from ui.rails.characters_rail import CharactersRail  
from ui.rails.content_rail import ContentRail
from ui.rails.timelines_rail import TimelinesRail
from ui.rails.world_building_rail import WorldBuildingRail
from ui.rails.canvas_rail import CanvasRail
from ui.rails.planning_rail import PlanningRail  


# Class is created in main on program startup
class Active_Rail(ft.Container):
    
    # Constructor
    def __init__(self, page: ft.Page, story: Story):
    
        self.p = page  # Store the page reference
        self.story = story  # Store the story reference
  
        # Consistent styling for all our rails
        super().__init__(
            alignment=ft.alignment.top_left,
            padding=ft.padding.only(top=10, bottom=10, right=8, left=8),
            border_radius=ft.border_radius.only(top_right=10, bottom_right=10),
            width=app.settings.data['active_rail_width'],  # Sets the width
        )

        # Add our 6 rails here first so they maintain consitent styling and don't have to be rebuilt on switches
        self.content_rail = ContentRail(page, story)
        self.characters_rail = CharactersRail(page, story)
        self.timelines_rail = TimelinesRail(page, story)
        self.world_building_rail = WorldBuildingRail(page, story)
        self.canvas_rail = CanvasRail(page, story)
        self.planning_rail = PlanningRail(page, story)

        # Displays our active rail on startup
        # All other rails have reload rail functions, but this one just displays the correct one
        self.display_active_rail(story)

    # Called when we create new widgets so all rails are in sync
    def reload_all_rails(self):
        ''' Reloads all rails in case of new widget creation '''
        
        self.content_rail.reload_rail()
        self.characters_rail.reload_rail()
        self.timelines_rail.reload_rail()
        self.world_building_rail.reload_rail()
        self.canvas_rail.reload_rail()
        self.planning_rail.reload_rail()

    # Called when we want to reload all other rails except the active one. Usually to keep expansion states of categories between rails
    async def reload_all_other_rails(self):
        ''' Reloads all rails except the active one '''
        
        active_rail = self.story.data.get('selected_rail', 'content')
        
        if active_rail != "content":
            self.content_rail.reload_rail()
        if active_rail != "characters":
            self.characters_rail.reload_rail()
        if active_rail != "timelines":
            self.timelines_rail.reload_rail()
        if active_rail != "world_building":
            self.world_building_rail.reload_rail()
        if active_rail != "canvas":
            self.canvas_rail.reload_rail()
        if active_rail != "planning":
            self.planning_rail.reload_rail()
        

        
    # Called when other workspaces are selected
    def display_active_rail(self, story: Story):
        ''' Reloads the active rail based on the selected workspace in workspaces_rail '''

       
        # Give us the correct rail based on our selected workspace
        if story.data.get('selected_rail', "content") == "content":
            self.content = self.content_rail

        elif story.data.get('selected_rail', "content") == "characters":
            self.content = self.characters_rail

        elif story.data.get('selected_rail', "content") == "timelines":
            self.content = self.timelines_rail

            # Make sure our timeline is shown if there is only one
            if len(self.story.timelines) == 1:
                for tl in self.story.timelines.values():
                    tl.toggle_visibility(value=True)

        elif story.data.get('selected_rail', "content") == "world_building":
            self.content = self.world_building_rail

        elif story.data.get('selected_rail', "content") == "canvas":
            self.content = self.canvas_rail

        elif story.data.get('selected_rail', "content") == "planning":
            self.content = self.planning_rail

        else:
            # Default to the content rail
            self.content = self.content_rail

        # Update the page to reflect changes
        self.p.update()

       
