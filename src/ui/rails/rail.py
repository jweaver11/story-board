'''
Parent rail class used by our six workspaces. Gives uniformity to our rails
'''

import flet as ft
import os
import json
from models.views.story import Story
from models.widgets.timeline import Timeline
from styles.tree_view.tree_view_directory import TreeViewDirectory
from handlers.check_widget_unique import check_widget_unique


class Rail(ft.Container):

    # Constructor
    def __init__(
        self, 
        page: ft.Page,                  # Page reference
        story: Story,                   # Story reference
        directory_path: str,            # Root path that loads this rails content
        timeline: Timeline = None,      # Timeline reference for creating plot points and arcs on timeline rail
    ):
        
        # Initialize the parent Container class first
        super().__init__(
            padding=ft.Padding(0, 0, 0, 0),        # Adds padding left to match divider on the right
        )
            
        # Store our parameters
        self.p = page
        self.story = story
        self.directory_path = directory_path
        self.timeline = timeline

        self.active_dropdown: TreeViewDirectory = None

        # Text style for our textfields
        self.text_style = ft.TextStyle(
            size=14,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.BOLD,
        )

        # Textfield for creating new items (sub-categories, chapters, notes, characters, etc.)
        self.new_item_textfield = ft.TextField(     
            hint_text="hint",                                   # Placeholder text before user starts typings
            data="data",                                        # Data for logic routing on submit
            autofocus=True,                                     # Auto-focus when made visible
            capitalization=ft.TextCapitalization.WORDS,     # Capitalize sentences for names
            visible=False,                                      # Hidden by default
            text_style=self.text_style,                         # Text style for consistency
            on_blur=self.on_new_item_blur,                      # Called when clicking off the textfield and after submitting
            on_change=self.on_new_item_change,                  # Called on every key input
            on_submit=self.submit_item,                         # Called when enter is pressed and textfield is focused
            dense=True,
        )


        # State variables used for our UI to track logic
        self.item_is_unique = True          # If the new category, chapter, note, etc. title is unique within its directory
        self.are_submitting = False         # If we are currently submitting this item

        # Calling initial rail to reload. Child override this one
        #self.reload_rail() 

    def get_menu_options(self) -> list[ft.Control]:
        ''' Returns a list of menu options when right clicking child rail '''
        return []
    
    def get_sub_menu_options(self) -> list[ft.Control]:
        ''' Returns a list of additional menu options when clicking directories in the rail '''
        return []
    
    # Called when a widget is dragged and dropped into this directory
    def on_drag_accept(self, e, new_directory: str):
        ''' Moves our widgets into this directory from wherever they were '''
        #print("Drag accepting")

        # Load our data (draggables can't just pass in simple data for some reason)
        event_data = json.loads(e.data)

        # Grab our draggable from the event
        draggable = e.page.get_control(event_data.get("src_id"))
            
        # Grab our key and set the widget
        widget_key = draggable.data

        widget = None

        for w in self.story.widgets:
            if w.data.get('key', "") == widget_key:
                widget = w
                break

        if widget is None:
            print("Error: Widget not found for drag accept")
            return

        # Call the move file using the new directory path
        widget.move_file(new_directory=new_directory)


    # Called when new category button or menu option is clicked
    def new_item_clicked(self, e):
        ''' Handles setting our textfield for new category creation '''

        tag = e.control.data
        
        # Make textfield visible, reset its value, and give it right data for logic
        self.new_item_textfield.visible = True
        self.new_item_textfield.value = None
        self.new_item_textfield.data = tag

        match tag:
            case "family_tree":
                self.new_item_textfield.hint_text = "Family Tree Name"
            case "character" | "category" :
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Name"
            case _:
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Title"
        

        # Close the menu (if ones is open), which will update the page as well
        self.story.close_menu()
        

    # Called whenever our user inputs a new key into one of our textfields for new items
    def on_new_item_change(self, e):
        ''' Checks if our title is unique within its directory (default in this case) '''

        # Start out assuming we are unique
        self.item_is_unique = True

        # Grab out title and tag from the textfield, and set our new key to compare
        title = e.control.value
        tag = e.control.data

        # Generate our new key to compare. Requires normalization
        nk = self.directory_path + "\\" + title + "_" + e.control.data
        new_key = os.path.normpath(nk)

        if tag == "category":
            new_key = os.path.normcase(os.path.normpath(self.directory_path + "\\" + title))
            new_key = new_key.rstrip()  # Remove trailing spaces for folder names
            for key in self.story.data['folders'].keys():
                
                # Path comparisons require normalization
                if os.path.normcase(os.path.normpath(key)) == new_key:
                    self.item_is_unique = False
                    error_text = "Category must be unique."
                    break

        # Not a category, so we check the widget
        else:
            error_text, self.item_is_unique = check_widget_unique(self.story, new_key)

        # If we are NOT unique, show our error text
        if not self.item_is_unique:
            #print("Setting error text:", error_text)
            e.control.error_text = error_text

        # Otherwise remove our error text
        else:
            e.control.error_text = None
            
        self.p.update()


    # Called when clicking off the textfield and after submission
    def on_new_item_blur(self, e):

        # Check if we're submitting, or normal blur
        if self.are_submitting:

            # Change submitting to false
            self.are_submitting = False     

            # If our item is unique, hide the textfield and update
            if self.item_is_unique:
                self.new_item_textfield.visible = False
                self.new_item_textfield.value = None
                self.new_item_textfield.error_text = None
                self.p.update()
                return
            
            # Otherwise its not unique, re-focus our textfield
            else:
                self.new_item_textfield.visible = True
                self.new_item_textfield.focus()
        
        # If we're not submitting, just hide the textfield and reset values
        else:
            self.new_item_textfield.visible = False
            self.new_item_textfield.value = None
            self.new_item_textfield.error_text = None
            self.p.update()


    # Called whenever we submit a new item (Chapter, note, category, etc.) via enter key
    def submit_item(self, e):
        ''' Sets our state to submitting, and creates new item if unique. Father is either timeline or arc for creating mini widgets '''

        # Change our submitting state
        self.are_submitting = True

        # Grab our title from the textfield
        title = e.control.value

        # Protect against empty titles. They break things
        if title is None or title.rstrip() == "":
            return
            
        # If our new title unique (check from on_new_item_change), create the new item
        if self.item_is_unique:

            # Check what kind of item we're creating based on textfield data
            tag = e.control.data

            # New categories
            if tag == "category":
                # Create our new category
                self.story.create_folder(directory_path=self.directory_path, name=title)

            # New plot points and arcs on timelines or arcs
            elif tag == "plot_point":
                if self.timeline is not None:
                    print("Creating plot point:", title)
                    self.timeline.create_plot_point(title)

            # New arcs on timelines
            elif tag == "arc":
                if self.timeline is not None:
                    print("Creating arc:", title)
                    self.timeline.create_arc(title)
                 
            # New widgets
            else:
                # Create the widget and reload all our rails
                self.story.create_widget(title, tag)
                self.story.active_rail.content.reload_rail()



            

    # Called when we select a new dropdown
    def refresh_buttons(self):
        ''' Refreshes the buttons at top of the rail '''
        pass

    # Called every time the mouse moves over the workspace
    def on_hovers(self, e):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.story.mouse_x = e.global_x 
        self.story.mouse_y = e.global_y 

    

    # Called when changes occure that require rail to be reloaded. Should be overwritten by children
    def reload_rail(self) -> ft.Control:
        ''' Sets our rail (extended ft.Container) content and applies the page update '''

        # Set your content for the rail
        self.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                ft.Text("Base Rail - No specific content"),
                # Add more controls here as needed
            ]
        )

        # Apply the update to UI
        self.p.update()

        # Return yourself as the control
        return self