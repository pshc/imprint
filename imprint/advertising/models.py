from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
import os

CACHED_MEDIA_DIR = None
def get_ad_dir(self, filename):
    global CACHED_MEDIA_DIR
    if not CACHED_MEDIA_DIR:
        dir = os.path.join(settings.SITE_MEDIA_SUBDIR, 'ads')
        try:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, dir))
        except OSError, e:
            if e.errno != 17:
                raise
        CACHED_MEDIA_DIR = dir
    return os.path.join(CACHED_MEDIA_DIR, filename)

AD_TYPES = ((1, 'Left Square (180x150)'),
            (2, 'Skyscraper (top) (160x600)'),
            (3, 'Skyscraper (bottom) (160x600)'),
            (4, 'Bottom Banner (728x90)'))

class ImageAd(models.Model):
    image = models.ImageField(upload_to=get_ad_dir)
    type = models.PositiveSmallIntegerField(choices=AD_TYPES, db_index=True)
    url = models.URLField(help_text='Destination URL for this ad.')
    is_active = models.BooleanField('Active', default=True, db_index=True)
    caption = models.CharField(max_length=100, blank=True,
            help_text='Alternate text displayed while/if the image loads.')
    client = models.SlugField(max_length=50,
            help_text='For Google Analytics tracking. '
                      'Letters, numbers, and dashes only.')

    hits = models.PositiveIntegerField(editable=False, default=0)
    site = models.ForeignKey(Site, related_name='ads', editable=False,
            default=Site.objects.get_current)
    added_on = models.DateTimeField(editable=False, default=datetime.now)

    @property
    def image_filename(self):
        return os.path.basename(self.image.name)

    def __unicode__(self):
        return self.image_filename

    class Meta:
        ordering = ["added_on"]

    # Not get_absolute_url to prevent false clicks
    @models.permalink
    def get_redirect_url(self):
        return ('image-ad-redirect', (), {'client': self.client})

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
