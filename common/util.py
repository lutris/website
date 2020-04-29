"""Various utility functions used across the website"""
import yaml
import romkan
from lxml.html.clean import Cleaner  # pylint: disable=no-name-in-module
from xpinyin import Pinyin
from transliterate import translit
from PIL import Image
from django.contrib.auth import get_user_model
from django.utils.text import slugify as django_slugify
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile
SLUG_MAX_LENGTH = 50


def slugify(text):
    """Version of slugify that supports Japanese and Chinese characters"""
    if not text:
        return ""
    slug = django_slugify(text)
    if not slug:
        # Title may be in Japanese
        slug = django_slugify(romkan.to_roma(text))
    if not slug:
        # Title may be in Chinese
        pinyin = Pinyin()
        slug = django_slugify(pinyin.get_pinyin(text))
    if not slug:
        # Try transliterate which supports Cyryllic, Greek and other alphabets
        slug = django_slugify(translit(text, reversed=True))
    return slug[:50]


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
    text = str(text)
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


def create_user(username='user', password='password'):
    user = get_user_model().objects.create(username=username,
                                           is_active=True)
    user.set_password(password)
    user.save()
    return user


def clean_html(dirty_markup):
    """Removes all tags while preserving some.
    Keeps the tags that are valid in Gtk markup
    This allows to render proper html for installer descriptions.
    """
    cleaner = Cleaner(
        style=True,
        scripts=True,
        remove_unknown_tags=False,
        safe_attrs=set(['href']),
        allow_tags=('b', 'i', 'a')
    )
    clean_markup = cleaner.clean_html(dirty_markup)
    # The lxml cleaner adds a div around the resulting
    # markup, which we don't want.
    return clean_markup[5:-6]


def load_yaml(content):
    """Loads a YAML string and return a native structure.

    ~~ Uses BaseLoader to convert everything as a string, it is just as safe if ~~
    ~~ not safer than SafeLoader since there is no type conversion. ~~

    SafeLoader is used for now, the client doesn't parse boolean values correctly.
    """
    return yaml.load(content, Loader=yaml.SafeLoader)


def dump_yaml(native_data):
    """Takes a native structure and outputs it in YAML.

    default_flow_style is disabled to ensure that every level gets expanded as
    YAML mappings and not JSON.
    """
    return yaml.safe_dump(native_data, default_flow_style=False)


def get_crop_size(image_size, target_ratio):
    """Return size of the biggest image that can be cut out from the
    original that will respect the target ratio.

    Args:
        size (tuple): Size of the original image
        target_ratio (float): Ratio for the target image
    """
    image_width, image_height = image_size
    original_ratio = image_width / float(image_height)
    if target_ratio > original_ratio:
        target_width = image_width
        target_height = image_width / target_ratio
    else:
        target_width = image_height * target_ratio
        target_height = image_height
    return (target_width, target_height)


def crop_banner(img_path, dest_path):
    """Crop an image to fit the banner ratio

    Args:
        img_path (str): path for the image to resize.
        dest_path (str): path to store the modified image.
    """
    image = Image.open(img_path)

    # Get current and desired ratio for the images
    img_width = image.size[0]
    img_height = image.size[1]
    target_ratio = 184 / 69.0
    target_width, target_height = get_crop_size(image.size, target_ratio)

    img_ratio = img_width / float(img_height)
    if target_ratio > img_ratio:
        box = (0, (img_height - target_height) / 2, img_width, (img_height + target_height) / 2)
    else:
        box = ((img_width - target_width) / 2, 0, (img_width + target_width) / 2, img_height)

    image = image.crop(box)
    image.save(dest_path)


def check_image_size(image_type: str, image: ImageFieldFile) -> bool:
    image_size = '{0}x{1}'.format(image.width, image.height)
    if image_type == 'icon' and image_size != settings.ICON_SIZE:
        return False
    if image_type == 'large icon' and image_size != settings.ICON_LARGE_SIZE:
        return False
    if image_type == 'banner' and image_size != settings.BANNER_SIZE:
        return False
    return True


def resize_image(image_type: str, image: ImageFieldFile):
    # using style of processing as described here: https://docs.djangoproject.com/en/2.2/topics/files/
    image_size = None
    if image_type not in ['icon', 'large icon', 'banner']:
        raise ValueError("Unsupported image type: %s" % image_type)
    if image_type == 'icon':
        image_size = settings.ICON_SIZE.split('x')
    if image_type == 'large icon':
        image_size = settings.ICON_LARGE_SIZE.split('x')
    if image_type == 'banner':
        image_size = settings.BANNER_SIZE.split('x')
    image.open()
    pil_image = Image.open(image)
    resized_image = pil_image.resize((int(image_size[0]), int(image_size[1])))
    pil_image.close()
    image.open(mode='w')
    resized_image.save(image)
