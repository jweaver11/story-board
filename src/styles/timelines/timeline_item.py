import flet as ft
from styles.timelines.timeline_dropdown import TimelineDropdown
from models.mini_widget import MiniWidget
from styles.menu_option_style import MenuOptionStyle
from models.mini_widgets.timelines.plot_point import PlotPoint
from styles.colors import colors


# RAIL ITEMS FOR PLOTPOINTS AND ARCS
class TimelineItem(ft.GestureDetector):
    
    # Constructor
    def __init__(
        self, 
        mini_widget: MiniWidget, 
        title: str,
        icon: ft.Icon = None,
        #father: Timeline = None,
        dir_dropdown: TimelineDropdown = None,
        additional_menu_options: list[ft.Control] = None
    ):
        
         
        # Set our widget reference and tag
        self.mini_widget = mini_widget
        self.title = title
        self.color = self.mini_widget.data.get('color', ft.Colors.PRIMARY)
        self.additional_menu_options = additional_menu_options
        

        # Check if we're a plot point or an arc for icon purposes
        if isinstance(self.mini_widget, PlotPoint): 
            self.tag = "plot_point"
        else:
            self.tag = "arc"


        if self.tag == "plot_point":
            self.icon = ft.Icons.LOCATION_ON_OUTLINED

        else:
            self.icon = ft.Icons.CIRCLE_OUTLINED

        if icon is not None:
            self.icon = icon
            

        # Set our text style
        self.text_style = ft.TextStyle(
            size=14,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.BOLD,
        )

        # Get icon color from widget data if it exists
        #self.icon_color = mini_widget.data.get('color', 'primary')

        # Parent constructor
        super().__init__(
            on_enter = self.on_hover,
            on_exit = self.on_stop_hover,
            on_secondary_tap = lambda e: self.mini_widget.owner.story.open_menu(self.get_menu_options()),
            on_tap = lambda e: self.mini_widget.toggle_visibility(value=True),    # Open up timeline if not opened, focus our mini widget
            mouse_cursor = ft.MouseCursor.CLICK,
        )


        self.reload()
    
    # Called when this item is right clicked
    def get_menu_options(self) -> list[ft.Control]:
        ''' Pops open a column of the menu options for this tree view item'''

        
        # Rename button
        menu_options = [
            MenuOptionStyle(
                on_click=self.rename_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    expand=True,
                    tooltip="",
                    padding=ft.Padding(0,0,0,0),
                    content=ft.Row(
                        expand=True,
                        controls=[
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=ft.Colors.PRIMARY),
                            ft.Text("Color", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True), 
                            ft.Icon(ft.Icons.ARROW_RIGHT_OUTLINED, color=ft.Colors.ON_SURFACE, size=16),
                        ]
                    ),
                    items=self.get_color_options()
                ),
            ),
            MenuOptionStyle(
                on_click=lambda e: self.delete_clicked(e),
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]
        
        # Run through our additional menu options if we have any, and set their on_click methods
        #for option in self.additional_menu_options or []:

            # Set their on_click to call our on_click method, which can handle any type of widget
            #option.on_tap = lambda e, t=option.data: self.father.new_item_clicked(type=t)

            # Add them to the list
            #menu_options.append(option)



        return menu_options


    # Called when hovering mouse over a tree view item
    def on_hover(self, e):
        self.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
        self.mini_widget.p.update()

    # Called when stopping hover over a tree view item
    def on_stop_hover(self, e):
        self.content.bgcolor = ft.Colors.TRANSPARENT
        self.mini_widget.p.update()

    # Called when rename button is clicked
    def rename_clicked(self, e):
        
        # TODO: Edit rename to fit arcs

        # Track if our name is unique for checks, and if we're submitting or not
        is_unique = True
        submitting = False

        # Grab our current name for comparison
        current_name = self.mini_widget.title.lower()

        # Called when clicking outside the input field to cancel renaming
        def _cancel_rename(e):
            ''' Puts our name back to static and unalterable '''

            # Grab our submitting state
            nonlocal submitting

            # Since this auto calls on submit, we need to check. If it is cuz of a submit, do nothing
            if submitting:
                submitting = not submitting     # Change submit status to False so we can de-select the textbox
                return
            
            # Otherwise we're not submitting (just clicking off the textbox), so we cancel the rename
            else:

                self.reload()
                self.mini_widget.p.update()

        # Called everytime a change in textbox occurs
        def _name_check(e):
            ''' Checks if the name is unique within its type of widget '''

            # Grab the new name, and tag
            name = e.control.value.lower()
            tag = self.mini_widget.data.get('tag', None)

            # Nonlocal variables
            nonlocal is_unique
            nonlocal submitting

            # Set submitting to false, and unique to True
            submitting = False
            is_unique = True


            # Check our widgets tag, and then check for uniqueness accordingly
            if tag is not None:

                # Plot points
                if tag == "plot_point":
                    for pp in self.mini_widget.owner.plot_points.values():
                        if pp.title.lower() == name and pp.title.lower() != current_name:
                            is_unique = False

                # Arcs
                elif tag == "arc":
                    for arc in self.mini_widget.owner.arcs.values():
                        if arc.title.lower() == name and arc.title.lower() != current_name:
                            is_unique = False


            # Give us our error text if not unique
            if not is_unique:
                e.control.error_text = "Name already exists"
            else:
                e.control.error_text = None

            # Apply the update
            self.mini_widget.p.update()

        # Called when submitting our textfield.
        def _submit_name(e):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''

            # Get our name and check if its unique
            name = e.control.value

            # Non local variables
            nonlocal is_unique
            nonlocal text_field
            nonlocal submitting

            # Set submitting to True
            submitting = True

            # If it is, call the rename function. It will do everything else
            if is_unique:
                self.mini_widget.rename(name)
                
                
            # Otherwise make sure we show our error
            else:
                text_field.error_text = "Name already exists"
                text_field.focus()                                  # Auto focus the textfield
                self.mini_widget.p.update()
                
        # Our text field that our functions use for renaming and referencing
        text_field = ft.TextField(
            value=self.mini_widget.title,
            expand=True,
            dense=True,
            autofocus=True,
            adaptive=True,
            text_size=14,
            text_style=self.text_style,
            on_submit=_submit_name,
            on_change=_name_check,
            on_blur=_cancel_rename,
        )

        # Replaces our name text with a text field for renaming
        self.content.content.content.controls[1] = text_field

        # Clears our popup menu button and applies to the UI
        self.mini_widget.p.overlay.clear()
        self.mini_widget.p.update()

    def get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        def _change_icon_color(color: str):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            # Change the data
            self.mini_widget.change_data(**{'color': color})
            self.color = color
            
            # Change our icon to match, apply the update
            self.reload()
            self.mini_widget.reload_mini_widget()
            self.mini_widget.owner.reload_widget()
            #self.mini_widget.story.workspace.reload_workspace()

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.PopupMenuItem(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=lambda e, col=color: _change_icon_color(col)
                )
            )

        return color_controls
    
    # Called when the delete button is clicked in the menu options
    def delete_clicked(self, e):
        ''' Deletes this file from the story '''

        def _delete_confirmed(e):
            ''' Deletes the widget after confirmation '''

            self.mini_widget.p.close(dlg)

            if self.tag == "plot_point":
                self.mini_widget.owner.delete_plot_point(self.mini_widget)
            else:
                self.mini_widget.owner.delete_arc(self.mini_widget)

            self.mini_widget.owner.story.active_rail.content.reload_rail()
            self.mini_widget.owner.story.close_menu()
            

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.mini_widget.title} forever?", weight=ft.FontWeight.BOLD),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.mini_widget.p.close(dlg)),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ]
        )

        self.mini_widget.p.open(dlg)


    # Called to reload our tree view file display
    def reload(self):

        self.content = ft.Container(
            expand=True, 
            padding=ft.Padding(0, 2, 5, 2),
            
            content=ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                content=ft.Row(
                    expand=True,
                    controls=[
                        ft.Icon(self.icon, color=self.color, size=20), 
                        #ft.Container(width=20),
                        ft.Text(value=self.title, style=self.text_style),
                    ],
                ),
            )
        )
        

        #self.p.update()