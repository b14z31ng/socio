from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='root'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('post/', views.post_content, name='post_content'),
    path('users/search/', views.search_users, name='search_users'),
    path('conversations/', views.conversations, name='conversations'),
    path('chat/<int:user_id>/', views.chatbox, name='chatbox'),
]