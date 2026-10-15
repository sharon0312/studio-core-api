from django.urls import path
from . import views

app_name='studios'

urlpatterns = [
    
    ## common apis ###
    path('list-studios', views.list_studios, name='list-studios'),
    path('studio-detail', views.studio_detail, name='studio-detail'),
    
    
    
    ######## staff apis #########
    
    path('create-studio', views.create_studio, name='create-studio'),
    
    
]