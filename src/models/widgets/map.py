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
from models.mini_widgets.map_location import Location
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
                mouse_cursor=ft.MouseCursor.PRECISE if self.data.get('map_data', {}).get('drawing_mode') else None, 
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

        #await self.rebuild_plotline_canvas(update=True)
        self.reload_widget()
        for mw in self.mini_widgets:
            if mw.visible:
                await mw.hide_mini_widget()

        await new_location.show_mini_widget() 

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
            new_item_tf.error = None
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
                ft.TextButton("Cancel", style=ft.ButtonStyle(color=ft.Colors.ERROR), on_click=lambda _: self.p.pop_dialog()),
                submit_button
            ],
        )

        self.p.show_dialog(dlg)    
    
 
    def _get_menu_options(self) -> list[ft.Control]:
        

        # TODO: Add Valley, Plains, Rivers, Storm, Lake, Village
            

        # New (all dif types of locations), rename color
        return [
             MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, self.data.get('color', "primary")), 
                            ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    controls=[
                        
                        ft.MenuItemButton(
                            "Label", leading=ft.Icon(ft.Icons.TEXT_FIELDS_OUTLINED, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, #data="none",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Point of Interest", leading=ft.Icon(ft.Icons.LOCATION_PIN, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data="point_of_interest",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Mountain", leading=ft.Icon(ft.Icons.TERRAIN, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data="mountain",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Forest", leading=ft.Icon(ft.Icons.FOREST, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data="forest",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Water", leading=ft.Icon(ft.Icons.WATER, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data="water",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "City", leading=ft.Icon(ft.Icons.LOCATION_CITY, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data="city",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.MenuItemButton(
                            "Dungeon", leading=ft.Icon(ft.Icons.STAIRS_OUTLINED, self.data.get('color', "primary")),
                            on_click=self.new_location_clicked, data="dungeon",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        
                        
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ), 
                no_padding=True, no_effects=True
            ),
            
            MenuOptionStyle(
                on_click=self.rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.data.get('color', 'primary'),),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                    ), 
                ]),
            ),
            MenuOptionStyle(
                ft.SubmenuButton(
                    ft.Row([
                        ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.data.get('color', "primary")), 
                        ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                        ft.Icon(ft.Icons.ARROW_RIGHT),
                    ], expand=True),
                    self.get_color_options(), 
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    tooltip="Change this widget's color"
                ),
                no_padding=True, no_effects=True
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
        # Users can choose to create their image or use some default ones, or upload their own
        # Make show_info_button is a checkmark when in drawing mode

        # Clear our map stack controls so we can re-add them
        self.map_stack.controls.clear()
        self.map_stack.controls = [     # Add our background and canvas
            ft.Container(
                expand=True, ignore_interactions=True, border=ft.Border.all(2, ft.Colors.OUTLINE_VARIANT),
                #image=ft.DecorationImage("map_background.png", fit=ft.BoxFit.FILL)    # Our background image
            ),
            self.canvas, 
        ] 

        # Add our map locations to the stack
        for mw in self.mini_widgets:
            if hasattr(mw, 'map_control') and hasattr(mw, 'map_label'):
                self.map_stack.controls.append(mw.map_control)
                self.canvas.shapes.append(mw.map_label)
                #self.map_stack.controls.append(mw.map_label)
        
                
        # Create our interactive viewer for panning and zooming
        interactive_viewer = ft.InteractiveViewer(
            content=self.map_stack, 
            expand=3,
            scale_factor=500, boundary_margin=50,
            min_scale=0.5, max_scale=3.0,
        )

        mini_widgets_visible = False
        for mw in self.mini_widgets:
            if mw.visible:
                mini_widgets_visible = True
                break

        async def _show_mini_widget(e):
            e.control.visible = False
            e.control.update()
            await self.information_display.show_mini_widget()

        if not mini_widgets_visible:
            self.body_container.content = ft.Row(
                [
                    interactive_viewer, 
                    ft.IconButton(
                        ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
                        on_click=_show_mini_widget, 
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    )
                ], expand=True, spacing=0
            )
            self._render_widget()
            return      

        


        self.body_container.content = interactive_viewer


        self._render_widget()
    



        