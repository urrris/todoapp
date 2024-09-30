from cryptography.fernet import Fernet
from datetime import timedelta, date
from decouple import config
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from re import fullmatch
from urllib import parse
from .models import User, Project, Task, Notification


class RegisterView(View):
    """Класс представления страницы регистрации."""

    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            context = {'hint': 'Пароль должен быть от 8 до 50 символов', 'colorized': 'false'}
            return render(request, 'environment/user/register.html', context=context)
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
        if not (fullmatch(r'[a-zA-Z]\w{4,49}', username)):
            form_fields['hint'] = 'Введённый псевдоним должен содержать от 5 до 50 символов английского алфавита.'
            return render(request, 'environment/user/register.html', context=form_fields)
        if (not (fullmatch(r'[a-z0-9\.]+?@[a-z]+?\.(com|ru)', email))):
            form_fields['hint'] = 'Введённый адрес электронной почты некорректен.'
            return render(request, 'environment/user/register.html', context=form_fields)
        if (not (fullmatch(r"""[\w~`=\-!@'"#№|$;%:&,<>/\\\^\?\*\(\)\[\]\{\}\+]{8,}""", password))):
            form_fields['hint'] = 'Введённый пароль некорректен.'
            return render(request, 'environment/user/register.html', context=form_fields)

        # Проверка на наличие уже созданного профиля пользователя
        try:
            User.objects.get(email=email)
            form_fields['hint'] = 'Данный аккаунт уже существует.'
            return render(request, 'environment/user/register.html', context=form_fields)
        except:
            if (photo == ''):
                user = User(username=username, email=email, password=password)
            else:
                user = User(username=username, email=email,
                            password=password, photo=photo)
            user.save()
            send_confirmation_email(user)
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
            user = User.objects.get(email=email, password=password)
            request.session['__user-email'] = email
            request.session.set_expiry(timedelta(days=1))
            if not(user.email_confirmed):
                request.session['__user-verification'] = True
                return redirect('/user-verification')
            else:
                request.session['login'] = True
                check_tasks_deadline(request)
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
        context = {
            'username': user.username,
            'email': user.email,
            'photo': user.photo,
            'theme': user.theme,
            'friends': user.friends.all(),
            'notifications': user.notifications.all(),
            'own_projects': user.own_projects.all(),
            'other_projects': user.other_projects.all()
        }
        return render(request, 'environment/user/workspace.html', context=context)

    def post(self, request: HttpRequest):
        data = request.POST

        if len(data.keys()) == 1:  # Выход из аккаунта пользователя
            request.session.set_expiry(timedelta(microseconds=1))
            return redirect('login')
        else:  # Отправка данных различных форм; изменение состояния объектов, зависимых от пользователя
            email = request.session['__user-email']
            user = User.objects.get(email=email)

            if data.get('create-project', False):  # Форма для создания нового проекта
                project_name = data.get('project-name')

                try:
                    user.own_projects.get(title=project_name)
                    return HttpResponse('The project to be created already exists', status=400)
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
            elif data.get('delete-project', False):  # Удаление проекта
                project_name = data.get('project-name')
                email = request.session['__user-email']

                user = User.objects.get(email=email)
                project = user.own_projects.get(title=project_name)
                project.delete()

                return JsonResponse({})
            elif data.get('create-task', False):  # Форма для создания новой задачи
                task_name = data.get('task-name')
                task_project = data.get('task-project')
                task_project_type = data.get('project-type')

                if (task_project_type == 'own'):
                    user_projects = user.own_projects
                else:
                    user_projects = user.other_projects
                project = user_projects.get(title=task_project)
                project_tasks = project.tasks.all()

                try:
                    project_tasks.get(title=task_name)
                    return HttpResponse('The task to be created already exists', status=400)
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
                old_project_type = data.get('old-project-type')
                new_task_name = data.get('task-name')
                new_project_name = data.get('task-project')
                new_project_type = data.get('project-type')
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
            elif data.get('delete-task', False):  # Удаление задачи
                task_name = data.get('task-name')
                project_name = data.get('project-name')
                project_type = data.get('project-type')
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
            elif data.get('change-theme', False):  # Изменение темы пользовательского интерфейса
                theme = eval(data.get('theme'))
                email = request.session['__user-email']

                user = User.objects.get(email=email)
                user.theme = theme
                user.save()

                return JsonResponse({})
            elif data.get('accept-friend-request', False):  # Принятие запроса дружбы
                notification_id = data.get('n-id')
                email = request.session.get('__user-email')
                user = User.objects.get(email=email)

                notification = user.notifications.get(id=notification_id)
                user.friends.add(notification.sender)

                return JsonResponse({'sender': notification.sender.email})
            elif data.get('delete-friend', False):  # Удаление пользователя из друзей
                friend_email = data.get('friend-email')
                friend = User.objects.get(email=friend_email)
                email = request.session.get('__user-email')
                user = User.objects.get(email=email)

                user.friends.remove(friend)
                user.save()

                # При удалении определённого пользователя из друзей - удаляем его из сотрудников и исполнителей задач проекта
                for project in user.own_projects.all():
                    try:
                        project.coworkers.remove(friend)
                        project.save()
                    except:
                        pass
                    else:
                        for task in project.tasks.all():
                            try:
                                task.executors.remove(friend)
                                task.save()
                            except:
                                pass

                return JsonResponse({})
            elif data.get('change-user-photo', False):
                new_photo = request.FILES.get('photo')
                email = request.session.get('__user-email')
                user = User.objects.get(email=email)

                user.photo = new_photo
                user.save()

                return JsonResponse({})
            elif data.get('delete-user-photo', False):
                email = request.session.get('__user-email')
                user = User.objects.get(email=email)

                user.photo = None
                user.save()

                return JsonResponse({})
            elif data.get('change-username', False):
                new_username = data.get('username')
                if not(fullmatch(r'[a-zA-Z]\w{4,49}', new_username)):
                    return JsonResponse({})
                email = request.session.get('__user-email')
                user = User.objects.get(email=email)

                user.username = new_username
                user.save()

                return JsonResponse({})

            return redirect('workspace')


