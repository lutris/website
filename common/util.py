from django.contrib.auth import get_user_model
from django.utils.text import slugify
SLUG_MAX_LENGTH = 50


def get_auto_increment_slug(model, instance, text, slug=None):
    """Return a slug of `text` while keeping it unique within a given model.
    If the slug exists, a number will be appended to it until it is made unique
    The slug field must be named `slug`.

    :param model: Class of the Model the object belongs to
    :param instance: Instance of object the slug belongs to
    :param text: The string to slugify
    :param slug: Optional initial slug
    :return: Unique slug for the model
    """
    text = unicode(text)
    if not slug:
        original_slug = slugify(text)[:SLUG_MAX_LENGTH]
        slug = original_slug
    else:
        original_slug = slug
    slug_exists = True
    counter = 1
    while slug_exists:
        pk = instance.pk if instance else 0
        slug_exists = (
            model.objects
            .exclude(pk=pk)
            .filter(slug=slug)
            .exists()
        )
        if slug_exists:
            suffix = "-%d" % counter
            slug = original_slug[:SLUG_MAX_LENGTH - len(suffix)] + suffix
            counter += 1
    return slug


def create_admin(username='admin', password='admin'):
    user = get_user_model().objects.create(username=username,
                                           is_superuser=True,
                                           is_staff=True,
                                           is_active=True)
    user.set_password(password)
    user.save()
    return user
