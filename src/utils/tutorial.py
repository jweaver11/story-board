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
            await app.load_previous_story(page) # Loads last story if there is one
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

    # Clears out any content at the start of the tutorial so we can creat
    async def create_content():

        # Clear all the content (if any) from the tutorial story so we can re-create it
        for widget in story.widgets.values():   # Remove existing visible widgets from workspace
            if widget.data.get('visible'):
                story.workspace.remove_widget_from_workspace(widget)

        # Force canvas rail to show
        if not app.settings.data.get('story', {}).get('show_canvas_rail'):
            app.settings.update_data(**{'story': {'show_canvas_rail': True}})
            canvas_rail.width = 78

        # Clar widget list
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

        await story.create_folder("Book 1", update=False)
        await story.create_widget("Manuscript", "manuscript", update=False)
        await story.create_widget("Canvas", "canvas", update=False)
        await story.create_widget("Plotline", "plotline", update=False)
        await story.create_widget("Character", "character", update=False)
        await story.create_widget("Note", "note", update=False)
        await story.create_widget("Canvas Board", "canvas_board", update=False)
        await story.create_widget("Map", "map", update=False)
        await story.create_widget("World", "world", update=False)
        await story.create_widget("Item", "item", update=False)
        await story.create_widget("Plot Chart", "plot_chart", update=False)
        await story.create_widget("Comic Preview", "comic_preview", update=False)
        await story.create_widget("Bar Chart", "chart", chart_type="bar", update=False)
        await story.create_widget("Radar Chart", "chart", chart_type="radar", update=False)
        await story.create_widget("Character Relationship Map", "character_relationship_map", update=False)

        # Since widgets are not added how they think they are, trick them into thinking they are all hidden initially
        for widget in story.widgets.values():
            widget.update_data(**{'visible': False})

        story.active_rail.reload_rail()

    async def show_widget(widget_tag: str, chart_type: str="radar"):
        nonlocal story
        for widget in story.widgets.values():
            if widget.data.get('tag') == widget_tag:
                if widget.data.get('tag') == "chart":
                    if widget.data.get('chart_type') != chart_type:
                        continue

                await widget.show_widget()
                return

        # If we didn't find the widget (user deleted it), create it
        title = widget_tag.replace("_", " ").title()
        await story.create_widget(title, widget_tag, chart_type=chart_type)
       

        

    # Give us the actual content of the current tutorial step
    async def load_tutorial_step():
        nonlocal tutorial_step
            
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
                canvas_rail.visible = False
                canvas_rail.update()
            case 3:
                tutorial_tip.value = "Here is your canvas rail, for all your drawing controls.\n\nIf you don't plan on drawing, you can hide this rail from the file menu, or in the settings."
                tutorial_tip_container.left = 100
                tutorial_tip_container.top = 100
                tutorial_arrow.left = 175
                tutorial_arrow.top = 250
                tutorial_arrow.icon = ft.Icons.ARROW_BACK

                canvas_rail.visible = True
                active_rail.visible = False
                active_rail_resizer.visible = False
                workspace.visible = False
                canvas_rail.update()
                active_rail.update()
                active_rail_resizer.update()
                workspace.update()
            
            case 4:

                tutorial_tip.value = "This is your binder view of your Story's structure of all your folders and widgets.\n\nWe have created one of each widget for this tutorial."
                tutorial_arrow.top = page.height / 2 - 50
                tutorial_tip_container.top = page.height / 2 - 10
                tutorial_arrow.left = 330
                tutorial_tip_container.left = 330

                active_rail.visible = True
                active_rail_resizer.visible = True
                active_rail.update()
                active_rail_resizer.update()

                workspace.visible = True
                workspace.update()
                
            
            case 5:
                
                
                tutorial_tip.value = "Create new Widgets and Folders here, or by right clicking on a folder.\n\nWe have created one of each widget for this tutorial."
                tutorial_arrow.top = 60
                tutorial_tip_container.top = 60
                tutorial_tip_container.left = 280
                tutorial_arrow.left = 240
                tutorial_arrow.visible = True
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
                tutorial_arrow.flip = None

            case 6:
                tutorial_tip.value = "Here is your workspace. This is where you can view and interact with your Story's content.\n\nLet's go through each widget one by one."
                tutorial_arrow.top = page.height - 400
                tutorial_tip_container.top = page.height - 360
                tutorial_tip_container.left = 80
                tutorial_arrow.left = 250
                tutorial_arrow.visible = True
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
                tutorial_arrow.flip = ft.Flip(True)
                
            case 7:
                tutorial_tip.value = None
                
                tutorial_tip.spans=[
                    ft.TextSpan("Manuscript:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("The meat and potatoes for creating all novel-based stories. Similar to Microsoft Word or Google Docs, use the manuscript widget as a fully built text editor.\n\nAdd your own comments or references images to the side of any manuscript!", style=ft.TextStyle(size=16))
                ]
                await show_widget("manuscript")
            case 8:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Canvas:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("The main widget for creating all comic-based stories. This widget allows illustrators to watch their ideas come to life on the Canvas.\n\nCreate your own drawing masterpiece or upload exported files from another drawing app!", style=ft.TextStyle(size=16))
                ]
                await show_widget("canvas")
            case 9:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Note:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget perfect for all your ideas, themes, research, etc., into organized note cards.", style=ft.TextStyle(size=16))
                ]
                await show_widget("note")
            case 10:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Character:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for all the characters in your story. Flesh out your characters physical look, personality, origin, arcs, etc!\n\nSelect the 'New Section' button in the bottom right to seperate ideas.\n\nYou can also create character templates in Settings -> templates.", style=ft.TextStyle(size=16))
                ]
                await show_widget("character")
            case 11:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Plotline:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("Plotlines help visualize your Story's progression of arcs and plotpoints.\n\nThis is also a helpful widget for D&D Campaigns.", style=ft.TextStyle(size=16))
                ]
                await show_widget("plotline")
            case 12:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Map:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the geography of your world.\n\nCreate maps of continents, countries, cities, forests, dungeons, etc.\n\nMaps allow you to create locations with fleshed out information and label important areas.", style=ft.TextStyle(size=16))
                ]
                await show_widget("map")
            case 13:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Character Relationship Map:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the relationships between your characters.\n\nVisualize family trees, social connections, friends, enemies, and anything your heart desires.\n\nThis widget can be particularly useful for romance stories.", style=ft.TextStyle(size=16))
                ]
                await show_widget("character_relationship_map")
            case 14:
                
                tutorial_tip.spans=[
                    ft.TextSpan("World:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for fleshing out to ideas of your world.\n\nCreate your lore, power systems, government, geography and more!\n\nSelect the 'New Section' button in the bottom right to seperate ideas.\n\nYou can also create character templates in Settings -> templates", style=ft.TextStyle(size=16))
                ]
                await show_widget("world")
            case 15:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Item:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for all items, weapons, armor, and MacGuffins in your story!\n\nFlesh out their size, abilities, looks, cost, and any other ideas you have!", style=ft.TextStyle(size=16))
                ]
                await show_widget("item")
            case 16:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Comic Preview:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing how your comic pages will look when stitched together.\n\nChoose either a horizontal or vertical display.", style=ft.TextStyle(size=16))
                ]
                await show_widget("comic_preview")
            case 17:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Radar Chart:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A dual widget for visualizing any data you want in your story. Create your radar or bar charts for visualizing elements in your story like power systems.", style=ft.TextStyle(size=16))
                ]
                await show_widget("chart")
            case 18:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Bar Chart:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A dual widget for visualizing any data you want in your story. Create your radar or bar charts for visualizing elements in your story like power systems.", style=ft.TextStyle(size=16))
                ]
                await show_widget("chart", "bar")

            case 19:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Plot Chart:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing flow charts of your stories progression. Very useful for managing multiple story routes and arcs at the same time.", style=ft.TextStyle(size=16))
                ]
                await show_widget("plot_chart")
            case 20:
                
                tutorial_tip.spans=[
                    ft.TextSpan("Canvas Board:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for planning out comic-based chapters for your story. Describe and sketch out your ideas for all you panels ahead of time. Connect them to an existing canvas in your story to see how progress is coming along!", style=ft.TextStyle(size=16))
                ]
                await show_widget("canvas_board")
            
            
        tutorial_tip_container.update()
        tutorial_arrow.update()

    # Grab our variables so we can hide and show them when we want
    page: ft.Page = story.page
    canvas_rail = story.canvas_rail
    active_rail = story.active_rail
    active_rail_resizer = story.active_rail_resizer
    workspace = story.workspace

    # Rails start hidden
    canvas_rail.visible = False
    active_rail.visible = False
    active_rail_resizer.visible = False
    workspace.visible = False

    # Update elements manually, since story excludes itself from automatic updates
    canvas_rail.update()
    active_rail.update()
    active_rail_resizer.update()
    workspace.update()

    # Clear out any existing things in the rail
    page.run_task(create_content)
    

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
        "StoryBoard is a story creation and organizational tool for both novel and comic based authors. \n\nThis tutorial will give you a quick introduction to everything you will need when creating your masterpiece!\n\nUse the buttons at the bottom of the app for, previous step, next step, or to exit the tutorial.\n\nKeep in mind, any changes you make in the tutorial are not permanent.", 
        expand=True, size=16, #weight=ft.FontWeight.W_400
    )
    tutorial_step = 0
        
    tutorial_tip_container = ft.Container(
        ft.Column([
            tutorial_tip, 
                
            progress_text := ft.Text(f"{str(tutorial_step)}/30", color=ft.Colors.ON_SURFACE_VARIANT, size=12, visible=False)
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, ), 
         
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, padding=ft.Padding.all(10), 
        border_radius=4, width=300, 
        alignment=ft.Alignment.TOP_CENTER, 
        animate_position=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        shadow=ft.BoxShadow(0, 0, ft.Colors.SURFACE_CONTAINER_LOWEST), 
        left=page.width / 2 - 150, top=page.height / 2 - 150,
        
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
                #bgcolor=ft.Colors.OUTLINE_VARIANT,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                #shadow=ft.BoxShadow(1, 3),
                padding=ft.Padding.all(10),
                #border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            )
        ], bottom=0, left=0, right=0, expand=True, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    ]