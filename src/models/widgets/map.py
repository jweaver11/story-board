'''
The map class for all maps inside our story
Maps are widgets that have their own drawing canvas, background image, information display, and locations
'''


import flet as ft
from models.widget import Widget
from models.mini_widgets.map_info import MapInformationDisplay
from models.views.story import Story
from utils.verify_data import verify_data
from models.dataclasses.canvas_state import State
import flet.canvas as cv
from models.app import app
from styles.menu_option_style import MenuOptionStyle
import asyncio
from models.mini_widgets.location import Location
from utils.safe_string_checker import return_safe_name


class Map(Widget):

    # Constructor. Requires title, widget widget, page reference, world map widget, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        page: ft.Page, 
        directory_path: str, 
        story: Story,                  
        data: dict = None,
        is_rebuilt: bool = False
    ):
        
        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True
        
                
        # Parent constructor
        super().__init__(
            title=title,           
            page=page,                         
            directory_path=directory_path, 
            story=story,
            data=data,  
            is_rebuilt = is_rebuilt
        ) 


        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_map",
                'tag': "map", 
                'color': app.settings.data.get('default_map_color'),
                'icon': "map_outlined",     # What icon to render on a parent map (if we have one)

                
                'image_base64': str,                # Saves our icon as img64 string (Used a preview as well from other widgets)
                'left': int,                        # Our left position on our parent map (if we have one)
                'top': int,                         # Our top position on our parent map (if we have one)
                              
                'locations': dict,        # Our locations on this map. Locations can also be maps
                # If location is a map, it just has a tag and the maps key to reference it so we can open its information display when clicking it

                # Map data for the information display
                'map_data': dict,
                
                
            },  
        )

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)

        
        # Drawing elements
        self.state = State()
        self.paint_brush = ft.Paint(stroke_width=3)

        # State utils
        self.map_width: int = 0
        self.map_height: int = 0
        

        # Dict of our sub maps
        self.locations: dict = {}
        self.information_display: ft.Container 

        self.load_locations()
        self._create_information_display()


        self.canvas = cv.Canvas(
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.PRECISE if self.data.get('map_data', {}).get('drawing_mode') else ft.MouseCursor.CLICK, 
                expand=True,

                # Drawing event handlers
                #on_pan_start=self.start_drawing,
                #on_pan_update=self.is_drawing,
                #on_pan_end=lambda e: self.save_canvas(),
                #on_tap_up=self.add_point,      # Handles so we can add points

                # Non-drawing event handlers
                on_secondary_tap=lambda e: self.story.open_menu(self._get_menu_options()),
                on_hover=self._get_coords,
                #on_tap=self._show_info_display,
                on_tap=lambda e: self.story.open_menu(self._get_menu_options()),
                drag_interval=5, hover_interval=20,
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

        # Canvas has a custom tab, so it re-uses almost everything from widget
        # UI ELEMENTS - Tab
        self.tabs: ft.Tabs 
        self.tab: ft.Tab  
        self.icon: ft.Icon
        self.tab_text: ft.Text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True)

        # Grabs our tag to determine the icon we'll use
        tag = self.data.get('tag', '')

        # Set our icon based on what type of widget we are using tag
        match tag:
            case "document": self.icon = ft.Icon(ft.Icons.DESCRIPTION_OUTLINED)
            case "canvas": self.icon = ft.Icon(ft.Icons.BRUSH_OUTLINED)
            case "canvas_board": self.icon = ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED)
            case "note": self.icon = ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED)
            case "character": self.icon = ft.Icon(ft.Icons.PERSON_OUTLINE)
            case "character_connection_map": self.icon = ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED)
            case "plotline": self.icon = ft.Icon(ft.Icons.TIMELINE)
            case "map": self.icon = ft.Icon(ft.Icons.MAP_OUTLINED)
            case "world": self.icon = ft.Icon(ft.Icons.PUBLIC_OUTLINED)
            case "object": self.icon = ft.Icon(ft.Icons.SHIELD_OUTLINED)
            case _: self.icon = ft.Icon(ft.Icons.ERROR_OUTLINE)


        # Set the color and size
        self.icon = ft.IconButton(
            ft.Icons.MAP_OUTLINED, self.data.get('color', ft.Colors.PRIMARY), 
            mouse_cursor=ft.MouseCursor.CLICK, on_click=self.information_display.show_mini_widget,
            tooltip="Show Canvas Info",
        )
        

        tab_text = ft.Text(self.title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True)
        
        # Our icon button that will hide the widget when clicked in the workspace
        hide_tab_icon_button = ft.IconButton(    # Icon to hide the tab from the workspace area
            scale=0.8,
            on_click=self.hide_widget,
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Hide",
            mouse_cursor=ft.MouseCursor.CLICK,
        )


        self.tab_gd = ft.GestureDetector(
            ft.Row(
                [self.icon, tab_text, hide_tab_icon_button],
                spacing=0
            ),     # Changes here to add show info button
            mouse_cursor=ft.MouseCursor.CLICK,
            hover_interval=100,
            on_hover=self._set_coords,
            on_secondary_tap=lambda _: self.story.open_menu(self._get_menu_options()),
        )

        # Tab that holds our widget title and 'body'.
        # Since this is a ft.Tab, it needs to be nested in a ft.Tabs control or it wont render.
        self.tab = ft.Tab(

            # Content of the tab itself. Has widgets name and hide widget icon, and functionality for dragging
            label=ft.Draggable(   # Draggable is the control so we can drag and drop to different pin locations
                group="widgets",    # Group for draggables (and receiving drag targets) to accept each other
                data=self.data.get('key', ""),  # Pass ourself through the data (of our tab, NOT our object) so we can move ourself around

                # Drag event utils
                on_drag_start=self._start_drag,    # Shows our pin targets when we start dragging

                # Content when we are dragging the follows the mouse
                content_feedback=ft.TextButton(self.title), # Normal text won't restrict its own size, so we use a button

                # The content of our draggable. We use a gesture detector so we have more events
                content=self.tab_gd
            )                    
        )

        # Tabs stuff
        self.tabs = ft.Tabs(
            expand=True,  
            length=1,
            selected_index=0,
            content=ft.Column([
                ft.TabBar(tabs=[self.tab]),     # Holds our tab at the top of the widget
                ft.TabBarView([self.master_stack], expand=True)# Holds our body
            ], expand=True),
            
        )   
        self.content = self.tabs
           
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init

    # Called in the constructor
    def _create_information_display(self):
        ''' Creates our plotline information display mini widget '''
        
        self.information_display = MapInformationDisplay(
            title=self.title,
            widget=self,
            page=self.p,
            key="map_data",    
            data=self.data.get('map_data'),      
        )
        # Add to our mini widgets so it shows up in the UI
        self.mini_widgets.append(self.information_display)

    async def create_location(self, title: str, data: dict=None):
        
        new_location = Location(
            title=title,
            widget=self,
            page=self.p,
            key="locations",   
            data=data,      
            left=self.l,
            top=self.t
        )
       
        self.locations[title] = new_location
        self.mini_widgets.append(new_location)
        self.reload_widget()

    def load_locations(self):
        for title, data in self.data.get('locations', {}).items():
            self.locations[title] = Location(
                title=title,
                widget=self,
                page=self.p,
                key="locations",     # Not used, but its required so just whatever works
                data=data,
            )
            self.mini_widgets.append(self.locations[title])

    # Called when clicking on our map to show our information display
    async def _show_info_display(self, e: ft.TapEvent):
        ''' If we're not in drawing mode, show our information display '''
        if not self.data.get('map_data', {}).get('drawing_mode', False):
            self.information_display.show_mini_widget()

    # Called when right cliicking a new pp, arc, or marker ON the plotline to create it at a specific location
    async def new_location_clicked(self, e):
        ''' Opens a dialog to input the mini widgets name, and creates it at that location '''

        # Checks that the name in the textfield does not match any of the existing mini widgets of that type, and updates visually to reflect
        async def _check_name_unique(e):
            name = new_item_tf.value.strip()
            submit_button.disabled = False
            new_item_tf.error_text = None
            if not name:
                submit_button.disabled = True
            elif name in self.locations:
                submit_button.disabled = True
                new_item_tf.error = "Name must be unique"
                await new_item_tf.focus()

            else:
                submit_button.disabled = False
                new_item_tf.error = None
            
            new_item_tf.update()
            submit_button.update()
            
        # Create the nwew mini widget with the current text field value. Makes sure we passed checks first
        async def _create_new_mw(e):

            # Button is disabled if name is the same
            if submit_button.disabled:
                new_item_tf.focus()
                return
            
            title = new_item_tf.value.strip()
            await self.create_location(title, data)
            
            if self.information_display.visible:
                self.information_display.reload_mini_widget()

            self.p.pop_dialog()   # Close the dialog

            #await asyncio.sleep(0)        # Needs a buffer or wont work for some reason
            await self.story.close_menu()       


        # Grab the type of mini widget we are creating
        data = e.control.data
        print("Data for new location:", data)

        # Textfield for the name of the new mw
        new_item_tf = ft.TextField(
            label=f"Location Name", expand=True, on_change=_check_name_unique, autofocus=True,
            capitalization=ft.TextCapitalization.WORDS, on_submit=_create_new_mw
        )

        # Button for creating new mw. Can also press enter in the textfield
        submit_button = ft.TextButton("Create", on_click=_create_new_mw, disabled=True)

        # Dialog we open onto the page
        dlg = ft.AlertDialog(
            title=ft.Text(f"New Location Name"),
            content=new_item_tf,
            actions=[
                ft.TextButton("Cancel", style=ft.ButtonStyle(color=ft.Colors.ERROR), on_click=lambda e: self.p.close(dlg)),
                submit_button
            ],
        )

        self.p.show_dialog(dlg)    
    

    def _get_menu_options(self) -> list[ft.Control]:
        

        async def _show_info_display(e):
            ''' Shows our information display mini widget '''
            self.information_display.show_mini_widget()
            await self.story.close_menu()

        # New (all dif types of locations), rename color
        return [
             MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", weight=ft.FontWeight.BOLD)]),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    #ft.CupertinoIcons.LOCATION
                    tooltip="New Location", menu_padding=0,
                    items=[
                        ft.PopupMenuItem(
                            text="Blank", icon=ft.Icons.CHECK_BOX_OUTLINE_BLANK,
                            on_click=self.new_location_clicked, data={'icon': 'location_pin'}
                        ),
                        ft.PopupMenuItem(
                            text="Point of Interest", icon=ft.Icons.LOCATION_PIN,
                            on_click=self.new_location_clicked, data={'icon': 'location_pin'}
                        ),
                        ft.PopupMenuItem(
                            text="Mountain", icon=ft.Icons.TERRAIN,
                            on_click=self.new_location_clicked, data={'icon': 'terrain'}
                        ),
                        ft.PopupMenuItem(
                            text="Forest", icon=ft.Icons.FOREST,
                            on_click=self.new_location_clicked, data={'icon': 'forest'}
                        ),
                        ft.PopupMenuItem(
                            text="Ocean", icon=ft.Icons.WATER,
                            on_click=self.new_location_clicked, data={'icon': 'water'}
                        ),
                        ft.PopupMenuItem(
                            text="City", icon=ft.Icons.LOCATION_CITY,
                            on_click=self.new_location_clicked, data={'icon': 'location_city'}
                        ),
                        ft.PopupMenuItem(
                            text="Dungeon", icon=ft.Icons.STAIRS_OUTLINED,
                            on_click=self.new_location_clicked, data={'icon': 'stairs_outlined'}
                        )
                        
                    ]
                ), no_padding=True,
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


    # Called when we need to rebuild out map UI
    def reload_widget(self):       
        ''' Rebuilds/reloads our map UI '''

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        # TODO: 
        # Little Info Display Button in the bottom right that can be dragged around and shows map info display. No header, clicking canvas does not open it
        # Also drawing mode button should be near it
        # Users can choose to create their image or use some default ones, or upload their own
        # Make show_info_button is a checkmark when in drawing mode

        # Clear our map stack controls so we can re-add them
        self.map_stack.controls.clear()
        self.map_stack.controls = [     # Add our background and canvas
            ft.Container(
                expand=True, ignore_interactions=True,
                #image=ft.DecorationImage("map_background.png", fit=ft.ImageFit.FILL)    # Our background image
            ),
            self.canvas, 
        ] 

        # Add our map locations to the stack
        for mw in self.mini_widgets:
            if hasattr(mw, 'map_control') and hasattr(mw, 'map_label'):
                self.map_stack.controls.append(mw.map_control)
                self.canvas.shapes.append(mw.map_label)
                #self.map_stack.controls.append(mw.map_label)

        # Add all our mini widgets to the plotline stack as well
        self.map_stack.controls.append(
            ft.Row([
                ft.Column([mw for mw in self.mini_widgets if mw.data.get('side_location', "") == "left"], expand=1),
                ft.Container(expand=2, ignore_interactions=True),
                ft.Column([mw for mw in self.mini_widgets if mw.data.get('side_location', "") == "right"], expand=1)
            ])
        )

        
                
        # Create our interactive viewer for panning and zooming
        iv = ft.InteractiveViewer(
            content=self.map_stack, expand=True,
            scale_factor=750, boundary_margin=50,
            min_scale=0.5, max_scale=2.0, scale=1.0,
        )
        

        self.body_container.content = iv


        # Not used, but changes how our mini widgets are positioned
        self.header = ft.Container(ignore_interactions=True, height=50)


        self._render_widget()
    



        