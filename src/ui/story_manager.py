"""
Story Manager Dialog - Handles creation, loading, and management of stories
"""

import flet as ft
from models.user import user


def create_new_story_dialog(page: ft.Page):
    """Create dialog for creating a new story"""
    
    story_name_field = ft.TextField(
        label="Story Name",
        hint_text="Enter the name for your new story",
        width=300,
        autofocus=True
    )
    
    def create_story_clicked(e):
        story_name = story_name_field.value.strip()
        
        if not story_name:
            page.open(ft.SnackBar(ft.Text("Please enter a story name")))
            return
        
        # Check if story already exists
        if story_name in user.stories:
            page.open(ft.SnackBar(ft.Text(f"Story '{story_name}' already exists")))
            return
        
        try:
            # Create new story
            new_story = user.create_new_story(story_name)
            
            # Switch to the new story
            user.switch_active_story(story_name)
            
            # Update page title
            page.title = f"StoryBoard -- {user.active_story.title} -- Saved"
            
            # Close dialog
            dialog.open = False
            page.update()
            
            # Show success message
            page.open(ft.SnackBar(ft.Text(f"Created and switched to story: {story_name}")))
            
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error creating story: {str(ex)}")))
    
    def cancel_clicked(e):
        dialog.open = False
        page.update()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Create New Story"),
        content=ft.Container(
            content=ft.Column([
                ft.Text("Enter details for your new story:"),
                story_name_field,
            ], tight=True),
            width=400,
            height=150
        ),
        actions=[
            ft.TextButton("Cancel", on_click=cancel_clicked),
            ft.ElevatedButton("Create Story", on_click=create_story_clicked),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    return dialog


def create_load_story_dialog(page: ft.Page):
    """Create dialog for loading existing stories"""
    
    # Get all available stories
    story_names = user.get_all_story_names()
    
    if not story_names:
        # No stories available
        return ft.AlertDialog(
            modal=True,
            title=ft.Text("No Stories Found"),
            content=ft.Text("No existing stories were found. Create a new story first."),
            actions=[
                ft.TextButton("OK", on_click=lambda e: setattr(e.control.parent.parent, 'open', False) or page.update())
            ]
        )
    
    # Create list of story tiles
    story_tiles = []
    selected_story = ft.Ref[str]()
    selected_story.current = story_names[0] if story_names else None
    
    def story_selected(story_name):
        selected_story.current = story_name
        for tile in story_tiles:
            tile.selected = (tile.title.value == story_name)
        page.update()
    
    for story_name in story_names:
        is_active = (user.active_story and user.active_story.title == story_name)
        
        tile = ft.ListTile(
            leading=ft.Icon(ft.Icons.BOOK if not is_active else ft.Icons.BOOK_ONLINE),
            title=ft.Text(story_name),
            subtitle=ft.Text("Active Story" if is_active else "Available Story"),
            selected=selected_story.current == story_name,
            on_click=lambda e, name=story_name: story_selected(name)
        )
        story_tiles.append(tile)
    
    def load_story_clicked(e):
        if not selected_story.current:
            page.open(ft.SnackBar(ft.Text("Please select a story")))
            return
        
        if user.active_story and user.active_story.title == selected_story.current:
            page.open(ft.SnackBar(ft.Text(f"'{selected_story.current}' is already the active story")))
            dialog.open = False
            page.update()
            return
        
        try:
            # Switch to selected story
            success = user.switch_active_story(selected_story.current)
            
            if success:
                # Update page title
                page.title = f"StoryBoard -- {user.active_story.title} -- Saved"
                
                # Close dialog
                dialog.open = False
                page.update()
                
                # Show success message
                page.open(ft.SnackBar(ft.Text(f"Switched to story: {selected_story.current}")))
            else:
                page.open(ft.SnackBar(ft.Text(f"Failed to load story: {selected_story.current}")))
                
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error loading story: {str(ex)}")))
    
    def cancel_clicked(e):
        dialog.open = False
        page.update()
    
    def delete_story_clicked(e):
        if not selected_story.current:
            page.open(ft.SnackBar(ft.Text("Please select a story to delete")))
            return
        
        if selected_story.current == "default_story":
            page.open(ft.SnackBar(ft.Text("Cannot delete the default story")))
            return
        
        # Create confirmation dialog
        def confirm_delete(e):
            try:
                success = user.delete_story(selected_story.current)
                if success:
                    page.open(ft.SnackBar(ft.Text(f"Deleted story: {selected_story.current}")))
                    # Refresh the dialog
                    dialog.open = False
                    page.update()
                    new_dialog = create_load_story_dialog(page)
                    page.open(new_dialog)
                else:
                    page.open(ft.SnackBar(ft.Text(f"Failed to delete story: {selected_story.current}")))
            except Exception as ex:
                page.open(ft.SnackBar(ft.Text(f"Error deleting story: {str(ex)}")))
            
            confirm_dialog.open = False
            page.update()
        
        def cancel_delete(e):
            confirm_dialog.open = False
            page.update()
        
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Are you sure you want to delete the story '{selected_story.current}'?\n\nThis action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.ElevatedButton("Delete", on_click=confirm_delete, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
            ]
        )
        
        page.open(confirm_dialog)
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Load Story"),
        content=ft.Container(
            content=ft.Column([
                ft.Text("Select a story to load:"),
                ft.Container(
                    content=ft.ListView(
                        controls=story_tiles,
                        height=250,
                    ),
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=8,
                    padding=5,
                ),
            ], tight=True),
            width=500,
            height=350
        ),
        actions=[
            ft.TextButton("Delete", on_click=delete_story_clicked, icon=ft.Icons.DELETE, 
                         style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.Container(expand=True),  # Spacer
            ft.TextButton("Cancel", on_click=cancel_clicked),
            ft.ElevatedButton("Load Story", on_click=load_story_clicked),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    
    return dialog


def save_current_story(page: ft.Page):
    """Save the current active story"""
    try:
        if not user.active_story:
            page.open(ft.SnackBar(ft.Text("No active story to save")))
            return
        
        # Save story metadata
        user.active_story.save_story_metadata()
        
        # Show success message
        page.open(ft.SnackBar(ft.Text(f"Story '{user.active_story.title}' saved successfully")))
        
        # Update page title to show saved status
        page.title = f"StoryBoard -- {user.active_story.title} -- Saved"
        page.update()
        
    except Exception as e:
        page.open(ft.SnackBar(ft.Text(f"Error saving story: {str(e)}")))
