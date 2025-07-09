from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import login as auth_login
from django.contrib import messages
from .forms import UserRegistrationForm
from django.shortcuts import redirect
from django.contrib.auth import logout
from strategies.models import Strategy, StrategyRun
from accounts.models import ActivityLog

# Create your views here.

@login_required
def dashboard(request):
    print("DASHBOARD VIEW CALLED")
    # Get user's favorite strategies
    favorite_strategies = Strategy.objects.filter(strategyfavorite__user=request.user)
    # Get user's recent activities (last 10), explicitly ordered by -timestamp
    recent_activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]
    print("Recent activities for dashboard:")
    for a in recent_activities:
        print(a, a.action, a.extra)
    context = {
        'favorite_strategies': favorite_strategies,
        'recent_activities': recent_activities,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')
