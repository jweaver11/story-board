''' 
Default data dict for character data templates 
'''
 
def default_character_template_data_dict() -> dict:
    return {

        #'About': "",

        'Basic Info': {
            'Nickname': "",    
            'Role': "",        # Importance of character in the story. Main, Side, Background, None
            'Tag': "",         # Tag for grouping of characters. Protagonist, Antagonist, Supporting, None
            'Morality': "",    
            'Age': "",         
            'Nationality': "", 
            'Occupation': "",  
            'Personality': "", 
            'Goals': "",       
        },
        'Physical Description': {
            'Build': "",           # Sumarrized build of character 
            'Main Outfit': "",      
            'Sex': "", 
            'Race': "",  
            'Skin Color': "",  
            'Hair Color': "",   
            'Eye Color': "",    
            'Height': "",   
            'Weight': "",   
            'Distinguishing Features': "",  
        },
        'Family':  {
            'Love Interest': "",    
            'Father': "",   
            'Mother': "",    
            'Siblings': "",
            'Children': "",
            'Ancestors': "",
            'Other': "",
        },   
        'Origin': {     
            'Birth Date': "",   
            'Hometown': "",     
            'Education': "",        
            'Trauma': "",
        },  
        'Notes': {}       # Anything the user wants to add on their own
    }