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
from models.widgets.canvas import Canvas


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

                'image_base64': str,  # Saves our icon as img64 string

                'markers': dict,        # Our markers on this map

                # WIP - parent maps and child maps connected to this one
                'world': str,       # The world this map belongs to
                'parent_maps': dict,        # Any parent map this map belongs too
                'child_maps': dict,         # Any child/sub maps this map has
                'alignment': {'x': 0, 'y': 0},   # Our alignment on our parent map. Both values between -1 and 1
      
            },  
        )

        
        # Drawing elements
        self.state = State()
        self.paint_brush = ft.Paint(stroke_width=3)

        # State utils
        self.drawing_mode = False  
        self.dragging_mode = False  
        self.map_width: int = 0
        self.map_height: int = 0

        # Dict of our sub maps
        self.maps: list = []
        self.details = {}


        self.canvas = cv.Canvas(
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.PRECISE,
                expand=True,
                #on_pan_start=self.start_drawing,
                #on_pan_update=self.is_drawing,
                #on_pan_end=lambda e: self.save_canvas(),
                #on_tap_up=self.add_point,      # Handles so we can add points
                on_secondary_tap=lambda e: print("TEMP"),
                drag_interval=10,
            ),
            expand=True, resize_interval=100,
            on_resize=self._rebuild_map_canvas, 
        )



        self.information_display = MapInformationDisplay(
            title=self.title,
            owner=self,                     # Our map is the owner of this mini widget
            father=self,                    # Our map is also the father of this mini widget
            page=self.p,
            key="information_display",
            data=None
        )

        self.map_gd = ft.GestureDetector(
            hover_interval=10,
            mouse_cursor=ft.MouseCursor.PRECISE,   
            on_tap=lambda e: print("Open Information Display"),
            on_secondary_tap=lambda e: print("Open menu to add marker or sub map"),
            on_enter=lambda e: print("Show hover effects"),
            on_exit=lambda e: print("Hide hover effects"),
            on_hover=self._hover_gd,
            content=ft.Container(
                expand=True, ignore_interactions=True,
                image=ft.DecorationImage("map_background.png", fit=ft.ImageFit.FILL)    # Our background image
            ),
        )


        self.mini_widgets.append(self.information_display)
        

        # Reloads the information canvas of the map
        self.reload_widget()


    def _toggle_drawing_mode(self):
        ''' Toggles our drawing mode on/off '''
        self.data['in_drawing_mode'] = not self.data.get('in_drawing_mode')
        print("Toggling drawing mode to:", self.data.get('in_drawing_mode'))
        self.save_dict()
        self.reload_widget()


    async def _hover_gd(self, e: ft.HoverEvent):
        ''' Handles our hover over the map '''
        # Set coordinates for menu
        self.story.mouse_x = e.global_x
        self.story.mouse_y = e.global_y

        # Calculate and set our alignments for new items
        w = max(int(self.map_width or 0), 1)
        x = float(e.local_x)
        raww = (2.0 * x / w) - 1.0
        raww = max(-1.0, min(1.0, raww))

        # Calculate and set our y alignment
        h = max(int(self.map_height or 0), 1)
        y = float(e.local_y)
        rawh = (2.0 * y / h) - 1.0
        rawh = max(-1.0, min(1.0, rawh))

        self.data['alignment']['x'] = round(raww, 2)
        self.data['alignment']['y'] = round(rawh, 2)

        print("New x alignment:", self.data.get('alignment').get('x'), "New Y alignment:", self.data.get('alignment').get('y'))


    # Called for any size changes to our map canvas
    async def _rebuild_map_canvas(self, e: cv.CanvasResizeEvent=None):
        ''' Redraws our map on the canvas when it is resized. Does it on startup as well '''

        # Update our page reference and size
        self.canvas.page = self.p
        self.map_width = int(e.width)
        self.map_height = int(e.height)
        print("Rebuilding map canvas to size:", self.map_width, "x", self.map_height)


    # Called when we need to rebuild out map UI
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
            expand=True, alignment=ft.Alignment(.95, -.95),
            controls=[
                self.canvas,    # Our drawing canvas on bottom. From here, it is not actually used other than resizing logic
                self.map_gd
            ]  # Gestured Detector, which holds our background image, on the bottom
        )

        iv = ft.InteractiveViewer(
            content=stack, expand=True,
            scale_factor=750, boundary_margin=50,
            min_scale=0.5, max_scale=2.0, scale=1.0,
        )

        # If we're in drawing mode, Insert our canvas over the gesture detector
        if self.data.get('in_drawing_mode'):
            del stack.controls[0]   # Remove the canvas from the bottom where it only handles resizing, and put it overtop the gd
            stack.controls.append(self.canvas)   
            
  

        iv.content = stack


        self.header = ft.Row([
            ft.IconButton(
                ft.Icons.DRAW_OUTLINED if not self.data.get('in_drawing_mode') else ft.Icons.DONE,
                tooltip="Enter Drawing Mode" if not self.data.get('in_drawing_mode') else "Exit Drawing Mode",
                on_click=lambda e: self._toggle_drawing_mode(),
            ),
            # Undo and redo buttons
            ft.PopupMenuButton(
                icon=ft.Icons.IMAGE_ASPECT_RATIO_OUTLINED, tooltip="Set the background of your canvas. If one is set, it will be exported with the canvas",
                menu_padding=ft.padding.all(0), 
                #on_cancel=self._set_color,
                items=[
                    #ft.PopupMenuItem("None", on_click=self._set_canvas_background, tooltip="No background"),
                    #ft.PopupMenuItem("Color", on_click=self._set_canvas_background, tooltip="Set a solid color background"),
                    #ft.PopupMenuItem("Image", on_click=self._set_canvas_background, tooltip="Set an image as the background"),
                ]
            ),
            # Show information display
            ft.IconButton(
                ft.Icons.INFO_OUTLINED,
                tooltip="Toggle Information Display",
                on_click=lambda e: self.information_display.toggle_visibility(value=True),
            ),
            # Button to hide markers
        ])

        self.body_container.content = ft.Column([self.header, ft.Divider(thickness=2, height=8), iv], spacing=0)


        self._render_widget()
    



        