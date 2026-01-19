'''
The map class for all maps inside our story
Maps are widgets that have their own drawing canvas, background image, information display, and markers/locations
'''

# TODO: 
# BLANK NO TEMPLATE MAPS EXIST AS WELL
# ADD DUPLICATE OPTION AS WELL
# Users can choose to create their image or use some default ones, or upload their own
# When hovering over a map, display it on the rail as well so we can see where new sub maps would

# THERES A MAP DISPLAY DUMMY, HB U CHECK THAT OUT!!!!!


import os
import json
import flet as ft
from models.widget import Widget
from models.mini_widgets.world_building.map_information_display import MapInformationDisplay
from models.views.story import Story
from utils.verify_data import verify_data
from styles.snack_bar import SnackBar
from models.dataclasses.state import State
import flet.canvas as cv
from threading import Thread
from models.app import app



class Map(Widget):

    # Constructor. Requires title, owner widget, page reference, world map owner, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        page: ft.Page, 
        directory_path: str, 
        story: Story,                  
        data: dict = None
    ):
        
                
        # Parent constructor
        super().__init__(
            title=title,           
            page=page,                         
            directory_path=directory_path, 
            story=story,
            data=data,  
        ) 


        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   
            {
                'tag': "map", 
                'color': app.settings.data.get('default_map_color'),

                'information_display_visibility': True,   # Info display mini widget visibility
                              
                'summary': str,
                'in_drawing_mode': bool,         # Whether we are in drawing mode or not

                'markers': dict,        # Our markers on this map

                # WIP - parent maps and child maps connected to this one
                'world': str,       # The world this map belongs to
                'parent_maps': dict,        # Any parent map this map belongs too
                'child_maps': dict,         # Any child/sub maps this map has
                'alignment': {'x': 0, 'y': 0},   # Our alignment on our parent map. Both values between -1 and 1
      
            },  
        )

        # UI Elements
        self.interactive_viewer: ft.InteractiveViewer = None    # Our interactive viewer for zooming and panning
        self.stack: ft.Stack = None                             # Our main stack for layering the map elements
        self.background_image: ft.Image = None                  # Background image (if we have one) that goes
        self.canvas: cv.Canvas = None                           # Our drawing canvas overtop the background image
        self.top_layer: ft.Container = None                     # Top layer to show our locations, markers, etc. on top of the canvas


        # Drawing elements
        self.state = State()
        self.paint_brush = ft.Paint(stroke_width=3)

        # State utils
        self.drawing_mode = False  
        self.dragging_mode = False  

        # Dict of our sub maps
        self.maps: list = []
        self.details = {}


        # The display container for our map
        self.canvas: ft.InteractiveViewer = None

        self.information_display = MapInformationDisplay(
            title=self.title,
            owner=self,                     # Our map is the owner of this mini widget
            father=self,                    # Our map is also the father of this mini widget
            page=self.p,
            key="information_display",
            data=None
        )

        self.map_gd = ft.GestureDetector(
            content=ft.Stack(),     # Stack to add our 
            on_secondary_tap=lambda e: print("Open menu to add marker or sub map"),
            on_tap=lambda e: print("Open Information Display"),
            on_enter=lambda e: print("Show hover effects"),
            on_exit=lambda e: print("Hide hover effects"),
            on_hover=lambda e: print("Update our alignment/offset so new items know where to go")
        )

        self.mini_widgets.append(self.information_display)
        
        # Load the rest of our map details and data thats not sub maps
        self.load_details()

        # Reloads the information canvas of the map
        self.reload_widget()


    # Store their data in their own files, so lets make them widgets
    # Their map dict is now list, and contains the title of their sub maps, not the data


    

            

    def load_details(self):
        ''' Loads the rest of our map details that are not sub maps into our details dict '''
        #self.load_locations()
        #self.load_lores()
        #self.load_history()
        #self.load_power_systems()
        #self.load_technology()
        #self.load_social_systems()
        #self.load_governments()
        pass
 

    def on_hover(self, e: ft.HoverEvent):
        #print(e)
        pass
        # Grab local mouse to figure out x and map it to our timeline


    

    # Called when we need to rebuild out timeline UI
    def reload_widget(self):       
        ''' Rebuilds/reloads our map UI '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        
        # Make it so that maps 'mini widget' shows inside of the map...
        # We render our map and all the markers, then go through our 'sub maps', find their data, and render them on top as well
        # - Sub maps only have the title still, we don't save their data
        # -- Recursively go through rendering sub maps on top of parent map


        
        # Create our stack that will hold our background image, canvas, and map elements
        stack = ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    expand=True, ignore_interactions=True,
                    image=ft.DecorationImage("map_background.png", fit=ft.ImageFit.FILL)    # Our background image
                ),
                
                
                ft.Container(bgcolor="red", height=50, width=50, shape=ft.BoxShape.CIRCLE),
                
            ]
        )





        #stack.controls.append(self.canvas)

        self.body_container.content = stack


        self._render_widget()
    



        