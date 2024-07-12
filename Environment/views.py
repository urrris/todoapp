import re
from datetime import timedelta
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from .models import User, Project, Task


class RegisterView(View):
    """Класс представления страницы регистрации."""

    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            return render(request, 'environment/user/register.html', {'hint': 'Пароль должен быть от 8 до 50 символов', 'colorized': 'false'})
        return redirect('/workspace')

    def post(self, request: HttpRequest):
        username = request.POST.get('username', False)
        photo = request.FILES.get('photo', '')
        email = request.POST.get('email', False)
        password = request.POST.get('password', False)
        confirm_password = request.POST.get('confirm_password', False)

        form_fields = {'username': username, 'email': email, 'password': password,
                       'confirm_password': confirm_password, 'hint': '', 'colorized': 'true'}

        if not (all((username, email, password, confirm_password))):
            form_fields['hint'] = 'Все поля, отмеченные *, должны быть заполнены.'
            return render(request, 'environment/user/register.html', context=form_fields)
        if (password != confirm_password):
            form_fields['hint'] = 'Введённые пароли не совпадают.'
            return render(request, 'environment/user/register.html', context=form_fields)
        if (len(password) > 50):
            form_fields['hint'] = 'Введённый пароль не должен превышать длину в 50 символов.'
            return render(request, 'environment/user/register.html', context=form_fields)
        if not (re.fullmatch(r'[a-zA-Z]\w{4,49}', username)):
            form_fields['hint'] = 'Введённый псевдоним должен содержать от 5 до 50 символов английского алфавита.'
            return render(request, 'environment/user/register.html', context=form_fields)
        if (not (re.fullmatch(r'[a-z0-9\.]+?@[a-z]+?\.(com|ru)', email))):
            form_fields['hint'] = 'Введённый адрес электронной почты некорректен.'
            return render(request, 'environment/user/register.html', context=form_fields)
        if (not (re.fullmatch(r"""[\w~`=\-!@'"#№|$;%:&,<>/\\\^\?\*\(\)\[\]\{\}\+]{8,}""", password))):
            form_fields['hint'] = 'Введённый пароль некорректен.'
            return render(request, 'environment/user/register.html', context=form_fields)

        # Проверка на наличие уже созданного профиля пользователя
        try:
            User.objects.get(email=email)
            form_fields['hint'] = 'Данный аккаунт уже существует.'
            return render(request, 'environment/user/register.html', context=form_fields)
        except:
            user = User(username=username, email=email,
                        password=password, photo=photo)
            user.save()
            return redirect('/login')


class LoginView(View):
    """Класс представления страницы входа в аккаунт."""

    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            return render(request, 'environment/user/login.html')
        return redirect('/workspace')

    def post(self, request: HttpRequest):
        email = request.POST.get('email', False)
        password = request.POST.get('password', False)

        form_fields = {'email': email, 'password': password,
                       'hint': '', 'colorized': 'true'}

        if not (all((email, password))):
            form_fields['hint'] = 'Все поля, отмеченные *, должны быть заполнены.'
            return render(request, 'environment/user/login.html', context=form_fields)

        try:
            User.objects.get(email=email, password=password)
            request.session['login'] = True
            request.session['__user-email'] = email
            request.session.set_expiry(timedelta(days=1))
            return redirect('/workspace')
        except:
            form_fields['hint'] = 'Адрес электронной почты или пароль введены некорректно.'
            return render(request, 'environment/user/login.html', context=form_fields)


