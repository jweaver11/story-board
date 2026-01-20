# Class used for our Plot Points and Arcs dropdowns in the Plotline rail, that sit inside of the Plotline dropdowns


import flet as ft
from styles.menu_option_style import MenuOptionStyle
from models.views.story import Story
from models.widgets.plotline import Plotline

# Expansion tiles used for Plotlines (when more than 1), plotpoints labels, and arcs labels
class LabelDropdown(ft.GestureDetector):

    # Constructor
    def __init__(
        self,
        title: str,                                              # Title of this folder
        story: Story,                                            # Story reference for mouse positions and other logic
        additional_menu_options: list[ft.Control],               # Additional menu options when right clicking a category, depending on the rail
        plotline: Plotline,                                      # Reference to the Plotline this dropdown represents
        rail,                    
        plotline_dropdown,
    ):

        # Set our parameters
        self.title = title.title()
        self.story = story
        self.plotline = plotline
        self.additional_menu_options = additional_menu_options
        self.rail = rail
        self.plotline_dropdown = plotline_dropdown


        # Set other variables
        self.color = ft.Colors.PRIMARY
        self.is_expanded = self.plotline.data.get("plot_points_dropdown_expanded", True) if self.title == "Plot Points" else self.plotline.data.get("arcs_dropdown_expanded", True)

        # State tracking variables
        self.are_submitting = False
        self.item_is_unique = True
        
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

            # Set their on_click to call our on_click method, which can handle any type of widget
            option.on_tap = self.new_item_clicked

            # Add to our menu options list
            menu_options.append(option)

        # Return our menu options list
        return menu_options
    
    # Called when expanding/collapsing the directory
    def toggle_expand(self):
        ''' Makes sure our state and data match the updated expanded/collapsed state '''

        # Update our expanded state and data to match, and save it to file
        self.is_expanded = not self.is_expanded
        self.plotline.data["plot_points_dropdown_expanded" if self.title == "Plot Points" else "arcs_dropdown_expanded"] = self.is_expanded
        self.plotline.save_dict()


        # If a different Plotline is active, we unfocus it and focuse our parent instead
        if self.rail.active_dropdown is not None:

            # Check that its a Plotline dropdown
            if hasattr(self.rail.active_dropdown, "is_focused"):
                
                # Unfocus it and apply the changes
                self.rail.active_dropdown.is_focused = False
                self.rail.active_dropdown.refresh_expansion_tile()
            
            # If not a Plotline dropdown, it must be a label dropdown, so we grab its parent Plotline dropdown
            else:

                # Unfocus its parent Plotline dropdown and apply the changes
                self.rail.active_dropdown.plotline_dropdown.is_focused = False
                self.rail.active_dropdown.plotline_dropdown.refresh_expansion_tile()

        # Set ourselves as the active dropdown and refresh the rail buttons
        self.rail.active_dropdown = self
        self.rail.refresh_buttons()

        # Focus our Plotline dropdown parent as well
        self.plotline_dropdown.is_focused = True
        self.plotline_dropdown.refresh_expansion_tile()
        

    # Called when creating new category or when additional menu items are clicked
    async def new_item_clicked(self, e=None, tag: str=None):
        ''' Shows the textfield for creating new item. Requires what type of item (category, chapter, note, etc.) '''

        # Clear out any previous value
        self.new_item_textfield.value = None

        # If this is called from outside our object, pass in a tag instead
        if e is not None: 
            data = e.control.data
        else:
            data = tag
        
         
        # If the data passed in is a plotpoint
        if data == "plot_point":
            self.new_item_textfield.visible = True
            self.new_item_textfield.data = "plot_point"
            self.new_item_textfield.hint_text = "Plot Point Title"
            self.new_item_textfield.value = None
        elif data == "arc":
            self.new_item_textfield.visible = True
            self.new_item_textfield.data = "arc"
            self.new_item_textfield.hint_text = "Arc Title"
            self.new_item_textfield.value = None

        # Check our expanded state. Rebuild if needed
        if self.is_expanded == False:
            self.toggle_expand()
            self.reload()

        # Close the menu, which will also update the page
        await self.story.close_menu()


    def new_item_check(self, e):
        ''' Checks if our new item is unique in our Plotline's dicts '''

        # Get our name and check if its unique
        title = e.control.value

        # Either plotpoint or arc, whatever we're submitting
        type = e.control.data

        print(type)

        # Check for plot points
        if type == "plot_point":

            # Run through our Plotline Plotline/arcs plot points to see if the name exists
            if title in self.plotline.plot_points.keys():
                self.item_is_unique = False
                e.control.error_text = "Title must be unique"
            else:
                self.item_is_unique = True
                e.control.error_text = None

        # Check for arcs
        elif type == "arc":
            if title in self.plotline.arcs.keys():
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
                self.plotline.create_plot_point(title=title)

            # Arcs
            elif type == "arc":
                self.plotline.create_arc(title=title)
            
        # Otherwise make sure we show our error
        else:
            self.new_item_textfield.focus()                                  # Auto focus the textfield
            self.story.p.update()

    # Called when we need to reload this directory tile
    def reload(self):
        

        # Set our icon to a Plotline unless we are labeld for Plot Points or Arcs dropdown
        if self.title == "Plot Points":
            icon = ft.Icon(ft.Icons.LOCATION_PIN, color=self.color)
        elif self.title == "Arcs":
            icon = ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=self.color)
        else:
            icon = ft.Icon(ft.Icons.ERROR_OUTLINE)

        expansion_tile = ft.ExpansionTile(
            title=ft.Text(value=self.title, weight=ft.FontWeight.BOLD, text_align="left"),
            #title=ft.Row([
                #new_item_button,
                #ft.Text(value=self.title, weight=ft.FontWeight.BOLD, text_align="left"),
            #]),
            dense=True,
            leading=icon,
            initially_expanded=self.is_expanded,
            visual_density=ft.VisualDensity.COMPACT,
            tile_padding=ft.Padding(6, 0, 0, 0),      # If no leading icon, give us small indentation
            #tile_padding=ft.Padding(0, 0, 0, 0),      # If leading icon, no indentation
            controls_padding=ft.Padding(10, 0, 0, 0),       # Keeps all sub children indente
            maintain_state=True,
            expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
            adaptive=True,
            bgcolor=ft.Colors.TRANSPARENT,
            shape=ft.RoundedRectangleBorder(),
            on_change=lambda e: self.toggle_expand(),
        )

        # Re-adds our content controls in the correct order
        if self.content is not None and self.content.controls is not None:

            # Add all controls except the textfield first
            for control in self.content.controls:
                if control != self.new_item_textfield:
                    expansion_tile.controls.append(control)

            # Finally add our new item textfield at the bottom
            expansion_tile.controls.append(self.new_item_textfield)
    

        
        # Set the content
        self.content = expansion_tile