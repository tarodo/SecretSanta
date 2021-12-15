from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Game(models.Model):
    name = models.CharField('Название игры', max_length=200)
    cost_limit = models.CharField('Лимит на стоимость', blank=True, max_length=40)
    reg_finish = models.DateTimeField('Дата окончания регистраций')
    delivery = models.DateTimeField('Дата отправления подарока')
    created_at = models.DateTimeField(
        'Когда создана игра',
        default=timezone.now)


class Wishlist(models.Model):
    name = models.CharField('Название подарка', max_length=100)


class Interest(models.Model):
    name = models.CharField('Зона интереса для подарка', max_length=100)


class GameUser(models.Model):
    td_id = models.CharField('ID телеграмма', max_length=20)
    is_admin = models.BooleanField('Админ?', default=False)
    name = models.CharField('Имя игрока', max_length=200)
    phone = PhoneNumberField(blank=True, verbose_name="Номер владельца")
    letter = models.TextField('Письмо Санте')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name="Игра")
    wishlist = models.ManyToManyField(Wishlist, verbose_name="Вишлист игрока")
    interest = models.ManyToManyField(Interest, verbose_name="Интересы игрока")


class Lottery(models.Model):
    who = models.OneToOneField(GameUser, on_delete=models.CASCADE, related_name='who', verbose_name="Кто дарит")
    whom = models.OneToOneField(GameUser, on_delete=models.CASCADE, related_name='whom', verbose_name="Кому дарит")
