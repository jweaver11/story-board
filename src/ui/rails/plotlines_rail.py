""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.rail.plotline_dropdown import PlotlineDropdown
from styles.rail.mini_widget_item import MiniWidgetItem
from styles.menu_option_style import MenuOptionStyle


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
                    ft.Text("Upload\nPlotline", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
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


        

        # Run through each plotline in the story
        for plotline in self.story.plotlines.values():

            # Create an expansion tile for our plotline that we need in order to load its data
            dropdown = PlotlineDropdown(
                title=plotline.title, 
                story=self.story, 
                plotline=plotline, 
                rail=self
            )

            # Sort our mini widgets
            sorted_plot_points = dict(sorted(plotline.plot_points.items(), key=lambda item: item[1].data.get('left', 0)))  
            sorted_arcs = dict(sorted(plotline.arcs.items(), key=lambda item: item[1].data.get('left', 0)))
            sorted_markers = dict(sorted(plotline.markers.items(), key=lambda item: item[1].data.get('left', 0)))

            dropdown.expansion_tile.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.LOCATION_PIN),
                    ft.Text("Plot Points", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD)
                ])
            )

            # Go through our plotpoints from our plotline, and add each item
            for plot_point in sorted_plot_points.values():
                dropdown.expansion_tile.controls.append(MiniWidgetItem(plot_point))

            dropdown.expansion_tile.controls.append(ft.Divider())
            dropdown.expansion_tile.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.CIRCLE_OUTLINED),
                    ft.Text("Arcs", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD)
                ])
            )

            # Go through all the arcs/sub arcs held in our parent arc or plotline
            for arc in sorted_arcs.values():
                dropdown.expansion_tile.controls.append(MiniWidgetItem(arc))

            dropdown.expansion_tile.controls.append(ft.Divider())
            dropdown.expansion_tile.controls.append(
                ft.Row([
                    ft.Icon(ft.Icons.FLAG_OUTLINED),
                    ft.Text("Markers", theme_style=ft.TextThemeStyle.LABEL_LARGE, weight=ft.FontWeight.BOLD)
                ])
            )

            for marker in sorted_markers.values():
                dropdown.expansion_tile.controls.append(MiniWidgetItem(marker))


            # Add our arcs dropdown to the plotline dropdown
            #plotline.plotline_dropdown.content.controls.append()
            plotline.plotline_dropdown = dropdown
            content.controls.append(plotline.plotline_dropdown)
            content.controls.append(ft.Divider())
    
        content.controls.append(ft.Container(height=6))

        # Finally, add our new item textfield at the bottom
        content.controls.append(self.new_item_textfield)

        # Gesture detector to put on top of stack on the rail to pop open menus on right click
        menu_gesture_detector = ft.GestureDetector(
            content=content,
            expand=True,
            on_hover=self.on_hovers,
            on_secondary_tap=lambda e: self.story.open_menu(self.get_menu_options()),
            hover_interval=20,
        )

        # Set our content to be a column
        self.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                header,
                ft.Divider(),
                menu_gesture_detector
            ]
        )

      

        # Apply the changes to the page
        self.p.update()


    
