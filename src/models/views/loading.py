import flet as ft

@ft.component
def LoadingView() -> ft.View:
    ''' Creates a loading view to be shown while the app is initializing '''
    return ft.View(
        controls=[
            ft.Text("Loading...", size=24),
            ft.ProgressRing()
        ],
        route="/loading",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )