from django import forms
from django.contrib.auth.models import User
from .models import Driver


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']



from .models import VehicleDocument, BusRoute, Bus


class DriverRegisterForm(forms.ModelForm):
    route = forms.ModelChoiceField(queryset=BusRoute.objects.all(), required=True)
    total_seats = forms.IntegerField(min_value=1, required=True)

    class Meta:
        model = Driver
        fields = ['phone', 'vehicle_number']
