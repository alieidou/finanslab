from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from backtest.forms import BacktestForm
from strategies.models import Strategy, StrategyRun, StrategyFavorite
import yfinance as yf
import pandas as pd
import json
from datetime import datetime, date
import vectorbt as vbt
from accounts.models import ActivityLog


def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    mean_return = returns.mean()
    std_return = returns.std()
    if std_return == 0 or pd.isna(std_return):
        return 0.0
    sharpe = (mean_return - risk_free_rate) / std_return * (252 ** 0.5)
    return sharpe


def calculate_max_drawdown(equity_curve):
    roll_max = equity_curve.cummax()
    drawdown = (equity_curve - roll_max) / roll_max
    max_drawdown = drawdown.min()
    return max_drawdown


def serialize_dates(obj):
    if isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    else:
        return obj

def safe_format_percent(value):
    try:
        # value float ise formatla
        if isinstance(value, (float, int)):
            return f'{value:.2%}'
        # Eğer string ise, float'a çevirip formatla
        val_float = float(str(value).replace('%', '').replace('+', ''))
        return f'{val_float:.2%}'
    except Exception:
        return 'N/A'

def safe_format_float(value):
    try:
        if isinstance(value, (float, int)):
            return f'{value:.2f}'
        val_float = float(value)
        return f'{val_float:.2f}'
    except Exception:
        return 'N/A'


