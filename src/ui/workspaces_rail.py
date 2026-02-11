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
            alignment=ft.alignment.center,  # Aligns content to the 
            padding=ft.padding.only(bottom=10, right=2, left=2),
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        )

        # Build our rail on start
        self.reload_rail(story)


    # Called whenever we select a new workspace selector rail
    def on_workspace_change(self, e, story: Story):
        ''' Changes our selected workspace in settings and for our object.
        Applies the correct active rail to match the selection '''
        from models.app import app
        
        # Save our newly selected workspace in the settings, and save it for our object (just easier for referencing)
        if story is not None:   # Make objects later, rather than return functions

            # Catch unneccessary reloads when we are already on the selected rail (Canvas Rail doesn't like it):
            if story.data.get('selected_rail', 'content') == e.control.destinations[e.control.selected_index].data:
                return
        
            # Save and reload new rail
            story.data['selected_rail'] = e.control.destinations[e.control.selected_index].data
            story.save_dict()
            story.active_rail.display_active_rail(story)


    # Called by clicking button on bottom right of rail
    def toggle_collapse_rail(self, e, story: Story):
        ''' Collapses or expands the rail, and saves the state in settings '''
        from models.app import app    # Always grabs updated reference when collapsing/expanding

        # Toggle our collapsed state
        app.settings.data['workspaces_rail_is_collapsed'] = not app.settings.data['workspaces_rail_is_collapsed']
        app.settings.save_dict()
        
        self.reload_rail(story)  # Reload the rail to apply changes


    # Called mostly when re-ordering or collapsing the rail. Also called on start
    def reload_rail(self, story) -> ft.Control:
        ''' Reloads our rail, and applies the correct styles and controls based on the state of the rail '''
        from models.app import app    # Always grabs updated reference when reloading

        selected_rail = story.data.get('selected_rail', 'content') if story is not None else "content"

        # Creates our rails for each workspace selection, that get added to the workspaces_rail list
        nav_rail = ft.NavigationRail(
            expand=True, bgcolor=ft.Colors.TRANSPARENT,  
            selected_index=None,
            on_change=lambda e: self.on_workspace_change(e, story),    
            destinations=[  
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.LIBRARY_BOOKS_OUTLINED), # Icon on the rail
                    selected_icon=ft.Icon(ft.Icons.LIBRARY_BOOKS_ROUNDED, color=ft.Colors.PRIMARY), # Selected icon on the rail
                    padding=ft.padding.only(top=10, bottom=10), # Padding for spacing
                    data="content", label_content=ft.Text("Content", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.PEOPLE_OUTLINE_ROUNDED), 
                    selected_icon=ft.Icon(ft.Icons.PEOPLE_ROUNDED, color=ft.Colors.PRIMARY),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="characters", label_content=ft.Text("Characters", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.TIMELINE_ROUNDED, scale=1.2), 
                    selected_icon=ft.Icon(ft.Icons.TIMELINE_OUTLINED, color=ft.Colors.PRIMARY, scale=1.2),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="plotlines", label_content=ft.Text("Plotlines", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.PUBLIC_OUTLINED),
                    selected_icon=ft.Icon(ft.Icons.PUBLIC, color=ft.Colors.PRIMARY),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="world_building", label_content=ft.Text("World Building", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DRAW_OUTLINED), 
                    selected_icon=ft.Icon(ft.Icons.DRAW_ROUNDED, color=ft.Colors.PRIMARY),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="canvas", label_content=ft.Text("Canvas", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.EVENT_NOTE_OUTLINED),
                    selected_icon=ft.Icon(ft.Icons.EVENT_NOTE, color=ft.Colors.PRIMARY),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="planning", label_content=ft.Text("Planning", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
            ],
        )
        
    

        # Reads our selected workspace from ourself, and toggles the correct workspace selection icon
        if selected_rail == "content":
            nav_rail.selected_index = 0    # Selects first destination in destination list (cuz there is only one)
        elif selected_rail == "characters":
            nav_rail.selected_index = 1
        elif selected_rail == "plotlines":
            nav_rail.selected_index = 2
        elif selected_rail == "world_building":
            nav_rail.selected_index = 3
        elif selected_rail == "canvas":
            nav_rail.selected_index = 4
        elif selected_rail == "planning":
            nav_rail.selected_index = 5

        # If we're collapsed...
        if app.settings.data['workspaces_rail_is_collapsed']:

            self.width = 50     # Make the rail less wide

            for destination in nav_rail.destinations:
                destination.label_content = ft.Text("", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE)   # Remove labels below icons

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
        )


        self.content = ft.Column([
            nav_rail,
            #ft.Container(expand=True),
            ft.Row(
                spacing=0, 
                controls=[
                    ft.Container(expand=True),  # Fills left side of row
                    collapse_icon_button,
                ]
            ),
        ], expand=True)

        # Can fail when changing views. It only fails tho when it doesnt need to update
        try: 
            self.update()
        except Exception as e:
            pass
        
        
