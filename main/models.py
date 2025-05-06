import os
import base64
import hmac
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import FileExtensionValidator

# Key management module
class KeyManager:
    @staticmethod
    def get_aes_key():
        return settings.AES_ENCRYPTION_KEY
    @staticmethod
    def get_hmac_key():
        return settings.AES_ENCRYPTION_KEY  # For demo, use same key

# AES encryption/decryption
class CryptoUtils:
    @staticmethod
    def encrypt(data):
        key = KeyManager.get_aes_key()
        cipher = Cipher(algorithms.AES(key), modes.CBC(key[:16]), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(encrypted).decode()
    @staticmethod
    def decrypt(encrypted_data):
        key = KeyManager.get_aes_key()
        cipher = Cipher(algorithms.AES(key), modes.CBC(key[:16]), backend=default_backend())
        decryptor = cipher.decryptor()
        encrypted_data = base64.b64decode(encrypted_data)
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
        return (unpadder.update(decrypted_padded) + unpadder.finalize()).decode()
    @staticmethod
    def hmac(data):
        key = KeyManager.get_hmac_key()
        return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    encrypted_username = models.CharField(max_length=256, default="", blank=True)
    bio = models.TextField(blank=True, null=True, default="")
    bio_mac = models.CharField(max_length=64, blank=True, null=True, default="")
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def save(self, *args, **kwargs):
        self.encrypted_username = CryptoUtils.encrypt(self.user.username)
        if self.bio:
            self.bio = CryptoUtils.encrypt(self.bio)
            self.bio_mac = CryptoUtils.hmac(self.bio)
        super().save(*args, **kwargs)

    def get_username(self):
        return CryptoUtils.decrypt(self.encrypted_username)
    def get_bio(self):
        if self.bio:
            # Integrity check
            if self.bio_mac == CryptoUtils.hmac(self.bio):
                return CryptoUtils.decrypt(self.bio)
            return '[INTEGRITY CHECK FAILED]'
        return None

    def get_profile_pic_url(self):
        if self.profile_pic:
            return self.profile_pic.url
        return None

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    encrypted_content = models.TextField(default="", blank=True)
    content_mac = models.CharField(max_length=64, default="", blank=True)
    media = models.FileField(upload_to='posts/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'])])
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.encrypted_content = CryptoUtils.encrypt(self.encrypted_content)
        self.content_mac = CryptoUtils.hmac(self.encrypted_content)
        super().save(*args, **kwargs)

    def get_content(self):
        # Integrity check
        if self.content_mac == CryptoUtils.hmac(self.encrypted_content):
            return CryptoUtils.decrypt(self.encrypted_content)
        return '[INTEGRITY CHECK FAILED]'

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    encrypted_content = models.TextField(default="", blank=True)
    content_mac = models.CharField(max_length=64, default="", blank=True)
    media = models.FileField(upload_to='messages/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'])])
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.encrypted_content = CryptoUtils.encrypt(self.encrypted_content)
        self.content_mac = CryptoUtils.hmac(self.encrypted_content)
        super().save(*args, **kwargs)

    def get_content(self):
        if self.content_mac == CryptoUtils.hmac(self.encrypted_content):
            return CryptoUtils.decrypt(self.encrypted_content)
        return '[INTEGRITY CHECK FAILED]'

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"

class Group(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='chat_groups')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    encrypted_content = models.TextField(default="", blank=True)
    content_mac = models.CharField(max_length=64, default="", blank=True)
    media = models.FileField(upload_to='group_messages/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'])])
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.encrypted_content = CryptoUtils.encrypt(self.encrypted_content)
        self.content_mac = CryptoUtils.hmac(self.encrypted_content)
        super().save(*args, **kwargs)

    def get_content(self):
        if self.content_mac == CryptoUtils.hmac(self.encrypted_content):
            return CryptoUtils.decrypt(self.encrypted_content)
        return '[INTEGRITY CHECK FAILED]'