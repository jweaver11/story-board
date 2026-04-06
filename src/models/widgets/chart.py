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

                'bar_data': {
                    
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
                    'shape': "circle",   # Whether to show our radar chart as a circle or polygon
                    'show_info': True,  # Whether to show the info column on the side with our nodes and data sets
                    'data_sets': [      # The data sets that make up the radar chart
                        {               # Starts maximized invisible so they can see other datasets at all times
                            'color': "primary",
                            'entries': [10, 5, 10, 10, 5],   # The values for each title/axis of the radar chart
                            'visible': True,
                            'title': "Data Set 1",
                            'expanded': True,   # Whether the dataset's info is expanded in the side column
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

    def _bar_chart_view(self):
        ''' Builds out the body of our bar chart widget '''

        chart = fch.BarChart(
            groups=[
                fch.BarChartGroup(0, [fch.BarChartRod(from_y=0, to_y=3), fch.BarChartRod(from_y=0, to_y=5), fch.BarChartRod(from_y=0, to_y=2)]),
                fch.BarChartGroup(1, [fch.BarChartRod(from_y=0, to_y=4), fch.BarChartRod(from_y=0, to_y=2), fch.BarChartRod(from_y=0, to_y=6)]),
                fch.BarChartGroup(2, [fch.BarChartRod(from_y=0, to_y=5), fch.BarChartRod(from_y=0, to_y=3), fch.BarChartRod(from_y=0, to_y=4)]),
            ],
            interactive=True,
            max_y=10,
            bottom_axis=fch.ChartAxis(ft.Text("Bottom Axis"), label_size=40),
            left_axis=fch.ChartAxis(ft.Text("Left Axis"), title_size=40),
            baseline_y=0,
            expand=True,
        )
        self.body_container.content = chart

    async def _radar_chart_event(self, e: fch.RadarChartEvent):
        return
        chart = e.control
        event_type = e.type                 # Type of event
        dataset_index = e.data_set_index        # Index of which dataset we are interacting with
        entry_index = e.entry_index         # Index of which entry in the dataset we are interacting with  
        entry_value = e.entry_value     # Value of the indexed entry in that dataset

        print(e)

        if dataset_index is None or entry_index is None:
            #print("returned early")
            return      # If either of these are None, we aren't interacting with an actual entry so we can ignore the event
        
        #TODO: dataset index only shows index of visible charts, so its messed up if some are hidden
        

        match event_type:
            
            case fch.ChartEventType.POINTER_HOVER:
                #print(e)
                return
                chart.data_sets[dataset_index].fill_color = ft.Colors.with_opacity(0.5, self.data.get('radar_data', {}).get('data_sets', )[dataset_index].get('color', ft.Colors.PRIMARY))   # Make the dataset more opaque on hover to highlight it
                chart.update()
                # Could show a tooltip or something here with info about the entry we're hovering

            case fch.ChartEventType.PAN_START | fch.ChartEventType.LONG_PRESS_START | fch.ChartEventType.TAP_DOWN:
                # Grab whatever point is being interacted with
                pass
            case fch.ChartEventType.PAN_UPDATE | fch.ChartEventType.LONG_PRESS_MOVE_UPDATE:
                #print(e)
                new_value = entry_value  # Or calculate from pointer position if needed

                # 2. Update your data model
                self.data['radar_data']['data_sets'][dataset_index]['entries'][entry_index] = new_value

                # 3. Optionally: update the chart visually in real-time
                chart.data_sets[dataset_index].entries[entry_index].value = new_value
                chart.update()
            case fch.ChartEventType.PAN_END | fch.ChartEventType.LONG_PRESS_END:
                pass
                #print("End event: ", e)
            
                
        
        
    async def _toggle_show_info(self, e):
        self.data['radar_data']['show_info'] = not self.data['radar_data'].get('show_info', True)
        await self.save_dict()
        self.reload_widget()
        

        

    def _radar_chart_view(self):
        ''' Builds out the body of our radar chart widget '''

        #TODO: Show key at top of chart colors and labels
        # Maximum and Minimum Graph Values
        
        async def _update_entry(e):
            idx, entry_idx = e.control.data
            new_value = e.control.value

            # Update our data model
            self.data['radar_data']['data_sets'][idx]['entries'][entry_idx] = new_value

            # Update the chart visually in real-time
            chart.data_sets[idx].entries[entry_idx].value = new_value
            chart.update()

        class DataSet(ft.ExpansionTile):
            def __init__(self, title: str, color: str, entries: list, visible: bool, idx: int, expanded: bool):
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
                        )
                    ),
                    dense=True, tile_padding=ft.Padding.only(right=11), controls_padding=ft.Padding.only(right=11),
                    shape=ft.RoundedRectangleBorder(), expanded=expanded,
                    controls=[
                        ft.Slider(
                            value=entry, min=0, max=100, label="{value}", on_change=_update_entry, data=(idx, i),
                        ) for i, entry in enumerate(entries)
                    ]
                )
            
            
        
        chart = fch.RadarChart(
            expand=2,
            titles=[fch.RadarChartTitle(text=title) for title in self.data.get('radar_data', {}).get('nodes', [])],
            center_min_value=True,
            tick_count=5,
            #ticks_text_style=ft.TextStyle(size=16, color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
            ticks_text_style=ft.TextStyle(size=16, color=ft.Colors.TRANSPARENT, italic=True),
            title_text_style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
            on_event=self._radar_chart_event,
            animation=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            title_position_percentage_offset=0.1,
            radar_shape=fch.RadarShape.CIRCLE if self.data.get('radar_data', {}).get('shape', "circle") == "circle" else fch.RadarShape.POLYGON,
        )    

        # Add our data sets to the chart
        for ds in self.data.get('radar_data', {}).get('data_sets', []):
            color = ds.get('color', "primary")
            entries: list = ds.get('entries', [])
            visible: bool = ds.get('visible', True)
            
            if not visible:     # Skip non-visible ones
                continue

            chart.data_sets.append(
                fch.RadarDataSet(
                    fill_color=ft.Colors.with_opacity(0.2, color),
                    border_color=color,
                    entry_radius=4,
                    entries=[fch.RadarDataSetEntry(value) for value in entries],
                )
            )
        
        if self.data.get('radar_data', {}).get('show_info', True):

            self.body_container.content = ft.Row(
                [
                    chart, 
                    ft.IconButton(
                        ft.Icons.INFO_OUTLINE, on_click=self._toggle_show_info, 
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    )
                ], expand=True, spacing=0
            )
            return

        # Renames a node title on the chart
        async def _update_title(e):
            self.data['radar_data']['nodes'][e.control.data] = e.control.value
            await self.save_dict()
            chart.titles[e.control.data].text = e.control.value
            chart.update()

        # Deletes a node/title and the corresponding data for it in each data set
        async def _delete_title(e):
            del self.data['radar_data']['nodes'][e.control.data]
            for ds in self.data.get('radar_data', {}).get('data_sets', []):
                del ds['entries'][e.control.data]
            await self.save_dict()
            self.reload_widget()

        # Adds a new title to the end of our titles list
        async def _add_title(e):
            self.data['radar_data']['nodes'].append(f"Node {len(self.data['radar_data']['nodes']) + 1}")
            for ds in self.data.get('radar_data', {}).get('data_sets', []):
                ds['entries'].append(0)   # Add default value for new title to each data set
            await self.save_dict()
            self.reload_widget()

        # Toggles the chart either polygon or circle shaped
        async def _toggle_shape(e):
            if self.data['radar_data']['shape'] == "circle":
                self.data['radar_data']['shape'] = "polygon"
                chart.radar_shape = fch.RadarShape.POLYGON
                e.control.icon = ft.Icons.STAR_OUTLINE  
            else:
                self.data['radar_data']['shape'] = "circle"
                chart.radar_shape = fch.RadarShape.CIRCLE
                e.control.icon = ft.Icons.CIRCLE_OUTLINED
            await self.save_dict()
            e.control.update()
            chart.update()

        async def _add_data_set(e):
            self.data['radar_data']['data_sets'].append({
                'color': "primary",
                'entries': [2 for _ in self.data['radar_data']['nodes']],   # Default entries for each title/node
                'visible': True,
                'title': f"Data Set {len(self.data['radar_data']['data_sets']) + 1}",
                'expanded': True
            })
            await self.save_dict()
            self.reload_widget()

        async def _delete_data_set(e):
            idx = e.control.data
            del self.data['radar_data']['data_sets'][idx]
            await self.save_dict()
            self.reload_widget()

        async def _toggle_dataset_visibility(e):
            idx = e.control.data
            ds = self.data['radar_data']['data_sets'][idx]
            ds['visible'] = not ds.get('visible', True)
            await self.save_dict()
            self.reload_widget()

        async def _change_dataset_color(e):
            idx = e.control.data
            color = str(e.control.content)
            self.data['radar_data']['data_sets'][idx]['color'] = color
            await self.save_dict()
            self.reload_widget()

        titles = []
        for idx, title in enumerate(self.data.get('radar_data', {}).get('nodes', [])):
            titles.append(
                ft.Row([
                    TextField(
                        value=title, 
                        dense=True, data=idx, expand=True,
                        on_blur=_update_title,
                        suffix_icon=ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                            mouse_cursor="click", data=idx,
                            on_click=_delete_title
                        ) if idx >= 3 else None   # Minimum 3 nodes
                    ), ft.Container(width=1)
                ])
            )      

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
                    expanded
                )
            )


        info_column = ft.Column(
            [
                ft.Row([
                    ft.Text(f"\tNodes", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        self.data.get('color', ft.Colors.PRIMARY),
                        on_click=_add_title,
                        mouse_cursor=ft.MouseCursor.CLICK,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE, ft.Colors.ON_SURFACE_VARIANT, on_click=self._toggle_show_info, 
                        mouse_cursor=ft.MouseCursor.CLICK, bgcolor=ft.Colors.SURFACE_CONTAINER,
                    ),
                    ft.Container(width=11)
                    
                ], spacing=0)
            ] +
            titles + 
            [
                ft.Divider()
            ] +
            data_sets + 
            [
                
            ],
            expand=True, scroll="auto"
        )

        holder_column = ft.Column([
            info_column,
            ft.TextButton(
                ft.Text("Toggle Chart Shape", color=self.data.get('color', ft.Colors.PRIMARY), weight=ft.FontWeight.BOLD),
                ft.Icons.CIRCLE_OUTLINED if self.data.get('radar_data', {}).get('shape', "circle") == "circle" else ft.Icons.STAR_OUTLINE,
                self.data.get('color', ft.Colors.PRIMARY),
                on_click=_toggle_shape,
                style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK)
            )
        ], scroll="none")


        chart_info = ft.Container(
            expand=1,
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.only(left=11, top=8, bottom=8),
            shadow=ft.BoxShadow(0, 1),
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            content=holder_column
        )

        

        self.body_container.content = ft.Row(
            [
                chart,
                
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
        