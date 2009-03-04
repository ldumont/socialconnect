from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    SEX_CHOICE = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('X', ''),      
    )
    
    user = models.ForeignKey(User, editable=False)
    birthday = models.DateField(blank=True, null=True)
    description = models.CharField(max_length=250, blank=True, null=True, default='')
    picture = models.ImageField(upload_to="images/photos", blank=True, null=True)
    sex = models.CharField(max_length=1, default='X', choices=SEX_CHOICE)
    

    def __unicode__(self):
        return self.user.username


