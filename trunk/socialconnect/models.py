import copy
import time

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from facebook import Facebook
from facebook import FacebookError
from opensocial import OpenSocial
from opensocial import OpenSocialError

from classes.profile import Profile, FBProfile, OSProfile
from proxylayer.request_proxy import FBRequestProxy, OSRequestProxy
from utils.exceptions import *


class PlatformManager(models.Manager):
    """
        Get the synchronized platforms of a user for a specific task.
    """
    
    def get_task_user(self, user, task):
        
        # filter the PlatformAccount to have only those with a platform that supports the task and then map the list to get a list of platforms
        return map(lambda x: x.platform, filter(lambda x: x.platform.as_leaf_class().support_task(task), PlatformAccount.objects.filter(user=user)))
        
        

class Platform(models.Model):
    ''' 
        This model represents a supported remote platform. This model works as an interface for an OpenSocial or Facebook platform.
        
    ''' 
    
    # name of the platform
    name = models.CharField(max_length=200)
    
    # entrypoint of the Platform REST API
    api_url = models.URLField(verify_exists=False)
    
    # a logo for the platform
    logo = models.ImageField(upload_to="images/logos", height_field="16", width_field="16", blank=True)
    
    # true if the platform is active
    is_active = models.BooleanField(default=True)
    
    # used to have the as_leaf_class method
    content_type = models.ForeignKey(ContentType, editable=False, null=True)
    
    # supported features by the platform
    support_people = models.BooleanField(default=False)
    support_groups = models.BooleanField(default=False)
    support_activities_push = models.BooleanField(default=False) 
    support_activities_pull = models.BooleanField(default=False) 
    support_notifications = models.BooleanField(default=False)
    
    # custom manager
    objects = PlatformManager()
    

    def save(self, *args, **kwargs):
        '''
            Custom saving function to be able to use the as_leaf_class() method.
        '''
        
        if not self.content_type :
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super(Platform, self).save(*args, **kwargs)


    def as_leaf_class(self):
        '''
            Get the FBPlatform or OSPlatform instance/child of the platform.
        '''
        content_type = self.content_type
        model = content_type.model_class()
        if(model == Platform):
            return self
        return model.objects.get(id=self.id)

        
    def support_task(self, task):
        '''
            Return True if the platform support the task. Raise an Exception if the task is not known.
            
            Params:
                task: the task
        '''
        if task == 'people':
            return self.support_people
        elif task == 'groups':              
            return self.support_groups
        elif task == 'activities_push':
            return self.support_activities_push
        elif task == 'activities_pull':
            return self.support_activities_pull
        elif task == 'appdata':
            return self.support_appdata
        elif task == 'notifications':
            return self.support_notifications
        else:
            raise Exception('support_task: task not known')
    
    
    def build_profiles(self, fields, profiles):
        ''' 
            This function takes the Json reponse from a platform and return a list of Profile objects 
            
            Params:
                fields: the fields we are waiting for in the profiles (vary as the platform)
                profiles: the profiles retrived from the platform

        '''
        
        profiles_objects = []
        for profile in profiles:
            if self.as_leaf_class().__class__ == FBPlatform:
                profiles_objects.append(FBProfile(profile[fields['id']], profile[fields['displayName']], profile.get(fields['profile_url'], None), profile.get(fields['birthday'], None), profile.get(fields['gender'], None), profile.get(fields['aboutMe'], None), profile.get(fields['emails'], None), profile.get(fields['address'], None), profile.get(fields['photo'], None), profile.get(fields['work_history'], None)))
            else:
                profiles_objects.append(OSProfile(profile[fields['id']], profile[fields['displayName']], profile.get(fields['profile_url'], None), profile.get(fields['birthday'], None), profile.get(fields['gender'], None), profile.get(fields['aboutMe'], None), profile.get(fields['emails'], None), profile.get(fields['address'], None), profile.get(fields['photo'], None), profile.get(fields['work_history'], None)))

        return profiles_objects
        
    def __unicode__(self):
        return self.name
            
            
            
