from django.conf.urls import url

from msgvis.apps.api import views
from django.views.decorators.csrf import csrf_exempt

api_root_urls = {

    'dataset': url(r'^dataset/$', csrf_exempt(views.DatasetView.as_view()), name='dataset'),
    'message': url(r'^message/(?P<message_id>[0-9]+)$', csrf_exempt(views.MessageView.as_view()), name='message'),
    'dictionary': url(r'^dictionary/$', csrf_exempt(views.DictionaryView.as_view()), name='dictionary'),
    'svm': url(r'^svm/$', csrf_exempt(views.SVMResultView.as_view()), name='svm'),
    'vector': url(r'^vector/(?P<message_id>[0-9]+)$', csrf_exempt(views.FeatureVectorView.as_view()), name='vector'),
    'feature_list': url(r'^feature/$', csrf_exempt(views.UserFeatureView.as_view()), name='feature_list'),
    'feature': url(r'^feature/(?P<feature_id>[0-9]+)/$', csrf_exempt(views.UserFeatureView.as_view()), name='feature'),
    'assignment': url(r'^assignment/$', csrf_exempt(views.CodeAssignmentView.as_view()), name='assignment'),
    'definition': url(r'^definition/(?P<code_id>[0-9]+)$', csrf_exempt(views.CodeDefinitionView.as_view()), name='definition'),
    'code_messages': url(r'^code_messages/$', csrf_exempt(views.CodeMessageView.as_view()), name='code_messages'),
}

urlpatterns = api_root_urls.values() + [
    url(r'^$', views.APIRoot.as_view(root_urls=api_root_urls)),
]
