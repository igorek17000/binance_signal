from django.db import models


class Setting(models.Model):
    take_profit = models.FloatField()
    stop_loss = models.FloatField()
    leverage = models.IntegerField()
    balance_percent = models.FloatField()
    minimal_price = models.FloatField()
    status = models.BooleanField()

    def __str__(self):
        return "Настройки"

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'


class Deal(models.Model):
    coin = models.CharField(max_length=40)
    type = models.CharField(max_length=40)
    stop_loss = models.FloatField()
    take_profit = models.FloatField()
    leverage = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Сделка - {self.id}"

    class Meta:
        verbose_name = 'Сделка'
        verbose_name_plural = 'Сделки'
