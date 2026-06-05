''' 
Loads all data in a directory and adds it to expansion tiles or to rail (column) for uniform look 
When called recursively, only the parent expansion tile argument is provided
When called initially when there is no parent dropdown, a column is provided instead
'''

import flet as ft
import os
import json
from models.views.story import Story
from styles.rail.tree_view_directory import TreeViewDirectory
from styles.rail.tree_view_file import TreeViewFile
import math


def load_directory_data(
    page: ft.Page,                                        # Page reference for overlays if needed    
    story: Story,                                         # Story reference for any story related data
    directory: str,                                       # The directory to load data from
    rail: ft.Control,                                     # The rail this tree view is in
    folder: TreeViewDirectory = None,             # Optional parent expansion tile for when recursively called
    column: ft.Column = None,                             # Optional column to add to if this is the top most call with no parent expansion tile
) -> ft.Control:
    
    def _canon_path(p: str) -> str:
        return os.path.normcase(os.path.normpath(p))
    

    try: 

        # Gives us a list of all files and folders in our current directory
        entrys = os.listdir(directory)

        # Keep track of directories vs files so we can add them in the order we want
        directories = []
        files = []  

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

            # Create the new folder dropdown
            new_folder = TreeViewDirectory(
                full_path=full_path,
                title=capital_dir_path,
                story=story, page=page,
                color=color, rail=rail,
                is_expanded=is_expanded,
                father=folder,
            )

            # Since its a folder, load all its content recursively
            load_directory_data(
                page=page,                                                
                story=story,                                            
                directory=full_path,                                      
                folder=new_folder,                     
                rail=rail,
            )


            # After loading the folders content, add it to either a parent folder (if it has one) or the column for the rail
            if folder is not None:
                folder.expansion_tile.controls.append(new_folder)
            else:
                column.controls.append(new_folder)

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

                # Create the file item
                file = TreeViewFile(
                    widget,
                    father=folder,
                )       


                # Add them to parent expansion tile if one exists, otherwise just add it to the column
                if folder is not None:
                    folder.expansion_tile.controls.append(file)
                else: 
                    column.controls.append(file)
                

            else:
                print("Could not find widget")
                continue

        # Return the parent expansion tile or column depending on what was provided
        return folder if folder is not None else column
    
    # Handle errors
    except Exception as e:
        print(f"Error loading directory data from {directory}: {e}")
        return None