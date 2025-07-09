from django import forms
from .models import Strategy

SMA_BUY_CHOICES = [
    ("cross_above", "Buy when price crosses above SMA"),
    ("above_n_days", "Buy when price is above SMA for N days")
]
SMA_SELL_CHOICES = [
    ("cross_below", "Sell when price crosses below SMA"),
    ("below_n_days", "Sell when price is below SMA for N days")
]
RSI_BUY_CHOICES = [
    ("rsi_below_30", "Buy when RSI < oversold")
]
RSI_SELL_CHOICES = [
    ("rsi_above_70", "Sell when RSI > overbought")
]
MACD_BUY_CHOICES = [
    ("macd_above_signal", "Buy when MACD crosses above Signal"),
    ("macd_positive", "Buy when MACD is positive")
]
MACD_SELL_CHOICES = [
    ("macd_below_signal", "Sell when MACD crosses below Signal"),
    ("macd_negative", "Sell when MACD is negative")
]
MEAN_BUY_CHOICES = [
    ("below_threshold", "Buy when price is below mean by threshold")
]
MEAN_SELL_CHOICES = [
    ("above_threshold", "Sell when price is above mean by threshold")
]

class StrategyForm(forms.ModelForm):
    # User-defined strategy name
    strategy_name = forms.CharField(max_length=100, required=True, label="Strategy Name", widget=forms.TextInput(attrs={'class': 'form-input w-full', 'placeholder': 'Give your strategy a unique name'}))
    # Common fields
    name = forms.ChoiceField(choices=Strategy.STRATEGY_CHOICES, widget=forms.Select(attrs={'class': 'form-input w-full'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-input w-full', 'rows': 4}))

    # SMA
    sma_window = forms.IntegerField(required=False, min_value=1, max_value=200, label="SMA Window", widget=forms.NumberInput(attrs={'class': 'form-input w-full'}))
    sma_buy_on = forms.ChoiceField(required=False, choices=SMA_BUY_CHOICES, label="SMA Buy Rule", widget=forms.Select(attrs={'class': 'form-input w-full'}))
    sma_sell_on = forms.ChoiceField(required=False, choices=SMA_SELL_CHOICES, label="SMA Sell Rule", widget=forms.Select(attrs={'class': 'form-input w-full'}))
    sma_n = forms.IntegerField(required=False, min_value=1, max_value=20, label="N days (for above/below N days)", widget=forms.NumberInput(attrs={'class': 'form-input w-full'}))

    # RSI
    rsi_window = forms.IntegerField(required=False, min_value=1, max_value=100, label="RSI Window", widget=forms.NumberInput(attrs={'class': 'form-input w-full'}))
    rsi_oversold = forms.IntegerField(required=False, min_value=1, max_value=50, label="RSI Oversold", widget=forms.NumberInput(attrs={'class': 'form-input w-full'}))
    rsi_overbought = forms.IntegerField(required=False, min_value=50, max_value=100, label="RSI Overbought", widget=forms.NumberInput(attrs={'class': 'form-input w-full'}))
    rsi_buy_on = forms.ChoiceField(required=False, choices=RSI_BUY_CHOICES, label="RSI Buy Rule", widget=forms.Select(attrs={'class': 'form-input w-full'}))
    rsi_sell_on = forms.ChoiceField(required=False, choices=RSI_SELL_CHOICES, label="RSI Sell Rule", widget=forms.Select(attrs={'class': 'form-input w-full'}))

    # MACD
    macd_fast = forms.IntegerField(required=False, min_value=1, max_value=50, label="MACD Fast", widget=forms.NumberInput(attrs={'class': 'form-input w-full'}))
    macd_slow = forms.IntegerField(required=False, min_value=1, max_value=100, label="MACD Slow", widget=forms.NumberInput(attrs={'class': 'form-input w-full'}))
    macd_signal = forms.IntegerField(required=False, min_value=1, max_value=50, label="MACD Signal", widget=forms.NumberInput(attrs={'class': 'form-input w-full'}))
    macd_buy_on = forms.ChoiceField(required=False, choices=MACD_BUY_CHOICES, label="MACD Buy Rule", widget=forms.Select(attrs={'class': 'form-input w-full'}))
    macd_sell_on = forms.ChoiceField(required=False, choices=MACD_SELL_CHOICES, label="MACD Sell Rule", widget=forms.Select(attrs={'class': 'form-input w-full'}))

    # Mean Reversion
    mean_window = forms.IntegerField(required=False, min_value=5, max_value=100, label="Mean Window", widget=forms.NumberInput(attrs={'class': 'form-input w-full', 'placeholder': '20'}))
    mean_threshold = forms.FloatField(required=False, min_value=0.001, max_value=0.1, label="Mean Threshold", widget=forms.NumberInput(attrs={'class': 'form-input w-full', 'step': '0.001', 'placeholder': '0.02'}))
    mean_buy_on = forms.ChoiceField(required=False, choices=MEAN_BUY_CHOICES, label="Mean Buy Rule", widget=forms.Select(attrs={'class': 'form-input w-full'}))
    mean_sell_on = forms.ChoiceField(required=False, choices=MEAN_SELL_CHOICES, label="Mean Sell Rule", widget=forms.Select(attrs={'class': 'form-input w-full'}))

    class Meta:
        model = Strategy
        fields = ['strategy_name', 'name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            params = self.instance.parameters or {}
            # Pre-populate custom fields from parameters
            self.fields['sma_window'].initial = params.get('window')
            self.fields['sma_buy_on'].initial = params.get('buy_on')
            self.fields['sma_sell_on'].initial = params.get('sell_on')
            self.fields['sma_n'].initial = params.get('n')
            self.fields['rsi_window'].initial = params.get('window')
            self.fields['rsi_oversold'].initial = params.get('oversold')
            self.fields['rsi_overbought'].initial = params.get('overbought')
            self.fields['rsi_buy_on'].initial = params.get('buy_on')
            self.fields['rsi_sell_on'].initial = params.get('sell_on')
            self.fields['macd_fast'].initial = params.get('fast')
            self.fields['macd_slow'].initial = params.get('slow')
            self.fields['macd_signal'].initial = params.get('signal')
            self.fields['macd_buy_on'].initial = params.get('buy_on')
            self.fields['macd_sell_on'].initial = params.get('sell_on')
            self.fields['mean_window'].initial = params.get('window')
            self.fields['mean_threshold'].initial = params.get('threshold')
            self.fields['mean_buy_on'].initial = params.get('buy_on')
            self.fields['mean_sell_on'].initial = params.get('sell_on')
        else:
            # Set default values for new strategies
            self.fields['mean_window'].initial = 20
            self.fields['mean_threshold'].initial = 0.02

    def clean(self):
        cleaned = super().clean()
        
        # Handle unique constraint for strategy_name when editing
        strategy_name = self.cleaned_data.get('strategy_name')
        if strategy_name and self.instance and self.instance.pk:
            # Check if the name is being changed and if the new name already exists
            if strategy_name != self.instance.strategy_name:
                if Strategy.objects.filter(strategy_name=strategy_name).exclude(pk=self.instance.pk).exists():
                    self.add_error('strategy_name', 'A strategy with this name already exists.')
        
        # Validate required fields for each strategy type
        strat = self.cleaned_data.get('name')
        if strat == 'SMA':
            if not self.cleaned_data.get('sma_window'):
                self.add_error('sma_window', 'This field is required.')
            if not self.cleaned_data.get('sma_buy_on'):
                self.add_error('sma_buy_on', 'This field is required.')
            if not self.cleaned_data.get('sma_sell_on'):
                self.add_error('sma_sell_on', 'This field is required.')
        elif strat == 'RSI':
            if not self.cleaned_data.get('rsi_window'):
                self.add_error('rsi_window', 'This field is required.')
            if not self.cleaned_data.get('rsi_oversold'):
                self.add_error('rsi_oversold', 'This field is required.')
            if not self.cleaned_data.get('rsi_overbought'):
                self.add_error('rsi_overbought', 'This field is required.')
            if not self.cleaned_data.get('rsi_buy_on'):
                self.add_error('rsi_buy_on', 'This field is required.')
            if not self.cleaned_data.get('rsi_sell_on'):
                self.add_error('rsi_sell_on', 'This field is required.')
        elif strat == 'MACD':
            if not self.cleaned_data.get('macd_fast'):
                self.add_error('macd_fast', 'This field is required.')
            if not self.cleaned_data.get('macd_slow'):
                self.add_error('macd_slow', 'This field is required.')
            if not self.cleaned_data.get('macd_signal'):
                self.add_error('macd_signal', 'This field is required.')
            if not self.cleaned_data.get('macd_buy_on'):
                self.add_error('macd_buy_on', 'This field is required.')
            if not self.cleaned_data.get('macd_sell_on'):
                self.add_error('macd_sell_on', 'This field is required.')
        elif strat == 'MEAN_REVERSION':
            if not self.cleaned_data.get('mean_window'):
                self.add_error('mean_window', 'This field is required.')
            if not self.cleaned_data.get('mean_threshold'):
                self.add_error('mean_threshold', 'This field is required.')
            if not self.cleaned_data.get('mean_buy_on'):
                self.add_error('mean_buy_on', 'This field is required.')
            if not self.cleaned_data.get('mean_sell_on'):
                self.add_error('mean_sell_on', 'This field is required.')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        strat = self.cleaned_data['name']
        params = {}
        if strat == 'SMA':
            params = {
                'window': self.cleaned_data['sma_window'],
                'buy_on': self.cleaned_data['sma_buy_on'],
                'sell_on': self.cleaned_data['sma_sell_on'],
            }
            if self.cleaned_data.get('sma_n'):
                params['n'] = self.cleaned_data['sma_n']
        elif strat == 'RSI':
            params = {
                'window': self.cleaned_data['rsi_window'],
                'oversold': self.cleaned_data['rsi_oversold'],
                'overbought': self.cleaned_data['rsi_overbought'],
                'buy_on': self.cleaned_data['rsi_buy_on'],
                'sell_on': self.cleaned_data['rsi_sell_on'],
            }
        elif strat == 'MACD':
            params = {
                'fast': self.cleaned_data['macd_fast'],
                'slow': self.cleaned_data['macd_slow'],
                'signal': self.cleaned_data['macd_signal'],
                'buy_on': self.cleaned_data['macd_buy_on'],
                'sell_on': self.cleaned_data['macd_sell_on'],
            }
        elif strat == 'MEAN_REVERSION':
            params = {
                'window': self.cleaned_data['mean_window'],
                'threshold': self.cleaned_data['mean_threshold'],
                'buy_on': self.cleaned_data['mean_buy_on'],
                'sell_on': self.cleaned_data['mean_sell_on'],
            }
        instance.parameters = params
        if commit:
            instance.save()
        return instance 