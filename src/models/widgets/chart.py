# Charts for a story

''' Class for the Item widget. Displays as its own tab for easy access to pinning '''

import flet as ft
from models.views.story import Story
from models.widget import Widget
from utils.verify_data import verify_data
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
        data: dict = None, 
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
                'color': app.settings.data.get('default_chart_color'),
                'chart_type': type,             # How our chart is being displayed (bar or radar)
                'description': str(),

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
        
        


    # Returns our widgets view for bar charts
    def bar_chart_view(self):
        ''' Builds out the body of our bar chart widget '''

        # Updates the indices for the controls for groups and rods in the chart and sidebar
        async def update_indices():
            await update_group_indices()
            await update_rod_indices()

        # Update each label in the chart and expansion tile delete button in the sidebar
        async def update_group_indices():
            for group_idx, label in enumerate(self.data.get('bar_data', {}).get('groups', [])):
                chart.bottom_axis.labels[group_idx].value = group_idx                   # Value of label on chart 
                chart.bottom_axis.labels[group_idx].label.data = group_idx              # Data of tf for changing
                sidebar_bar_group_column.controls[group_idx].trailing.data = group_idx  # Delete button for that group in sidebar

        # Updates the indices for each rod within each group in the sidebar and chart
        async def update_rod_indices():
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
            await update_indices()      # Update indices 
            
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
            await update_indices()   # Update indices after deleting a group

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
            await update_indices()

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
            await update_indices()

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
            color=group_data.get('rods', [{}])[0].get('color', self.data.get('color', ft.Colors.PRIMARY)) if len(group_data.get('rods', [])) > 0 else self.data.get('color', ft.Colors.PRIMARY) 
            rods=[rod for rod in group_data.get('rods', [])]

            # Build expansion_tile functionality
            return ft.ExpansionTile(
                ft.Text(title, weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),   # Group title
                trailing=ft.IconButton(     # Delete group button
                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                    mouse_cursor=ft.MouseCursor.CLICK, data=group_idx, on_click=delete_group
                ),
                dense=True, tile_padding=ft.Padding.only(left=10, right=0), controls_padding=ft.Padding.only(right=20, left=20),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, collapsed_bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                data=group_idx, shape=ft.RoundedRectangleBorder(radius=4), collapsed_shape=ft.RoundedRectangleBorder(radius=4),
                expanded=is_new,
                controls=[
                    ft.Divider(2, 2),   
                    ft.Row([
                        ft.Text("Rods", color=ft.Colors.ON_SURFACE_VARIANT, italic=True, weight=ft.FontWeight.BOLD, size=14),   # Label of Rods
                        ft.IconButton(      # Add new rod button
                            ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                            self.data.get('color', ft.Colors.PRIMARY),
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
            self.update_data(**{'bar_data': {'show_labels': new_show_labels_value}})
            # Update chart
            new_show_labels_value = e.control.value
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
                        ft.Icon(ft.Icons.SETTINGS_OUTLINED, "primary"),
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
        self.sidebar_body.controls.append(
            ft.Row([
                ft.Text(f"\tGroups", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                ft.IconButton(      # Create group button
                    ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                    self.data.get('color', ft.Colors.PRIMARY),
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_click=create_group,
                ),
            ], spacing=0))

        # Add the sidebar bar group
        self.sidebar_body.controls.append(sidebar_bar_group_column)

        # Set our content
        self.content = ft.Row([
            ft.Container(chart, expand=3, padding=ft.Padding.only(bottom=20, left=20)),
            self.show_sidebar_button,
            self.sidebar
        ])
        
    # Returns our widgets view for radar charts
    def radar_chart_view(self):
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
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            self.reload_widget()

        # Updates whether our dataset is expanded in the info column or not
        async def _update_expanded_state(e):
            expanded = e.control.expanded
            idx = e.control.data
            self.data.get('radar_data', {}).get('data_sets', [])[idx]['expanded'] = expanded
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})

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
                    title=ft.TextField(
                        title, dense=True, data=idx, expand=True,
                        prefix_icon=ft.PopupMenuButton(
                            icon=ft.Icons.COLOR_LENS_OUTLINED, 
                            icon_color=color, menu_padding=ft.Padding.all(0),
                            tooltip="Change Color",
                            style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
                            items=[
                                ft.PopupMenuItem(
                                    color.capitalize(), label_text_style=ft.TextStyle(color=color, weight=ft.FontWeight.BOLD),
                                    data=idx, on_click=_update_dataset_color, mouse_cursor=ft.MouseCursor.CLICK
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

        
        
        if not self.data.get('show_sidebar', True):

            self.body_container.content = ft.Column([
                ft.Container(height=1),
                ft.Row([ft.Container(keys, expand=True)]),
                ft.Row(
                    [
                        chart, 
                        ft.IconButton(
                            ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED, self.data.get('color', ft.Colors.PRIMARY),
                            on_click=self._toggle_show_sidebar, 
                            mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                        )
                    ], expand=True, spacing=0
                )
            ], expand=True)
            return  # Don't load the info column if we're not showing it

        # Renames a node title on the chart
        async def _update_node_title(e):
            self.data['radar_data']['nodes'][e.control.data] = e.control.value
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            chart.titles[e.control.data].text = e.control.value
            chart.update()

        # Deletes a node/title and the corresponding data for it in each data set
        async def _delete_node_title(e):

            async def _delete_node_title_confirm(_):
                del self.data['radar_data']['nodes'][e.control.data]
                for ds in self.data.get('radar_data', {}).get('data_sets', []):
                    del ds['entries'][e.control.data]
                self.update_data(**{'radar_data': self.data.get('radar_data', {})})
                self.reload_widget()
                self.page.pop_dialog()

            node_title = self.data['radar_data']['nodes'][e.control.data]

            dlg = ft.AlertDialog(
                title=f"Are you sure you want to delete {node_title}?",
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.PRIMARY)),
                    ft.TextButton("Delete", on_click=_delete_node_title_confirm, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                ]
            )
            self.page.show_dialog(dlg)

        # Adds a new title to the end of our titles list, and a default value for each dataset
        async def _add_node_title(e):
            self.data['radar_data']['nodes'].append(f"Node {len(self.data['radar_data']['nodes']) + 1}")
            default_value = int(self.data.get('radar_data', {}).get('max_value', 20) / 2)
            if default_value < self.data.get('radar_data', {}).get('min_value', 0):
                default_value = int(self.data.get('radar_data', {}).get('min_value', 0))
            for ds in self.data.get('radar_data', {}).get('data_sets', []):
                ds['entries'].append(default_value)   
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            self.reload_widget()

        # Toggles the chart either polygon or circle shaped
        async def _toggle_shape(e):
            self.data['radar_data']['make_chart_round'] = e.control.value
            if e.control.value:
                chart.radar_shape = fch.RadarShape.CIRCLE
            else:
                chart.radar_shape = fch.RadarShape.POLYGON
               
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
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
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            self.reload_widget()

        # Delete a dataset and all its info
        async def _delete_data_set(e):

            async def _delete_data_set_confirm(_):
                idx = e.control.data
                del self.data['radar_data']['data_sets'][idx]
                self.update_data(**{'radar_data': self.data.get('radar_data', {})})
                self.reload_widget()
                self.page.pop_dialog()

            dataset_title = self.data['radar_data']['data_sets'][e.control.data]['title']

            dlg = ft.AlertDialog(
                title=f"Are you sure you want to delete {dataset_title}?",
                actions=[
                    ft.TextButton("Cancel", on_click=lambda _: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.PRIMARY)),
                    ft.TextButton("Delete", on_click=_delete_data_set_confirm, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, color=ft.Colors.ERROR)),
                ]
            )
            self.page.show_dialog(dlg)

        # Toggle whether a dataset is visible on the chart
        async def _toggle_dataset_visibility(e):
            idx = e.control.data
            ds = self.data['radar_data']['data_sets'][idx]
            ds['visible'] = not ds.get('visible', True)
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            self.reload_widget()

        # Change datasets color on the chart
        async def _update_dataset_color(e):
            idx = e.control.data
            color = str(e.control.content)
            self.data['radar_data']['data_sets'][idx]['color'] = color
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            self.reload_widget()

        # Go through and add our titles/nodes to the chart
        titles = []
        for idx, title in enumerate(self.data.get('radar_data', {}).get('nodes', [])):
            titles.append(
                ft.TextField(
                    value=title, margin=ft.Margin.only(bottom=10, right=11),
                    dense=True, data=idx, expand=True,
                    on_blur=_update_node_title,
                    suffix_icon=ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                        mouse_cursor="click", data=idx,
                        on_click=_delete_node_title
                    ) if idx >= 3 else None   # Minimum 3 nodes
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
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            self.reload_widget()
           


        min_value_tf = ft.TextField(
            value=str(self.data.get('radar_data', {}).get('min_value', 0)),
            label="Min Value", dense=True, expand=True,
            on_blur=_update_min_max_value,
            input_filter=ft.NumbersOnlyInputFilter(),
            tooltip="Minimum value in the center of the chart. Must be less than max value. If values in data sets are below this, they will be set to this value. ",
            data="min_value"
        )
        max_value_tf = ft.TextField(
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
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            chart.update()

        async def _update_show_tick_labels(e):
            self.data['radar_data']['show_tick_labels'] = not self.data['radar_data'].get('show_tick_labels', False)
            chart.ticks_text_style = ft.TextStyle(size=16, color=self.data.get('color', ft.Colors.ON_SURFACE_VARIANT) if self.data['radar_data'].get('show_tick_labels', False) else ft.Colors.TRANSPARENT, italic=True)
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            chart.update()

        async def _toggle_rotate_node_titles(e):
            self.data['radar_data']['rotate_node_titles'] = not self.data['radar_data'].get('rotate_node_titles', False)
            for title in chart.titles:
                title.angle = None if self.data['radar_data'].get('rotate_node_titles', False) else 360
            self.update_data(**{'radar_data': self.data.get('radar_data', {})})
            chart.update()

        sidebar_bar_group_column = ft.Column(
            data_sets + [
                
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
                #ft.Divider(),
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

        self.sidebar_body.controls.append(sidebar_bar_group_column)

        self.content = ft.Row(
            [
                ft.Column([
                    ft.Container(height=1),
                    ft.Row([ft.Container(keys, expand=True)]),
                    chart,
                ], expand=3),
                self.show_sidebar_button,
                self.sidebar
            ], expand=True, spacing=0
        )
       

    def build(self):
        super().build()

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''


        if self.data.get('chart_type', "") == "bar":
            self.bar_chart_view()
        else:
            self.radar_chart_view()

        try:

            self.update()
        except Exception as _:
            pass
        