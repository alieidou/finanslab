from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Strategy, StrategyFavorite
from .forms import StrategyForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.contrib import messages
from strategies.models import StrategyRun
from django.db.models import Avg, Count, Q, Max, Min
import json
from accounts.models import ActivityLog

# Create your views here.

class StrategyListView(LoginRequiredMixin, ListView):
    model = Strategy
    template_name = 'strategies/strategy_list.html'
    context_object_name = 'strategies'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.GET.get('favorites') == '1':
            qs = qs.filter(strategyfavorite__user=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context['favorites'] = set(StrategyFavorite.objects.filter(user=user).values_list('strategy_id', flat=True))
        else:
            context['favorites'] = set()
        context['showing_favorites'] = self.request.GET.get('favorites') == '1'
        return context

class StrategyCreateView(LoginRequiredMixin, CreateView):
    model = Strategy
    form_class = StrategyForm
    template_name = 'strategies/strategy_form.html'
    success_url = reverse_lazy('strategy-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        print(f"[DEBUG] ActivityLog: add_strategy for user {self.request.user} strategy {self.object}")
        ActivityLog.objects.create(
            user=self.request.user,
            action='add_strategy',
            strategy=self.object,
            extra={'strategy_name': self.object.strategy_name}
        )
        return response

class StrategyUpdateView(LoginRequiredMixin, UpdateView):
    model = Strategy
    form_class = StrategyForm
    template_name = 'strategies/strategy_form.html'
    success_url = reverse_lazy('strategy-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        print(f"[DEBUG] ActivityLog: edit_strategy for user {self.request.user} strategy {self.object}")
        ActivityLog.objects.create(
            user=self.request.user,
            action='edit_strategy',
            strategy=self.object,
            extra={'strategy_name': self.object.strategy_name}
        )
        return response

class StrategyDeleteView(LoginRequiredMixin, DeleteView):
    model = Strategy
    template_name = 'strategies/strategy_confirm_delete.html'
    success_url = reverse_lazy('strategy-list')

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        print("STRATEGY DELETE VIEW CALLED")
        print(f"[DEBUG] ActivityLog: delete_strategy for user {request.user} strategy {obj}")
        ActivityLog.objects.create(
            user=request.user,
            action='delete_strategy',
            strategy=obj,
            extra={'strategy_name': obj.strategy_name}
        )
        return super().post(request, *args, **kwargs)

@require_POST
@login_required
def toggle_strategy_favorite(request, pk):
    print(f"toggle_strategy_favorite called by user {request.user} for strategy {pk}")
    strategy = Strategy.objects.get(pk=pk)
    fav, created = StrategyFavorite.objects.get_or_create(user=request.user, strategy=strategy)
    if not created:
        fav.delete()
        is_favorite = False
        print(f"[DEBUG] ActivityLog: unfavorite_strategy for user {request.user} strategy {strategy}")
        ActivityLog.objects.create(
            user=request.user,
            action='unfavorite_strategy',
            strategy=strategy,
            extra={'strategy_name': strategy.strategy_name}
        )
    else:
        is_favorite = True
        print(f"[DEBUG] ActivityLog: favorite_strategy for user {request.user} strategy {strategy}")
        ActivityLog.objects.create(
            user=request.user,
            action='favorite_strategy',
            strategy=strategy,
            extra={'strategy_name': strategy.strategy_name}
        )
    return JsonResponse({'success': True, 'is_favorite': is_favorite})

@login_required
def strategy_analytics(request):
    """Show performance insights for strategies"""
    user = request.user
    
    # Get all strategies (they are shared across users)
    strategies = Strategy.objects.all()
    
    # Get backtest results for the current user
    backtest_results = StrategyRun.objects.filter(user=user).select_related('strategy')
    
    # Calculate strategy performance metrics for strategies the user has run
    strategy_metrics = []
    for strategy in strategies:
        strategy_backtests = backtest_results.filter(strategy=strategy)
        total_runs = strategy_backtests.count()
        
        if total_runs > 0:
            # Extract total_return values from JSON result field
            returns = []
            for run in strategy_backtests:
                total_return = run.result.get('total_return', '0%')
                if isinstance(total_return, str) and '%' in total_return:
                    try:
                        # Remove % and convert to float
                        return_value = float(total_return.replace('%', ''))
                        returns.append(return_value)
                    except (ValueError, AttributeError):
                        returns.append(0)
                else:
                    returns.append(0)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                profitable_runs = sum(1 for r in returns if r > 0)
                success_rate = (profitable_runs / len(returns)) * 100
                best_return = max(returns)
                worst_return = min(returns)
                
                strategy_metrics.append({
                    'strategy': strategy,
                    'total_runs': total_runs,
                    'avg_return': round(avg_return, 2),
                    'success_rate': round(success_rate, 1),
                    'best_return': round(best_return, 2),
                    'worst_return': round(worst_return, 2),
                    'recent_runs': strategy_backtests.order_by('-run_at')[:5]
                })
    
    # Overall platform statistics
    total_strategies = strategies.count()
    total_backtests = backtest_results.count()
    overall_success_rate = 0
    overall_avg_return = 0
    
    if total_backtests > 0:
        all_returns = []
        for run in backtest_results:
            total_return = run.result.get('total_return', '0%')
            if isinstance(total_return, str) and '%' in total_return:
                try:
                    return_value = float(total_return.replace('%', ''))
                    all_returns.append(return_value)
                except (ValueError, AttributeError):
                    all_returns.append(0)
            else:
                all_returns.append(0)
        
        if all_returns:
            profitable_total = sum(1 for r in all_returns if r > 0)
            overall_success_rate = (profitable_total / len(all_returns)) * 100
            overall_avg_return = sum(all_returns) / len(all_returns)
    
    # Strategy type performance
    strategy_type_stats = {}
    for strategy_type, _ in Strategy.STRATEGY_CHOICES:
        type_strategies = strategies.filter(name=strategy_type)
        type_backtests = backtest_results.filter(strategy__name=strategy_type)
        
        if type_backtests.count() > 0:
            type_returns = []
            for run in type_backtests:
                total_return = run.result.get('total_return', '0%')
                if isinstance(total_return, str) and '%' in total_return:
                    try:
                        return_value = float(total_return.replace('%', ''))
                        type_returns.append(return_value)
                    except (ValueError, AttributeError):
                        type_returns.append(0)
                else:
                    type_returns.append(0)
            
            if type_returns:
                type_avg_return = sum(type_returns) / len(type_returns)
                type_profitable = sum(1 for r in type_returns if r > 0)
                type_success_rate = (type_profitable / len(type_returns)) * 100
                
                strategy_type_stats[strategy_type] = {
                    'count': type_strategies.count(),
                    'avg_return': round(type_avg_return, 2),
                    'success_rate': round(type_success_rate, 1),
                    'total_runs': type_backtests.count()
                }
        else:
            # Show strategy type even if no backtests yet
            strategy_type_stats[strategy_type] = {
                'count': type_strategies.count(),
                'avg_return': 0,
                'success_rate': 0,
                'total_runs': 0
            }
    
    # Ensure we have at least some data to display
    if not strategy_type_stats:
        for strategy_type, _ in Strategy.STRATEGY_CHOICES:
            type_strategies = strategies.filter(name=strategy_type)
            strategy_type_stats[strategy_type] = {
                'count': type_strategies.count(),
                'avg_return': 0,
                'success_rate': 0,
                'total_runs': 0
            }
    
    context = {
        'strategy_metrics': strategy_metrics,
        'total_strategies': total_strategies,
        'total_backtests': total_backtests,
        'overall_success_rate': round(overall_success_rate, 1),
        'overall_avg_return': round(overall_avg_return, 2),
        'strategy_type_stats': strategy_type_stats,
    }
    
    return render(request, 'strategies/analytics.html', context)
