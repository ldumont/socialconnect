from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/(.*)', admin.site.root),
)

urlpatterns = patterns('yasn.views',

    url(r'^$', 'home', name='home'),    
    
    # Accounts urls
    url(r'^signup/$', 'signup', name="signup"), 
    url(r'^login/$', 'login_view', name='login_view'),
    url(r'^logout/$', 'logout_view', name="logout_view"),
    url(r'^recoverpassword/$', 'recover_password', name="recover_password"),
    url(r'^changepassword/$', 'change_password', name="change_password"),
    
    url(r'^ajax_subscription_remove$', 'ajax_subscription_remove', name='ajax_subscription_remove'),
    
    # Profile urls
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^profile/(?P<user_id>\d+)/$', 'profile', name='profile_view'),
    url(r'^profile/edit/$', 'edit_profile', name="edit_profile"),
    url(r'^profile/edit/(?P<platform_id>\d+)/$', 'edit_profile', name="edit_profile_from_remote"),

    # Friends urls
    url(r'^friends/$', 'friends', name='friends'),
    url(r'^friends/matched/(?P<platform_id>\d+)/$', 'get_matched_friends', name='get_matched_friends'), 
    url(r'^friends/add/$', 'add_friends', name='add_friends'),
    url(r'^ajax_friend_remove$', 'ajax_friend_remove', name='ajax_friend_remove'),
    url(r'^friends/invite/(?P<platform_id>\d+)/$', 'invite_friends', name='invite_friends'),
    url(r'^friends/invite/(?P<platform_id>\d+)/send$', 'send_invite_friends', name='send_invite_friends'),
    
    # Stories urls
    url(r'^stories/$', 'view_stories', name='view_stories'),
    url(r'^stories/add/$', 'add_story', name='add_story'),
    url(r'^stories/view/(?P<story_id>\d+)/$', 'view_story', name='view_story'),
    url(r'^stories/remotestory/(?P<story_id>\d+)/(?P<platform_id>\d+)$', 'remote_story', name='remote_story'),
    url(r'^stories/remotecomment/(?P<story_id>\d+)/(?P<platform_id>\d+)$', 'remote_comment', name='remote_comment'),

    
    
    # Proof of Concept
    url(r'^poc/$', 'proof_of_concept', name='proof_of_concept'),
    url(r'^poc/synch/(?P<platform_id>\d+)/$', 'synch_account', name='synch_account'),
    url(r'^poc/friends/(?P<platform_id>\d+)/$', 'get_friends_and_profile', name='get_friends_and_profile'),
    url(r'^poc/profile/(?P<platform_id>\d+)/$', 'get_profile', name='get_profile'),
    url(r'^poc/groups/(?P<platform_id>\d+)/$', 'get_groups', name='get_groups'),

)

