''' Creates our contexts for the app to use so they can be imported from components who have access to them '''

import flet as ft

# App and settings
AppContext = ft.create_context(None)
AppSettingsContext = ft.create_context(None)

# Drawing controls
PaintContext = ft.create_context(None)
DrawingContext = ft.create_context(None)
TextContext = ft.create_context(None)
