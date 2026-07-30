""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.menu_option_style import MenuOptionStyle
from models.isolated_controls.column import IsolatedColumn
from styles.rail.widget_rail_item import WidgetRailItem
from models.isolated_controls.list_view import IsolatedListView


# Class is created in main on program startup
class PlotlinesRail(Rail):

    # Constructor
    def __init__(self, story: Story):
        
        # Parent constructor
        super().__init__(story=story)

         
 

    # Called to return our list of menu options when right clicking on the plotline rail
    def get_new_item_menu_options(self) -> list[ft.Control]:
        ''' Returns our menu options for the plotlines rail. In this case just plotlines '''

        return [
           MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                    [
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                            data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Colors.PRIMARY), content="Plot Chart", 
                            data="plot_chart", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                            tooltip="New Items and Equipment for your story", 
                        ),  
                        ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True
            ),

            # Upload options
            MenuOptionStyle(
                content=ft.SubmenuButton(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.IMPORT_EXPORT_OUTLINED, ft.Colors.PRIMARY), 
                            ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Icon(ft.Icons.ARROW_RIGHT),
                        ], expand=True),
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                    [
                        
                    ],
                    menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                    style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                ),
                no_padding=True, no_effects=True, 
            ),
        ]
    

    # Reload the rail whenever we need
    def build(self) -> ft.Control:
        ''' Reloads the plot and plotline rail, useful when switching stories '''

        async def _change_sort_method(e: ft.Event):
            new_sort_method = e.data
            self.story.data['plotline_rail_sort_method'] = new_sort_method
            await self.story.save_dict()
            self.story.active_rail.reload_rail()

        async def _change_sort_direction(e: ft.Event):

            old_sort_method = self.story.data.get('plotline_rail_sort_direction', "Ascending")
            if old_sort_method == "Ascending":
                self.story.data['plotline_rail_sort_direction'] = "Descending"
                e.control.tooltip = "Sort Direction: Descending"
                e.control.icon = ft.CupertinoIcons.SORT_UP
            else:
                self.story.data['plotline_rail_sort_direction'] = "Ascending"
                e.control.tooltip = "Sort Direction: Ascending"
                e.control.icon = ft.CupertinoIcons.SORT_DOWN

            await self.story.save_dict()

            plotlines_list_view.reverse = self.story.data.get('plotline_rail_sort_direction', "Ascending") == "Descending"
            plot_charts_list_view.reverse = self.story.data.get('plotline_rail_sort_direction', "Ascending") == "Descending"
            plot_charts_list_view.update()
            plotlines_list_view.update()
            e.control.update()

        async def _reorder_widget(e: ft.OnReorderEvent):
            ''' Handles the reordering and reloading of characters based on their new positions on the rail when we drag and drop them '''
            
            # If we didn't move, return out
            if e.old_index == e.new_index:
                return
            
            # Move the control up the list
            e.control.controls.insert(e.new_index, e.control.controls.pop(e.old_index))
            e.control.update()

            # Update the indices of the characters we dragged past as well
            for idx, ctrl in enumerate(e.control.controls):
                widget = ctrl.content.widget
                if widget.data.get('rail_index', 999) != idx:
                    widget.data['rail_index'] = idx 
                    await widget.save_dict()

        top_row_buttons = [
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, "primary"),
                    shape=ft.BoxShape.CIRCLE,
                    alignment=ft.Alignment.CENTER
                ),
                [
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                        data="plotline", on_click=self.new_item_clicked, close_on_click=True, 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"), 
                        tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                    ),
                    ft.MenuItemButton(
                        leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Colors.PRIMARY), content="Plot Chart", 
                        data="plot_chart", on_click=self.new_item_clicked, close_on_click=True,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                        tooltip="New Items and Equipment for your story", 
                    ),  
                ],
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
            ft.SubmenuButton(
                ft.Container(
                    ft.Icon(ft.Icons.IMPORT_EXPORT_OUTLINED, ft.Colors.OUTLINE),
                    shape=ft.BoxShape.CIRCLE,
                    alignment=ft.Alignment.CENTER
                ),
                [     
                    
                ],
                disabled=True,
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
                style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.CircleBorder(), alignment=ft.Alignment.CENTER, mouse_cursor="click"),
            ),
        ]

        menubar = ft.MenuBar(
            top_row_buttons,
            style=ft.MenuStyle(
                bgcolor="transparent", shadow_color="transparent",
                shape=ft.RoundedRectangleBorder(radius=4),
            ), 
        )

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[menubar]
        )

        plotlines = [widget for widget in self.story.widgets.values() if widget.data.get('tag', "") == "plotline"]
        plotlines.sort(key=lambda pl: pl.data.get('rail_index', 999))
        plotline_controls = [ft.ReorderableDragHandle(WidgetRailItem(pl)) for pl in plotlines]

        plot_charts = [widget for widget in self.story.widgets.values() if widget.data.get('tag', "") == "plot_chart"]
        plot_charts.sort(key=lambda pl: pl.data.get('rail_index', 999))
        plot_chart_controls = [ft.ReorderableDragHandle(WidgetRailItem(pl)) for pl in plot_charts]


        plotlines_list_view = ft.ReorderableListView(
            plotline_controls,
            on_reorder=_reorder_widget, 
            spacing=0, show_default_drag_handles=False, 
        )

        plot_charts_list_view = ft.ReorderableListView(
            plot_chart_controls, expand=True,
            on_reorder=_reorder_widget,
            spacing=0, show_default_drag_handles=False,
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

                ft.Text("\tPlotlines", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),

                plotlines_list_view,
                ft.Divider(),
                ft.Text("\tPlot Charts", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD, italic=True, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                plot_charts_list_view,

                ft.Container(expand=True)
            ] 
                
        )

        menu_gesture_detector = ft.GestureDetector(
            content=content, expand=True, on_hover=self._set_menu_coords,
            on_secondary_tap=lambda _: self.story.open_menu(self.get_new_item_menu_options()), 
            hover_interval=20,
        )

        sort_dropdown = ft.Dropdown(
            self.story.data.get('plotline_rail_sort_method', "Index"),
            [
                ft.DropdownOption(
                    "Default", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4)),
                    tooltip="Sort world building widgets by the order they were loaded. On Windows, usually alphabetical. On Mac, usually by creation date."
                ),
                ft.DropdownOption(
                    "Index", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4)),
                    tooltip="Sort world building widgets by a reorderable index so you can drag them up and down on the rail."
                ), 
                ft.DropdownOption(
                    "Color", style=ft.ButtonStyle(mouse_cursor="click", shape=ft.RoundedRectangleBorder(radius=4)),
                    tooltip="Sort world building widgets by their color."
                )
            ],
            label="Sort by",
            dense=True, expand=True,
            on_select=_change_sort_method,
            border_color=ft.Colors.OUTLINE_VARIANT,
            leading_icon=ft.IconButton(
                ft.CupertinoIcons.SORT_DOWN if self.story.data.get('plotline_rail_sort_direction', "Ascending") == "Ascending" else ft.CupertinoIcons.SORT_UP,
                ft.Colors.PRIMARY, 
                tooltip=f"Sort Direction: {self.story.data.get('plotline_rail_sort_direction', 'Ascending')}", 
                on_click=_change_sort_direction, mouse_cursor="click", 
            ),
            menu_style=ft.MenuStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=4)),
        )

        self.controls = [
            header,
            ft.Divider(thickness=2, leading_indent=8),
            menu_gesture_detector,
            ft.Row([sort_dropdown], margin=ft.Margin.only(left=8))
        ]

      



