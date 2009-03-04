from socialconnect.models import FBPlatform, OSPlatform
from django.contrib import admin

# Add the platform management to the Django admin
class FBPlatformAdmin(admin.ModelAdmin):
    fieldsets = ( 
        (None, {'fields': ('name', 'api_url', 'logo', 'is_active', 'api_version')}),    
        ('Facebook Login Authentification', {'fields': ('login_url', 'api_key', 'api_secret')}),
        ('Calls support', {'fields': ('support_people', 'support_groups', 'support_activities_push', 'support_activities_pull', 'support_notifications')})
    )
admin.site.register(FBPlatform, FBPlatformAdmin)


class OSPlatformAdmin(admin.ModelAdmin):
    fieldsets = ( 
        (None, {'fields': ('name', 'api_url', 'logo', 'is_active')}),   
        ('OAuth Authentification', {'fields': ('oauth_consumer_key', 'oauth_consumer_secret', 'oauth_request_token_url', 'oauth_authorization_url', 'oauth_access_token_url', 'oauth_signature_method', 'oauth_token_validity')}),  
        ('Calls support', {'fields': ('support_people', 'support_groups', 'support_activities_push', 'support_activities_pull', 'support_notifications')}),
        ('Fields correction', {'fields': ('os_id', 'os_displayName', 'os_profileUrl', 'os_birthday', 'os_gender', 'os_description', 'os_emails', 'os_addresses', 'os_thumbnailUrl', 'os_organizations')})
    )
admin.site.register(OSPlatform, OSPlatformAdmin )
