from django.contrib import admin
from .models import Setting, Deal


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('status', 'take_profit', 'stop_loss', 'leverage', 'balance_percent', 'minimal_price')


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('coin', 'type', 'take_profit', 'stop_loss', 'leverage', 'date')
