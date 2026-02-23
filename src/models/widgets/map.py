'''
The map class for all maps inside our story
Maps are widgets that have their own drawing canvas, background image, information display, and locations
'''


import flet as ft
from models.widget import Widget
from models.mini_widgets.map_information_display import MapInformationDisplay
from models.views.story import Story
from utils.verify_data import verify_data
from models.dataclasses.state import State
import flet.canvas as cv
from models.app import app
from styles.menu_option_style import MenuOptionStyle
import asyncio


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

                'drawing_mode': bool,            # Whether we are in drawing mode or not
                'image_base64': str,                # Saves our icon as img64 string (Used a preview as well from other widgets)
                'left': int,                        # Our left position on our parent map (if we have one)
                'top': int,                         # Our top position on our parent map (if we have one)
                              
                'locations': dict,        # Our locations on this map. Locations can also be maps
                # If location is a map, it just has a tag and the maps key to reference it so we can open its information display when clicking it

                # Map data for the information display
                'map_data': dict,
                
                
            },  
        )

        
        # Drawing elements
        self.state = State()
        self.paint_brush = ft.Paint(stroke_width=3)

        # State utils
        self.map_width: int = 0
        self.map_height: int = 0
        

        # Dict of our sub maps
        self.maps: list = []
        self.details = {}

        # Declare and create our information display, which is our maps
        self.information_display: ft.Container = None
        self._create_information_display()


        self.canvas = cv.Canvas(
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.PRECISE if self.data.get('drawing_mode') else ft.MouseCursor.CLICK, 
                expand=True,

                # Drawing event handlers
                #on_pan_start=self.start_drawing,
                #on_pan_update=self.is_drawing,
                #on_pan_end=lambda e: self.save_canvas(),
                #on_tap_up=self.add_point,      # Handles so we can add points

                # Non-drawing event handlers
                on_secondary_tap=lambda e: self.story.open_menu(self._get_menu_options()),
                on_hover=self._get_coords,
                on_tap=self._show_info_display,
                drag_interval=500, hover_interval=20,
            ),
            expand=True, resize_interval=100,
            on_resize=self._rebuild_map_canvas, 
        )

        # Our stack for map locations
        self.map_stack = ft.Stack([
            ft.Container(
                expand=True, ignore_interactions=True,
                #image=ft.DecorationImage("map_background.png", fit=ft.ImageFit.FILL)    # Our background image
            ),
            self.canvas,
        ], expand=True)
           
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Called in the constructor
    def _create_information_display(self):
        ''' Creates our plotline information display mini widget '''
        
        self.information_display = MapInformationDisplay(
            title=self.title,
            owner=self,
            page=self.p,
            key="map_data",     # Not used, but its required so just whatever works
            data=self.data.get('map_data'),      
        )
        # Add to our mini widgets so it shows up in the UI
        self.mini_widgets.append(self.information_display)

    def load_locations(self):
        pass
        # For location in location. Check tag, create location object (or map object). Add to self.locations

    # Called when clicking on our map to show our information display
    async def _show_info_display(self, e: ft.TapEvent):
        ''' If we're not in drawing mode, show our information display '''
        if not self.data.get('drawing_mode'):
            self.information_display.show_mini_widget()

    # Called when right cliicking a new pp, arc, or marker ON the plotline to create it at a specific location
    async def new_item_clicked(self, e):
        ''' Opens a dialog to input the mini widgets name, and creates it at that location '''

        # Checks that the name in the textfield does not match any of the existing mini widgets of that type, and updates visually to reflect
        async def _check_name_unique(e):
            name = new_item_tf.value.strip()
            submit_button.disabled = False
            new_item_tf.error_text = None
            if not name:
                submit_button.disabled = True
            elif tag == "plot_point" and name in self.plot_points:
                submit_button.disabled = True
                new_item_tf.error_text = "Name must be unique"
                new_item_tf.focus()
            elif tag == "arc" and name in self.arcs:
                submit_button.disabled = True
                new_item_tf.error_text = "Name must be unique"
                new_item_tf.focus()
            elif tag == "marker" and name in self.markers:
                submit_button.disabled = True
                new_item_tf.error_text = "Name must be unique"
                new_item_tf.focus()

            else:
                submit_button.disabled = False
                new_item_tf.error_text = None
            
            new_item_tf.update()
            submit_button.update()
            
        # Create the nwew mini widget with the current text field value. Makes sure we passed checks first
        async def _create_new_mw(e):

            # Button is disabled if name is the same
            if submit_button.disabled:
                new_item_tf.focus()
                return
            
            title = new_item_tf.value.strip()
            if tag == "plot_point":
                await self.create_plot_point(title)
            
                

            if self.information_display.visible:
                self.information_display.reload_mini_widget()

            self.p.close(dlg)   # Close the dialog

            await asyncio.sleep(0.1)        # Needs a buffer or wont work for some reason
            await self.story.close_menu()       


        # Grab the type of mini widget we are creating
        tag = e.control.data

        # Textfield for the name of the new mw
        new_item_tf = ft.TextField(
            label=f"Title", expand=True, on_change=_check_name_unique, autofocus=True,
            capitalization=ft.TextCapitalization.WORDS, on_submit=_create_new_mw
        )

        # Button for creating new mw. Can also press enter in the textfield
        submit_button = ft.TextButton("Create", on_click=_create_new_mw, disabled=True)

        # Dialog we open onto the page
        dlg = ft.AlertDialog(
            title=ft.Text(f"New {tag.replace('_', ' ').title()} Name"),
            content=new_item_tf,
            actions=[
                ft.TextButton("Cancel", style=ft.ButtonStyle(color=ft.Colors.ERROR), on_click=lambda e: self.p.close(dlg)),
                submit_button
            ],
        )

        self.p.open(dlg)    

            

    # Called to toggle our drawing mode on/off
    def _toggle_drawing_mode(self):
        ''' Toggles our drawing mode on/off '''

        # Change our data value for drawing mode and save it
        self.data['in_drawing_mode'] = not self.data.get('in_drawing_mode', False)
        self.save_dict()
        
        # If we entered drawing mode, show our drawing canvas rail. Otherwise, go back to the previous rail
        if self.data['in_drawing_mode']:
            self.story.active_rail.display_active_rail(self.story, "canvas")
            self.canvas.content.mouse_cursor = ft.MouseCursor.PRECISE
        else:
            self.story.active_rail.display_active_rail(self.story)
            self.canvas.content.mouse_cursor = ft.MouseCursor.CLICK

        self.reload_widget()    # Reload our widget

    

    def _get_menu_options(self) -> list[ft.Control]:
        async def new_item_clicked(e):
            ''' Called when new plot point or arc is clicked from plotline context menu '''
            
            tag = e.control.data

            if tag is not None:
                match tag:
                    #case 'arc':
                        #await self.create_arc(f"Arc {len(self.arcs) + 1}")
                   # case "marker":
                        #await self.create_marker(f"Marker {len(self.markers) + 1}")
                    #case 'plot_point':  
                        #await self.create_plot_point(f"Plot Point {len(self.plot_points) + 1}")
                    case _:
                        pass
            else:
                print("Error: No tag found for new item creation")

            await asyncio.sleep(.3)
            await self.story.close_menu()

        async def _show_info_display(e):
            ''' Shows our information display mini widget '''
            self.information_display.show_mini_widget()
            await self.story.close_menu()

        # New (all dif types of locations), rename color
        return [
             MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New Location", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                    tooltip="New Location", menu_padding=0,
                    items=[
                        ft.PopupMenuItem(
                            text="Blank", icon=ft.Icons.CHECK_BOX_OUTLINE_BLANK,
                            on_click=new_item_clicked, data="blank"
                        ),
                        ft.PopupMenuItem(
                            text="Sub Map", icon=ft.Icons.MAP_OUTLINED,
                            on_click=new_item_clicked, data="sub_map"
                        ),
                        
                    ]
                ),
            ),
            MenuOptionStyle(
                on_click=_show_info_display,
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE),
                    ft.Text(
                        "Show Info", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            # Delete button
            MenuOptionStyle(
                on_click=self._rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            # Color changing popup menu
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    expand=True,
                    tooltip="",
                    padding=None,
                    content=ft.Row(
                        expand=True,
                        controls=[
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=self.data.get('color', None)),
                            ft.Text("Color", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True), 
                        ]
                    ),
                    items=self._get_color_options()
                )
            ),
        ]
    



    # Called for any size changes to our map canvas
    async def _rebuild_map_canvas(self, e: cv.CanvasResizeEvent=None):
        ''' Redraws our map on the canvas when it is resized. Does it on startup as well '''

        # Update our page reference and size
        self.canvas.page = self.p
        self.map_width = int(e.width)
        self.map_height = int(e.height)
        self._render_widget()


    # Called when we need to rebuild out map UI
    def reload_widget(self):       
        ''' Rebuilds/reloads our map UI '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        # TODO: 
        # Users can choose to create their image or use some default ones, or upload their own

        # Clear our map stack controls so we can re-add them
        self.map_stack.controls.clear()
        self.map_stack.controls = [     # Add our background and canvas
            ft.Container(
                expand=True, ignore_interactions=True,
                image=ft.DecorationImage("map_background.png", fit=ft.ImageFit.FILL)    # Our background image
            ),
            self.canvas,
        ]

        # Add our map locations to the stack
        for mw in self.mini_widgets:
            if hasattr(mw, 'map_control'):
                self.map_stack.controls.append(mw.map_control)
                
        # Create our interactive viewer for panning and zooming
        iv = ft.InteractiveViewer(
            content=self.map_stack, expand=True,
            scale_factor=750, boundary_margin=50,
            min_scale=0.5, max_scale=2.0, scale=1.0,
        )


        # Create our header
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


        # Not used, but changes how our mini widgets are positioned
        self.header = ft.Container(ignore_interactions=True, height=50)


        self._render_widget()
    



        