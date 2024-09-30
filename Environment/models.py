from django.db import models


def user_directory_path(instance, filename):
    """Формирует путь для сохранения фотографий пользователя."""
    return f"users/{instance.email}/photos/{filename}"


class User(models.Model):
    username = models.CharField('Псевдоним', max_length=50)
    email = models.EmailField('E-mail', primary_key=True)
    password = models.CharField('Пароль', max_length=50)
    photo = models.ImageField('Фото', upload_to=user_directory_path, blank=True)
    theme = models.BooleanField('Тема рабочего пространства', default=False)
    friends = models.ManyToManyField('self', blank=True)
    email_confirmed = models.BooleanField('Статус подтверждения e-mail', default=False)
    confirmation_code = models.CharField('Код подтверждения', max_length=50, blank=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"User({self.username}: {self.email})"


class Project(models.Model):
    title = models.CharField('Название', max_length=50)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="own_projects")
    coworkers = models.ManyToManyField(User, related_name="other_projects")

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    def __str__(self):
        return f"Project({self.title}: {self.creator})"


class Task(models.Model):
    title = models.CharField('Название', max_length=50)
    description = models.TextField("Описание", blank=True)
    priority = models.IntegerField("Приоритет", choices=[(1, "High"), (2, "Middle"), (3, "Low")], default=1)
    deadline = models.DateField('Дата закрытия задачи')
    status = models.CharField(choices={
        "Todo": "Todo",
        "InProgress": "In progress",
        "Done": "Done"
    }, default="Todo")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    executors = models.ManyToManyField(User, related_name='tasks')

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self):
        return f"Task({self.title}: {self.project})"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    type = models.CharField(choices={
        'FriendRequest': 'Friend request',
        'FriendRequestAccepted': 'Friend request accepted',
        'Unfriending': 'Unfriending',
        'SetProjectCoworker': 'Set as project coworker',
        'DeleteProjectCoworker': 'Delete from project coworkers',
        'AddProjectCoworker': 'Add as project coworker',
        'SetTaskExecutor': 'Set as task executor',
        'DeleteTaskExecutor': 'Delete from task executors',
        'AddTaskExecutor': 'Add as task executor',
        'DeadlineApproaching': 'Task deadline is approaching',
        'DeadlineOver': 'Task deadline is over'
    }, default='FriendRequest')
    project = models.CharField('Название проекта', blank=True)
    task = models.CharField('Називание задачи', blank=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return f"Notification({self.recipient}: {self.type})"
