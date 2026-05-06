from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('authority', 'Authority'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_verified = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Volunteer Features
    is_available = models.BooleanField(default=False)
    is_verified_helper = models.BooleanField(default=False)
    help_category = models.CharField(max_length=50, blank=True, null=True) # e.g. "Medical", "Food"
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class Alert(models.Model):
    CATEGORY_CHOICES = (
        ('police', 'Police'),
        ('fire', 'Fire'),
        ('medical', 'Medical'),
        ('general', 'General'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in progress', 'In Progress'),
        ('resolved', 'Resolved'),
    )
    SCOPE_CHOICES = (
        ('global', 'Global'),
        ('local', 'Local Community'),
        ('authorities', 'All Authorities'),
        ('specific', 'Select Authorities'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    message = models.TextField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='alerts/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='local')
    target_authority = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    is_global = models.BooleanField(default=False) # Legacy, keeping for compatibility
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} alert by {self.user.username}"

class Contribution(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    contributors_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class LocalNeed(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class BloodRequest(models.Model):
    blood_group = models.CharField(max_length=5)
    location = models.CharField(max_length=255)
    is_urgent = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blood_group} requested at {self.location}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='comments')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.alert.id}"
