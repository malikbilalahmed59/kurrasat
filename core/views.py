from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

def index(request):
    return render(request, 'index.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def payment(request):
    return render(request, 'payment.html')

def charter(request):
    return render(request, 'charter.html')
