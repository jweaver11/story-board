'''
The map class for all maps inside our story
Maps are widgets that have their own drawing canvas, background image, information display, and markers/locations
'''



import os
import json
import flet as ft
from models.widget import Widget
from models.mini_widgets.map_information_display import MapInformationDisplay
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
                # Widget data
                'tag': "map", 
                'color': app.settings.data.get('default_map_color'),
                'icon': "map_outlined",     # What icon to render on a parent map (if we have one)

                # State and view data
                'information_display_visibility': True,   # Info display mini widget visibility
                'in_drawing_mode': bool,            # Whether we are in drawing mode or not
                'image_base64': str,                # Saves our icon as img64 string (Used a preview as well from other widgets)
                'left': int,                        # Our left position on our parent map (if we have one)
                'top': int,                         # Our top position on our parent map (if we have one)
                              
                'locations': dict,        # Our locations on this map. Locations can also be maps
                # If location is a map, it just has a tag and the maps key to reference it so we can open its information display when clicking it

                # Map data for the information display
                'map_data': {
                    'Summary': str,
                }
                # TODO: 
                # Users can choose to create their image or use some default ones, or upload their own
                # THERES A MAP DISPLAY DUMMY, HB U CHECK THAT OUT!!!!!
            },  
        )

        
        # Drawing elements
        self.state = State()
        self.paint_brush = ft.Paint(stroke_width=3)

        # State utils
        self.drawing_mode = False  
        self.map_width: int = 0
        self.map_height: int = 0
        self.l: int = 0      # Values to pass into locations for left and top coordinates
        self.t: int = 0

        # Dict of our sub maps
        self.maps: list = []
        self.details = {}

        self.information_display = MapInformationDisplay(
            title=self.title,
            owner=self,                     # Our map is the owner of this mini widget
            page=self.p,
            key="information_display",
            data=None
        )


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

        self.map_gd = ft.GestureDetector(
            hover_interval=20,
            mouse_cursor=ft.MouseCursor.PRECISE,   
            on_tap=self.tap_gd,
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
        

        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Called when clicking on our map to show our information display
    async def tap_gd(self, e: ft.TapEvent):
        ''' If we're not in drawing mode, show our information display '''
        if not self.drawing_mode:
            self.information_display.show_mini_widget()

    # Called to toggle our drawing mode on/off
    def _toggle_drawing_mode(self):
        ''' Toggles our drawing mode on/off '''

        # Change our data value for drawing mode and save it
        self.data['in_drawing_mode'] = not self.data.get('in_drawing_mode', False)
        self.save_dict()
        
        # If we entered drawing mode, show our drawing canvas rail. Otherwise, go back to the previous rail
        if self.data['in_drawing_mode']:
            self.story.active_rail.display_active_rail(self.story, "canvas")
        else:
            self.story.active_rail.display_active_rail(self.story)

        self.reload_widget()    # Reload our widget

    # Called when mouse hovers over the map
    async def _hover_gd(self, e: ft.HoverEvent):
        ''' Sets our coordinate positions for menus and passing in new items '''
        self.story.mouse_x = e.global_x
        self.story.mouse_y = e.global_y
        self.l = e.local_x
        self.t = e.local_y


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

        
        # We render our map and all the markers, then go through our 'sub maps', find their data, and render them on top as well
        # - Sub maps only have the title still, we don't save their data
        # -- Recursively go through rendering sub maps on top of parent map


        
        # Create our stack that will hold our background image, canvas, and map elements
        stack = ft.Stack(
            expand=True, #alignment=ft.Alignment(.95, -.95),
            controls=[
                self.canvas,    # Our drawing canvas on bottom. From here, it is not actually used other than resizing logic
                self.map_gd
            ]  # Gestured Detector, which holds our background image, on the bottom
        )

        for mw in self.mini_widgets:
            if hasattr(mw, 'map_control'):
                stack.controls.append(mw.map_control)
                

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


        header = ft.Row([
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
                on_click=self.information_display.show_mini_widget,
            ),
            # Button to hide markers
        ])

        self.body_container.content = ft.Column([header, ft.Divider(thickness=2, height=8), iv], spacing=0)


        self._render_widget()
    



        