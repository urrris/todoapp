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
            return render(request, 'environment/user/register.html', {'hint': 'Пароль должен не менее 8 символов', 'flag': 'false'})
        return redirect('/workspace')

    def post(self, request: HttpRequest):
        username = request.POST.get('username', False)
        photo = request.FILES.get('photo', '')
        email = request.POST.get('email', False)
        password = request.POST.get('password', False)
        confirm_password = request.POST.get('confirm_password', False)
        
        fields = {'username': username, 'email': email, 'password': password,
                  'confirm_password': confirm_password, 'hint': '', 'flag': 'true'}

        if not(all((username, email, password, confirm_password))):
            fields['hint'] = 'Все поля, отмеченные *, должны быть заполнены.'
            return render(request, 'environment/user/register.html', fields)
        if (password != confirm_password):
            fields['hint'] = 'Введённые пароли не совпадают.'
            return render(request, 'environment/user/register.html', fields)
        if not (re.fullmatch(r'[a-zA-Z]\w{4,}', username)):
            fields['hint'] = 'Введённый псевдоним должен содержать не менее 5 символов английского алфавита.'
            return render(request, 'environment/user/register.html', fields)
        if (not (re.fullmatch(r'[a-z0-9\.]+?@[a-z]+?\.(com|ru)', email))):
            fields['hint'] = 'Введённый адрес электронной почты некорректен.'
            return render(request, 'environment/user/register.html', fields)
        if (not (re.fullmatch(r"""[\w~`=\-!@'"#№|$;%:&,<>/\\\^\?\*\(\)\[\]\{\}\+]{8,}""", password))):
            fields['hint'] = 'Введённый пароль некорректен.'
            return render(request, 'environment/user/register.html', fields)

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

        fields = {'email': email, 'password': password, 'hint': '', 'flag': 'true'}

        if not (all((email, password))):
            fields['hint'] = 'Все поля, отмеченные *, должны быть заполнены.'
            return render(request, 'environment/user/login.html', fields)

        try:
            User.objects.get(email=email, password=password)
            request.session['login'] = True
            request.session['__user-email'] = email
            request.session.set_expiry(timedelta(days=1))
            return redirect('/workspace')
        except:
            fields['hint'] = 'Адрес электронной почты или пароль введены некорректно.'
            return render(request, 'environment/user/login.html', fields)


class WorkspaceView(View):
    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            return redirect('login')
        request.session.set_expiry(timedelta(days=1))
        user = User.objects.get(email=request.session.get('__user-email'))
        return render(request, 'environment/user/workspace.html', 
                      {'photo': user.photo.url, "own_projects": user.own_projects.all(), 'other_projects': user.projects.all()}
                      )

    def post(self, request: HttpRequest):
        request.session.set_expiry(timedelta(microseconds=1))
        return redirect('register')
