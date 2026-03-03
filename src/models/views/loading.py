import flet as ft


def create_loading_view(page: ft.Page) -> ft.Column:
    ''' Creates a loading view to be shown while the app is initializing '''
    return ft.Column(
        controls=[
            ft.Row([ft.Text("Loading...", size=24,  text_align=ft.TextAlign.CENTER)], alignment=ft.CrossAxisAlignment.CENTER),
            ft.ProgressRing()
        ],
        #route="/loading",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER, expand=True,
    )