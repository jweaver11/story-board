'''
Extended flet controls that implement the same styling for easy access
'''

import flet as ft
from styles.menu_option_style import MenuOptionStyle
from models.views.story import Story
from models.widgets.timeline import Timeline
import os
from styles.colors import colors


# TODO: When clicking and expanding, make sure to set the active_timeline to this timeline, 
# so we can use the buttons at top of rail when there are multiple timelines

# Expansion tiles used for timelines (when more than 1), plotpoints labels, and arcs labels
class TimelineDropdown(ft.GestureDetector):

    # Constructor
    def __init__(
        self,
        title: str,                                              # Title of this folder
        story: Story,                                            # Story reference for mouse positions and other logic
        additional_menu_options: list[ft.Control],               # Additional menu options when right clicking a category, depending on the rail
        timeline: Timeline,                                      # Reference to the timeline this dropdown represents 
        rail,     
    ):

        # Set our parameters
        self.title = title.title()
        self.story = story
        self.timeline = timeline
        self.additional_menu_options = additional_menu_options
        self.rail = rail


        # Set other variables
        self.color = self.timeline.data.get("color", "primary")
        self.is_expanded = self.timeline.data.get("dropdown_is_expanded", True)

        # State tracking variables
        self.are_submitting = False
        self.item_is_unique = True
        self.is_focused = False
        
        # Set our text style
        self.text_style = ft.TextStyle(
            size=14,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.BOLD,
        )
        
        # Textfield for creating new items (sub-categories, chapters, notes, characters, etc.)
        self.new_item_textfield = ft.TextField(  
            hint_text=f"new_item Title",   
            data="data passed in",       
            autofocus=True,
            capitalization=ft.TextCapitalization.SENTENCES,
            on_change=self.new_item_check,
            on_blur=self.on_new_item_blur,
            on_submit=self.new_item_submit,
            visible=False,
            text_style=self.text_style,
            dense=True,
        )

        self.expansion_tile: ft.ExpansionTile = None    # Placeholder for our expansion tile

        
        # Parent constructor
        super().__init__(
            mouse_cursor=ft.MouseCursor.CLICK,
            #on_enter=self.on_hover,
            #on_exit=self.on_stop_hover,
            on_secondary_tap=lambda e: self.story.open_menu(self.get_menu_options()),
        )
        

        self.reload()

    # Called to return our menu options when right clicking our dropdown
    def get_menu_options(self) -> list[ft.Control]:
        ''' Filters the five options we received, and only returns what we need with correct logic '''
    
        # Our menu options list
        menu_options: list[ft.Control] = []

        # Run through our additional menu options if we have any, and set their on_click methods
        for option in self.additional_menu_options or []:

            option.on_tap = self.new_item_clicked

            # Add to our menu options list
            menu_options.append(option)

        # Add our other three buttons
        menu_options.extend([
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
            # Color changing popup menu
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    expand=True,
                    tooltip="",
                    padding=None,
                    content=ft.Row(
                        expand=True,
                        controls=[
                            ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=ft.Colors.PRIMARY),
                            ft.Text("Color", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True), 
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN_OUTLINED, color=ft.Colors.ON_SURFACE, size=16),
                        ]
                    ),
                    items=self.get_color_options()
                )
            ),
            # Delete button
            MenuOptionStyle(
                on_click=lambda e: self.delete_clicked(e),
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            ),
        ])
        # Return our menu options list
        return menu_options
    
    # Called when expanding/collapsing the directory
    def toggle_expand(self):
        ''' Makes sure our state and data match the updated expanded/collapsed state '''

        self.is_expanded = not self.is_expanded

        self.timeline.data["dropdown_is_expanded"] = self.is_expanded
        self.timeline.save_dict()

        # Make the timeline widget visible if its not
        if not self.timeline.visible:
            self.timeline.toggle_visibility()

        #print("Active dropdown before:", self.rail.active_dropdown)
        if self.rail.active_dropdown is not None:
            if hasattr(self.rail.active_dropdown, "is_focused"):
                
                self.rail.active_dropdown.is_focused = False
                self.rail.active_dropdown.refresh_expansion_tile()
            
            else:
                self.rail.active_dropdown.timeline_dropdown.is_focused = False
                self.rail.active_dropdown.timeline_dropdown.refresh_expansion_tile()

        self.rail.active_dropdown = self
        self.rail.refresh_buttons()

        self.is_focused = True
        self.refresh_expansion_tile()
        

    # Called when creating a new plot point or arc only
    def new_item_clicked(self, e=None, tag: str=None):
        ''' Shows the textfield for creating new item. Requires what type of item (category, chapter, note, etc.) '''

        # If this is called from outside our object, pass in a tag instead
        if e is not None: 
            data = e.control.data
        else:
            data = tag
        
        # Check our expanded state. Rebuild if needed
        if self.is_expanded == False:
            self.toggle_expand()
            self.reload()
         
        # If the data passed in is a plotpoint
        if data == "plot_point":

            self.content.controls[0].new_item_clicked(tag="plot_point")

        # Otherwise we're an arc
        else:

            self.content.controls[1].new_item_clicked(tag="arc")

        # Close the menu, which will also update the page
        self.story.close_menu()

    # Called when our new item textfield changes
    def new_item_check(self, e):
        ''' Checks if our new item is unique in our timeline's dicts '''

        # Get our name and check if its unique
        title = e.control.value

        # Either plotpoint or arc, whatever we're submitting
        type = e.control.data

        # Check for plot points
        if type == "plot_point":

            # Run through our timeline timeline/arcs plot points to see if the name exists
            if title in self.timeline.plot_points.keys():
                self.item_is_unique = False
                e.control.error_text = "Title must be unique"
            else:
                self.item_is_unique = True
                e.control.error_text = None

        # Check for arcs
        elif type == "arc":
            if title in self.timeline.arcs.keys():
                self.item_is_unique = False
                e.control.error_text = "Title must be unique"
            else:
                self.item_is_unique = True
                e.control.error_text = None

        # Update the page to show changes
        self.story.p.update()

    # Called when clicking off the textfield and after submission
    def on_new_item_blur(self, e):
        ''' Handles if we need to hide our textfield or re-focus it based on submissions '''
        
        # Check if we're submitting, or normal blur
        if self.are_submitting:

            # Change submitting to false
            self.are_submitting = False     

            # If our item is unique, hide the textfield and update
            if self.item_is_unique:
                e.control.visible = False
                e.control.value = None
                e.control.error_text = None
                self.story.p.update()
                return
            
            # Otherwise its not unique, re-focus our textfield
            else:
                e.control.visible = True
                e.control.focus()
        
        # If we're not submitting, just hide the textfield and reset values
        else:
            e.control.visible = False
            e.control.value = None
            e.control.error_text = None
            self.story.p.update()


    def new_item_submit(self, e):

        # Get our name and check if its unique
        title = e.control.value

        # Set submitting to True
        self.are_submitting = True

        # Either plotpoint or arc, whatever we're submitting
        type = e.control.data

        # If we're unique, figure out what item we are creating
        if self.item_is_unique:

            # Plot points
            if type == "plot_point":
                self.timeline.create_plot_point(title=title)

            # Arcs
            elif type == "arc":
                self.timeline.create_arc(title=title)
            
        # Otherwise make sure we show our error
        else:
            self.new_item_textfield.focus()                                  # Auto focus the textfield
            self.story.p.update()

        
    # Called when rename button is clicked
    def rename_clicked(self, e):

        # Track if our name is unique for checks, and if we're submitting or not
        self.is_unique = True
        self.are_submitting = False

        # Called when clicking outside the input field to cancel renaming
        def _cancel_rename(e):
            ''' Puts our name back to static and unalterable '''

            # Grab our submitting state

            # Since this auto calls on submit, we need to check. If it is cuz of a submit, do nothing
            if self.are_submitting:
                self.are_submitting = not self.are_submitting     # Change submit status to False so we can de-select the textbox
                return
            
            # Otherwise we're not submitting (just clicking off the textbox), so we cancel the rename
            else:

                self.story.active_rail.content.reload_rail()
                

        # Called everytime a change in textbox occurs
        def _name_check(e):
            ''' Checks if the name is unique within its type of widget '''

            nonlocal text_field

            # Grab the new name
            new_name = text_field.value

             # Set submitting to false, and unique to True
            self.are_submitting = False
            self.is_unique = True
        

            for timeline in self.story.timelines.values():

                # If there is no change, skip the checks
                if new_name.capitalize() == self.title:
                    break

                elif new_name.capitalize() == timeline.title:
                    self.is_unique = False
                    break
           

            # Give us our error text if not unique
            if not self.is_unique:
                e.control.error_text = "Timeline already exists"
            else:
                e.control.error_text = None

            # Apply the update
            self.timeline.p.update()

        # Called when submitting our textfield.
        def _submit_name(e):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''

            nonlocal text_field

            # Get our name and check if its unique
            new_name = text_field.value
            
            # Set submitting to True
            self.are_submitting = True

            # If it is, call the rename function. It will do everything else
            if self.is_unique:

                #new_path = self.full_path[:self.full_path.rfind("\\")+1] + new_name

                self.timeline.rename(new_name)

                self.story.active_rail.content.reload_rail()
                
                
            # Otherwise make sure we show our error
            else:
                text_field.error_text = "Name already exists"
                text_field.focus()                                  # Auto focus the textfield
                self.timeline.p.update()
                
        # Our text field that our functions use for renaming and referencing
        text_field = ft.TextField(
            value=self.title,
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
        self.expansion_tile.title = text_field

        # Clears our popup menu button and applies to the UI
        self.story.close_menu()

    def get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        def _change_icon_color(color: str):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            # Change the data
            self.timeline.data['color'] = color
            self.timeline.save_dict()

            self.color = color

            self.reload()
            
            # Change our icon to match, apply the update
            #self.story.active_rail.content.reload_rail()
            self.timeline.reload_widget()
            #self.close_menu(None)      # Auto closing menu works, but has a grey screen bug

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

            self.timeline.p.close(dlg)
            self.timeline.story.delete_widget(self.timeline)
            

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.timeline.title} forever?", weight=ft.FontWeight.BOLD),
            alignment=ft.alignment.center,
            title_padding=ft.padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.timeline.p.close(dlg)),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ]
        )

        self.timeline.p.open(dlg)


    def refresh_expansion_tile(self):
        if self.is_focused:
            self.expansion_tile.bgcolor = ft.Colors.with_opacity(.8, ft.Colors.ON_INVERSE_SURFACE)
            self.expansion_tile.collapsed_bgcolor = ft.Colors.with_opacity(.8, ft.Colors.ON_INVERSE_SURFACE)
        else:
            self.expansion_tile.bgcolor = ft.Colors.TRANSPARENT
            self.expansion_tile.collapsed_bgcolor = ft.Colors.TRANSPARENT

        self.timeline.p.update()


    # Called when we need to reload this directory tile
    def reload(self):

        

        self.expansion_tile = ft.ExpansionTile(
            title=ft.Text(value=self.title, weight=ft.FontWeight.BOLD, text_align="left"),
            dense=True,
            initially_expanded=self.is_expanded,
            visual_density=ft.VisualDensity.COMPACT,
            tile_padding=ft.Padding(6, 0, 0, 0),      # If no leading icon, give us small indentation
            controls_padding=ft.Padding(10, 0, 0, 0),       # Keeps all sub children indented
            leading=ft.Icon(ft.Icons.TIMELINE_OUTLINED, color=self.color),
            maintain_state=True,
            expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
            adaptive=True,
            bgcolor=ft.Colors.TRANSPARENT if not self.is_focused else ft.Colors.with_opacity(.8, ft.Colors.ON_INVERSE_SURFACE),
            collapsed_bgcolor=ft.Colors.TRANSPARENT if not self.is_focused else ft.Colors.with_opacity(.8, ft.Colors.ON_INVERSE_SURFACE),
            #shape=ft.RoundedRectangleBorder(),
            on_change=lambda e: self.toggle_expand(),
        )

        # Our controls should always be 3. Plot point dropdown, arcs dropdown, and a spacing container
        # Re-adds our content controls so we can keep states
        if self.content is not None:        # Protects against first loads
            if self.content.controls is not None:       # Re-add our controls when we reload
                for control in self.content.controls:
                    self.expansion_tile.controls.append(control)

        
        # Set the content
        self.content = self.expansion_tile

        self.refresh_expansion_tile()

        self.timeline.p.update()