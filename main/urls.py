'''
URL Patterns
'''
from rest_framework.urlpatterns import format_suffix_patterns
from oauth2_provider import urls as oauth2_urls
import oauth2_provider.views as oauth2_views

from django.views.generic.base import RedirectView

from django.urls import path,include
from main import views

# OAuth2 provider endpoints
oauth2_endpoint_views = [   
    path('authorize/', oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path('token/', oauth2_views.TokenView.as_view(), name="token"),
    path('revoke-token/', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
]

urlpatterns = [

    path('', views.root_path),

    path('send-email/', views.SendEmailView.as_view()),
    path('get-email/<start_date>/<end_date>', views.GetEmailView.as_view()),

    #txt
    path('robots.txt', views.RobotsTxt, name='robotsTxt'),
    path('ads.txt', views.AdsTxt, name='adsTxt'),
    path('.well-known/security.txt', views.SecurityTxt, name='securityTxt'),
    path('humans.txt', views.HumansTxt, name='humansTxt'),

    #icons
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico'), name='favicon'),
    path('apple-touch-icon-precomposed.png', RedirectView.as_view(url='/static/apple-touch-icon-precomposed.png'), name='favicon'),
    path('apple-touch-icon.png', RedirectView.as_view(url='/static/apple-touch-icon-precomposed.png'), name='favicon'),
    path('apple-touch-icon-120x120-precomposed.png', RedirectView.as_view(url='/static/apple-touch-icon-precomposed.png'), name='favicon'),

    #oauth
    path("o/", include((oauth2_endpoint_views, 'oauth2_provider'), namespace='oauth2_provider')),
]

urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]

urlpatterns = format_suffix_patterns(urlpatterns)
