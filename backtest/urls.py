from django.urls import path
from .views import run_backtest, backtest_dashboard, run_detail, delete_run, toggle_favorite, download_report, update_note
from . import views

urlpatterns = [
    path('run/', views.run_backtest, name='run-backtest'),
    path('dashboard/', views.backtest_dashboard, name='backtest-dashboard'),
    path('run/<int:run_id>/', run_detail, name='run-detail'),
    path('run/<int:run_id>/delete/', delete_run, name='delete-run'),
    path('run/<int:run_id>/favorite/', toggle_favorite, name='toggle-favorite'),
    path('run/<int:run_id>/download/', download_report, name='download-report'),
    path('run/<int:run_id>/note/', update_note, name='update-note'),
] 