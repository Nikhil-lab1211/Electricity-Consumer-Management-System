# user_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Consumer, Complaint, PowerOutage

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone', 'password1', 'password2']

class ConsumerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Consumer
        fields = ['account_number', 'meter_number', 'address', 'connection_type', 'sanctioned_load']
        widgets = {
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'meter_number': forms.TextInput(attrs={'class': 'form-control'}),
            'connection_type': forms.Select(attrs={'class': 'form-control'}),
            'sanctioned_load': forms.NumberInput(attrs={'class': 'form-control'})
        }

class BillCheckForm(forms.Form):
    account_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))

class PaymentForm(forms.Form):
    consumer_id = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bill_amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    payment_method = forms.ChoiceField(choices=[
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('net_banking', 'Net Banking'),
        ('upi', 'UPI')
    ], widget=forms.Select(attrs={'class': 'form-control'}))

class OutageReportForm(forms.ModelForm):
    class Meta:
        model = PowerOutage
        fields = ['area_code', 'description']
        widgets = {
            'area_code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
        }

class ConsumptionTrackForm(forms.Form):
    meter_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))