from django.urls import path
from . import views

app_name='classes'

urlpatterns = [
    
    ## common apis ###
    path('list-classes', views.list_classes, name='list-classes'),
    
    
    
    #### member apis #####
    path('book-class', views.book_class, name='book-class'),
    path('cancel-booking', views.cancel_booking, name='cancel-booking'),
    path('leave-waitlist', views.cancel_booking, name='leave-waitlist'),
    path('list-bookings', views.my_bookings, name='list-booking'),
    path('waitlist', views.my_waitlist, name='waitlist'),

    
    

    

    
    
    
    
    
    
    
    ######## staff apis #########
    
    path('create-studio-class', views.create_class, name='create-studio-class'),

    path('list-members', views.members_list, name='list-members'),
    path('grant-credits', views.grant_credits, name='grant-credits'),
    
    
    
    
]