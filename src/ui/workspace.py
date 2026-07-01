'''
UI styling for the main workspace area of appliction that holds our widgets (tabs)
Returns our container with our formatting areas inside the workspace area.
The stories 'mast_stack' holds our 'master_row', which contains our five pins: top, left, main, right, and bottom.
Overtop that, we append our drag targets when we start dragging a widget (tab). Thats why its a stack
'''

import flet as ft
from models.app import app
from models.views.story import Story
import json
from styles.colors import dark_gradient
from styles.snack_bar import SnackBar
from models.isolated_controls.row import IsolatedRow
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.tab_bar_view import IsolatedTabBarView
import asyncio

# Our workspace object that is stored in our story object
class Workspace(ft.Container):
    # Constructor
    def __init__(self, page: ft.Page, story: Story):

        # Set our container properties for the workspace
        super().__init__(
            expand=True,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        )

        self.p = page
        self.story = story

        self.is_resizing = False # State tracking if we're resizing a canvas

        

        # Main pin is not rendered directly since it changes based on active tab when more than one widget is present
        self.main_pin = []      # List to hold all our widgets in the main pin that we manipulate easier
        self.main_pin_tabs: ft.Tabs = None
        self.main_pin_column = ft.Column(expand=True)

        self.reload_workspace()   # Load our workspace content for the first time without updating the UI, since we're still in the constructor


    def arrange_widgets(self):
        self.main_pin.clear()
        sorted_widgets = sorted(self.story.widgets.values(), key=lambda w: w.data.get('index', 0))
        visible_widget_index = 0
        for w in sorted_widgets:
            if w.data.get('visible', False):

                # Rebuild and add the widget to the main pin
                widget = self.story.rebuild_widget(w)  
                #widget = w  
                self.main_pin.append(widget)

                # If this widget index is not 999, (meaning we were not just added to workspace), don't set that index 
                if widget.data['index'] != 999:
                    widget.data['index'] = visible_widget_index

                visible_widget_index += 1
    

    def reload_workspace(self):

        # TODO: Make the widget itself as the content part, we add its tab portion here.
        # Will reduce control count a lot

        self.arrange_widgets()

        # If we're empty, skip all logic
        if len(self.main_pin) <= 0:
            self.content = None
            try:
                self.update()
            except Exception:
                pass
            return

        # Sets our new index when switching tabs
        async def tab_change(e: ft.Event):
            from models.widgets.canvas import Canvas

            # Save new selected index
            self.story.update_data(**{'main_pin_selected_idx': e.data})

            for idx, w in enumerate(self.main_pin):
                if idx == e.data:
                    tabs.content.controls[0].indicator_color = w.data.get('color', ft.Colors.ON_SURFACE_VARIANT)
                    tabs.content.controls[0].update()  

                # Make it so canvases don't redraw unneccesarily when switching tabs
                if isinstance(w, Canvas):
                    w.skip_first_resize = True

        # Tabs that hold our workspace
        tabs = ft.Tabs(
            expand=True, 
            length=len(self.main_pin),
            #selected_index=int(self.story.data.get('main_pin_selected_idx', 0)),    # Set the selected index from our data
            on_change=tab_change,
            animation_duration=100,
            content=ft.Column([
                ft.TabBar(
                    tabs=[widget.tab for widget in self.main_pin], scrollable=True, indicator_color=ft.Colors.ON_SURFACE_VARIANT, divider_height=2
                ), 
                ft.TabBarView(
                    #controls=[widget.master_stack for widget in self.main_pin],
                    controls=[widget for widget in self.main_pin],
                    expand=True
                )
            ], expand=True, spacing=0),
        )   

        

        # Check our last widget. If its index is 999, it was just added and needs its data updated
        if self.main_pin[-1].data.get('index', -1) == 999:   
            tabs.selected_index = len(self.main_pin) - 1    # Set the selected index
            self.story.data['main_pin_selected_idx'] = len(self.main_pin) - 1 
            self.story.update_data(**{'main_pin_selected_idx': len(self.main_pin) - 1})  # Update our story data to reflect the new selected index
            tabs.content.controls[0].indicator_color = self.main_pin[-1].data.get('color', ft.Colors.ON_SURFACE_VARIANT)
            

        else:
            for widget in self.main_pin:
                if widget.data.get('index', -1) == self.story.data.get('main_pin_selected_idx', 0):
                    tabs.content.controls[0].indicator_color = widget.data.get('color', ft.Colors.ON_SURFACE_VARIANT)
                    tabs.selected_index = widget.data.get('index', 0)
                    break

        # If our selected index is out of range (The active tab was last and just hidden), make the last tab active
        if int(self.story.data.get('main_pin_selected_idx', 0)) >= len(self.main_pin):
            tabs.selected_index = len(self.main_pin) - 1
            self.story.update_data(**{'main_pin_selected_idx': len(self.main_pin) - 1})  # Update our story data to reflect the new selected index


        # Set our tabs as the content
        self.content = tabs

        try:
            self.update()
        except Exception:
            pass