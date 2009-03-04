import re

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from facebook import FacebookError
from opensocial import OpenSocialError
from socialconnect.utils.exceptions import *

from socialconnect.models import Platform, PlatformAccount

def exception_handler(function):
    
    def reset_session(platform_id, request):
        ''' 
            Utility function that reset the session with a remote platform 
        '''
        
        try:
            PlatformAccount.objects.get(platform=platform_id, user=request.user).as_leaf_class().invalidate_token()
        except PlatformAccount.DoesNotExist:
            pass
        
        try:    
            del request.session['social_context']
        except KeyError:
            pass
    
    
    def handle(request,*args,**kwargs):
        platform_id = kwargs.get('platform_id', None)

        try:
            return function(request,*args,**kwargs)
            
        except RedirectFBException:
            '''
                This Exception is raised if we need to go to Facebook to login the user, authorized the app or get new session.
            '''
            return HttpResponseRedirect(Platform.objects.get(id=platform_id).as_leaf_class().get_login_url())

        except RedirectOSException:
            '''
                This Exception is raised if we need to go to OpenSocial to login the user or authorized the OAuth token.
            '''
            return HttpResponseRedirect(reverse('oauth_request_token'))

        except FacebookError, ex:
            '''
                This Exception is raised if the proxy_layer get an error from the platform or with the data sent by the platform.
                The social_context is destroyed and the session is invalidated to try again.

            '''

            print ex        
            
            # token or session error
            if ex.code in [101, 102]:
                reset_session(platform_id, request)
                return HttpResponseRedirect(request.path)

            # It's another exception    
            raise               
                    
        except OpenSocialError, ex:
            
            print ex
            
            if ex.code == 100:
                reset_session(platform_id, request)
                return HttpResponseRedirect(request.path)
                
            raise
            
        except SocialConnectException, ex:
            ''' 
                This exception could be raised in some very rare case where multiple users use the same computer
                to synchronize their accounts. 
                It should be adapted to the platform needs.
            '''
            return HttpResponse(ex.message)
                        
        #except Exception, ex:
        #   PlatformAccount.objects.get(platform=platform_id, user=social_context.user).as_leaf_class().invalidate_token()
        #   del request.session['social_context']
        #   return direct_to_template(request, 'yasn/error.html', {'error': ex})
        
    return handle