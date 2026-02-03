''' 
Default data dict for character data templates 
'''

def default_character_template_data_dict() -> dict:
    return {
        #'Template Data': dict,     # This is how templates store their data
        'Basic Info': {
            'Summary': str,     # Short summary of the character. Optional
            'Nickname': str,    # Nickname or Alias of the character
            'Role': str,        # Importance of character in the story. Main, Side, Background, None
            'Tag': str,         # Tag for custom grouping of characters. Protagonist, Antagonist, Supporting, None
            'Morality': str,    # Lawful, netural, chaotic all have good, neutral, evil (9 alignments)
            'Age': str,         # Age of the character
            'Nationality': str, # Where character is from
            'Occupation': str,  # What the character does for a living
            'Personality': str, # Description of the character's personality
            'Goals': str,       # List of characters goals/motivations
        },
        'Physical Description': {
            'Sex': str, 
            'Build': str,           # Sumarrized build of character 
            'Race': str,  
            'Skin Color': str,  
            'Hair Color': str,   
            'Eye Color': str,    
            'Height': str,   
            'Weight': str,   
            'Distinguishing Features': str,  
        },
        
        'Family':  {
            'Love Interest': str,    
            'Father': str,   
            'Mother': str,    
            'Siblings': str,
            'Children': str,
            'Ancestors': str,
            'Other': str,
        },   
        'Origin': {     
            'Birth Date': str,   
            'Hometown': str,     
            'Education': str,        
            'Trauma': str,
        },  

        # Connections we have to other characters in the story
        'Connections': dict,    # Example: {'char_key': {'title': 'Joe', 'tags': 'Friend, Classmate'}}
        
        'Custom Fields': dict       # Anything the user wants to add on their own
        # custom fields {key: {label: str, value: str}, key2: {label: str, value: str} ... }
    }