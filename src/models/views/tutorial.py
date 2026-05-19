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
                workspaces_rail.visible = False
                workspaces_rail_divider.visible = False
                active_rail.visible = False
                active_rail_divider.visible = False
                tutorial_tip_container.left = 50
                tutorial_tip_container.top = 10
                tutorial_arrow.left = 20
                tutorial_arrow.top = 10
                workspaces_rail.update()
                workspaces_rail_divider.update()
                active_rail.update()
                active_rail_divider.update()
            case 2:
                
                tutorial_tip.value = "You can also open the settings from here"
                tutorial_tip_container.left = page.width - tutorial_tip_container.width - 50
                tutorial_arrow.left = page.width - 32
                tutorial_arrow.icon = ft.Icons.ARROW_UPWARD
                workspaces_rail.visible = False
                workspaces_rail_divider.visible = False
                workspaces_rail.update()
                workspaces_rail_divider.update()
            case 3:
                tutorial_tip.value = "This is the rail that lets you select between different rails. \n\nDrag the icons up and down to reorder them"
                workspaces_rail.visible = True
                workspaces_rail_divider.visible = True
                workspaces_rail.update()
                workspaces_rail_divider.update()
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
                active_rail.visible = False
                active_rail_divider.visible = False
                active_rail.update()
                active_rail_divider.update()
            case 5:
                if tutorial_story.data.get('selected_rail') != "content":
                    workspaces_rail.change_workspace(e=1, story=tutorial_story, force_rail="content")
                tutorial_tip.value = "Here is the Active Rail that you have selected. This will change depending on the workspace you select on the left.\n\nDrag the right side of the rail to resize."
                active_rail.visible = True
                active_rail_divider.visible = True
                active_rail.update()
                active_rail_divider.update()
                tutorial_arrow.top = (page.height - 90) / 2 + 90
                tutorial_tip_container.top = (page.height - 90) / 2 - 160
                tutorial_arrow.left = 410
                tutorial_tip_container.left = 410
            case 6:
                if tutorial_story.data.get('selected_rail') != "content":
                    workspaces_rail.change_workspace(e=1, story=tutorial_story, force_rail="content")
                tutorial_tip.value = "Lets start with the content rail. This is where you can create and upload your content, also known as widgets.\n\nWidgets are the building blocks of your story, from characters, plotlines, world building, notes, documents, and more!"
                tutorial_arrow.top = 20
                tutorial_tip_container.top = 20
                tutorial_tip_container.left = 370
                tutorial_arrow.left = 320
            case 7:
                if tutorial_story.data.get('selected_rail') != "content":
                    workspaces_rail.change_workspace(e=1, story=tutorial_story, force_rail="content")
                tutorial_tip.value = "Create folders to organize your books, seasons, chapters, or however you want!\n\nHover over a folder or right click it to see its options.\n\nDrag widgets to and from folders exactly how you would expect."
                tutorial_arrow.top = 80
                tutorial_tip_container.top = 80
                tutorial_tip_container.left = 400
                tutorial_arrow.left = 360
                widget_descriptions.visible = False
                tutorial_story.workspace.visible = False
                tutorial_arrow.icon = ft.Icons.ARROW_BACK
                
            case 8:
                if tutorial_story.data.get('selected_rail') != "content":
                    workspaces_rail.change_workspace(e=1, story=tutorial_story, force_rail="content")
                widget_descriptions.visible = True
                tutorial_story.workspace.visible = True
                workspace.content = None
                workspace.update()
                tutorial_arrow.top = (page.height - 90) / 2 + 80
                tutorial_tip_container.top = (page.height - 90) / 2 - 160
                tutorial_arrow.left = 410
                tutorial_tip_container.left = 410
                #tutorial_arrow.icon = ft.Icons.ARROW_OUTWARD
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
                    ft.TextSpan("The main widget for creating all novel-based stories. Similar to Microsoft Word or Google Docs, use the document widget as a fully built text editor. Add your own comments, notes, and references to the side of any document!", style=ft.TextStyle(size=16))
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
                    ft.TextSpan("A widget for visualizing the progression of your story. Create multiple plotlines for arcs, sub arcs, plot points, or regression & multi-timeline stories. Connect events on your plotline to a map and watch your world change over time!", style=ft.TextStyle(size=16))
                ]
            case 14:
                widget = Map("Map Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Map:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the geography of your world. Create your own maps from scratch using the canvas or upload them from another program. Connect locations on your map to events on your plotline and watch your world change over time!", style=ft.TextStyle(size=16))
                ]
            case 15:
                widget = CharacterConnectionMap("Character Connection Map Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Character Connection Map:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the relationships between your characters. Create your own character connection map from scratch using the canvas or upload them from another program. Connect characters on your map to events on your plotline and watch your world change over time!", style=ft.TextStyle(size=16))
                ]
            case 16:
                widget = World("World Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("World:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the lore of your world. Create your own world building wiki from scratch using the canvas or upload it from another program. Connect lore entries on your world wiki to events on your plotline and watch your world change over time!", style=ft.TextStyle(size=16))
                ]
            case 17:
                widget = Item("Item Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Item:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing the important items in your story. Create your own item encyclopedia from scratch using the canvas or upload it from another program. Connect items on your encyclopedia to events on your plotline and watch your world change over time!", style=ft.TextStyle(size=16))
                ]
            case 18:
                widget = ComicPreview("Comic Preview Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Comic Preview:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for visualizing how your comic pages will look when printed. Create your own comic page previews from scratch using the canvas or upload them from another program. Connect pages on your preview to events on your plotline and watch your world change over time!", style=ft.TextStyle(size=16))
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
                widget = CanvasBoard("Canvas Board Widget", page, tutorial_story.data.get('content_directory_path'), tutorial_story)
                workspace.content = widget
                workspace.update()
                tutorial_tip.spans=[
                    ft.TextSpan("Canvas Board:\n", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                    ft.TextSpan("A widget for planning out comic-based chapters for your story. Describe and sketch out your ideas for all you panels ahead of time. Connect them to an existing canvas in your story to see how progress is coming along!", style=ft.TextStyle(size=16))
                ]
            
            # TODO: Finish better detail about each widget
            # Finish rest of rails
            case 21:
                workspace.content = None
                workspace.update()
                if tutorial_story.data.get('selected_rail') != "canvas":
                    workspaces_rail.change_workspace(e=1, story=tutorial_story, force_rail="canvas")
                tutorial_arrow.top = (page.height - 90) / 2 + 50
                tutorial_tip_container.top = (page.height - 90) / 2 - 160
                tutorial_arrow.left = 410
                tutorial_tip_container.left = 410
                tutorial_tip.value = "Next is the canvas rail. This controls all your paint and drawing based settings for your canvases (drawings), maps, and canvas boards."
        tutorial_tip_container.update()
        tutorial_arrow.update()
        

    menubar = ft.Container(
        border=ft.Border.only(bottom=ft.BorderSide(width=1, color=ft.Colors.OUTLINE_VARIANT)),
        bgcolor=ft.Colors.SURFACE,
        content=ft.Row(
            spacing=0,
            controls=[
                ft.MenuBar(
                    expand=True,
                    style=ft.MenuStyle(     # Styling our menubar
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.TRANSPARENT,
                        shadow_color=ft.Colors.TRANSPARENT,
                        mouse_cursor={
                            ft.ControlState.HOVERED: ft.MouseCursor.WAIT,
                            ft.ControlState.DEFAULT: ft.MouseCursor.ZOOM_OUT,
                        },
                    ),
                    controls=[  # The controls shown in our menu bar from left to right
                        ft.SubmenuButton(   # Button that opens a subment
                            content=ft.Container(
                                content=ft.Text("File", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE,),     # Content of subment button
                                alignment=ft.Alignment.CENTER
                            ), 
                            style=ft.ButtonStyle(padding=ft.Padding.all(0), shape=ft.RoundedRectangleBorder(radius=10)),
                            menu_style=ft.MenuStyle(padding=ft.Padding.all(0)),
                            tooltip="File options, such as creating a new story, opening a story, saving, and exporting. (Won't work during tutorial)",
                        ),
                    ], 
                ),   
                ft.Container(expand=True),  # empty space in middle of menubar
                # Fix broken widgets button

                ft.Text(
                    "Alpha", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, 
                    tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                ),  # Feedback button
                ft.Icon(
                    ft.Icons.INFO_OUTLINED, color=ft.Colors.PRIMARY, scale=.5, 
                    tooltip="Storyboard is currently in alpha. Bugs are expected. More features coming soon! \nCheck out Settings -> Resources for a list of planned features and known issues. \nJoin the Discord to suggest your features and report bugs."
                ),
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, "primary", disabled=True, tooltip="Open the Settings (Won't work during tutorial)"),   # Settings button
            ]
        )
    )
    
    # Give us 1 of each widget to show them all off
    async def create_tutorial_content():
        tutorial_story.create_folder(tutorial_story.data.get('content_directory_path'), "Folder")
        await tutorial_story.create_widget("Document", "document", no_delay=True)
        await tutorial_story.create_widget("Note", "note", no_delay=True)
        await tutorial_story.create_widget("Canvas", "canvas", no_delay=True)
        await tutorial_story.create_widget("Character", "character", no_delay=True)
        await tutorial_story.create_widget("Plotline", "plotline", no_delay=True)
        await tutorial_story.create_widget("Map", "map", no_delay=True)
        await tutorial_story.create_widget("Character Connection Map", "character_connection_map", no_delay=True)
        await tutorial_story.create_widget("World", "world", no_delay=True)
        await tutorial_story.create_widget("Canvas Board", "canvas_board", no_delay=True)
        await tutorial_story.create_widget("Item", "item", no_delay=True)
        await tutorial_story.create_widget("Chart", "chart", no_delay=True)
        await tutorial_story.create_widget("Comic Preview", "comic_preview", no_delay=True)    
        await asyncio.sleep(0.3)

    tutorial_story = Story("Tutorial Story", page)
    page.run_task(create_tutorial_content)   # Create some content for the tutorial story so it doesn't look so sad and empty
    tutorial_story.startup()    # Prepare the story

    for widget in tutorial_story.widgets:
        widget.visible = False
        widget.data['visible'] = False
        page.run_task(widget.save_dict)   # Save that the widgets are not visible in the story data
        widget.reload_widget()

    tutorial_story.workspace.reload_workspace()
    tutorial_story.workspace.expand = 2
    tutorial_story.workspace.visible = False
    workspaces_rail = WorkspacesRail(page, tutorial_story)
    workspaces_rail.visible = False

    active_rail = tutorial_story.active_rail
    active_rail.visible = False
    active_rail.expand = False
    active_rail.width = 225
    active_rail.animate_size = ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN)
    active_rail.animate = ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN)

    # Resize the rail when dragging
    async def move_active_rail_divider(e: ft.DragUpdateEvent):
        active_rail.width += int(e.local_delta.x)   
        if active_rail.width < 250:
            active_rail.width = 250
        elif active_rail.width > 500:
            active_rail.width = 500
        active_rail.update()

    active_rail_divider = ft.GestureDetector(
        content=ft.Container(
            width=10,   
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            content=ft.VerticalDivider(2, 2),     
            padding=ft.Padding.only(right=8),  
        ),
        mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,  
        on_pan_update=move_active_rail_divider, # Resize the active rail as app is dragging
        drag_interval=50,
        visible=False,
        animate_size=ft.Animation(500, ft.AnimationCurve.FAST_LINEAR_TO_SLOW_EASE_IN),
    )
        

    tutorial_tip = ft.Text(
        "StoryBoard is a story creation and organizational tool for both novel and comic based authors. \n\nThis tutorial will give you a quick introduction to everything you will need when creating your masterpiece!\n\nUse the buttons below for next step, previous step, or to exit the tutorial.", 
        expand=True, size=16, #weight=ft.FontWeight.W_400
    )
    tutorial_step = 0
        
    tutorial_tip_format = ft.Column([
        tutorial_tip,
        ft.Row([
            
            previous_tip_button := ft.IconButton(ft.Icons.UNDO, ft.Colors.OUTLINE_VARIANT, on_click=_previous_tutorial_step, mouse_cursor=ft.MouseCursor.CLICK, disabled=True),
            ft.TextButton("Exit Tutorial", on_click=_end_tutorial_clicked, style=ft.ButtonStyle(mouse_cursor=ft.MouseCursor.CLICK), ),
            next_tip_button := ft.IconButton(ft.Icons.REDO, ft.Colors.PRIMARY, on_click=_next_tutorial_step, mouse_cursor=ft.MouseCursor.CLICK),
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
    widget_descriptions = ft.Container(
        ft.Column([
        ft.Text(
            spans=[
                ft.TextSpan("Document: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("The main widget for creating all novel-based stories. Similar to Microsoft Word or Google Docs, use the document widget as a fully built text editor. Add your own comments, notes, and references to the side of any document!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Canvas: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("The main widget for creating all comic-based stories. This widget allows illustrators to watch their ideas come to life on the Canvas. Create your own drawing masterpiece or upload exported files from another drawing app!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Note: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget for all your ideas, themes, research, etc. Don't let the magic fade, save it here!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Character: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget for all the characters in your story. Flesh out your characters physical look, personality, origin, arcs, etc!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Plotline: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget for visualizing the progression of your story. Create multiple plotlines for arcs, sub arcs, plot points, or regression & multi-timeline stories. Connect events on your plotline to a map and watch your world change over time!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Canvas Board: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget for planning out comic-based chapters for your story. Describe and sketch out your ideas for all you panels ahead of time. Connect them to an existing canvas in your story to see how progress is coming along!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("World: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget to describe your world(s) for your story. Plan out the lore, history, governments, factions, power systems, etc. You can create templates for your worlds, and connect them to existing maps!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Map: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget to visualize locations in your story. Create a map for worlds, countries, cities, dungeons, etc. Connect locations on your map to other maps for a connected feel to your story!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Item: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget for all items, weapons, armor, and MacGuffins in your story!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Comic Preview: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget for comic-based stories for visualizing all your canvases (and external drawings you want to see), in a nice, scrollable vertical or horizontal format. See how your chapter comes together visually before you present it to the world!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Chart: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget for visualizing power systems and other ideas in a chart format. Supports manipulation of bar and radar charts, with implicit animations!", style=ft.TextStyle(size=16))
            ],
        ),
        ft.Text(
            spans=[
                ft.TextSpan("Charcter Connection Map: ", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
                ft.TextSpan("A widget to visualize how your characters connect to each other within a story. See family trees, friends, enemies, guilds, etc.", style=ft.TextStyle(size=16))
            ],
        ),
        
    ], spacing=24, scroll=ft.ScrollMode.AUTO, alignment=ft.MainAxisAlignment.START, expand=True,),
    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, visible=False, expand=True, margin=ft.Margin.symmetric(vertical=10)
    )

    workspace = ft.Container(expand=True, bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST, padding=ft.Padding.only(right=10, bottom=10, top=10))
                
    

    return ft.View(
        route="/tutorial",
        controls=[
            menubar,
            ft.Stack([
                ft.Row([
                    workspaces_rail,
                    workspaces_rail_divider := ft.VerticalDivider(2, 2, visible=False),

                    active_rail,
                    active_rail_divider,
                    #tutorial_story.workspace,
                    workspace,
                    widget_descriptions
                ], spacing=0, expand=True),
                tutorial_tip_container, tutorial_arrow
            ], expand=True),
        ],
        padding=ft.Padding.all(0), spacing=0, #scroll=ft.ScrollMode.AUTO

    )