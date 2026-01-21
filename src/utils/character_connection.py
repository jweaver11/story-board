import flet as ft

def new_character_connection_clicked(widget):

    content = ft.Container(
        ft.Column([
            ft.Row([
                # Dropdown 
            ])
        ]),
        height=widget.p.width * .75,
        width=widget.p.width * .75
    )

    dlg = ft.AlertDialog(
        title=ft.Text(f"{widget.title} Connections"),
        content=content,
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: widget.p.close(dlg), style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ft.TextButton("Done", on_click=lambda e: widget.p.close(dlg)),
        ],
    )
    
    
    dlg.open = True
    widget.p.open(dlg)