from django import forms
from strategies.models import Strategy

class BacktestForm(forms.Form):
    strategy = forms.ModelChoiceField(
        queryset=Strategy.objects.all(),
        empty_label="Select a strategy",
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    ticker = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., AAPL, GOOGL, MSFT'
        })
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        })
    ) 