""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.menu_option_style import MenuOptionStyle
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.list_view import IsolatedListView
from styles.rail.widget_rail_item import WidgetRailItem


class WorldBuildingRail(Rail):

    # Constructor
    def __init__(self, story: Story):
        
        # Initialize the parent Rail class first
        super().__init__(story=story)

          

    # Called to return our list of menu options for the content rail
    def get_new_item_menu_options(self) -> list[ft.Control]:
            
        # Builds our buttons that are our options in the menu
        return [
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                            data="map", on_click=self.new_item_clicked, close_on_click=True,
                            tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        ),
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), ft.Text("World", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("world"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                            tooltip="Create a new world for your story. Choose from templates or create a default world."
                        ),
                        ft.SubmenuButton(
                            ft.Row([ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, ft.Colors.PRIMARY), ft.Text("Chart", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                            self.get_template_options("chart"), 
                            menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                            style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                            tooltip="New Charts for your story"
                        ), 
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.STAR_OUTLINE_ROUNDED, ft.Colors.PRIMARY), content="Item", 
                            data="item", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), 
                            tooltip="New Items and Equipment for your story"
                        ),  
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True
            ),

            # Upload options
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True, 
            ),
            
        ]


    # Called on startup and when we have changes to the rail that have to be reloaded 
    def build(self):
        ''' Reloads/Rebuilds our rail based on current data '''

        async def _change_sort_method(e: ft.Event):
            new_sort_method = e.data
            self.story.update_data(**{'world_building_rail_sort_method': new_sort_method})
            self.story.active_rail.reload_rail()

        async def _change_sort_direction(e: ft.Event):

            old_sort_method = self.story.data.get('world_building_rail_sort_direction', "Ascending")
            if old_sort_method == "Ascending":
                self.story.update_data(**{'world_building_rail_sort_direction': "Descending"})
                e.control.tooltip = "Sort Direction: Descending"
                e.control.icon = ft.CupertinoIcons.SORT_UP
            else:
                self.story.update_data(**{'world_building_rail_sort_direction': "Ascending"})
                e.control.tooltip = "Sort Direction: Ascending"
                e.control.icon = ft.CupertinoIcons.SORT_DOWN

            maps_list_view.reverse = self.story.data.get('world_building_rail_sort_direction', "Ascending") == "Descending"
            worlds_list_view.reverse = self.story.data.get('world_building_rail_sort_direction', "Ascending") == "Descending"
            charts_list_view.reverse = self.story.data.get('world_building_rail_sort_direction', "Ascending") == "Descending"
            maps_list_view.update()
            worlds_list_view.update()
            charts_list_view.update()
            e.control.update()

        async def _reorder_widget(e: ft.OnReorderEvent):
            ''' Handles the reordering and reloading of world_buildings based on their new positions on the rail when we drag and drop them '''
            
            # If we didn't move, return out
            if e.old_index == e.new_index:
                return
            
            # Move the control up the list
            e.control.controls.insert(e.new_index, e.control.controls.pop(e.old_index))
            e.control.update()

            # Update the indices of the world_buildings we dragged past as well
            for idx, ctrl in enumerate(e.control.controls):
                widget = ctrl.content.widget
                if widget.data.get('rail_index', 999) != idx:
                    widget.update_data(**{'rail_index': idx})

        top_row_buttons = [
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, "primary"),
                    shape=ft.BoxShape.CIRCLE,
                    alignment=ft.Alignment.CENTER
                ),
                [
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.MAP_OUTLINED, ft.Colors.PRIMARY), content="Map",
                        data="map", on_click=self.new_item_clicked, close_on_click=True,
                        tooltip="Create a new Map to visualize the locations of your story and the layout of your world",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    ),
                    ft.SubmenuButton(
                        ft.Row([ft.Icon(ft.Icons.PUBLIC_OUTLINED, ft.Colors.PRIMARY), ft.Text("World", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                        self.get_template_options("world"), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="Create a new world for your story. Choose from templates or create a default world."
                    ),
                    ft.SubmenuButton(
                        ft.Row([ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, ft.Colors.PRIMARY), ft.Text("Chart", color=ft.Colors.ON_SURFACE, expand=True)], expand=True),
                        self.get_template_options("chart"), 
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                        style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="New Charts for your story"
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.STAR_OUTLINE_ROUNDED, ft.Colors.PRIMARY), content="Item", 
                        data="item", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                        tooltip="New Items and Equipment for your story"
                    ),  
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, ft.Colors.OUTLINE),
                    shape=ft.BoxShape.CIRCLE,
                    alignment=ft.Alignment.CENTER
                ),
                [     
                    
                ],
                disabled=True,
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
        ]      
        

        menubar = ft.MenuBar(
            top_row_buttons,
            style=ft.MenuStyle(
                bgcolor="transparent", shadow_color="transparent",
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[menubar]
        )


        
        # Methods: index, color
        sort_dropdown = ft.Dropdown(
            self.story.data.get('world_building_rail_sort_method', "Index"),
            [
                ft.DropdownOption(
                    "Default", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=10)),
                    tooltip="Sort world building widgets by the order they were loaded. On Windows, usually alphabetical. On Mac, usually by creation date."
                ),
                ft.DropdownOption(
                    "Index", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=10)),
                    tooltip="Sort world building widgets by a reorderable index so you can drag them up and down on the rail."
                ), 
                ft.DropdownOption(
                    "Color", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=10)),
                    tooltip="Sort world building widgets by their color."
                )
            ],
            label="Sort by",
            dense=True, expand=True,
            on_select=_change_sort_method,
            border_color=ft.Colors.OUTLINE_VARIANT,
            leading_icon=ft.IconButton(
                ft.CupertinoIcons.SORT_DOWN if self.story.data.get('world_building_rail_sort_direction', "Ascending") == "Ascending" else ft.CupertinoIcons.SORT_UP,
                ft.Colors.PRIMARY, 
                tooltip=f"Sort Direction: {self.story.data.get('world_building_rail_sort_direction', 'Ascending')}", 
                on_click=_change_sort_direction, mouse_cursor="click", 
            ),
            menu_style=ft.MenuStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
        )
           
        # List for our world_buildings and world_building connection maps
        maps = []
        worlds = []
        charts = []
        items = []

        # Add all character and CCM widgets to their respective lists
        for widget in self.story.widgets.values():
            if widget.data.get('tag', "") == "map":
                maps.append(widget)
            elif widget.data.get('tag', "") == "world":
                worlds.append(widget)    
            elif widget.data.get('tag', "") == "chart":
                charts.append(widget)
            elif widget.data.get('tag', "") == "item":
                items.append(widget)

        # Sort lists by color
        if self.story.data.get('world_building_rail_sort_method', "Index") == "Color":

            # Sort our world_buildings and ccms
            maps.sort(key=lambda c: c.data.get('color', "default"))
            worlds.sort(key=lambda c: c.data.get('color', "default"))
            charts.sort(key=lambda c: c.data.get('color', "default"))
            items.sort(key=lambda c: c.data.get('color', "default"))    

            # Build our controls for maps and ccms
            map_controls = [WidgetRailItem(char) for char in maps]
            world_controls = [WidgetRailItem(ccm) for ccm in worlds] 
            chart_controls = [WidgetRailItem(chart) for chart in charts]
            item_controls = [WidgetRailItem(item) for item in items]

        # Sort lists by index (default)
        elif self.story.data.get('world_building_rail_sort_method', "Index") == "Index":
            maps.sort(key=lambda c: c.data.get('rail_index', 0))
            worlds.sort(key=lambda c: c.data.get('rail_index', 0))
            charts.sort(key=lambda c: c.data.get('rail_index', 0))
            items.sort(key=lambda c: c.data.get('rail_index', 0))

            map_controls = [ft.ReorderableDragHandle(WidgetRailItem(char)) for char in maps]
            world_controls = [ft.ReorderableDragHandle(WidgetRailItem(ccm)) for ccm in worlds]
            chart_controls = [ft.ReorderableDragHandle(WidgetRailItem(chart)) for chart in charts]
            item_controls = [ft.ReorderableDragHandle(WidgetRailItem(item)) for item in items]

            # Update their index by their actual rail position now, since new maps start with index of 999
            for idx, map in enumerate(maps):
                if map.data.get('rail_index', 999) != idx:
                    map.update_data(**{'rail_index': idx})

            for idx, world in enumerate(worlds):
                if world.data.get('rail_index', 999) != idx:
                    world.update_data(**{'rail_index': idx})

            for idx, chart in enumerate(charts):
                if chart.data.get('rail_index', 999) != idx:
                    chart.update_data(**{'rail_index': idx})

            for idx, item in enumerate(items):
                if item.data.get('rail_index', 999) != idx:
                    item.update_data(**{'rail_index': idx})

        # Otherwise just sort by the way the system loaded them
        else:
            map_controls = [WidgetRailItem(char) for char in maps]
            world_controls = [WidgetRailItem(ccm) for ccm in worlds]
            chart_controls = [WidgetRailItem(chart) for chart in charts]
            item_controls = [WidgetRailItem(item) for item in items]
        
        
        maps_list_view = ft.ReorderableListView(
            map_controls, 
            on_reorder=_reorder_widget, 
            spacing=0, show_default_drag_handles=False, 
            reverse=self.story.data.get('world_building_rail_sort_direction', "Ascending") == "Descending"
        )

        worlds_list_view = ft.ReorderableListView(
            world_controls,
            on_reorder=_reorder_widget,
            spacing=0, show_default_drag_handles=False, 
            reverse=self.story.data.get('world_building_rail_sort_direction', "Ascending") == "Descending"
        )

        charts_list_view = ft.ReorderableListView(   
            chart_controls,
            on_reorder=_reorder_widget,
            spacing=0, show_default_drag_handles=False,
            reverse=self.story.data.get('world_building_rail_sort_direction', "Ascending") == "Descending"
        )

        items_list_view = ft.ReorderableListView(
            item_controls,
            on_reorder=_reorder_widget,
            spacing=0, show_default_drag_handles=False,
            reverse=self.story.data.get('world_building_rail_sort_direction', "Ascending") == "Descending"
        )
        

        # Build the content of our rail
        content = IsolatedListView(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            expand=True,
            controls=[
                # Spacer and new item text field
                ft.Container(height=6),
                self.new_item_textfield,

                ft.Text("\tMaps", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),

                # Our characters
                maps_list_view,

                # Spacer and label for Character Connection Maps Section
                ft.Divider(),
                ft.Text("\tWorlds", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                
                # Our CCM's
                worlds_list_view,

                ft.Divider(),
                ft.Text("\tCharts", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                charts_list_view,

                ft.Divider(),
                ft.Text("\tItems", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                items_list_view,

                ft.Container(expand=True)
            ] 
                
        )

        menu_gesture_detector = ft.GestureDetector(
            content=content, expand=True, on_hover=self._set_menu_coords,
            on_secondary_tap=lambda _: self.story.open_menu(self.get_new_item_menu_options()), 
            hover_interval=20,
        )

        self.controls = [
            header,
            ft.Divider(thickness=2, leading_indent=8),
            menu_gesture_detector,
            ft.Container(ft.Row([sort_dropdown]), margin=ft.Margin.symmetric(horizontal=4)),
        ]
        
        
        


        
