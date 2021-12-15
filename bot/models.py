from django.db import models
from django.utils import timezone


class Game(models.Model):
    name = models.CharField('Название игры', max_length=200)
    created_at = models.DateTimeField(
        'Когда создана игра',
        default=timezone.now,
        db_index=True)
