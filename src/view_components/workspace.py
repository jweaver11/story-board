'''
UI styling for the main workspace area of appliction that holds our widgets (tabs)
Returns our container with our formatting areas inside the workspace area.
The stories 'mast_stack' holds our 'master_row', which contains our five pins: top, left, main, right, and bottom.
Overtop that, we append our drag targets when we start dragging a widget (tab). Thats why its a stack
'''

import flet as ft
#from models.app import app
from models.views.story import Story
from models.widget import Widget
import functools
import json
from styles.colors import dark_gradient
from styles.snack_bar import SnackBar
from models.isolated_controls.row import IsolatedRow
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.tab_bar_view import IsolatedTabBarView
import asyncio
from styles.menu_option_style import MenuOptionStyle
import os
from models.widget import WidgetView
from models.widgets.note import NoteView
from contexts.contexts import StoryContext, OverlayContext

# Our workspace object that is stored in our story object
class WorkspaceOld(ft.Container):
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

    # Returns the active widget in the workspace as a reference
    def get_active_widget(self) -> Widget:
        if not self.tab_view.controls or self.tabs.selected_index is None or self.tabs.selected_index >= len(self.tab_view.controls):
            # Bandaid fix that returns the last widget. It fixes a selected_index bug I can't figure out, 
            # but it only happens when the last widget is the active widget, so this works
            return self.tab_view.controls[len(self.tab_bar.tabs) - 1]  
        return self.tab_view.controls[self.tabs.selected_index]

    # Adds a new widget to the workspace
    async def add_widget_to_workspace(self, widget: Widget):

        # Remove placeholder if workspace was empty
        if self.placeholder_visible:
            self.tab_bar.tabs.pop(0)
            self.tab_view.controls.pop(0)
            self.placeholder_visible = False

        # Rebuild widget to update page reference, set our new selected index to the end
        new_widget: Widget = self.story.rebuild_widget(widget)
        new_selected_index = len(self.tab_bar.tabs)

        # Add the tab header + a cheap placeholder — NOT the heavy widget yet
        self.tab_bar.tabs.append(self.create_widget_tab_ctrl(new_widget))
        self.tab_view.controls.append(ft.Container(ft.ProgressRing(), expand=True, alignment=ft.Alignment.CENTER))  # Lightweight stand-in

        # Upade length and new selected index
        self.tabs.length = len(self.tab_bar.tabs)
        self.tabs.selected_index = new_selected_index

        # Update data and indicator color for the new tab
        new_widget.update_data(**{'index': new_selected_index})
        self.story.update_data(**{'workspace_selected_index': new_selected_index})
        self.tab_bar.indicator_color = new_widget.data.get('color', ft.Colors.PRIMARY)

        # Flutter only has to render a blank Container first
        self.update()
        self.tab_bar.update()
        await asyncio.sleep(0.05)  # One frame for the lightweight update to land

        # Flutter engine is free now, so move_to will always work
        await self.tabs.move_to(new_selected_index, animation_duration=100)

        # Now swap the placeholder for the real widget - this is the costly update
        self.tab_view.controls[-1] = new_widget
        self.tab_view.update()

    

    

    # Removes a widget from the workspace
    async def remove_widget_from_workspace(self, widget: Widget):
        # Grab index
        widget_idx = widget.data.get('index', -100)
        if widget_idx < 0 or widget_idx >= len(self.tab_bar.tabs):  # Should be impossible
            self.page.show_dialog(SnackBar("Error: Widget index out of range when trying to remove from workspace: " + str(widget_idx)))
            return
        
        # Remove from controls and adjust length
        self.tab_bar.tabs.pop(widget_idx)
        self.tab_view.controls.pop(widget_idx)
        self.tabs.length = len(self.tab_bar.tabs)

        # Check selected index is still in range. If not, adjust it
        if self.tabs.selected_index >= len(self.tab_bar.tabs) - 1:
            self.tabs.selected_index = len(self.tab_bar.tabs) - 1
            self.story.update_data(**{'workspace_selected_index': self.tabs.selected_index})                

        # Add the placeholder if we need it
        if len(self.tab_bar.tabs) < 1:
            self.tab_bar.tabs.append(self.create_placeholder_tab_ctrl())
            self.tab_view.controls.append(self.create_placeholder_tab_view())
            self.tabs.length = len(self.tab_bar.tabs)
            self.tabs.selected_index = 0
            self.tab_bar.indicator_color = ft.Colors.PRIMARY
            self.update()
            return

        # Make sure indicator color is updated
        self.tab_bar.indicator_color = self.tab_view.controls[self.tabs.selected_index].data.get('color', ft.Colors.ON_SURFACE_VARIANT)

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

    # Handles a click event on a tab in the workspace
    async def tab_click(self, e: ft.Event):
        """Save the active widget before Flet switches to another tab."""
        selected_index = self.tabs.selected_index
        if 0 <= selected_index < len(self.tab_view.controls):
            selected_widget = self.tab_view.controls[selected_index]
            if hasattr(selected_widget, 'save_file'):
                await selected_widget.save_file()
    
    # Sets our new selected index when we change tabs and updates the tab bar indicator color to match the new selected tab
    async def tab_change(self, e: ft.Event):

        # Save new selected index
        new_selected_index = int(e.data)
        self.story.update_data(**{'workspace_selected_index': new_selected_index})

        # Set the new selected index and indicator color, then update
        self.tabs.selected_index = new_selected_index
        self.tab_bar.indicator_color = self.tab_view.controls[new_selected_index].data.get('color', ft.Colors.ON_SURFACE_VARIANT)
        self.update()

    # Saves the active widget on certain calls
    async def save_active_widget(self):
        widget = self.get_active_widget()
       

        print("Saving active widget:", widget.data.get('title'))
        if widget and hasattr(widget, 'save_file'):
            await widget.save_file()

        # TODO: Index wrong someone when hiding


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
            scrollable=True, indicator_color=indicator_color, divider_height=2,
            enable_feedback=False, 
            on_click=self.tab_click,
            label_padding=ft.Padding.only(left=6), #padding=ft.Padding.all(20)
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





