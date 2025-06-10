from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        else:
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre!')
    else:
        form = AuthenticationForm()
    return render(request, 'tasks/login.html', {'form': form})

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hesap oluşturuldu: {username}')
            return redirect('login')
        else:
            messages.error(request, 'Kayıt sırasında hata oluştu!')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/register.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')
