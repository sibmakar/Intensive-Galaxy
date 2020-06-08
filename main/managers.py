from django.db import models


class ProductTagManager(models.Manager):
    """Product Tag Manager

    Notes
    -----
    To be used to load data into db using natural keys
    """

    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class ActiveManager(models.Manager):
    """Active Model Manager
    Notes
    -----
    Filters objects which has active=True
    """

    def active(self):
        return self.filter(active=True)