class NotificationView(View):
    """Класс представления пользовательских уведомлений."""

    def get(self, request: HttpRequest):
        pass

    def post(self, request: HttpRequest):
        data = request.POST
        request_type = data.get('r-type', '')

        if request_type == 'send-notification':
            n_type = data.get('type')
            n_recipient = User.objects.get(email=data.get('recipient'))
            n_sender = User.objects.get(email=request.session.get('__user-email'))

            notification = Notification(recipient=n_recipient, sender=n_sender, type=n_type)

            # ('SetProjectCoworker', 'DeleteProjectCoworker', 'AddProjectCoworker', 'SetTaskExecutor', 'DeleteTaskExecutor', 'AddTaskExecutor', 'DeadlineOver', 'DeadlineApproaching')
            if (n_type not in {'FriendRequest', 'Unfriending', 'FriendRequestAccepted'}):
                n_project = data.get('project')
                notification.project = n_project
                # ('DeadlineOver', 'DeadlineApproaching')
                if (n_type not in {'SetProjectCoworker', 'DeleteProjectCoworker', 'AddProjectCoworker'}):
                    n_task = data.get('task')
                    notification.task = n_task

            notification.save()
        elif request_type == 'hide-notification':
            notification_id = data.get('n-id')
            email = request.session.get('__user-email')
            user = User.objects.get(email=email)

            notification = user.notifications.get(id=notification_id)
            notification.delete()

        return JsonResponse({})
    

