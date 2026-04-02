'''
Parent rail class used by our six workspaces. Gives uniformity to our rails
'''

import flet as ft
import os
import json
from models.views.story import Story
from models.widgets.plotline import Plotline
from styles.rail.tree_view_directory import TreeViewDirectory
from utils.check_widget_unique import check_widget_unique
from utils.alert_dialogs.new_canvas import new_canvas_alert_dlg
import asyncio
from models.app import app
from models.isolated_controls.column import IsolatedColumn
from models.isolated_controls.list_view import IsolatedListView


@ft.control
class Rail(IsolatedColumn):

    # Constructor
    def __init__(
        self, 
        page: ft.Page,                  # Page reference
        story: Story,                   # Story reference
        directory_path: str,            # Root path that loads this rails content
        plotline: Plotline = None,      # plotline reference for creating plot points and arcs on plotline rail
    ):
        
        # Initialize the parent Container class first
        super().__init__(spacing=0, expand=True, scroll="none")
            
        # Store our parameters
        self.p = page
        self.story = story
        self.directory_path = directory_path
        self.plotline = plotline        # Plotlines rail

        # Text style for our textfields
        self.text_style = ft.TextStyle(
            size=14,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.BOLD,
        )

        # Textfield for creating new items (sub-categories, chapters, notes, characters, etc.)
        self.new_item_textfield = ft.TextField(     
            hint_text="", data="",                 # Hint text and data tag for logic                      
            autofocus=True, dense=True,                 
            capitalization=ft.TextCapitalization.SENTENCES,     # Capitalize sentences for names
            visible=False,                                      # Hidden by default
            text_style=self.text_style,                         # Text style for consistency
            on_blur=self.on_new_item_blur,                      # Called when clicking off the textfield and after submitting
            on_change=self.on_new_item_change,                  # Called on every key input
            on_submit=self.submit_item,                         # Called when enter is pressed and textfield is focused
            icon=None,
        )
        


        # State variables used for our UI to track logic
        self.item_is_unique = True          # If the new folder, chapter, note, etc. title is unique within its directory
        self.are_submitting = False         # If we are currently submitting this item


    def get_menu_options(self) -> list[ft.Control]:
        ''' Returns a list of menu options when right clicking child rail '''
        return []
    
    def get_sub_menu_options(self) -> list[ft.Control]:
        ''' Returns a list of additional menu options when clicking directories in the rail '''
        return []
    
    def get_template_options(self, widget_type: str) -> list[ft.Control]:
        ''' Returns a list of template options when right clicking empty space in the rail '''


        template_options = []

        if widget_type == "character":
            
            for name, template in app.settings.data.get('character_templates', {}).items():
                template_options.append(
                    ft.MenuItemButton(
                        name, data=widget_type, on_click=self.new_item_clicked, 
                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=10))
                    )
                )

        # Add add button to bottom that opens the settings to the template section
        # Add templates label at the top that is disabled

        elif widget_type == "world":
            for name, template in app.settings.data.get('world_templates', {}).items():
                template_options.append(
                    ft.MenuItemButton(
                        name, data=widget_type, on_click=self.new_item_clicked, 
                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=10))
                    )
                )

        # Not used
        else:
            template_options = [
                ft.MenuItemButton("Blank", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Research", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Theme", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Idea", data=widget_type, on_click=self.new_item_clicked),
            ]
        return template_options
    
    # Called when a widget is dragged and dropped into this directory
    def on_drag_accept(self, e: ft.DragTargetEvent, new_directory: str):
        ''' Moves our widgets into this directory from wherever they were '''
        #print("Drag accepting")

        draggable = e.page.get_control(e.src_id)
            
        # Grab our key and set the widget
        widget_key = draggable.data

        widget = None

        for w in self.story.widgets:
            if w.data.get('key', "") == widget_key:
                widget = w
                break

        if widget is None:
            print("Error: Widget not found for drag accept")
            print(f"Widget key: {widget_key}")
            return

        # Call the move file using the new directory path

        if self.p.run_task(widget.move_file, new_directory):
            return
        
        else:

            # Update the background color
            e.control.content.bgcolor = ft.Colors.with_opacity(0.0, ft.Colors.ON_SURFACE)
            e.control.content.update()


    # Called when new category button or menu option is clicked
    async def new_item_clicked(self, e):
        ''' Handles setting our textfield for new category creation '''

            
        tag = e.control.data
        
        # Make textfield visible, reset its value, and give it right data for logic
        self.new_item_textfield.visible = True
        self.new_item_textfield.value = None
        self.new_item_textfield.data = tag
        self.new_item_textfield.error = None
        self.new_item_textfield.label = None
        self.new_item_textfield.icon = None


        match tag:
            case "character_connection_map":
                self.new_item_textfield.hint_text = "Character Connection Map Title"
            case "world_building":
                self.new_item_textfield.hint_text = "World Building Name"
            case "plot_point": 
                self.new_item_textfield.hint_text = "Plot Point Title"
            case "character" | "folder" | "item" | "object":
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Name"
                if tag == "character":
                    template_name = str(e.control.content)
                    self.new_item_textfield.label = template_name

            case "canvas":
                await self.story.close_menu()
                self.p.show_dialog(new_canvas_alert_dlg(self.p, self.story))
                return
                        
            case "canvas_board":
                self.new_item_textfield.hint_text = "Canvas Board Title"
            case "world":
                self.new_item_textfield.hint_text = "World Title"
                template_name = str(e.control.content)
                self.new_item_textfield.label = f"{template_name} Template"
            case _:
                self.new_item_textfield.hint_text = f"{tag.capitalize()} Title"

        # Open the textfield early since we have to wait for async close menu
        self.new_item_textfield.update()
        await self.new_item_textfield.focus()
        await self.controls[2].content.content.content.scroll_to(0) # Scroll to top of rail
        
        await self.story.close_menu()
        

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

        if tag == "folder":
            new_key = os.path.normcase(os.path.normpath(self.directory_path + "\\" + title))
            new_key = new_key.strip()  # Remove trailing spaces for folder names
            for key in self.story.data['folders'].keys():
                
                # Path comparisons require normalization
                if os.path.normcase(os.path.normpath(key)) == new_key:
                    self.item_is_unique = False
                    error_text = "Folder must be unique."
                    break

        # Some mini widgets that have their own uniquess checks
        elif tag == "plot_point" and self.plotline is not None:
            for key in self.plotline.plot_points.keys():
                if key == title:
                    self.item_is_unique = False
                    error_text = "Title must be unique"
                    break
            
        elif tag == "arc" and self.plotline is not None:
            for key in self.plotline.arcs.keys():
                if key == title:
                    self.item_is_unique = False
                    error_text = "Title must be unique"
                    break
        elif tag == "marker" and self.plotline is not None:
            for key in self.plotline.markers.keys():
                if key == title:
                    self.item_is_unique = False
                    error_text = "Title must be unique"
                    break

        # Not a category, so we check the widget
        else:
            error_text, self.item_is_unique = check_widget_unique(self.story, new_key)

        # If we are NOT unique, show our error text
        if not self.item_is_unique:
            e.control.error = error_text

        # Otherwise remove our error text
        else:
            e.control.error = None
            
        e.control.update()


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
                self.new_item_textfield.error = None
                self.new_item_textfield.update()
                return
            
            # Otherwise its not unique, re-focus our textfield
            else:
                self.new_item_textfield.visible = True
                self.p.run_task(self.new_item_textfield.focus)
                self.new_item_textfield.update()
        
        # If we're not submitting, just hide Textfield
        else:
            self.new_item_textfield.visible = False
            self.new_item_textfield.update()


    # Called whenever we submit a new item (Chapter, note, category, etc.) via enter key
    async def submit_item(self, e):
        ''' Sets our state to submitting, and creates new item if unique. Father is either Plotline or arc for creating mini widgets '''

        # Change our submitting state
        self.are_submitting = True

        # Grab our title from the textfield
        title = e.control.value

        # Protect against empty titles. They break things
        if title is None or title.strip() == "":
            return
        
        tag = e.control.data
            
        # If our new title unique (check from on_new_item_change), create the new item
        if self.item_is_unique:

            self.story.blocker.visible = True 
            self.story.blocker.update()
            self.p.pop_dialog()   # Close the textfield dialog
            await asyncio.sleep(0)   # Wait for the dialog to close before creating the new

            match tag:
                # New categories
                case "folder":
                    # Create our new category
                    self.story.create_folder(directory_path=self.directory_path, name=title)

                # Mini widgets
                case "plot_point":
                    if self.plotline is not None:
                        print("Creating plot point:", title)
                        await self.plotline.create_plot_point(title)
                case "arc":
                    if self.plotline is not None:
                        print("Creating arc:", title)
                        await self.plotline.create_arc(title)
                case "marker":
                    if self.plotline is not None:
                        print("Creating marker:", title)
                        await self.plotline.create_marker(title)

                # All other cases are widgets
                case _:
                    # Create the widget and reload all our rails
                    await self.story.create_widget(title, tag)

            if self.story.blocker.visible:
                self.story.blocker.visible = False
                self.story.blocker.update()



    # Called when new character button or menu option is clicked
    def new_canvas_clicked(self, e):
        ''' Handles setting our textfield for new character creation '''

        # Close the menu (if ones is open), which will update the page as well
        self.story.close_menu_instant()   
        self.p.show_dialog(new_canvas_alert_dlg(self.p, self.story))

    # Called every time the mouse moves over our rail
    async def on_hovers(self, e: ft.PointerEvent):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.story.mouse_x = e.global_position.x 
        self.story.mouse_y = e.global_position.y

    

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
        try:        # Handle first launch
            self.update()
        except Exception as e:
            pass

        # Return yourself as the control
        return self