import re

from django.http import HttpRequest
from django.shortcuts import render, redirect
from datetime import timedelta

from django.views import View
from .models import User

# Create your views here.


class RegisterView(View):
    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            return render(request, 'environment/user/register.html', {'hint': 'Пароль должен быть более 8 символов', 'flag': 'false'})
        return redirect('/workspace')

    def post(self, request: HttpRequest):
        username = request.POST.get('username', False)
        photo = request.FILES.get('photo', '')
        email = request.POST.get('email', False)
        password = request.POST.get('password', False)
        confirm_password = request.POST.get('confirm_password', False)

        if not (all((username, email, password, confirm_password))):
            return render(request, 'environment/user/register.html', {'hint': 'Все поля, отмеченные *, должны быть заполнены.', 'flag': 'true'})
        if (password != confirm_password):
            return render(request, 'environment/user/register.html', {'hint': 'Введённые пароли не совпадают.', 'flag': 'true'})
        if not (re.fullmatch(r'[a-zA-Z]\w{4,}', username)):
            return render(request, 'environment/user/register.html', {'hint': 'Введённый псевдоним должен содержать не менее 5 символов английского алфавита.', 'flag': 'true'})
        if (not (re.fullmatch(r'[a-z0-9\.]+?@[a-z]+?\.(com|ru)', email))):
            return render(request, 'environment/user/register.html', {'hint': 'Введённый адрес электронной почты некорректен.', 'flag': 'true'})
        if (not (re.fullmatch(r"""[\w~`=\-!@'"#№|$;%:&,<>/\\\^\?\*\(\)\[\]\{\}\+]{8,}""", password))):
            return render(request, 'environment/user/register.html', {'hint': 'Введённый пароль некорректен.', 'flag': 'true'})

        try:
            User.objects.get(email=email)
        except:
            user = User(username=username, email=email,
                        password=password, photo=photo)
            user.save()

        return redirect('/login')


class LoginView(View):
    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            return render(request, 'environment/user/login.html')
        return redirect('/workspace')

    def post(self, request: HttpRequest):
        email = request.POST.get('email', False)
        password = request.POST.get('password', False)

        if not (all((email, password))):
            return render(request, 'environment/user/login.html', {'hint': 'Все поля, отмеченные *, должны быть заполнены.', 'flag': 'true'})

        try:
            User.objects.get(email=email, password=password)
            request.session['login'] = True
            request.session['__user-email'] = email
            request.session.set_expiry(timedelta(days=1))
            return redirect('/workspace')
        except:
            return render(request, 'environment/user/login.html', {'hint': 'Пользователь не найден.', 'flag': 'true'})


class WorkspaceView(View):
    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            return redirect('login')
        user = User.objects.get(email=request.session.get('__user-email'))
        return render(request, 'environment/user/workspace.html', {'username': user.username, 'email': user.email, 'photo': user.photo.url})

    def post(self, request: HttpRequest):
        request.session.set_expiry(timedelta(microseconds=1))
        return redirect('register')
