from django.contrib import admin
from .models import Game, GameUser, Wishlist, Interest, Lottery
# Register your models here.


class GameAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )
    list_display = ('name', 'cost_limit', 'reg_finish', 'delivery', )


class GameUserAdmin(admin.ModelAdmin):
    list_display = ('td_id', 'name', 'phone')


class LotteryAdmin(admin.ModelAdmin):
    list_display = ('game', 'who', 'whom')


admin.site.register(Game, GameAdmin)
admin.site.register(GameUser, GameUserAdmin)
admin.site.register(Wishlist)
admin.site.register(Interest)
admin.site.register(Lottery, LotteryAdmin)
