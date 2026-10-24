import flet as ft

# Creates a loading view to be shown while the app is initializing
@ft.component
def SavingToCloudView() -> ft.View:
    ''' Creates a loading view to be shown while the app is initializing '''
    return ft.View(
        controls=[
            ft.Text("Saving changes to Cloud...", size=24),
            ft.ProgressRing()
        ],
        route="/loading",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )