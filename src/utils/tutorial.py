''' Returns a list of controls the tutorial story will use in the overlay '''
import flet as ft
import flet_shadcn_ui as shad
import shutil
import os
import math
from styles.card import Card

LAST_TUTORIAL_STEP = 18


def run_tutorial(story) -> list[ft.Control]:
    from models.app import app

    async def _end_tutorial_clicked(e: ft.Event=None):
        ''' Ends the tutorial and routes to the home page '''

        async def _confirm_exit(e: ft.Event):
            # Delete the story from the app's storage and remove its directory from the filesystem. 
            # Otherwise this creates a new story everytime the tutorial is run
            try:
                
                story_id = story.data.get('id')
                app.settings.story = None                    

                story_dir_path = story.data.get('directory_path')
                full_norm = os.path.normcase(os.path.normpath(story_dir_path))
                
                # Delete the folder from storage
                shutil.rmtree(full_norm)

                ft.context.page.pop_dialog()
                await ft.context.page.push_route("/")
                #ft.context.page.show_dialog(shad.Toast(f"{story.data.get('title', 'Story')} deleted successfully."))

                ft.context.page.title = "StoryBoard (alpha)"
                ft.context.page.update()

            except Exception as e:
                print(f"Error deleting story: {e}")
            await app.load_previous_story(page) # Loads last story if there is one
            page.show_dialog(shad.Toast("You can access the tutorial anytime in Settings -> Resources", duration=7000))

        page.show_dialog(shad.Dialog(
            title="Are you sure you want to exit the tutorial?", 
            actions=[
                shad.Button("No, Continue Tutorial", on_click=lambda _: page.pop_dialog(), color=ft.Colors.ERROR, size=shad.ButtonSize.SM, variant=shad.ButtonVariant.OUTLINE),
                shad.Button("Yes, Exit Tutorial", on_click=_confirm_exit, color=ft.Colors.PRIMARY, size=shad.ButtonSize.SM, variant=shad.ButtonVariant.DESTRUCTIVE)
            ]
        ))

    # Load the previous tutorial step
    async def previous_tutorial_step(e: ft.Event=None):
        nonlocal tutorial_step
        if tutorial_step > 0:
            tutorial_step -= 1
            await load_tutorial_step()

    # Load the next tutorial step
    async def next_tutorial_step(e: ft.Event=None):
        nonlocal tutorial_step
        if tutorial_step < LAST_TUTORIAL_STEP:
            tutorial_step += 1
        await load_tutorial_step()

    async def create_widget(widget_tag: str):
        
        # If we didn't find the widget (user deleted it), create it
        title = widget_tag.replace("_", " ").title()
        for w in story.widgets.values():
            if w.data.get('tag', '') == widget_tag:
                await w.show_widget()   # Show them if their tags match
                return
        await story.create_widget(title, widget_tag)
       
        
    # Give us the actual content of the current tutorial step
    async def load_tutorial_step():
        nonlocal tutorial_step
            
        match tutorial_step:
            case 0:
                tutorial_title.value = "StoryBoard"
                tutorial_tip_container.left = page.width / 2 - 175
                tutorial_tip_container.top = page.height / 2 - 150
                tutorial_arrow.visible = False
                tutorial_tip.value = "StoryBoard is a story creation and organizational tool for both novel and comic based authors, meant to be used by itself or in tandem with other creative tools." \
                        "\n\nThis tutorial will give you a quick introduction to everything you will need when creating your masterpiece!" \
                        "\n\nUse the buttons at the bottom of the app for, previous step, next step, or to exit the tutorial." \
                        "\n\nKeep in mind, any changes you make will be deleted upon exiting the tutorial."
            case 1:
                
                tutorial_arrow.visible = True
                tutorial_title.value = "File Menu"
                tutorial_tip.value = "This is the File Menu, where you will manage your stories, exporting, and settings."
                
                tutorial_tip_container.left = 60
                tutorial_tip_container.top = 50
                tutorial_arrow.left = 20
                tutorial_arrow.top = 50
                
            case 2:
                tutorial_title.value = "Settings"
                tutorial_tip.value = "You can also open the settings from here"
                tutorial_tip_container.left 
                tutorial_arrow.left = page.width - 32
                tutorial_tip_container.left = tutorial_arrow.left - 20 - tutorial_tip_container.width
                tutorial_arrow.top = 50
                tutorial_tip_container.top = 50
                tutorial_arrow.icon = ft.Icons.ARROW_UPWARD
            case 3:
                tutorial_title.value = "Cloud Connect"
                tutorial_tip.value = "Connect to the cloud here or in the settings to save and sync your work across devices."
                tutorial_arrow.left = page.width - 72
                tutorial_arrow.top = 50
                tutorial_arrow.icon = ft.Icons.ARROW_UPWARD
                tutorial_tip_container.left = tutorial_arrow.left - 20 - tutorial_tip_container.width
                tutorial_tip_container.top = 50
                tree_view_rail.visible = False
                tree_view_rail_resizer.visible = False
                workspace.visible = False
                workspace.update()
                tree_view_rail_resizer.update()
                tree_view_rail.update()

                
            
            case 4:
                
                tutorial_title.value = "Create Items"
                tutorial_tip.value = "Create new Widgets here, and folders to organize them." \
                    "\n\nWidgets are the building blocks of your story. We'll go through them one by one soon."
                tutorial_arrow.top = 56
                tutorial_tip_container.top = 56
                tutorial_tip_container.left = 240
                tutorial_arrow.left = 200
                tutorial_arrow.visible = True
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
                tutorial_arrow.flip = None
                tree_view_rail.visible = True
                tree_view_rail_resizer.visible = True
                workspace.visible = True
                workspace.update()
                tree_view_rail_resizer.update()
                tree_view_rail.update()

            case 5:
                tutorial_title.value = "Workspace"
                tutorial_tip.value = "Here is your workspace. This is where you can build your widgets\n\nLet's go through each widget one by one."
                
                tutorial_tip_container.top = page.height - 370
                tutorial_tip_container.left = 0
                tutorial_arrow.left = tutorial_tip_container.left + tutorial_tip_container.width - 40
                tutorial_arrow.top = page.height - 410
                tutorial_arrow.visible = True
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
                tutorial_arrow.flip = ft.Flip(True)
                
            case 6:
                tutorial_title.value = "Manuscript"
                tutorial_tip.value = "The meat and potatoes for creating all novel-based stories.\n\n" \
                    "Similar to Google Docs and Microsoft Word, use the manuscript widget as your built-in text editor.\n\n" \
                    "Many widgets have sidebars on the right side for additional info and options."
                await create_widget("manuscript")
            case 7:
                tutorial_title.value = "Character"
                tutorial_tip.value = "A widget for all the characters in your story." \
                "\n\nFlesh out your characters looks, personality, origin, arcs, etc." \
                "\n\nOpen settings -> templates to customize your character template."
                await create_widget("character")
            case 8:
                tutorial_title.value = "Note"
                tutorial_tip.value = "The perfect note-card organization board for all your ideas, themes, research, and anything else you can imagine."
                await create_widget("note")
            case 9:
                tutorial_title.value = "Kanban"
                tutorial_tip.value = "A widget for organizing tasks and story elements in a Kanban board style." \
                "\n\nCreate columns for different stages of your workflow and move cards between them as you progress." \
                "\n\nOpen settings -> templates to customize your Kanban template."
                await create_widget("kanban")
            case 10:
                tutorial_title.value = "Plotline"
                tutorial_tip.value = "Plotlines help visualize your Story's progression using plot points and markers." \
                "\n\nRight click the plotline to add new plot points or markers, and to see the rest of the options. " \
                "These options can be set to default for all new Plotlines in settings -> widgets" \
                "\n\nThis widget also works well for tracking D&D Campaigns :)"
                await create_widget("plotline")
            case 11:
                tutorial_title.value = "Plot Chart"
                tutorial_tip.value = "As the alternative to Plotlines, Plot Charts allow you to organize your Story's progression in a node-edge based structure." \
                "\n\nThese particularly shine when you need to track complex storylines with multiple branching paths." \
                "\n\nRight click anywhere on the stack to add a new Node, then drag the connectors to connect to other Nodes."
                await create_widget("plot_chart")
            case 12:
                tutorial_title.value = "Item"
                tutorial_tip.value = "A widget for all items, weapons, armor, and MacGuffins in your story." \
                "\n\nFlesh out their size, abilities, looks, cost, and any other ideas you have!" \
                "\n\nOpen settings -> templates to customize your item template."
                await create_widget("item")
            case 13:
                tutorial_title.value = "World"
                tutorial_tip.value = "Build your world(s) in your story in their entirety." \
                "\n\nCreate your lore, power systems, government, geography and more!" \
                "\n\nOpen settings -> templates to customize your world template."
                await create_widget("world")
            case 14:
                tutorial_title.value = "Map"
                tutorial_tip.value = "A widget for visualizing the geography of your world." \
                "\n\nRight click the map to create locations with fleshed out information, or change the background image." \
                "\n\nDraw your own maps using StoryBoard, or upload an existing file to use as the map."
                await create_widget("map")
            case 15:
                tutorial_title.value = "Radar Chart"
                tutorial_tip.value = "The radar chart is the ultimate vizualization of any power system in your story." \
                "\n\nUse it to compare different characters, abilities, or any other elements in your story." \
                "\n\nUse the sidebar to add new datasets and nodes, and adjust options about the chart."
                await create_widget("radar_chart")
            case 16:
                tutorial_title.value = "Bar Chart"
                tutorial_tip.value = "One of the most common ways to visualize data in your story." \
                "\n\nUse it to compare different characters, abilities, or any other elements in your story." \
                "\n\nUse the sidebar to add new groups and rods, and adjust options about the chart."
                await create_widget("bar_chart")
            case 17:
                tutorial_title.value = "Connection Map"
                tutorial_tip.value = "Visualize connections between characters or any other widgets in your story." \
                "\n\nDrag widgets from the rail onto the stack to add them to the Connection Map. Drag between characters to create or delete a connection."
                "\n\nThis widget can be particularly useful for romance stories."
                await create_widget("connection_map")   
                tutorial_tip_container.top = page.height - 370
                tutorial_tip_container.left = 0
                tutorial_arrow.left = tutorial_tip_container.left + tutorial_tip_container.width - 40
                tutorial_arrow.top = page.height - 410
                tutorial_arrow.visible = True
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
                tutorial_arrow.rotate = None
                #tutorial_arrow.flip = ft.Flip(True)
            

            case 18:
                tutorial_title.value = "Tutorial Complete!"
                tutorial_tip.value = "Get out there and create your masterpiece!"
                tutorial_tip_container.left = page.width / 2 - 175
                tutorial_tip_container.top = page.height / 2 - 150
                tutorial_arrow.top = page.height - 90
                tutorial_arrow.left = page.width / 2 - 12
                tutorial_arrow.rotate = ft.Rotate(math.pi / 2 * 3)
                tutorial_arrow.visible = True

        '''
        case 18:
            tutorial_title.value = "Canvas"
            tutorial_tip.value = "Now we are getting into the comic-based widgets." \
            "\n\nThe Canvas is the main widget for drawing and creating all comic-based stories. Use the sidebar to create new layers, and apply effects to them." \
            "\n\nCreate your own masterpieces or upload exported files from another drawing app!"
            await create_widget("canvas")
        case 19:
            tutorial_title.value = "Canvas Board"
            tutorial_tip.value = "A widget for planning out comic-based chapters for your story." \
            "\n\nDescribe and sketch out your ideas for all you panels ahead of time, " \
            "then connect them to a Canvas or an exported file from another drawing app and watch your Chapter progress."
            await create_widget("canvas_board")
            
        case 20:
            tutorial_title.value = "Comic Preview"
            tutorial_tip.value = "Preview how a comic chapter will look with all its panels stitched together." \
            "\n\nAdd panels from the sidebar to your preview, adjust their order and layout as needed."
            await create_widget("comic_preview")
            tutorial_arrow.visible = True
            tutorial_tip_container.top = page.height - 320
            tutorial_tip_container.left = 10
            tutorial_arrow.left = tutorial_tip_container.left + tutorial_tip_container.width - 40
            tutorial_arrow.top = page.height - 360
        '''
            
            
        tutorial_tip_container.update()
        tutorial_arrow.update()

    # Grab our variables so we can hide and show them when we want
    page: ft.Page = story.page
    #canvas_rail = story.canvas_rail
    tree_view_rail = story.tree_view_rail
    tree_view_rail_resizer = story.tree_view_rail_resizer
    workspace = story.workspace

    # Rails start hidden
    tree_view_rail.visible = False
    tree_view_rail.width = 275  # Set size early since it fits well
    tree_view_rail_resizer.visible = False
    workspace.visible = False

    # Update elements manually, since story excludes itself from automatic updates
    tree_view_rail.update()
    tree_view_rail_resizer.update()
    workspace.update()

    tutorial_title = ft.Text("StoryBoard", theme_style=ft.TextThemeStyle.TITLE_LARGE, weight=ft.FontWeight.BOLD,)
        
    tutorial_tip = ft.Text(
        "StoryBoard is a story creation and organizational tool for both novel and comic based authors, meant to be used by itself or in tandem with other creative tools." \
        "\n\nThis tutorial will give you a quick introduction to everything you will need when creating your masterpiece!" \
        "\n\nUse the buttons at the bottom of the app for, previous step, next step, or to exit the tutorial." \
        "\n\nKeep in mind, any changes you make will be deleted upon exiting the tutorial.", 
    )
        
    tutorial_step = 0

    tutorial_tip_container = Card(
        content=ft.Column([
            tutorial_title,
            tutorial_tip,
        ]),
        width=275, bgcolor=ft.Colors.SURFACE,
        left=page.width / 2 - 175, top=page.height / 2 - 150,
        animate_position=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        shadow=ft.BoxShadow(1, 1, color=ft.Colors.SURFACE)
    )

    tutorial_arrow = ft.Icon(
        ft.Icons.ARROW_UPWARD, ft.Colors.PRIMARY, scale=1.5, left=20, top=10, animate_position=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        visible=False
    )
    
                
    return [
        tutorial_tip_container,
        tutorial_arrow,
        
        ft.Row([
            shad.Button(
                "Prev", ft.Icons.UNDO,
                on_click=previous_tutorial_step, 
                variant=shad.ButtonVariant.PRIMARY, size=shad.ButtonSize.LG,
            ),
            shad.Button(
                "Exit Tutorial", 
                on_click=_end_tutorial_clicked, variant=shad.ButtonVariant.DESTRUCTIVE, size=shad.ButtonSize.LG
            ),
            shad.Button(
                "Next", ft.Icons.REDO,
                on_click=next_tutorial_step, 
                variant=shad.ButtonVariant.PRIMARY, size=shad.ButtonSize.LG,
            ),
        ], bottom=10, left=0, right=0, alignment=ft.MainAxisAlignment.CENTER),
    ]