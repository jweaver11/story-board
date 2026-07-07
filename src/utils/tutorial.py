''' Returns a list of controls the tutorial story will use in the overlay '''
import flet as ft
import asyncio
from styles.snack_bar import SnackBar

import shutil
import os


def run_tutorial(story) -> list[ft.Control]:
    from models.app import app

    async def _end_tutorial_clicked(e: ft.Event=None):
        ''' Ends the tutorial and routes to the home page '''

        async def _confirm_exit(e: ft.Event):
            await app.load_previous_story(page)
            page.show_dialog(SnackBar("You can access the tutorial anytime in Settings -> Resources", duration=7000))

        page.show_dialog(ft.AlertDialog(
            title="Are you sure you want to exit the tutorial?", 
            actions=[
                ft.Button("No, keep going", on_click=lambda _: page.pop_dialog(), color=ft.Colors.PRIMARY, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK)),
                ft.Button("Yes, exit tutorial", on_click=_confirm_exit, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK))
            ]
        ))

    # Load the previous tutorial step
    async def _previous_tutorial_step(e: ft.Event=None):
        nonlocal tutorial_step
        if tutorial_step > 0:
            tutorial_step -= 1
            await load_tutorial_step()

    # Load the next tutorial step
    async def _next_tutorial_step(e: ft.Event=None):
        nonlocal tutorial_step
        tutorial_step += 1
        await load_tutorial_step()

    # Clears out any content in the story's content directory and clears the widgets list
    async def clear_story_content():
        story.widgets.clear()
        folder_path = story.data.get('content_directory_path')
        if os.path.exists(folder_path) and os.path.isdir(folder_path):  
            for entry in os.scandir(folder_path):
                try:
                    if entry.is_dir(follow_symlinks=False):
                        shutil.rmtree(entry.path)
                    else:
                        os.remove(entry.path)  # files + symlinks
                except Exception as e:
                    print(f"Error deleting {entry.path}: {e}")
        story.workspace.reload_workspace()
        story.active_rail.reload_rail()

    # Give us the actual content of the current tutorial step
    async def load_tutorial_step():
        nonlocal tutorial_step
        nonlocal folder_created, document_created, note_created, character_created, canvas_created, plotline_created, canvas_board_created, map_created, world_created, item_created, plot_chart_created, comic_preview_created, bar_chart_created, radar_chart_created, character_connection_map_created
            
        #tutorial_tip.value = "StoryBoard is a story creation and organizational tool for both novel and comic based authors. \n\nThis tutorial will give you a quick introduction to everything you will need when creating your masterpiece!\n\nUse the buttons at the bottom of the app for, previous step, next step, or to exit the tutorial.", 

        match tutorial_step:
            case 0:
                previous_tip_button.disabled = True 
                previous_tip_button.icon_color = ft.Colors.OUTLINE_VARIANT
                previous_tip_button.update()
                tutorial_tip_container.left = page.width / 2 - 150
                tutorial_tip_container.top = page.height / 2 - 150
                tutorial_arrow.visible = False
                progress_text.value = f"{str(tutorial_step)}/30"
                tutorial_tip.value = "StoryBoard is a story creation and organizational tool for both novel and comic based authors. \n\nThis tutorial will give you a quick introduction to everything you will need when creating your masterpiece!\n\nUse the buttons below for next step, previous step, or to exit the tutorial."
            case 1:
                previous_tip_button.disabled = False
                previous_tip_button.icon_color = ft.Colors.PRIMARY
                previous_tip_button.update()
                tutorial_arrow.visible = True
                progress_text.value = f"{str(tutorial_step)}/30"
                tutorial_tip.value = "This is the menu bar, where you can access app settings, account settings, and more!\n\nHovering over most things will show a tooltip with more information on them!"
                
                tutorial_tip_container.left = 70
                tutorial_tip_container.top = 50
                tutorial_arrow.left = 20
                tutorial_arrow.top = 50
                
            case 2:
                tutorial_tip.value = "You can also open the settings from here"
                tutorial_tip_container.left = page.width - tutorial_tip_container.width - 50
                tutorial_arrow.left = page.width - 32
                tutorial_arrow.icon = ft.Icons.ARROW_UPWARD
                workspaces_rail.visible = False
                workspaces_rail.update()
            case 3:
                tutorial_tip.value = "This is the rail that lets you select between different active rails. \n\nDrag the icons up and down to reorder them"
                tutorial_tip_container.left = 140
                tutorial_tip_container.top = 100
                tutorial_arrow.left = 140
                tutorial_arrow.top = 265
                tutorial_arrow.icon = ft.Icons.ARROW_BACK

                workspaces_rail.visible = True
                workspaces_rail.update()
            case 4:
                tutorial_tip.value = "Collapse or expand the rail here"
                tutorial_arrow.top = page.height - 43
                tutorial_tip_container.top = page.height - 100
                tutorial_tip_container.left = 150
                tutorial_arrow.left = 140
                active_rail.visible = False
                active_rail_resizer.visible = False
                active_rail.update()
                active_rail_resizer.update()
                
            case 5:

                tutorial_tip.value = "This is the active rail. It shows the currently selected rail, and lets you select between the different rails. \n\nDrag the right side to resize it"
                tutorial_arrow.top = page.height / 2 - 50
                tutorial_tip_container.top = page.height / 2 - 10
                tutorial_arrow.left = 410
                tutorial_tip_container.left = 410
                active_rail.visible = True
                active_rail_resizer.visible = True
                active_rail.update()
                active_rail_resizer.update()
            case 6:
                workspaces_rail.change_workspace(None, story=story, force_rail="content")
                tutorial_tip.value = "Lets start with the content rail. This is where you create and upload Folders and Widgets.\n\nWidgets are the building blocks of your story, from characters, plotlines, world building, notes, documents, and more!"
                tutorial_arrow.top = 60
                tutorial_tip_container.top = 60
                tutorial_tip_container.left = 370
                tutorial_arrow.left = 320
            case 7:
                workspace.visible = False
                workspace.update()
                if not folder_created:
                    await story.create_folder(story.data.get('content_directory_path'), "Folder")
                    folder_created = True
                if not document_created:
                    await story.create_widget("Document", "document")
                    document_created = True
                tutorial_tip.value = "Here is what a folder and a widget look like. Right click it to see its options.\n\nDrag widgets to and from folders to move them.\n\nNext we'll look at each widget. Feel free to interact with them as we go along, but know your work won't be saved."
                tutorial_arrow.top = 120
                tutorial_tip_container.top = 120
                tutorial_tip_container.left = 440
                tutorial_arrow.left = 400
                tutorial_arrow.visible = True
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
                
            case 8:
                tutorial_tip.value = None
                workspace.visible = True
                workspace.update()
                tutorial_arrow.top = page.height - 340
                tutorial_arrow.left = 350
                tutorial_arrow.icon = ft.Icons.ARROW_FORWARD
                tutorial_tip_container.left = 50
                tutorial_tip_container.top = page.height - 300
                #widget = Document("Document Widget", page, story.data.get('content_directory_path'), story)
                #workspace.content = widget
                #workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Document:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("The main widget for creating all novel-based stories. Similar to Microsoft Word or Google Docs, use the document widget as a fully built text editor.\n\nAdd your own comments or references images to the side of any document!", style=ft.TextStyle(size=16))
                ]
                tutorial_tip.value = None
            case 9:
                
                #if not canvas_created:
                    #await story.create_widget("Canvas", "canvas")
                    #canvas_created = True
                tutorial_tip.spans=[
                    ft.TextSpan("Canvas:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("The main widget for creating all comic-based stories. This widget allows illustrators to watch their ideas come to life on the Canvas.\n\nCreate your own drawing masterpiece or upload exported files from another drawing app!", style=ft.TextStyle(size=16))
                ]
            case 10:
                if not note_created:
                    await story.create_widget("Note", "note")
                    note_created = True
                tutorial_tip.spans=[
                    ft.TextSpan("Note:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for all your ideas, themes, research, etc.\n\nSelect the 'New Segment' button in the bottom right to seperate ideas.", style=ft.TextStyle(size=16))
                ]
            case 11:
                if not character_created:
                    await story.create_widget("Character", "character")
                    character_created = True
                tutorial_tip.spans=[
                    ft.TextSpan("Character:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for all the characters in your story. Flesh out your characters physical look, personality, origin, arcs, etc!\n\nSelect the 'New Section' button in the bottom right to seperate ideas.\n\nYou can also create character templates in Settings -> templates", style=ft.TextStyle(size=16))
                ]
            case 12:
                #widget = Plotline("Plotline Widget", page, story.data.get('content_directory_path'), story)
                #workspace.content = widget
                #workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Plotline:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the progression of your story. Create multiple plotlines for arcs, sub arcs, plot points, or regression & multi-timeline stories.", style=ft.TextStyle(size=16))
                ]
            case 13:
                #widget = Map("Map Widget", page, story.data.get('content_directory_path'), story)
                #workspace.content = widget
                #workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Map:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the geography of your world.\n\nCreate maps of continents, countries, cities, forests, dungeons, etc.\n\nMaps allow you to create locations with fleshed out information and label important areas.", style=ft.TextStyle(size=16))
                ]
            case 14:
                if not character_connection_map_created:
                    await story.create_widget("Character Relationship Map", "character_connection_map")
                    character_connection_map_created = True
                tutorial_tip.spans=[
                    ft.TextSpan("Character Connection Map:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the relationships between your characters.\n\nVisualize family trees, social connections, friends, enemies, and anything your heart desires.\n\nThis widget can be particularly useful for romance stories.", style=ft.TextStyle(size=16))
                ]
            case 15:
                if not world_created:
                    await story.create_widget("World", "world")
                    world_created = True
                tutorial_tip.spans=[
                    ft.TextSpan("World:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for fleshing out to ideas of your world.\n\nCreate your lore, power systems, government, geography and more!\n\nSelect the 'New Section' button in the bottom right to seperate ideas.\n\nYou can also create character templates in Settings -> templates", style=ft.TextStyle(size=16))
                ]
            case 16:
                if not item_created:
                    await story.create_widget("Item", "item")
                    item_created = True
                tutorial_tip.spans=[
                    ft.TextSpan("Item:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for all items, weapons, armor, and MacGuffins in your story!\n\nFlesh out their size, abilities, looks, cost, and any other ideas you have!", style=ft.TextStyle(size=16))
                ]
            case 17:
                #widget = ComicPreview("Comic Preview Widget", page, story.data.get('content_directory_path'), story)
                #workspace.content = widget
                #workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Comic Preview:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing how your comic pages will look when stitched together.\n\nChoose either a horizontal or vertical display.", style=ft.TextStyle(size=16))
                ]
            case 18:
                if not radar_chart_created:
                    await story.create_widget("Radar Chart", "chart", chart_type="radar")
                    radar_chart_created = True
                tutorial_tip.spans=[
                    ft.TextSpan("Radar Chart:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A dual widget for visualizing any data you want in your story. Create your radar or bar charts for visualizing elements in your story like power systems.", style=ft.TextStyle(size=16))
                ]
            case 19:
                if not bar_chart_created:
                    await story.create_widget("Bar Chart", "chart", chart_type="bar")
                    bar_chart_created = True
                tutorial_tip.spans=[
                    ft.TextSpan("Bar Chart:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A dual widget for visualizing any data you want in your story. Create your radar or bar charts for visualizing elements in your story like power systems.", style=ft.TextStyle(size=16))
                ]

            case 20:
                #widget = PlotChart("Plot Chart Widget", page, story.data.get('content_directory_path'), story)
                #workspace.content = widget
                #workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Plot Chart:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing flow charts of your stories progression. Very useful for managing multiple story routes and arcs at the same time.", style=ft.TextStyle(size=16))
                ]
            case 21:
                #widget = CanvasBoard("Canvas Board Widget", page, story.data.get('content_directory_path'), story)
                tutorial_tip_container.left = 30
                tutorial_tip_container.top = 10
                #workspace.content = widget
                #workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Canvas Board:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for planning out comic-based chapters for your story. Describe and sketch out your ideas for all you panels ahead of time. Connect them to an existing canvas in your story to see how progress is coming along!", style=ft.TextStyle(size=16))
                ]
                tutorial_tip.value = None
            
            # TODO: Finish better detail about each widget
            # Finish rest of rails
            case 21:
                
                
                tutorial_arrow.top = (page.height - 90) / 2 + 50
                tutorial_tip_container.top = (page.height - 90) / 2 - 160
                tutorial_arrow.left = 410
                tutorial_tip_container.left = 410
                tutorial_tip.spans = None
                tutorial_tip.value = "Next is the canvas rail. This controls all your paint and drawing based settings for your canvases (drawings), maps, and canvas boards."
        tutorial_tip_container.update()
        tutorial_arrow.update()

    # Grab our variables so we can hide and show them when we want
    page: ft.Page = story.page
    workspaces_rail = story.workspaces_rail
    active_rail = story.active_rail
    active_rail_resizer = story.active_rail_resizer
    workspace = story.workspace

    # Rails start hidden
    workspaces_rail.visible = False
    active_rail.visible = False
    active_rail_resizer.visible = False
    workspaces_rail.update()
    active_rail.update()
    active_rail_resizer.update()

    # Clear out any existing things in the rail
    page.run_task(clear_story_content)
    
    # State tracking so we don't re-create things that already exist
    folder_created = False
    document_created = False
    canvas_created = False
    note_created = False
    character_created = False
    plotline_created = False
    canvas_board_created = False
    map_created = False
    world_created = False
    item_created = False
    plot_chart_created = False
    comic_preview_created = False
    bar_chart_created = False
    radar_chart_created = False
    character_connection_map_created = False


    previous_tip_button = ft.Button(
        "Previous Step",
        ft.Icons.UNDO, 
        on_click=_previous_tutorial_step, disabled=True,
        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),
        
    )
    next_tip_button = ft.Button(
        "Next Step",
        ft.Icons.REDO,
        on_click=_next_tutorial_step, 
        style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK),        
    )

        
    tutorial_tip = ft.Text(
        "StoryBoard is a story creation and organizational tool for both novel and comic based authors. \n\nThis tutorial will give you a quick introduction to everything you will need when creating your masterpiece!\n\nUse the buttons at the bottom of the app for, previous step, next step, or to exit the tutorial.", 
        expand=True, size=16, #weight=ft.FontWeight.W_400
    )
    tutorial_step = 0
        
    tutorial_tip_container = ft.Container(
        ft.Column([
            tutorial_tip, 
                
            progress_text := ft.Text(f"{str(tutorial_step)}/30", color=ft.Colors.ON_SURFACE_VARIANT, size=12, visible=False)
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, ), 
         
        bgcolor=ft.Colors.SURFACE, padding=ft.Padding.all(10), border_radius=4, width=300, #height=300,
        alignment=ft.Alignment.TOP_CENTER, animate_position=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        shadow=ft.BoxShadow(1, 2, ft.Colors.ON_SURFACE_VARIANT), left=page.width / 2 - 150, top=page.height / 2 - 150,
        
    )
    tutorial_arrow = ft.Icon(
        ft.Icons.ARROW_UPWARD, ft.Colors.PRIMARY, scale=1.5, left=20, top=10, animate_position=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        visible=False
    )
    
                
    return [
        tutorial_tip_container,
        tutorial_arrow,
        ft.Row([
            ft.Container(
                ft.Row([
                    previous_tip_button,
                    ft.Button("Exit Tutorial", color=ft.Colors.ERROR, on_click=_end_tutorial_clicked, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), ),
                    next_tip_button,
                ], alignment=ft.MainAxisAlignment.CENTER),
                border_radius=4,
                bgcolor=ft.Colors.OUTLINE_VARIANT,
                shadow=ft.BoxShadow(1, 3),
                padding=ft.Padding.all(10),
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            )
        ], bottom=0, left=0, right=0, expand=True, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    ]