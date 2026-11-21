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
import flet_shadcn_ui as shad
from styles.highlight_button import HighlightButton


    

class BarChart(Widget):

    # Constructor
    def __init__(
        self, 
        title: str, 
        directory_path: str, 
        story: Story, 
        data: dict = {}, 
        is_new: bool = False,
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
                'tag': "bar_chart",             # Tag to identify what type of object this is
                'color': app.settings.data.get('widget_defaults', {}).get('chart', {}).get('color', "primary"),

                'show_sidebar': True,   # Whether to show the info column on the side of our charts or not.

                'chart_data': {
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

            },
        )

    def build(self):
        super().build()

        # Updates the indices for the controls for groups and rods in the chart and sidebar
        def update_indices():
            update_group_indices()
            update_rod_indices()

        # Update each label in the chart and expansion tile delete button in the sidebar
        def update_group_indices():
            for group_idx, label in enumerate(self.data.get('chart_data', {}).get('groups', [])):
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
                            item.data = (group_idx, rod_idx, item.data[2])
                        ctrl.controls[0].content.content.content.color = ctrl.controls[0].content.content.content.color
                        ctrl.controls[2].data = (group_idx, rod_idx)    # Slider
                        ctrl.controls[4].data = (group_idx, rod_idx)    # Delete button
                        rod_idx += 1

        # Create a new group with default data in data, chart, and sidebar
        async def create_group(e: ft.Event):

            # Give med value for rod
            median_value = int(self.data.get('chart_data', {}).get('max_y', 20) / 2)
            if median_value < self.data.get('chart_data', {}).get('min_value', 0):
                median_value = int(self.data.get('chart_data', {}).get('min_value', 0))

            # Add rod to data and update
            self.data['chart_data']['groups'].append({
                'name': f"Group {len(self.data.get('chart_data', {}).get('groups', [])) + 1}",
                'expanded': True,
                'rods': [
                    {
                        'to_y': median_value, 
                        'color': "primary"
                    }
                ]
            })
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

            # Add the new group to the sidebar, chart, and bottom chart axis labels. 
            sidebar_bar_group_column.controls.append(create_sidebar_group(len(self.data.get('chart_data', {}).get('groups', [])) - 1, self.data.get('chart_data', {}).get('groups', [])[-1], is_new=True))
            chart.groups.append(create_chart_bar_group(len(self.data.get('chart_data', {}).get('groups', [])) - 1, self.data.get('chart_data', {}).get('groups', [])[-1]))
            chart.bottom_axis.labels.append(create_bar_group_label(len(self.data.get('chart_data', {}).get('groups', [])) - 1, self.data.get('chart_data', {}).get('groups', [])[-1].get('name', f"Group {len(self.data.get('chart_data', {}).get('groups', []))}")))
            self.update()
            update_indices()      # Update indices 
            
        # Deletes a group from data, chart, and sidebar
        async def delete_group(e: ft.Event):
            idx = e.control.data    
            # Delete from data
            self.data.get('chart_data', {}).get('groups', []).pop(idx)
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

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
            group_data = self.data.get('chart_data', {}).get('groups', [])[group_idx]

            # Median value for new rod
            median_value = int(self.data.get('chart_data', {}).get('max_y', 20) / 2)
            if median_value < self.data.get('chart_data', {}).get('min_value', 0):
                median_value = int(self.data.get('chart_data', {}).get('min_value', 0))

            # Add to data and update the data
            group_data['rods'].append({
                'to_y': median_value, 
                'color': "primary"
            })
            self.data['chart_data']['groups'][group_idx] = group_data
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

            # Grab that rod data and its new index
            rod_data = group_data['rods'][-1]
            new_rod_idx = len(self.data.get('chart_data', {}).get('groups', [])[group_idx]['rods']) - 1

            # Add the rod to the group on the char
            chart.groups[group_idx].rods.append(
                fch.BarChartRod(
                    from_y=0, to_y=rod_data.get('to_y', 0), 
                    width=self.data.get('chart_data', {}).get('rod_width', 30),
                    border_radius=None if self.data.get('chart_data', {}).get('rod_shape', "rounded") == "rounded" else ft.BorderRadius.only(top_left=2, top_right=2),
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
            self.data['chart_data']['groups'][group_idx]['rods'][rod_idx]['to_y'] = new_value
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

        # Deletes a rod from the chart, data, and sidebar
        async def delete_rod(e: ft.Event):
            group_idx, rod_idx = e.control.data

            self.data['chart_data']['groups'][group_idx]['rods'].pop(rod_idx)
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})
            chart.groups[group_idx].rods.pop(rod_idx)
            sidebar_bar_group_column.controls[group_idx].controls.pop(rod_idx+2)
            self.update()
            update_indices()

        # Changes color of a rod in data, chart, and sidebar
        async def change_rod_color(e: ft.Event[ft.Control]):
            # Grab indices and new color
            group_idx, rod_idx, new_color = e.control.data

            # Update data
            self.data['chart_data']['groups'][group_idx]['rods'][rod_idx]['color'] = new_color
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

            # Update charts rod color and sidebar
            chart.groups[group_idx].rods[rod_idx].color = new_color
            e.control.parent.icon_color = new_color
            e.control.parent.parent.controls[2].active_color = new_color
            e.control.parent.content.content.content.color = new_color
            self.update()

        # Creates the rod controls for the sidebar inside a group expansion tile
        def create_sidebar_rod(group_idx: int, rod_idx: int, rod: dict):
            # Set min and max
            min_value=0
            max_value=self.data.get('chart_data', {}).get('max_y', 20)

            return ft.Row([
                
                shad.ContextMenu(
                    HighlightButton(ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, rod.get('color', ft.Colors.PRIMARY)), is_round=True, use_padding=True), 
                    [
                        shad.MenuItem(
                            content=ft.Icon(ft.Icons.CIRCLE, color=color, size=20),
                            on_click=change_rod_color, close_on_click=True, data=(group_idx, rod_idx, color),
                            expand=True,
                        ) for color in colors
                    ],
                    open_on_tap=True
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
            expanded=group_data.get('expanded', False)
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
                expanded=expanded,
                on_change=lambda e: self.update_data(**{'chart_data': {'groups': {group_idx: {'expanded': e.control.expanded}}}}),
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
            self.update_data(**{'chart_data': {axis_type: new_title}})

        # Sets the maximum value for the Y-axis of the chart
        async def set_max_y_value(e: ft.Event):
            
            # Handle empty values
            if e.control.value == "" or e.control.value is None:
                e.control.value = str(chart.max_y)
                e.control.update()
                return
            
            # Update data
            new_value = int(e.control.value)
            self.update_data(**{'chart_data': {'max_y': new_value}})

            # Update chart
            chart.max_y = new_value
            chart.update()

        # Sets whether to show labels on the chart axes
        async def set_show_labels(e: ft.Event):
            # Update data
            new_show_labels_value = e.control.value
            self.update_data(**{'chart_data': {'show_labels': new_show_labels_value}})
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
            self.update_data(**{'chart_data': {'rod_width': new_width}})

        async def set_rod_spacing_value(e: ft.Event):
            # Update data
            new_spacing = int(e.control.value)
            self.update_data(**{'chart_data': {'rod_spacing': new_spacing}})
            # Update the spacing of each rod in the chart
            for group in chart.groups:
                group.spacing = new_spacing
            chart.update()

        # Save in data after done adjusting rod spacing
        async def set_rod_spacing_data(e: ft.Event):
            new_spacing = int(e.control.value)
            self.update_data(**{'chart_data': {'rod_spacing': new_spacing}})

        # Sets whether the rods in the chart should be stacked
        async def set_stacked_rods(e: ft.Event):
            # Update data
            stack_rods = e.control.value
            self.update_data(**{'chart_data': {'stack_rods': stack_rods}})
            # Update the stacking of each group in the chart
            for group in chart.groups:
                group.group_vertically = e.control.value
            chart.update()

        # Set the rod shape to either rounded or square 
        async def set_rod_shape(e: ft.Event):
            # Update data
            new_shape = "rounded" if e.control.value else "square"
            self.update_data(**{'chart_data': {'rod_shape': new_shape}})
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
                self.update_data(**{'chart_data': {'show_horizontal_grid_lines': show_grid_lines}})
                chart.horizontal_grid_lines = fch.ChartGridLines() if show_grid_lines else None
            else:
                self.update_data(**{'chart_data': {'show_vertical_grid_lines': show_grid_lines}})
                chart.vertical_grid_lines = fch.ChartGridLines() if show_grid_lines else None
            chart.update()

        # Returns the small label control under each bar group on the chart
        def create_bar_group_label(idx: int, name: str) -> fch.ChartAxisLabel:
            # Updates the label in data and in the sidebar
            async def set_bar_group_label(e: ft.Event):
                idx = e.control.data
                new_label = e.control.value
                self.data['chart_data']['groups'][idx]['name'] = new_label
                self.update_data(**{'chart_data': self.data.get('chart_data', {})})
                sidebar_bar_group_column.controls[idx].title.value = new_label
                sidebar_bar_group_column.controls[idx].update()
            # Return the chart axis label with the text field for editing the label
            return fch.ChartAxisLabel(
                idx,        # Requires value of index
                label=ft.TextField(     # Tf for editing the label
                    value=name, dense=True, width=120, clip_behavior=ft.ClipBehavior.NONE,
                    data=idx, on_change=set_bar_group_label, border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
                    text_align=ft.TextAlign.CENTER, text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500), bgcolor=ft.Colors.TRANSPARENT
                )
                
            )

        # Creates a group control for the chart using index and data
        def create_chart_bar_group(idx: int, group_data: dict) -> fch.BarChartGroup:
            return fch.BarChartGroup(
                idx,        # Needs for alignment
                spacing=self.data.get('chart_data', {}).get('rod_spacing', 4), 
                group_vertically=self.data.get('chart_data', {}).get('stack_rods', False),
                rods=[
                    fch.BarChartRod(
                        from_y=0, to_y=rod.get('to_y', 0), 
                        width=self.data.get('chart_data', {}).get('rod_width', 30),
                        border_radius=None if self.data.get('chart_data', {}).get('rod_shape', "rounded") == "rounded" else ft.BorderRadius.only(top_left=2, top_right=2),
                        color=rod.get('color', self.data.get('color', ft.Colors.PRIMARY)),
                    ) for rod in group_data.get('rods', [])
                ]
            )

        # Our bar chart
        chart = fch.BarChart(
            groups=[create_chart_bar_group(idx, group) for idx, group in enumerate(self.data.get('chart_data', {}).get('groups', []))],
            #on_event=lambda e: print(e),

            # User customizable options
            max_y=self.data.get('chart_data', {}).get('max_y', 20),
            left_axis=fch.ChartAxis(
                ft.TextField(
                    value=self.data.get('chart_data', {}).get('left_axis_title', ""), 
                    data="left", on_change=set_chart_axis_title, border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
                    text_align=ft.TextAlign.CENTER, text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.TRANSPARENT
                ), 
                title_size=40, label_size=30,
                show_labels=self.data.get('chart_data', {}).get('show_labels', False),
            ),
            bottom_axis=fch.ChartAxis(
                ft.TextField(
                    value=self.data.get('chart_data', {}).get('bottom_axis_title', ""), 
                    data="bottom", on_change=set_chart_axis_title, border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
                    text_align=ft.TextAlign.CENTER, text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.TRANSPARENT
                ),
                title_size=40, label_size=30,
                show_labels=self.data.get('chart_data', {}).get('show_labels', False),
                labels=[create_bar_group_label(idx, group.get('name', f"Group {idx + 1}")) for idx, group in enumerate(self.data.get('chart_data', {}).get('groups', []))]
            ),
            top_axis=fch.ChartAxis(ft.Text(""), labels=fch.ChartAxisLabel(0, " ")), # Invisible label for behavior purposes
            horizontal_grid_lines=fch.ChartGridLines() if self.data.get('chart_data', {}).get('show_horizontal_grid_lines', False) else None,
            vertical_grid_lines=fch.ChartGridLines() if self.data.get('chart_data', {}).get('show_vertical_grid_lines', False) else None,

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
            [create_sidebar_group(idx, group) for idx, group in enumerate(self.data.get('chart_data', {}).get('groups', []))],
            expand=True, scroll="auto", #spacing=0,
        )

        # Insert our settings into the sidebar header after our title
        self.sidebar_header.controls.append(
            shad.ContextMenu(
                HighlightButton(ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY), is_round=True, use_padding=True),
                [
                    # Toggle stacked rods
                    ft.Switch(
                        value=self.data.get('chart_data', {}).get('stack_rods', False), 
                        label="\tStack Rods", on_change=set_stacked_rods
                    ),
                    # Toggle rounded rods
                    ft.Switch(
                        value=True if self.data.get('chart_data', {}).get('rod_shape', "rounded") == "rounded" else False, 
                        label="\tRounded Rods", on_change=set_rod_shape
                    ),
                    # Toggle axis labels
                    ft.Switch(
                        value=self.data.get('chart_data', {}).get('show_labels', False), 
                        label="\tShow Axis Labels", on_change=set_show_labels
                    ),
                    # Toggle horizontal grid lines
                    ft.Switch(
                        value=self.data.get('chart_data', {}).get('show_horizontal_grid_lines', False), 
                        label="\tShow Horizontal Grid Lines", on_change=set_grid_lines, data="horizontal"
                    ),
                    # Toggle vertical grid lines
                    ft.Switch(
                        value=self.data.get('chart_data', {}).get('show_vertical_grid_lines', False), 
                        label="\tShow Vertical Grid Lines", on_change=set_grid_lines, data="vertical"
                    ),
                    # Adjust max y value of the chart
                    ft.TextField(
                        label="Max Y Value", value=str(self.data.get('chart_data', {}).get('max_y', 20)), 
                        input_filter=ft.NumbersOnlyInputFilter(), data="max", on_blur=set_max_y_value,
                        margin=ft.Margin.only(top=6, left=10, right=10), 
                        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.OUTLINE_VARIANT), border_radius=4),
                        dense=True
                    ),
                    # Adjust Rod width
                    ft.Row([
                        ft.Text("\t\tRod Width", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                        ft.Slider(
                            value=self.data.get('chart_data', {}).get('rod_width', 30), min=10, max=100, 
                            label="{value}", expand=True, on_change=set_rod_width_value, on_change_end=set_rod_width_data
                        ),
                    ], spacing=0),
                    # Adjust rod spacing
                    ft.Row([
                        ft.Text("\t\tRod Spacing", theme_style=ft.TextThemeStyle.LABEL_LARGE),
                        ft.Slider(
                            value=self.data.get('chart_data', {}).get('rod_spacing', 30), min=0, max=20, 
                            label="{value}", expand=True, on_change=set_rod_spacing_value, on_change_end=set_rod_spacing_data
                        ),
                    ], spacing=0),
                ],
                open_on_tap=True
            ),
        )

        

        # Add a label and add groups button in the sidebar
        self.sidebar_notes_label.margin = None
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
        
