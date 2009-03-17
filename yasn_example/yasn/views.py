from datetime import datetime
from random import *
import re
import time
import string
from urllib import urlretrieve

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template

from accounts.models import UserProfile
from socialconnect.models import SocialContext, PlatformAccount, Platform
from socialconnect.utils.decorators import exception_handler

from yasn.models import Relation, Story, StoryComment
from yasn.forms import UserForm, UserProfileForm, SignupForm, RecoverPasswordForm, StoryForm, StoryCommentForm


@login_required
def home(request):
    '''
        Home view.
    '''
    
    name = request.user.first_name+' '+request.user.last_name
    if name == ' ':
        name = request.user.username
            
    return direct_to_template(request, 'yasn/home.html', {'name': name})


def login_view(request):
    '''
        Login view that also do the user login.
    '''
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:              
                login(request, user)
                return HttpResponseRedirect(reverse('home'))
            else:
                # return a 'disabled account' error message
                return direct_to_template(request, 'yasn/message.html', {'message': 'Account is disabled.', 'back': reverse('home')})
        else:
            # return an 'invalid login' error message.
            return direct_to_template(request, 'yasn/message.html', {'message': 'Invalid username or password.', 'back': reverse('login_view')})
        
    return direct_to_template(request, 'yasn/login.html')
        
        
def logout_view(request):
    '''
        Logout the user.
    '''
    
    logout(request)
    return HttpResponseRedirect(reverse('home'))    


def signup(request):
    '''
        Signup view that also do the signup.
    '''
    
    if not request.user.is_authenticated():
        
        if request.method == 'POST':        
            signup_form = SignupForm(request.POST)
        
            if(signup_form.is_valid()):         
                # create the user   
                u = User.objects.create_user(signup_form.cleaned_data['username'], signup_form.cleaned_data['email'], signup_form.cleaned_data['password'])     
                p = UserProfile(user=u)
                p.save()
            
                login(request, authenticate(username=signup_form.cleaned_data['username'], password=signup_form.cleaned_data['password']))
            
                return HttpResponseRedirect(reverse('home'))
                        
        else:
            signup_form = SignupForm()      
    else:
        return HttpResponseRedirect(reverse('home'))
        
    return direct_to_template(request, 'yasn/signup.html', {'signup_form': signup_form})


def recover_password(request):
    '''
        View to recover a user password.
    '''
    
    if not request.user.is_authenticated():
        if request.method == 'POST':
            recover_form = RecoverPasswordForm(request.POST)
            
            if recover_form.is_valid():
                user = User.objects.get(email=recover_form.cleaned_data['email'])
                
                # generate a random password only numerical but could be improved to add letters    
                chars = string.ascii_letters + string.digits

                new_password = "".join(choice(chars) for x in range(6))            
                
                # send the new password by email and then save the new password
                email = EmailMessage('YASN: New password', 'Here is your new password for YASN: '+new_password, settings.EMAIL_SENDER, [user.email])
                email.send()
                user.set_password(new_password)
                user.save()
                
                return direct_to_template(request, 'yasn/message.html', {'message': 'Email sent!', 'back': reverse('home')})
            
        else:       
            recover_form = RecoverPasswordForm()                
    else:
        return HttpResponseRedirect(reverse('home'))

    return direct_to_template(request, 'yasn/recover_password.html', {'recover_form': recover_form})

@login_required
def change_password(request):
    '''
        View to change a user password.
    '''
    
    if request.method == 'POST':
        change_pass_form = PasswordChangeForm(request.user, request.POST)
        
        if change_pass_form.is_valid():
            request.user.set_password(change_pass_form.cleaned_data['new_password1'])
            request.user.save()
            return direct_to_template(request, 'yasn/message.html', {'message': 'Password changed!', 'back': reverse('profile')})
            
    else:
        change_pass_form = PasswordChangeForm(request.user)
        
    return direct_to_template(request, 'yasn/change_password.html', {'change_pass_form': change_pass_form})


