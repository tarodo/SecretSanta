from django.contrib import admin
from .models import Game, GameUser, Wishlist, Interest, Lottery
# Register your models here.


class GameAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )
    list_display = ('name', "code", 'cost_limit', 'reg_finish', 'delivery', )


class GameUserAdmin(admin.ModelAdmin):
    list_display = ('td_id', "username", 'name', 'phone')


class LotteryAdmin(admin.ModelAdmin):
    list_display = ('game', 'who', 'whom')


class WishlistAdmin(admin.ModelAdmin):
    list_display = ('name', 'interest', 'price')


admin.site.register(Game, GameAdmin)
admin.site.register(GameUser, GameUserAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Interest)
admin.site.register(Lottery, LotteryAdmin)
