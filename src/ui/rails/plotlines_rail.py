""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.rail.plotline_dropdown import PlotlineDropdown
from styles.rail.mini_widget_item import MiniWidgetItem
from styles.menu_option_style import MenuOptionStyle
from models.isolated_controls.column import IsolatedColumn


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
            ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="Create New Plotline", 
                on_click=self.new_item_clicked, data="plotline"
            ),
            ft.IconButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload Plotline",
                #on_click=lambda e: print(""),
            ),
        ]

        self.reload_rail()

    # Called when we reorder our plotlines on the rail
    async def _handle_plotline_reorder(self, e):
        ''' Handles the reordering and reloading of plotlines based on their new positions on the rail when we drag and drop them '''
        old_index = e.old_index
        new_idx = e.new_index

        # Find which plotline we dragged
        for widget in self.story.widgets:
            if widget.data.get('tag', "") == "plotline" and widget.data.get('rail_index', 0) == old_index:
                dragged_plotline = widget
                break
        # Set its new index
        dragged_plotline.data['rail_index'] = new_idx
        dragged_plotline.save_dict()

        # If we didn't move, return out
        if old_index == new_idx:
            return
        
        # If we dragged down
        elif old_index < new_idx:
            for widget in self.story.widgets:
                if widget.data.get('rail_index', 0) > old_index and widget.data.get('rail_index', 0) <= new_idx and widget != dragged_plotline:
                    widget.data['rail_index'] -= 1
                    widget.save_dict()
        
        # If we dragged up
        elif old_index > new_idx:
            for widget in self.story.widgets:
                if widget.data.get('rail_index', 0) >= new_idx and widget.data.get('rail_index', 0) < old_index and widget != dragged_plotline:
                    widget.data['rail_index'] += 1
                    widget.save_dict()
                
        # Apply our changes
        self.reload_rail()
 

    # Called to return our list of menu options when right clicking on the plotline rail
    def get_menu_options(self) -> list[ft.Control]:
        ''' Returns our menu options for the plotlines rail. In this case just plotlines '''

        return [
            MenuOptionStyle(
                ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED, tooltip="Create New Plotline"),
                    ft.Text("New Plotline", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ]),
                on_click=self.new_item_clicked, data="plotline",
            ),
            MenuOptionStyle(
                ft.Row([
                    ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED, tooltip="Upload Plotline"),
                    ft.Text("Upload Plotline", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                ]),
                #on_click=self.new_item_clicked, data="plotline", 
            )
        ]
    

    # Reload the rail whenever we need
    def reload_rail(self) -> ft.Control:
        ''' Reloads the plot and plotline rail, useful when switching stories '''

        header = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=self.top_row_buttons
        )

        # Build the content of our rail
        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[]
        )

        # Reorderable List for our plotlines on the rail
        reorderable_plotlines = ft.ReorderableListView(show_default_drag_handles=False, on_reorder=self._handle_plotline_reorder)

        # Sort our plotlines by their index
        plotlines_list = [w for w in self.story.widgets if w.data.get('tag', "") == "plotline"]
        sorted_plotlines = sorted(plotlines_list, key=lambda plotline: plotline.data.get('rail_index', 0))

        i = 0   # Start index for our plotlines

        # Run through each plotline in the story
        for plotline in sorted_plotlines:
            
            # Build a column for our dropdown, and a divider under it to seperate each plotline
            column = ft.Column(expand=False, spacing=0)

            # Create an expansion tile for our plotline that we need in order to load its data
            dropdown = PlotlineDropdown(
                title=plotline.title, 
                story=self.story, 
                plotline=plotline, 
                rail=self
            )

            # Sort our mini widgets by start earliest to latest
            sorted_plot_points = dict(sorted(plotline.plot_points.items(), key=lambda item: item[1].data.get('left', 0)))  
            sorted_arcs = dict(sorted(plotline.arcs.items(), key=lambda item: item[1].data.get('left', 0)))
            sorted_markers = dict(sorted(plotline.markers.items(), key=lambda item: item[1].data.get('left', 0)))

            # Add a label for our plotpoints section in the dropdown
            dropdown.expansion_tile.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.LOCATION_PIN),
                    ft.Text("Plot Points", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD)
                ])
            )
            dropdown.expansion_tile.controls.append(ft.Container(height=4))   # Spacer
            # Go through our plotpoints from our plotline, and add each item
            for plot_point in sorted_plot_points.values():
                dropdown.expansion_tile.controls.append(MiniWidgetItem(plot_point))
            dropdown.expansion_tile.controls.append(ft.Divider())   # Divider between our plot points and arcs sections

            # Arcs label
            dropdown.expansion_tile.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.CIRCLE_OUTLINED),
                    ft.Text("Arcs", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD)
                ])
            )
            dropdown.expansion_tile.controls.append(ft.Container(height=4))   # Spacer
            # Go through all the arcs/sub arcs held in our parent arc or plotline
            for arc in sorted_arcs.values():
                dropdown.expansion_tile.controls.append(MiniWidgetItem(arc))
            dropdown.expansion_tile.controls.append(ft.Divider())       # Divider between our arcs and markers sections

            # Markers label
            dropdown.expansion_tile.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.FLAG_OUTLINED),
                    ft.Text("Markers", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD)
                ])
            )
            dropdown.expansion_tile.controls.append(ft.Container(height=4))   # Spacer
            # Go through all the markers held in our plotline and add them to the dropdown
            for marker in sorted_markers.values():
                dropdown.expansion_tile.controls.append(MiniWidgetItem(marker))

            # Set the plotlines dropdown to the one we have just built for it
            plotline.plotline_dropdown = dropdown

            # Add the dropdown as a reorderable element for the list
            column.controls.append(
                ft.ReorderableDragHandle(dropdown)
            )
            i += 1      # Increment index
            column.controls.append(ft.Divider())    # Add a divider under the plotline for visual seperation

            # Add the column to the reorderable list view controls
            reorderable_plotlines.controls.append(column)

        

        # Finally, add our new item textfield at the bottom
        content.controls.append(reorderable_plotlines)
        content.controls.append(self.new_item_textfield)
        

        # Gesture detector to put on top of stack on the rail to pop open menus on right click
        menu_gesture_detector = ft.GestureDetector(
            content=content, expand=True,
            on_hover=self._set_menu_coords,
            on_secondary_tap=lambda _: self.story.open_menu(self.get_menu_options()),
            hover_interval=20,
        )

        # Set our content to be a column
        self.content = IsolatedColumn(
            spacing=0,
            expand=True,
            controls=[
                header,
                ft.Divider(),
                menu_gesture_detector
            ]
        )


        self.controls = [
            #header,
            #ft.Divider(),
            ft.Text("Coming Soon")
            #menu_gesture_detector
        ]

      

        # Apply the update
        try:
            self.update()
        except Exception:
            pass



