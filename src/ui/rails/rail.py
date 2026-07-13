'''
Parent rail class used by our six workspaces. Gives uniformity to our rails
'''

import flet as ft
import os
import json
from models.views.story import Story
from models.widgets.plotline import Plotline
from styles.rail.rail_folder import RailFolder
from utils.check_widget_unique import check_widget_unique
from utils.new_canvas import new_canvas_alert_dlg
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
        super().__init__(spacing=0, expand=True, scroll="none",)
            
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
                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4))
                    )
                )

        # Add add button to bottom that opens the settings to the template section
        # Add templates label at the top that is disabled

        elif widget_type == "world":
            for name, template in app.settings.data.get('world_templates', {}).items():
                template_options.append(
                    ft.MenuItemButton(
                        name, data=widget_type, on_click=self.new_item_clicked, 
                        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4))
                    )
                )

        elif widget_type == "chart":
            template_options = [
                ft.MenuItemButton(
                    "Bar", data=f"{widget_type}:bar", 
                    on_click=self.new_item_clicked, leading=ft.Icon(ft.Icons.INSERT_CHART_OUTLINED_OUTLINED, ft.Colors.PRIMARY),
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4))
                ),
                ft.MenuItemButton(
                    "Radar", data=f"{widget_type}:radar", 
                    on_click=self.new_item_clicked, leading=ft.Icon(ft.CupertinoIcons.COMPASS, ft.Colors.PRIMARY),
                    style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK, shape=ft.RoundedRectangleBorder(radius=4))
                ),
            ]

        # Not used, but maybe used in future for notes or something
        else:
            template_options = [
                ft.MenuItemButton("Blank", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Research", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Theme", data=widget_type, on_click=self.new_item_clicked),
                ft.MenuItemButton("Idea", data=widget_type, on_click=self.new_item_clicked),
            ]
        return template_options
    
    # Called when a widget is dragged and dropped into this directory
    def move_widget_file(self, e: ft.DragTargetEvent, new_directory: str):
        ''' Moves our widgets into this directory from wherever they were '''
        #print("Drag accepting")

        draggable = e.page.get_control(e.src_id)

        widget = self.story.get_widget_by_id(draggable.data)

        if widget is None:
            print("Error: Widget not found for drag accept")
            return

        # Call the move file using the new directory path
        #self.story.blocker.visible = True
        #self.story.blocker.update()
        

        if self.p.run_task(widget.move_file, new_directory):
            #self.story.blocker.visible = False
            #self.story.blocker.update()
            return
        
        else:

            # Update the background color
            e.control.content.bgcolor = ft.Colors.with_opacity(0.0, ft.Colors.ON_SURFACE)
            #e.control.content.update()
            #self.story.blocker.visible = False
            #self.story.blocker.update()


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
            case "character_relationship_map":
                self.new_item_textfield.hint_text = "Character Relationship Map Title"
            
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
                self.new_item_textfield.label = f"{template_name}"
            case "comic_preview":
                self.new_item_textfield.hint_text = "Comic Preview Title"
            case "plot_chart":
                self.new_item_textfield.hint_text = "Plot Chart Title"
            case _:
                if ":" in tag:
                    self.new_item_textfield.hint_text = f"{tag.split(':')[0].capitalize()} Title"
                else:
                    self.new_item_textfield.hint_text = f"{tag.capitalize()} Title"

        # Open the textfield early since we have to wait for async close menu
        self.new_item_textfield.update()
        await self.new_item_textfield.focus()
        
        await self.story.close_menu()


    # Called when clicking off the textfield and after submission
    def on_new_item_blur(self, e):
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
        if ":" in tag:
            tag, chart_type = tag.split(":")
            
        # If our new title unique (check from on_new_item_change), create the new item
        if self.item_is_unique:

            #blocker.visible = True 
            #self.story.blocker.update()
            self.p.pop_dialog()   # Close the textfield dialog
            await asyncio.sleep(0)   # Wait for the dialog to close before creating the new

            match tag:
                # New categories
                case "folder":
                    # Create our new category
                    await self.story.create_folder(directory_path=self.directory_path, name=title)

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
                    await self.story.create_widget(title, tag, chart_type=chart_type if tag == "chart" else None)

            #if self.story.blocker.visible:
                #self.story.blocker.visible = False
                #self.story.blocker.update()



    # Called when new character button or menu option is clicked
    def new_canvas_clicked(self, e):
        ''' Handles setting our textfield for new character creation '''

        # Close the menu (if ones is open), which will update the page as well
        self.story.close_menu_instant()   
        self.p.show_dialog(new_canvas_alert_dlg(self.p, self.story))

    # Called every time the mouse moves over our rail
    async def _set_menu_coords(self, e: ft.PointerEvent):
        ''' Stores our mouse positioning so we know where to open menus '''
        self.story.mouse_x = e.global_position.x 
        self.story.mouse_y = e.global_position.y

    

    # Called when changes occure that require rail to be reloaded. Should be overwritten by children
    def reload_rail(self):
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
        except Exception:
            pass

        # Return yourself as the control
        #return self