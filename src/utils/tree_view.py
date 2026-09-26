''' 
Loads all data in a directory and adds it to expansion tiles or to rail (column) for uniform look 
When called recursively, only the parent expansion tile argument is provided
When called initially when there is no parent dropdown, a column is provided instead
'''

import flet as ft
import os
import json
from models.views.story import Story
from styles.tree_view_folder import RailFolderView
from styles.tree_view_file import RailFile
import math

# Helper function to normalize paths for consistent comparison
def _canon_path(p: str) -> str:
    return os.path.normcase(os.path.normpath(p))


# Load all data in a directory and add it to expansion tiles or to rail (column) for uniform look
def load_directory_data(story: Story, directory: str) -> list[ft.Control]:

    try: 

        # Gives us a list of all files and folders in our current directory
        entrys = os.listdir(directory)

        
        directories = []    # List to store directory names separately
        files = []      # List to store file names separately

        # Lists to store the controls for directories and files separately
        directory_controls = []   
        file_controls = []

        # Goes through all the folders and files in the directory, create a full path for them, and categorize them into directories and files lists
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
            

            # Grab and normalize the full path
            full_path = os.path.join(directory, directory_name)     
            #full_path = _canon_path(full_path)

            # Grab the data from the story
            
            folder_data = story.folders[full_path]
            
            if not folder_data:
                print(f"No folder data found for {full_path}")
                continue

            # Create the new folder dropdown
            folder_view = RailFolderView(folder_data, story)

            # Since its a folder, load all its content recursively
            load_directory_data(story, full_path)

            # After loading the folders content, add it to either a parent folder (if it has one) or the column for the rail
            directory_controls.append(folder_view)


        # Now go through our files
        for file_name in files:
            break
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
            
            # Add the file control to the controls list
            if widget:    
                file_controls.append(RailFile(widget, story))
                
            else:
                print("Could not find widget inside load_directory_data")
                continue

        # Sort Folders and files alphabetically
        #directory_controls.sort(key=lambda x: x.folder_data['name'].lower())
        #file_controls.sort(key=lambda x: x.widget.title.lower())

        # Retrun directory/folder controls on top, followed by file controls
        return directory_controls + file_controls
    
    # Handle errors
    except Exception as e:
        print(f"Error loading directory data from {directory}: {e}")
        return None