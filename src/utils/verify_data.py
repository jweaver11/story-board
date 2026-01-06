
# Called when an object (Widget or Mini Widget) is loaded or created. 
def verify_data(object, required_data: dict) -> bool:
    ''' 
    Verifys an object's data has all required fields passed in. 
    Objects MUST have a save_dict() method, and a data attribute thats a dict.
    '''

    # Internal recursive function to handle nested dicts, typing, and values all in one
    def _verify_data(current_data: dict, required_data: dict):
        ''' Internal recursive function to verify nested dicts '''
        
        # Run through each key in the required data we passed in
        for key, value in required_data.items():

            # If its a certain type and the data doesn't match, make it default value of that type (int=0, str="", etc.)
            if isinstance(value, type):

                # Make sure the key doesn't already exist so we don't override it
                if key not in current_data:
                    current_data[key] = value()

                # OLD
                #if key not in current_data or not isinstance(current_data[key], value):
                   #current_data[key] = value()
            
            # If its a dict, make sure our key our key is a dict too, then recurse through this function
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
                
                # Special case for overwriting defaults 'tag' key to always set the value
                elif key == 'tag':
                    current_data[key] = value

                # Special case for overwriting 'pin_location' key to always set the value
                elif key == 'pin_location':
                    current_data[key] = value

                # Special case for overwriting 'directory_path' key to always set the value (in case user moves files outside of app)
                elif key == 'directory_path':
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