class PasswordView(View):
    def get(self, request: HttpRequest):
        if not (request.session.get('login', False)):
            return redirect('login')
        
        path = request.path_info
        if (path == '/password-reset/'):
            return render(request, 'environment/user/password-reset.html')
        elif (path == '/password-reset-confirmation/'):
            context = {'hint': 'Пароль должен содержать от 8 до 50 символов', 'colorized': 'false'}
            return render(request, 'environment/user/password-reset-confirmation.html', context=context)
        elif (path == '/password-change/'):
            context = {'hint': 'Пароль должен содержать от 8 до 50 символов', 'colorized': 'false'}
            return render(request, 'environment/user/password-change.html', context=context)
    
    def post(self, request: HttpRequest):
        path = request.path_info
        context = {'colorized': 'true'}
        if (path == '/password-reset/'):
            email = request.POST.get('email', '0')
            try:
                user = User.objects.get(email=email)
                code = generate_confirmation_code()

                user.confirmation_code = code
                user.save()
                send_mail(subject='Письмо для сброса пароля',
                          message=f'''Здравствуйте!\n\nЧтобы сборсить пароль от аккаунта на TodoApp, перейдите по ссылке http://127.0.0.1:8000/password-reset-confirmation/ и введите следующий код подтверждения:\n{code}\n\nЕсли вы не запрашивали сброс пароля, просто проигнорируйте это сообщение.''',
                          from_email=None,
                          recipient_list=[email])
                
                request.session['__password-reset'] = True
                request.session['__user-email'] = email
                request.session.set_expiry(timedelta(minutes=10))
                context['hint'] = 'Письмо с инструкциями для сброса пароля было отправлено на Ваш адрес электронной почты.'
                context['colorized'] = 'false'
                return render(request, 'environment/user/password-reset.html', context=context)
            except:
                context['hint'] = 'Пользователя с таким адресом электронной почты не существует.'
                context['email'] = email
                return render(request, 'environment/user/password-reset.html', context=context)
            
        elif (path == '/password-reset-confirmation/'):
            if (request.session.get('__password-reset', False)):
                code = request.POST.get('confirmation-code', False)
                password = request.POST.get('password', False)
                confirm_password = request.POST.get('confirm_password', False)

                if not (all((code, password, confirm_password))):
                    context['hint'] = 'Все поля, отмеченные *, должны быть заполнены.'
                    return render(request, 'environment/user/password-reset-confirmation.html', context=context)

                email = request.session['__user-email']                
                user = User.objects.get(email=email)
                if (user.confirmation_code == code):
                    if (password != confirm_password):
                        context['hint'] = 'Введённые пароли не совпадают.'
                        return render(request, 'environment/user/password-reset-confirmation.html', context=context)
                    if (not (fullmatch(r"""[\w~`=\-!@'"#№|$;%:&,<>/\\\^\?\*\(\)\[\]\{\}\+]{8,}""", password))):
                        context['hint'] = 'Введённый пароль некорректен.'
                        return render(request, 'environment/user/password-reset-confirmation.html', context=context)
                    
                    user.password = password
                    user.confirmation_code = ''
                    user.save()
                    request.session.pop('__password-reset')
                    return redirect('login')
            
            context['hint'] = 'Сброс пароля не удался.'
            return render(request, 'environment/user/password-reset-confirmation.html', context=context)
        
        elif (path == '/password-change/'):
            current_password = request.POST.get('current-password', False)
            new_password = request.POST.get('password', False)
            confirm_password = request.POST.get('confirm_password', False)

            if not(all((current_password, new_password, confirm_password))):
                context['hint'] = 'Все поля, отмеченные *, должны быть заполнены.'
                return render(request, 'environment/user/password-change.html', context=context)
            
            email = request.session['__user-email']
            user = User.objects.get(email=email)
            if (user.password == current_password):
                if (new_password != confirm_password):
                    context['hint'] = 'Введённые новые пароли не совпадают.'
                    return render(request, 'environment/user/password-change.html', context=context)
                if (not (fullmatch(r"""[\w~`=\-!@'"#№|$;%:&,<>/\\\^\?\*\(\)\[\]\{\}\+]{8,}""", new_password))):
                    context['hint'] = 'Введённый новый пароль некорректен.'
                    return render(request, 'environment/user/password-change.html', context=context)

                user.password = new_password
                user.save()
                request.session.set_expiry(timedelta(milliseconds=1))
                return redirect('/login')
            
            context['hint'] = 'Сменить пароль не удалось.'
            return render(request, 'environment/user/password-change.html', context=context)


class UserView(View):
    def get(self, request: HttpRequest):
        context = {
            'hint': '''На указанный при регистрации адрес электронной почты было отправлено письмо к кодом подтверждения учётной записи. 
                       Просим Вас ввести его в поле выше.'''
        }
        return render(request, 'environment/user/user-verification.html', context=context)
    
    def post(self, request: HttpRequest):
        context = {'colorized': 'true'}
        if (request.session.get('__user-verification', False)):
            code = request.POST.get('confirmation-code', False)

            if not(code):
                context['hint'] = 'Все поля, отмеченные *, должны быть заполнены.'
                return render(request, 'environment/user/user-verification.html', context=context)
            
            email = request.session.get('__user-email')
            user = User.objects.get(email=email)
            if (user.confirmation_code == code):
                user.email_confirmed = True
                user.confirmation_code = ''
                user.save()

                request.session.pop('__user-verification')
                request.session['login'] = True
                request.session.set_expiry(timedelta(days=1))
                check_tasks_deadline(request)

                return redirect('/login')

        context['hint'] = 'Подтвердить созданную учётную запись не удалось.'
        return render(request, 'environment/user/user-verification.html', context=context)


def get_tasks(request: HttpRequest):
    """Возвращает список задач, принадлежащих конкретному проекту."""
    project_name = request.headers.get('Project-Name')
    project_name = parse.unquote(project_name)
    project_type = request.headers.get('Project-Type')
    project_type = parse.unquote(project_type)
    email = request.session['__user-email']
    user = User.objects.get(email=email)

    if (project_type == 'own'):
        user_projects = user.own_projects
    else:
        user_projects = user.other_projects

    # Отбираем только те задачи, одним из исполнетелей которых является пользователь
    tasks = [(t.title, t.status) for t in user_projects.get(title=project_name).tasks.all() if t.executors.contains(user)]
    data = {'tasks': tasks, 'theme': user.theme}

    return JsonResponse(data)


