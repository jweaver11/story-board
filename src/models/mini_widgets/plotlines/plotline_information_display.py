import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from models.widgets.plotline import Plotline


# Display that makes Plotlines share much uniformaty in their information display like arcs do
class PlotlineInformationDisplay(MiniWidget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(self, title: str, owner: Widget, father: Plotline, page: ft.Page, key: str, data: dict=None):

        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,                    
            father=father,                  # In this case, father is always the Plotline or arc we belong to
            page=page,          
            key=key,  # Not used, but its required so just whatever works
            data=None,      # No data is used here, so NEVER reference it. Use self.owner.data instead
        ) 
        
        # Since we only reference out owners data and not our own, we don't need to verify it here

        # Set our visibility based on our owners data
        self.visible = self.owner.data.get('information_display_visibility', True)
        #self.visible = False

        self.reload_mini_widget()

    # Called when saving changes to our Plotline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our Plotlines data instead '''
        try:
            self.owner.save_dict()
        except Exception as e:
            print(f"Error saving Plotline information display data to {self.owner.title}: {e}")

    def toggle_visibility(self, e=None, value: bool=None):
        ''' Toggles our visibility and updates our owners data accordingly '''

        # Update our visibility
        self.owner.data['information_display_visibility'] = not self.visible if value is None else value
        self.visible = self.owner.data.get('information_display_visibility', True)

        # IF we hit that we are visible, and not special exclusive, hide all other exclusive mini widgets on the same side
        if self.visible:
            for mini_widget in self.owner.mini_widgets:
                if mini_widget.visible and mini_widget != self and mini_widget.data.get('side_location', 'right') == self.data.get('side_location', 'right'):
                    mini_widget.toggle_visibility(value=False)

        self.save_dict()
        self.reload_mini_widget()
        self.owner.reload_widget()
        

    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        self.title_control = ft.Row([
            ft.Text(self.data['title'], weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                tooltip=f"Close {self.title}",
                on_click=lambda e: self.toggle_visibility(value=False),
            ),
        ])
        

        # Rebuild our information display
        self.content_control = ft.TextField(
            hint_text="plot point",
            #on_submit=self.change_x_position,
            expand=True,
        )



        # TODO: Add 'Events', which shows in order of plot points, arcs, and markers on the plotline

        # SUmmary
        # Events
        # Plot points
        # arcs
        # Markers
        # LEft and right edge label, time label, divisions

        self.content = ft.Column(
            [
                self.title_control,
                ft.Divider(height=2, thickness=2),
                ft.Container(expand=True, height=10),
                self.content_control,
                #ft.Container(expand=True),

                ft.TextButton(f"Close {self.title}", on_click=self.toggle_visibility),
            ],
            expand=True, tight=True, spacing=0, scroll="auto"
        )

        self.p.update()