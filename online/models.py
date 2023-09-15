# models.py

from django.db import models
from django.conf import settings  # Import the settings module

class OnlineClass(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use settings.AUTH_USER_MODEL

class Session(models.Model):
    online_class = models.ForeignKey(OnlineClass, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    video_conference_link = models.URLField()
    recorded_video_link = models.URLField(blank=True, null=True)

class Attendee(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use settings.AUTH_USER_MODEL
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