@login_required
def profile(request, user_id=None):
    '''
        Show a user profile. Either the current user profile or any other user.
    '''

    # get the current user profile
    if user_id is None or user_id == str(request.user.id):
        profile = get_object_or_404(UserProfile.objects.select_related(), user=request.user)
        subscriptions = PlatformAccount.objects.get_user_accounts(profile)
        mode = 'self'
        
    # get another user profile
    else: 
        profile = get_object_or_404(UserProfile.objects.select_related(), user__id=user_id)
        subscriptions = {}
        mode = 'other'          

    return direct_to_template(request, 'yasn/profile_view.html', {'mode': mode, 'profile': profile, 'subscriptions': subscriptions, 'subscriptions_size': len(subscriptions) })
    
    
@login_required
@exception_handler
def edit_profile(request, platform_id=None):
    '''
        Show a form to edit a profil and save it.
    '''

    if request.method == 'POST':
        # verifiy fields and save the profile from the form 
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=UserProfile.objects.get(user=request.user))
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            new_profile = profile_form.save(commit=False)           

            # if we have a picture for a remote platform we download it and save it
            if 'remote-pic-cb' in request.POST:
                image_url = request.POST['remote-pic-url']
                image_name = str(request.user.username)+'.'+image_url.split(".")[-1]
                                
                urlretrieve(image_url, settings.MEDIA_ROOT+'images/photos/'+image_name)
                new_profile.picture = 'images/photos/'+image_name
            
            new_profile.save()
                                    
        return HttpResponseRedirect(reverse('profile'))
    
    elif platform_id is not None:
        # get the data from a remote platform
        social_context = SocialContext.get_or_create_social_context(request, platform_id)       
        profile = social_context.get_profile(request, 'edit_profile_from_remote', platform_id)  
                
        # fill the form with the remote data
        user_form = UserForm({'first_name': profile.givenName, 'last_name': profile.familyName})
        profile_form = UserProfileForm({'description': profile.aboutMe, 'sex': profile.gender, 'birthday': profile.birthday})           
        picture_preview =  profile.photo
        remote = True       
            
    else:   
        # fill the form with values from db
        user_profile = UserProfile.objects.get(user=request.user)
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
        picture_preview = user_profile.picture
        remote = False

    supported_platforms = SocialContext.get_platforms(request, 'people')
    
    return direct_to_template(request, 'yasn/profile_edit.html', {'user_form': user_form, 'profile_form': profile_form, 'platforms': supported_platforms, 'picture_preview': picture_preview or None, 'remote': remote})


@login_required
def friends(request):
    '''
        Show local friends of the user.
    '''
    
    # local friends of the user
    friends = Relation.objects.relations_list(user=request.user.get_profile())
    
    # remote platform to get friends
    platforms_get = SocialContext.get_platforms(request, 'people')
    
    # remote platform to invite friends
    platforms_notifications = SocialContext.get_platforms(request, 'notifications')
    
    return direct_to_template(request, 'yasn/friends_list.html', {'friends': friends, 'friends_size': len(friends), 'platforms_get': platforms_get, 'platforms_notifications': platforms_notifications})
    
    
@login_required
def add_friends(request):
    '''
        View that add friends to the current user.
    '''
    
    if request.method == 'POST':
        reg = re.compile('^users-.*$')
        for item in request.POST:
            if reg.match(item):
                # create and save the relation
                r = Relation(user=request.user.get_profile(), target=UserProfile.objects.get(user__username=item.split('-', 1)[1]))
                r.save()
                
    return HttpResponseRedirect(reverse('friends')) 
    
    
