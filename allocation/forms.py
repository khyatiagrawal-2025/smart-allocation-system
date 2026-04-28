from django import forms
from .models import Request
from django.contrib.auth.models import User


class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['request_type', 'description', 'urgency', 'location']


# 👇 new Form Registration 👇
class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    # DOB Field with HTML5 Date Picker
    dob = forms.DateField(
        required=True, 
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date of Birth"
    )
    
    # Password matching 6 to 80 characters rule
    password = forms.CharField(
        min_length=6, 
        max_length=80, 
        widget=forms.PasswordInput(), 
        required=True
    )
    confirm_password = forms.CharField(
        min_length=6, 
        max_length=80, 
        widget=forms.PasswordInput(), 
        required=True
    )
    
    # Checkbox for Terms and Conditions (User bina tick kiye submit nahi kar payega)
    terms_confirmed = forms.BooleanField(
        required=True, 
        label="I accept the System Terms & Conditions",
        error_messages={'required': 'You must accept the terms to register.'}
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    # Password match check karne ke liye
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match!")
        return cleaned_data

    # Data database mein save karne ke liye
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Password ko encrypt karta hai
        if commit:
            user.save()
        return user