import flet as ft
from models.mini_widget import MiniWidget
from models.widget import Widget
from models.widgets.timeline import Timeline


# Display that makes timelines share much uniformaty in their information display like arcs do
class TimelineInformationDisplay(MiniWidget):

    # Constructor. Requires title, owner widget, page reference, and optional data dictionary
    def __init__(self, title: str, owner: Widget, father: Timeline, page: ft.Page, key: str, data: dict=None):

        # Parent constructor
        super().__init__(
            title=title,        
            owner=owner,                    
            father=father,                  # In this case, father is always the timeline or arc we belong to
            page=page,          
            key=key,  # Not used, but its required so just whatever works
            data=None,      # No data is used here, so NEVER reference it. Use self.owner.data instead
        ) 
        
        # Since we only reference out owners data and not our own, we don't need to verify it here

        # Set our visibility based on our owners data
        self.visible = self.owner.data.get('information_display_visibility', True)
        self.visible = False

        self.reload_mini_widget()

    # Called when saving changes to our timeline object
    def save_dict(self):
        ''' Overwrites standard mini widget save and save our timelines data instead '''
        try:
            self.owner.save_dict()
        except Exception as e:
            print(f"Error saving timeline information display data to {self.owner.title}: {e}")
        

    # Called when reloading our mini widget UI
    def reload_mini_widget(self):

        self.content = ft.Column(
            [
                self.title_control,
                self.content_control,

                ft.TextButton(f"Close {self.title}", on_click=self.toggle_visibility),
            ],
            expand=True,
        )

        self.p.update()