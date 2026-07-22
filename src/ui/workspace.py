'''
UI styling for the main workspace area of appliction that holds our widgets (tabs)
Returns our container with our formatting areas inside the workspace area.
The stories 'mast_stack' holds our 'master_row', which contains our five pins: top, left, main, right, and bottom.
Overtop that, we append our drag targets when we start dragging a widget (tab). Thats why its a stack
'''

import flet as ft
from models.app import app
from models.views.story import Story
from models.widget import Widget
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
    def __init__(self, story: Story):

        # Set our container properties for the workspace
        super().__init__(expand=True)

        self.story: Story = story

        # Our workspace variables
        self.tab_bar: ft.TabBar         # The tab bar that holds our tabs for each widget   
        self.tab_view: ft.TabBarView    # The tab view that holds our widgets in the body of the workspace
        self.tabs: ft.Tabs              # The tabs control that holds the tab bar and tab view together in a column

        # State variables
        self.placeholder_visible: bool = False  # True if we have no widgets in the workspace and are showing a placeholder tab to prevent errors

    # Adds a new widget to the workspace
    async def add_widget_to_workspace(self, widget: Widget):

        # If we have a placeholder tab, remove it since we're adding a real widget
        if self.placeholder_visible:
            # Remove the placeholder tab and view
            self.tab_bar.tabs.pop(0)
            self.tab_view.controls.pop(0)
            self.placeholder_visible = False

        # Rebuild the widget to ensure it has updated page references
        new_widget: Widget = self.story.rebuild_widget(widget)

        # Add a new tab for the widget and add the widget to the tab view
        self.tab_bar.tabs.append(self.create_widget_tab_ctrl(new_widget))
        self.tab_view.controls.append(new_widget)

        # Grab the last tab to be our new selected index
        new_selected_index = len(self.tab_bar.tabs) - 1     

        # Adjust the tabs properties
        self.tabs.length = len(self.tab_bar.tabs)
        self.tabs.selected_index = new_selected_index

        # Force the update
        self.update()
        await asyncio.sleep(0.05)  # Wait a frame to ensure selecting the tab is kept in a seperate frame

        # Update the new widgets data to reflect its new position, and story data to match
        new_widget.update_data(**{'index': new_selected_index})  
        self.story.update_data(**{'workspace_selected_index': new_selected_index}) 

        # Focus the new tab and update the indicator color
        self.tab_bar.indicator_color = new_widget.data.get('color', ft.Colors.PRIMARY)
        await self.tabs.move_to(new_selected_index, animation_duration=100)  # Select the new widget tab
        self.tab_bar.update()

        # TODO: Add length check here

    # Creates a new tab control for the given widget
    def create_widget_tab_ctrl(self, widget: Widget) -> ft.Tab:
        # Set our icon based on what type of widget we have
        match widget.data.get('tag', ''):
            case "document": icon = ft.Icons.DESCRIPTION_OUTLINED
            case "canvas": icon = ft.Icons.BRUSH_OUTLINED
            case "canvas_board": icon = ft.Icons.SPACE_DASHBOARD_OUTLINED
            case "note": icon = ft.Icons.LIBRARY_BOOKS_OUTLINED
            case "character": icon = ft.Icons.PERSON_OUTLINE
            case "character_relationship_map": icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case "plotline": icon = ft.Icons.TIMELINE
            case "map": icon = ft.Icons.MAP_OUTLINED
            case "world": icon = ft.Icons.PUBLIC_OUTLINED
            case "item": icon = ft.Icons.STAR_OUTLINE_ROUNDED
            case "chart": 
                if widget.data.get('chart_type', '') == 'bar':
                    icon = ft.Icons.INSERT_CHART_OUTLINED 
                else:
                    icon = ft.CupertinoIcons.COMPASS
            case "comic_preview": icon = ft.Icons.SLIDESHOW_OUTLINED
            case "plot_chart": icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case _: icon = ft.Icons.ERROR_OUTLINE

        # Set the icon contrl
        tab_icon = ft.Icon(icon, color=widget.data.get('color', ft.Colors.PRIMARY))  

        # Title of the text in the tab
        tab_title = ft.Text(
            widget.data.get('title', ''), weight=ft.FontWeight.BOLD, size=16, 
            color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True
        )

        # Button to remove the widget from the workspace
        hide_widget_button = ft.IconButton(    # Hide widget button on right side of tab
            scale=0.8,
            on_click=widget.hide_widget,    # Calls remove_widget_from_workspace. Just keep it this way for consistency with other widget actions
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Hide",
            mouse_cursor=ft.MouseCursor.CLICK,
        )

        # Gesture Detector for opening menus that holds our tab icon, title, and hide button
        tab_gd = ft.GestureDetector(
            ft.Row([tab_icon, tab_title, hide_widget_button]),
            mouse_cursor=ft.MouseCursor.CLICK,
            hover_interval=100,
            on_hover=widget.set_mouse_coords,
            on_secondary_tap=lambda: self.story.open_menu(widget.get_menu_options()),
        )

        # Set the tab itself
        tab = ft.Tab(label=tab_gd) 
        return tab

    # Removes a widget from the workspace
    async def remove_widget_from_workspace(self, widget: Widget):
        # Grab index
        widget_idx = widget.data.get('index', -100)
        if widget_idx < 0 or widget_idx >= len(self.tab_bar.tabs):
            self.page.show_dialog(SnackBar("Error: Widget index out of range when trying to remove from workspace: " + str(widget_idx)))
            return
        
        # Remove from controls and adjust length
        self.tab_bar.tabs.pop(widget_idx)
        self.tab_view.controls.pop(widget_idx)
        self.tabs.length = len(self.tab_bar.tabs)

        # Check selected index is still in range. If not, adjust it
        if self.tabs.selected_index >= len(self.tab_bar.tabs):
            self.tabs.selected_index = len(self.tab_bar.tabs) - 1
            self.story.update_data(**{'workspace_selected_index': self.tabs.selected_index})
            if len(self.tab_bar.tabs) > 0:
                self.tab_bar.indicator_color = self.tab_view.controls[self.tabs.selected_index].data.get('color', ft.Colors.ON_SURFACE_VARIANT)
                self.tab_bar.update()

        # Add the placeholder if we need it
        if len(self.tab_bar.tabs) < 1:
            self.tab_bar.tabs.append(self.create_placeholder_tab_ctrl())
            self.tab_view.controls.append(self.create_placeholder_tab_view())
            self.tabs.length = len(self.tab_bar.tabs)
            self.tabs.selected_index = 0
            self.update()
            return

        # Update the workspace and the tab_indices to reflect shiften positions
        self.update()
        self.update_tab_indices() 

    # Updates the tab indices after a widget is removed from the tab to maintain proper ordering
    def update_tab_indices(self):
        for i, widget in enumerate(self.tab_view.controls):
            widget.update_data(**{'index': i})
        
    # Create a placeholder tab control if there are no widgets in the workspace, since tabs needs a non-empty list
    def create_placeholder_tab_ctrl(self) -> ft.Tab:
        self.placeholder_visible = True
        return ft.Tab(" <- Add Widget")
    
    # Creates a placeholder control for the tab view if there are no widgets in the workspace, since tab view needs a non-empty list
    def create_placeholder_tab_view(self) -> ft.Container:
        return ft.Container(
            ft.Text("Add a widget to the workspace", theme_style=ft.TextThemeStyle.TITLE_LARGE), 
            expand=True, alignment=ft.Alignment.CENTER
        )
    
    # Updates the color of a widget tab in the workspace
    async def update_widget_tab_color(self, idx: int, color: str):
        if idx < 0 or idx >= len(self.tab_bar.tabs):
            self.page.show_dialog(SnackBar("Error: Widget index out of range when trying to update tab color in workspace: " + str(idx)))
            return

        # Update the tab icon color
        tab_gd: ft.GestureDetector = self.tab_bar.tabs[idx].label
        tab_row: ft.Row = tab_gd.content
        tab_icon: ft.Icon = tab_row.controls[0]
        tab_icon.color = color

        # Update the indicator color if this is the selected tab
        if self.tabs.selected_index == idx:
            self.tab_bar.indicator_color = color

        self.tab_bar.update()

    # Updates the title of a widget tab in the workspace
    async def update_widget_tab_title(self, idx: int, title: str):
        if idx < 0 or idx >= len(self.tab_bar.tabs):
            self.page.show_dialog(SnackBar("Error: Widget index out of range when trying to update tab title in workspace: " + str(idx)))
            return

        # Update the tab title text
        tab_gd: ft.GestureDetector = self.tab_bar.tabs[idx].label
        tab_row: ft.Row = tab_gd.content
        tab_title: ft.Text = tab_row.controls[1]
        tab_title.value = title

        self.tab_bar.update()
    
    # Sets our new selected index when we change tabs and updates the tab bar indicator color to match the new selected tab
    async def tab_change(self, e: ft.Event):

        # Save new selected index
        new_selected_index = e.data
        self.story.update_data(**{'workspace_selected_index': new_selected_index})

        # Set the new selected index and indicator color, then update
        self.tabs.selected_index = new_selected_index
        self.tab_bar.indicator_color = self.tab_view.controls[new_selected_index].data.get('color', ft.Colors.ON_SURFACE_VARIANT)
        self.update()

    # Reloads the workspace
    def build(self):

        # Grab only the visible widgets and sort them by their index
        visible_widgets: list = [w for w in self.story.widgets.values() if w.data.get('visible', False)]
        sorted_visible_widgets: list = sorted(visible_widgets, key=lambda w: w.data.get('index', 0))

        # Current selected index
        selected_idx = int(self.story.data.get('workspace_selected_index', 0))  
        if selected_idx >= len(sorted_visible_widgets):
            selected_idx = len(sorted_visible_widgets) - 1

        # Handle the selected index for errors, and grab the right indicator color for the tab ba
        if selected_idx <= 0:
            if len(sorted_visible_widgets) <= 0:
                indicator_color = ft.Colors.PRIMARY
            else:
                indicator_color = sorted_visible_widgets[selected_idx].data.get('color', ft.Colors.PRIMARY)
        else:
            indicator_color = sorted_visible_widgets[selected_idx].data.get('color', ft.Colors.PRIMARY)


        # Go through them all, update their index to be accurate now
        for i, widget in enumerate(sorted_visible_widgets):
            widget.update_data(**{'index': i})

        # Build at tab bar with tabs for each widget
        self.tab_bar = ft.TabBar(
            tabs=[self.create_widget_tab_ctrl(widget) for widget in sorted_visible_widgets],    # Gives a tab for each widget
            scrollable=True, indicator_color=indicator_color, divider_height=2
        )

        # Build our tab view that holds each widget
        self.tab_view = ft.TabBarView(
            controls=[widget for widget in sorted_visible_widgets],     # Adds each widget
            expand=True
        )

        # Build our tabs control
        self.tabs = ft.Tabs(
            expand=True, 
            length=len(sorted_visible_widgets),
            selected_index=selected_idx,  
            on_change=self.tab_change,
            animation_duration=100,
            content=ft.Column([
                self.tab_bar,
                self.tab_view
            ], expand=True, spacing=0),
        )    

        # Set our tabs as the content
        self.content = self.tabs

        # If we're empty, skip all logic
        if len(sorted_visible_widgets) <= 0:
            self.tab_bar.tabs.append(self.create_placeholder_tab_ctrl())
            self.tab_view.controls.append(self.create_placeholder_tab_view())
            self.tabs.length = len(self.tab_bar.tabs)
            self.tabs.selected_index = 0
            return
        