@login_required
@exception_handler
def get_matched_friends(request, platform_id):  
    '''
        Get the remote friends of a user that match users on the local platform
    '''
    
    # get the social context
    social_context = SocialContext.get_or_create_social_context(request, platform_id)

    # retrieve matched friends          
    friends_accounts = social_context.get_friends(request, 'get_matched_friends', True, platform_id)

    users = []
    rel = Relation.objects.select_related(depth=1).filter(user=request.user.get_profile())
    
    for account in friends_accounts:                        
        if list(rel.filter(target=account.user)) == []:
            users.append({'username': account.user.user.username, 'givenName': account.user.user.first_name, 'familyName': account.user.user.last_name, 'photo': account.user.picture})
            
    return direct_to_template(request, 'yasn/friends.html', {'friends': users, 'platform': social_context.current_platform.name})           
    
    
@login_required
def ajax_friend_remove(request):
    '''
        Ajax view to remove a relation.
    '''
    if request.is_ajax():
        if request.method == 'POST':
            if 'username' in request.POST:
                # the target user
                u = UserProfile.objects.get(user__username=request.POST['username'])
    
                # disconnect the users
                Relation.objects.disconnect(request.user.get_profile(), u)
    
                return HttpResponse('ok')
                
            return HttpResponse('Error: No username provided') 
            
        return HttpResponse('Error: Method was not POST')           
        
    return HttpResponseRedirect(reverse('home'))
    
    
@login_required
def ajax_subscription_remove(request):
    '''
        Ajax view to remove a plaftorm account
    '''
    if request.is_ajax():
        if request.method == 'POST':
            if 'platform_id' in request.POST:           
            
                # remove the subscription
                SocialContext.remove_subscription(request, request.POST['platform_id'])
            
                return HttpResponse('ok')
            
            return HttpResponse('Error: No platform id provided')
        
        return HttpResponse('Error: Method was not POST')
        
    return HttpResponseRedirect(reverse('home'))



@login_required
def add_story(request):
    '''
        Show a form to add a story.
    '''
    
    if request.method == 'POST':
        story_form = StoryForm(request.POST)
        
        if story_form.is_valid():
            
            # create and save the story 
            story = Story(author=request.user.get_profile(), body=story_form.cleaned_data['body'], title=story_form.cleaned_data['title'])
            story.save()

            # go to a view to notify on a remote platform
            if 'notify' in request.POST:
                return HttpResponseRedirect(reverse('remote_story', args=[story.id, request.POST['notify']]))
            else:
                return HttpResponseRedirect(reverse('view_story', args=[story.id]))         
                
    else:
        story_form = StoryForm()
    
        # remote platforms that support activities notification where the user has an account 
        platforms = Platform.objects.get_task_user(request.user.get_profile(), 'activities_push')
        return direct_to_template(request, 'yasn/story_add.html', {'story_form': story_form, 'platforms': platforms})
    
    
@login_required
@exception_handler
def remote_story(request, story_id, platform_id):
    '''
        View that send a notification of a story to a remote platform.
    '''
    
    # get the social context
    social_context = SocialContext.get_or_create_social_context(request, platform_id)
    
    # template data
    template_id = settings.TEMPLATE_STORY_ID
    domain = Site.objects.get_current().domain
    template_data = {'story_link':'http://'+domain+''+Story.objects.get(id=story_id).get_absolute_url(), 'link':'<a href="http://'+domain+'">YASN</a>'}
    
    # notify the remote platform
    args = (story_id, platform_id)
    
    response = social_context.publish_user_action(request, 'remote_story', template_id, template_data, None, *args)
    
    # an error occurs when notifying the story
    if response == 0:
        return direct_to_template(request, 'yasn/message.html', {'message': 'Notification failed!', 'back': reverse('view_story', args=[story_id])})
        
    return HttpResponseRedirect(reverse('view_story', args=[story_id])) 
        
        
@login_required
def view_stories(request):
    '''
        View to see all the storis.
    '''
    
    stories = Story.objects.all()
    return direct_to_template(request, 'yasn/stories_view.html', {'stories': stories})


