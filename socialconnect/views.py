import time

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse

from facebook import Facebook
from oauth import oauth
from opensocial import OpenSocial
from restclient import GET

from socialconnect.models import PlatformAccount, PlatformOSAccount, PlatformFBAccount
from socialconnect.models import SocialContext
from socialconnect.utils.decorators import exception_handler
from socialconnect.utils.exceptions import *


@login_required
@exception_handler
def fb_after_login(request):
    '''
        Facebook callback. The user is redirected here from the Facebook login page.
    '''

    # get the social context
    social_context = SocialContext.get_or_create_social_context(request)
    
    # get the Facebook platform
    fb_platform = social_context.current_platform.as_leaf_class()
    
    # create a com object
    com_object = Facebook(fb_platform.api_key, fb_platform.api_secret, request.GET['auth_token'])
    
    # get a session
    com_object.auth.getSession()

    # create a platform account if necessary
    try:
        platform_account = PlatformAccount.objects.get(user=request.user.get_profile(), platform=social_context.current_platform).as_leaf_class()
        
        # check if the token is for the actual user (the FB tokens have the following format : xxxxxxxxxxxx-123456789 where 123456789 is the FB user id)
        if com_object.session_key.split('-')[-1] != platform_account.remote_id:
            raise SocialConnectException('Please log out of Facebook')

    except PlatformAccount.DoesNotExist:
        # create a new account
        platform_account = PlatformFBAccount(platform=social_context.current_platform, user=request.user.get_profile(), remote_id=com_object.uid, is_active=True)
        try:
            platform_account.save(request.user.get_profile())
        except UsedAccountException:
            raise SocialConnectException(social_context.current_platform.name+' account already linked to an other user.')
    
    # update the db
    platform_account.update_token(com_object)

    # update social context 
    social_context.com_object = com_object
    
    # chech if the user has granted offline access
    #extended_perm = 'offline_access'           
    #if com_object.users.hasAppPermission(extended_perm):
    
    # return to the callback view
    return HttpResponseRedirect(reverse(request.session['callback_view'], args=request.session['callback_args']))

    #else:
    #   return HttpResponseRedirect('http://www.new.facebook.com/authorize.php?api_key='+ fb_platform.api_key +'&v=1.0&ext_perm='+ extended_perm +'&next=http://apps.electronlibre.com/socialconnect/fbafterperm')


# @login_required       
# @exception_handler    
# def fb_after_permission(request):
#   
#   # get the social context
#   social_context = SocialContext.get_or_create_social_context(request)
#   com_object = Facebook(social_context.current_platform.as_leaf_class().api_key, social_context.current_platform.as_leaf_class().api_secret)
#   com_object.auth.createToken()
#   com_object.auth.getSession()
#   
#   # update the db
#   platform_account.update_token(com_object)
#   
#   return HttpResponseRedirect(reverse(request.session['callback_view'], args=request.session['callback_args']))


@login_required
@exception_handler  
def oauth_request_token(request):
    '''
        This view starts the oauth process from the beginning and finish just before redirecting the user to the 
        platform's authorisation page.
    '''

    # get the social context and the current_platform
    social_context = SocialContext.get_or_create_social_context(request)
    current_platform = social_context.current_platform

    token = OpenSocial.get_request_token(current_platform.oauth_consumer_key, current_platform.oauth_consumer_secret, eval('oauth.'+current_platform.oauth_signature_method)(), current_platform.oauth_request_token_url)
    
    # save token in the session
    request.session[current_platform.name+'-token'] = token
    
    # send the user to the platform's page to authorize the request token
    oauth_request = oauth.OAuthRequest.from_token_and_callback(token=token, callback='http://'+Site.objects.get_current().domain+''+reverse('oauth_exchange_token'), http_url=current_platform.oauth_authorization_url)     
    return HttpResponseRedirect(oauth_request.to_url()) 



@login_required     
@exception_handler      
def oauth_exchange_token(request):
    '''
        This view is the OpenSocial callback.
        It exchanges an authorized request token with an access token usable to query the platform.
    '''

    # get the social context, the current_platform and the platform_account
    social_context = SocialContext.get_or_create_social_context(request)
    current_platform = social_context.current_platform

    # initialize necessary parameters for oauth 
    token = request.session[current_platform.name+'-token']
    consumer = oauth.OAuthConsumer(current_platform.oauth_consumer_key, current_platform.oauth_consumer_secret)
    oauth_signature_method = eval('oauth.'+current_platform.oauth_signature_method)()
    
    # get access token
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_url=current_platform.oauth_access_token_url)
    oauth_request.sign_request(oauth_signature_method, consumer, token) 
    
    #response = GET(current_platform.oauth_access_token_url, headers=oauth_request.to_header()) 
    response = GET(oauth_request.to_url())  # using the header doesn't seems to work on partuza

    # access token
    token = oauth.OAuthToken.from_string(response)
    
    # token validity
    token_expire = current_platform.oauth_token_validity + int(time.time())

    # update social context
    com_object = OpenSocial(current_platform.oauth_consumer_key, current_platform.oauth_consumer_secret, current_platform.oauth_signature_method, current_platform.api_url, token.key, token.secret, token_expire)

    # get the user id
    remote_id = com_object.get_uid()
    
    # create a platform account if necessary
    try:    
        platform_account = PlatformAccount.objects.get(user=request.user.get_profile(), platform=social_context.current_platform).as_leaf_class()
        
        # update the db
        platform_account.update_token(com_object)

    except PlatformAccount.DoesNotExist:
        # create a new account       
        platform_account = PlatformOSAccount(platform=social_context.current_platform, user=request.user.get_profile(), remote_id=remote_id, is_active=True, oauth_token=token.key, oauth_token_secret=token.secret, oauth_token_expire=token_expire)
        try:
            platform_account.save(request.user.get_profile())
        except UsedAccountException:
            raise SocialConnectException(social_context.current_platform.name+' account already linked to an other user.')
        
        
    # update social context 
    social_context.com_object = com_object
    
    # clean the session
    del request.session[current_platform.name+'-token']
    
    # return to the callback view
    return HttpResponseRedirect(reverse(request.session['callback_view'], args=request.session['callback_args']))   
        

