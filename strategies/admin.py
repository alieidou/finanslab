from django.contrib import admin
from .models import Strategy, StrategyRun

# Register your models here.
admin.site.register(Strategy)
admin.site.register(StrategyRun)
