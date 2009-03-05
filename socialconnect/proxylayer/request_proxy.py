import sys


class Proxy(object):
    '''
        This is a generic proxy to deal with any platform. It acts as an interface for a Facebook or OpenSocial proxy.
        All methods in this class raise a NotImplementedError Exception to imitate an interface behavior. The methods
        are implemented in the subclasses
        
        Params: 
            com_object: A communication object related to the target platform. This object is an instance of the pyfacebook or opensocial library.
            
    '''
    
    def __init__(self, com_object):
        self.com_object = com_object
    
    
    def get_friends(self):
        '''
            Returns the friends of the authentificated user.                        
        '''
        raise NotImplementedError

    def get_users_profile(self): 
        '''
            Return a list of profiles related to the uids list.
        '''
        raise NotImplementedError       
        
    def get_profile(self):
        '''
            This function return the profile of the authentificated user by calling getUsersProfile with the user uid as parameter

        '''
        raise NotImplementedError   
            
    def get_groups(self):
        '''
            This function return the groups of the authentificated user.
        '''
        raise NotImplementedError   
                    
    def publish_user_action(self): 
        '''
            This function publish an action using a given template
        '''
        raise NotImplementedError
                
    def send_notifications(self):
        '''
            This function send a notification to the ids provided
        '''
        raise NotImplementedError       
            

    
class FBRequestProxy(Proxy):
    ''' 
        This is a proxy to send requests to Facebook
        
        Params: 
            com_object: a communication object related to the target platform
                        this object is related to the pyfacebook library
        
    '''
    
    def __init__(self, fb):
        Proxy.__init__(self, fb)
                
                
    def get_friends(self, fields, get_profiles=False):      
        '''
            Returns the friends of the authentificated user.
            
            Params:
                fields: A list of fields to retrieve for each friend. If not present, the default list is used.
                get_profile: if True, a second request is made to get the profile of the users form the first call
                        
        '''
        
        # calling the communication object to retrieve a list of friends uids
        friends_ids = self.com_object.friends.get()
        
        if not get_profiles:
            # return list of ids
            return friends_ids
        else:                   
            # return list of friend's profiles with a second call
            return self.com_object.users.getInfo(friends_ids, fields)
        


    def get_users_profile(self, uids, fields):      
        '''
            This function return the profiles from a list of user uid, useful to retrieve friends profile for example

            Params:
                uids: list of user id
                fields: A list of fields to retrieve for the profile. If not present, the default list is used.
        '''

        return self.com_object.users.getInfo(uids, fields)
    
    
    def get_profile(self, fields):
        '''
            This function return the profile of the authentificated user by calling getUsersProfile with the user uid as parameter

            Params: 
                fields: A list of fields to retrieve for the profile. If not present, the default list is used.

        '''
        return self.get_users_profile(self.com_object.uid, fields)
    

    def get_groups(self):   
        '''
            This function return the groups of the authentificated user on the target platform
        ''' 
        return self.com_object.groups.get(self.com_object.uid)

        
    def publish_user_action(self, template_id, template_data=None, target_ids=None): 
        '''
            This function publish an action using a given template
        '''
        try:
            return self.com_object.feed.publishUserAction(template_id, template_data, target_ids)
            
        except FacebookError, ex:
            # Feed limit error
            if ex.code in [340, 341]:
                return 0
            else:
                raise
            

    def send_notifications(self, uids, text, type='user_to_user'):
        '''
            This function send a notification to the ids provided
            
            Params:
                uids: target users
                text: text of the notification
                type: type is 'user_to_user' by default but 'app_to_user' is also possible
            
        '''
        return self.com_object.notifications.send(uids, text, type=type)
        

        

class OSRequestProxy(Proxy):
    ''' 
        This is a proxy to send request to OpenSocial
    '''
    
    
    def __init__(self, os):
        Proxy.__init__(self, os)


    def get_friends(self, fields, get_profiles=False):
        '''
            Returns the friends of the authentificated user.
            
            Params:
                fields: A list of fields to retrieve for each friend. If not present, the default list is used.
                get_profile: if True, the profile are filtered to have only the ids
                        
        '''
        friends = self.com_object.get_friends(fields)       
        
        if get_profiles:
            # return the friends and their profile
            return friends
        else:
            # return list of ids
            return map(lambda friend: friend['id'], friends)

        
    def get_users_profile(self, ids, fields): 
        '''
            This function return the profiles from a list of user uid, usefull to retrieve friends profile for example
            
            Params:
                uids: list of user id
                fields: A list of fields to retrieve for the profile. If not present, the default list is used
        '''
        
        return self.com_object.get_users_profile(ids, fields)
                
        
        
    def get_profile(self, fields):
        '''
            This function return the profile of the authentificated user by calling getUsersProfile with the user uid as parameter

            Params: 
                fields: A list of fields to retrieve for the profile. If not present, the default list is used.

        '''
        
        return self.get_users_profile(['@me'], fields)



        




