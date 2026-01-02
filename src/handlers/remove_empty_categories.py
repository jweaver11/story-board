from styles.tree_view.tree_view_directory import TreeViewDirectory
from styles.tree_view.tree_view_file import TreeViewFile
import flet as ft



def remove_empty_categories(directory_control: TreeViewDirectory, parent_directory_control: TreeViewDirectory = None, parent_column: ft.Column = None):
    ''' Checks if our TreeViewDirectory is empty (No files or sub-directories with files) '''

    is_empty = True

    for control in directory_control.content.content.controls:

        # If we find a file control, we have widgets, so not empty
        if isinstance(control, TreeViewFile):
            is_empty = False
            break

        # Otherwise if we find a Directory (Sub-category) go back through that one
        elif isinstance(control, TreeViewDirectory):
            remove_empty_categories(control, parent_directory_control=directory_control)

    # If we're empty remove ourselves from our parent
    if is_empty:
        #print(f"Removing empty category: {directory_control.title}")
        
        # If we're inside another TreeViewDirectory
        if parent_directory_control is not None:
            parent_directory_control.content.content.controls.remove(directory_control)

        # If we're in the top most column of the rail
        else:
            parent_column.controls.remove(directory_control)

    else: 
        print("Not removing: ", directory_control.title)
        
    return
 