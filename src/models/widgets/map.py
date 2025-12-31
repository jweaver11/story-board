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
        father: str = None,                     # Parent map this map belongs to (using data['key'] of the parent map)
        category: str = None,                   # Type of map this is (world map, continent, country, city, dungeon, room, etc)
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
                'father': father,               # Parent map this map belongs to. None if top level map
                'information_display': {'visibility': True},   # Info display mini widget visibility
                'category': category,           # Category/psuedo folder this map belongs to
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
                on_pan_start=self.start_drawing,
                on_pan_update=self.is_drawing,
                on_pan_end=lambda e: self.save_canvas(),
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

        # Load our drawing/display
        self.load_canvas()
        

        # Reloads the information canvas of the map
        self.reload_widget()


    # Store their data in their own files, so lets make them widgets
    # Their map dict is now list, and contains the title of their sub maps, not the data


    # Called when loading our drawing data from its file
    def load_canvas(self):
        ''' Loads our drawing from our saved map drawing file '''

        # Clear existing shapes we might have
        self.map.shapes.clear()

        try:

            # Set our file path
            filename = os.path.join(self.directory_path, f"{self.title}_canvas.json")

            # Check if file exists, if not create it with empty data
            if not os.path.exists(filename):
                with open(filename, "w") as f:
                    json.dump({}, f)    

            # Load the data from the file
            with open(filename, "r") as f:
                coords = json.load(f)
                for x1, y1, x2, y2 in coords:
                    self.map.shapes.append(cv.Line(x1, y1, x2, y2, paint=ft.Paint(stroke_width=3)))

            # Update the page to reflect loaded drawing
            self.p.update()

        # Handle errors
        except Exception as e:
            print(f"Error loading canvas from {filename}: {e}")

    # Called to save our drawing data to its file
    def save_canvas(self):
        ''' Saves our map drawing data to its own json file. Maps are special and get their 'drawing' saved seperately '''

        try:

            # Set our file path
            file_path = os.path.join(self.directory_path, f"{self.title}_canvas.json")

            # Create the directory if it doesn't exist. Catches errors from users deleting folders
            os.makedirs(self.directory_path, exist_ok=True)
            
            # Save the data to the file (creates file if doesnt exist)
            with open(file_path, "w") as f:   
                json.dump(self.state.shapes, f)
        
        # Handle errors
        except Exception as e:
            print(f"Error saving widget to {file_path}: {e}") 
            print("Data that failed to save: ", self.state.shapes)


    # Use our parent delete file method, and delete our canvas as well
    def delete_file(self, old_file_path) -> bool:

        # Call our parent delete first
        if super().delete_file(old_file_path):

            try:

                # Set our canvas file path
                file_path = os.path.join(self.directory_path, f"{self.title}_canvas.json")

                # Delete the file if it exists
                if os.path.exists(file_path):
                    os.remove(file_path)
                else:
                    print(f"File {old_file_path} does not exist, cannot delete.")

                return True

            except Exception as e:
                print(f"Error deleting map canvas file: {e}")
                return False

        else:
            return False
        

    # Called when renaming our map
    def rename(self, title: str):
        ''' Calls our parent to rename our json file, and then renames our canvas file as well '''

        # Save our old title
        old_title = self.title

        # Call parent to rename our main widget file
        super().rename(title)

        # Save our old file path for renaming our canvas
        old_file_path = os.path.join(self.directory_path, f"{old_title}_canvas.json")     
                                               
        # Rename our canvas file 
        os.rename(old_file_path, self.data['key'] + "_canvas" + ".json") 

        # Save our canvas
        self.save_canvas()

    # Called when moving file
    def move_file(self, new_directory):
        ''' Calls parent move, and then save canvas to give us our new canvas file '''

        # Copy canvas file here first

        # Call our parent move file. Since we defined our own delete file, it will delete the canvas file as well
        super().move_file(new_directory)

        # TODO: Paste new canvas file with correct title

        # Now save our new canvas file
        self.save_canvas()
            

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


    async def start_drawing(self, e: ft.DragStartEvent):
        self.state.x, self.state.y = e.local_x, e.local_y

    async def is_drawing(self, e: ft.DragUpdateEvent):
        def draw_line():
            line = cv.Line(
                self.state.x, self.state.y, e.local_x, e.local_y,
                paint=self.paint_brush
            )
            self.map.shapes.append(line)
            self.state.shapes.append((self.state.x, self.state.y, e.local_x, e.local_y))
            #self.map.update()
            self.p.update()
            self.state.x, self.state.y = e.local_x, e.local_y
        Thread(target=draw_line, daemon=True).start()

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
    



        