from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('add_strategy', 'Added a strategy'),
        ('edit_strategy', 'Edited a strategy'),
        ('delete_strategy', 'Deleted a strategy'),
        ('favorite_strategy', 'Added strategy to favorites'),
        ('unfavorite_strategy', 'Removed strategy from favorites'),
        ('run_backtest', 'Ran a backtest'),
    ]
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    strategy = models.ForeignKey('strategies.Strategy', null=True, blank=True, on_delete=models.SET_NULL)
    run = models.ForeignKey('strategies.StrategyRun', null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} {self.get_action_display()} at {self.timestamp}"
