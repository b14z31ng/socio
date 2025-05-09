from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Profile, Post, CryptoUtils, Message, FriendRequest, Group, GroupMessage, CallHistory
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Credential check function
def check_credentials(username, password):
    try:
        user = User.objects.get(username=username)
        if check_password(password, user.password):
            return user
    except User.DoesNotExist:
        return None
    return None

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = check_credentials(username, password)
        if user is not None:
            login(request, user)
            return redirect('post_content')
        else:
            return HttpResponse('Invalid credentials')
    return render(request, 'main/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose another one.')
            return render(request, 'main/signup.html')
        user = User.objects.create_user(username=username, password=password)
        # Encrypt and store user info
        Profile.objects.create(user=user)
        return redirect('login')
    return render(request, 'main/signup.html')

@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if 'profile_pic' in request.FILES:
            profile.profile_pic = request.FILES['profile_pic']
            profile.save()
            messages.success(request, 'Profile picture updated!')
            return redirect('profile')
        if 'message' in request.POST:
            user_id = request.POST.get('message')
            return redirect('chatbox', user_id=user_id)
    posts = Post.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/profile.html', {'profile': profile, 'posts': posts})

@login_required
def post_content(request):
    if request.method == 'POST':
        content = request.POST.get('content', '')
        media = request.FILES.get('media')
        post = Post(user=request.user, encrypted_content=content, media=media)
        post.save()
        return redirect('post_content')  # Redirect after POST to prevent duplicate submissions
    posts = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Ensure Profile exists for the user
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'main/post.html', {'profile': profile, 'posts': page_obj})

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    users = []
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
    if request.method == 'POST':
        if 'message' in request.POST:
            user_id = request.POST.get('message')
            return redirect('chatbox', user_id=user_id)
    return render(request, 'main/search_users.html', {'users': users, 'query': query})

@login_required
def conversations(request):
    user = request.user
    sent_to = Message.objects.filter(sender=user).values_list('receiver', flat=True)
    received_from = Message.objects.filter(receiver=user).values_list('sender', flat=True)
    user_ids = set(list(sent_to) + list(received_from))
    users = User.objects.filter(id__in=user_ids).exclude(id=user.id)
    groups = user.chat_groups.all()
    search_query = request.GET.get('search', '')
    if search_query:
        searched_users = User.objects.filter(username__icontains=search_query).exclude(id=user.id)
        searched_groups = Group.objects.filter(name__icontains=search_query, members=user)
    else:
        searched_users = []
        searched_groups = []
    return render(request, 'main/conversations.html', {
        'users': users,
        'groups': groups,
        'searched_users': searched_users,
        'searched_groups': searched_groups,
        'search_query': search_query
    })

@login_required
def chatbox(request, user_id):
    other_user = User.objects.get(id=user_id)
    user = request.user
    sent_to = Message.objects.filter(sender=user).values_list('receiver', flat=True)
    received_from = Message.objects.filter(receiver=user).values_list('sender', flat=True)
    user_ids = set(list(sent_to) + list(received_from))
    users = User.objects.filter(id__in=user_ids).exclude(id=user.id)
    groups = user.chat_groups.all()
    search_query = request.GET.get('search', '')
    if search_query:
        searched_users = User.objects.filter(username__icontains=search_query).exclude(id=user.id)
        searched_groups = Group.objects.filter(name__icontains=search_query, members=user)
    else:
        searched_users = []
        searched_groups = []
    messages = Message.objects.filter(
        (models.Q(sender=user) & models.Q(receiver=other_user)) |
        (models.Q(sender=other_user) & models.Q(receiver=user))
    ).order_by('timestamp')
    if request.method == 'POST':
        content = request.POST.get('content', '')
        media = request.FILES.get('media')
        if content or media:
            msg = Message(sender=user, receiver=other_user, encrypted_content=content, media=media)
            msg.save()
            # Send message to WebSocket group for instant update
            channel_layer = get_channel_layer()
            room_name = f"chat_{min(user.id, other_user.id)}_{max(user.id, other_user.id)}"
            async_to_sync(channel_layer.group_send)(
                room_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'sender': user.id,  # Use numeric ID for frontend compatibility
                        'content': msg.get_content(),
                        'media_url': msg.media.url if msg.media else '',
                        'timestamp': msg.timestamp.strftime('%H:%M')
                    }
                }
            )
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True})
            else:
                return redirect('chatbox', user_id=other_user.id)
    return render(request, 'main/chatbox.html', {
        'other_user': other_user,
        'messages': messages,
        'users': users,
        'groups': groups,
        'search_query': search_query,
        'searched_users': searched_users,
        'searched_groups': searched_groups,
    })

@login_required
def friends_page(request):
    user = request.user
    # Friends: accepted requests where user is from_user or to_user
    friends = User.objects.filter(
        models.Q(sent_friend_requests__to_user=user, sent_friend_requests__status='accepted') |
        models.Q(received_friend_requests__from_user=user, received_friend_requests__status='accepted')
    ).distinct()
    # Incoming requests
    incoming = FriendRequest.objects.filter(to_user=user, status='pending')
    # Outgoing requests
    outgoing = FriendRequest.objects.filter(from_user=user, status='pending')
    return render(request, 'main/friends.html', {
        'friends': friends,
        'incoming': incoming,
        'outgoing': outgoing,
    })

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    created = False
    if to_user != request.user and not FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        created = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'created': created})
    return redirect(request.META.get('HTTP_REFERER', 'friends'))

@login_required
def accept_friend_request(request, request_id):
    fr = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    fr.status = 'accepted'
    fr.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'action': 'accepted'})
    return redirect(request.META.get('HTTP_REFERER', 'friends'))

@login_required
def decline_friend_request(request, request_id):
    fr = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    fr.status = 'declined'
    fr.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'action': 'declined'})
    return redirect(request.META.get('HTTP_REFERER', 'friends'))

@login_required
def cancel_friend_request(request, request_id):
    try:
        fr = FriendRequest.objects.get(id=request_id, from_user=request.user)
        fr.delete()
        result = 'deleted'
    except FriendRequest.DoesNotExist:
        result = 'not_found'
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'action': result})
    return redirect(request.META.get('HTTP_REFERER', 'friends'))

@login_required
def remove_friend(request, user_id):
    user = request.user
    other = get_object_or_404(User, id=user_id)
    FriendRequest.objects.filter(
        (models.Q(from_user=user, to_user=other) | models.Q(from_user=other, to_user=user)),
        status='accepted'
    ).delete()
    return redirect('friends')

@login_required
def user_profile(request, user_id):
    if request.user.id == user_id:
        return redirect('profile')
    other = get_object_or_404(User, id=user_id)
    profile = Profile.objects.filter(user=other).first()
    user = request.user
    # Check friend status
    is_friend = FriendRequest.objects.filter(
        ((models.Q(from_user=user, to_user=other) | models.Q(from_user=other, to_user=user)) &
         models.Q(status='accepted'))
    ).exists()
    outgoing_request = FriendRequest.objects.filter(from_user=user, to_user=other, status='pending').first()
    incoming_request = FriendRequest.objects.filter(from_user=other, to_user=user, status='pending').first()
    friend_status = None
    if is_friend:
        friend_status = 'friends'
    elif outgoing_request:
        friend_status = 'outgoing'
    elif incoming_request:
        friend_status = 'incoming'
    else:
        friend_status = 'none'
    posts = Post.objects.filter(user=other).order_by('-created_at')
    context = {
        'other_user': other,
        'profile': profile,
        'friend_status': friend_status,
        'outgoing_request': outgoing_request,
        'incoming_request': incoming_request,
        'posts': posts,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.GET.get('friend_action_partial') == '1':
        return render(request, 'main/_friend_action.html', context)
    return render(request, 'main/user_profile.html', context)

@login_required
def create_group(request):
    users = User.objects.exclude(id=request.user.id)
    if request.method == 'POST':
        name = request.POST.get('name')
        member_ids = request.POST.getlist('members')
        if name and member_ids:
            group = Group.objects.create(name=name, created_by=request.user)
            group.members.add(request.user)
            for uid in member_ids:
                user = User.objects.get(id=uid)
                group.members.add(user)
            return redirect('group_chat', group_id=group.id)
    return render(request, 'main/create_group.html', {'users': users})

@login_required
def group_list(request):
    groups = request.user.chat_groups.all()
    return render(request, 'main/group_list.html', {'groups': groups})

@login_required
def group_chat(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.user not in group.members.all():
        return HttpResponse('You are not a member of this group.', status=403)
    user = request.user
    sent_to = Message.objects.filter(sender=user).values_list('receiver', flat=True)
    received_from = Message.objects.filter(receiver=user).values_list('sender', flat=True)
    user_ids = set(list(sent_to) + list(received_from))
    users = User.objects.filter(id__in=user_ids).exclude(id=user.id)
    groups = user.chat_groups.all()
    search_query = request.GET.get('search', '')
    if search_query:
        searched_users = User.objects.filter(username__icontains=search_query).exclude(id=user.id)
        searched_groups = Group.objects.filter(name__icontains=search_query, members=user)
    else:
        searched_users = []
        searched_groups = []
    if request.method == 'POST':
        content = request.POST.get('content', '')
        media = request.FILES.get('media')
        if content or media:
            GroupMessage.objects.create(group=group, sender=request.user, encrypted_content=content, media=media)
            return redirect(reverse('group_chat', args=[group.id]))
    messages = group.messages.select_related('sender').order_by('timestamp')
    return render(request, 'main/group_chat.html', {
        'group': group,
        'messages': messages,
        'users': users,
        'groups': groups,
        'search_query': search_query,
        'searched_users': searched_users,
        'searched_groups': searched_groups,
    })

@login_required
def call_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'main/call_user.html', {'other_user': user})

@csrf_exempt
def log_call(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        caller_id = data.get('caller_id')
        receiver_id = data.get('receiver_id')
        started_at = data.get('started_at')
        ended_at = data.get('ended_at')
        status = data.get('status')
        duration = data.get('duration', 0)
        CallHistory.objects.create(
            caller_id=caller_id,
            receiver_id=receiver_id,
            started_at=started_at,
            ended_at=ended_at,
            status=status,
            duration=duration
        )
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)

@login_required
def call_history(request):
    calls = CallHistory.objects.filter(models.Q(caller=request.user) | models.Q(receiver=request.user)).order_by('-started_at')
    return render(request, 'main/call_history.html', {'calls': calls})