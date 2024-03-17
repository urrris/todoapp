from django.contrib import admin
from .models import User, Project, Task, Subtask

# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "creator"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "project"]


@admin.register(Subtask)
class Subtask(admin.ModelAdmin):
    list_display = ["title", "task"]