@login_required()
def run_backtest(request):
    result = None

    if request.method == 'POST':
        form = BacktestForm(request.POST)
        if form.is_valid():
            strategy = form.cleaned_data['strategy']
            ticker = form.cleaned_data['ticker']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            try:
                df = yf.download(ticker, start=start_date, end=end_date)
                if df is None or df.empty:
                    result = {'error': 'No data found for this ticker/date range.'}
                elif 'Close' not in df.columns:
                    result = {'error': 'Downloaded data missing Close prices.'}
                else:
                    close = df['Close']
                    if isinstance(close, pd.DataFrame):
                        close = close.squeeze()
                    if hasattr(close, 'values') and len(close.shape) == 2 and close.shape[1] == 1:
                        close = pd.Series(close.to_numpy().ravel(), index=close.index)
                    if not isinstance(close, pd.Series):
                        close = pd.Series(close)
                    strat_name = strategy.name
                    params = strategy.parameters or {}
                    sharpe = max_dd = None

                    # Extract buy/sell rules from parameters
                    buy_on = params.get('buy_on')
                    sell_on = params.get('sell_on')

                    if strat_name == 'SMA':
                        sma_window = params.get('window', 20)
                        close = pd.Series(close)
                        sma = close.rolling(window=sma_window).mean()
                        # Ensure close and sma are pandas Series
                        if not isinstance(close, pd.Series):
                            close = pd.Series(close)
                        if not isinstance(sma, pd.Series):
                            sma = pd.Series(sma, index=close.index)
                        # Buy rules
                        if buy_on == 'cross_above':
                            entries = (close > sma) & (close.shift(1) <= sma.shift(1))
                        elif buy_on == 'above_n_days':
                            n = params.get('n', 3)
                            entries = (close > sma).rolling(window=n).sum() == n
                        else:
                            entries = close > sma
                        # Sell rules
                        if sell_on == 'cross_below':
                            exits = (close < sma) & (close.shift(1) >= sma.shift(1))
                        elif sell_on == 'below_n_days':
                            n = params.get('n', 3)
                            exits = (close < sma).rolling(window=n).sum() == n
                        else:
                            exits = close < sma
                        pf = vbt.Portfolio.from_signals(close, entries, exits, freq='1D')
                        stats = pf.stats()
                        if stats is not None:
                            if hasattr(stats, 'get'):
                                total_return = stats.get('Total Return [%]', None)
                                sharpe = stats.get('Sharpe Ratio', None)
                                max_dd_raw = stats.get('Max Drawdown [%]', None)
                            else:
                                stats = dict(stats)
                                total_return = stats.get('Total Return [%]', None)
                                sharpe = stats.get('Sharpe Ratio', None)
                                max_dd_raw = stats.get('Max Drawdown [%]', None)
                        else:
                            total_return = sharpe = max_dd_raw = None
                        max_dd = (max_dd_raw / 100) if max_dd_raw is not None else None
                        params = {'window': sma_window, 'buy_on': buy_on, 'sell_on': sell_on}

                    elif strat_name == 'RSI':
                        rsi_window = params.get('window', 14)
                        oversold = params.get('oversold', 30)
                        overbought = params.get('overbought', 70)
                        rsi_obj = vbt.RSI.run(close, window=rsi_window)
                        rsi_series = getattr(rsi_obj, 'rsi', None)
                        if not isinstance(rsi_series, pd.Series):
                            raise ValueError("RSI serisi alınamadı.")
                        # Buy rules
                        if buy_on == 'rsi_below_30':
                            entries = rsi_series < oversold
                        else:
                            entries = rsi_series < oversold
                        # Sell rules
                        if sell_on == 'rsi_above_70':
                            exits = rsi_series > overbought
                        else:
                            exits = rsi_series > overbought
                        pf = vbt.Portfolio.from_signals(close, entries, exits, freq='1D')
                        stats = pf.stats()
                        if stats is not None:
                            if hasattr(stats, 'get'):
                                total_return = stats.get('Total Return [%]', None)
                                sharpe = stats.get('Sharpe Ratio', None)
                                max_dd_raw = stats.get('Max Drawdown [%]', None)
                            else:
                                stats = dict(stats)
                                total_return = stats.get('Total Return [%]', None)
                                sharpe = stats.get('Sharpe Ratio', None)
                                max_dd_raw = stats.get('Max Drawdown [%]', None)
                        else:
                            total_return = sharpe = max_dd_raw = None
                        max_dd = (max_dd_raw / 100) if max_dd_raw is not None else None
                        params = {'window': rsi_window, 'oversold': oversold, 'overbought': overbought, 'buy_on': buy_on, 'sell_on': sell_on}

                    elif strat_name == 'MACD':
                        macd_fast = params.get('fast', 12)
                        macd_slow = params.get('slow', 26)
                        macd_signal = params.get('signal', 9)
                        macd_obj = vbt.MACD.run(close, fast_window=macd_fast, slow_window=macd_slow, signal_window=macd_signal)
                        macd_line = getattr(macd_obj, 'macd', None)
                        signal_line = getattr(macd_obj, 'signal', None)
                        # Ensure macd_line and signal_line are pandas Series
                        if not isinstance(macd_line, pd.Series):
                            macd_line = pd.Series(macd_line, index=close.index)
                        if not isinstance(signal_line, pd.Series):
                            signal_line = pd.Series(signal_line, index=close.index)
                        if not isinstance(macd_line, pd.Series) or not isinstance(signal_line, pd.Series):
                            raise ValueError("MACD veya Signal serisi alınamadı.")
                        # Buy rules
                        if buy_on == 'macd_above_signal':
                            entries = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
                        elif buy_on == 'macd_positive':
                            entries = macd_line > 0
                        else:
                            entries = macd_line > signal_line
                        # Sell rules
                        if sell_on == 'macd_below_signal':
                            exits = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
                        elif sell_on == 'macd_negative':
                            exits = macd_line < 0
                        else:
                            exits = macd_line < signal_line
                        pf = vbt.Portfolio.from_signals(close, entries, exits, freq='1D')
                        stats = pf.stats()
                        if stats is not None:
                            if hasattr(stats, 'get'):
                                total_return = stats.get('Total Return [%]', None)
                                sharpe = stats.get('Sharpe Ratio', None)
                                max_dd_raw = stats.get('Max Drawdown [%]', None)
                            else:
                                stats = dict(stats)
                                total_return = stats.get('Total Return [%]', None)
                                sharpe = stats.get('Sharpe Ratio', None)
                                max_dd_raw = stats.get('Max Drawdown [%]', None)
                        else:
                            total_return = sharpe = max_dd_raw = None
                        max_dd = (max_dd_raw / 100) if max_dd_raw is not None else None
                        params = {'fast': macd_fast, 'slow': macd_slow, 'signal': macd_signal, 'buy_on': buy_on, 'sell_on': sell_on}

                    elif strat_name == 'MEAN_REVERSION':
                        try:
                            mean_window = params.get('window', 20)
                            mean_threshold = params.get('threshold', 0.02)

                            # Clamp to safe values
                            if mean_threshold > 0.05:
                                mean_threshold = 0.05
                            if mean_window > 50:
                                mean_window = 50

                            # Ensure close is a pandas Series
                            close = pd.Series(close)
                            mean = close.rolling(window=mean_window).mean()
                            if not isinstance(mean, pd.Series):
                                mean = pd.Series(mean, index=close.index)
                            distance = (close - mean) / mean
                            if not isinstance(distance, pd.Series):
                                distance = pd.Series(distance, index=close.index)

                            # Buy rules
                            if buy_on == 'below_threshold':
                                entries = distance < -mean_threshold
                            else:
                                entries = distance < -mean_threshold

                            # Sell rules
                            if sell_on == 'above_threshold':
                                exits = distance > mean_threshold
                            else:
                                exits = distance > mean_threshold

                            if not isinstance(entries, pd.Series):
                                entries = pd.Series(entries, index=close.index)
                            if not isinstance(exits, pd.Series):
                                exits = pd.Series(exits, index=close.index)

                            # Debug information
                            print(f"Mean Reversion Debug - Window: {mean_window}, Threshold: {mean_threshold}")
                            print(f"Entries sum: {entries.sum()}, Exits sum: {exits.sum()}")
                            print(f"Distance range: {distance.min():.4f} to {distance.max():.4f}")
                            print(f"Price range: {close.min():.2f} to {close.max():.2f}")

                            if entries.sum() > 0 and exits.sum() > 0:
                                pf = vbt.Portfolio.from_signals(close, entries, exits, freq='1D')
                                stats = pf.stats()
                                if stats is not None:
                                    if hasattr(stats, 'get'):
                                        total_return = stats.get('Total Return [%]', None)
                                        sharpe = stats.get('Sharpe Ratio', None)
                                        max_dd_raw = stats.get('Max Drawdown [%]', None)
                                    else:
                                        stats = dict(stats)
                                        total_return = stats.get('Total Return [%]', None)
                                        sharpe = stats.get('Sharpe Ratio', None)
                                        max_dd_raw = stats.get('Max Drawdown [%]', None)
                                else:
                                    total_return = sharpe = max_dd_raw = None
                                max_dd = (max_dd_raw / 100) if max_dd_raw is not None else None
                            else:
                                result = {'error': f'Mean Reversion strategy generated no valid signals. Entries: {entries.sum()}, Exits: {exits.sum()}. Distance range: {distance.min():.4f} to {distance.max():.4f}. Threshold was clamped to {mean_threshold}, window to {mean_window}. Try reducing the threshold or window further if needed.'}
                                return render(request, 'backtest/run_backtest.html', {'form': form, 'result': result})

                            params = {'window': mean_window, 'threshold': mean_threshold, 'buy_on': buy_on, 'sell_on': sell_on}
                        except Exception as e:
                            result = {'error': f'Mean Reversion strategy error: {str(e)}'}
                            return render(request, 'backtest/run_backtest.html', {'form': form, 'result': result})

                    result = {
                        'strategy': strat_name,
                        'total_return': safe_format_percent(total_return / 100 if total_return is not None else None),
                        'sharpe_ratio': safe_format_float(sharpe),
                        'max_drawdown': safe_format_percent(max_dd),
                        **params,
                        'ticker': ticker,
                        'start_date': start_date,
                        'end_date': end_date,
                    }

                    # Kayıt veritabanına
                    StrategyRun.objects.create(
                        user=request.user,
                        strategy=strategy,
                        parameters=serialize_dates({**params, 'ticker': ticker, 'start_date': start_date, 'end_date': end_date}),
                        result=serialize_dates(result),
                    )
                    # Log activity
                    print(f"[DEBUG] ActivityLog: run_backtest for user {request.user} strategy {strategy}")
                    ActivityLog.objects.create(
                        user=request.user,
                        action='run_backtest',
                        strategy=strategy,
                        extra={'ticker': ticker, 'start_date': str(start_date), 'end_date': str(end_date)}
                    )

            except Exception as e:
                result = {'error': f'Hata oluştu: {str(e)}'}
        else:
            form = BacktestForm()
    else:
        form = BacktestForm()

    return render(request, 'backtest/run_backtest.html', {'form': form, 'result': result})


