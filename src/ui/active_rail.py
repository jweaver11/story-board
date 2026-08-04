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
class ActiveRail(ft.Container):
    
    # Constructor
    def __init__(self, story: Story):
    
        self.story = story  # Store the story reference
  
        # Consistent styling for all our rails
        super().__init__(
            alignment=ft.Alignment.TOP_CENTER,
            padding=ft.Padding.only(top=10, bottom=10),
            width=app.settings.data.get('story', {}).get('active_rail_width', 250),
            animate_size=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )
        
    # Reload our rail on startup
    def build(self):
        self.reload_rail(update=False)
        
    # Called when a new workspace is selected
    def reload_rail(self, update: bool=True):
        ''' Reloads the active rail based on the selected workspace in workspaces_rail '''

        self.content = ContentRail(self.story)
        if update:
            self.update()
        return

        # Grab our selected rail and re-set our content to a new one of those
        selected_rail = self.story.data.get('selected_rail', "content")
        match selected_rail:
            case "content": self.content = ContentRail(self.story)
            case "characters": self.content = CharactersRail(self.story)
            case "plot": self.content = PlotlinesRail(self.story)
            case "world_building": self.content = WorldBuildingRail(self.story)
            case "canvas": self.content = CanvasRail(self.story)
            case "planning": self.content = PlanningRail(self.story)
            case _: self.content = ContentRail(self.story)
                
        # Update except on build where it updates automatically
        if update: 
            self.update()