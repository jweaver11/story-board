'''
The map class for all maps inside our story
Maps are widgets that have their own drawing canvas, and info display. they can contain nested sub maps as well.
'''

#TODO: 
# BLANK NO TEMPLATE MAPS EXIST AS WELL
# ADD DUPLICATE OPTION AS WELL
# Users can choose to create their image or use some default ones, or upload their own
# When hovering over a map, display it on the rail as well so we can see where new sub maps would

# THERES A MAP DISPLAY DUMMY, HB U CHECK THAT OUT!!!!!


import os
import json
import flet as ft
from models.widget import Widget
from models.mini_widgets.world_building.map_information_display import Map_Information_Display
from models.views.story import Story
from handlers.verify_data import verify_data
from styles.snack_bar import Snack_Bar
from models.state import State
import flet.canvas as cv
from threading import Thread



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
        
        # Supported categories: World map, continent, region, ocean, country, city, dungeon, room, none.
        
        
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
                'information_display': {'visibility': True},   # Info display mini widget visibility
                'is_displayed': True,           # Whether the map is visible in the world building widget or not
                'sub_maps': list,               # Sub maps contained within this map
                'markers': dict,                # Markers placed on the map
                'locations': dict,
                'geography': dict,              # Geography of the world
                'rooms': dict,                  
                'notes': str,

                'position': {               # Our position on our parent map when parent map is not in edit mode
                    'x': 0,                    
                    'y': 0,                     
                },

                'sub_categories': {                     # Categories for organizing our sub maps on the rail
                    'category_name': {
                        'title': str,                   # Title of the category
                        'is_expanded': bool,            # Whether the category is expanded or collapsed
                    },
                },
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

        # State handlers
        self.drawing_mode = False  
        self.dragging_mode = False  

        # Dict of our sub maps
        self.maps: list = []
        self.details = {}

        # The Visual Canvas map for drawing
        self.map = cv.Canvas(
            content=ft.GestureDetector(
                #on_pan_start=self.start_drawing,
                #on_pan_update=self.is_drawing,
                #on_pan_end=lambda e: self.save_canvas(),
                on_double_tap=lambda e: print("Double tap detected"),
                #drag_interval=10,
            ),
            expand=True
        )

        self.brush = ft.Paint(stroke_width=3)

        # The display container for our map
        self.canvas: ft.InteractiveViewer = None

        self.information_display = Map_Information_Display(
            title=self.title,
            owner=self,                     # Our map is the owner of this mini widget
            father=self,                    # Our map is also the father of this mini widget
            page=self.p,
            key="information_display",
            data=None
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

        #

        # Make it so that maps 'mini widget' shows inside of the map...
        # Multiple mini widgets able to be shown at same time
        # We render our map and all the markers, then go through our 'sub maps', find their data, and render them on top as well
        # - Sub maps only have the title still, we don't save their data
        # -- Recursively go through rendering sub maps on top of parent map

        # Adds like 1000 gd's on top of the map for right clicking and placing marks/content. The mini widget that is placed is then the...
        # Content of one of those 1000 gd's. 

        # canvas of our map (Gesture detector)
        canvas = ft.Column([
            self.map,
            ft.Row(
                expand=True,
                controls=[
                    ft.ElevatedButton("Save Drawing", on_click=lambda e: self.save_canvas()),
                    ft.ElevatedButton("Load Drawing", on_click=lambda e: self.load_canvas())
                ]
            )
        ])

        stack = ft.Stack(
            expand=True,
            controls=[
                ft.Image(
                    src="map_background.png",
                    fit=ft.ImageFit.COVER,
                    expand=True
                ),
                canvas,
            ]
        )

        canvas_container = ft.Container(
            content=stack,
            expand=True,
        )

        self.canvas = canvas_container

        self.body_container.content = self.canvas

        self._render_widget()
    



        