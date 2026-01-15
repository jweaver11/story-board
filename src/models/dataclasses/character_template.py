''' 
Default data dict for character data templates 
'''
# Role ^
# Morality ^
# Age ^
# Prefix ^
# Nationality ^ 
# Nationality ^
# Occupation ^
# Goals ^
# Physical Description {}
# Family {}
# Origin {}
# Strengths []
# Weaknesses []
# Personality
# Connections {}
# Custom fields {}

def default_character_template_data_dict() -> dict:
    return {
        'Summary': str,  # Short summary of the character. Optional
        'Role': "None",   # Importance of character in the story. main, side, background, uncategorized
        'Morality': str,  # Lawful, netural, chaotic all have good, neutral, evil (9 alignments)
        'Age': str, # Age of the character
        'Nationality': str, # Where character is from
        'Occupation': str, # What the character does for a living
        'Goals': list,          # List of characters goals/motivations
        'Personality': str,  # Description of the character's personality
        'Physical Description': {
            'Sex': str,     # Biology of the character. Has add option
            'Build': str,   # Sumarrized build of character 
            'Race': str,    # Race of the character. Has add option
            'Skin Color': str,  
            'Hair Color': str,   
            'Eye Color': str,    
            'Height': str,   
            'Weight': str,   
            'Distinguishing Features': str,  
        },
        
        'Family':  { #TODO "connections" dropdown+tree/detective view?
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
        },  
        'Connections': {
            #TODO list of other characters and relationship types
        },
        'Custom Fields': dict       # Anything the user wants to add on their own
        # custom fields {key: {label: str, value: str}, key2: {label: str, value: str} ... }
    }