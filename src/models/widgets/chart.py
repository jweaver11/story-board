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
                    'data_sets': [      # The data sets that make up the radar chart
                        {
                            'color': "primary",
                            'entries': [10, 5, 10, 5, 10],   # The values for each title/axis of the radar chart
                            'visible': True,
                            'title': "Data Set 1"
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

    async def _radar_chart_event(self, e):
        return
        print(e)
        

    def _radar_chart_view(self):
        ''' Builds out the body of our radar chart widget '''

        # TODO: RADAR -- 
        # Adjust the number of datasetentrys for the entire chart
        # Ability to interact with chart using mouse cursor?
        # Can Add Groups/data sets. Can change their color as well. Use Block Picker. Toggle them visible or not
        # Show chart as circle or polygon (toggle)
        
        chart = fch.RadarChart(
            expand=2,
            titles=[fch.RadarChartTitle(text=title) for title in self.data.get('radar_data', {}).get('nodes', [])],
            center_min_value=False,
            ticks_text_style=ft.TextStyle(size=16, color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
            title_text_style=ft.TextStyle(
                size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,
            ),
            on_event=self._radar_chart_event,
            animation=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            title_position_percentage_offset=0.05,
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


        titles = []
        for idx, title in enumerate(self.data.get('radar_data', {}).get('nodes', [])):
            titles.append(
                ft.Row([
                    TextField(
                        value=title, multiline=True,
                        dense=True, data=idx, expand=True,
                        on_blur=_update_title,
                        suffix_icon=ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, ft.Colors.ERROR, 
                            mouse_cursor="click", data=idx,
                            on_click=_delete_title
                        ) if idx >= 3 else None   # Minimum 3 nodes
                    )
                ])
            )      

        data_sets = [] 
        for idx, ds in enumerate(self.data.get('radar_data', {}).get('data_sets', [])):
            color = ds.get('color', "primary")
            entries: list = ds.get('entries', [])
            visible: bool = ds.get('visible', True)
            title: str = ds.get('title', "Data Set")
            data_sets.append(
                TextField(
                    title,
                    multiline=True,
                    dense=True, data=idx, expand=True,
                    icon=ft.IconButton(
                        ft.Icons.VISIBILITY_OUTLINED if visible else ft.Icons.VISIBILITY_OFF_OUTLINED,
                        color if visible else ft.Colors.ON_SURFACE_VARIANT,
                        # on click = toggle visb
                        mouse_cursor=ft.MouseCursor.CLICK, data=idx,
                    ),
                    prefix_icon=ft.PopupMenuButton(ft.Icon(ft.Icons.COLOR_LENS_OUTLINED)),
                    #suffix_icon=delete_button
                )
            )

        info_column = ft.Column(
            [
                ft.Row([
                    ft.Text(f"\tTitles", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None)),
                    ft.TextButton(
                        "Add Node", ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                        on_click=_add_title,
                        style=ft.ButtonStyle(self.data.get('color', ft.Colors.PRIMARY), icon_size=18, mouse_cursor=ft.MouseCursor.CLICK, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14)),
                    ),
                    ft.TextButton(
                        "Toggle Chart Shape",
                        ft.Icons.CIRCLE_OUTLINED if self.data.get('radar_data', {}).get('shape', "circle") == "circle" else ft.Icons.STAR_OUTLINE,
                        self.data.get('color', ft.Colors.PRIMARY),
                        on_click=_toggle_shape,
                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK)
                    )
                ], spacing=0)
            ] +
            titles + 
            [
                ft.Divider()
            ] +
            data_sets,
            expand=True
        )


        chart_info = ft.Container(
            expand=1,
            border_radius=ft.BorderRadius.all(10),
            border=ft.Border.all(2, ft.Colors.SECONDARY_CONTAINER),
            padding=ft.Padding.all(8),
            bgcolor=ft.Colors.with_opacity(.7, ft.Colors.SURFACE),
            blur=5,
            content=info_column
        )

        self.body_container.content = ft.Row([chart, chart_info], expand=True)

        

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
        