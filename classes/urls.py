from django.urls import path
from . import views

app_name='classes'

urlpatterns = [
    
    ## common apis ###
    path('list-classes', views.list_classes, name='list-classes'),
    
    
    ######## staff apis #########
    
    path('create-studio-class', views.create_class, name='create-studio-class'),

    path('list-members', views.members_list, name='list-members'),
    path('grant-credits', views.grant_credits, name='grant-credits'),
    
    
    
    
]