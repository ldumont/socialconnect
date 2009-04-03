from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm


from accounts.models import UserProfile
from yasn.models import Story, StoryComment

class UserForm(ModelForm):
    '''
        A form for a user.
    '''
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
        
        
class UserProfileForm(ModelForm):
    '''
        A form for a user profile.
    '''
    class Meta:
        model = UserProfile
        fields = ('description', 'picture', 'sex', 'birthday')
        
        
class UserField(forms.CharField):
    '''
        A field for a username with a unicity validation.
    '''
    def clean(self, value):
        super(UserField, self).clean(value)
        try:
            User.objects.get(username=value)
            raise forms.ValidationError("Someone is already using this username. Please pick an other.")
        except User.DoesNotExist:
            return value


class SignupForm(forms.Form):
    '''
        The signup form.
    '''
    username = UserField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput(), label="Repeat your password")
    email = forms.EmailField()


    def clean_password(self):
        if self.data['password'] != self.data['password2']:
            raise forms.ValidationError('Passwords are not the same')
        return self.data['password']

    def clean(self,*args, **kwargs):
        self.clean_password()
        return super(SignupForm, self).clean(*args, **kwargs)


class RecoverEmailField(forms.EmailField):
    '''
        A field for an email that check if an account exists with such an email (for password recovery)
    '''
    def clean(self, value):
        super(RecoverEmailField, self).clean(value)
        
        try:
            User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise forms.ValidationError('No user with such an email address')
            

class RecoverPasswordForm(forms.Form):
    '''
        The recover password form.
    ''' 
    email = RecoverEmailField() 
       
    def clean(self, *args, **kwargs):
            return super(RecoverPasswordForm, self).clean(*args, **kwargs)

class StoryForm(ModelForm):
    '''
        The form to add a story.
    '''
    class Meta:
        model = Story
        fields = ('title', 'body')
                
class StoryCommentForm(ModelForm):
    '''
        The form to add a comment to a story.
    '''
    class Meta: 
        model = StoryComment
        fields = ('body',)
