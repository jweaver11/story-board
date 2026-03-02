''' UI model file to create our all_workspaces_rail on the left side of the screen.
This object is stored in app.all_workspaces_rail.
Handles new workspace selections, re-ordering, collapsing, and expanding the rail. '''

import flet as ft

from models.views.story import Story

# Class so we can store our all workspaces rail as an object inside of app
class WorkspacesRail(ft.Container):
    
    # Constructor for our all_workspaces_rail object. Needs a page reference passed in
    def __init__(self, page: ft.Page, story: Story = None):

        self.p = page   # Page reference
       
        # Style our rail (container)
        super().__init__(
            alignment=ft.Alignment.CENTER,  # Aligns content to the 
            padding=ft.Padding.only(bottom=10, right=2, left=2),
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        )

        # Build our rail on start
        self.reload_rail(story)

    

    # Called whenever we select a new workspace selector rail
    def change_workspace(self, e, story: Story, force_rail: str=None):
        ''' Changes our selected workspace for the active rail '''

        if story is None:       # Protect settings being open but no story loaded
            return
        
        if force_rail is not None:      # Use manual setting if one is passed in
            story.data['selected_rail'] = force_rail

        else:   # Otherwise, we are called from ourselves, so just use the data from the rail we clicked on
            story.data['selected_rail'] = e.control.destinations[0].data

        # Save data and apply the rail updates
        story.save_dict()
        story.active_rail.display_active_rail(story) 
        self.reload_rail(story)  



    # Called by clicking button on bottom right of rail
    def toggle_collapse_rail(self, e, story: Story):
        ''' Collapses or expands the rail, and saves the state in settings '''
        from models.app import app    # Always grabs updated reference when collapsing/expanding

        # Toggle our collapsed state
        app.settings.data['workspaces_rail_is_collapsed'] = not app.settings.data['workspaces_rail_is_collapsed']
        app.settings.save_dict()
        
        self.reload_rail(story)  # Reload the rail to apply changes


    # Called whenever the rail is reordered
    def handle_rail_reorder(self, e: ft.OnReorderEvent, story: Story):
        ''' Reorders our list based on the drag and drop, saves the new order in settings '''
        from models.app import app    # Always grabs updated reference when re-ordering

        workspaces_rail_order = app.settings.data['workspaces_rail_order']

        # Reorders our list based on the drag and drop
        item = workspaces_rail_order.pop(e.old_index)
        workspaces_rail_order.insert(e.new_index, item)

        # Save the new order to settings
        app.settings.data['workspaces_rail_order'] = workspaces_rail_order
        app.settings.save_dict()

        self.reload_rail(story)  # Reload the rail to apply changes

    # Called mostly when re-ordering or collapsing the rail. Also called on start
    def reload_rail(self, story) -> ft.Control:
        ''' Reloads our rail, and applies the correct styles and controls based on the state of the rail '''
        from models.app import app    # Always grabs updated reference when reloading

        # Holds our list of controls that we will add in the rail later
        workspaces_rail = []

        selected_rail = story.data.get('selected_rail', 'content') if story is not None else "content"

        # Creates our rails for each workspace selection, that get added to the workspaces_rail list
        content_rail = ft.NavigationRail(
            height=70,  # Set height of each rail
            bgcolor=ft.Colors.TRANSPARENT,  # Make rail background transparent
            selected_index=None,    # All rails start unselected, we set the right one later
            on_change=lambda e: self.change_workspace(e, story),    # When the rail is clicked

            destinations=[  # Each rail only has one destination
                # We do it this way so we can change the order when re-ordering the rail
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.LIBRARY_BOOKS_OUTLINED), # Icon on the rail
                    selected_icon=ft.Icon(ft.Icons.LIBRARY_BOOKS_ROUNDED, color=ft.Colors.PRIMARY), # Selected icon on the rail
                    padding=ft.Padding.only(top=10, bottom=10), # Padding for spacing
                    # Label underneath the icon and the data we will use to identify the rail
                    data="content", 
                    label=ft.Text(
                        "Content" if app.settings.data.get('workspaces_rail_is_collapsed', False) == False else " ", 
                        no_wrap=True, 
                        theme_style=ft.TextThemeStyle.LABEL_LARGE
                    ) ,  # If not collapsed, show label, if collapsed, hide label
                ),
            ],
        )
        # Characters workspace rail
        characters_rail = ft.NavigationRail(
            height=70,
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.change_workspace(e, story),  
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.PEOPLE_OUTLINE_ROUNDED), 
                    selected_icon=ft.Icon(ft.Icons.PEOPLE_ROUNDED, color=ft.Colors.PRIMARY),
                    padding=ft.Padding.only(top=10, bottom=10),
                    data="characters", 
                    label=ft.Text("Characters" if app.settings.data.get('workspaces_rail_is_collapsed', False) == False else " ", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE) 
                ),
            ],
        )
        # Plot and plotline workspace rail
        plotlines_rail = ft.NavigationRail(
            height=70,  
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.change_workspace(e, story),   
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.TIMELINE_ROUNDED, scale=1.2), 
                    selected_icon=ft.Icon(ft.Icons.TIMELINE_OUTLINED, color=ft.Colors.PRIMARY, scale=1.2),
                    padding=ft.Padding.only(top=10, bottom=10),
                    data="plotlines", 
                    label=ft.Text("Plotlines" if app.settings.data.get('workspaces_rail_is_collapsed', False) == False else " ", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE) 
                ),
            ],
        )
        # World building workspace rail
        world_building_rail = ft.NavigationRail(
            height=70,  
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.change_workspace(e, story),    
            destinations=[
                ft.NavigationRailDestination(
                    #icon=ft.Icon(ft.Icons.MAP_OUTLINED), selected_icon=ft.Icon(ft.Icons.MAP, color=ft.Colors.PRIMARY),
                    icon=ft.Icon(ft.Icons.PUBLIC_OUTLINED),
                    selected_icon=ft.Icon(ft.Icons.PUBLIC, color=ft.Colors.PRIMARY),
                    padding=ft.Padding.only(top=10, bottom=10),
                    data="world_building", 
                    label=ft.Text("World Building" if app.settings.data.get('workspaces_rail_is_collapsed', False) == False else " ", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE)
                ),
            ],
        )
        # Canvas workspace rail
        canvas_rail = ft.NavigationRail(
            height=70,  
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.change_workspace(e, story),  
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DRAW_OUTLINED), 
                    #icon=ft.Icons.BRUSH_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.DRAW_ROUNDED, color=ft.Colors.PRIMARY),
                    padding=ft.Padding.only(top=10, bottom=10),
                    data="canvas", 
                    label=ft.Text("Canvas" if app.settings.data.get('workspaces_rail_is_collapsed', False) == False else " ", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE)
                ),
            ],
        )
        # Planning workspace rail
        planning_rail = ft.NavigationRail(
            height=70,  
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.change_workspace(e, story),  
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.EVENT_NOTE_OUTLINED),
                    selected_icon=ft.Icon(ft.Icons.EVENT_NOTE, color=ft.Colors.PRIMARY),
                    padding=ft.Padding.only(top=10, bottom=10),
                    data="planning", 
                    label=ft.Text("Plan & Design" if app.settings.data.get('workspaces_rail_is_collapsed', False) == False else " ", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE, text_align=ft.TextAlign.CENTER) 
                ),
            ],
        )

        # Reads our selected workspace from ourself, and toggles the correct workspace selection icon
        if selected_rail == "content":
            content_rail.selected_index = 0    # Selects first destination in destination list (cuz there is only one)
        elif selected_rail == "characters":
            characters_rail.selected_index = 0
        elif selected_rail == "plotlines":
            plotlines_rail.selected_index = 0
        elif selected_rail == "world_building":
            world_building_rail.selected_index = 0
        elif selected_rail == "canvas":
            canvas_rail.selected_index = 0
        elif selected_rail == "planning":
            planning_rail.selected_index = 0

        idx = 0
        # Goes through our workspace order, and adds the correct control to our list for the rail
        # We do it this way so when the app re-orders the rail, it will save their changes
        for workspace in app.settings.data['workspaces_rail_order']:     # Just a list of strings
            if workspace == "content":
                workspaces_rail.append(ft.ReorderableDragHandle(content_rail))   # Add our corresponding workspace selector rail to the list
            elif workspace == "characters":
                workspaces_rail.append(ft.ReorderableDragHandle(characters_rail)) 
            elif workspace == "plotlines":
                workspaces_rail.append(ft.ReorderableDragHandle(plotlines_rail))
            elif workspace == "world_building":
                workspaces_rail.append(ft.ReorderableDragHandle(world_building_rail))
            elif workspace == "canvas":
                workspaces_rail.append(ft.ReorderableDragHandle(canvas_rail))
            elif workspace == "planning":
                workspaces_rail.append(ft.ReorderableDragHandle(planning_rail))

            idx += 1


        # If we're collapsed...
        if app.settings.data['workspaces_rail_is_collapsed']:

            self.width = 50     # Make the rail less wide
            
            # Remove our labels below the icons
            content_rail.destinations[0].label_content = None
            characters_rail.destinations[0].label_content = None
            plotlines_rail.destinations[0].label_content = None
            world_building_rail.destinations[0].label_content = None
            canvas_rail.destinations[0].label_content = None
            planning_rail.destinations[0].label_content = None

            # Set our collapsed icon buttons icon depending on collapsed state
            collapse_icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT_ROUNDED

        # If not collapsed, make rail normal size and set the correct icon
        else:
            self.width = 120
            collapse_icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT_ROUNDED


        # Set our collapsed icon button using our defined icon above
        collapse_icon_button = ft.IconButton(
            icon=collapse_icon,
            on_click=lambda e: self.toggle_collapse_rail(e, story),
            mouse_cursor=ft.MouseCursor.CLICK
        )

        # Sets our content as a column. This will fill our width and hold...
        # Either our list of workspaces, or a reorderable list of our workspaces
        self.content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=18,
        )

        # If we're reorderable, make our reorderable rail using a reorderable list
        reorderable_list = ft.ReorderableListView(
            padding=4, show_default_drag_handles=False,
            on_reorder=lambda e: self.handle_rail_reorder(e, story),
        )

        # Add our workspaces (rails) to the list. Add the list to our column
        reorderable_list.controls.extend(workspaces_rail)  
        self.content.controls.append(reorderable_list)

        # Fill in empty space under the rail, before the collapse icon button at the bottom
        self.content.controls.append(ft.Container(expand=True))

        # Add our collapse icon button to the right side of the rail
        self.content.controls.append(ft.Row(
            spacing=0, 
            controls=[
                ft.Container(expand=True),  # Fills left side of row
                collapse_icon_button,
            ]), 
        )

        # Can fail when changing views. It only fails tho when it doesnt need to update
        try: 
            self.update()
        except Exception as e:
            pass