# TODO: 
# plot chart need right click to add nodes
        


'''
    # OLD --------------------------------------------------------------
    # Arranges our widgets into the main pin
    def arrange_widgets(self):
        self.main_pin.clear()
        visible_widgets = [w for w in self.story.widgets.values() if w.data.get('visible', False)]
        sorted_widgets = sorted(visible_widgets, key=lambda w: w.data.get('index', 0))
        for i, w in enumerate(sorted_widgets):
            if w.data.get('visible', False):

                # Rebuild and add the widget to the main pin
                widget = self.story.rebuild_widget(w)  
                widget.update_data(**{'index': i})
                self.main_pin.append(widget)

    

    # Reloads the workspace
    def reload_workspace(self, update: bool=True):

        self.page.run_task(self.story.block_page)

        self.arrange_widgets()

        # If we're empty, skip all logic
        if len(self.main_pin) <= 0:
            self.content = None
            if update:
                self.update()
            self.page.run_task(self.story.unblock_page)
            return

        # Sets our new index when switching tabs
        async def tab_change(e: ft.Event):
            from models.widgets.canvas import Canvas

            # Save new selected index
            self.story.update_data(**{'workspace_selected_index': e.data})


            for idx, widget in enumerate(self.main_pin):
                if idx == e.data:
                    tabs.content.controls[0].indicator_color = widget.data.get('color', ft.Colors.ON_SURFACE_VARIANT)
                    tabs.content.controls[0].update()  

                # Make it so canvases don't redraw unneccesarily when switching tabs
                if isinstance(widget, Canvas):
                    widget.skip_first_resize = True

        sel_idx = int(self.story.data.get('workspace_selected_index', 0))

        # Tabs that hold our workspace
        tabs = ft.Tabs(
            expand=True, 
            length=len(self.main_pin),
            selected_index=sel_idx if sel_idx < len(self.main_pin) else len(self.main_pin) - 1,  
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
            #tabs.selected_index = len(self.main_pin) - 1    # Set the selected index
            #self.story.data['workspace_selected_index'] = len(self.main_pin) - 1 
            #self.story.update_data(**{'workspace_selected_index': len(self.main_pin) - 1})  # Update our story data to reflect the new selected index
            #tabs.content.controls[0].indicator_color = self.main_pin[-1].data.get('color', ft.Colors.ON_SURFACE_VARIANT)
            pass
            

        else:
            for widget in self.main_pin:
                if widget.data.get('index', -1) == self.story.data.get('workspace_selected_index', 0):
                    tabs.content.controls[0].indicator_color = widget.data.get('color', ft.Colors.ON_SURFACE_VARIANT)
                    tabs.selected_index = widget.data.get('index', 0)
                    break

        # If our selected index is out of range (The active tab was last and just hidden), make the last tab active
        if int(self.story.data.get('workspace_selected_index', 0)) >= len(self.main_pin):
            tabs.selected_index = len(self.main_pin) - 1
            self.story.update_data(**{'workspace_selected_index': len(self.main_pin) - 1})  # Update our story data to reflect the new selected index


        # Set our tabs as the content
        self.content = tabs

        if update:
            self.update()
        
        self.page.run_task(self.story.unblock_page)
'''