
import flet as ft

@ft.component
def Blocker(block_page: bool=False):
    ''' A small spinning ring to block interactions with the page while demanding calculations happen '''
    return ft.Container(
        ft.Row([
            ft.ProgressRing(width=100, height=100)
        ], alignment=ft.MainAxisAlignment.CENTER), 
        expand=True, 
        visible=block_page, 
        blur=5, left=0, right=0, top=0, bottom=0,
        key="blocker"
    )