''' 
Loads all data in a directory and adds it to expansion tiles or to rail (column) for uniform look 
When called recursively, only the parent expansion tile argument is provided
When called initially when there is no parent dropdown, a column is provided instead
'''

import flet as ft
import os
import json
from models.views.story import Story
from styles.tree_view.tree_view_directory import TreeViewDirectory
from styles.tree_view.tree_view_file import TreeViewFile


def load_directory_data(
    page: ft.Page,                                        # Page reference for overlays if needed    
    story: Story,                                         # Story reference for any story related data
    directory: str,                                       # The directory to load data from
    rail: ft.Control,                                     # The rail this tree view is in
    dir_dropdown: TreeViewDirectory = None,             # Optional parent expansion tile for when recursively called
    column: ft.Column = None,                             # Optional parent column to add elements too when not starting inside a tile
    tags: list[str] = None,                                 # Only load widgets with specific tags for this directory
    additional_directory_menu_options: list[ft.Control] = None,      # Additional menu options passed in from parent rail to be used for directories
    additional_file_menu_options: list[ft.Control] = None   
    # Only dir_dropdown OR column should be provided, but one is required
) -> ft.Control:
    
    def _canon_path(p: str) -> str:
        return os.path.normcase(os.path.normpath(p))
    

    try: 

        # Gives us a list of all files and folders in our current directory
        entrys = os.listdir(directory)

        # Keep track of directories vs files so we can add them in the order we want
        directories = []
        files = []  

        # Goes through them all
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
        for directory_name in directories:

            # Set the path and give us the capitalized name
            full_path = os.path.join(directory, directory_name)
            capital_dir_path = directory_name.capitalize()
            
            # Build a normalized map of folder metadata once per call in order to get the call
            folders_meta = { _canon_path(k): v for k, v in story.data.get('folders', {}).items() }

            # Set our data to pass in for the folder
            color = folders_meta.get(_canon_path(full_path), {}).get('color', "primary")
            is_expanded = folders_meta.get(_canon_path(full_path), {}).get('is_expanded', False)

            # Create the expansion tile here
            new_expansion_tile = TreeViewDirectory(
                full_path=full_path,
                title=capital_dir_path,
                story=story, page=page,
                color=color, rail=rail,
                is_expanded=is_expanded,
                additional_menu_options=additional_directory_menu_options,
                father=dir_dropdown if dir_dropdown is not None else None,
            )

            # Recursively go through this directory as well to load its data, and any sub directories
            load_directory_data(
                page=page,                                                # Page reference
                story=story,                                              # Story reference
                directory=full_path,                                      # Our new directory to load
                dir_dropdown=new_expansion_tile,                          # Our new parent expansion tile
                rail=rail,
                tags=tags,                                                # Any tags to filter by
                additional_directory_menu_options=additional_directory_menu_options,           # Any additional menu options to pass down
                additional_file_menu_options=additional_file_menu_options
            )

            # Add our expansion tile for the directory to its parent, or the column if top most directory
            if dir_dropdown is not None:
                dir_dropdown.content.content.controls.append(new_expansion_tile)
            else:
                column.controls.append(new_expansion_tile)

        # Now go through our files
        for file_name in files:
            widget = None

            try:
                # Load the file data to see if it's valid
                with open(os.path.join(directory, file_name), 'r', encoding='utf-8') as f:
                    file_data = json.load(f)

                key = file_data.get('key', None)

                

                for widget in story.widgets:
                    if widget.data.get('key', None) == key:
                        widget = widget
                        break

            except Exception as e:
                print(f"Error loading file {file_name} in directory {directory}: {e}")
                continue
            
            
            if widget is not None:

                for tag in (tags if tags is not None else []):
                    if widget.data.get('tag', None) == tag:
                        # Create the file item
                        item = TreeViewFile(
                            widget,
                            father=dir_dropdown if dir_dropdown is not None else None,
                            additional_menu_options=additional_file_menu_options
                        )        

                        # Add them to parent expansion tile if one exists, otherwise just add it to the column
                        if dir_dropdown is not None:
                            dir_dropdown.content.content.controls.append(item)
                        else: 
                            column.controls.append(item)
                        pass

                        break
                    else:
                        continue

        # Return the parent expansion tile or column depending on what was provided
        return dir_dropdown if dir_dropdown is not None else column
    
    # Handle errors
    except Exception as e:
        print(f"Error loading directory data from {directory}: {e}")
        return None