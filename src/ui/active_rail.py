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
from ui.rails.plotlines_rail import PlotlinesRail
from ui.rails.world_building import WorldBuildingRail
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
            alignment=ft.Alignment.TOP_CENTER,
            padding=ft.Padding.only(top=10, bottom=10, right=8, left=8),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            expand=True
        )

        # Add our 6 rails here first so they maintain consitent styling and don't have to be rebuilt on switches
        self.content_rail = ContentRail(page, story)
        self.characters_rail = CharactersRail(page, story)
        self.plotlines_rail = PlotlinesRail(page, story)
        self.world_building_rail = WorldBuildingRail(page, story)
        self.canvas_rail = CanvasRail(page, story)
        self.planning_rail = PlanningRail(page, story)

        self.content_first_launch = True
        self.characters_first_launch = True 
        self.plotlines_first_launch = True
        self.world_building_first_launch = True
        self.canvas_first_launch = True
        self.planning_first_launch = True

        # Displays our active rail on startup
        # All other rails have reload rail functions, but this one just displays the correct one
        self.display_active_rail(story)
        
    # Called when other workspaces are selected
    def display_active_rail(self, story: Story, rail: str = None):
        ''' Reloads the active rail based on the selected workspace in workspaces_rail '''

        # Allows us to force a rail without saving it to data. Useful for maps
        if rail is not None:
            selected_rail = rail

        # Otherwise we'll just get it from the story data
        else:
            selected_rail = story.data.get('selected_rail', "content")

        match selected_rail:
            case "content":
                self.content = self.content_rail
                if self.content_first_launch:
                    self.content_first_launch = False
                    self.content.reload_rail()
            case "characters":
                self.content = self.characters_rail
                if self.characters_first_launch:
                    self.characters_first_launch = False
                    self.characters_rail.reload_rail()
            case "plotlines":
                self.content = self.plotlines_rail
                if self.plotlines_first_launch:
                    self.plotlines_first_launch = False
                    self.plotlines_rail.reload_rail()
            case "world_building":
                self.content = self.world_building_rail
                if self.world_building_first_launch:
                    self.world_building_first_launch = False
                    self.world_building_rail.reload_rail()
            case "canvas":
                self.content = self.canvas_rail
                if self.canvas_first_launch:
                    self.canvas_first_launch = False
                    self.canvas_rail.reload_rail()
            case "planning":
                self.content = self.planning_rail
                if self.planning_first_launch:
                    self.planning_first_launch = False
                    self.planning_rail.reload_rail()
            case _:
                self.content = self.content_rail
                if self.content_first_launch:
                    self.content_first_launch = False
                    self.content.reload_rail()

        try:
            self.update()
        except Exception as e:
            pass