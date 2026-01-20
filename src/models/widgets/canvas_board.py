'''
Class for showing all our characters laidd out in a family tree view.
'''

import flet as ft
from models.widget import Widget
from models.views.story import Story
from utils.verify_data import verify_data
from models.app import app


class CanvasBoard(Widget):
    # Constructor
    def __init__(self, name: str, page: ft.Page, directory_path: str, story: Story, data: dict=None):

        # Parent class constructor
        super().__init__(
            title = name,  
            page = page,   
            directory_path = directory_path, 
            story = story,   
            data = data,    
        )

        # Verifies this object has the required data fields, and creates them if not
        verify_data(
            object=self,   # Pass in our own data so the function can see the actual data we loaded
            required_data={
                'tag': "canvas_board",
                'color': app.settings.data.get('default_canvas_board_color'),

                'description': str, # Description of this canvas board. Some could be for chapters (multiple canvas) or just one board

                # Labels on the top part of our grid. Users can add onto these as needed
                'matrix_labels': ["Preview", "Sketch", "Concept"],   # Preview -> Ties to a specific Canvas and shows a preview of that Canvas in real time
                # Sketch provides a simple canvas for rough sketches/thumbnails. Conecpt is text descriptions of the idea

                'matrix': [
                    ["1", "2", "3"],      # 1 will be a key to a specific canvas, 2 is a sketch canvas shapes data, 3 is a str
                    ["4", "5", "6"]
                ]
            },
        )
        
        self.icon = ft.Icon(ft.Icons.PERSON, size=100, expand=False)    # Icon of character

        # Build our widget on start, but just reloads it later
        self.reload_widget()

    # Called when making changes to the data in a matrix cell
    def _update_matrix_cell(self, row: int, column: int, value):
        ''' Updates a specific cell in our matrix data '''
        

        if isinstance(value, str):
            self.data['matrix'][row][column] = value
            self.save_dict()
    

    

    # Called after any changes happen to the data that need to be reflected in the UI
    def reload_widget(self):
        ''' Reloads/Rebuilds our widget based on current data '''

        # TODO: Show filters at top for our characters to show
        # PURPOSE: To show a family tree view of our characters and their connections to one another

        # Rebuild out tab to reflect any changes
        self.reload_tab()

        description_container = ft.Container(            # For Summary
            padding=ft.padding.all(8), border_radius=ft.border_radius.all(5), expand=True,
            border=ft.border.all(2, ft.Colors.OUTLINE), 
            content=ft.TextField(
                expand=True, value=self.data.get('description', ""), dense=True, multiline=True,
                capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                on_blur=lambda e: self.change_data(**{'description': e.control.value}),
                border=ft.InputBorder.NONE,                  
            ),
        )

        

        def _get_label_controls() -> list[ft.Control]:
            ''' Formats our labels insto text controls above our grid '''
            controls = []
            controls.append(ft.Container(width=6))
            for label in self.data['matrix_labels']:
                controls.append(
                    ft.Container(
                        ft.Text(label, style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=self.data.get('color', "primary")), selectable=True),
                        padding=5, alignment=ft.alignment.center, expand=True
                    )
                )

            controls.append(ft.Container(width=6))
            return controls
        

        # Lays out our controls in a nice grid format
        def _get_grid_controls() -> list[ft.Control]:

            controls = []
            for idx, row in enumerate(self.data['matrix']):

                # Build our border, and remove sides we don't need on edges
                border = ft.border.only(
                    left=ft.BorderSide(1, ft.Colors.OUTLINE),
                    right=ft.BorderSide(1, ft.Colors.OUTLINE),
                    top=ft.BorderSide(1, ft.Colors.OUTLINE),
                    bottom=ft.BorderSide(1, ft.Colors.OUTLINE),
                )
                no_top_border = False
                no_bottom_border = False    

                # Check our index for on the edge or not
                if idx == 0:
                    no_top_border = True
                elif idx == len(self.data['matrix']) - 1:
                    no_bottom_border = True
  
                row_control = ft.Row(spacing=0, expand=True, controls=[])

                for sub_idx, cell in enumerate(row):

                    # Check our index for on the edge or not
                    if sub_idx == 0:
                        border = ft.border.only(
                            right=ft.BorderSide(1, ft.Colors.OUTLINE),
                            top=ft.BorderSide(0 if no_top_border else 1, ft.Colors.OUTLINE),
                            bottom=ft.BorderSide(0 if no_bottom_border else 1, ft.Colors.OUTLINE),
                        )

                    elif sub_idx == len(row) - 1:
                        border = ft.border.only(
                            left=ft.BorderSide(1, ft.Colors.OUTLINE),
                            top=ft.BorderSide(0 if no_top_border else 1, ft.Colors.OUTLINE),
                            bottom=ft.BorderSide(0 if no_bottom_border else 1, ft.Colors.OUTLINE),
                        )

                    else:
                        # All borders
                        border = ft.border.all(1, ft.Colors.OUTLINE)

                    # Check our index against our label
                    label = self.data['matrix_labels'][sub_idx]

                    # Depending on our label, the content of our container will be differnt.
                    # Either image with preview of canvas, sketch canvas, or text area for concept
                    match label:
                        case "Preview":
                            pass
                        case "Sketch":
                            pass
                        case "Concept":
                            pass
                        case _:
                            pass

                    if isinstance(cell, str):

                        row_control.controls.append(
                            ft.Container(
                                ft.TextField(
                                    str(cell),
                                    dense=True, multiline=True, border=ft.InputBorder.NONE,
                                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                                    on_blur=lambda e, r=idx, c=sub_idx: self._update_matrix_cell(r, c, e.control.value)
                                ), 
                                expand=True, border=border,
                                padding=5, alignment=ft.alignment.top_center,
                            )
                        )

                    else:
                        row_control.controls.append(
                            ft.Container(
                                ft.TextField(
                                    str(cell),
                                    dense=True, multiline=True, border=ft.InputBorder.NONE,
                                    capitalization=ft.TextCapitalization.SENTENCES, adaptive=True,
                                    #on_blur
                                ), 
                                expand=True,
                                border=ft.border.all(1, ft.Colors.ON_SURFACE),
                                padding=5, alignment=ft.alignment.top_center,
                            )
                        )

                controls.append(row_control)

            return controls

        

        # Body of the tab, which is the content of flet container
        body = ft.Container(
            expand=True,               
            padding=6,                 
            content=ft.Column(
                spacing=0, expand=True, #scroll="auto", 
                controls=[                 
                
                    ft.Row([
                        ft.Container(width=6), 
                        ft.Text("Description", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16), color=self.data.get('color', None), selectable=True),
                    ], spacing=0),
                    ft.Container(height=10),

                    ft.Row([description_container]),
                    ft.Container(height=10),

            
                    ft.Row(_get_label_controls(), spacing=0),

            ])
        )    

        body.content.controls.extend(_get_grid_controls())

        

        
        # Set our content to the body_container (from Widget class) as the body we just built
        self.body_container.content = body

        # Call render widget (from Widget class) to update the UI
        self._render_widget()
            


