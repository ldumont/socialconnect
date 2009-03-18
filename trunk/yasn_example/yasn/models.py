import datetime

from django.db import models
from django.db.models import permalink

from accounts.models import UserProfile


class RelationManager(models.Manager):
    '''
        Custom manager for a relation.
    '''

    # check if user_a has a relation to user_b
    def connection_exists(self, user_a, user_b):
        relations = Relation.objects.filter(user=user_a, target=user_b)
        if relations.count()==1:
            return True
        return False

    # connect user_a with user_b
    def connect(self, user_a, user_b):
        relation = Relation()
        relation.user = user_a
        relation.target = user_b
        relation.save()
    
    # disconnect user_a from user_b
    def disconnect(self, user_a, user_b):
        Relation.objects.filter(user=user_a, target=user_b).delete()
    
    # list relations of a user  
    def relations_list(self, user):
        return map(lambda rel: rel.target, user.relation_set.all())
    

class Relation(models.Model):
    '''
        Relation between two users.
    '''
    
    # the source user
    user = models.ForeignKey(UserProfile)   
    
    # the target user
    target = models.ForeignKey(UserProfile, related_name='Targeted user')
        
    # a custom manager
    objects = RelationManager()

    def __unicode__(self):
        return '%(user_b)s is %(user_a)s\'s contact' % {'user_b':self.target.user.first_name +' '+ self.target.user.last_name, 'user_a':self.user.user.first_name +' '+ self.user.user.last_name}
        
        
class Story(models.Model):
    '''
        A story posted by a user.
    '''
    
    # author of the story
    author = models.ForeignKey(UserProfile)
    
    # title of the story
    title = models.CharField(blank=False, null=False, max_length=200)
    
    # body of the story
    body = models.TextField(blank=False, null=False)
    
    # date of writing of the story
    date = models.DateTimeField(default=datetime.datetime.now)
    
    # get the absolute url of the story     
    def get_absolute_url(self):
        return ('view_story', [str(self.id)])
        
    get_absolute_url = permalink(get_absolute_url)      
    
    def __unicode__(self):
        return self.title
        

class StoryComment(models.Model):
    '''
        A comment on a story.
    '''
    # author of the comment
    author = models.ForeignKey(UserProfile)
    
    # story of the comment
    story = models.ForeignKey(Story)
    
    # body of the comment
    body = models.TextField(blank=False, null=False)
    
    # date of writing of the comment
    date = models.DateTimeField(default=datetime.datetime.now)
    
    def __unicode__(self):
        return 'On '+self.story.title+' by '+self.author.user.username
    
    



    