""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.rail.plotline_dropdown import PlotlineDropdown
from styles.rail.mini_widget_item import MiniWidgetItem
from styles.menu_option_style import MenuOptionStyle
from models.isolated_controls.column import IsolatedColumn
from styles.rail.widget_rail_item import WidgetRailItem
from models.isolated_controls.list_view import IsolatedListView


# Class is created in main on program startup
class PlotlinesRail(Rail):

    # Constructor
    def __init__(self, page: ft.Page, story: Story):
        
        # Parent constructor
        super().__init__(
            page=page,
            story=story,
            directory_path=story.data.get('content_directory_path', '')
        )

        # Drop down we reference when adding new items to that dropdown
        self.active_dropdown: PlotlineDropdown = None

        # UI elements
        self.top_row_buttons = [
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
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"), 
                        tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
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

        self.reload_rail()

    
        
 

    # Called to return our list of menu options when right clicking on the plotline rail
    def get_menu_options(self) -> list[ft.Control]:
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
                        padding=ft.Padding.all(8), border_radius=ft.BorderRadius.all(6), shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    [
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, ft.Colors.PRIMARY), content="Plotline",
                            data="plotline", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                            tooltip="Create a new plotline to visualize and expand upon your sequence of events in your story"
                        ),
                        ft.MenuItemButton(
                            leading=ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Colors.PRIMARY), content="Plot Chart", 
                            data="plot_chart", on_click=self.new_item_clicked, close_on_click=True,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                            tooltip="New Items and Equipment for your story", 
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
    

    # Reload the rail whenever we need
    def reload_rail(self) -> ft.Control:
        ''' Reloads the plot and plotline rail, useful when switching stories '''

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

        menubar = ft.MenuBar(
            self.top_row_buttons,
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

        plotlines = [widget for widget in self.story.widgets.values() if widget.data.get('tag', "") == "plotline" or widget.data.get('tag', "") == "plot_chart"]
        plotlines.sort(key=lambda pl: pl.data.get('rail_index', 999))
        plotline_controls = [ft.ReorderableDragHandle(WidgetRailItem(pl)) for pl in plotlines]


        plotlines_list_view = ft.ReorderableListView(
            plotline_controls, 
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

                plotlines_list_view,

                ft.Container(expand=True)
            ] 
                
        )

        menu_gesture_detector = ft.GestureDetector(
            content=content, expand=True, on_hover=self._set_menu_coords,
            on_secondary_tap=lambda _: self.story.open_menu(self.get_menu_options()), 
            hover_interval=20,
        )

        self.controls = [
            header,
            ft.Divider(leading_indent=8),
            menu_gesture_detector
        ]

      

        # Apply the update
        try:
            self.update()
        except Exception:
            pass



