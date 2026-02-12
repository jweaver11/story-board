''' 
Default data dict for character data templates 
'''

def default_character_template_data_dict() -> dict:
    return {
        #'Template Data': dict,     # This is how templates store their data
        'Basic Info': {
            'Summary': str,     # Short summary of the character. Optional
            'Nickname': str,    
            'Role': str,        # Importance of character in the story. Main, Side, Background, None
            'Tag': str,         # Tag for custom grouping of characters. Protagonist, Antagonist, Supporting, None
            'Morality': str,    
            'Age': str,         
            'Nationality': str, 
            'Occupation': str,  
            'Personality': str, 
            'Goals': str,       
        },
        'Physical Description': {
            'Build': str,           # Sumarrized build of character 
            'Sex': str, 
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
        
        'Custom Fields': dict       # Anything the user wants to add on their own
        # custom fields {label: value, num_dogs: 5}
    }