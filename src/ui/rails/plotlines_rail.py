""" WIP """

import flet as ft
from models.views.story import Story
from ui.rails.rail import Rail
from styles.plotlines.plotline_dropdown import PlotlineDropdown
from styles.plotlines.label_dropdown import LabelDropdown
from styles.plotlines.plotline_item import PlotlineItem
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
            ft.PopupMenuButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED,
                tooltip="New", menu_padding=0,
                items=[
                    ft.PopupMenuItem(
                        text="plotline", icon=ft.Icons.TIMELINE_OUTLINED,
                        on_click=self.new_item_clicked, data="plotline"
                    ),
                    ft.PopupMenuItem(
                        text="Plot Point", icon=ft.Icons.ADD_LOCATION_OUTLINED,
                        on_click=self.new_item_clicked, data="plot_point"
                    ),
                    ft.PopupMenuItem(
                        text="Arc", icon=ft.Icons.CIRCLE_OUTLINED,
                        on_click=self.new_item_clicked, data="arc"
                    ),
                    ft.PopupMenuItem(
                        text="Marker", icon=ft.Icons.FLAG_OUTLINED,
                        on_click=self.new_item_clicked, data="marker"
                    )
                ]
            ),
            ft.IconButton(
                icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                tooltip="Upload Plotline", disabled=False,
                on_click=lambda e: print(""),
            ),
        ]
 
        

    # Called to return our list of menu options when right clicking on the plotline rail
    def get_menu_options(self) -> list[ft.Control]:
        ''' Returns our menu options for the plotlines rail. In this case just plotlines '''

        if len(self.story.plotlines) == 1:
            return [
                MenuOptionStyle(
                    content=ft.PopupMenuButton(
                        content=ft.Container(
                            ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                            padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                        ),
                        tooltip="New", menu_padding=0,
                        items=[
                            ft.PopupMenuItem(
                                text="plotline", icon=ft.Icons.TIMELINE_OUTLINED,
                                on_click=self.new_item_clicked, data="plotline"
                            ),  
                            ft.PopupMenuItem(
                                text="Plot Point", icon=ft.Icons.ADD_LOCATION_OUTLINED,
                                on_click=self.new_item_clicked, data="plot_point"
                            ),
                            ft.PopupMenuItem(
                                text="Arc", icon=ft.Icons.CIRCLE_OUTLINED,
                                on_click=self.new_item_clicked, data="arc"
                            ),
                            ft.PopupMenuItem(
                                text="Marker", icon=ft.Icons.FLAG_OUTLINED,
                                on_click=self.new_item_clicked, data="marker"
                            )
                        ]
                    ),
                    no_padding=True
                ),
                MenuOptionStyle(
                    content=ft.PopupMenuButton(
                        content=ft.Container(
                            ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED), ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                            padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                        ),
                        tooltip="Upload", menu_padding=0,
                        items=[ft.PopupMenuItem(text="Plotline", icon=ft.Icons.TIMELINE_OUTLINED,)]
                    ),
                    no_padding=True
                )
            ]

        else:
            return [
                MenuOptionStyle(
                    content=ft.PopupMenuButton(
                        content=ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                        tooltip="New", menu_padding=0,
                        items=[
                            ft.PopupMenuItem(
                                text="Plotline", icon=ft.Icons.TIMELINE_OUTLINED,
                                on_click=self.new_item_clicked, data="plotline"
                            ),  
                        ]
                    ),
                ),
                MenuOptionStyle(
                    content=ft.PopupMenuButton(
                        content=ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD_OUTLINED), ft.Text("Upload", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                        tooltip="Upload", menu_padding=0,
                        items=[ft.PopupMenuItem(text="Plotline", icon=ft.Icons.TIMELINE_OUTLINED,)]
                    ),
                )
            ]
    
    # Called when right clicking a plotline, arc, or the arc/plot point drop downs
    def get_sub_menu_options(self, tag: str=None, is_label: bool=False) -> list[ft.Control]:
        ''' Returns the menu options for our sub items based on its tag '''

        # List we will return at end function
        options = []

        # Depending on what tag we have, return different options. Plot points label just gets plot point option
        if tag == "plot_points_label" and is_label:
            options.append(
                # Create plot point button
                MenuOptionStyle(
                    data="plot_point",
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD_LOCATION_OUTLINED),
                        ft.Text("Plot Point", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                    ])
                ),
            )

        # Arcs label just gets arc option
        elif tag == "arcs_label" and is_label:
            options.append(
                # Create arc button
                MenuOptionStyle(
                    data="arc",
                    content=ft.Row([
                        ft.Icon(ft.Icons.CIRCLE_OUTLINED),
                        ft.Text("Arc", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                    ])
                ),
            )

        else:
            options.extend([
                MenuOptionStyle(
                    content=ft.PopupMenuButton(
                        content=ft.Row([ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE_OUTLINED), ft.Text("New", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)]),
                        tooltip="New", menu_padding=0,
                        items=[
                            ft.PopupMenuItem(
                                text="Plot Point", icon=ft.Icons.ADD_LOCATION_OUTLINED,
                                on_click=self.new_item_clicked, data="plot_point"
                            ),  
                            ft.PopupMenuItem(
                                text="Arc", icon=ft.Icons.ADD_CIRCLE_OUTLINED,
                                on_click=self.new_item_clicked, data="arc"
                            ), 
                        ]
                    ),
                ),
            ])

        return options
    
    # Refreshes our top row buttons based on our active dropdown
    def refresh_buttons(self, no_active_dropdown: bool=False):
        ''' Refreshes the top row buttons based on our active dropdown/plotline to update our colors and disabled states '''

        # When clicking on the rail, get rid of our active dropdown
        if no_active_dropdown and len(self.story.plotlines) != 1:
            self.active_dropdown = None

        # Next, see if our dropdown is just a label. If it is, make the plotline_dropdown it sits inside as our active dropdown
        # We do this so we can add plot points and arcs even from the opposite label dropdown
        if self.active_dropdown is not None:
            if isinstance(self.active_dropdown, LabelDropdown):
                self.active_dropdown = self.active_dropdown.plotline_dropdown

        # Go through each button and update their color, disabled state, and on click function
        for i, button in enumerate(self.top_row_buttons):

            # Skip the plotlines button, its always active and needs no changes
            if i == 0:
                continue

            else:
                
                # Color is primary if we have an active dropdown, otherwise its grey-ish
                button.icon_color = ft.Colors.PRIMARY if self.active_dropdown is not None else ft.Colors.ON_SURFACE_VARIANT

                # Button is disabled if no active dropdown and more than one plotline
                button.disabled = self.active_dropdown is None and len(self.story.plotlines) != 1

                # On click function goes to active dropdown logic if we have one, otherwise goes to rail logic
                button.on_click = self.active_dropdown.new_item_clicked if self.active_dropdown is not None else self.new_item_clicked
    
        # Finally, update the page
        self.p.update()
           


    # Reload the rail whenever we need
    def reload_rail(self) -> ft.Control:
        ''' Reloads the plot and plotline rail, useful when switching stories '''

        # WHEN CREATING NEW PP OR ARC, ADD IT DEFAULT TO MIDDLE OF plotline AND BE ABLE TO BE DRAGGED AROUND

        self.refresh_buttons()

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
            plotline.plotline_dropdown = PlotlineDropdown(
                title=plotline.title, 
                story=self.story, 
                plotline=plotline, 
                additional_menu_options=self.get_sub_menu_options(),
                rail=self
            )

            # Create our plotline dropdowns here in 

            # Load our plotline data
            # New drop down for our plotpoints
            plot_points_dropdown = LabelDropdown(
                title="Plot Points",
                story=self.story,
                additional_menu_options=self.get_sub_menu_options(tag="plot_points_label", is_label=True),
                plotline=plotline,
                rail=self,
                plotline_dropdown=plotline.plotline_dropdown
            )

        
            # Go through our plotpoints from our plotline, and add each item
            for plot_point in plotline.plot_points.values():
                plot_points_dropdown.content.controls.append(
                    PlotlineItem(title=plot_point.title, mini_widget=plot_point)
                )

            plot_points_dropdown.content.controls.append(plot_points_dropdown.new_item_textfield)

            # Add our plot points dropdown to the plotline dropdown
            plotline.plotline_dropdown.content.controls.append(plot_points_dropdown)

            # New drop down for our arcs
            arcs_dropdown = LabelDropdown(
                title="Arcs",
                story=self.story,
                additional_menu_options=self.get_sub_menu_options(tag="arcs_label", is_label=True),
                plotline=plotline,
                rail=self,
                plotline_dropdown=plotline.plotline_dropdown
            )
            

            # Go through all the arcs/sub arcs held in our parent arc or plotline
            for arc in plotline.arcs.values():

                arcs_dropdown.content.controls.append(
                    PlotlineItem(title=arc.title, mini_widget=arc)
                )

            arcs_dropdown.content.controls.append(arcs_dropdown.new_item_textfield)


            # Add our arcs dropdown to the plotline dropdown
            plotline.plotline_dropdown.content.controls.append(arcs_dropdown)


            # If theres only one plotline, no need to add the parent expansion to the page.
            if len(self.story.plotlines) == 1:

                # If only one plotline, just add its content directly to the rail rather than making it a dropdown
                content.controls.extend(plotline.plotline_dropdown.content.controls)

                # Set our active_dropdown if we only have one
                self.active_dropdown = plotline.plotline_dropdown

            # Otherwise, add the full expansion panel
            else:
                content.controls.append(plotline.plotline_dropdown)
    
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

        # Make sure our buttons are refreshed
        self.refresh_buttons()

        # Apply the changes to the page
        self.p.update()


    