def get_project_info(request: HttpRequest):
    """Возвращает информацию о конкретном проекте."""
    project_name = request.headers.get('Project-Name')
    project_name = parse.unquote(project_name)
    project_type = request.headers.get('Project-Type')
    project_type = parse.unquote(project_type)
    email = request.session['__user-email']
    user = User.objects.get(email=email)

    if (project_type == 'own'):
        user_projects = user.own_projects
    else:
        user_projects = user.other_projects

    project = user_projects.get(title=project_name)
    user_friends = set(user.friends.all())
    # Сравнение с user в последующих 3-х строках необходимо для отображения списка коллег по проекту по отношению к текущему пользователю
    active_coworkers = {c.email: True for c in project.coworkers.all() if c != user}
    coworkers = {c.email: False for c in user_friends if c != user}
    coworkers.update(active_coworkers)
    if project.creator != user:
        coworkers[project.creator.email] = True
    data = {'coworkers': coworkers}

    return JsonResponse(data)


def get_task_executors(request: HttpRequest):
    """Возвращает список возможных исполнителей задачи при её создании."""
    project_name = request.headers.get('Project-Name')
    project_name = parse.unquote(project_name)
    project_type = request.headers.get('Project-Type')
    project_type = parse.unquote(project_type)
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
    project_name = parse.unquote(project_name)
    project_type = request.headers.get('Project-Type')
    project_type = parse.unquote(project_type)
    task_name = request.headers.get('Task-Name')
    task_name = parse.unquote(task_name)
    email = request.session['__user-email']
    user = User.objects.get(email=email)

    if (project_type == 'own'):
        user_projects = user.own_projects
    else:
        user_projects = user.other_projects

    project = user_projects.get(title=project_name)
    task = project.tasks.get(title=task_name)
    executors = {e.email: False for e in project.coworkers.all()}
    active_executors = {e.email: True for e in task.executors.all()}
    executors.update(active_executors)
    executors[project.creator.email] = executors.get(project.creator.email, False)
    data = {'description': task.description, 'executors': executors,
            'deadline': task.deadline, 'priority': task.priority, 'status': task.status}

    return JsonResponse(data)


def search_for_users(request: HttpRequest):
    data = request.headers.get('Data')
    data = parse.unquote(data)
    email = request.session.get('__user-email')
    user = User.objects.get(email=email)

    users = User.objects.filter(email__icontains=data)
    users = users.union(User.objects.filter(username__icontains=data))
    result = {'theme': user.theme, 'users': {}}
    for u in users:
        if u == user:
            continue
        else:
            try:
                # Запрос дружбы к пользователю уже был отправлен
                u.notifications.get(Q(sender=user) & Q(type='FriendRequest'))
            except:
                try:
                    photo = u.photo.url
                except:
                    photo = False
                if user.friends.contains(u):
                    result['users'][u.email] = (u.username, photo, True)
                else:
                    result['users'][u.email] = (u.username, photo, False)

    return JsonResponse(data=result)


def check_tasks_deadline(request: HttpRequest):
    email = request.session.get('__user-email')
    user = User.objects.get(email=email)
    today = date.today()

    for task in user.tasks.all():
        deadline = task.deadline - today
        if deadline.days < 0:
            try:
            # Уведомление уже было отправлено ранее
                user.notifications.get(Q(type='DeadlineOver') & Q(
                    project=notification.project) & Q(task=notification.task))
            except:
                notification = Notification(recipient=user, sender=user, type='DeadlineOver',
                                            project=task.project.title, task=task.title)
        elif deadline <= timedelta(days=1):
            try:
                # Уведомление уже было отправлено ранее
                user.notifications.get(Q(type='DeadlineApproaching') & Q(
                    project=notification.project) & Q(task=notification.task))
            except:
                notification = Notification(recipient=user, sender=user, type='DeadlineApproaching',
                                        project=task.project.title, task=task.title)
        notification.save()

    return JsonResponse({})


def generate_confirmation_code():
    code = Fernet.generate_key()
    code = str(code)
    code = code[2:len(code)-2]
    return code


def send_confirmation_email(user: User):
    code = generate_confirmation_code()

    user.confirmation_code = code
    user.save()
    send_mail(subject='Подтверждение созданной учётной записи TodoApp',
              message=f'Добро пожаловать, {user.username}! Просим Вас подтвердить свою учётную запись, перейдя по ссылке http://127.0.0.1:8000/user-verification/ и введя следующий код подтверждения:\n{code}\n',
              from_email=None,
              recipient_list=[user.email])

    return JsonResponse({})
