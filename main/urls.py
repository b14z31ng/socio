from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='root'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('post/', views.post_content, name='post_content'),
    path('users/search/', views.search_users, name='search_users'),
    path('conversations/', views.conversations, name='conversations'),
    path('chat/<int:user_id>/', views.chatbox, name='chatbox'),
    path('friends/', views.friends_page, name='friends'),
    path('friends/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friends/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friends/decline/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('friends/cancel/<int:request_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('friends/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<int:group_id>/', views.group_chat, name='group_chat'),
    path('call/<int:user_id>/', views.call_user, name='call_user'),
    path('call_history/', views.call_history, name='call_history'),
    path('api/log_call/', views.log_call, name='log_call'),
]