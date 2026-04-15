'''
Very simple mini widget that shows markers on the timeline, which are simplified plot points.
Just displayed as a dashed vertical line on the plotline with a label, and a description
'''



import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
from styles.text_styles import text_style
import flet.canvas as cv
from styles.text_field import TextField

# Plotpoint mini widget object that appear on plotlines and arcs
class Marker(MiniWidget):

    # Constructor. Requires title, widget widget, page reference, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        widget: Widget, 
        page: ft.Page, 
        key: str,                           # Key is markers for plotlines
        x_alignment: float = 0.0,           # Float from -1 to 1 representing where we are on the plotline. -1 is left, 0 is center, 1 is right
        left: int = None,                   # Absolute left position on plotline. If not provided, will be calculated from x_alignment
        data: dict = None       
    ):
        
        
        
        # Parent constructor
        super().__init__(
            title=title,        
            widget=widget,        
            page=page,          
            key=key,  
            data=data,    
        ) 

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                'tag': "marker",            # Tag to identify what type of object this is
                'title': str,
                'x_alignment': x_alignment,           # Float from -1 to 1 representing where we are on the plotline. Used for resizing calcs
                'left': left,                       # Integer Absolute left position on plotline
                'color': "note",           # Color of the plot point on the plotline
                'description': str,
            },
        )
        

        # Set our x alignment to position on our plotline. -1 is left, 0 is center, 1 is right. Default 0

        # UI elements
        self.plotline_control: ft.Container = None    # Circle container to show our plot point on the plotline

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our plot point
        

        # Build our slider for moving our plot point
        self.reload_plotline_control()
        self.reload_mini_widget()

    def delete_dict(self, e=None):

        self.widget.plot_points.pop(self.data.get('title', None), None)
        super().delete_dict()

    async def _drag_start(self, e=None):
        ''' Called when we start dragging our plot point. Sets our state to dragging and changes our mouse cursor '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.RESIZE_LEFT_RIGHT
        self.is_dragging = True
        self.plotline_control.update()
        

    # Called when actively dragging our slider thumb to change our x position
    async def move_marker(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        if e is None:
            delta_x = 0
        else:
            delta_x = e.local_delta.x

        if not isinstance(delta_x, (int, float)):
            delta_x = 0
        
        # Calculate our new absolute positioning based on our delta x from dragging
        new_left = self.plotline_control.left + delta_x

        # Clamp sides and use timeline padding
        if new_left < 10:        # Padding on left because canvas draws in middle (5px)
            new_left = 10
        elif new_left > self.widget.plotline_width - 20:  # No padding needed on right
            new_left = self.widget.plotline_width - 20
        
        # Set our new left position within our stack
        self.plotline_control.left = new_left

        self.data['left'] = new_left

        self.plotline_control.update()

    # Called when we finish dragging our plotline_marker to save our position
    async def _drag_end(self, e=None):
        ''' Updates our alignment and side location, and applies the updadte to the canvas for our label '''

        self.plotline_control.content.mouse_cursor = ft.MouseCursor.CLICK
        self.is_dragging = False

        await self.highlight()

        x_alignment = (self.data.get('left', 0) / (self.widget.plotline_width - 10)) * 2.0 - 1.0

        self.data['x_alignment'] = x_alignment
 
        await self.save_dict()


        if self.widget.information_display.visible:
            self.widget.information_display.reload_mini_widget()

        await self.widget.rebuild_plotline_canvas(True)
        
        
    # Called when hovering over our plot point to show the slider
    async def highlight(self, e=None):
        ''' Shows our slider and hides our plotline_marker. Makes sure all other sliders are hidden '''
        if self.is_dragging:
            return

        self.plotline_control.content.content.opacity = .7 if self.plotline_control.content.content.opacity != .7 else 1
        self.plotline_control.update()

        # Apply it to the UI
        #self.p.update()

            
    # Called when toggling whether this plot point is shown on the plotline in the plotline filters
    def toggle_plotline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the plotline '''

        # Change the control visibility, data, and save it
        self.plotline_control.visible = value
        self.data['is_shown_on_widget'] = value
        self.p.run_task(self.save_dict)
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.hide_mini_widget()
        
        for mw in self.widget.mini_widgets:
            if hasattr(mw, 'plotline_control'):
                mw.reload_plotline_control(no_update=True)
        self.widget.reload_widget()
          

    # Called from reload_mini_widget
    def reload_plotline_control(self, no_update=False):
        """ Rebuilds our plotline control that holds our plot point and slider """

        # Our container that is our plot point on the plotline, and contains our gesture detector for hovering and right clicking
        self.plotline_control = ft.Container(
            margin=ft.Margin(16, 0, 16, 0), expand=True,
            width=10, alignment=ft.Alignment.CENTER, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            #bgcolor="red",
            #border=ft.Border.all(2, self.data.get('color', None), ft.BorderSide(style=ft.BorderStyle.SOLID)),
            left=self.data.get('left', 0), 
            animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            content=ft.GestureDetector(
                width=10, mouse_cursor=ft.MouseCursor.CLICK,
                on_enter=self.highlight, on_exit=self.highlight,
                on_tap_down=self._drag_start,
                on_pan_start=self._drag_start, on_pan_end=self._drag_end,
                on_pan_update=self.move_marker, drag_interval=20, 
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                on_tap=self.show_mini_widget,
                content=cv.Canvas(
                    width=10, opacity=.7, resize_interval=20,    
                    content=ft.Container(ignore_interactions=True, expand=True),
                    shapes=[],    # Set shapes empty so timeline knows to set its dashed line
                ),
            ),
        )

        if no_update:
            return

        try:
            self.plotline_control.update()
        except Exception as _:
            pass

        


    # Called when reloading changes to our plot point and in constructor
    def reload_mini_widget(self):
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''


        title_control = ft.Row([
            
            ft.GestureDetector(
                ft.Text(f"\t{self.data['title']}", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, 
                color=self.data.get('color', None), expand=True),
                on_double_tap=self._rename_clicked,
                on_secondary_tap=lambda _: self.widget.story.open_menu(self._get_menu_options()),
                mouse_cursor="click", hover_interval=500, expand=True
            ),
                
            
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.OUTLINE,
                tooltip=f"Close {self.title}",
                on_click=self.hide_mini_widget,
                mouse_cursor="click"
            ),
        ], spacing=0)




        description_tf = TextField(
            value=self.data.get('description', ''), multiline=True, expand=True, 
            on_blur=lambda e: self.change_data(**{'description': e.control.value}), 
            label="Description", dense=True, capitalization=ft.TextCapitalization.SENTENCES,
        )

        notes_label = ft.Row([
            ft.Container(width=6),
            ft.Text("Notes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
            ft.IconButton(
                ft.Icons.NEW_LABEL_OUTLINED, self.data.get('color', "primary"), tooltip="Add Note",
                on_click=self._new_note_clicked,
                mouse_cursor="click"
            )
        ], spacing=0)

        notes_column = self._build_notes_column()
        
        content = ft.Column(
            expand=True, tight=True, scroll="auto", alignment=ft.MainAxisAlignment.START, 
            controls=[
                ft.Container(height=1),  # Little padding
                description_tf,
                ft.Divider(2, 2),

                notes_label,
                ft.Container(notes_column, margin=ft.Margin.symmetric(horizontal=20)),
            ]
        )

        column = ft.Column([
            title_control,
            ft.Divider(),
            content
        ], expand=True, scroll="none", tight=True, alignment=ft.MainAxisAlignment.START, spacing=0)
        
        self.content = column
            

        try:
            self.update()
        except Exception as _:
            pass
