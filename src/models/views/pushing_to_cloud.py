import flet as ft

# Creates a loading view to be shown while the app is initializing
def PushingToCloudView() -> ft.View:
    ''' Creates a loading view to be shown while the app is initializing '''
    return ft.View(
        controls=[
            ft.Text("Pushing changes to your google drive...", size=24),
            ft.ProgressRing()
        ],
        route="/pushing_to_cloud",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )