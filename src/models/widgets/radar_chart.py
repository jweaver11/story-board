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


    

class RadarChart(Widget):

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
                'tag': "radar_chart",             # Tag to identify what type of object this is
                'color': app.settings.data.get('widget_defaults', {}).get('chart', {}).get('color', "primary"),

                'show_sidebar': True,   # Whether to show the info column on the side of our charts or not.    

                # Data used for radar charts
                'chart_data': {
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
                            #'expanded': False,
                            #'entries': [0, 20, 20, 20, 20],   # The values for each title/axis of the radar chart. First value is min, second is max
                        #},
                        #{},...
                        
                    ]     
                }

            },
        )
        

    def build(self):
        super().build()
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
            self.data['chart_data']['data_sets'][dataset_idx]['entries'][entry_idx] = new_value
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

        # Updates the title of a dataset
        async def update_dataset_title(e: ft.Event):
            data_set_idx = e.control.data
            new_title = e.control.value
            # Update the data
            self.data.get('chart_data', {}).get('data_sets', [])[data_set_idx]['title'] = new_title
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

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

        should_rotate_nodes = self.data.get('chart_data', {}).get('rotate_node_titles', False)
        chart = fch.RadarChart(
            data_sets=[
                fch.RadarDataSet(
                    fill_color=ft.Colors.TRANSPARENT, # Protect weird transparent bugs
                    border_color=ft.Colors.TRANSPARENT,
                    entry_radius=0,
                    entries=[   # One invisible min and max value or chart renders weird
                        fch.RadarDataSetEntry(self.data.get('chart_data', {}).get('min_value', 0)),
                    ] + [fch.RadarDataSetEntry(self.data.get('chart_data', {}).get('max_value', 0)) for i, _ in enumerate(self.data.get('chart_data', {}).get('nodes', [])) if i < len(self.data.get('chart_data', {}).get('nodes', [])) - 1],
                ),
            ],
            expand=3,
            #on_event=lambda e: print(e),
            #radar_border_side=ft.BorderSide(1, ft.Colors.OUTLINE),
            #border=ft.Border.all(1, ft.Colors.OUTLINE),
            titles=[fch.RadarChartTitle(title, None if should_rotate_nodes else 360) for title in self.data.get('chart_data', {}).get('nodes', [])],
            center_min_value=True,
            tick_count=self.data.get('chart_data', {}).get('tick_count', 2),
            ticks_text_style=ft.TextStyle(
                size=16, color=ft.Colors.TRANSPARENT, italic=True
            ) if not self.data.get('chart_data', {}).get('show_tick_labels', False) else 
                ft.TextStyle(size=16, color=ft.Colors.PRIMARY, italic=True),
            title_text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
            animation=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            title_position_percentage_offset=0.1,
            radar_shape=fch.RadarShape.CIRCLE if self.data.get('chart_data', {}).get('make_chart_round', False) else fch.RadarShape.POLYGON,
            interactive=True
        )    

        # Add our data sets to the chart
        for idx, ds in enumerate(self.data.get('chart_data', {}).get('data_sets', [])):
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
                        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
                        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                        on_change=update_dataset_title, content_padding=4,
                        width=140, bgcolor=ft.Colors.TRANSPARENT, multiline=True
                    ),
                ], tight=True, spacing=6),
                border_radius=ft.BorderRadius.all(4), padding=ft.Padding.all(6),
                #margin=ft.Margin.only(left=10),
            )

        # Load our keys above the chart
        dataset_keys = ft.Row(
            [create_data_set_key_control(idx, ds) for idx, ds in enumerate(self.data.get('chart_data', {}).get('data_sets', []))], 
            alignment=ft.MainAxisAlignment.CENTER, wrap=True, margin=ft.Margin.only(top=10)
        )

        # Renames a node title on the chart
        async def update_node_title(e: ft.Event):
            # Update data
            self.data['chart_data']['nodes'][e.control.data] = e.control.value
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})
            # Update node on chart
            chart.titles[e.control.data].text = e.control.value
            chart.update()

        # Deletes a node/title and the corresponding data for it in each data set
        async def delete_node(e: ft.Event):
            node_idx = e.control.data
            
            # Delete the node from data and all values tied to it
            del self.data['chart_data']['nodes'][node_idx]
            for ds in self.data.get('chart_data', {}).get('data_sets', []):
                del ds['entries'][node_idx]
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

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
            self.data['chart_data']['make_chart_round'] = e.control.value
            if e.control.value:
                chart.radar_shape = fch.RadarShape.CIRCLE
            else:
                chart.radar_shape = fch.RadarShape.POLYGON
                
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})
            chart.update()

        # Adding a new dataset with default values in each node
        async def create_data_set(e: ft.Event):
            # Set median value
            median_value = int(self.data.get('chart_data', {}).get('max_value', 20) / 2)
            if median_value < self.data.get('chart_data', {}).get('min_value', 0):
                median_value = int(self.data.get('chart_data', {}).get('min_value', 0))

            # Add to data
            self.data['chart_data']['data_sets'].append({
                'title': f"Data Set {len(self.data['chart_data']['data_sets']) + 1}",
                'color': "primary",
                'expanded': True,
                'entries': [median_value for _ in self.data['chart_data']['nodes']],   # Default entries for each title/node
            })
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

            # Add dataset to our sidebar column
            sidebar_dataset_column.controls.append(
                create_data_set_sidebar_control(
                    len(self.data['chart_data']['data_sets']) - 1, 
                    self.data['chart_data']['data_sets'][-1], 
                    is_new=True
                )
            )

            # Add control to the chart data
            chart.data_sets.append(
                create_data_set_chart_control(
                    len(self.data['chart_data']['data_sets']) - 1,
                    self.data['chart_data']['data_sets'][-1]
                )
            )

            # Add key to our keys and update
            dataset_keys.controls.append(
                create_data_set_key_control(
                    len(self.data['chart_data']['data_sets']) - 1,
                    self.data['chart_data']['data_sets'][-1]
                )
            )

            self.update()

        # Returns a sidebar control for datasets
        def create_data_set_sidebar_control(data_set_idx: int, data_set_data: dict, is_new: bool=False) -> ft.ExpansionTile:

            def update_expanded(e: ft.Event):
                self.data['chart_data']['data_sets'][idx]['expanded'] = e.data
                self.update_data(**{'chart_data': self.data.get('chart_data', {})})

            min_value = self.data.get('chart_data', {}).get('min_value', 0)
            max_value = self.data.get('chart_data', {}).get('max_value', 20)
            title = data_set_data.get('title', f"Data Set {data_set_idx}")
            color = data_set_data.get('color', "primary")
            entries = data_set_data.get('entries', [])
            expanded = data_set_data.get('expanded', False)
            idx = data_set_idx
            
            color_cm = shad.ContextMenu(
                HighlightButton(ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color), is_round=True, use_padding=True), 
                [
                    shad.MenuItem(
                        content=ft.Icon(ft.Icons.CIRCLE, color=color, size=20),
                        on_click=update_dataset_color, close_on_click=True, data=color,
                        expand=True
                    ) for color in colors
                ],
                open_on_tap=True
            )
            return ft.ExpansionTile(
                leading=color_cm,
                title=ft.Text(title, weight=ft.FontWeight.BOLD, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                trailing=ft.IconButton(
                    ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                    mouse_cursor=ft.MouseCursor.CLICK, data=color,
                    on_click=delete_data_set
                ),
                dense=True, tile_padding=ft.Padding.only(left=10, right=10), controls_padding=ft.Padding.only(right=20, left=20),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH, collapsed_bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                shape=ft.RoundedRectangleBorder(radius=4), collapsed_shape=ft.RoundedRectangleBorder(radius=4),
                expanded=expanded,
                on_change=update_expanded,
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
            del self.data['chart_data']['data_sets'][data_set_idx]
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})
            
            # Remove from keys, chart, and sidebar
            dataset_keys.controls.pop(data_set_idx)
            chart.data_sets.pop(data_set_idx + 1)   # Skip first invisible dataset
            sidebar_dataset_column.controls.pop(data_set_idx)
            self.update()
            update_indices()

        # Change data_sets color on the chart
        async def update_dataset_color(e: ft.Event[ft.Control]):
            data_set_idx = e.control.parent.parent.data
            new_color = e.control.data
            self.data['chart_data']['data_sets'][data_set_idx]['color'] = new_color
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

            # Update sidebar icon color for this dataset
            sidebar_dataset_column.controls[data_set_idx].leading.icon_color = new_color
            # Update key color for this dataset
            container = dataset_keys.controls[data_set_idx].content.controls[0]
            container.border = ft.Border.all(2, new_color)
            container.bgcolor = ft.Colors.with_opacity(0.2, new_color)

            # Update the chart's dataset color to reflect the change
            chart.data_sets[data_set_idx + 1].fill_color = ft.Colors.with_opacity(0.2, new_color)  # Skip first invisible dataset
            chart.data_sets[data_set_idx + 1].border_color = new_color
            e.control.parent.content.content.content.color = new_color

            self.update()

        # Called to create a new node
        async def create_node(e: ft.Event):

            # Set new title and median value
            node_title = f"Node {len(self.data['chart_data']['nodes']) + 1}"
            median_value = int(self.data.get('chart_data', {}).get('max_value', 20) / 2)
            
            # Add this new node to the list of nodes and append the median value to each data set entry
            self.data['chart_data']['nodes'].append(node_title)
            if median_value < self.data.get('chart_data', {}).get('min_value', 0):
                median_value = int(self.data.get('chart_data', {}).get('min_value', 0))
            for ds in self.data.get('chart_data', {}).get('data_sets', []):
                ds['entries'].append(median_value)   

            # Update our data to support this new node
            self.update_data(**{'chart_data': self.data.get('chart_data', {})})
            sidebar_nodes_column.controls.append(create_sidebar_node(len(self.data['chart_data']['nodes']) - 1, node_title))

            # Add the new entries to the charts
            for ds in chart.data_sets:
                ds.entries.append(fch.RadarDataSetEntry(median_value))

            # Add new title to the chart and update
            should_rotate_nodes = self.data.get('chart_data', {}).get('rotate_node_titles', False)
            chart.titles.append(fch.RadarChartTitle(node_title, angle=None if should_rotate_nodes else 360))
            self.update()
            
        # Creates the node control in the sidebar
        def create_sidebar_node(idx: int, title: str) -> ft.Container:
            return ft.Container(
                ft.TextField(
                    value=title, 
                    dense=True, data=idx, expand=True,
                    on_change=update_node_title,
                    content_padding=4,
                    border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
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
        sidebar_dataset_column = ft.Column([create_data_set_sidebar_control(idx, data) for idx, data in enumerate(self.data.get('chart_data', {}).get('data_sets', []))])
        sidebar_nodes_column = ft.Column([create_sidebar_node(idx, title) for idx, title in enumerate(self.data.get('chart_data', {}).get('nodes', []))]) 

        
        # Update the minimum and maximum values for the radar chart and ensure all dataset entries conform to the new scale
        async def update_min_max_value(e: ft.Event):
            # Grab our new value and either min or max depending on which control triggered the event
            new_value = int(e.control.value)
            key = e.control.data
            # Return early if no changes
            if key == "min_value" and new_value == self.data['chart_data'].get('min_value', 0):
                return
            if key == "max_value" and new_value == self.data['chart_data'].get('max_value', 20):
                return
            
            # Validate that the new min or max value is within acceptable bounds relative to the other value
            if key == "min_value" and new_value >= self.data['chart_data'].get('max_value', 20):
                e.control.error = "Min value must be less than max value"
                e.control.value = str(self.data['chart_data'].get('min_value', 0))
                await e.control.focus()
                e.control.update()
                return
            if key == "max_value" and new_value <= self.data['chart_data'].get('min_value', 0):
                e.control.error = "Max value must be greater than min value"
                e.control.value = str(self.data['chart_data'].get('max_value', 20))
                await e.control.focus()
                e.control.update()
                return
            
            # Otherwide, update our data for either min or max
            self.update_data(**{'chart_data': {key: new_value}})

            # Go through each dataset in data and ensure all entries conform to the new min and max values
            for idx, ds in enumerate(self.data.get('chart_data', {}).get('data_sets', [])):
                for i in range(len(ds.get('entries', []))):
                    if ds['entries'][i] < self.data['chart_data'].get('min_value', 0):
                        ds['entries'][i] = self.data['chart_data'].get('min_value', 0)
                    if ds['entries'][i] > self.data['chart_data'].get('max_value', 20):
                        ds['entries'][i] = self.data['chart_data'].get('max_value', 20)

            self.update_data(**{'chart_data': self.data.get('chart_data', {})})

            # Update all our sliders to make sure they are within bounds for dataset ctrls in sidebar
            new_min = int(self.data['chart_data'].get('min_value', 0))
            new_max = int(self.data['chart_data'].get('max_value', 20))
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
                            e.value = self.data['chart_data'].get('min_value', 0)
                        else:
                            e.value = self.data['chart_data'].get('max_value', 20)
                    continue
                for e in ds.entries:
                    if e.value < self.data['chart_data'].get('min_value', 0):
                        e.value = self.data['chart_data'].get('min_value', 0)
                    if e.value > self.data['chart_data'].get('max_value', 20):
                        e.value = self.data['chart_data'].get('max_value', 20)

            self.update()
                    
        # Increases or decreases the tick count
        async def update_tick_count(e: ft.Event):
            change_function = e.control.data

            if change_function == "add":
                self.data['chart_data']['tick_count'] = self.data['chart_data'].get('tick_count', 2) + 1
            elif change_function == "subtract" and self.data['chart_data'].get('tick_count', 2) > 1:
                self.data['chart_data']['tick_count'] = self.data['chart_data'].get('tick_count', 2) - 1

            chart.tick_count = self.data['chart_data'].get('tick_count', 2)
            self.update_data(**{'chart_data': {'tick_count': self.data['chart_data'].get('tick_count', 2)}})
            chart.update()

        # Updates if we show our tick labels or not
        async def update_show_tick_labels(e):
            self.update_data(**{'chart_data': {'show_tick_labels': not self.data.get('chart_data', {}).get('show_tick_labels', False)}})
            chart.ticks_text_style = ft.TextStyle(size=16, color=ft.Colors.PRIMARY if self.data['chart_data'].get('show_tick_labels', False) else ft.Colors.TRANSPARENT, italic=True)
            chart.update()

        # Updates if we rotate our node titles or not
        async def toggle_rotate_node_titles(e):
            self.update_data(**{'chart_data': {'rotate_node_titles': not self.data['chart_data'].get('rotate_node_titles', False)}})
            for title in chart.titles:
                title.angle = None if self.data['chart_data'].get('rotate_node_titles', False) else 360
            chart.update()

        # Insert our settings into the sidebar header after our title
        self.sidebar_header.controls.append(
            shad.ContextMenu(
                HighlightButton(ft.Icon(ft.Icons.SETTINGS_OUTLINED, ft.Colors.PRIMARY), is_round=True, use_padding=True),
                [
                    ft.Switch(
                        True, "\tMake Chart Round", value=self.data.get('chart_data', {}).get('make_chart_round', False),
                        on_change=toggle_shape, mouse_cursor=ft.MouseCursor.CLICK
                    ),
                    ft.Switch(
                        True, "\tShow Interval Labels", value=self.data.get('chart_data', {}).get('show_tick_labels', False),
                        on_change=update_show_tick_labels, mouse_cursor=ft.MouseCursor.CLICK, 
                    ),
                    ft.Switch(
                        True, "\tRotate Chart Nodes", value=self.data.get('chart_data', {}).get('rotate_node_titles', False),
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
                        value=str(self.data.get('chart_data', {}).get('min_value', 0)),
                        label="Min Value", expand=True,
                        on_blur=update_min_max_value,
                        data="min_value",
                        input_filter=ft.NumbersOnlyInputFilter(),
                        margin=ft.Margin.only(top=6, left=10, right=10), 
                        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.OUTLINE_VARIANT), border_radius=4),
                        dense=True
                    ),
                    ft.TextField(
                        value=str(self.data.get('chart_data', {}).get('max_value', 20)),
                        label="Max Value", expand=True,
                        on_blur=update_min_max_value,
                        input_filter=ft.NumbersOnlyInputFilter(),
                        data="max_value",
                        margin=ft.Margin.only(top=6, left=10, right=10), 
                        border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.OUTLINE_VARIANT), border_radius=4),
                        dense=True
                    )
                ],
                open_on_tap=True
            ),
        )
        
        
        self.sidebar_notes_label.margin = None
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
