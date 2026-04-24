# Charts for a story

''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_field import TextField
import flet_charts as fch
from styles.colors import colors
import math
    

class Chart(Widget):

    # Constructor
    def __init__(
        self, 
        title: str, 
        page: ft.Page, 
        directory_path: str, 
        story: Story, 
        data: dict = None, 
        is_rebuilt: bool = False,
        type: str = "bar"           # Type of chart we are (either bar or radar)
    ):

        # Check if we're new and need to create file
        is_new = False
        if data is None:
            is_new = True

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      
            page = page,                        
            directory_path = directory_path,    
            story = story,                     
            data = data,
            is_rebuilt = is_rebuilt
        )
        

        verify_data(
            self,   # Pass in our own data so the function can see the actual data we loaded
            {
                # Widget data
                'key': f"{self.directory_path}\\{return_safe_name(self.title)}_chart", 
                'tag': "chart",             # Tag to identify what type of object this is
                'color': app.settings.data.get('default_chart_color'),
                'pin_location': app.settings.data.get('default_chart_pin_location', "right") if data is None else data.get('pin_location', "right"),   # Default pin location for items
                'type': type,             # How our chart is being displayed (bar or radar)
                'Description': str,

                'show_info': True,   # Whether to show the info column on the side of our charts or not.

                'bar_data': {
                    'left_axis_title': "Left Axis",
                    'bottom_axis_title': "Bottom Axis",
                    'show_labels': True,           # Whether to show labels on our axes or not
                    'rod_shape': "rounded",          # The shape of our bars/rods. Either "rounded" or "square"
                    'rod_width': 30,         # The width of our bars/rods. Only applies to vertical bar charts, not horizontal ones
                    'stack_rods': False,      # If False, rods display on top of each other, not side by side
                    'show_horizontal_grid_lines': True,
                    'show_vertical_grid_lines': False,
                    'max_y': 20,        # The max y value of our chart, which is the value that will fill the whole chart. Should be higher than any value in our bars
                    'groups': [
                        #{
                            #'name': "Group 1", 
                            #'visible': True,
                            #'expanded': False,
                            #'rods': [
                                #{'to_y': 5, 'color': "primary"},
                                #{'to_y': 10, 'color': "primary"},
                                #{'to_y': 7, 'color': "primary"},
                            #]
                        #},
                    ]
                },        


                # Data used for radar charts
                'radar_data': {
                    'nodes': [     # Titles around the edge of the chart
                        "Node 1", 
                        "Node 2", 
                        "Node 3", 
                        "Node 4",
                        "Node 5"
                    ],   
                    'make_chart_round': True,   # Whether to show our radar chart as a circle or polygon
                    'min_value': 0,     # The minimum value for our radar chart, which will be the center point of the chart
                    'max_value': 20,    # The maximum value for our radar chart, which will be the outer edge of the chart
                    'tick_count': 2,    # Number of tick lines between the center and outer edge of the chart
                    'show_tick_labels': False,      # Whether to show the labels for each tick line or not
                    'rotate_node_titles': True,    # Whether to keep our titles flat and not rotate them with the chart or not
                    'data_sets': [      # The data sets that make up the radar chart
                        {               # Starts maximized invisible so they can see other datasets at all times
                            'color': "transparent",
                            'entries': [0, 20, 20, 20, 20],   # The values for each title/axis of the radar chart. First value is min, second is max
                            'visible': True,
                            'title': "Data Set 1",
                            'expanded': False,   # Whether the dataset's info is expanded in the side column
                        },
                        #{},...
                        
                    ]     
                }

            },
        )

        if self.data.get('type', "") == "bar":
            self.icon.icon = ft.Icons.INSERT_CHART_OUTLINED
        else:
            self.icon.icon = ft.CupertinoIcons.COMPASS

        # Saving creates the file if we're new
        if is_new:
            self.p.run_task(self.save_dict)
        
        if self.visible:
            self.reload_widget()         # Build our widget if it's visible on init


    # Returns our widgets view for bar charts
    def _bar_chart_view(self):
        ''' Builds out the body of our bar chart widget '''


        async def _toggle_group_visibility(e):
            idx = e.control.data
            group = self.data.get('bar_data', {}).get('groups', [])[idx]
            group['visible'] = not group.get('visible', True)
            await self.save_dict()
            self.reload_widget()

        async def _update_group_title(e):
            idx = e.control.data
            new_title = e.control.value
            self.data.get('bar_data', {}).get('groups', [])[idx]['name'] = new_title
            await self.save_dict()
            chart.bottom_axis.labels[idx].label = new_title
            chart.update()

        async def _delete_group(e):
            idx = e.control.data

            async def _delete_group_confirm(_):
                
                self.data.get('bar_data', {}).get('groups', []).pop(idx)
                await self.save_dict()
                self.reload_widget()
                self.p.pop_dialog()
                

            group_title = self.data.get('bar_data', {}).get('groups', [])[idx].get('name', "Group")

            dlg = ft.AlertDialog(
                title=f"Are you sure you want to delete {group_title}?",
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.PRIMARY)),
                    ft.TextButton("Delete", on_click=_delete_group_confirm, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                ]
            )
            self.p.show_dialog(dlg)

        async def _update_expanded_state(e):
            expanded = e.control.expanded
            idx = e.control.data
            self.data.get('bar_data', {}).get('groups', [])[idx]['expanded'] = expanded
            await self.save_dict()

        async def _add_rod_clicked(e):
            idx = e.control.data
            group = self.data.get('bar_data', {}).get('groups', [])[idx]
            median_value = int(self.data.get('bar_data', {}).get('max_y', 20) / 2)
            if median_value < self.data.get('radar_data', {}).get('min_value', 0):
                median_value = int(self.data.get('radar_data', {}).get('min_value', 0))
            group['rods'].append({
                'to_y': median_value, 
                'color': "primary"
            })
            await self.save_dict()
            self.reload_widget()

        async def _update_rod_value(e):
            idx, rod_idx = e.control.data
            new_value = int(e.control.value)

            # Update our data model
            self.data['bar_data']['groups'][idx]['rods'][rod_idx]['to_y'] = new_value

            # Find acutal index here in case of hidden groups
            visible_idx = -1
            for i, group in enumerate(self.data.get('bar_data', {}).get('groups', [])):
                if group.get('visible', True):
                    visible_idx += 1
                if i == idx:
                    break

            # Update the chart visually in real-time
            chart.groups[visible_idx].rods[rod_idx].to_y = new_value
            chart.update()

        async def _delete_rod_clicked(e):
            idx, rod_idx = e.control.data

            
            self.data['bar_data']['groups'][idx]['rods'].pop(rod_idx)
            await self.save_dict()
            self.reload_widget()
            self.p.pop_dialog()

        async def _change_rod_color(e):
            idx, rod_idx = e.control.data
            new_color = e.control.content
            e.control.parent.icon_color = new_color
            e.control.parent.update()   

            self.data['bar_data']['groups'][idx]['rods'][rod_idx]['color'] = new_color
            await self.save_dict()
            chart.groups[idx].rods[rod_idx].color = new_color
            chart.update()

           

        # Class to hold our datasets in the dropdown menu in the info column
        class BarGroup(ft.ExpansionTile):
            def __init__(self, title: str, color: str, rods: list, visible: bool, idx: int, expanded: bool, min_value: int = 0, max_value: int = 20):
                self.index = idx
            
                super().__init__(
                    leading=ft.IconButton(
                        ft.Icons.VISIBILITY_OUTLINED if visible else ft.Icons.VISIBILITY_OFF_OUTLINED,
                        ft.Colors.PRIMARY,
                        on_click=_toggle_group_visibility,
                        mouse_cursor=ft.MouseCursor.CLICK, 
                        data=idx,
                    ),
                    title=TextField(
                        title, dense=True, data=idx, expand=True,
                        suffix_icon=ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                            mouse_cursor=ft.MouseCursor.CLICK, data=idx,
                            on_click=_delete_group
                        ),
                        on_blur=_update_group_title
                    ),
                    dense=True, tile_padding=ft.Padding.only(right=20), controls_padding=ft.Padding.only(right=30, left=30),
                    expanded=expanded, 
                    controls=[
                        ft.Row([
                            ft.Text("Rods", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, weight=ft.FontWeight.BOLD, size=14),
                            ft.TextButton(
                                "Add New Rod", #ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.BOLD)), 
                                on_click=_add_rod_clicked, 
                                data=idx
                            )
                        ]),
                    ] + [
                        
                        ft.Row([
                            ft.PopupMenuButton(
                                icon=ft.Icons.COLOR_LENS_OUTLINED, 
                                icon_color=rod.get('color', ft.Colors.PRIMARY) if visible else ft.Colors.ON_SURFACE_VARIANT, 
                                menu_padding=ft.Padding.all(0),
                                tooltip="Change Color",
                                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                                items=[
                                    ft.PopupMenuItem(
                                        color.capitalize(), label_text_style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD),
                                        mouse_cursor=ft.MouseCursor.CLICK,
                                        on_click=_change_rod_color, data=(idx, i)
                                    ) for color in colors
                                ]
                            ),
                            ft.Text(str(min_value), weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                            ft.Slider(
                                value=rod.get('to_y', 0), 
                                min=min_value,
                                max=max_value, 
                                label="{value}", on_change=_update_rod_value, 
                                data=(idx, i),
                                expand=True,
                                divisions=max_value - min_value if max_value > min_value else None,
                                disabled=True if not visible else False
                            ),
                            ft.Text(str(max_value), weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, on_click=_delete_rod_clicked, data=(idx, i), mouse_cursor=ft.MouseCursor.CLICK)    
                        ], spacing=0) for i, rod in enumerate(rods)
                    ],
                    data=idx,
                    on_change=_update_expanded_state,
                    
                )
                

        # TODO:
        # Add labels to Bar Chart Groups
        # Hide Groups. And rods????

        async def _set_axis_title(e):
            new_title = e.control.value
            axis = e.control.data

            match axis:

                # Update our data and chart to reflect
                case "left":
                    self.data['bar_data']['left_axis_title'] = new_title
                    chart.left_axis.title = ft.Text(new_title, theme_style=ft.TextThemeStyle.LABEL_LARGE,  size=18)
                    
                case "bottom":
                    self.data['bar_data']['bottom_axis_title'] = new_title
                    chart.bottom_axis.title = ft.Text(new_title, theme_style=ft.TextThemeStyle.LABEL_LARGE,  size=18)
                    
                case "top":
                    self.data['bar_data']['top_axis_title'] = new_title
                    chart.top_axis.title = ft.Text(new_title, theme_style=ft.TextThemeStyle.LABEL_LARGE,  size=18)
                    
                case "right":
                    self.data['bar_data']['right_axis_title'] = new_title
                    chart.right_axis.title = ft.Text(new_title, theme_style=ft.TextThemeStyle.LABEL_LARGE,  size=18)


            await self.save_dict()
            chart.update()

        async def _set_max_value(e):
            
            if e.control.value == "" or e.control.value is None:
                return
            new_value = int(e.control.value)
            self.data['bar_data']['max_y'] = new_value       

            await self.save_dict()
            chart.max_y = new_value
            chart.update()   

        async def _set_show_labels(e):
            self.data['bar_data']['show_labels'] = e.control.value
            chart.left_axis.show_labels = e.control.value
            chart.bottom_axis.show_labels = e.control.value

            await self.save_dict()
            chart.update()
        
        async def _set_rod_width(e):
            
            new_width = int(e.control.value)
            self.data['bar_data']['rod_width'] = new_width
            for group in chart.groups:
                for rod in group.rods:
                    rod.width = new_width

            await self.save_dict()
            chart.update()

        async def _set_stacked_rods(e):
            self.data['bar_data']['stack_rods'] = e.control.value
            for group in chart.groups:
                group.group_vertically = e.control.value

            await self.save_dict()
            chart.update()

        async def _set_rod_shape(e):
            new_shape = "rounded" if e.control.value else "square"
            self.data['bar_data']['rod_shape'] = new_shape
            for group in chart.groups:
                for rod in group.rods:
                    rod.border_radius = None if new_shape == "rounded" else ft.BorderRadius.only(top_left=2, top_right=2)

            await self.save_dict()
            chart.update()

        async def _set_grid_lines(e):
            grid_line_type = e.control.data
            show_grid_lines = e.control.value

            match grid_line_type:
                case "horizontal":
                    self.data['bar_data']['show_horizontal_grid_lines'] = show_grid_lines
                    chart.horizontal_grid_lines = fch.ChartGridLines() if show_grid_lines else None
                case "vertical":
                    self.data['bar_data']['show_vertical_grid_lines'] = show_grid_lines
                    chart.vertical_grid_lines = fch.ChartGridLines() if show_grid_lines else None

            await self.save_dict()
            chart.update()

        x_labels = []
        for idx, group in enumerate(self.data.get('bar_data', {}).get('groups', [])):
            if group.get('visible', True) == False:
                continue
            print("group name: ", group.get('name', ""))
            x_labels.append(fch.ChartAxisLabel(idx, label=group.get('name', "")))

        # Our bar chart
        chart = fch.BarChart(
            
            # User customizable options
            max_y=self.data.get('bar_data', {}).get('max_y', 20),
            bottom_axis=fch.ChartAxis(
                ft.Text(self.data.get('bar_data', {}).get('bottom_axis_title'), theme_style=ft.TextThemeStyle.LABEL_LARGE,  size=18),
                title_size=40, label_size=30,
                show_labels=self.data.get('bar_data', {}).get('show_labels', False),
                labels=x_labels
            ),
            left_axis=fch.ChartAxis(
                ft.Text(self.data.get('bar_data', {}).get('left_axis_title'), theme_style=ft.TextThemeStyle.LABEL_LARGE, size=18), 
                title_size=40, label_size=30,
                show_labels=self.data.get('bar_data', {}).get('show_labels', False),
                
            ),
            top_axis=fch.ChartAxis(ft.Text(""), labels=fch.ChartAxisLabel(0, " ")), # Invisible label for behavior purposes
            horizontal_grid_lines=fch.ChartGridLines() if self.data.get('bar_data', {}).get('show_horizontal_grid_lines', False) else None,
            vertical_grid_lines=fch.ChartGridLines() if self.data.get('bar_data', {}).get('show_vertical_grid_lines', False) else None,

            # Constants - user cannot change
            expand=3,
            interactive=True,
            animation=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            border=ft.Border.only(
                left=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT),
                bottom=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT),
            ),
            
        )

        # Load our data into the chart
        for idx, group in enumerate(self.data.get('bar_data', {}).get('groups', [])):
            # Skip hidden ones
            if group.get('visible', True) == False:
                continue
            group = fch.BarChartGroup(
                idx,
                spacing=4, 
                group_vertically=self.data.get('bar_data', {}).get('stack_rods', False),
                rods=[
                    fch.BarChartRod(
                        from_y=0, to_y=rod.get('to_y', 0), 
                        width=self.data.get('bar_data', {}).get('rod_width', 30),
                        border_radius=None if self.data.get('bar_data', {}).get('rod_shape', "rounded") == "rounded" else ft.BorderRadius.only(top_left=2, top_right=2),
                        color=rod.get('color', self.data.get('color', ft.Colors.PRIMARY)),
                    ) for rod in group.get('rods', [])
                ]
            )
            chart.groups.append(group)

        
        # If we're not showing info, just give us a button to show info and return early
        if not self.data.get('show_info', True):

            self.body_container.content = ft.Row(
                [
                    ft.Container(chart, expand=3, padding=ft.Padding.only(left=20, bottom=20)), 
                    ft.IconButton(
                        ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
                        on_click=self._toggle_show_info, 
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    )
                ], expand=True, spacing=0
            )
            return  # Don't load the info column if we're not showing it     
        
        # Adding a new dataset with default values in each node
        async def _add_group(e):
            median_value = int(self.data.get('bar_data', {}).get('max_y', 20) / 2)
            if median_value < self.data.get('radar_data', {}).get('min_value', 0):
                median_value = int(self.data.get('radar_data', {}).get('min_value', 0))
            self.data['bar_data']['groups'].append({
                'name': f"Group {len(self.data.get('bar_data', {}).get('groups', [])) + 1}",
                'visible': True,
                'expanded': False,
                'rods': [
                    {
                        'to_y': median_value, 
                        'color': "primary"
                    }
                ]
            })
            await self.save_dict()
            self.reload_widget()
        
        def _get_groups_info() -> list[ft.Control]:
            controls = [
                # Data for our bar chart info sections
                ft.Row([
                    ft.Text(f"\tData", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        self.data.get('color', ft.Colors.PRIMARY),
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_click=_add_group,
                    ),
                ], spacing=0),
            ]

            for idx, group in enumerate(self.data.get('bar_data', {}).get('groups', [])):
                controls.append(
                    BarGroup(
                        title=group.get('name', "Group"), 
                        color=group.get('rods', [{}])[0].get('color', self.data.get('color', ft.Colors.PRIMARY)) if len(group.get('rods', [])) > 0 else self.data.get('color', ft.Colors.PRIMARY), 
                        rods=[rod for rod in group.get('rods', [])], 
                        visible=group.get('visible', True),
                        idx=idx, 
                        expanded=group.get('expanded', False),
                        min_value=0,
                        max_value=self.data.get('bar_data', {}).get('max_y', 20)
                    )
                )

            return controls


        groups_info = _get_groups_info()
       
        info_column = ft.Column(
            expand=True, scroll="auto", spacing=0,
            controls=groups_info + [
                
                
                ft.Divider(),

                
                # Appearence and information sections
                ft.Text(f"\tAppearence", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                ft.Container(height=10),

                # Axis titles
                ft.Row([
                    TextField(
                        label="Left Axis Title", value=self.data.get('bar_data', {}).get('left_axis_title', ""), 
                        expand=True, data="left", on_blur=_set_axis_title
                    ),
                    TextField(
                        label="Bottom Axis Title", value=self.data.get('bar_data', {}).get('bottom_axis_title', ""), 
                        expand=True, data="bottom", on_blur=_set_axis_title
                    ),
                ]),
                
                ft.Container(height=10),

                # Max y value   
                TextField(
                    label="Max Y Value", value=str(self.data.get('bar_data', {}).get('max_y', 20)), 
                    input_filter=ft.NumbersOnlyInputFilter(), data="max", on_blur=_set_max_value
                ),
                

                # Rod options
                ft.Row([
                    ft.Text("Rod Width", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                    ft.Slider(
                        value=self.data.get('bar_data', {}).get('rod_width', 30), min=10, max=100, 
                        label="{value}", expand=True, on_change=_set_rod_width
                    ),
                ], spacing=0),
                ft.Switch(
                    value=self.data.get('bar_data', {}).get('stack_rods', False), 
                    label="\tStack Rods", on_change=_set_stacked_rods
                ),
                ft.Switch(
                    value=True if self.data.get('bar_data', {}).get('rod_shape', "rounded") == "rounded" else False, 
                    label="\tRounded Rods", on_change=_set_rod_shape
                ),

                # Axis and Grid line options
                ft.Switch(
                    value=self.data.get('bar_data', {}).get('show_labels', False), 
                    label="\tShow Axis Labels", on_change=_set_show_labels
                ),
                ft.Switch(
                    value=self.data.get('bar_data', {}).get('show_horizontal_grid_lines', False), 
                    label="\tShow Horizontal Grid Lines", on_change=_set_grid_lines, data="horizontal"
                ),
                ft.Switch(
                    value=self.data.get('bar_data', {}).get('show_vertical_grid_lines', False), 
                    label="\tShow Vertical Grid Lines", on_change=_set_grid_lines, data="vertical"
                ),

                
                
            ]
        )

        chart_info = ft.Container(
            expand=1,
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8,),
            shadow=ft.BoxShadow(0, 1),
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            content=ft.Column(
                [
                    ft.Row([
                        ft.Text(
                            f"\tChart Info", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, 
                            color=self.data.get('color', None), expand=True
                        ),
                        ft.IconButton(
                            ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=self._toggle_show_info,
                            mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                        ),
                    ]),
                    ft.Divider(2, 2),

                    info_column
                ], expand=True, scroll="none", spacing=0),
        )
        self.body_container.content = ft.Row(
            [
                ft.Container(chart, expand=3, padding=ft.Padding.only(bottom=20, left=20)),
                chart_info
            ], expand=True, spacing=0
        )
        
        
    # Returns our widgets view for radar charts
    def _radar_chart_view(self):
        ''' Builds out the body of our radar chart widget '''
        
        async def _update_entry(e):
            idx, entry_idx = e.control.data
            new_value = int(e.control.value)

            # Update our data model
            self.data['radar_data']['data_sets'][idx]['entries'][entry_idx] = new_value

            # Find acutal index here in case of hidden datasets
            visible_idx = -1
            for i, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', [])):
                if ds.get('visible', True):
                    visible_idx += 1
                if i == idx:
                    break

            # Update the chart visually in real-time
            chart.data_sets[visible_idx].entries[entry_idx].value = new_value
            chart.update()

        # Updates the title of a dataset
        async def _update_dataset_title(e):
            entry_idx = e.control.data
            new_title = e.control.value

            self.data.get('radar_data', {}).get('data_sets', [])[entry_idx]['title'] = new_title
            await self.save_dict()
            self.reload_widget()

        # Updates whether our dataset is expanded in the info column or not
        async def _update_expanded_state(e):
            expanded = e.control.expanded
            idx = e.control.data
            self.data.get('radar_data', {}).get('data_sets', [])[idx]['expanded'] = expanded
            await self.save_dict()

        # Class to hold our datasets in the dropdown menu in the info column
        class DataSet(ft.ExpansionTile):
            def __init__(self, title: str, color: str, entries: list, visible: bool, idx: int, expanded: bool, min_value: int = 0, max_value: int = 20):
                self.index = idx
            
                super().__init__(
                    leading=ft.IconButton(
                        ft.Icons.VISIBILITY_OUTLINED if visible else ft.Icons.VISIBILITY_OFF_OUTLINED,
                        color if visible else ft.Colors.ON_SURFACE_VARIANT,
                        on_click=_toggle_dataset_visibility,
                        mouse_cursor=ft.MouseCursor.CLICK, data=idx,
                    ),
                    title=TextField(
                        title, dense=True, data=idx, expand=True,
                        prefix_icon=ft.PopupMenuButton(
                            icon=ft.Icons.COLOR_LENS_OUTLINED, 
                            icon_color=color, menu_padding=ft.Padding.all(0),
                            tooltip="Change Color",
                            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                            items=[
                                ft.PopupMenuItem(
                                    color.capitalize(), label_text_style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD),
                                    data=idx, on_click=_change_dataset_color, mouse_cursor=ft.MouseCursor.CLICK
                                ) for color in colors
                            ]
                        ),
                        suffix_icon=ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                            mouse_cursor=ft.MouseCursor.CLICK, data=idx,
                            on_click=_delete_data_set
                        ),
                        on_blur=_update_dataset_title
                    ),
                    dense=True, tile_padding=ft.Padding.only(right=20), controls_padding=ft.Padding.only(right=30, left=30),
                    #shape=ft.RoundedRectangleBorder(), 
                    expanded=expanded,
                 
                    controls=[
                        ft.Row([
                            ft.Text(str(min_value), weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                            ft.Slider(
                                value=entry, 
                                min=min_value,
                                max=max_value, 
                                label="{value}", on_change=_update_entry, data=(idx, i),
                                expand=True,
                                divisions=max_value - min_value if max_value > min_value else None,
                                disabled=True if not visible else False
                            ),
                            ft.Text(str(max_value), weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE)
                        ], spacing=0) for i, entry in enumerate(entries)
                    ],
                    data=idx,
                    on_change=_update_expanded_state
                )

        should_rotate = self.data.get('radar_data', {}).get('rotate_node_titles', False)
        
        chart = fch.RadarChart(
            expand=3,
            titles=[fch.RadarChartTitle(title, None if should_rotate else 360) for title in self.data.get('radar_data', {}).get('nodes', [])],
            center_min_value=True,
            tick_count=self.data.get('radar_data', {}).get('tick_count', 2),
            ticks_text_style=ft.TextStyle(
                size=16, color=ft.Colors.TRANSPARENT, italic=True
            ) if not self.data.get('radar_data', {}).get('show_tick_labels', False) else 
                ft.TextStyle(size=16, color=self.data.get('color', ft.Colors.ON_SURFACE_VARIANT), italic=True),
            title_text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
            animation=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            title_position_percentage_offset=0.1,
            radar_shape=fch.RadarShape.CIRCLE if self.data.get('radar_data', {}).get('make_chart_round', False) else fch.RadarShape.POLYGON,
            interactive=True
        )    

        # Add our data sets to the chart
        for idx, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', [])):
            color = ds.get('color', "primary")
            entries: list = ds.get('entries', [])
            visible: bool = ds.get('visible', True)

            if not visible:     # Skip non-visible ones
                continue

            chart.data_sets.append(
                fch.RadarDataSet(
                    fill_color=ft.Colors.with_opacity(0.2, color) if color != "transparent" else ft.Colors.TRANSPARENT, # Protect weird transparent bugs
                    border_color=color,
                    entry_radius=4,
                    entries=[fch.RadarDataSetEntry(value) for value in entries],
                )
            )

        # Load our keys above the chart
        keys = ft.Row([], alignment=ft.MainAxisAlignment.CENTER, wrap=True)
        for idx, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', [])):
            
            if idx == 0:        # Skip first one
                continue

            if ds.get('visible', True) == False:        #  Skip non-visible ones
                continue

            key = ft.Container(
                ft.Row([
                    ft.Container(
                        height=30, width=80, 
                        border=ft.Border.all(2, ds.get('color', ft.Colors.PRIMARY)), 
                        bgcolor=ft.Colors.with_opacity(0.2, ds.get('color', ft.Colors.PRIMARY))
                    ),
                    ft.Text(ds.get('title', "Data Set"), style=ft.TextStyle(weight=ft.FontWeight.BOLD))
                ], tight=True, spacing=4),
                #bgcolor=ft.Colors.SURFACE_CONTAINER, 
                border_radius=ft.BorderRadius.all(4), padding=ft.Padding.all(6),
                margin=ft.Margin.only(left=10),
            )
            keys.controls.append(key)

        
        
        if not self.data.get('show_info', True):

            self.body_container.content = ft.Column([
                ft.Container(height=1),
                ft.Row([ft.Container(keys, expand=True)]),
                ft.Row(
                    [
                        chart, 
                        ft.IconButton(
                            ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
                            on_click=self._toggle_show_info, 
                            mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                        )
                    ], expand=True, spacing=0
                )
            ], expand=True)
            return  # Don't load the info column if we're not showing it

        # Renames a node title on the chart
        async def _update_node_title(e):
            self.data['radar_data']['nodes'][e.control.data] = e.control.value
            await self.save_dict()
            chart.titles[e.control.data].text = e.control.value
            chart.update()

        # Deletes a node/title and the corresponding data for it in each data set
        async def _delete_node_title(e):

            async def _delete_node_title_confirm(_):
                del self.data['radar_data']['nodes'][e.control.data]
                for ds in self.data.get('radar_data', {}).get('data_sets', []):
                    del ds['entries'][e.control.data]
                await self.save_dict()
                self.reload_widget()
                self.p.pop_dialog()

            node_title = self.data['radar_data']['nodes'][e.control.data]

            dlg = ft.AlertDialog(
                title=f"Are you sure you want to delete {node_title}?",
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.PRIMARY)),
                    ft.TextButton("Delete", on_click=_delete_node_title_confirm, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                ]
            )
            self.p.show_dialog(dlg)

        # Adds a new title to the end of our titles list, and a default value for each dataset
        async def _add_node_title(e):
            self.data['radar_data']['nodes'].append(f"Node {len(self.data['radar_data']['nodes']) + 1}")
            default_value = int(self.data.get('radar_data', {}).get('max_value', 20) / 2)
            if default_value < self.data.get('radar_data', {}).get('min_value', 0):
                default_value = int(self.data.get('radar_data', {}).get('min_value', 0))
            for ds in self.data.get('radar_data', {}).get('data_sets', []):
                ds['entries'].append(default_value)   
            await self.save_dict()
            self.reload_widget()

        # Toggles the chart either polygon or circle shaped
        async def _toggle_shape(e):
            self.data['radar_data']['make_chart_round'] = e.control.value
            if e.control.value:
                chart.radar_shape = fch.RadarShape.CIRCLE
            else:
                chart.radar_shape = fch.RadarShape.POLYGON
               
            await self.save_dict()
            chart.update()

        # Adding a new dataset with default values in each node
        async def _add_data_set(e):
            median_value = int(self.data.get('radar_data', {}).get('max_value', 20) / 2)
            if median_value < self.data.get('radar_data', {}).get('min_value', 0):
                median_value = int(self.data.get('radar_data', {}).get('min_value', 0))
            self.data['radar_data']['data_sets'].append({
                'color': "primary",
                'entries': [median_value for _ in self.data['radar_data']['nodes']],   # Default entries for each title/node
                'visible': True,
                'title': f"Data Set {len(self.data['radar_data']['data_sets'])}",
                'expanded': False
            })
            await self.save_dict()
            self.reload_widget()

        # Delete a dataset and all its info
        async def _delete_data_set(e):

            async def _delete_data_set_confirm(_):
                idx = e.control.data
                del self.data['radar_data']['data_sets'][idx]
                await self.save_dict()
                self.reload_widget()
                self.p.pop_dialog()

            dataset_title = self.data['radar_data']['data_sets'][e.control.data]['title']

            dlg = ft.AlertDialog(
                title=f"Are you sure you want to delete {dataset_title}?",
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.p.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.PRIMARY)),
                    ft.TextButton("Delete", on_click=_delete_data_set_confirm, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                ]
            )
            self.p.show_dialog(dlg)

        # Toggle whether a dataset is visible on the chart
        async def _toggle_dataset_visibility(e):
            idx = e.control.data
            ds = self.data['radar_data']['data_sets'][idx]
            ds['visible'] = not ds.get('visible', True)
            await self.save_dict()
            self.reload_widget()

        # Change datasets color on the chart
        async def _change_dataset_color(e):
            idx = e.control.data
            color = str(e.control.content)
            self.data['radar_data']['data_sets'][idx]['color'] = color
            await self.save_dict()
            self.reload_widget()

        # Go through and add our titles/nodes to the chart
        titles = []
        for idx, title in enumerate(self.data.get('radar_data', {}).get('nodes', [])):
            titles.append(
                ft.Container(
                    TextField(
                        value=title, 
                        dense=True, data=idx, expand=True,
                        on_blur=_update_node_title,
                        suffix_icon=ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                            mouse_cursor="click", data=idx,
                            on_click=_delete_node_title
                        ) if idx >= 3 else None   # Minimum 3 nodes
                    ),
                    margin=ft.Margin.only(bottom=10, right=11), expand=True
                )
                
            )      

        # Go through and add our Data Sets to the info column on the side
        data_sets = [
            ft.Row([
                ft.Text(f"\tDatasets", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                ft.IconButton(
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    self.data.get('color', ft.Colors.PRIMARY),
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_click=_add_data_set,
                ),
            ], spacing=0)
        ] 

        for idx, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', [])):
            if idx == 0:    # Skip first one
                continue
        
            color = ds.get('color', "primary")
            entries: list = ds.get('entries', [])
            visible: bool = ds.get('visible', True)
            title: str = ds.get('title', "Data Set")
            expanded: bool = ds.get('expanded', False)
            data_sets.append(
                DataSet(
                    title,
                    color,
                    entries,
                    visible,
                    idx,
                    expanded,
                    self.data.get('radar_data', {}).get('min_value', 0),
                    self.data.get('radar_data', {}).get('max_value', 20)
                )
            )

        

        async def _update_min_max_value(e):
            new_value = int(e.control.value)
            key = e.control.data
            if key == "min_value" and new_value == self.data['radar_data'].get('min_value', 0):
                return
            if key == "max_value" and new_value == self.data['radar_data'].get('max_value', 20):
                return
            if key == "min_value" and new_value >= self.data['radar_data'].get('max_value', 20):
                e.control.error = "Min value must be less than max value"
                e.control.value = str(self.data['radar_data'].get('min_value', 0))
                await e.control.focus()
                e.control.update()
                return
            if key == "max_value" and new_value <= self.data['radar_data'].get('min_value', 0):
                e.control.error = "Max value must be greater than min value"
                e.control.value = str(self.data['radar_data'].get('max_value', 20))
                await e.control.focus()
                e.control.update()
                return
            self.data['radar_data'][key] = new_value

            for idx, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', [])):
                if idx == 0:    # Set first one's values to the new min/max so it always fills the whole chart and shows the new scale
                    ds['entries'][0] = self.data['radar_data'].get('min_value', 0)
                    ds['entries'][1] = self.data['radar_data'].get('max_value', 20)
                    #continue
                for i in range(len(ds.get('entries', []))):
                    if ds['entries'][i] < self.data['radar_data'].get('min_value', 0):
                        ds['entries'][i] = self.data['radar_data'].get('min_value', 0)
                    elif ds['entries'][i] > self.data['radar_data'].get('max_value', 20):
                        ds['entries'][i] = self.data['radar_data'].get('max_value', 20)
            await self.save_dict()
            self.reload_widget()
           


        min_value_tf = TextField(
            value=str(self.data.get('radar_data', {}).get('min_value', 0)),
            label="Min Value", dense=True, expand=True,
            on_blur=_update_min_max_value,
            input_filter=ft.NumbersOnlyInputFilter(),
            tooltip="Minimum value in the center of the chart. Must be less than max value. If values in data sets are below this, they will be set to this value. ",
            data="min_value"
        )
        max_value_tf = TextField(
            value=str(self.data.get('radar_data', {}).get('max_value', 20)),
            label="Max Value", dense=True, expand=True,
            on_blur=_update_min_max_value,
            input_filter=ft.NumbersOnlyInputFilter(),
            tooltip="Maximum value at the outer edge of the chart. Must be greater than min value. If values in data sets are above this, they will be set to this value.",
            data="max_value"
        )

        async def _update_tick_count(e):
            change_function = e.control.data

            if change_function == "add":
                self.data['radar_data']['tick_count'] = self.data['radar_data'].get('tick_count', 2) + 1
            elif change_function == "subtract" and self.data['radar_data'].get('tick_count', 2) > 1:
                self.data['radar_data']['tick_count'] = self.data['radar_data'].get('tick_count', 2) - 1

            chart.tick_count = self.data['radar_data'].get('tick_count', 2)
            await self.save_dict()
            chart.update()

        async def _update_show_tick_labels(e):
            self.data['radar_data']['show_tick_labels'] = not self.data['radar_data'].get('show_tick_labels', False)
            chart.ticks_text_style = ft.TextStyle(size=16, color=self.data.get('color', ft.Colors.ON_SURFACE_VARIANT) if self.data['radar_data'].get('show_tick_labels', False) else ft.Colors.TRANSPARENT, italic=True)
            await self.save_dict()
            chart.update()

        async def _toggle_rotate_node_titles(e):
            self.data['radar_data']['rotate_node_titles'] = not self.data['radar_data'].get('rotate_node_titles', False)
            for title in chart.titles:
                title.angle = None if self.data['radar_data'].get('rotate_node_titles', False) else 360
            await self.save_dict()
            chart.update()

        info_column = ft.Column(
            data_sets + [
                ft.Divider(),
                
                
                
                ft.Row([
                    ft.Text(f"\tNodes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        self.data.get('color', ft.Colors.PRIMARY),
                        on_click=_add_node_title,
                        mouse_cursor=ft.MouseCursor.CLICK,
                    ),
                    
                    
                ], spacing=0),
                
            ] + titles + [
                ft.Divider(),
                ft.Container(height=10),
                ft.Text(f"\tAppearence", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                ft.Container(height=10),
                ft.Row([min_value_tf, max_value_tf]),
                ft.Row([
                    ft.Text(
                        "\tInterval Count", style=ft.TextStyle(weight=ft.FontWeight.BOLD), #color=self.data.get('color', None),
                        tooltip="Increase or Decrease the number of lines between the center and outer edge of the chart"
                    ),
                    
                    ft.IconButton(ft.Icons.ADD_OUTLINED, self.data.get('color', ft.Colors.PRIMARY), mouse_cursor=ft.MouseCursor.CLICK, on_click=_update_tick_count, data="add"),
                    ft.IconButton(ft.Icons.REMOVE_OUTLINED, ft.Colors.ERROR, mouse_cursor=ft.MouseCursor.CLICK, on_click=_update_tick_count, data="subtract"),
                    
                ], spacing=0),
                
                
                ft.Switch(
                    True, "\tMake Chart Round", value=self.data.get('radar_data', {}).get('make_chart_round', False),
                    on_change=_toggle_shape, mouse_cursor=ft.MouseCursor.CLICK
                ),
                ft.Switch(
                    True, "\tShow Interval Labels", value=self.data.get('radar_data', {}).get('show_tick_labels', False),
                    on_change=_update_show_tick_labels, mouse_cursor=ft.MouseCursor.CLICK, 
                ),
                ft.Switch(
                    True, "\tRotate Chart Nodes", value=self.data.get('radar_data', {}).get('rotate_node_titles', False),
                    on_change=_toggle_rotate_node_titles, mouse_cursor=ft.MouseCursor.CLICK,
                ),
            ],
            
            expand=True, scroll="auto", spacing=0
        )



        chart_info = ft.Container(
            expand=1,
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8,),
            shadow=ft.BoxShadow(0, 1),
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            content=ft.Column(
                [
                    ft.Row([
                        ft.Text(
                            f"\tChart Info", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD, 
                            color=self.data.get('color', None), expand=True
                        ),
                        ft.IconButton(
                            ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=self._toggle_show_info, 
                            mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                        ),
                    ]),
                    ft.Divider(),
                    info_column
                ], expand=True, scroll="none", spacing=0),
        )

        

        self.body_container.content = ft.Row(
            [
                ft.Column([
                    ft.Container(height=1),
                    ft.Row([ft.Container(keys, expand=True)]),
                    chart,
                ], expand=3),
                chart_info
            ], expand=True, spacing=0
        )
       

        

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: BAR CHART FEATURES --


        # Rebuild out tab to reflect any changes
        self.reload_tab()

        if self.data.get('type', "") == "bar":
            self._bar_chart_view()
        else:
            self._radar_chart_view()
        
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        