from django.contrib import admin
from .models import Game, GameUser, Wishlist, Interest, Lottery
# Register your models here.

admin.site.register(Game)
admin.site.register(GameUser)
admin.site.register(Wishlist)
admin.site.register(Interest)
admin.site.register(Lottery)
