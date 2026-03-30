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
            padding=ft.Padding.only(top=10, bottom=10, right=10, left=10),
            #bgcolor=ft.Colors.SURFACE,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            expand=True
        )

        # Loads the active rail
        self.reload_rail()
        
    # Called when other workspaces are selected
    def reload_rail(self, rail: str = None):
        ''' Reloads the active rail based on the selected workspace in workspaces_rail '''

        # Allows us to force a rail without saving it to data. Useful for maps
        if rail is not None:
            selected_rail = rail

        # Otherwise we'll just get it from the story data
        else:
            selected_rail = self.story.data.get('selected_rail', "content")

        match selected_rail:
            case "content":
                self.content = ContentRail(self.p, self.story)
            case "characters":
                self.content = CharactersRail(self.p, self.story)
                
            case "plotlines":
                self.content = PlotlinesRail(self.p, self.story)
                
            case "world_building":
                self.content = WorldBuildingRail(self.p, self.story)
                
            case "canvas":
                self.content = CanvasRail(self.p, self.story)
                
            case "planning":
                self.content = PlanningRail(self.p, self.story)
                
            case _:
                self.content = ContentRail(self.p, self.story)
                

        try:
            self.update()
        except Exception as e:
            pass