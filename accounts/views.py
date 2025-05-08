from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('core:index')  # Replace with your home page URL name

def signup(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Your account has been created successfully!'))
            return redirect('core:index')
    else:
        form = UserRegistrationForm()

    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', 'core:index')
                return redirect(next_url)
            else:
                messages.error(request, _('Invalid username or password.'))
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        # Check which form was submitted
        if 'form_type' in request.POST and request.POST['form_type'] == 'avatar_update':
            # Handle avatar form
            if 'profile_image' in request.FILES:
                profile = request.user.profile
                profile.profile_image = request.FILES['profile_image']
                profile.save()
                messages.success(request, _('Profile image updated!'))
                return redirect('accounts:profile')
        else:
            # Handle main profile form
            form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
            if form.is_valid():
                form.save()
                messages.success(request, _('Your profile has been updated!'))
                return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    password_form = PasswordChangeForm(request.user)
    return render(request, 'profile.html', {'form': form, 'password_form': password_form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Your password was successfully updated!'))
            return redirect('accounts:profile')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'password_change.html', {'form': form})