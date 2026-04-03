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

                'radar_data': {
                    'labels': [],   
                    'tick_count': 4,
                    'show_tick_labels': True,
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
        chart = fch.RadarChart(
            expand=True,
            titles=[
                fch.RadarChartTitle(text="Title 1"), 
                fch.RadarChartTitle(text="Title 2"), 
                fch.RadarChartTitle(text="Title 3"), 
                fch.RadarChartTitle(text="Title 4"),
                fch.RadarChartTitle(text="Title 5")
            ],
            center_min_value=True,
            tick_count=4,
            ticks_text_style=ft.TextStyle(size=16, color=ft.Colors.ON_SURFACE_VARIANT, italic=True),
            title_text_style=ft.TextStyle(
                size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,
            ),
            on_event=self._radar_chart_event,
            animation=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            title_position_percentage_offset=0.05,
            data_sets=[
                fch.RadarDataSet(
                    fill_color=ft.Colors.with_opacity(0.2, ft.Colors.DEEP_PURPLE),
                    border_color=ft.Colors.DEEP_PURPLE,
                    entry_radius=4,
                    entries=[
                        fch.RadarDataSetEntry(300),
                        fch.RadarDataSetEntry(50),
                        fch.RadarDataSetEntry(250),
                        fch.RadarDataSetEntry(250),
                        fch.RadarDataSetEntry(250),
                    ],
                ),
                fch.RadarDataSet(
                    fill_color=ft.Colors.with_opacity(0.15, ft.Colors.PINK),
                    border_color=ft.Colors.PINK,
                    entry_radius=4,
                    entries=[
                        fch.RadarDataSetEntry(250),
                        fch.RadarDataSetEntry(100),
                        fch.RadarDataSetEntry(200),
                        fch.RadarDataSetEntry(250),
                        fch.RadarDataSetEntry(250),
                    ],
                ),
                fch.RadarDataSet(
                    fill_color=ft.Colors.with_opacity(0.12, ft.Colors.CYAN),
                    border_color=ft.Colors.CYAN,
                    entry_radius=4,
                    entries=[
                        fch.RadarDataSetEntry(200),
                        fch.RadarDataSetEntry(150),
                        fch.RadarDataSetEntry(50),
                        fch.RadarDataSetEntry(250),
                        fch.RadarDataSetEntry(250),
                    ],
                ),
            ],
            
            
        )

        self.body_container.content = chart

        

    # Called after any changes happen to the data that need to be reflected in the UI, usually just ones that require a rebuild
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: RADAR -- 
        # Adjust the number of datasetentrys for the entire chart
        # Ability to interact with chart using mouse cursor?
        # Can Add Groups/data sets. Can change their color as well. Toggle them visible or not
        # Toggle labels on and off
        # Adjust number of ticks, and if they should show their labels or not. Usee ft.Text and two up/down buttons
        # Show chart as circle or polygon (toggle)
        # Change titles/labels 

        # BAR --


        # Rebuild out tab to reflect any changes
        self.reload_tab()

        if self.data.get('type', "") == "bar":
            self._bar_chart_view()
        else:
            self._radar_chart_view()
        
        #self.body_container.content = ft.Text("Chart: " + self.title, size=20)
        
        # Build in widget function that will handle loading our mini widgets and rendering the whole thing
        self._render_widget()
        