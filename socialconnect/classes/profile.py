import re
import time
from datetime import date


class Profile(object):
    '''
        Profile is the interface for Facebook or OpenSocial profile to describe a person.
        It's built arround a minimal list of fields available on both platforms.
        
        Each sub-class FBProfile or OSProfile has specfic method for extracting more detailed information from those fields.

        Params:
            id:
            name:
            profile_url (optional):
            birthday (optional):
            sex (optional):
            description (optional):
            emails (optional):
            address (optional):
            picture (optional):
            work_history (optional):

    '''

    def __init__(self, id, name, profile_url='', birthday='', sex='', description='', emails='', address='', picture='', work_history=''):
        self.id = id
        self.displayName = name
        self.givenName, self.familyName = self.extract_names()
        self.profile_url = profile_url      
        self.birthday = self.extract_birthday(birthday)
        self.gender = self.extract_sex(sex)
        self.aboutMe = description
        self.emails = emails
        self.address = address
        self.street_address = None
        self.locality = None
        self.postalCode = None
        self.region = None
        self.country = None
        self.phoneNumbers = None
        self.photo = picture
        self.work_history = work_history
        self.organization = None
        

    @staticmethod
    def get_default_fields(platform):
        '''
            Retrieveable fields for each platform.  
        ''' 
        
        if platform == 'FB':
            return {'id': u'uid', 'displayName': u'name', 'profile_url': u'profile_url', 'birthday': u'birthday', 'gender': u'sex', 'aboutMe': u'about_me', 'emails': u'email_hashes', 'address': u'current_location', 'photo': u'pic', 'work_history': u'work_history'}
        else:
            return {'id': u'id', 'displayName': u'displayName', 'profile_url': u'profileUrl', 'birthday': u'birthday', 'gender': u'gender', 'aboutMe': u'aboutMe', 'emails': u'emails', 'address': u'addresses', 'photo': u'thumbnailUrl', 'work_history': u'organizations'}

        
        
    def extract_names(self):
        '''
            This method tries to extract the firstname and lastname from the name.
            If there is a space in the displayName, it take the first token as the givenName and the second as familyName.
        '''

        if self.displayName.count(' ') != 0:
            names = self.displayName.split(' ', 1)
            return names[0], names[1]
        else:
            return self.displayName, ''


    def extract_sex(self, sex):
        '''
            This method tries to extract the gender of the user.
        '''
        
        raise NotImplementedError
            
            
    def extract_birthday(self, birthday):
        '''
            This method tries to extract the birthday of the user to build a Python date.
        '''
        
        raise NotImplementedError
            
                

    def __unicode__(self):
        return self.displayName

    #Find a way to declare reg exp for each platforms, maybe in the models. What is here is completely static and MUST be changed
    
    #Voir pour etendre avec un objet par platforme voir __attr__ et aussi la redefinition des fcts foo_get, foo_del, foo_set (pour les platformes qui n'ont pas tous les types ou autre)


class FBProfile(Profile):
    
        
    def extract_sex(self, sex):
        '''
            This method tries to extract the gender of the user.
        '''     
        if sex is not None:     
            # Format: male              
            reg_male = re.compile('^male$')
            # Format: female            
            reg_female = re.compile('^female$')
            
            if reg_male.match(sex):
                return 'M'
            elif reg_female.match(sex)  :
                return 'F'          
        return 'X'
    
    
    def extract_birthday(self, birthday):
        '''
            This method tries to extract the birthday of the user to build a Python date.
        '''

        if birthday is not None:
            # Format: January 1, 1970
            reg = re.compile('^(\w+)\s(\d{1,2}),\s(\d{4})$')
            m = reg.match(birthday)
            
            if m:
                return date(int(m.group(3)), time.strptime(m.group(1), "%B")[1], int(m.group(2)))

        return birthday
        
        
class OSProfile(Profile):
    

    def extract_sex(self, sex):
        '''
            This method tries to extract the gender of the user.
        '''     
        if sex is not None:
            # Format: male or Male
            reg_male = re.compile('^male|Male$')
            # Format: female or Female
            reg_female = re.compile('^female|Female$')
            
            if reg_male.match(sex):
                return 'M'
            elif reg_female.match(sex):
                return 'F'          
        return 'X'
    
    
    def extract_birthday(self, birthday):
        '''
            This method tries to extract the birthday of the user to build a Python date.
        '''

        if birthday is not None:
            # Format: 1970-01-01
            reg = re.compile('^(\d{4})-(\d{2})-(\d{2})')
            m = reg.match(birthday)
            
            if m:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

        return birthday