class FBPlatform(Platform):
    ''' 
        A sub-model for Facebook and maybe for future Facebook-like platforms.
        
    '''
    
    # the url where to redirect the user for login
    login_url = models.URLField(verify_exists=False)
    
    # api_key and api_secret provided by the platform
    api_key = models.CharField(max_length=200)
    api_secret = models.CharField(max_length=200)
    
    # api version
    api_version = models.CharField(max_length=100, default='1.0')
    
    
    #def save(self, *args, **kwargs):
    #   if FBPlatform.objects.all().count() >= 1:
    #       raise Exception('Only one Facebook platform should be present at a time. To override this comment the FBPlatfom.save() method in SocialConnect models.')        
    #   super(FBPlatform, self).save(*args, **kwargs)
    
    
    def get_fields(self):
        '''
            This method returns a copy of the standard fields list. 
        '''
        return copy.copy(Profile.get_default_fields('FB'))
    
    
    def get_login_url(self):
        '''
            Build the Facebook login URL for Facebook authorization.
        '''
        return self.login_url+'?api_key='+self.api_key+'&v='+self.api_version+'&next='+reverse('fb_after_login')

        

class OSPlatform(Platform):
    '''
        A sub-model for an opensocial platform.
    ''' 

    # oauth key and secret provided by the platform
    oauth_consumer_key = models.CharField("Consumer key", max_length=200)
    oauth_consumer_secret = models.CharField("Consumer secret", max_length=200)
    
    # oauth urls
    oauth_request_token_url = models.URLField("Request token url", verify_exists=False)
    oauth_authorization_url = models.URLField("Authorization token url", verify_exists=False)
    oauth_access_token_url = models.URLField("Access token url", verify_exists=False)
    oauth_token_validity = models.IntegerField("Token validity", help_text="Validity of the token in seconds.")
    
    # oauth signature encryption methods
    OAUTH_METHODS = (
        ('OAuthSignatureMethod_HMAC_SHA1', 'HMAC_SHA1'),
        ('OAuthSignatureMethod_PLAINTEXT', 'PLAINTEXT'),
    )
    oauth_signature_method = models.CharField("Signature method", max_length=200, choices=OAUTH_METHODS)
    
    
    # special fields for platform OS
    # these fields are used to define special name for the fields send by an os platform
    os_id = models.CharField(max_length=200, blank=True, null=True)
    os_displayName = models.CharField(max_length=200, blank=True, null=True)    
    os_profileUrl = models.CharField(max_length=200, blank=True, null=True) 
    os_birthday = models.CharField(max_length=200, blank=True, null=True)   
    os_gender = models.CharField(max_length=200, blank=True, null=True) 
    os_description = models.CharField(max_length=200, blank=True, null=True)
    os_emails = models.CharField(max_length=200, blank=True, null=True)     
    os_addresses = models.CharField(max_length=200, blank=True, null=True)
    os_thumbnailUrl = models.CharField(max_length=200, blank=True, null=True)
    os_organizations = models.CharField(max_length=200, blank=True, null=True)
    
     

        
    def get_fields(self):
        '''
            This method takes the standard fields list and check if a special name
            is given for these fields for this paltform.
        '''
        fields = copy.copy(Profile.get_default_fields('OS'))

        if self.os_id != '':
            fields['id'] = self.os_id
        
        if self.os_displayName != '':
            fields['displayName'] = self.os_displayName
                
        if self.os_profileUrl != '':
            fields['profile_url'] = self.os_profileUrl
            
        if self.os_birthday != '':
            fields['birthday'] = self.os_birthday
        
        if self.os_gender != '':
            fields['gender'] = self.os_gender
            
        if self.os_description != '':
            fields['aboutMe'] = self.os_description
            
        if self.os_emails != '':
            fields['emails'] = self.os_emails
            
        if self.os_addresses != '':
            fields['address'] = self.os_addresses
            
        if self.os_thumbnailUrl != '':
            fields['picture'] = self.os_thumbnailUrl

        if self.os_organizations != '': 
            fields['work_history'] = self.os_organizations      
            
        return fields
        
        
