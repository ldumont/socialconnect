from yasn.models import Relation, Story, StoryComment
from django.contrib import admin

class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')
admin.site.register(Story, StoryAdmin)
    
class StoryCommentAdmin(admin.ModelAdmin):
    list_display = ('story', 'author')
admin.site.register(StoryComment, StoryCommentAdmin)    
    
admin.site.register(Relation)