@login_required
def view_story(request, story_id):
    '''
        View to display a story with its comments and a form to add comments
    '''
    
    # add a comment
    if request.method == 'POST':
        comment_form = StoryCommentForm(request.POST)
        
        if comment_form.is_valid():
            
            # create and save the comment
            comment = StoryComment(author=request.user.get_profile(), body=comment_form.cleaned_data['body'], story=Story.objects.get(id=story_id))     
            comment.save()
            
            # go to a view to notify on a remote platform
            if 'notify' in request.POST:
                return HttpResponseRedirect(reverse('remote_comment', args=[story_id, request.POST['notify']]))
            else:           
                return HttpResponseRedirect(reverse('view_story', args=[story_id]))
    else:
        comment_form = StoryCommentForm()
                
        # get the story
        story = get_object_or_404(Story, id=story_id)
        
        # story comments
        comments = list(StoryComment.objects.filter(story=story))       
    
        # remote platforms that support activities notification where the user has an account 
        platforms = Platform.objects.get_task_user(request.user.get_profile(), 'activities_push')           
            
        return direct_to_template(request, 'yasn/story_view.html', {'story': story, 'comments': comments, 'comment_form': comment_form, 'platforms': platforms})


@login_required
@exception_handler
def remote_comment(request, story_id, platform_id):
    '''
        View that send a notification of a comment on a story to a remote platform.
    '''
    
    # get the social context
    social_context = SocialContext.get_or_create_social_context(request, platform_id)
    
    # author of the story
    author = Story.objects.select_related().get(id=story_id).author
    
    # try to see if the author has an account on the remote platform
    try:
        author_account = PlatformAccount.objects.select_related().get(user=author, platform__id=platform_id)
    except PlatformAccount.DoesNotExist:
        author_account = None
        
    # template data
    domain = Site.objects.get_current().domain
    template_data = {'story_link':'http://'+domain+''+Story.objects.get(id=story_id).get_absolute_url(), 'link':'<a href="http://'+domain+'">YASN</a>'}
    target_ids = None

    # if the user has no account on the remote platform, send the author as a string 
    if not author_account:
        template_id = settings.TEMPLATE_COMMENT_AUTHOR_ID
                    
        if author.user.first_name or author.user.last_name == '':
            template_data['author'] = author.user.username
        else:
            template_data['author'] = author.user.first_name +' '+author.user.last_name
        
    # if the user has an account and is the author of the story                         
    elif author == request.user.get_profile():
        template_id = settings.TEMPLATE_COMMENT_AUTHOR_ID
        template_data['author'] = 'himself'
            
    # if the author has an account on the selected platform, link him on the notification               
    else:
        template_id = settings.TEMPLATE_COMMENT_TARGET_ID
        target_ids = author_account.remote_id
                        
    # notify the remote platform
    args = (story_id, platform_id)

    response = social_context.publish_user_action(request, 'remote_comment', template_id, template_data, target_ids, *args)

    # an error occurs when notifying the story
    if response == 0:
        return direct_to_template(request, 'yasn/message.html', {'message': 'Notification failed!', 'back': reverse('view_story', args=[story_id])})

        
    return HttpResponseRedirect(reverse('view_story', args=[story_id]))
    
    
@login_required 
@exception_handler
def invite_friends(request, platform_id):
    '''
        View to display the remote friend of the user and send them invitations.
    '''
    
    # get the social context
    social_context = SocialContext.get_or_create_social_context(request, platform_id)
        
    # friends of the user from the remote platform 
    remote_friends = social_context.get_friends(request, 'invite_friends', False, platform_id)
    
    # remote_ids (converted to int) of all user on YASN that synch their account with the remote platform
    platform_accounts_ids = [int(x) for x in PlatformAccount.objects.filter(platform__id=1).values_list('remote_id', flat=True)]
    
    # filter to remove the friends form the remote platform that have already synch their account with YASN 
    remote_friends = filter(lambda user: not user.id in platform_accounts_ids, remote_friends)
    
    return direct_to_template(request, 'yasn/friends.html', {'friends': remote_friends, 'platform': social_context.current_platform, 'invite': True})


