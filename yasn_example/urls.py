from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/(.*)', admin.site.root),
    (r'^socialconnect/', include('socialconnect.urls')),
    (r'^', include('yasn.urls')),           
)