class PlatformAccountManager(models.Manager):
    '''
        A platform account manager.
    '''
    
    def get_user_accounts(self, user):
        '''
            Retrieve all remote accounts of a user.
        '''
        return self.filter(user=user)
        

class PlatformAccount(models.Model):
    ''' 
        An account on a remote platform for a specific user.
            
    '''

    # the target platform
    platform = models.ForeignKey(Platform) 
    
    # the user on the local platform
    user = models.ForeignKey(settings.AUTH_PROFILE_MODULE)
    #user = models.ForeignKey(UserProfile)
    
    # the id of the user on the target platform
    remote_id = models.CharField(max_length=200, editable=False, null=True) 
    
    # is the account is active
    is_active = models.BooleanField(default=True)
    
    # content type useful to have the as_leaf_class method
    content_type = models.ForeignKey(ContentType,editable=False,null=True)
        
    # custom manager
    objects = PlatformAccountManager()


    def save(self, user=None, *args, **kwargs):
        '''
            Custom saving function to be able to use the as_leaf_class() method and check 
            if the remote account is not already synchronized.
            If a user is provided, the synchronization check will happen.
        '''

        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        
        # check that the account is not already used by another user 
        if user:
            # the accounts with the same remote_id
            accounts = PlatformAccount.objects.select_related().filter(remote_id=self.remote_id).exclude(user=user)
            # the accounts with the same remote_id and from the same platform
            accounts = filter(lambda platform_account: platform_account.as_leaf_class() == self.platform_account, accounts)
            # if there are any of those accounts raise an UsedAccountException
            if len(accounts) != 0:
                raise UsedAccountException                      
            
        super(PlatformAccount, self).save(*args, **kwargs)


    def as_leaf_class(self):
        '''
            Get the PlatformFBAccount or PlatformOSAccount instance/child of the account.
        '''
        
        content_type = self.content_type
        model = content_type.model_class()
        if(model == PlatformAccount):
            return self
        return model.objects.get(id=self.id)
    
    
    def is_token_valid(self):
        '''
            Return False is the token has expired or if the token is empty
        '''     
        
        raise NotImplementedError
    
    def update_token(self, obj):
        '''
            Update the token parameters from a com_object
        '''
        
        raise NotImplementedError
        
    def invalidate_token(self):
        '''
            Reset the current token
        '''

        raise NotImplementedError
    
    def __unicode__(self):
        return self.user.user.username +' on '+self.platform.name

            
    
class PlatformFBAccount(PlatformAccount):
    '''
        An account for a Facebook platform.
    '''
    
    # session_id and session_id_expiration for the account
    token = models.CharField(max_length=200, editable=False, null=True) 
    token_expire = models.IntegerField(max_length=50, editable=False, null=True)
    
    def is_token_valid(self):
        '''
            Return False is the token has expired or if the token is empty.
            If token_expire equals 0 we have an infinite session from extended permission (not used actually).
        '''
        
        if self.token is not None:
            return self.token_expire == 0 or self.token_expire > time.time()        
        else:
            return False
            
    def update_token(self, obj):
        '''
            Update the token parameters from a com_object.
        ''' 
        
        self.token = obj.session_key
        self.token_expire = obj.session_key_expires
        self.save() 
        
    def invalidate_token(self):
        '''
            Reset the current token.
        '''

        self.token = None
        self.token_expire = None
        self.save()
            
    
