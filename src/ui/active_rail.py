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
from constants import MIN_ACTIVE_RAIL_WIDTH


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

    def toggle_collapse_rail(self, e: ft.Event[ft.IconButton]):
        # use the resizer as our state
        if self.width > 40:
            self.width = 40
            e.control.icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT_ROUNDED
            self.content.controls[0].visible = False
        else:
            self.width = MIN_ACTIVE_RAIL_WIDTH
            e.control.icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED
            self.content.controls[0].visible = True
        self.update()
        app.settings.update_data(**{'story': {'active_rail_width': self.width}})
        
    # Reload our rail on startup
    def build(self):
        self.reload_rail(update=False)
        
    # Called when a new workspace is selected
    def reload_rail(self, update: bool=True):
        ''' Reloads the active rail based on the selected workspace in workspaces_rail '''

        # Grab our selected rail and re-set our content to a new one of those
        selected_rail = self.story.data.get('selected_rail', "content")
        match selected_rail:
            case "content": selected_rail = ContentRail(self.story)
            case "characters": selected_rail = CharactersRail(self.story)
            case "plot": selected_rail = PlotlinesRail(self.story)
            case "world_building": selected_rail = WorldBuildingRail(self.story)
            case "canvas": selected_rail = CanvasRail(self.story)
            case "planning": selected_rail = PlanningRail(self.story)
            case _: selected_rail = ContentRail(self.story)

        if self.width > 40:
            collapse_icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED
            col_visible = True
        else:
            collapse_icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT_ROUNDED
            col_visible = False  # Hide the rail if it's collapsed

        # To collapse the active rail
        collapse_icon_button = ft.IconButton(
            collapse_icon, ft.Colors.PRIMARY,
            on_click=self.toggle_collapse_rail,
        )

        self.content = ft.Stack(
            [
                ft.Column([selected_rail], expand=True, visible=col_visible),    # Force rail to take up all the space
                ft.Column([ft.Row([collapse_icon_button], alignment=ft.MainAxisAlignment.END)], expand=True, alignment=ft.MainAxisAlignment.END)
            ], 
            expand=True
        )
                
        # Update except on build where it updates automatically
        if update: 
            self.update()