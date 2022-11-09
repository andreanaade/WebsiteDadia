from django.urls import path
from . import views


urlpatterns = [
    path('new-auth/', views.new_auth, name='New Auth'),
    path('register/', views.register, name='Register'),
    path('login/', views.login, name='Login'),
    path('logout/', views.logout, name='Logout'),
    path('', views.profile, name='Profile'),
    path('update-profile/', views.update_profile, name='Update Profile'),
    path('notifikasi/', views.notifikasi, name='Notifikasi')
]