class WorkspaceView(View):
    """Класс представления рабочего пространства пользователя."""

    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            return redirect('login')

        # Обновление срока действия пользовательской сессии
        request.session.set_expiry(timedelta(days=1))
        user = User.objects.get(email=request.session.get('__user-email'))
        context = {"own_projects": user.own_projects.all(), 'other_projects': user.other_projects.all(),
                   'friends': user.friends.all(), 'theme': user.theme, 'email': user.email}
        return render(request, 'environment/user/workspace.html', context=context)

    def post(self, request: HttpRequest):
        data = request.POST

        if len(data.keys()) == 1:  # Выход из аккаунта пользователя
            request.session.set_expiry(timedelta(microseconds=1))
            return redirect('login')
        else:  # Отправка данных различных форм
            email = request.session['__user-email']
            user = User.objects.get(email=email)

            if data.get('create-project', False):  # Форма для создания нового проекта
                project_name = data.get('project-name')

                try:
                    user.own_projects.get(title=project_name)
                except:
                    project_coworkers = data.getlist('project-coworkers', ())
                    coworkers_profiles = [User.objects.get(
                        email=p_c) for p_c in project_coworkers]

                    project = Project(title=project_name, creator=user)
                    project.save()
                    project.coworkers.set(coworkers_profiles)
            # Форма для редактирования существующего проекта
            elif data.get('edit-project', False):
                old_project_name = data.get('old-project-name')
                new_project_name = data.get('project-name')
                project_coworkers = data.getlist('project-coworkers', ())
                coworkers_profiles = {User.objects.get(
                    email=p_c) for p_c in project_coworkers}

                project = user.own_projects.get(title=old_project_name)

                project.title = new_project_name
                for task in project.tasks.all():  # При удалении определённого пользователя из коллег проекта - удаляем его из исполнителей задач проекта
                    executors = set(task.executors.all()) - coworkers_profiles
                    for executor in executors:
                        task.executors.remove(executor)
                project.coworkers.set(coworkers_profiles)
                project.save()
            elif data.get('create-task', False):  # Форма для создания новой задачи
                task_name = data.get('task-name')
                task_project = data.get('task-project')
                task_project_type = request.headers.get('Project-Type')

                if (task_project_type == 'own'):
                    user_projects = user.own_projects
                else:
                    user_projects = user.other_projects
                project = user_projects.get(title=task_project)
                project_tasks = project.tasks.all()

                try:
                    project_tasks.get(title=task_name)
                except:
                    task_description = data.get('task-description', '')
                    task_executors = data.getlist('task-executors', ())
                    task_deadline = data.get('task-deadline')
                    task_priority = data.get('task-priority')
                    task_status = data.get('task-status')
                    executors_profiles = {User.objects.get(
                        email=t_e) for t_e in task_executors}

                    task = Task(title=task_name, description=task_description, priority=task_priority,
                                deadline=task_deadline, status=task_status, project=project)
                    task.save()
                    task.executors.set(executors_profiles)
            elif data.get('edit-task', False):  # Форма для редактирования существующей задачи
                old_task_name = data.get('old-task-name')
                old_project_name = data.get('old-project-name')
                old_project_type = request.headers.get('Old-Project-Type')
                new_task_name = data.get('task-name')
                new_project_name = data.get('task-project')
                new_project_type = request.headers.get('Project-Type')
                task_description = data.get('task-description', '')
                task_executors = data.getlist('task-executors', ())
                task_deadline = data.get('task-deadline')
                task_priority = data.get('task-priority')
                task_status = data.get('task-status')
                executors_profiles = {User.objects.get(
                    email=p_c) for p_c in task_executors}

                user_projects = {'own': user.own_projects,
                                 'other': user.other_projects}
                project = user_projects[old_project_type].get(
                    title=old_project_name)
                project_tasks = project.tasks.all()

                task = project_tasks.get(title=old_task_name)
                task.title = new_task_name
                task.description = task_description
                task.executors.set(executors_profiles)
                task.deadline = task_deadline
                task.priority = task_priority
                task.status = task_status
                # Изменение проекта, которому принадлежит задача (при потребности)
                if (old_project_name != new_project_name or old_project_type != new_project_type):
                    task.project = user_projects[new_project_type].get(
                        title=new_project_name)
                task.save()

            return redirect('workspace')


