''' Returns our folder's sub-folders and widgets so users are aware of what all they're deleting '''

import flet as ft
import os
import json
from models.views.story import Story


def return_folder_content(directory: str, story: Story, expansion_tile: ft.ExpansionTile | ft.Column):
    ''' Returns a list of flet controls representing the contents of the folder '''

    # Return normalized path for folder comparison
    def _canon_path(p: str) -> str:
        return os.path.normcase(os.path.normpath(p))

    # Gives us a list of all files and folders in our current directory
    entrys = os.listdir(directory)

    # Keep track of directories vs files so we can add them in the order we want
    directories = []
    files = []  

    # Goes through every folder and file and categorizes them
    for entry in entrys:

        # Sets the new path
        full_path =  os.path.join(directory, entry)

        # Add directories to their own list
        if os.path.isdir(full_path):
            directories.append(entry)

        # Add files to their own list
        elif os.path.isfile(full_path):
            files.append(entry)

    # Go through our directories first
    for folder_name in directories:

        # Set the path and give us the capitalized name
        full_path = os.path.join(directory, folder_name)
        capital_dir_path = folder_name.capitalize()
        
        # Build a normalized map of folder metadata once per call in order to get the call
        folders_meta = { _canon_path(k): v for k, v in story.data.get('folders', {}).items() }

        # Set our data to pass in for the folder
        color = folders_meta.get(_canon_path(full_path), {}).get('color', "primary")

        new_expansion_tile = ft.ExpansionTile(
            title=ft.Text(capital_dir_path, color=color, weight=ft.FontWeight.BOLD), 
            leading=ft.Icon(ft.Icons.FOLDER_OUTLINED, color=color),
            controls_padding=ft.Padding(15, 5, 0, 5), dense=True,
            tile_padding=ft.Padding(5, 0, 0, 0), shape=ft.RoundedRectangleBorder(),
        )

        # Recursivly load the new folders content as well
        return_folder_content(full_path, story, new_expansion_tile)

        if new_expansion_tile.controls:
            new_expansion_tile.expanded = True

        # Add our expansion tile for the directory to its parent, or the column if top most directory
        expansion_tile.controls.append(new_expansion_tile)
        
    # Now go through our files
    for file_name in files:
        
        # Load the file data to see if it's valid
        with open(os.path.join(directory, file_name), 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        title = file_data.get('title', None)
        tag = file_data.get('tag', [])
        color = file_data.get('color', ft.Colors.PRIMARY)

        # Set our icon based on what type of widget we are using tag
        match tag:
            case "document": icon = ft.Icon(ft.Icons.DESCRIPTION_OUTLINED)
            case "canvas": icon = ft.Icon(ft.Icons.BRUSH_OUTLINED)
            case "canvas_board": icon = ft.Icon(ft.Icons.SPACE_DASHBOARD_OUTLINED)
            case "note": icon = ft.Icon(ft.Icons.STICKY_NOTE_2_OUTLINED)
            case "character": icon = ft.Icon(ft.Icons.PERSON_OUTLINE)
            case "character_connection_map": icon = ft.Icon(ft.Icons.ACCOUNT_TREE_OUTLINED)
            case "plotline": icon = ft.Icon(ft.Icons.TIMELINE)
            case "map": icon = ft.Icon(ft.Icons.MAP_OUTLINED)
            case "world": icon = ft.Icon(ft.Icons.PUBLIC_OUTLINED)
            case "object": icon = ft.Icon(ft.Icons.SHIELD_OUTLINED)
            case _: icon = ft.Icon(ft.Icons.ERROR_OUTLINE)

        expansion_tile.controls.append(ft.Row([icon, ft.Text(f"{title}", weight=ft.FontWeight.BOLD)]))

