from django.conf.urls.defaults import *


urlpatterns = patterns('socialconnect.views',
    url(r'^fbafterlogin/$', 'fb_after_login', name='fb_after_login'),
    url(r'^oauthrequest/$', 'oauth_request_token', name='oauth_request_token'),
    url(r'^oauthexchange/$', 'oauth_exchange_token', name='oauth_exchange_token'),  
    #url(r'^fbafterperm/$', 'fb_after_permission', name='fb_after_permission'),
)