@login_required
@exception_handler
def send_invite_friends(request, platform_id):
    '''
        View that send the invitations.
    '''
    
    if request.method == 'POST':
        
        # get the target ids
        ids = []
        reg = re.compile('^users-.*$')
        for item in request.POST:
            if reg.match(item):
                ids.append(item.split('-', 1)[1])
            
            # get the social context    
            social_context = SocialContext.get_or_create_social_context(request, platform_id)
            
            # text of the invitation
            text = 'ask you to join him on <a href="'+Site.objects.get_current().domain+'">YASN<a/> to experience a new social network! <a href="'+Site.objects.get_current().domain+''+reverse('signup')+'">Join now!</a>'
            
            # send the invitations
            response = social_context.send_notifications(request, 'send_invite_friends', ids, text, platform_id)
        return direct_to_template(request, 'yasn/message.html', {'message': 'Invitations sent!', 'back': reverse('friends')})
            
    return HttpResponseRedirect(reverse('home'))
    
    
    
    
#### Proof of concepts views ####

@login_required
def proof_of_concept(request):
    '''
        Home of proof of concept.
    '''
    
    # get the platform for each task
    people_supported_platforms = SocialContext.get_platforms(request, 'people')
    groups_supported_platforms = SocialContext.get_platforms(request, 'groups')
    activities_pull_supported_platforms = SocialContext.get_platforms(request, 'activities_pull')
    
    return direct_to_template(request, 'yasn/poc/home.html', {'people_supported_platforms': people_supported_platforms, 'groups_supported_platforms': groups_supported_platforms, 'activities_pull_supported_platforms': activities_pull_supported_platforms})


@login_required
@exception_handler
def synch_account(request, platform_id):
    '''
        View to simply sync an account with a remote platform.
    '''
    
    # get the social context
    social_context = SocialContext.get_or_create_social_context(request, platform_id)
    
    # synch the account
    social_context.synch_account(request, 'synch_account', platform_id)
    
    return direct_to_template(request, 'yasn/message.html', {'message': 'Synchronization done!', 'back': reverse('proof_of_concept')})

    
@login_required
@exception_handler
def get_profile(request, platform_id):
    '''
        View that get the user profile and display it without formatting.
    '''
    
    # get the social context
    social_context = SocialContext.get_or_create_social_context(request, platform_id)
    
    # get the profile from the remote platform
    profile_infos = social_context.get_profile(request, 'get_profile', platform_id)

    # get the remote platform
    platform = Platform.objects.get(id=platform_id)
    
    return direct_to_template(request, 'yasn/poc/profile.html', {'profile': profile_infos, 'platform_name': platform.name})
        

@login_required
@exception_handler
def get_friends_and_profile(request, platform_id):      
    '''
        View that get the user's friends and their profiles from the remote platform.
    '''
    
    # get the social context
    social_context = SocialContext.get_or_create_social_context(request, platform_id)
    
    # get the friends from the remote platform
    friends_infos = social_context.get_friends(request, 'get_friends_and_profile', False, platform_id)

    return direct_to_template(request, 'yasn/poc/friends.html', {'friends': friends_infos, 'platform': social_context.current_platform.name})   
            

@login_required
@exception_handler
def get_groups(request, platform_id):   
    '''
        View that get the groups of the user on the remote platform.
    '''
    
    # get the social context
    social_context = SocialContext.get_or_create_social_context(request, platform_id)
    
    # get the platform
    platform = Platform.objects.get(id=platform_id)
        
    # get the groups
    groups_infos = social_context.get_groups(request, 'get_groups', platform_id)
    
    return direct_to_template(request, 'yasn/poc/groups.html', {'my': groups_infos, 'platform_name': platform.name})
        


    
    




    
