from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created == True:
        user_profile = Profile(user=instance)
        user_profile.save()

class Profile(models.Model):
    avatar = models.ImageField(upload_to='avatars', blank=True)
    website = models.URLField()
    user = models.OneToOneField(User)

    def __unicode__(self):
        return "%s's profile" % self.user.username 

