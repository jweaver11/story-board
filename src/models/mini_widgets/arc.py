import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from utils.verify_data import verify_data
import flet.canvas as cv
import math
from models.app import app


class Arc(MiniWidget):

    # Constructor.
    def __init__(
        self, 
        title: str, 
        owner: Widget, 
        page: ft.Page, 
        key: str, 
        x_alignment: float = None,          # Position of plot point on plotline if we pass one in (between -1 and 1)
        data: dict = None
    ):
        
        
        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,                    # Top most plotline this arc belongs too
            page=page,          
            key=key,  
            data=data,         
        ) 

        # Newly created arcs
        if x_alignment is not None:
            x_align_pixel = int((x_alignment + 1) / 2 * owner.plotline_width)
            left = x_align_pixel - 50
            right = x_align_pixel + 50

            if left <= 0:
                left = 0
            
            if right >= owner.plotline_width:
                right = 0

            if x_alignment <= 0:
                side_location = "right"
                
            else:
                side_location = "left"

        else:
            side_location = "right"     # Needs a value but won't be passed in since it should have one already
            left = 0
            right = 0
    

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {   
                # Mini widget data
                'tag': "arc",                               # Tag to identify what type of object this is
                'color': "secondary",                       # Color of the arc in the plotline
                
                # Rail display data
                'dropdown_is_expanded': True,               # If the arc dropdown is expanded on the rail
                
                # For rendering on plotline
                'side_location': side_location, 
                'on_top': True,                             # If the mini widget should appear on top of the plotline. If false, appears below      
                'rail_dropdown_is_expanded': True,          # If the rail dropdown is expanded  
                'is_shown_on_widget': True,                 # If this arcs plotline control is shown on the plotline widget

                # Absolute Left and Right positions of the arc on the plotline
                'left': left,
                'right': right,       # Default width
                
                # Arc Data
                'summary': str,
                'start_date': str,                          # Start and end date of the branch, for plotline view
                'end_date': str, 
                'involved_characters': list,
                'related_locations': list,
                'related_items': list,
                'events': list,                             # List of events that occur during this arc
            },
        )


        # UI elements
        self.plotline_control: ft.Container = None      # Arc shaped contorl on the plotline

        # Set drag handles on left and right of arc connections to the plotline
        self.left_drag_handle = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT, content=ft.Icon(ft.Icons.DRAG_INDICATOR), 
            on_tap=self.show_mini_widget,    # Focus this mini widget when clicked
            on_secondary_tap=lambda e: print("Right clicked arc"), 
            on_enter=self._highlight,      # Highlight container
            visible=False, on_pan_update=self.change_x_positions, on_pan_start=self.start_dragging, on_pan_end=self.finished_dragging
        )
        self.right_drag_handle = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT, content=ft.Icon(ft.Icons.DRAG_INDICATOR), 
            on_tap=self.show_mini_widget,    # Focus this mini widget when clicked
            on_secondary_tap=lambda e: print("Right clicked arc"), 
            on_enter=self._highlight,      # Highlight container
            visible=False, on_pan_update=self.change_x_positions, on_pan_start=self.start_dragging, on_pan_end=self.finished_dragging
        )    
        
        
        # State variables
        self.is_dragging: bool = False              # If we are currently dragging our arc slider
        self.hidden = False                         # Track if we're in hidden mode for easier dragging

        # Loads our arc
        self.reload_plotline_control()
        self.reload_mini_widget()

    def delete_dict(self, e=None):

        self.owner.arcs.pop(self.data.get('title', None), None)
        super().delete_dict()


    # Called when we hover over our arc on the plotline
    async def _highlight(self, e: ft.HoverEvent):
        ''' Focuses the arc control '''

        # Change its border opacity and update the page
        self.plotline_control.border = ft.border.only( 
            left=ft.BorderSide(2, self.data.get('color', "secondary")),
            right=ft.BorderSide(2, self.data.get('color', "secondary")),
            top=ft.BorderSide(2, self.data.get('color', "secondary")),
        )
        self.plotline_control.content.opacity = 1.0
        self.left_drag_handle.visible = True
        self.right_drag_handle.visible = True

        self.plotline_control.page = self.p
        self.plotline_control.update()

    # Called when we stop hovering over our arc on the plotline
    async def _stop_highlight(self, e: ft.HoverEvent):
        ''' Changes the arc control to unfocused '''

        if self.is_dragging:
            return
        
        # If we are not visible, lower our border and text
        if not self.visible:
            self.plotline_control.border=ft.border.only(        # Make boarder more see through
                left=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                right=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                top=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            )
            self.plotline_control.content.opacity = .7        # Make text less prominent
            self.left_drag_handle.visible = False
            self.right_drag_handle.visible = False
        
            self.plotline_control.page = self.p
            self.plotline_control.update()

    def show_mini_widget_old_quesiton_mark(self, e=None):

        self.opacity = 1
        self.ignore_interactions = False
        self.plotline_control.border = ft.border.only(
            left=ft.BorderSide(2, self.data.get('color', "secondary")),
            right=ft.BorderSide(2, self.data.get('color', "secondary")),
            top=ft.BorderSide(2, self.data.get('color', "secondary")),
        )

        for arc in self.owner.arcs.values():
            if arc != self and arc.data.get('is_pinned', False) == False:
                arc.hide_mini_widget()

        if not self.hidden:
            super().show_mini_widget()
        else:
            self.data['visible'] = True
            self.visible = True
            self.save_dict()

            for mw in self.owner.mini_widgets:
                if mw != self and mw.data.get('is_pinned', False) == False:
                    mw.hide_mini_widget()   

            self.reload_mini_widget(no_update=True)
            self.owner.reload_widget()
    
    def hide_mini_widget(self, e=None, update: bool=False):
        ''' Hides this arc '''

        

        # Set the parts we need to hide in addition to the mini widget info display
        self.opacity = 0
        self.ignore_interactions = True

        self.plotline_control.border = ft.border.only(
            left=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            right=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            top=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
        )

        self.left_drag_handle.visible = False
        self.right_drag_handle.visible = False
        
        return super().hide_mini_widget(update=update)
    

    # Called at the start of dragging our point on the slider
    async def start_dragging(self, e):
        ''' Called when we start dragging our slider thumb '''

        self.is_dragging = True

        # Hide all other info displays while dragging
        for mw in self.owner.mini_widgets:
            mw.visible = False
            if isinstance(mw, Arc) and mw != self:
                mw.plotline_control.ignore_interactions = True

        self.p.update()


    # Called at the end of dragging our point on the slider to update it
    def change_x_positions(self, e: ft.DragUpdateEvent):
        ''' Changes our x position on the slider, and saves it to our data dictionary, but not to our file yet '''

        # Check to make sure we are wide enough (100px)
        width = self.owner.plotline_width - self.data.get('left', 0) - self.data.get('right', 0)
        
        # If we're dragging the left handle, update left position
        if e.control == self.left_drag_handle:
            new_left = self.data.get('left', 0) + e.delta_x

            # Clamp edges
            if new_left < 10:
                new_left = 10
            if new_left > self.owner.plotline_width - 10:     # Make sure we don't drag past the plotline
                new_left = self.owner.plotline_width - 10

            # Width check that we're not too small
            if width >= 100:
                self.data['left'] = new_left
                self.plotline_control.left = new_left

            elif width < 100 and e.delta_x < 0:   # If we're trying to make it smaller, allow it, but not if we're trying to make it bigger
                self.data['left'] = new_left
                self.plotline_control.left = new_left

        # If we're dragging the right handle, update the right position
        else:
            new_right = self.data.get('right', 0) - e.delta_x

            # Clamp edges
            if new_right < 10:     # Make sure we don't drag past the plotline
                new_right = 10
            if new_right > self.owner.plotline_width:
                new_right = self.owner.plotline_width

            # Width check that we're not too small
            if width >= 100:
                self.data['right'] = new_right
                self.plotline_control.right = new_right

            elif width < 100 and e.delta_x > 0:   # If we're trying to make it smaller, allow it, but not if we're trying to make it bigger
                self.data['right'] = new_right
                self.plotline_control.right = new_right

        # Update the height of the arc based on its width
        ratio = (self.data.get('left', 0) + self.data.get('right', 0)) / max(self.owner.plotline_width, 1)
        ratio = 1.0 - ratio
        new_height = ((self.owner.plotline_height - 50) // 2) * (ratio) + 20

        self.plotline_control.height = int(new_height)

        # Apply the updates
        self.plotline_control.page = self.p 
        self.plotline_control.update()


    # Called when we finish dragging our slider thumb to save our new position
    def finished_dragging(self, e):
        ''' Saves our new x positions to the file and updates alignment. Then applies the UI changes '''

        # Update our state
        self.is_dragging = False                # No longer dragging

        # TODO: Update our x_alignment as well
        #self.data['x_alignment'] = ((self.data.get('left', 0) + self.data.get('right', 0)) / 2) / max(self.owner.plotline_width, 1) * 2 - 1    


        if self.data.get('x_alignment', 0) <= 0:
            self.data['side_location'] = "right"
        else:
            self.data['side_location'] = "left"

        # Make all other plot points visible again
        for pp in self.owner.plot_points.values():
            if pp.data.get('is_shown_on_widget', True):
                pp.plotline_control.visible = True
            
        # Save our new positions to file
        self.save_dict()

        # Make other arcs work again
        for mw in self.owner.mini_widgets:
            if mw.data.get('visible', True):
                mw.visible = True
            if isinstance(mw, Arc):
                mw.plotline_control.ignore_interactions = False

        # Apply changes and make sure update plotline info
        if self.owner.information_display.visible:
            self.owner.information_display.reload_mini_widget(no_update=True)
        self.owner.reload_widget()

    # Called when toggling whether this plot point is shown on the plotline in the plotline filters
    def toggle_plotline_control(self, value: bool):
        ''' Toggles whether this plot point is shown on the plotline '''

        # Change the control visibility, data, and save it
        self.plotline_control.visible = value
        self.data['is_shown_on_widget'] = value
        self.save_dict()
        
        # If we're hiding it, also hide our mini widget if it's open
        if value == False:
            self.hide_mini_widget(update=True)
        # Otherwise, just update the page
        else:
            self.p.update()      
        

    # Called from reload mini widget to update our plotline control
    def reload_plotline_control(self):
        ''' Reloads our arc drawing on the plotline based on current/updated data, including page size '''


        self.plotline_control = ft.Container(
            left=self.data.get('left', 0), right=self.data.get('right', None),
            alignment=ft.alignment.top_center, height=0,
            margin=ft.Margin(16, 0, 16, 0), animate_position=ft.Animation(200, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.only(          # Give use borderes on top left and right
                left=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                right=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
                top=ft.BorderSide(2, ft.Colors.with_opacity(.7, self.data.get('color', "secondary"))),
            ),
            padding=ft.padding.only(top=10),
            border_radius=ft.border_radius.only(top_left=1000, top_right=1000, bottom_left=0, bottom_right=0),      # Make it uber curved to look like an arc
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                hover_interval=100, expand=True,
                on_tap=self.show_mini_widget,    # Focus this mini widget when clicked
                on_secondary_tap=lambda e: print("Right clicked arc"), 
                on_enter=self._highlight,      # Highlight container
                on_exit=self._stop_highlight,        # Stop highlight
                #on_hover=self.on_start_hover,
                content=ft.Column([
                    ft.Row([
                        self.left_drag_handle,
                        ft.Text(self.title, theme_style=ft.TextThemeStyle.LABEL_LARGE, overflow=ft.TextOverflow.ELLIPSIS),
                        self.right_drag_handle
                    ], expand=True, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.START, spacing=0),
                ], expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            )
        )

        #print(f"Plotline control left and right for {self.title}: ", self.data.get('left', 0), self.data.get('right', 100))
        
        

    # Called to reload our mini widget content
    def reload_mini_widget(self, no_update: bool=False):

        async def _toggle_pin(e):
            ''' Pins or unpins our information display '''
            is_pinned = self.data.get('is_pinned', False)
            self.data['is_pinned'] = not is_pinned
            self.save_dict()
            self.reload_mini_widget()
            self.owner.reload_widget()

        # Reload our plotline control and all associated components 
        #self.reload_plotline_control()

        # Add hide mode so we can drag without Info Display taking up the screen
        def _hide_mode(e):
            self.opacity = 0 if self.opacity == 1 else 1
            self.ignore_interactions = True if self.ignore_interactions == False else False
            self.hidden = True
            self.p.update()


        self.title_control = ft.Row([
            ft.Icon(ft.Icons.CIRCLE_OUTLINED, self.owner.data.get('color', None)),
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD),
            ft.IconButton(
                ft.Icons.PUSH_PIN_OUTLINED if not self.data.get('is_pinned', False) else ft.Icons.PUSH_PIN_ROUNDED,
                self.owner.data.get('color', None),
                tooltip="Pin Information Display" if not self.data.get('is_pinned', False) else "Unpin Information Display",
                on_click=_toggle_pin
            ),
            ft.Container(expand=True),
            ft.IconButton(
                ft.Icons.MINIMIZE_OUTLINED, ft.Colors.ON_SURFACE_VARIANT,
                tooltip="Hide", on_click=_hide_mode
            ),
            ft.IconButton(
                ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT,
                tooltip=f"Close {self.title}", on_click=lambda e: self.hide_mini_widget(update=True),
            ),
        ], spacing=0)

        
        content = ft.Column([
            self.title_control,
            ft.Divider(height=2, thickness=2),
            ft.Container(height=10)  # Spacing 
        ], expand=True, tight=True, spacing=0)


        # Format our final layout so the scrollbar doesn't sit overtop the content
        row = ft.Row(expand=True, controls=[content, ft.Container(width=8)], spacing=0)
    
        column = ft.Column([
            row
        ], expand=True, scroll="auto", tight=True)
        
        self.content = column
    

        if no_update:
            return
        else:
            self.p.update()


