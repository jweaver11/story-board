# Charts for a story

''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from models.app import app
from utils.safe_string_checker import return_safe_name
from styles.text_fields import TextField
import flet_charts as fch
from styles.colors import colors
import math
from styles.snack_bar import SnackBar
    

class Chart(Widget):

    # Constructor
    def __init__(
        self, 
        title: str, 
        directory_path: str, 
        story: Story, 
        data: dict = {}, 
        is_new: bool = False,
        type: str = "bar"           # Type of chart we are (either bar or radar)
    ):

        # Initialize from our parent class 'Widget'. 
        super().__init__(
            title = title,                      
            directory_path = directory_path,    
            story = story,                     
            data = data,
            is_new = is_new
        )
        

        # If we're new, give default values for our data 
        if self.is_new == True:
            self.data.update({
                # Widget data
                'tag': "chart",             # Tag to identify what type of object this is
                'color': app.settings.data.get('widget_defauls', {}).get('chart', {}).get('color', "primary"),
                'chart_type': type,             # How our chart is being displayed (bar or radar)

                'show_sidebar': True,   # Whether to show the info column on the side of our charts or not.

                'bar_data': {
                    'left_axis_title': "Left Axis",
                    'bottom_axis_title': "Bottom Axis",
                    'show_labels': app.settings.data.get('widget_defaults', {}).get('show_labels', True),           # Whether to show labels on our axes or not
                    'rod_shape': app.settings.data.get('widget_defaults', {}).get('rod_shape', "rounded"),          # The shape of our bars/rods. Either "rounded" or "square"
                    'rod_width': app.settings.data.get('widget_defaults', {}).get('rod_width', 30),         # The width of our bars/rods. Only applies to vertical bar charts, not horizontal ones
                    'stack_rods': app.settings.data.get('widget_defaults', {}).get('stack_rods', False),      # If False, rods display on top of each other, not side by side
                    'show_horizontal_grid_lines': app.settings.data.get('widget_defaults', {}).get('show_horizontal_grid_lines', True),
                    'show_vertical_grid_lines': app.settings.data.get('widget_defaults', {}).get('show_vertical_grid_lines', False),
                    'max_y': 20,        # The max y value of our chart, which is the value that will fill the whole chart. Should be higher than any value in our bars
                    'rod_spacing': app.settings.data.get('widget_defaults', {}).get('rod_spacing', 10),   # The spacing between rods in the chart
                    'groups': [
                        #{
                            #'name': "Group 1", 
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
                    'make_chart_round': app.settings.data.get('widget_defaults', {}).get('make_chart_round', True),   # Whether to show our radar chart as a circle or polygon
                    'min_value': 0,     # The minimum value for our radar chart, which will be the center point of the chart
                    'max_value': 20,    # The maximum value for our radar chart, which will be the outer edge of the chart
                    'tick_count': app.settings.data.get('widget_defaults', {}).get('tick_count', 2),    # Number of tick lines between the center and outer edge of the chart
                    'show_tick_labels': app.settings.data.get('widget_defaults', {}).get('show_tick_labels', False),      # Whether to show the labels for each tick line or not
                    'rotate_node_titles': app.settings.data.get('widget_defaults', {}).get('rotate_node_titles', True),    # Whether to keep our titles flat and not rotate them with the chart or not
                    'data_sets': [      # The data sets that make up the radar chart
                        #{               # Starts maximized invisible so they can see other data_sets at all times
                            #'title': "Data Set 1",
                            #'color': "transparent",
                            #'entries': [0, 20, 20, 20, 20],   # The values for each title/axis of the radar chart. First value is min, second is max
                        #},
                        #{},...
                        
                    ]     
                }

            },
        )
        
        


    # Returns our widgets view for bar charts
    def bar_chart_view(self):
        ''' Builds out the body of our bar chart widget '''

        # Updates the indices for the controls for groups and rods in the chart and sidebar
        def update_indices():
            update_group_indices()
            update_rod_indices()

        # Update each label in the chart and expansion tile delete button in the sidebar
        def update_group_indices():
            for group_idx, label in enumerate(self.data.get('bar_data', {}).get('groups', [])):
                chart.bottom_axis.labels[group_idx].value = group_idx                   # Value of label on chart 
                chart.bottom_axis.labels[group_idx].label.data = group_idx              # Data of tf for changing
                sidebar_bar_group_column.controls[group_idx].trailing.data = group_idx  # Delete button for that group in sidebar

        # Updates the indices for each rod within each group in the sidebar and chart
        def update_rod_indices():
            for group_idx, exp_tile in enumerate(sidebar_bar_group_column.controls):
                rod_idx = 0     # Set our rod index to only incriment when we find a rod control and ignore other controls
                for ctrl in exp_tile.controls:
                    if isinstance(ctrl, ft.Row) and len(ctrl.controls) > 2:
                        for item in ctrl.controls[0].items:     # Color picker popup items
                            item.data = (group_idx, rod_idx)
                        ctrl.controls[2].data = (group_idx, rod_idx)    # Slider
                        ctrl.controls[4].data = (group_idx, rod_idx)    # Delete button
                        rod_idx += 1

        # Create a new group with default data in data, chart, and sidebar
        async def create_group(e: ft.Event):

            # Give med value for rod
            median_value = int(self.data.get('bar_data', {}).get('max_y', 20) / 2)
            if median_value < self.data.get('radar_data', {}).get('min_value', 0):
                median_value = int(self.data.get('radar_data', {}).get('min_value', 0))

            # Add rod to data and update
            self.data['bar_data']['groups'].append({
                'name': f"Group {len(self.data.get('bar_data', {}).get('groups', [])) + 1}",
                'expanded': False,
                'rods': [
                    {
                        'to_y': median_value, 
                        'color': "primary"
                    }
                ]
            })
            self.update_data(**{'bar_data': self.data.get('bar_data', {})})

            # Add the new group to the sidebar, chart, and bottom chart axis labels. 
            sidebar_bar_group_column.controls.append(create_sidebar_group(len(self.data.get('bar_data', {}).get('groups', [])) - 1, self.data.get('bar_data', {}).get('groups', [])[-1], is_new=True))
            chart.groups.append(create_chart_bar_group(len(self.data.get('bar_data', {}).get('groups', [])) - 1, self.data.get('bar_data', {}).get('groups', [])[-1]))
            chart.bottom_axis.labels.append(create_bar_group_label(len(self.data.get('bar_data', {}).get('groups', [])) - 1, self.data.get('bar_data', {}).get('groups', [])[-1].get('name', f"Group {len(self.data.get('bar_data', {}).get('groups', []))}")))
            self.update()
            update_indices()      # Update indices 
            
        # Deletes a group from data, chart, and sidebar
        async def delete_group(e: ft.Event):
            idx = e.control.data    
            # Delete from data
            self.data.get('bar_data', {}).get('groups', []).pop(idx)
            self.update_data(**{'bar_data': self.data.get('bar_data', {})})

            # Delete from UI
            chart.groups.pop(idx)
            chart.bottom_axis.labels.pop(idx)   # Remove the corresponding bottom axis label from the chart
            sidebar_bar_group_column.controls.pop(idx)
            self.update()
            update_indices()   # Update indices after deleting a group

        # Creates a rod for a specific group in the data, chart, and sidebar
        async def create_rod(e: ft.Event):
            # Grab idx and data
            group_idx = e.control.data
            group_data = self.data.get('bar_data', {}).get('groups', [])[group_idx]

            # Median value for new rod
            median_value = int(self.data.get('bar_data', {}).get('max_y', 20) / 2)
            if median_value < self.data.get('radar_data', {}).get('min_value', 0):
                median_value = int(self.data.get('radar_data', {}).get('min_value', 0))

            # Add to data and update the data
            group_data['rods'].append({
                'to_y': median_value, 
                'color': "primary"
            })
            self.data['bar_data']['groups'][group_idx] = group_data
            self.update_data(**{'bar_data': self.data.get('bar_data', {})})

            # Grab that rod data and its new index
            rod_data = group_data['rods'][-1]
            new_rod_idx = len(self.data.get('bar_data', {}).get('groups', [])[group_idx]['rods']) - 1

            # Add the rod to the group on the char
            chart.groups[group_idx].rods.append(
                fch.BarChartRod(
                    from_y=0, to_y=rod_data.get('to_y', 0), 
                    width=self.data.get('bar_data', {}).get('rod_width', 30),
                    border_radius=None if self.data.get('bar_data', {}).get('rod_shape', "rounded") == "rounded" else ft.BorderRadius.only(top_left=2, top_right=2),
                    color=rod_data.get('color', self.data.get('color', ft.Colors.PRIMARY)),
                ) 
            )
            # Add it to the sidebar as well
            sidebar_bar_group_column.controls[group_idx].controls.append(create_sidebar_rod(group_idx, new_rod_idx, rod_data))
            self.update()
            update_indices()

        # Updates the value of our rod on the chart in real-time as the slider is moved, without adjusting data
        async def update_rod_value(e: ft.Event):
            group_idx, rod_idx = e.control.data
            new_value = int(e.control.value)

            # Update the chart visually in real-time
            chart.groups[group_idx].rods[rod_idx].to_y = new_value
            chart.update()

        # Updates the value of our rod in our data once at the end of a slider call
        async def update_rod_data(e: ft.Event):
            group_idx, rod_idx = e.control.data
            new_value = int(e.control.value)

            # Update our data 
            self.data['bar_data']['groups'][group_idx]['rods'][rod_idx]['to_y'] = new_value
            self.update_data(**{'bar_data': self.data.get('bar_data', {})})

        # Deletes a rod from the chart, data, and sidebar
        async def delete_rod(e: ft.Event):
            group_idx, rod_idx = e.control.data

            self.data['bar_data']['groups'][group_idx]['rods'].pop(rod_idx)
            self.update_data(**{'bar_data': self.data.get('bar_data', {})})
            chart.groups[group_idx].rods.pop(rod_idx)
            sidebar_bar_group_column.controls[group_idx].controls.pop(rod_idx+2)
            self.update()
            update_indices()

        # Changes color of a rod in data, chart, and sidebar
        async def change_rod_color(e: ft.Event):
            # Grab indices and new color
            group_idx, rod_idx = e.control.data
            new_color = e.control.content

            # Update data
            self.data['bar_data']['groups'][group_idx]['rods'][rod_idx]['color'] = new_color
            self.update_data(**{'bar_data': self.data.get('bar_data', {})})

            # Update charts rod color and sidebar
            chart.groups[group_idx].rods[rod_idx].color = new_color
            e.control.parent.icon_color = new_color
            e.control.parent.parent.controls[2].active_color = new_color
            self.update()

        # Creates the rod controls for the sidebar inside a group expansion tile
        def create_sidebar_rod(group_idx: int, rod_idx: int, rod: dict):
            # Set min and max
            min_value=0
            max_value=self.data.get('bar_data', {}).get('max_y', 20)

            return ft.Row([
                ft.PopupMenuButton(     # Change rod color button
                    icon=ft.Icons.COLOR_LENS_OUTLINED, 
                    icon_color=rod.get('color', ft.Colors.PRIMARY),
                    menu_padding=ft.Padding.all(0),
                    tooltip="Change Color",
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                    items=[
                        ft.PopupMenuItem(
                            color.capitalize(), label_text_style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD),
                            mouse_cursor=ft.MouseCursor.CLICK,
                            on_click=change_rod_color, data=(group_idx, rod_idx)
                        ) for color in colors
                    ]
                ),
                ft.Text(str(min_value), weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),  # Display min value left of slider
                ft.Slider(      # Slider to adjust rod value
                    value=rod.get('to_y', 0), 
                    min=min_value,
                    max=max_value, 
                    active_color=rod.get('color', self.data.get('color', ft.Colors.PRIMARY)),
                    #inactive_color=ft.Colors.ON_SURFACE_VARIANT,
                    label="{value}", 
                    on_change=update_rod_value,     # Adjust UI in real time updates
                    on_change_end=update_rod_data,  # Adjust data after drag complete
                    data=(group_idx, rod_idx),
                    expand=True,
                    divisions=max_value - min_value if max_value > min_value else None,
                ),
                ft.Text(str(max_value), weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),  # Display max value right of slider
                ft.IconButton(      # Delete rod button
                    ft.Icons.DELETE_OUTLINE_OUTLINED, ft.Colors.ERROR, 
                    on_click=delete_rod, data=(group_idx, rod_idx), mouse_cursor=ft.MouseCursor.CLICK
                )    
            ], spacing=0)

        # Creates an expansion tile for the sidebar for the passed in bar group idx and data
        def create_sidebar_group(group_idx: int, group_data: dict, is_new: bool=False) -> ft.ExpansionTile:
            # Set data from groups
            title=group_data.get('name', "Group")
            rods=[rod for rod in group_data.get('rods', [])]

            # Build expansion_tile functionality
            return ft.ExpansionTile(
                ft.Text(title, weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),   # Group title
                trailing=ft.IconButton(     # Delete group button
                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                    mouse_cursor=ft.MouseCursor.CLICK, data=group_idx, on_click=delete_group
                ),
                dense=True, tile_padding=ft.Padding.only(left=10, right=0), controls_padding=ft.Padding.only(right=10, left=10),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, collapsed_bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                data=group_idx, shape=ft.RoundedRectangleBorder(radius=4), collapsed_shape=ft.RoundedRectangleBorder(radius=4),
                expanded=is_new,
                controls=[
                    ft.Divider(2, 2),   
                    ft.Row([
                        ft.Text("Rods", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, weight=ft.FontWeight.BOLD, size=14),   # Label of Rods
                        ft.IconButton(      # Add new rod button
                            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                            ft.Colors.PRIMARY,
                            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.BOLD)), 
                            on_click=create_rod, 
                            data=group_idx
                        )
                    ], spacing=0),
                ] + [create_sidebar_rod(group_idx, rod_idx, rod) for rod_idx, rod in enumerate(rods)],  # Rod controls
            )
                
        # Sets new title for the chart axis based on the axis type (left, bottom, top, right)
        async def set_chart_axis_title(e: ft.Event):
            new_title = e.control.value
            axis_type = e.control.data + "_axis_title"
            self.update_data(**{'bar_data': {axis_type: new_title}})

        # Sets the maximum value for the Y-axis of the chart
        async def set_max_y_value(e: ft.Event):
            
            # Handle empty values
            if e.control.value == "" or e.control.value is None:
                e.control.value = str(chart.max_y)
                e.control.update()
                return
            
            # Update data
            new_value = int(e.control.value)
            self.update_data(**{'bar_data': {'max_y': new_value}})

            # Update chart
            chart.max_y = new_value
            chart.update()

        # Sets whether to show labels on the chart axes
        async def set_show_labels(e: ft.Event):
            # Update data
            new_show_labels_value = e.control.value
            self.update_data(**{'bar_data': {'show_labels': new_show_labels_value}})
            chart.left_axis.show_labels = new_show_labels_value
            chart.bottom_axis.show_labels = new_show_labels_value
            chart.update()
        
        # Sets the width of the rods in the chart to update real time
        async def set_rod_width_value(e: ft.Event):
            # Update data
            new_width = int(e.control.value)
            # Update the width of each rod in the chart
            for group in chart.groups:
                for rod in group.rods:
                    rod.width = new_width
            chart.update()

        # Save in data after done adjusting rod width
        async def set_rod_width_data(e: ft.Event):
            new_width = int(e.control.value)
            self.update_data(**{'bar_data': {'rod_width': new_width}})

        async def set_rod_spacing_value(e: ft.Event):
            # Update data
            new_spacing = int(e.control.value)
            self.update_data(**{'bar_data': {'rod_spacing': new_spacing}})
            # Update the spacing of each rod in the chart
            for group in chart.groups:
                group.spacing = new_spacing
            chart.update()

        # Save in data after done adjusting rod spacing
        async def set_rod_spacing_data(e: ft.Event):
            new_spacing = int(e.control.value)
            self.update_data(**{'bar_data': {'rod_spacing': new_spacing}})

        # Sets whether the rods in the chart should be stacked
        async def set_stacked_rods(e: ft.Event):
            # Update data
            stack_rods = e.control.value
            self.update_data(**{'bar_data': {'stack_rods': stack_rods}})
            # Update the stacking of each group in the chart
            for group in chart.groups:
                group.group_vertically = e.control.value
            chart.update()

        # Set the rod shape to either rounded or square 
        async def set_rod_shape(e: ft.Event):
            # Update data
            new_shape = "rounded" if e.control.value else "square"
            self.update_data(**{'bar_data': {'rod_shape': new_shape}})
            # Update the Chart UI
            for group in chart.groups:
                for rod in group.rods:
                    rod.border_radius = None if new_shape == "rounded" else ft.BorderRadius.only(top_left=2, top_right=2)
            chart.update()

        # Set whether to show horiz or vert grid lines depening on the button
        async def set_grid_lines(e: ft.Event):
            # Set value and which type of grid lines
            grid_line_type = e.control.data
            show_grid_lines = e.control.value
            # Update data and chart UI
            if grid_line_type == "horizontal":
                self.update_data(**{'bar_data': {'show_horizontal_grid_lines': show_grid_lines}})
                chart.horizontal_grid_lines = fch.ChartGridLines() if show_grid_lines else None
            else:
                self.update_data(**{'bar_data': {'show_vertical_grid_lines': show_grid_lines}})
                chart.vertical_grid_lines = fch.ChartGridLines() if show_grid_lines else None
            chart.update()

        # Returns the small label control under each bar group on the chart
        def create_bar_group_label(idx: int, name: str) -> fch.ChartAxisLabel:
            # Updates the label in data and in the sidebar
            async def set_bar_group_label(e: ft.Event):
                idx = e.control.data
                new_label = e.control.value
                self.data['bar_data']['groups'][idx]['name'] = new_label
                self.update_data(**{'bar_data': self.data.get('bar_data', {})})
                sidebar_bar_group_column.controls[idx].title.value = new_label
                sidebar_bar_group_column.controls[idx].update()
            # Return the chart axis label with the text field for editing the label
            return fch.ChartAxisLabel(
                idx,        # Requires value of index
                label=ft.TextField(     # Tf for editing the label
                    value=name, dense=True, width=120, clip_behavior=ft.ClipBehavior.NONE,
                    data=idx, on_blur=set_bar_group_label, border=ft.InputBorder.NONE,
                    text_align=ft.TextAlign.CENTER, text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500)
                )
                
            )

        # Creates a group control for the chart using index and data
        def create_chart_bar_group(idx: int, group_data: dict) -> fch.BarChartGroup:
            return fch.BarChartGroup(
                idx,        # Needs for alignment
                spacing=self.data.get('bar_data', {}).get('rod_spacing', 4), 
                group_vertically=self.data.get('bar_data', {}).get('stack_rods', False),
                rods=[
                    fch.BarChartRod(
                        from_y=0, to_y=rod.get('to_y', 0), 
                        width=self.data.get('bar_data', {}).get('rod_width', 30),
                        border_radius=None if self.data.get('bar_data', {}).get('rod_shape', "rounded") == "rounded" else ft.BorderRadius.only(top_left=2, top_right=2),
                        color=rod.get('color', self.data.get('color', ft.Colors.PRIMARY)),
                    ) for rod in group_data.get('rods', [])
                ]
            )

        # Our bar chart
        chart = fch.BarChart(
            groups=[create_chart_bar_group(idx, group) for idx, group in enumerate(self.data.get('bar_data', {}).get('groups', []))],
            #on_event=lambda e: print(e),

            # User customizable options
            max_y=self.data.get('bar_data', {}).get('max_y', 20),
            left_axis=fch.ChartAxis(
                ft.TextField(
                    value=self.data.get('bar_data', {}).get('left_axis_title', ""), 
                    data="left", on_blur=set_chart_axis_title, border=ft.InputBorder.NONE,
                    text_align=ft.TextAlign.CENTER, text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)
                ), 
                title_size=40, label_size=30,
                show_labels=self.data.get('bar_data', {}).get('show_labels', False),
            ),
            bottom_axis=fch.ChartAxis(
                ft.TextField(
                    value=self.data.get('bar_data', {}).get('bottom_axis_title', ""), 
                    data="bottom", on_blur=set_chart_axis_title, border=ft.InputBorder.NONE,
                    text_align=ft.TextAlign.CENTER, text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)
                ),
                title_size=40, label_size=30,
                show_labels=self.data.get('bar_data', {}).get('show_labels', False),
                labels=[create_bar_group_label(idx, group.get('name', f"Group {idx + 1}")) for idx, group in enumerate(self.data.get('bar_data', {}).get('groups', []))]
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
       
        # Column for sidebar groups
        sidebar_bar_group_column = ft.Column(
            [create_sidebar_group(idx, group) for idx, group in enumerate(self.data.get('bar_data', {}).get('groups', []))],
            expand=True, scroll="auto", #spacing=0,
        )

        # Insert our settings into the sidebar header after our title
        self.sidebar_header.controls.insert(
            1,
            ft.MenuBar(
                [
                    ft.SubmenuButton(
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY),
                        [
                            # Toggle stacked rods
                            ft.Switch(
                                value=self.data.get('bar_data', {}).get('stack_rods', False), 
                                label="\tStack Rods", on_change=set_stacked_rods
                            ),
                            # Toggle rounded rods
                            ft.Switch(
                                value=True if self.data.get('bar_data', {}).get('rod_shape', "rounded") == "rounded" else False, 
                                label="\tRounded Rods", on_change=set_rod_shape
                            ),
                            # Toggle axis labels
                            ft.Switch(
                                value=self.data.get('bar_data', {}).get('show_labels', False), 
                                label="\tShow Axis Labels", on_change=set_show_labels
                            ),
                            # Toggle horizontal grid lines
                            ft.Switch(
                                value=self.data.get('bar_data', {}).get('show_horizontal_grid_lines', False), 
                                label="\tShow Horizontal Grid Lines", on_change=set_grid_lines, data="horizontal"
                            ),
                            # Toggle vertical grid lines
                            ft.Switch(
                                value=self.data.get('bar_data', {}).get('show_vertical_grid_lines', False), 
                                label="\tShow Vertical Grid Lines", on_change=set_grid_lines, data="vertical"
                            ),
                            # Adjust max y value of the chart
                            ft.TextField(
                                label="Max Y Value", value=str(self.data.get('bar_data', {}).get('max_y', 20)), 
                                input_filter=ft.NumbersOnlyInputFilter(), data="max", on_blur=set_max_y_value,
                                margin=ft.Margin.only(top=6, left=10, right=10), border_color=ft.Colors.OUTLINE_VARIANT,
                                border_radius=4, dense=True
                            ),
                            # Adjust Rod width
                            ft.Row([
                                ft.Text("\t\tRod Width", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                                ft.Slider(
                                    value=self.data.get('bar_data', {}).get('rod_width', 30), min=10, max=100, 
                                    label="{value}", expand=True, on_change=set_rod_width_value, on_change_end=set_rod_width_data
                                ),
                            ], spacing=0),
                            # Adjust rod spacing
                            ft.Row([
                                ft.Text("\t\tRod Spacing", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                                ft.Slider(
                                    value=self.data.get('bar_data', {}).get('rod_spacing', 30), min=0, max=20, 
                                    label="{value}", expand=True, on_change=set_rod_spacing_value, on_change_end=set_rod_spacing_data
                                ),
                            ], spacing=0),
                            
                        ],
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                        style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                        tooltip="Adjust the settings for this bar chart."
                    ),
                ],
                style=ft.MenuStyle(
                    bgcolor="transparent", shadow_color="transparent",
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
            )
        )

        # Add a label and add groups button in the sidebar
        self.sidebar_body.controls.extend([
            ft.Row([
                ft.Text(f"Groups", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                ft.IconButton(      # Create group button
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    ft.Colors.PRIMARY,
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_click=create_group,
                ),
            ], spacing=0),
            sidebar_bar_group_column,

            # Notes stuff
            ft.Divider(),
            self.sidebar_notes_label,
            self.sidebar_notes_column
        ])

        # Set up our main conent
        self.content = ft.Stack([
            ft.Row([
                ft.Container(chart, expand=3, padding=ft.Padding.only(bottom=20, left=20)),
                self.toggle_sidebar_visibility_button, 
                self.sidebar
            ], spacing=0, expand=True, alignment=ft.MainAxisAlignment.END, 
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)
        
    # Returns our widgets view for radar charts
    def radar_chart_view(self):
        ''' Builds out the body of our radar chart widget '''

        

        # Update indices after datasets or nodes are added or deleted
        def update_indices():
            update_data_set_indices()
            update_node_indices()

        # Updates the indices of the datasets and nodes in the sidebar after any changes
        def update_data_set_indices():
            for idx, control in enumerate(sidebar_dataset_column.controls):
                control.trailing.data = idx
                control.leading.data = idx
            for idx, control in enumerate(dataset_keys.controls):
                control.data = idx

        # Updates indices of the nodes in the sidebar after one is deleted
        def update_node_indices():
            for idx, control in enumerate(sidebar_nodes_column.controls):
                control.content.suffix.data = idx
        
        # Updates the entry value on the chart for each drag
        async def update_entry(e: ft.Event):
            dataset_idx, entry_idx = e.control.data
            new_value = int(e.control.value)

            # Update the chart visually in real-time
            chart.data_sets[dataset_idx + 1].entries[entry_idx].value = new_value
            chart.update()

        # Updates entry value in data at end of each drag
        async def update_entry_data(e: ft.Event):
            dataset_idx, entry_idx = e.control.data
            new_value = int(e.control.value)

            # Update our data
            self.data['radar_data']['data_sets'][dataset_idx]['entries'][entry_idx] = new_value
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})

        # Updates the title of a dataset
        async def update_dataset_title(e: ft.Event):
            data_set_idx = e.control.data
            new_title = e.control.value
            print("Updated title with index", data_set_idx)
            # Update the data
            self.data.get('radar_data', {}).get('data_sets', [])[data_set_idx]['title'] = new_title
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})

            sidebar_dataset_column.controls[data_set_idx].title.value = new_title
            sidebar_dataset_column.controls[data_set_idx].update()

        # Creates a dataset control for the radar chart
        def create_data_set_chart_control(data_set_idx: int, data_set_data: dict) -> fch.RadarDataSet:
            color = data_set_data.get('color', "primary")
            entries = data_set_data.get('entries', [])
            
            return fch.RadarDataSet(
                fill_color=ft.Colors.with_opacity(0.2, color) if color != "transparent" else ft.Colors.TRANSPARENT, # Protect weird transparent bugs
                border_color=color,
                entry_radius=4,
                entries=[fch.RadarDataSetEntry(entry) for entry in entries],
            )

        should_rotate_nodes = self.data.get('radar_data', {}).get('rotate_node_titles', False)
        chart = fch.RadarChart(
            data_sets=[
                fch.RadarDataSet(
                    fill_color=ft.Colors.TRANSPARENT, # Protect weird transparent bugs
                    border_color=ft.Colors.TRANSPARENT,
                    entry_radius=0,
                    entries=[   # One invisible min and max value or chart renders weird
                        fch.RadarDataSetEntry(self.data.get('radar_data', {}).get('min_value', 0)),
                    ] + [fch.RadarDataSetEntry(self.data.get('radar_data', {}).get('max_value', 0)) for i, _ in enumerate(self.data.get('radar_data', {}).get('nodes', [])) if i < len(self.data.get('radar_data', {}).get('nodes', [])) - 1],
                ),
            ],
            expand=3,
            #on_event=lambda e: print(e),
            titles=[fch.RadarChartTitle(title, None if should_rotate_nodes else 360) for title in self.data.get('radar_data', {}).get('nodes', [])],
            center_min_value=True,
            tick_count=self.data.get('radar_data', {}).get('tick_count', 2),
            ticks_text_style=ft.TextStyle(
                size=16, color=ft.Colors.TRANSPARENT, italic=True
            ) if not self.data.get('radar_data', {}).get('show_tick_labels', False) else 
                ft.TextStyle(size=16, color=ft.Colors.PRIMARY, italic=True),
            title_text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
            animation=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            title_position_percentage_offset=0.1,
            radar_shape=fch.RadarShape.CIRCLE if self.data.get('radar_data', {}).get('make_chart_round', False) else fch.RadarShape.POLYGON,
            interactive=True
        )    

        # Add our data sets to the chart
        for idx, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', [])):
            chart.data_sets.append(create_data_set_chart_control(idx, ds))

        # Creates a control for our keys above our chart
        def create_data_set_key_control(data_set_idx: int, data_set_data: dict) -> ft.Container:
            return ft.Container(
                ft.Row([
                    ft.Container(
                        height=30, width=80, 
                        border=ft.Border.all(2, data_set_data.get('color', ft.Colors.PRIMARY)), 
                        bgcolor=ft.Colors.with_opacity(0.2, data_set_data.get('color', ft.Colors.PRIMARY))
                    ),
                    #ft.Text(ds.get('title', "Data Set"), style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                    ft.TextField(
                        data_set_data.get('title', "Data Set"), dense=True, data=data_set_idx,
                        border=ft.InputBorder.NONE, text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                        on_blur=update_dataset_title,
                        width=120
                    ),
                ], tight=True, spacing=6),
                border_radius=ft.BorderRadius.all(4), padding=ft.Padding.all(6),
                margin=ft.Margin.only(left=10),
            )

        # Load our keys above the chart
        dataset_keys = ft.Row(
            [create_data_set_key_control(idx, ds) for idx, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', []))], 
            alignment=ft.MainAxisAlignment.CENTER, wrap=True, margin=ft.Margin.only(top=10)
        )

        # Renames a node title on the chart
        async def update_node_title(e: ft.Event):
            # Update data
            self.data['radar_data']['nodes'][e.control.data] = e.control.value
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            # Update node on chart
            chart.titles[e.control.data].text = e.control.value
            chart.update()

        # Deletes a node/title and the corresponding data for it in each data set
        async def delete_node(e: ft.Event):
            node_idx = e.control.data
            
            # Delete the node from data and all values tied to it
            del self.data['radar_data']['nodes'][node_idx]
            for ds in self.data.get('radar_data', {}).get('data_sets', []):
                del ds['entries'][node_idx]
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})

            # Remove that node from the chart's data sets and titles
            for ds in chart.data_sets:
                del ds.entries[node_idx]
            chart.titles.pop(node_idx)

            # Remove the corresponding control from the sidebar nodes column and update
            sidebar_nodes_column.controls.pop(node_idx)
            self.update()
            update_indices()
            

        # Toggles the chart either polygon or circle shaped
        async def toggle_shape(e):
            self.data['radar_data']['make_chart_round'] = e.control.value
            if e.control.value:
                chart.radar_shape = fch.RadarShape.CIRCLE
            else:
                chart.radar_shape = fch.RadarShape.POLYGON
               
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            chart.update()

        # Adding a new dataset with default values in each node
        async def create_data_set(e: ft.Event):
            # Set median value
            median_value = int(self.data.get('radar_data', {}).get('max_value', 20) / 2)
            if median_value < self.data.get('radar_data', {}).get('min_value', 0):
                median_value = int(self.data.get('radar_data', {}).get('min_value', 0))

            # Add to data
            self.data['radar_data']['data_sets'].append({
                'title': f"Data Set {len(self.data['radar_data']['data_sets']) + 1}",
                'color': "primary",
                'entries': [median_value for _ in self.data['radar_data']['nodes']],   # Default entries for each title/node
            })
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})

            # Add dataset to our sidebar column
            sidebar_dataset_column.controls.append(
                create_data_set_sidebar_control(
                    len(self.data['radar_data']['data_sets']) - 1, 
                    self.data['radar_data']['data_sets'][-1], 
                    is_new=True
                )
            )

            # Add control to the chart data
            chart.data_sets.append(
                create_data_set_chart_control(
                    len(self.data['radar_data']['data_sets']) - 1,
                    self.data['radar_data']['data_sets'][-1]
                )
            )

            # Add key to our keys and update
            dataset_keys.controls.append(
                create_data_set_key_control(
                    len(self.data['radar_data']['data_sets']) - 1,
                    self.data['radar_data']['data_sets'][-1]
                )
            )

            self.update()

        # Returns a sidebar control for datasets
        def create_data_set_sidebar_control(data_set_idx: int, data_set_data: dict, is_new: bool=False) -> ft.ExpansionTile:
            min_value = self.data.get('radar_data', {}).get('min_value', 0)
            max_value = self.data.get('radar_data', {}).get('max_value', 20)
            title = data_set_data.get('title', f"Data Set {data_set_idx}")
            color = data_set_data.get('color', "primary")
            entries = data_set_data.get('entries', [])
            idx = data_set_idx
            return ft.ExpansionTile(
                leading=ft.PopupMenuButton(
                    icon=ft.Icons.COLOR_LENS_OUTLINED, 
                    icon_color=color, menu_padding=ft.Padding.all(0),
                    tooltip="Change Color", data=data_set_idx,
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                    items=[
                        ft.PopupMenuItem(
                            color.capitalize(), label_text_style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD),
                            data=idx, on_click=update_dataset_color, mouse_cursor=ft.MouseCursor.CLICK
                        ) for color in colors
                    ]
                ),
                title=ft.Text(title, weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                trailing=ft.IconButton(
                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                    mouse_cursor=ft.MouseCursor.CLICK, data=idx,
                    on_click=delete_data_set
                ),
                dense=True, tile_padding=ft.Padding.only(left=10, right=10), controls_padding=ft.Padding.only(right=20, left=20),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, collapsed_bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                shape=ft.RoundedRectangleBorder(radius=4), collapsed_shape=ft.RoundedRectangleBorder(radius=4),
                expanded=is_new,
                
                controls=[
                    ft.Row([
                        ft.Text(str(min_value), weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                        ft.Slider(
                            value=entry, 
                            min=min_value,
                            max=max_value, 
                            label="{value}", 
                            on_change=update_entry, on_change_end=update_entry_data,
                            data=(idx, i),
                            expand=True,
                            divisions=max_value - min_value if max_value > min_value else None,
                        ),
                        ft.Text(str(max_value), weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE)
                    ], spacing=0) for i, entry in enumerate(entries)
                ],
                data=idx
            )

        # Delete a dataset and all its info
        async def delete_data_set(e: ft.Event):
            # Delete from data
            data_set_idx = e.control.data
            del self.data['radar_data']['data_sets'][data_set_idx]
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            
            # Remove from keys, chart, and sidebar
            dataset_keys.controls.pop(data_set_idx)
            chart.data_sets.pop(data_set_idx + 1)   # Skip first invisible dataset
            sidebar_dataset_column.controls.pop(data_set_idx)
            self.update()
            update_indices()

        # Change data_sets color on the chart
        async def update_dataset_color(e: ft.Event):
            data_set_idx = e.control.parent.data
            new_color = str(e.control.content)
            self.data['radar_data']['data_sets'][data_set_idx]['color'] = new_color
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})

            # Update sidebar icon color for this dataset
            sidebar_dataset_column.controls[data_set_idx].leading.icon_color = new_color
            # Update key color for this dataset
            container = dataset_keys.controls[data_set_idx].content.controls[0]
            container.border = ft.Border.all(2, new_color)
            container.bgcolor = ft.Colors.with_opacity(0.2, new_color)

            # Update the chart's dataset color to reflect the change
            chart.data_sets[data_set_idx + 1].fill_color = ft.Colors.with_opacity(0.2, new_color)  # Skip first invisible dataset
            chart.data_sets[data_set_idx + 1].border_color = new_color
            self.update()

        # Called to create a new node
        async def create_node(e: ft.Event):

            # Set new title and median value
            node_title = f"Node {len(self.data['radar_data']['nodes']) + 1}"
            median_value = int(self.data.get('radar_data', {}).get('max_value', 20) / 2)
            
            # Add this new node to the list of nodes and append the median value to each data set entry
            self.data['radar_data']['nodes'].append(node_title)
            if median_value < self.data.get('radar_data', {}).get('min_value', 0):
                median_value = int(self.data.get('radar_data', {}).get('min_value', 0))
            for ds in self.data.get('radar_data', {}).get('data_sets', []):
                ds['entries'].append(median_value)   

            # Update our data to support this new node
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            sidebar_nodes_column.controls.append(create_sidebar_node(len(self.data['radar_data']['nodes']) - 1, node_title))

            # Add the new entries to the charts
            for ds in chart.data_sets:
                ds.entries.append(fch.RadarDataSetEntry(median_value))

            # Add new title to the chart and update
            should_rotate_nodes = self.data.get('radar_data', {}).get('rotate_node_titles', False)
            chart.titles.append(fch.RadarChartTitle(node_title, angle=None if should_rotate_nodes else 360))
            self.update()
            
        # Creates the node control in the sidebar
        def create_sidebar_node(idx: int, title: str) -> ft.Container:
            return ft.Container(
                ft.TextField(
                    value=title, 
                    dense=True, data=idx, expand=True,
                    on_blur=update_node_title,
                    border=ft.InputBorder.NONE, border_radius=4,
                    text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    suffix=ft.IconButton(       #  Delete button
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                        mouse_cursor="click" if idx >= 3 else None, 
                        data=idx,
                        on_click=delete_node if idx >= 3 else None,
                        opacity=1 if idx >= 3 else 0,
                        disabled=idx < 3
                    )    
                ),
                border_radius=4,
            )
        
        # Create sidebar column to hold our nodes and data_sets
        sidebar_dataset_column = ft.Column([create_data_set_sidebar_control(idx, data) for idx, data in enumerate(self.data.get('radar_data', {}).get('data_sets', []))])
        sidebar_nodes_column = ft.Column([create_sidebar_node(idx, title) for idx, title in enumerate(self.data.get('radar_data', {}).get('nodes', []))]) 

        
        # Update the minimum and maximum values for the radar chart and ensure all dataset entries conform to the new scale
        async def update_min_max_value(e: ft.Event):
            # Grab our new value and either min or max depending on which control triggered the event
            new_value = int(e.control.value)
            key = e.control.data
            # Return early if no changes
            if key == "min_value" and new_value == self.data['radar_data'].get('min_value', 0):
                return
            if key == "max_value" and new_value == self.data['radar_data'].get('max_value', 20):
                return
            
            # Validate that the new min or max value is within acceptable bounds relative to the other value
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
            
            # Otherwide, update our data for either min or max
            self.update_data(**{'radar_data': {key: new_value}})

            # Go through each dataset in data and ensure all entries conform to the new min and max values
            for idx, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', [])):
                for i in range(len(ds.get('entries', []))):
                    if ds['entries'][i] < self.data['radar_data'].get('min_value', 0):
                        ds['entries'][i] = self.data['radar_data'].get('min_value', 0)
                    if ds['entries'][i] > self.data['radar_data'].get('max_value', 20):
                        ds['entries'][i] = self.data['radar_data'].get('max_value', 20)

            self.update_data(**{'radar_data': self.data.get('radar_data', {})})

            # Update all our sliders to make sure they are within bounds for dataset ctrls in sidebar
            new_min = int(self.data['radar_data'].get('min_value', 0))
            new_max = int(self.data['radar_data'].get('max_value', 20))
            for ctrl in sidebar_dataset_column.controls:
                
                for c in ctrl.controls:
                    c.controls[0].value = str(new_min)      # Min text on left
                    c.controls[2].value = str(new_max)      # Max text on right 
                    slider = c.controls[1]
                    slider.min = new_min
                    slider.max = new_max
                    if slider.value < new_min:
                        slider.value = new_min
                    if slider.value > new_max:
                        slider.value = new_max

            # Update values for all entries in the datasets on our chart
            for idx, ds in enumerate(chart.data_sets):
                # Make sure first one updates as we want
                if idx == 0:
                    for i, e in enumerate(ds.entries):
                        if i == 0:
                            e.value = self.data['radar_data'].get('min_value', 0)
                        else:
                            e.value = self.data['radar_data'].get('max_value', 20)
                    continue
                for e in ds.entries:
                    if e.value < self.data['radar_data'].get('min_value', 0):
                        e.value = self.data['radar_data'].get('min_value', 0)
                    if e.value > self.data['radar_data'].get('max_value', 20):
                        e.value = self.data['radar_data'].get('max_value', 20)

            self.update()
                    
        # Increases or decreases the tick count
        async def update_tick_count(e: ft.Event):
            change_function = e.control.data

            if change_function == "add":
                self.data['radar_data']['tick_count'] = self.data['radar_data'].get('tick_count', 2) + 1
            elif change_function == "subtract" and self.data['radar_data'].get('tick_count', 2) > 1:
                self.data['radar_data']['tick_count'] = self.data['radar_data'].get('tick_count', 2) - 1

            chart.tick_count = self.data['radar_data'].get('tick_count', 2)
            self.update_data(**{'radar_data': {'tick_count': self.data['radar_data'].get('tick_count', 2)}})
            chart.update()

        # Updates if we show our tick labels or not
        async def update_show_tick_labels(e):
            self.update_data(**{'radar_data': {'show_tick_labels': not self.data.get('radar_data', {}).get('show_tick_labels', False)}})
            chart.ticks_text_style = ft.TextStyle(size=16, color=ft.Colors.PRIMARY if self.data['radar_data'].get('show_tick_labels', False) else ft.Colors.TRANSPARENT, italic=True)
            chart.update()

        # Updates if we rotate our node titles or not
        async def toggle_rotate_node_titles(e):
            self.update_data(**{'radar_data': {'rotate_node_titles': not self.data['radar_data'].get('rotate_node_titles', False)}})
            for title in chart.titles:
                title.angle = None if self.data['radar_data'].get('rotate_node_titles', False) else 360
            chart.update()

        # Insert our settings into the sidebar header after our title
        self.sidebar_header.controls.insert(
            1,
            ft.MenuBar(
                [
                    ft.SubmenuButton(
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY),
                        [
                            ft.Switch(
                                True, "\tMake Chart Round", value=self.data.get('radar_data', {}).get('make_chart_round', False),
                                on_change=toggle_shape, mouse_cursor=ft.MouseCursor.CLICK
                            ),
                            ft.Switch(
                                True, "\tShow Interval Labels", value=self.data.get('radar_data', {}).get('show_tick_labels', False),
                                on_change=update_show_tick_labels, mouse_cursor=ft.MouseCursor.CLICK, 
                            ),
                            ft.Switch(
                                True, "\tRotate Chart Nodes", value=self.data.get('radar_data', {}).get('rotate_node_titles', False),
                                on_change=toggle_rotate_node_titles, mouse_cursor=ft.MouseCursor.CLICK,
                            ),
                            ft.Row([
                                ft.Text(
                                    "\tInterval Count", style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                                    tooltip="Increase or Decrease the number of lines between the center and outer edge of the chart"
                                ),
                                ft.IconButton(
                                    ft.Icons.REMOVE_OUTLINED, ft.Colors.ERROR, 
                                    mouse_cursor=ft.MouseCursor.CLICK, on_click=update_tick_count, data="subtract"
                                ),
                                ft.IconButton(
                                    ft.Icons.ADD_OUTLINED, ft.Colors.PRIMARY, 
                                    mouse_cursor=ft.MouseCursor.CLICK, on_click=update_tick_count, data="add"
                                ),
                            ], spacing=0),
                            ft.TextField(
                                value=str(self.data.get('radar_data', {}).get('min_value', 0)),
                                label="Min Value", expand=True,
                                on_blur=update_min_max_value,
                                data="min_value",
                                input_filter=ft.NumbersOnlyInputFilter(),
                                margin=ft.Margin.only(top=6, left=10, right=10), border_color=ft.Colors.OUTLINE_VARIANT,
                                border_radius=4, dense=True
                            ),
                            ft.TextField(
                                value=str(self.data.get('radar_data', {}).get('max_value', 20)),
                                label="Max Value", expand=True,
                                on_blur=update_min_max_value,
                                input_filter=ft.NumbersOnlyInputFilter(),
                                data="max_value",
                                margin=ft.Margin.only(top=6, left=10, right=10), border_color=ft.Colors.OUTLINE_VARIANT,
                                border_radius=4, dense=True
                            )
                            
                            
                        ],
                        menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                        style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
                        tooltip="Adjust the settings for this bar chart."
                    ),
                ],
                style=ft.MenuStyle(
                    bgcolor="transparent", shadow_color="transparent",
                    shape=ft.RoundedRectangleBorder(radius=4),
                    padding=ft.Padding.all(0)
                ),
            )
        )

        self.sidebar_body.controls.extend([
            ft.Row([    # Label dataset
                ft.Text(f"Data Sets", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)), 
                ft.IconButton(      # Create new dataset button
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    ft.Colors.PRIMARY,
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_click=create_data_set,
                ),
            ], spacing=0),
            sidebar_dataset_column, # Column to hold our sidebar dataset controls
            ft.Row([    # Label Nodes
                ft.Text(f"Nodes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                ft.IconButton(      # Create new node button
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    ft.Colors.PRIMARY,
                    on_click=create_node,
                    mouse_cursor=ft.MouseCursor.CLICK,
                ),
            ]),
            sidebar_nodes_column,

            # Notes stuff
            ft.Divider(),
            self.sidebar_notes_label,
            self.sidebar_notes_column
                
        ])        


        # Set up our main conent
        self.content = ft.Stack([
            
            ft.Row([
                ft.Column([
                    dataset_keys,
                    chart,
                ], expand=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                self.toggle_sidebar_visibility_button, 
                self.sidebar,
            ], spacing=0, expand=True, alignment=ft.MainAxisAlignment.END, 
                    vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], expand=True, alignment=ft.Alignment.CENTER_RIGHT)
       

    def build(self):
        super().build()
        if self.data.get('chart_type', "") == "bar":
            self.bar_chart_view()
        else:
            self.radar_chart_view()

        
# TODO: Don't hold the placeholder dataset in chart data. Just render and alter it live
# Add dragging to manipulate radar chart entries real time
# Determine positive angles by 360/ node count, and if closer to 90 or 270, use that contoller
# ADD NOTES so people can use this to flesh out power systems if wanted