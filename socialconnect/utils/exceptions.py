
class NoTokenException(Exception):  
    def __init__(self, value=None):
        self.parameter = value

    def __unicode__(self):
        return repr(self.parameter)

class NoFBTokenException(NoTokenException):
    def __init__(self, value=None):
        NoTokenException.__init__(self, value)

class NoOSTokenException(NoTokenException):     
    def __init__(self, value=None):
        NoTokenException.__init__(self, value)



        
class NotSyncException(Exception):  
    def __init__(self, value=None):
        self.parameter = value

    def __unicode__(self):
        return repr(self.parameter)

class NotFBSyncException(NotSyncException):
    def __init__(self, value=None):
        NotSyncException.__init__(self, value)

class NotOSSyncException(NotSyncException):     
    def __init__(self, value=None):
        NotSyncException.__init__(self, value)
        
    
    
    
class RedirectException(Exception): 
    def __init__(self, value=None):
        self.parameter = value

    def __unicode__(self):
        return repr(self.parameter)
        
class RedirectFBException(RedirectException):
    def __init__(self, value=None):
        RedirectException.__init__(self, value)

class RedirectOSException(RedirectException):       
    def __init__(self, value=None):
        RedirectException.__init__(self, value)
        
        
        
class NotSupportedException(Exception): 
    def __init__(self, value=None):
        self.parameter = value
        
    def __unicode__(self):
        return repr(self.parameter)
        
        
class UsedAccountException(Exception):  
    def __init__(self, value=None):
        self.parameter = value

    def __unicode__(self):
        return repr(self.parameter)
        
        
class SocialConnectException(Exception):    
    def __init__(self, value=None):
        self.parameter = value

    def __unicode__(self):
        return repr(self.parameter)     