@ft.component
def Workspace():

    

    # Called to hide the widget from the workspace
    async def hide_widget(widget):
        ''' Hides this widget from the workspace but keeps it in the story and rail '''
        await overlay.block_page()

        widget.visible = False
        story.widgets[widget.id] = widget   # Touch to observable to trigger observers

        if widget.tag == "canvas" or widget.tag == "manuscript" or widget.tag == "map" or widget.tag == "canvas_board":    # Widgets that must be rendered to save
            ft.context.page.run_task(widget.save_file)
        await overlay.unblock_page()

    @ft.component
    def build_widget_view(widget: Widget):
        ''' Returns the correct widget view based on the widgets tag'''
        match widget.tag:
            case "note": return NoteView(widget)
        return WidgetView(widget)

    # Creates a new tab control for the given widget
    @ft.component
    def build_widget_tab(widget: Widget) -> ft.Tab:
        ''' Returns a new tab control for the given widget '''

        # When renaming, show our textfield and hide our title
        async def handle_rename(e=None):
            #await self.story.close_menu()
            edit_title_tf.value = widget.title
            edit_title_tf.visible = True
            tab_title.visible = False
            tab_gd.update()
            await edit_title_tf.focus()

        # When done renaming or canceling, hide our textfield and show our title. Make sure title is updated
        def blur_edit_title_tf(e=None):
            edit_title_tf.visible = False
            tab_title.visible = True
            tab_title.value = widget.title
            tab_gd.update()

        # Set our icon based on what type of widget we have
        match widget.tag:
            case "manuscript": icon = ft.Icons.DESCRIPTION_OUTLINED
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
                if widget.chart_type == 'bar':
                    icon = ft.Icons.INSERT_CHART_OUTLINED 
                else:
                    icon = ft.CupertinoIcons.COMPASS
            case "comic_preview": icon = ft.Icons.SLIDESHOW_OUTLINED
            case "plot_chart": icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case _: icon = ft.Icons.ERROR_OUTLINE

        # Set the icon contrl
        tab_icon = ft.Icon(icon, color=widget.color)  

        # Title of the text in the tab
        tab_title = ft.Text(
            widget.title, weight=ft.FontWeight.BOLD, size=16, 
            color=ft.Colors.ON_SURFACE, overflow=ft.TextOverflow.ELLIPSIS, expand=True
        )

        # Textfield for renaming. starts hidden
        edit_title_tf = ft.TextField(
            value=widget.title,
            visible=False,
            on_blur=blur_edit_title_tf,
            on_submit=widget.submit_rename,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            #border_radius=4, dense=True, capitalization=ft.TextCapitalization.SENTENCES,
            #border_color=ft.Colors.TRANSPARENT,
            #focused_border_color=ft.Colors.PRIMARY,
        )

        # Button to remove the widget from the workspace
        hide_widget_button = ft.IconButton(    # Hide widget button on right side of tab
            scale=0.8,
            on_click=functools.partial(hide_widget, widget),    # partial (not lambda) so Flet awaits the coroutine directly
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=ft.Colors.OUTLINE,
            tooltip="Hide",
            mouse_cursor=ft.MouseCursor.CLICK,
        )

        file_path = os.path.join(
            widget.directory_path,
            f"{widget.id}.json",
        )

        #menu_options = [
            #MenuOptionStyle(
                #on_click=handle_rename,
                #content=ft.Row([
                    #ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, widget.color),
                    #ft.Text(
                       # "Rename", 
                       # weight=ft.FontWeight.BOLD, 
                    #), 
                #]),
            #),
            #ft.MenuItemButton(
                #leading=ft.Icon(ft.Icons.DOWNLOAD_OUTLINED, ft.Colors.PRIMARY), content="Export Widget", 
               # on_click=story.handle_export, 
                #close_on_click=True,
                #style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
               # tooltip="Export this part of your story.", data=file_path
            #),
        #] + widget.get_menu_options()  

        # Gesture Detector for opening menus that holds our tab icon, title, and hide button
        tab_gd = ft.GestureDetector(
            ft.Row([tab_icon, tab_title, edit_title_tf, hide_widget_button]),
            mouse_cursor=ft.MouseCursor.CLICK,
            hover_interval=40,
            #on_hover=widget.set_mouse_coords,
            #on_secondary_tap=lambda: story.open_menu(menu_options),
        )

        # Set the tab itself
        tab = ft.Tab(label=tab_gd, key=f"{widget.id}_tab") 
        return tab

    story = ft.use_context(StoryContext)
    overlay = ft.use_context(OverlayContext)

    visible_widgets = [widget for widget in story.widgets.values() if widget.visible]
    sorted_visible_widgets: list = sorted(visible_widgets, key=lambda w: w.index)



    # Build at tab bar with tabs for each widget
    tab_bar = ft.TabBar(
        tabs=[build_widget_tab(widget) for widget in sorted_visible_widgets] if len(sorted_visible_widgets) > 0 else [ft.Tab(" <- Add Widget")],    # Gives a tab for each widget
        scrollable=True, 
        #indicator_color=indicator_color, 
        divider_height=2,
        enable_feedback=False, 
        #on_click=self.tab_click,
        label_padding=ft.Padding.only(left=6), #padding=ft.Padding.all(20)
    )

    # Build our tab view that holds each widget
    tab_view = ft.TabBarView(
        controls=[
            build_widget_view(widget) for widget in sorted_visible_widgets
        ] if len(sorted_visible_widgets) > 0 else [
            ft.Container(ft.Text(" <- Add Widget"), alignment=ft.Alignment.CENTER_LEFT)
        ],
        expand=True
    )

    return ft.Tabs(
        expand=True, 
        length=len(sorted_visible_widgets) if len(sorted_visible_widgets) > 0 else 1,
        selected_index=story.selected_index if story.selected_index <= len(sorted_visible_widgets) else 0,
        #selected_index=0,
        #on_change=self.tab_change,
        animation_duration=100,
        content=ft.Column([
            tab_bar,
            tab_view
        ], expand=True, spacing=0),
        key=f"{story.id}_workspace"
    )    


    