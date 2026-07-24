'''
Mini widgets are high complexity components that sit in the widgets content AND can display their info inside the parent widgets sidebar.
If it cannot do both, its not a mini widget
'''


import flet as ft
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
from styles.text_fields import TextField
import uuid
from constants import PLOTLINE_CANVAS_PADDING

class MiniWidget(ft.GestureDetector):

    # Constructor
    def __init__(
        self, 
        widget: Widget, 
        data: dict = {},
        is_new: bool=False  
    ):

        self.widget = widget        
        # Parent constructor
        super().__init__(
            data=data, 
            animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            on_right_pan_end=lambda: None,  # Needs an event or gets angy
        )

        # If we're new, give default values for our data 
        self.is_new: bool = is_new 

        # Give us default data if we're new. Child class will for a file save
        if self.is_new == True:
            self.data = {
                'id': str(uuid.uuid4()),
                'title': data.get('title', ''),         # Title of the mini widget, should match the object title
                'tag': str(),                           # Default mini widget tag, but should be overwritten by child classes
                'alignment': data.get('alignment', (0, 0)),     # Alignment of the mini widget on its parents stack
                'position': data.get('position', (200, 200)),       # Position of the mini widget on its parents stack
                'color': data.get('color', 'primary'),          # Color of the mini widget
                'notes': [],                            # Notes stored at bottom of info sidebar section
            }

        # State trackers
        self.is_dragging: bool = False              # If we are currently dragging our mini widget
        self.shown_in_sidebar: bool = False         # If we are currently shown on the sidebar and should stay highlighted
        
    # Called every time the mouse moves over our rail
    async def set_mouse_coords(self, e: ft.PointerEvent):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.widget.story.mouse_x = e.global_position.x 
        self.widget.story.mouse_y = e.global_position.y
            
    # Called by delete buttons to delete ourselves from data. Children deal with the UI
    async def handle_delete(self, e=None):
        await self.widget.story.close_menu()
        self.widget.data['mini_widgets_data'].pop(self.data.get('id', ''))
        self.widget.update_data(**{'mini_widgets_data': self.widget.data.get('mini_widgets_data', {})})

    # Updates our data then makes sure the widget data for us matches
    def update_data(self, **kwargs):
        
        # Allow Updates our data
        def _merge_data(target: dict, updates: dict):
            for key, value in updates.items():
                current_value = target.get(key)
                if isinstance(current_value, dict) and isinstance(value, dict):
                    _merge_data(current_value, value)
                else:
                    target[key] = value

        # Merge our data then have the widget match
        _merge_data(self.data, kwargs)  
        self.widget.update_data(**{'mini_widgets_data': {self.data.get('id', ''): self.data}})

    # Saves updated position to our data
    async def save_position(self, e: ft.DragEndEvent):
        # Update our data to match our new position
        self.is_dragging = False
        self.position = (self.left, self.top)
        self.update_data(**{'position': self.position})
        self.widget.set_mouse_coords(e)     # Reset the menu position


    async def _new_note_clicked(self, e=None):
        ''' Called when the new field button is clicked '''



    def _build_notes_column(self) -> ft.Column:
        ''' Builds our column of custom fields for this mini widget '''
        

    def get_menu_options(self) -> list[ft.Control]:

        # Color, rename, delete
        return []
        

        
    
    
    # Called when hovering over stacked control to give us a highlighted shadow
    async def highlight(self, e=None):
        ''' Shows our slider and hides our plotline_marker. Makes sure all other sliders are hidden '''
        self.shadow = ft.BoxShadow(2, 2, self.data.get('color', ft.Colors.PRIMARY), blur_style=ft.BlurStyle.OUTER)
        self.update()

    # Called when we stop hovering over our marker
    async def stop_highlight(self, e=None):
        if self.shown_in_sidebar:
            return
        self.shadow = None
        self.update()  

    

    # Shows our mini widget in the sidebar of our widgets content
    async def show_mini_widget(self, e=None):
        ''' Shows our mini widget '''
        self.shown_in_sidebar = True

        # Update header stuff
        self.widget.sidebar_title.value = self.data.get('title', '')   # Update title to match us

        # If we have a settings ctrl, add it to the sidebar header, otherwise remove it
        if hasattr(self, 'create_sidebar_header_setting_ctrl'):
            self.widget.sidebar_header.controls[1] = self.create_sidebar_header_setting_ctrl()
        else:
            self.widget.sidebar_header.controls.pop(1)

        # Build our sidebar body content
        self.widget.sidebar_body.controls = self.create_sidebar_ctrls() 

        # Check state 
        if hasattr(self.widget, 'showing_info'):
            if self.widget.showing_info == True:    # If widget is showing info, remove its description control at the bottom
                self.widget.sidebar.content.controls.pop(-1)
            self.widget.showing_info = False
        
        
        # Applies the update
        if not await self.widget.show_sidebar():
            self.widget.sidebar.update()

        
    # Hides our mini widget in the sidebar of our widgets content
    async def hide_mini_widget(self, e: ft.Event=None):
        ''' Hides our mini widget '''
        self.shown_in_sidebar = False
        await self.widget.hide_sidebar()

    # Child classes override this
    def create_sidebar_ctrls(self) -> list:
        ''' Creates the controls for the sidebar for this mini widget '''
        return [] 
    
    # Set the content of our mini widget
    def build(self):
        self.description_tf = ft.TextField(
            value=self.data.get('description', ''), label="Description",
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_color=ft.Colors.TRANSPARENT,
            margin=ft.Margin.only(top=4),
            focused_border_color=ft.Colors.PRIMARY,
            multiline=True, dense=True, expand=True, 
            on_blur=lambda e: self.update_data(**{'description': e.control.value}),
            capitalization=ft.TextCapitalization.SENTENCES,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD, italic=True, size=16, color=ft.Colors.PRIMARY) 
        )   

    
        
# TODO: Have notes label, button, input_tf all standardized