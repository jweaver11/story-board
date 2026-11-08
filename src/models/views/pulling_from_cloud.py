import flet as ft

# Creates a loading view to be shown while the app is initializing
def PullingFromCloudView() -> ft.View:
    ''' Creates a loading view to be shown while the app is initializing '''
    return ft.View(
        controls=[
            ft.Text("Pulling changes from your google drive...", size=24),
            ft.ProgressRing()
        ],
        route="/pulling_from_cloud",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )