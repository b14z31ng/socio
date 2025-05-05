from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Profile, Post, CryptoUtils, Message
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.db import models

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
    search_query = request.GET.get('search', '')
    if search_query:
        searched_users = User.objects.filter(username__icontains=search_query).exclude(id=user.id)
    else:
        searched_users = []
    return render(request, 'main/conversations.html', {'users': users, 'searched_users': searched_users, 'search_query': search_query})

@login_required
def chatbox(request, user_id):
    other_user = User.objects.get(id=user_id)
    user = request.user
    sent_to = Message.objects.filter(sender=user).values_list('receiver', flat=True)
    received_from = Message.objects.filter(receiver=user).values_list('sender', flat=True)
    user_ids = set(list(sent_to) + list(received_from))
    users = User.objects.filter(id__in=user_ids).exclude(id=user.id)
    search_query = request.GET.get('search', '')
    if search_query:
        searched_users = User.objects.filter(username__icontains=search_query).exclude(id=user.id)
    else:
        searched_users = []
    messages = Message.objects.filter(
        (models.Q(sender=user) & models.Q(receiver=other_user)) |
        (models.Q(sender=other_user) & models.Q(receiver=user))
    ).order_by('timestamp')
    if request.method == 'POST':
        content = request.POST.get('content', '')
        if content:
            msg = Message(sender=user, receiver=other_user, encrypted_content=content)
            msg.save()
            return redirect('chatbox', user_id=other_user.id)
    return render(request, 'main/chatbox.html', {
        'other_user': other_user,
        'messages': messages,
        'users': users,
        'search_query': search_query,
        'searched_users': searched_users,
    })