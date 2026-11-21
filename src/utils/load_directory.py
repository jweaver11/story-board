''' 
Loads all data in a directory and adds it to expansion tiles or to rail (column) for uniform look 
When called recursively, only the parent expansion tile argument is provided
When called initially when there is no parent dropdown, a column is provided instead
'''

import flet as ft
import os
import json
from models.views.story import Story
from styles.rail_folder import RailFolder
from styles.rail_file import RailFile
import math


def sort_entries(entrys: list, entry_type: str="file") -> list:
    '''Sort folders or files by the selected rail sort method, preserving their controls.'''
    from models.app import app
    sort_method = app.settings.data.get('story', {}).get('rail_sort_method', 'default')

    if sort_method not in (
        "alphabetical", "alphabetical_reversed",
        "color", "color_reversed",
        "creation_date", "creation_date_reversed",
    ):
        return entrys

    reverse = sort_method.endswith("_reversed")
    method = sort_method.removesuffix("_reversed")

    def sort_key(entry):
        # Nested entries are wrapped with an indentation control in a row.
        control = entry.controls[1] if isinstance(entry, ft.Row) else entry
        if entry_type == "folder":
            if method == "alphabetical":
                return control.title.lower()
            if method == "color":
                return str(control.color).lower()
            return control.created_at

        data = control.widget.data
        if method == "alphabetical":
            return (data.get('title') or '').lower()
        if method == "color":
            return (data.get('color') or '').lower()
        return data.get('created_at') or 0

    return sorted(entrys, key=sort_key, reverse=reverse)




def load_directory_controls(
    story: Story,                                         # Story reference for any story related data
    directory: str,                                       # The directory to load data from
    in_base_directory: bool=False                           # Optional column to add to if this is the top most call with no parent expansion tile
) -> list[ft.Control]:
    
    def _canon_path(p: str) -> str:
        return os.path.normcase(os.path.normpath(p))

    try: 

        # Gives us a list of all files and folders in our current directory
        entrys = os.listdir(directory)

        # Keep track of directories vs files so we can add them in the order we want
        directories = []
        files = []  

        directory_ctrls = []
        file_ctrls = []

        # Goes through all the folders and files
        for entry in entrys:
            # Set a full path they need for logic
            full_path =  os.path.join(directory, entry) 

            # Add to either directories or files list
            if os.path.isdir(full_path):
                directories.append(entry)
            elif os.path.isfile(full_path):
                files.append(entry)

        # Go through our directories first
        for directory_name in directories:

            # Set the path and give us the capitalized name
            full_path = os.path.join(directory, directory_name)
            capital_dir_path = directory_name.capitalize()
            
            # Build a normalized map of folder metadata once per call in order to get the call
            folders_meta = { _canon_path(k): v for k, v in story.data.get('folders', {}).items() }

            # Set our color and expanded state
            color = folders_meta.get(_canon_path(full_path), {}).get('color', "primary")
            is_expanded = folders_meta.get(_canon_path(full_path), {}).get('is_expanded', False)    
            created_at = folders_meta.get(_canon_path(full_path), {}).get('created_at', 0)
            notes = folders_meta.get(_canon_path(full_path), {}).get('notes', "")

            # Create the new folder dropdown
            new_folder = RailFolder(
                full_path=full_path,
                title=capital_dir_path,
                story=story,
                color=color, 
                is_expanded=is_expanded,
                created_at=created_at,
                notes=notes,
            )
            if in_base_directory == False:
                new_folder = ft.Row([
                    ft.Container(bgcolor=ft.Colors.OUTLINE_VARIANT, width=2, height=29, clip_behavior=ft.ClipBehavior.NONE),
                    new_folder
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

            directory_ctrls.append(new_folder)

        # Now go through our files
        for file_name in files:
            widget = None

            try:
                # Load the file data to see if it's valid
                with open(os.path.join(directory, file_name), 'r', encoding='utf-8') as f:
                    file_data = json.load(f)

                #key = file_data.get('key', None)
                id = file_data.get('id', None)
                widget = story.get_widget_by_id(id)

            except Exception as e:
                print(f"Error loading file {file_name} in directory {directory}: {e}")
                continue
            
            
            if widget is not None:

                # Create the file item
                file = RailFile(widget)       

                if in_base_directory == False:
                    file.expand = True
                    file = ft.Row([
                        ft.Container(bgcolor=ft.Colors.OUTLINE_VARIANT, width=2, height=29, clip_behavior=ft.ClipBehavior.NONE),
                        file
                    ], spacing=0)

                file_ctrls.append(file)

            else:
                print("Could not find widget")
                continue

        
        directory_ctrls = sort_entries(directory_ctrls, "folder")
        file_ctrls = sort_entries(file_ctrls, "file")

        # Return the parent expansion tile or column depending on what was provided
        return directory_ctrls + file_ctrls
    
    # Handle errors
    except Exception as e:
        print(f"Error loading directory data from {directory}: {e}")
        return None