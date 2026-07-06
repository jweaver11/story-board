''' View for our tutorial page '''
import flet as ft
import asyncio
from styles.snack_bar import SnackBar
from ui.workspaces_rail import WorkspacesRail
from models.views.story import Story
from models.widgets.document import Document
from models.widgets.canvas import Canvas 
from models.widgets.note import Note
from models.widgets.character import Character
from models.widgets.plotline import Plotline
from models.widgets.map import Map
from models.widgets.world import World
from models.widgets.character_connection_map import CharacterConnectionMap
from models.widgets.item import Item
from models.widgets.comic_preview import ComicPreview
from models.widgets.chart import Chart
from models.widgets.canvas_board import CanvasBoard
from models.widgets.plot_chart import PlotChart
import shutil
import os


def create_tutorial_view(page: ft.Page) -> ft.View:
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
       

    # Give us the actual content of the current tutorial step
    async def load_tutorial_step():
        nonlocal tutorial_step
            
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
                
                tutorial_tip_container.left = 50
                tutorial_tip_container.top = 10
                tutorial_arrow.left = 20
                tutorial_arrow.top = 10
                
            case 2:
                
                tutorial_tip.value = "You can also open the settings from here"
                tutorial_tip_container.left = page.width - tutorial_tip_container.width - 50
                tutorial_arrow.left = page.width - 32
                tutorial_arrow.icon = ft.Icons.ARROW_UPWARD
               
            case 3:
                tutorial_tip.value = "This is the rail that lets you select between different rails. \n\nDrag the icons up and down to reorder them"
                
                tutorial_tip_container.left = 140
                tutorial_tip_container.top = 40
                tutorial_arrow.left = 140
                tutorial_arrow.top = 10
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
            case 4:
                tutorial_tip.value = "Collapse or expand the rail here"
                tutorial_arrow.top = page.height - 90
                tutorial_tip_container.top = page.height - 200
                tutorial_tip_container.left = 140
                tutorial_arrow.left = 140
                
            case 5:
                
                tutorial_arrow.top = (page.height - 90) / 2 + 90
                tutorial_tip_container.top = (page.height - 90) / 2 - 160
                tutorial_arrow.left = 410
                tutorial_tip_container.left = 410
            case 6:
                
                tutorial_tip.value = "Lets start with the content rail. This is where you can create and upload your content, also known as widgets.\n\nWidgets are the building blocks of your story, from characters, plotlines, world building, notes, documents, and more!"
                tutorial_arrow.top = 20
                tutorial_tip_container.top = 20
                tutorial_tip_container.left = 370
                tutorial_arrow.left = 320
            case 7:
                
                tutorial_tip.value = "Create folders to organize your books, seasons, chapters, or however you want!\n\nHover over a folder or right click it to see its options.\n\nDrag widgets to and from folders exactly how you would expect."
                tutorial_arrow.top = 80
                tutorial_tip_container.top = 80
                tutorial_tip_container.left = 400
                tutorial_arrow.left = 360
                tutorial_story.workspace.visible = False
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
                
            case 8:
                
                tutorial_story.workspace.visible = True
                workspace.content = None
                workspace.update()
                tutorial_arrow.top = (page.height - 90) / 2 + 80
                tutorial_tip_container.top = (page.height - 90) / 2 - 160
                tutorial_arrow.left = 410
                tutorial_tip_container.left = 410
                tutorial_arrow.visible = True
                tutorial_tip.spans = None
                tutorial_tip.value = "We have created one widget of each type to show what they look like on the rail.\n\nNext we'll go through each widget. Feel free to interact with them, but know your work won't be saved."
            case 9:
                tutorial_arrow.visible = False
                tutorial_tip_container.left = 30
                tutorial_tip_container.top = 10
                widget = Document("Document Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Document:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("The main widget for creating all novel-based stories. Similar to Microsoft Word or Google Docs, use the document widget as a fully built text editor.\n\nAdd your own comments, notes, and references to the side of any document!", style=ft.TextStyle(size=16))
                ]
                tutorial_tip.value = None
            case 10:
                widget = Canvas("Canvas Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Canvas:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("The main widget for creating all comic-based stories. This widget allows illustrators to watch their ideas come to life on the Canvas. Create your own drawing masterpiece or upload exported files from another drawing app!", style=ft.TextStyle(size=16))
                ]
            case 11:
                widget = Note("Note Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Note:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for all your ideas, themes, research, etc. Don't let the magic fade, save it here!", style=ft.TextStyle(size=16))
                ]
            case 12:
                widget = Character("Character Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Character:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for all the characters in your story. Flesh out your characters physical look, personality, origin, arcs, etc!", style=ft.TextStyle(size=16))
                ]
            case 13:
                widget = Plotline("Plotline Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Plotline:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the progression of your story. Create multiple plotlines for arcs, sub arcs, plot points, or regression & multi-timeline stories.", style=ft.TextStyle(size=16))
                ]
            case 14:
                widget = Map("Map Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Map:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the geography of your world.\n\nCreate maps of continents, countries, cities, forests, dungeons, etc.\n\nMaps allow you to create locations with fleshed out information and label important areas.", style=ft.TextStyle(size=16))
                ]
            case 15:
                widget = CharacterConnectionMap("Character Connection Map Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Character Connection Map:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the relationships between your characters.\n\nVisualize family trees, social connections, friends, enemies, and anything your heart desires.\n\nThis widget can be particularly useful for romance stories.", style=ft.TextStyle(size=16))
                ]
            case 16:
                widget = World("World Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("World:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for fleshing out to ideas of your world.\n\nCreate your lore, power systems, government, geography and more! ", style=ft.TextStyle(size=16))
                ]
            case 17:
                widget = Item("Item Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Item:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for all items, weapons, armor, and MacGuffins in your story!\n\nFlesh out their size, abilities, looks, cost, and any other ideas you have!", style=ft.TextStyle(size=16))
                ]
            case 18:
                widget = ComicPreview("Comic Preview Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Comic Preview:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing how your comic pages will look when stitched together.\n\nChoose either a horizontal or vertical display.", style=ft.TextStyle(size=16))
                ]
            case 19:
                widget = Chart("Chart Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story, type="radar")
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Chart:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing any data you want in your story. Create your own charts from scratch using the canvas or upload them from another program. Connect data points on your chart to events on your plotline and watch your world change over time!", style=ft.TextStyle(size=16))
                ]
            case 20:
                widget = PlotChart("Plot Chart Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Plot Chart:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing flow charts of your stories progression. Very useful for managing multiple story routes and arcs at the same time.", style=ft.TextStyle(size=16))
                ]
            case 21:
                widget = CanvasBoard("Canvas Board Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                tutorial_tip_container.left = 30
                tutorial_tip_container.top = 10
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Canvas Board:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for planning out comic-based chapters for your story. Describe and sketch out your ideas for all you panels ahead of time. Connect them to an existing canvas in your story to see how progress is coming along!", style=ft.TextStyle(size=16))
                ]
                tutorial_tip.value = None
            
            # TODO: Finish better detail about each widget
            # Finish rest of rails
            case 22:
                workspace.content = None
                workspace.update()
                
                tutorial_arrow.top = (page.height - 90) / 2 + 50
                tutorial_tip_container.top = (page.height - 90) / 2 - 160
                tutorial_arrow.left = 410
                tutorial_tip_container.left = 410
                tutorial_tip.spans = None
                tutorial_tip.value = "Next is the canvas rail. This controls all your paint and drawing based settings for your canvases (drawings), maps, and canvas boards."
        tutorial_tip_container.update()
        tutorial_arrow.update()

    previous_tip_button = ft.IconButton(ft.Icons.UNDO, ft.Colors.OUTLINE_VARIANT, on_click=_previous_tutorial_step, mouse_cursor=ft.MouseCursor.CLICK, disabled=True)
    next_tip_button = ft.IconButton(ft.Icons.REDO, ft.Colors.PRIMARY, on_click=_next_tutorial_step, mouse_cursor=ft.MouseCursor.CLICK)

    tutorial_story = Story("Tutorial Story", page)

        
    tutorial_tip = ft.Text(
        "StoryBoard is a story creation and organizational tool for both novel and comic based authors. \n\nThis tutorial will give you a quick introduction to everything you will need when creating your masterpiece!\n\nUse the buttons below for next step, previous step, or to exit the tutorial.", 
        expand=True, size=16, #weight=ft.FontWeight.W_400
    )
    tutorial_step = 0
        
    tutorial_tip_format = ft.Column([
        tutorial_tip,
        ft.Row([
            
            previous_tip_button,
            ft.TextButton("Exit Tutorial", on_click=_end_tutorial_clicked, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), ),
            next_tip_button,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        progress_text := ft.Text(f"{str(tutorial_step)}/30", color=ft.Colors.ON_SURFACE_VARIANT, size=12, visible=False)
    ])
    tutorial_tip_container = ft.Container(
        tutorial_tip_format, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, padding=ft.Padding.all(10), border_radius=10, width=300, #height=300,
        alignment=ft.Alignment.TOP_CENTER, animate_position=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        shadow=ft.BoxShadow(1, 0), left=page.width / 2 - 150, top=page.height / 2 - 150,
    )
    tutorial_arrow = ft.Icon(
        ft.Icons.ARROW_UPWARD, ft.Colors.PRIMARY, scale=1.5, left=20, top=10, animate_position=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
        visible=False
    )
    
    workspace = ft.Container(expand=True, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, padding=ft.Padding.only(right=10, bottom=10, top=10))
                
    return tutorial_story