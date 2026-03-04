import flet as ft
from utils.safe_string_checker import return_safe_name

def story_is_unique(new_story_title: str) -> bool:
    ''' Checks if the given story title is unique among existing stories '''
    from models.app import app

    new_story_title = return_safe_name(new_story_title)
    
    # Compare against all existing story titles so we don't have any duplicates
    for story in app.stories.values():
        if return_safe_name(story.title) == new_story_title:
            print("Story title is not unique")
            return False
        
    # Reset error text if unique
    return True