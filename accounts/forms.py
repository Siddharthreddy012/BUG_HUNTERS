from django import forms
from django.contrib.auth.models import User
from .models import ParticipantProfile

class ParticipantRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'})
    )
    roll_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 21CS101 / Roll No'})
    )
    department = forms.ChoiceField(
        choices=ParticipantProfile.DEPARTMENT_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    year = forms.ChoiceField(
        choices=ParticipantProfile.YEAR_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@college.edu'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a unique username'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password (min 6 chars)'})
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean_roll_number(self):
        roll_number = self.cleaned_data.get('roll_number')
        if ParticipantProfile.objects.filter(roll_number__iexact=roll_number).exists():
            raise forms.ValidationError("This Roll Number is already registered.")
        return roll_number

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        cpwd = cleaned_data.get('confirm_password')

        if pwd and cpwd and pwd != cpwd:
            self.add_error('confirm_password', "Passwords do not match. Please verify and re-enter.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            ParticipantProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                roll_number=self.cleaned_data['roll_number'],
                department=self.cleaned_data['department'],
                year=self.cleaned_data['year']
            )
        return user

