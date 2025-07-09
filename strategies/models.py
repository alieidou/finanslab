from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.

class Strategy(models.Model):
    STRATEGY_CHOICES = [
        ('SMA', 'Simple Moving Average'),
        ('RSI', 'Relative Strength Index'),
        ('MACD', 'MACD'),
        ('MEAN_REVERSION', 'Mean Reversion'),
    ]
    strategy_name = models.CharField(max_length=100, unique=True, default='My Strategy')
    name = models.CharField(max_length=50, choices=STRATEGY_CHOICES)
    description = models.TextField()
    parameters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.strategy_name

class StrategyRun(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    run_at = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    is_favorite = models.BooleanField(default=False, null=False)

    def __str__(self):
        return f"{self.user} - {self.strategy} @ {self.run_at}"

class StrategyFavorite(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'strategy')

    def __str__(self):
        return f"{self.user} - {self.strategy} (Favorite)"
