from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Game(models.Model):
    name = models.CharField("Название игры", max_length=200)
    cost_limit = models.CharField("Лимит на стоимость", blank=True, max_length=40)
    reg_finish = models.DateTimeField("Дата окончания регистраций")
    delivery = models.DateTimeField("Дата отправления подарка")
    created_at = models.DateTimeField("Когда создана игра", default=timezone.now)

    def __str__(self):
        return f'{self.name} : {self.cost_limit} : {self.reg_finish.strftime("%d.%m.%Y %H:%M")}'

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игры"


class Wishlist(models.Model):
    name = models.CharField("Название подарка", max_length=100)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Вишлист"
        verbose_name_plural = "Вишлисты"


class Interest(models.Model):
    name = models.CharField("Зона интереса для подарка", max_length=100)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Интерес"
        verbose_name_plural = "Интересы"


class GameUser(models.Model):
    td_id = models.CharField("ID телеграмма", max_length=20)
    is_admin = models.BooleanField("Админ?", default=False)
    name = models.CharField("Имя игрока", max_length=200)
    phone = PhoneNumberField(verbose_name="Номер владельца")
    letter = models.TextField("Письмо Санте", blank=True)
    game = models.ManyToManyField(Game, verbose_name="Игра")
    wishlist = models.ManyToManyField(
        Wishlist, verbose_name="Вишлист игрока", blank=True
    )
    interest = models.ManyToManyField(
        Interest, verbose_name="Интересы игрока", blank=True
    )

    def __str__(self):
        return f"{self.td_id} : {self.name}"

    class Meta:
        verbose_name = "Участник"
        verbose_name_plural = "Участники"


class Lottery(models.Model):
    who = models.OneToOneField(
        GameUser, on_delete=models.CASCADE, related_name="who", verbose_name="Кто дарит"
    )
    whom = models.OneToOneField(
        GameUser,
        on_delete=models.CASCADE,
        related_name="whom",
        verbose_name="Кому дарит",
    )

    class Meta:
        verbose_name = "Жеребьевка"
        verbose_name_plural = "Жеребьевки"
