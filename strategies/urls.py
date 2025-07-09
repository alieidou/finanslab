from django.urls import path
from . import views

urlpatterns = [
    path('', views.StrategyListView.as_view(), name='strategy-list'),
    path('create/', views.StrategyCreateView.as_view(), name='strategy-create'),
    path('<int:pk>/edit/', views.StrategyUpdateView.as_view(), name='strategy-edit'),
    path('<int:pk>/delete/', views.StrategyDeleteView.as_view(), name='strategy-delete'),
    path('<int:pk>/favorite/', views.toggle_strategy_favorite, name='strategy-favorite'),
    path('analytics/', views.strategy_analytics, name='strategy-analytics'),
] 