@login_required
def run_detail(request, run_id):
    run = get_object_or_404(StrategyRun, id=run_id, user=request.user)
    # Reconstruct equity curve for performance chart
    equity_curve_dates = []
    equity_curve_values = []
    try:
        params = run.parameters or {}
        strat_name = run.strategy.name
        ticker = params.get('ticker')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        if ticker and start_date and end_date:
            df = yf.download(ticker, start=start_date, end=end_date)
            if df is not None and not df.empty and 'Close' in df.columns:
                close = df['Close']
                if strat_name == 'SMA':
                    sma_window = params.get('window', 20)
                    buy_on = params.get('buy_on')
                    sell_on = params.get('sell_on')
                    sma = close.rolling(window=sma_window).mean()
                    if buy_on == 'cross_above':
                        entries = (close > sma) & (close.shift(1) <= sma.shift(1))
                    elif buy_on == 'above_n_days':
                        n = params.get('n', 3)
                        entries = (close > sma).rolling(window=n).sum() == n
                    else:
                        entries = close > sma
                    if sell_on == 'cross_below':
                        exits = (close < sma) & (close.shift(1) >= sma.shift(1))
                    elif sell_on == 'below_n_days':
                        n = params.get('n', 3)
                        exits = (close < sma).rolling(window=n).sum() == n
                    else:
                        exits = close < sma
                    pf = vbt.Portfolio.from_signals(close, entries, exits, freq='1D')
                elif strat_name == 'RSI':
                    rsi_window = params.get('window', 14)
                    oversold = params.get('oversold', 30)
                    overbought = params.get('overbought', 70)
                    buy_on = params.get('buy_on')
                    sell_on = params.get('sell_on')
                    rsi_obj = vbt.RSI.run(close, window=rsi_window)
                    rsi_series = getattr(rsi_obj, 'rsi', None)
                    if buy_on == 'rsi_below_30':
                        entries = rsi_series < oversold
                    else:
                        entries = rsi_series < oversold
                    if sell_on == 'rsi_above_70':
                        exits = rsi_series > overbought
                    else:
                        exits = rsi_series > overbought
                    pf = vbt.Portfolio.from_signals(close, entries, exits, freq='1D')
                elif strat_name == 'MACD':
                    macd_fast = params.get('fast', 12)
                    macd_slow = params.get('slow', 26)
                    macd_signal = params.get('signal', 9)
                    buy_on = params.get('buy_on')
                    sell_on = params.get('sell_on')
                    macd_obj = vbt.MACD.run(close, fast_window=macd_fast, slow_window=macd_slow, signal_window=macd_signal)
                    macd_line = getattr(macd_obj, 'macd', None)
                    signal_line = getattr(macd_obj, 'signal', None)
                    if buy_on == 'macd_above_signal':
                        entries = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
                    elif buy_on == 'macd_positive':
                        entries = macd_line > 0
                    else:
                        entries = macd_line > signal_line
                    if sell_on == 'macd_below_signal':
                        exits = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
                    elif sell_on == 'macd_negative':
                        exits = macd_line < 0
                    else:
                        exits = macd_line < signal_line
                    pf = vbt.Portfolio.from_signals(close, entries, exits, freq='1D')
                elif strat_name == 'MEAN_REVERSION':
                    mean_window = params.get('window', 20)
                    mean_threshold = params.get('threshold', 0.02)
                    buy_on = params.get('buy_on')
                    sell_on = params.get('sell_on')
                    mean = close.rolling(window=mean_window).mean()
                    distance = (close - mean) / mean
                    
                    # Buy rules
                    if buy_on == 'below_threshold':
                        entries = distance < -mean_threshold
                    else:
                        # Default buy condition
                        entries = distance < -mean_threshold
                    
                    # Sell rules
                    if sell_on == 'above_threshold':
                        exits = distance > mean_threshold
                    else:
                        # Default sell condition
                        exits = distance > mean_threshold
                    
                    # Only create portfolio if we have valid signals
                    if entries.sum() > 0 and exits.sum() > 0:
                        pf = vbt.Portfolio.from_signals(close, entries, exits, freq='1D')
                    else:
                        pf = None
                else:
                    pf = None
                if pf is not None:
                    eq_curve = pf.value()
                    equity_curve_dates = [d.strftime('%Y-%m-%d') for d in eq_curve.index]
                    equity_curve_values = [float(v) for v in eq_curve.values]
    except Exception as e:
        equity_curve_dates = []
        equity_curve_values = []
    return render(request, 'backtest/run_detail.html', {'run': run, 'equity_curve_dates': equity_curve_dates, 'equity_curve_values': equity_curve_values})


