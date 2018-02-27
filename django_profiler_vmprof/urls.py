from django.conf.urls import url

from .views import ProfilerEntryJSON
from .views import ProfilerShortView
from .views import ProfilerEntryView
from .views import ProfilerIndexView


urlpatterns = [
    url(r'^json/(?P<pk>[0-9]+)/?$', ProfilerEntryJSON.as_view(), name='ProfilerEntryJSON'),
    url(r'^view/(?P<pk>[0-9]+)/?$', ProfilerShortView.as_view(), name='ProfilerShortView'),
    url(r'^view/?$',                ProfilerEntryView.as_view(), name='ProfilerEntryView'),
    url(r'^$',                      ProfilerIndexView.as_view(), name='ProfilerIndexView'),
]
