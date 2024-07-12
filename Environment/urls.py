from django.urls import path
from . import views


urlpatterns = [path('', views.RegisterView.as_view(), name='register'),
               path('login/', views.LoginView.as_view(), name='login'),
                path('workspace/', views.WorkspaceView.as_view(), name='workspace'),
                path('get-tasks/', views.get_tasks, name='get-tasks'),
                path('change-theme/', views.change_theme, name='change-theme'),
                path('get-project-info/', views.get_project_info, name='get-project-info'),
                path('delete-project/', views.delete_project, name='delete-project'),
                path('get-task-executors/', views.get_task_executors, name='get-task-executors'),
                path('get-task-info/', views.get_task_info, name='get-task-info'),
                path('delete-task/', views.delete_task, name='delete-task')]