class PlatformOSAccount(PlatformAccount):
    '''
        An account for an openSocial platform.
    '''
    
    oauth_token = models.CharField(max_length=200, editable=False, null=True)
    oauth_token_secret = models.CharField(max_length=200, editable=False, null=True)
    oauth_token_expire = models.IntegerField(editable=False, null=True)
    
    def is_token_valid(self):
        '''
            Return False is the token has expired or if the token is empty.
            If oauth_token_expire equals 0 we have an infinite session
        '''

        if self.oauth_token is not None:
            return self.oauth_token_expire == 0 or self.oauth_token_expire > time.time()
        else:
            return False

    def update_token(self, obj):
        '''
            Update the token parameters from a com_object.
        '''
        
        self.oauth_token = obj.token.key
        self.oauth_token_secret = obj.token.secret
        self.oauth_token_expire = obj.token_expire
        self.save()
        
    def invalidate_token(self):
        '''
            Reset the current token.
        '''

        self.oauth_token = None
        self.oauth_token_secret = None
        self.oauth_token_expire = None
        self.save()
        
        
    
class SocialContext(object):
    '''
        Context for a connection with a remote platform

        Params:
            user: concerned user
            platform_id: the id of the remote platform          

        A context is used for a specific user, with a specific platform. The context is instanciated the first time the user communicate
        with a remote platform and is stored in his session.    

        This context is designed to be used either with a FB platform or either with an OS platform. 
    '''

    # concerned user
    user = None

    # pyfacebook or opensocial-rest-client object to communicate with the platform
    com_object = None

    # the remote platform
    current_platform = None

    # id of the platform
    platform_id = -1

    def __init__(self, user, platform_id):
        self.user = user        
        self.platform_id = platform_id
        self.reload_platform()


    @staticmethod
    def get_or_create_social_context(request, platform_id=None):
        '''
            Get the social context from the session. If there isn't one in the session, create a new one.
            The call with platform_id=None is only done after the user was redirect to the remote platform and we are sure that we put a context
            in the session before getting the user to that platform.
        '''

        def create_social_context():
            '''
                Create a social context and save it in the session.
            '''
            # create a new social context
            social_context = SocialContext(request.user.get_profile(), platform_id)
            
            # save it in the session for further request
            request.session['social_context'] = social_context
            
            return social_context


        try:
                
            # if the context exist but has a platform_id equals to None, create a new one
            # this should normally never happend 
            if request.session['social_context'].platform_id is None:
                social_context = create_social_context()
                
            # get the context from the session
            else:
                social_context = request.session['social_context']

            # reload the platform information from the db to avoid inconsistency in a object from the session
            social_context.reload_platform()
                
        except KeyError:                                
            # there is no context in the session so create one
            if platform_id is None:
                # No context + no platform id raise ans exception
                raise RuntimeError("Wrong use of the get_or_create_social_context method: no social context was found in the session and no platform id is provided.")
                
            social_context = create_social_context()

        # if platform_id is not the same as in the session, we have change the platform context so we need a new one
        if (platform_id != None and str(request.session['social_context'].current_platform.pk) != platform_id) or (social_context.user != request.user.get_profile()):
            social_context = create_social_context()            

        return social_context

    @staticmethod
    def get_platforms(request, task):
        '''
            Static method that returns the list of platforms for a task.
            
            Params:
                task: the task (people | groups | activities_push | activities_pull | notifications)
        '''

        platforms = []
        # add the platforms that support the task
        if task == 'people':
            platforms = Platform.objects.filter(support_people=True, is_active=True)

        elif task == 'groups':              
            platforms = Platform.objects.filter(support_groups=True, is_active=True)

        elif task == 'activities_push':
            platforms = Platform.objects.filter(support_activities_push=True, is_active=True)

        elif task == 'activities_pull':
            platforms = Platform.objects.filter(support_activities_pull=True, is_active=True)

        elif task == 'notifications':
            platforms = Platform.objects.filter(support_notifications=True, is_active=True)

        else:
            raise Exception('get_synch_platforms: unknown task')

        return map(lambda platform: platform.as_leaf_class(), platforms)

    @staticmethod
    def remove_subscription(request, platform_id):
        '''
            This static method can be used to remove the link between a local user and his remote account on a remote platform. 
            This method also destroy the Social Context if it's related to this platform.
            
            Params:
                platform_id: id of the remote platform
        '''
        
        PlatformAccount.objects.get(platform__id=platform_id, user=request.user.get_profile()).delete()

        # if the user has a social context with this platform we need to delete it too
        try:
            if request.session['social_context'].platform_id == platform_id:
                del request.session['social_context']                               
        except KeyError:
            pass            
            

    def reload_platform(self):
        '''
            This method retrieves the platform from the database to ensure that the platform has the last attribute values.
            The platform cannot be reloaded if the platform_id is None.
        '''
        
        if self.platform_id is not None:
            self.current_platform = get_object_or_404(Platform, pk=self.platform_id).as_leaf_class()

    def if_fb_com_object_valid(self):
        '''
            This method checks if the Facebook communication object is valid and if the session has expires.
        '''

        return self.com_object is not None and (self.com_object.session_key_expires == 0 or self.com_object.session_key_expires > time.time())


    def is_os_com_object_valid(self):
        '''
            This function checks if the OpenSocial Platform Account has a valid access token.
        ''' 

        return self.com_object is not None and (self.com_object.token_expire == 0 or self.com_object.token_expire > time.time())


    def check_synchronization(self):
        '''
            This function checks if the user has a synchronized account with the target platform.
        '''

        try:
            return PlatformAccount.objects.get(platform=self.current_platform, user=self.user).as_leaf_class()

        except PlatformAccount.DoesNotExist:
            return None


    def synch_account(self, request, callback, *args):
        '''
            Just synchronize a user with a remote account.
            
            Params:
                request: the django http request
                callback: the view to callback if an RedirectException occurs
                args: any args for the callback view
        '''

        return self._validate_context(request, callback, args)


    def get_profile(self, request, callback, *args):
        '''
            Entry point for the profile getter. It validate the social context (synchronization, com_object, token) before making the call.

            Params:
                request: the django http request
                callback: the view to callback if an RedirectException occurs
                args: any args for the callback view
        '''
        
        # check if the platform supports the call
        if not self.current_platform.support_people:
            raise NotSupportedException()
            
        # validate of the context, then call
        if self._validate_context(request, callback, args):
            return self._get_profile()
            

    def _get_profile(self):
        '''
            Private method that instanciate the correct Proxy and call the api.
        '''

        fields = self.current_platform.get_fields()
        
        if self.current_platform.__class__ == FBPlatform: 
            proxy = FBRequestProxy(self.com_object)
        else:   
            proxy = OSRequestProxy(self.com_object) 


        return self.current_platform.build_profiles(fields, proxy.get_profile(fields.values()))[0]


    def get_friends(self, request, callback, matched, *args):
        '''
            Entry point for the friends getter. It validate the social context (synchronization, com_object, token) before making the call.
            This method returns a list of Profile objects of the user's friends from the remote platform. 
            It can match them with users on the local platform and return their local platform accounts.
            
            Params:
                request: the django http request
                callback: the view to callback if an RedirectException occurs
                matched: If true, the friends will be only thoses who have synch their profile with the target platform
                args: any args for the callback view
        '''
        
        # check if the platform supports the call
        if not self.current_platform.support_people:
            raise NotSupportedException()
        
        # validate of the context, then call
        if self._validate_context(request, callback, args):
            return self._get_friends(matched)


    def _get_friends(self, matched):     
        '''
            Private method that instanciate the correct Proxy, call the api and filter the request if matched is True.
        
        '''   
        
        # Those are the matching function for friends. By default they only check the remote_id but they
        # can be improved to enable more specific matching. The only restriction is that they have to
        # return PlatformAccounts querysets.        
        def _get_matched_fb():
            return PlatformFBAccount.objects.filter(remote_id__in=proxy.get_friends(fields.values(), get_profiles=False), platform=self.current_platform)
            
        def _get_matched_os():
            return PlatformOSAccount.objects.filter(remote_id__in=proxy.get_friends(fields.values(), get_profiles=False), platform=self.current_platform)
        
        fields = self.current_platform.get_fields()
        
        if self.current_platform.__class__ == FBPlatform:                                                                          
            proxy = FBRequestProxy(self.com_object)                                                                                

            if not matched:         
                # return a list of Profiles
                return self.current_platform.build_profiles(fields, proxy.get_friends(fields.values(), get_profiles=True))                                                                                                          
            else:                     
                # return the platformaccounts of the friends
                return _get_matched_fb()

        else:                                                                                                                      
            proxy = OSRequestProxy(self.com_object)                                                                                

            if not matched:                    
                # return a list of Profiles                                                                                                    
                return self.current_platform.build_profiles(fields, proxy.get_friends(fields.values(), get_profiles=True)) 
            else:                                   
                # return the platformaccounts of the friends
                return _get_matched_os()                            



    def get_groups(self, request, callback, *args):
        '''
            Entry point for the groups getter. It validate the social context (synchronization, com_object, token) before making the call.

            Params:
                request: the django http request
                callback: the view to callback if an RedirectException occurs
                args: any args for the callback view

        '''

        # check if the platform supports the call
        if not self.current_platform.support_groups:
            raise NotSupportedException()

        # validate of the context, then call
        if self._validate_context(request, callback, args):
            return self._get_groups()


    def _get_groups(self):
        '''
            Private method that instanciate the correct Proxy and call the api. 
        '''     

        if self.current_platform.__class__ == FBPlatform:
            proxy = FBRequestProxy(self.com_object) 
        else:
            proxy = OSRequestProxy(self.com_object) 
        return proxy.get_groups()


    def publish_user_action(self, request, callback, template_id, template_data, target_ids=None, *args):
        '''
        Params:
            request: the django http request
            callback: the view to callback if an RedirectException occurs
            template_id: the platform template for this action
            template_data: the data to match in the template
            target_ids (optional): the ids for the {*target*} tag
            args: any args for the callback view
        
        '''
        
        # check if the platform supports the call
        if not self.current_platform.support_activities_push:
            raise NotSupportedException()

        # validation of the context
        if self._validate_context(request, callback, args):
            return self._publish_user_action(template_id, template_data, target_ids)


    def _publish_user_action(self, template_id, template_data, target_ids=None):
        '''
            Private method that instanciate the correct Proxy and call the api.
        '''     

        if self.current_platform.__class__ == FBPlatform:
            proxy = FBRequestProxy(self.com_object) 
        else:
            proxy = OSRequestProxy(self.com_object) 
            
        return proxy.publish_user_action(template_id, template_data, target_ids)

        
    def send_notifications(self, request, callback, user_ids, text, *args):
        '''
            Send a notification to a list of users on the remote platform.
            
            Params:
                request: the django http request
                callback: the view to callback if an RedirectException occurs
                users_ids: target for the notification
                text: text of the notification
                args: any args for the callback view
                
        '''
        
        # check if the platform supports the call       
        if not self.current_platform.support_notifications:
            raise NotSupportedException()

        # validate of the context, then call
        if self._validate_context(request, callback, args):
            return self._send_notifications(user_ids, text)     


    def _send_notifications(self, user_ids, text):
        '''
            Private method that instanciate the correct Proxy and call the api.
        '''
        
        if self.current_platform.__class__ == FBPlatform:
            proxy = FBRequestProxy(self.com_object) 
        else:
            proxy = OSRequestProxy(self.com_object) 
        return proxy.send_notifications(user_ids, text)


    # def get_activities(self, request, callback, uid='@me', target='@self', *args):
    #   '''
    #       Get activities from the platform. By default get the current user self activities.
    #       Params:
    #           request: the django http request
    #           callback: the view to callback if an RedirectException occurs
    #           args: any args for the callback view
    # 
    #   '''
    # 
    #   # check if the platform supports the call
    #   if not self.current_platform.support_activities_pull:
    #       raise NotSupportedException()
    # 
    #   # validate of the context, then call
    #   if self._validate_context(request, callback, args):
    #       return self._get_activities(uid, target)
    # 
    # 
    # def _get_activities(self, uid, target):
    #   '''
    #       Private method that instanciate the correct Proxy and call the api      
    #   '''
    # 
    #   if self.current_platform.__class__ == FBPlatform:
    #       proxy = FBRequestProxy(self.com_object) 
    #   else:
    #       proxy = OSRequestProxy(self.com_object) 
    #   return proxy.get_activities(uid, target)

    def _validate_context(self, request, callback, args):
        '''
            Private method that validate the context before a request. 

            * Checks if the user has already synchronized with the platform, otherwise raise a NotFBSyncException
            * Checks if the social context has a valid com object, otherwise tries to get a token from the DB to instantiate a com object
            * If the DB token is valid create a com object, otherwise raise a NoFBTokenException

        '''

        # it's a FBPlatform     
        if self.current_platform.__class__ == FBPlatform:
            try:
                # check if the user has already sync this platform
                platform_account = self.check_synchronization()
                if platform_account is not None:
                    
                    # if the object is not valid, get a token from the DB   
                    if not self.if_fb_com_object_valid():       
                        
                        # create com object with the valid token
                        if platform_account.is_token_valid():                   
                            self.com_object = Facebook(self.current_platform.api_key, self.current_platform.api_secret)
                            self.com_object.session_key = platform_account.token
                            self.com_object.session_key_expires = platform_account.token_expire
                            self.com_object.uid = platform_account.remote_id

                        # need a new token from the platform
                        else:
                            raise NoFBTokenException

                    # exectuted to check if the Facebook account logged on the client is a good one                 
                    if self.com_object.uid != PlatformAccount.objects.get(platform=self.current_platform, user=request.user.get_profile()).remote_id:
                        self.com_object = None
                        raise SocialConnectException("The Facebook logged profile is not your profile. Please log out of Facebook.")

                    # the com_object is valid   
                    return True

                else:
                    # the user is not synchronized with the remote platform
                    raise NotFBSyncException

            except (NotFBSyncException, NoFBTokenException):
                # store callback and args in the session and raise a redirect exception to redirect the user to the remote platform     
                request.session['callback_view'] = callback
                request.session['callback_args'] = args
                raise RedirectFBException               
        
        # it's an OSPlatform
        elif self.current_platform.__class__ == OSPlatform:
            try:            
                # check if the user has already sync this platform
                platform_account = self.check_synchronization()         
                if platform_account is not None:

                    # if the object is not valid, get a token from the DB   
                    if not self.is_os_com_object_valid():

                        # create com object with the valid access token
                        if platform_account.is_token_valid():
                            self.com_object = OpenSocial(self.current_platform.oauth_consumer_key, self.current_platform.oauth_consumer_secret, self.current_platform.oauth_signature_method, self.current_platform.api_url, platform_account.oauth_token, platform_account.oauth_token_secret, platform_account.oauth_token_expire)
                            #platform_account.update_token(self.com_object)

                        # need a new token from the platform
                        else:
                            raise NoOSTokenException

                    # exectuted only if we got a valid token either form the com object or from the db  
                    return True

                else:
                    # the user is not synchronized with the remote platform
                    raise NotOSSyncException

            except (NotOSSyncException, NoOSTokenException): 
                # store callback and args in the session and raise a redirect exception to redirect the user to the remote platform     
                request.session['callback_view'] = callback
                request.session['callback_args'] = args
                raise RedirectOSException   
        else:
            raise Exception('_validate_context: the type of the platform is not Facebook or OpenSocial!!')  



    def __unicode__(self):
        return u"SocialContext for"+self.user.username+" on "+ self.current_platform.name