def get_tasks(request: HttpRequest):
    """Возвращает список задач, принадлежащих конкретному проекту."""
    project_name = request.headers.get('Project-Name')
    project_type = request.headers.get('Project-Type')
    email = request.session['__user-email']
    user = User.objects.get(email=email)

    if (project_type == 'own'):
        user_projects = user.own_projects
    else:
        user_projects = user.other_projects

    tasks = user_projects.get(title=project_name).tasks.all()
    data = {'tasks': list(
        map(lambda t: (t.title, t.status), tasks)), 'theme': user.theme}

    return JsonResponse(data)


def change_theme(request: HttpRequest):
    """Устанавливает тему пользовательского интерфейса."""
    theme = eval(request.headers.get('Theme'))
    email = request.session['__user-email']

    user = User.objects.get(email=email)
    user.theme = theme
    user.save()

    return JsonResponse({})


def get_project_info(request: HttpRequest):
    """Возвращает информацию о конкретном проекте."""
    project_name = request.headers.get('Project-Name')
    project_type = request.headers.get('Project-Type')
    email = request.session['__user-email']
    user = User.objects.get(email=email)

    if (project_type == 'own'):
        user_projects = user.own_projects
    else:
        user_projects = user.other_projects

    project = user_projects.get(title=project_name)
    user_friends = set(user.friends.all())
    # Сравнение с user в последующих 2-х строках необходимо для отображения списка коллег по проекту по отношению к текущему пользователю
    active_coworkers = {
        c.email: True for c in project.coworkers.all() if c != user}
    coworkers = {c.email: False for c in user_friends if c != user}
    coworkers.update(active_coworkers)
    data = {'coworkers': coworkers}

    return JsonResponse(data)


def delete_project(request: HttpRequest):
    project_name = request.headers.get('Project-Name')
    email = request.session['__user-email']

    user = User.objects.get(email=email)
    project = user.own_projects.get(title=project_name)
    project.delete()

    return JsonResponse({})


def get_task_executors(request: HttpRequest):
    """Возвращает список возможных исполнителей задачи при её создании."""
    project_name = request.headers.get('Project-Name')
    project_type = request.headers.get('Project-Type')
    email = request.session['__user-email']
    user = User.objects.get(email=email)

    if (project_type == 'own'):
        user_projects = user.own_projects
    else:
        user_projects = user.other_projects

    project = user_projects.get(title=project_name)
    executors = {e.email: 1 for e in project.coworkers.all()}
    # Следующие 2 строки необходимы, поскольку текущий пользователь и создатель проекта не состоят или могут не состоять в списоке работников проекта
    executors[user.email] = 1
    executors[project.creator.email] = 1
    data = {'executors': executors}

    return JsonResponse(data)


def get_task_info(request: HttpRequest):
    """Возвращает информацию о конкретной задаче."""
    project_name = request.headers.get('Project-Name')
    project_type = request.headers.get('Project-Type')
    task_name = request.headers.get('Task-Name')
    email = request.session['__user-email']
    user = User.objects.get(email=email)

    if (project_type == 'own'):
        user_projects = user.own_projects
    else:
        user_projects = user.other_projects

    project = user_projects.get(title=project_name)
    task = project.tasks.get(title=task_name)
    executors = {e.email: 0 for e in project.coworkers.all()}
    active_executors = {e.email: 1 for e in task.executors.all()}
    executors.update(active_executors)
    data = {'description': task.description, 'executors': executors,
            'deadline': task.deadline, 'priority': task.priority, 'status': task.status}

    return JsonResponse(data)


def delete_task(request: HttpRequest):
    task_name = request.headers.get('Task-Name')
    project_name = request.headers.get('Project-Name')
    project_type = request.headers.get('Project-Type')
    email = request.session['__user-email']
    user = User.objects.get(email=email)

    if (project_type == 'own'):
        user_projects = user.own_projects.all()
    else:
        user_projects = user.other_projects.all()

    project = user_projects.get(title=project_name)
    task = project.tasks.get(title=task_name)
    task.delete()

    return JsonResponse({})
