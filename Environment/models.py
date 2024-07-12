from django.db import models


class User(models.Model):
    username = models.CharField('Псевдоним', max_length=50)
    email = models.EmailField('E-mail', primary_key=True)
    password = models.CharField('Пароль', max_length=50)
    height = models.IntegerField("Высота фото", default=0)
    width = models.IntegerField("Ширина фото", default=0)
    photo = models.ImageField('Фото', blank=True, height_field="height", width_field="width", upload_to=f"users/{email}/photos")
    theme = models.BooleanField('Тема рабочего пространства', default=False)
    friends = models.ManyToManyField('self', blank=True)

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
