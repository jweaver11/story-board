
# Called when an object (Widget or Mini Widget) is loaded or created. 
def verify_data(object, required_data: dict) -> bool:
    ''' 
    Verifys an object's data has all required keys and sub keys passed in. Accepts default values or types.
    So long as the key exists, it will not override it or do type checking, else it will set it to the default value passed in
    Objects MUST have a save_dict() method, and a data attribute thats a dict.

    example: _verify_data(
        object=object, 
        required_data = {
            key1, "value1", 
            key2: int, 
            key3: {subkey1: str, subkey2: [1, 2, 3]}
        }
    )
    '''

    # Internal recursive function to handle nested dicts, typing, and values all in one
    def _verify_data(current_data: dict, required_data: dict = {}):
        ''' Internal recursive function to verify nested dicts '''
        
        # Run through each key in the required data we passed in
        for key, value in required_data.items():

            # If its a certain type and the data doesn't match, make it default value of that type (int=0, str="", etc.)
            if isinstance(value, type):

                # Make sure the key doesn't already exist so we don't override it
                if key not in current_data:
                    current_data[key] = value()
            
            # If its a dict, make sure our key is a dict too, then recurse through this function
            elif isinstance(value, dict):

                # Make sure the key doesn't already exist so we don't override it
                if key not in current_data or not isinstance(current_data[key], dict):
                    current_data[key] = {}
                    
                # Recurse through this function to verify the nested dict
                _verify_data(current_data[key], value)
            
            # Otherwise, we just set the value
            else:

                # Make sure the key doesn't already exist so we don't override it
                if key not in current_data:
                    current_data[key] = value
                
                # Special cases where we overwrite certain values regardless of existing data
                elif key == 'tag':      # So widgets can differentiate between themselves
                    current_data[key] = value
                elif key == 'pin_location':     # Where widgets are pinned in the workspace
                    current_data[key] = value
                elif key == 'directory_path':   # If the directory path changes, we need to update it
                    current_data[key] = value
                elif key == 'side_location':    # To ensure side location is always correct
                    current_data[key] = value
                elif key =='mini_widgets_displayed_overtop': 
                    current_data[key] = value  
               
        

    # Main block to run our internal function above
    try:

        # Sets our data to an empty dict if None or not a dict, so we can add to it
        if object.data is None or not isinstance(object.data, dict):
            object.data = {}

        # Run our objects data through the recursive function, and the required data
        _verify_data(object.data, required_data)

        # Save our updated data back to the file
        object.save_dict()      
        return True
    
    # Catch errors
    except Exception as e:
        print(f"Error verifying data for object {object.title}: {e}")
        return False