# Class so we can store our all workspaces rail as an object inside of app
class ReorderableWorkspacesRail(ft.Container):
    
    # Constructor for our all_workspaces_rail object. Needs a page reference passed in
    def __init__(self, page: ft.Page, story: Story = None):

        self.p = page   # Page reference
       
        # Style our rail (container)
        super().__init__(
            alignment=ft.alignment.center,  # Aligns content to the 
            padding=ft.padding.only(bottom=10, right=2, left=2),
            animate=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        )

        # Build our rail on start
        self.reload_rail(story)

    

    # Called whenever we select a new workspace selector rail
    def on_workspace_change(self, e, story: Story):
        ''' Changes our selected workspace in settings and for our object.
        Applies the correct active rail to match the selection '''
        
        # Save our newly selected workspace in the settings, and save it for our object (just easier for referencing)
        if story is not None:   # Make objects later, rather than return functions
            story.data['selected_rail'] = e.control.destinations[0].data
            story.save_dict()

            # Has the active rail grab its new selection
            story.active_rail.display_active_rail(story) 

            # Reloads our own rail to reflect icon changes
            self.reload_rail(story)  # Reload the rail to apply the new selection


        # Handle when there is no active story (shouldn't happen)
        else:
            print("No active story, cannot change active rail")


    # Called by clicking button on bottom right of rail
    def toggle_collapse_rail(self, e, story: Story):
        ''' Collapses or expands the rail, and saves the state in settings '''
        from models.app import app    # Always grabs updated reference when collapsing/expanding

        # Disable reorder before collapsing if reorder is enabled
        if app.settings.data['workspaces_rail_is_reorderable']:
            app.settings.data['workspaces_rail_is_reorderable'] = False
            app.settings.save_dict()

        # Toggle our collapsed state
        app.settings.data['workspaces_rail_is_collapsed'] = not app.settings.data['workspaces_rail_is_collapsed']
        app.settings.save_dict()
        
        self.reload_rail(story)  # Reload the rail to apply changes


    # Called by clicking re-order rail button in the settings.
    def toggle_reorder_rail(self, story: Story, value: bool = None):
        ''' Toggles the reorderable state of the rail, and saves the state in settings '''
        from models.app import app    # Always grabs updated reference when re-ordering

        # If we're collapsed, expand the rail first
        if app.settings.data['workspaces_rail_is_collapsed']:
            app.settings.data['workspaces_rail_is_collapsed'] = False
            app.settings.save_dict()

        # Toggle our reorderable state, and save it in settings
        if value is not None:
            app.settings.data['workspaces_rail_is_reorderable'] = value
        else:
            app.settings.data['workspaces_rail_is_reorderable'] = not app.settings.data['workspaces_rail_is_reorderable']
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
            on_change=lambda e: self.on_workspace_change(e, story),    # When the rail is clicked

            destinations=[  # Each rail only has one destination
                # We do it this way so we can change the order when re-ordering the rail
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.LIBRARY_BOOKS_OUTLINED), # Icon on the rail
                    selected_icon=ft.Icon(ft.Icons.LIBRARY_BOOKS_ROUNDED, color=ft.Colors.PRIMARY), # Selected icon on the rail
                    padding=ft.padding.only(top=10, bottom=10), # Padding for spacing
                    # Label underneath the icon and the data we will use to identify the rail
                    data="content", label_content=ft.Text("Content", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
            ],
        )
        # Characters workspace rail
        characters_rail = ft.NavigationRail(
            height=70,
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.on_workspace_change(e, story),  
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.PEOPLE_OUTLINE_ROUNDED), 
                    selected_icon=ft.Icon(ft.Icons.PEOPLE_ROUNDED, color=ft.Colors.PRIMARY),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="characters", label_content=ft.Text("Characters", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
            ],
        )
        # Plot and plotline workspace rail
        plotlines_rail = ft.NavigationRail(
            height=70,  
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.on_workspace_change(e, story),   
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.TIMELINE_ROUNDED, scale=1.2), 
                    selected_icon=ft.Icon(ft.Icons.TIMELINE_OUTLINED, color=ft.Colors.PRIMARY, scale=1.2),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="plotlines", label_content=ft.Text("Plotlines", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
            ],
        )
        # World building workspace rail
        world_building_rail = ft.NavigationRail(
            height=70,  
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.on_workspace_change(e, story),    
            destinations=[
                ft.NavigationRailDestination(
                    #icon=ft.Icon(ft.Icons.MAP_OUTLINED), selected_icon=ft.Icon(ft.Icons.MAP, color=ft.Colors.PRIMARY),
                    icon=ft.Icon(ft.Icons.PUBLIC_OUTLINED),
                    selected_icon=ft.Icon(ft.Icons.PUBLIC, color=ft.Colors.PRIMARY),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="world_building", label_content=ft.Text("World Building", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
            ],
        )
        # Canvas workspace rail
        canvas_rail = ft.NavigationRail(
            height=70,  
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.on_workspace_change(e, story),  
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DRAW_OUTLINED), 
                    #icon=ft.Icons.BRUSH_OUTLINED,
                    selected_icon=ft.Icon(ft.Icons.DRAW_ROUNDED, color=ft.Colors.PRIMARY),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="canvas", label_content=ft.Text("Canvas", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
                ),
            ],
        )
        # Planning workspace rail
        planning_rail = ft.NavigationRail(
            height=70,  
            bgcolor=ft.Colors.TRANSPARENT,
            selected_index=None,
            on_change=lambda e: self.on_workspace_change(e, story),  
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.EVENT_NOTE_OUTLINED),
                    selected_icon=ft.Icon(ft.Icons.EVENT_NOTE, color=ft.Colors.PRIMARY),
                    padding=ft.padding.only(top=10, bottom=10),
                    data="planning", label_content=ft.Text("Planning", no_wrap=True, theme_style=ft.TextThemeStyle.LABEL_LARGE),
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


        # Goes through our workspace order, and adds the correct control to our list for the rail
        # We do it this way so when the app re-orders the rail, it will save their changes
        for workspace in app.settings.data['workspaces_rail_order']:     # Just a list of strings
            if workspace == "content":
                workspaces_rail.append(content_rail)   # Add our corresponding workspace selector rail to the list
            elif workspace == "characters":
                workspaces_rail.append(characters_rail)    
            elif workspace == "plotlines":
                workspaces_rail.append(plotlines_rail)
            elif workspace == "world_building":
                workspaces_rail.append(world_building_rail)
            elif workspace == "canvas":
                workspaces_rail.append(canvas_rail)
            elif workspace == "planning":
                workspaces_rail.append(planning_rail)


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
        )

        # Sets our content as a column. This will fill our width and hold...
        # Either our list of workspaces, or a reorderable list of our workspaces
        self.content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=18,
        )

        # If we're reorderable, make our reorderable rail using a reorderable list
        if app.settings.data['workspaces_rail_is_reorderable']:

            # Can only reorder if on settings page, so check for that
            if self.p.route == "/settings":
                reorderable_list = ft.ReorderableListView(
                    padding=4,
                    on_reorder=lambda e: self.handle_rail_reorder(e, story),
                )

                # Add our workspaces (rails) to the list. Add the list to our column
                reorderable_list.controls.extend(workspaces_rail)  
                self.content.controls.append(reorderable_list)
            else:

                # If we're not on settings page, set it so we are not reorderable and build our normal rail
                app.settings.data['workspaces_rail_is_reorderable'] = False
                app.settings.save_dict()

                self.content.controls.extend(workspaces_rail) 

        # If we're not reorderable, add the selector workspaces (rails) to the column
        else:
            self.content.controls.extend(workspaces_rail) 

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
