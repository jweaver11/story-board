import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import math
from styles.text_styles import text_style
import flet.canvas as cv

# Plotpoint mini widget object that appear on timelines and arcs
class PlotPoint(MiniWidget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(
        self, 
        title: str, 
        owner: Widget, 
        father, 
        page: ft.Page, 
        key: str,                           # Key is plot_points for timelines
        x_alignment: float = None,          # Position of plot point on timeline if we pass one in (between -1 and 1)
        data: dict = None       
    ):
        
        if x_alignment is not None:
            side_location = 'right' if x_alignment <= 0 else 'left'
        else:
            side_location = None

        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,        
            father=father,      # In this case, father is always a timeline or another arc
            page=page,          
            key=key,  
            side_location=side_location,
            data=data,    
        ) 

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                'tag': "plot_point",            # Tag to identify what type of object this is
                'description': str,
                'events': list,                 # Numbered list of events that occur at this plot point
                'x_alignment': x_alignment if x_alignment is not None else float,           # Float between -1 and 1 on x axis of timeline. 0 is center
                'is_major': bool,               # If this plot point is a major event
                'date': str,                    # Date of the plot point
                'time': str,                    # Time of the plot point
                'color': "secondary",           # Color of the plot point on the timeline
                'involved_characters': list,
                'related_locations': list,
                'related_items': list,
            },
        )

        # Set our x alignment to position on our timeline. -1 is left, 0 is center, 1 is right. Default 0
        self.x_alignment = ft.Alignment(self.data.get('x_alignment', 0), 0)

        # UI elements
        self.timeline_point: ft.Container = None    # Circle container to show our plot point on the timeline
        self.timeline_label: ft.Container = None  # Text label below our plot point on the timeline
        self.slider: ft.Column = None               # Slider to drag our plot point along the timeline
        self.timeline_control: ft.Stack = None      # Stack that holds our timeline point and slider

        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our plot point

        # Build our slider for moving our plot point
        self.reload_mini_widget()

    def delete_dict(self, e=None):

        self.owner.plot_points.pop(self.data.get('title', None), None)
        super().delete_dict()

    # Called when actively dragging our slider thumb to change our x position
    async def change_x_position(self, e):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        # Grab our new position as a float of whatever number division we're on (-100 -> 100)
        new_position = float(e.control.value)
        np = new_position / 100         # Convert that float between -1 -> 1 for our alignment to work

        # Save the new position to data, but don't needlessly write to file until we stop dragging
        self.data['x_alignment'] = np
        self.is_dragging = True     # Update our dragging state. We do it here to see if we actually moved
        
    # Called when hovering over our plot point to show the slider
    async def show_slider(self, e=None):
        ''' Shows our slider and hides our timeline_point. Makes sure all other sliders are hidden '''

        # Check all other plot points
        for pp in self.owner.plot_points.values():

            # If they are dragging, we don't wanna also start dragging ours, so return out
            if pp.is_dragging and pp != self:
                return
            
            # Also check if they have a slider visible. This matter for very close together plot points. Make sure only one is ready to drag at a time
            elif pp.slider.visible and pp != self:
                return
            
        
        # If we didn't return out, show our slider and hide our timeline point
        self.slider.visible = True
        self.timeline_point.visible = False
        
        # Apply it to the UI
        self.p.update()

    # Called when we start dragging our slider thumb
    async def start_dragging(self, e=None):
        ''' Hides the labels of all the other plot points when we are dragging ours '''

        for plot_point in self.owner.plot_points.values():
            if plot_point != self:
                plot_point.timeline_label.visible = False

        self.timeline_point.visible = False
        self.timeline_label.visible = False

        self.p.update()


    # Called when we stop dragging our slider thumb, or when we drag too high or low from slider
    async def hide_slider(self, e=None):
        ''' Hides our slider and puts our dot back on the timeline. Saves our new position to the file '''

        # If we clicked the slider thumb but didnt move, make our mini widget visible
        if not self.is_dragging:
            self.toggle_visibility(value=True)
            return
    
        # Hide slider
        self.slider.visible = False
        self.timeline_point.visible = True      # Set our point to visible again
        self.is_dragging = False                # No longer dragging

        # Show all other plot point labels again
        for plot_point in self.owner.plot_points.values():
            plot_point.timeline_label.visible = True

        # Update our alignment based on our correct data. This is updated when dragging, so no need to set it here
        self.x_alignment = ft.Alignment(self.data.get('x_alignment', 0), 0)

        if self.data.get('x_alignment', 0) <= 0:
            self.data['side_location'] = 'right'
        else:
            self.data['side_location'] = 'left'

        # Save new x_alignment to file
        self.save_dict()
        
        # Must reload our plot point to apply the change to ourself, then reload the parent widget to apply the change to the page
        self.reload_mini_widget()
        self.owner.reload_widget()

    # Called to determine if we want to hide our slider
    def may_hide_slider(self, e=None):
        ''' Checks our dragging state. If we are dragging, don't hide the slider '''

        # Check if we're dragging
        if self.is_dragging:
            return
        
        # If we're not dragging, hide the slider
        else:
    
            # Hide slider
            self.slider.visible = False
            self.timeline_point.visible = True      # Set our point to visible again
            self.is_dragging = False

            # Since no data changed, just update the page to apply changes
            self.p.update()
            
    # Called when toggling whether this plot point is shown on the timeline in the timeline filters
    def toggle_timeline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the timeline '''

        # Change the control visibility, data, and save it
        self.timeline_control.visible = value
        self.data['is_shown_on_widget'] = value
        self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.toggle_visibility(value=value)
        # Otherwise, just update the page
        else:
            self.p.update()
          

    # Called whenever we need to rebuild our slider, such as on construction or when our x position changes
    def reload_slider(self):

        # Give us a ratio for integers for our left and right expand values to catch hover off of our plot pont
        ratio = (self.data.get('x_alignment', 0) + 1) / 2     # Convert -1 -> 1 to 0 -> 1
    
        # Set the left and right ratio
        left_ratio = int(ratio * 1000)
        right_ratio = 1000 - left_ratio

        # state used during dragging
        self.slider = ft.Column(
            spacing=0,
            visible=False,                                      # Start hidden until we hover over plot point
            controls=[
                #ft.GestureDetector(on_enter=self.hide_slider,  expand=True),    # Invisible container to hide slider when going too far up
                ft.Container(ignore_interactions=True, expand=True),    # Invisible container to hide slider when going too far up
                ft.Stack(
                    alignment=ft.Alignment(0,0),
                    controls=[
                    ft.GestureDetector(                                             # GD so we can detect right clicks on our slider
                        on_secondary_tap=lambda e: print("Right clicked plotpoint"),
                        content=ft.Slider(
                            min=-100, max=100, adaptive=True, divisions=200,  # Min and max values on each end of slider
                            value=self.data.get('x_alignment', 0) * 100,        # Where we start on the slider
                            interaction=ft.SliderInteraction.SLIDE_THUMB,       # Make sure you can only drag the plot point, and not click the slider to move it
                            active_color=ft.Colors.TRANSPARENT,                 # Get rid of the background colors
                            inactive_color=ft.Colors.TRANSPARENT,               # Get rid of the background colors
                            thumb_color=self.data.get('color', "secondary"),    # Color of our actual dot on the slider
                            overlay_color=ft.Colors.with_opacity(.5, self.data.get('color', "secondary")),    # Color of plot point when hovering over it or dragging      
                            on_change=self.change_x_position,      # Update our data with new x position as we drag
                            on_change_end=self.hide_slider,                     # Save the new position, but don't write it yet
                            on_change_start=self.start_dragging,      # Hide other plot point labels when we start dragging                      
                            on_blur=self.hide_slider                            # Hide the slider if we click away from it
                        ),
                    ),
                    # Sitting overtop the slider, is a row with expand based on our proportions
                    ft.Row(
                        spacing=0,
                        expand=True,
                        height=100,
                        controls=[
                            ft.GestureDetector(         # Catch our hovers to the left of the thumb
                                on_hover=self.may_hide_slider,
                                expand=left_ratio,
                                content=ft.Container(expand=True)
                            ),
                            ft.Column(
                                width=50,
                                spacing=0,
                                controls=[
                                    
                                    # Catch above and below the thumb
                                    ft.GestureDetector(expand=True, on_hover=self.may_hide_slider, data="line213", hover_interval=100),

                                    # Reserve safe space for the thumb
                                    ft.Container(       # Safe area
                                        ignore_interactions=True,
                                        shape=ft.BoxShape.CIRCLE,
                                        width=50, height=50, 
                                    ),
                                    ft.GestureDetector(expand=True, on_hover=self.may_hide_slider, data="line221", hover_interval=100),
                                ]
                            ),
                            ft.GestureDetector(         # Catch our hovers to the right of the thumb
                                on_hover=self.may_hide_slider,
                                data="called from line 226 gd",
                                expand=right_ratio,
                                content=ft.Container(expand=True)
                            ),
                        ]
                    )
                ]),
                ft.Container(ignore_interactions=True, expand=True),    # Invisible container to hide slider when going too far down
        ])

    # Called from reload_mini_widget
    def reload_timeline_control(self):
        ''' Rebuilds our timeline control that holds our plot point and slider '''

        # Reload our slider 
        self.reload_slider()

        # Our container that is our plot point on the timeline, and contains our gesture detector for hovering and right clicking
        self.timeline_point = ft.Container(
            margin=ft.Margin(16,0,16,0),        # Magic margin to match the margin on slider so they line up
            expand=False,         
            bgcolor=self.data.get('color', "secondary"),
            width=20, height=20, shape=ft.BoxShape.CIRCLE,           # 
            content=ft.GestureDetector(         # GD so we can detect hovers and right clicks
                expand=True,
                on_enter=self.show_slider,               # Show the slider when we hover over our plot point. This also hides timeline_point
                on_secondary_tap=lambda e: print("Right click on plot point"),  # Pop open our menu options when right clicking
                on_tap_down=self.show_slider,
            )
        )   

        # Build our label each time
        self.timeline_label = ft.Container(
            width=200,
            expand=True, alignment=self.x_alignment,
            border=ft.border.all(1, "red"),
            margin=ft.Margin(16,0,16,0), 
            ignore_interactions=True,
            content=ft.Column(
                expand=False,
                #alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(expand=8, ignore_interactions=True),   # Spacer to push text down
                    ft.Container(expand=3, alignment=ft.Alignment(0,0), content=ft.VerticalDivider(thickness=2, color=self.data.get('color', "secondary"))),  # Line above text
                    ft.Container(
                        expand=1,
                        alignment=ft.alignment.center,  # Center the text in its container
                        content=ft.Text(
                            value=self.title,
                            expand=True, overflow=ft.TextOverflow.VISIBLE,
                            no_wrap=True, text_align=ft.TextAlign.CENTER,
                            #style=text_style
                            #width=200,
                        ), 
                    ),    
                    ft.Container(expand=3, ignore_interactions=True)   
                ]
            )
        )

        self.timeline_label = ft.Container(
            expand=True,    
            border=ft.border.all(1, "red"),
            margin=ft.Margin(16,0,16,0), ignore_interactions=True,
            content=cv.Canvas(
                content=ft.Container(expand=True), #width=200,
                shapes=[

                ]
            )
        )

                

        # Rebuild our stack to hold our timeline point and slider
        self.timeline_control = ft.Stack(
            alignment=self.x_alignment,
            visible=self.data.get('is_shown_on_widget', True),
            expand=True,            # Make sure it fills the whole timeline width
            controls=[
                ft.Container(expand=True, ignore_interactions=True),        # Make sure our stack is always expanded to full size
                self.timeline_point,                                        # Our plot point on the timeline
                self.timeline_label,
                self.slider,                                                # Our slider that appears when we hover over the plot point
            ]
        ) 


    # Called when reloading changes to our plot point and in constructor
    def reload_mini_widget(self):
        ''' Rebuilds any parts of our UI and information that may have changed when we update our data '''

        # Reload our timeline control
        self.reload_timeline_control()

        self.title_control = ft.Row([
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.toggle_visibility(value=False),
            ),
        ])
        

        # Rebuild our information display
        self.content_control = ft.TextField(
            hint_text="plot point",
            on_submit=self.change_x_position,
            expand=True,
        )

        cont = ft.Container(margin=ft.Margin(0,10,0,10), content=self.content_control, expand=True)

        # Format our mini widget content
        self.content = ft.Column(
            spacing=0,
            controls=[
                self.title_control,
                ft.Divider(height=2, thickness=2),
                cont,
                ft.TextButton(
                    "Delete ME", 
                    on_click=lambda e: self.delete_dict()
                ),
            ],
        )
            

        self._render_mini_widget(no_update=True)