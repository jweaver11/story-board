import os
import json
from contexts.constants import STORIES_DIRECTORY_PATH

# Called on app startup in main
def load_stories(app):
    ''' Loads our saved stories from the json files in story folders within the stories directory. If none exist, do nothing '''
    from models.views.story import Story

    # Create the stories directory if it doesnt exist already
    os.makedirs(STORIES_DIRECTORY_PATH, exist_ok=True)
        
    # Iterate through all items in the stories directory
    for story_folder in os.listdir(STORIES_DIRECTORY_PATH):

        story_directory = os.path.join(STORIES_DIRECTORY_PATH, story_folder)
        
        # Look for JSON files within this story folder (ignore subdirectories)
        try:
            
            # Check every item (folder and file) in this story folder
            for item in os.listdir(story_directory):

                # Check for the story json data file. If it is, we'll load our story around this file data
                if item.endswith(".json"):

                    # Set the file path to this json file so we can open it
                    file_path = os.path.join(story_directory, item)

                    # Read the JSON file
                    with open(file_path, "r", encoding='utf-8') as f:
                        # Set our data to be passed into our objects
                        story_data = json.load(f)

                    # Our story title is the same as the folder
                    story_title = story_data.get("title", file_path.replace(".json", ""))
                    story_id = story_data.get("id", file_path.replace(".json", ""))
                        
                    app.stories[story_id] = Story(story_title, story_data)

                    break
                # Else, continue through the next story folder
                else:
                    continue
                    
        except Exception as e:
            print(f"Error loading story {story_title}: {e}. May not be a directory")

    app.ignore_settings_change = False