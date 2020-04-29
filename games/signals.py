from django.db.models.signals import pre_save
from django.dispatch import receiver
from common.util import check_image_size, resize_image

from games.models import Game


@receiver(pre_save, sender=Game)
def prepare_images(sender, **kwargs):
    # Ensure icon and banner are of proper sizes
    instance = kwargs.get('instance')
    if instance.pk:
        # Game already in database, check if files need to be changed
        try:
            game = Game.objects.get(pk=instance.pk)
            old_icon = game.icon
            old_banner = game.banner
            if instance.icon and old_icon and old_icon.name != instance.icon.name:
                old_icon.delete(save=False)
            if instance.banner and old_banner and old_banner.name != instance.banner.name:
                old_banner.delete(save=False)
        except Game.DoesNotExist:
            return
    # Check icon and banner sizes and resize if required
    if instance.icon and not check_image_size('icon', instance.icon):
        resize_image('icon', instance.icon)
    if instance.banner and not check_image_size('banner', instance.banner):
        resize_image('banner', instance.banner)