@login_required
@require_POST
def delete_run(request, run_id):
    run = get_object_or_404(StrategyRun, id=run_id, user=request.user)
    run.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def toggle_favorite(request, run_id):
    run = get_object_or_404(StrategyRun, id=run_id, user=request.user)
    run.is_favorite = not getattr(run, 'is_favorite', False)
    run.save()
    return JsonResponse({'success': True, 'is_favorite': run.is_favorite})


@login_required
def download_report(request, run_id):
    run = get_object_or_404(StrategyRun, id=run_id, user=request.user)

    report_data = {
        'run_id': run.pk,
        'user': run.user.username,
        'strategy': run.strategy.get_name_display(),
        'run_date': run.run_at.strftime('%Y-%m-%d %H:%M:%S'),
        'parameters': serialize_dates(run.parameters),
        'results': serialize_dates(run.result),
        'notes': run.notes or 'No notes provided'
    }

    response = HttpResponse(
        json.dumps(report_data, indent=2, default=str),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="backtest_report_{run_id}.json"'
    return response


@login_required
def backtest_dashboard(request):
    runs = StrategyRun.objects.filter(user=request.user).order_by('-run_at')

    # Filter by strategy if provided
    strategy_filter = request.GET.get('strategy')
    if strategy_filter:
        runs = runs.filter(strategy__name=strategy_filter)

    # Filter by ticker if provided
    ticker_filter = request.GET.get('ticker')
    if ticker_filter:
        runs = runs.filter(parameters__ticker__icontains=ticker_filter)

    # Sort options
    sort_by = request.GET.get('sort', '-run_at')
    if sort_by == 'total_return':
        def parse_percent(val):
            try:
                return float(str(val).replace('%', '').replace('+', ''))
            except Exception:
                return 0.0
        runs = sorted(runs, key=lambda x: parse_percent(x.result.get('total_return', '0%')), reverse=True)
    elif sort_by == 'sharpe':
        def parse_float(val):
            try:
                return float(val)
            except Exception:
                return 0.0
        runs = sorted(runs, key=lambda x: parse_float(x.result.get('sharpe_ratio', '0')), reverse=True)
    elif sort_by == 'date':
        runs = runs.order_by('-run_at')

    # Get unique strategies and tickers for filters
    strategies = Strategy.objects.all()
    tickers = set()
    for run in StrategyRun.objects.filter(user=request.user):
        ticker = run.parameters.get('ticker', '')
        if ticker:
            tickers.add(ticker)
    
    # Get user's favorite strategies
    favorite_strategies = Strategy.objects.filter(strategyfavorite__user=request.user)
    
    # Calculate total favorites count
    total_favorites = StrategyRun.objects.filter(user=request.user, is_favorite=True).count()
    
    context = {
        'runs': runs,
        'strategies': strategies,
        'tickers': sorted(list(tickers)),
        'current_strategy': strategy_filter,
        'current_ticker': ticker_filter,
        'current_sort': sort_by,
        'favorite_strategies': favorite_strategies,
        'total_favorites': total_favorites,
    }
    return render(request, 'backtest/dashboard.html', context)


def parse_percent(val):
    try:
        return float(str(val).replace('%', '').replace('+', ''))
    except Exception:
        return 0.0


def parse_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0


@login_required
@require_POST
def update_note(request, run_id):
    run = get_object_or_404(StrategyRun, id=run_id, user=request.user)
    note_text = request.POST.get('note', '').strip()
    
    run.notes = note_text
    run.save()
    
    return JsonResponse({
        'success': True,
        'note': note_text,
        'message': 'Note updated successfully!'
    })

