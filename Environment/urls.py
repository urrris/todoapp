from django.urls import path
from . import views


urlpatterns = [ path('', views.RegisterView.as_view(), name='register'),
                path('login/', views.LoginView.as_view(), name='login'),
                path('workspace/', views.WorkspaceView.as_view(), name='workspace'),
                path('notification/', views.NotificationView.as_view(), name='notification'),
                path('get-project-info/', views.get_project_info, name='get-project-info'),
                path('get-tasks/', views.get_tasks, name='get-tasks'),
                path('get-task-info/', views.get_task_info, name='get-task-info'),
                path('get-task-executors/', views.get_task_executors, name='get-task-executors'),
                path('search-for-users/', views.search_for_users, name='search-for-users') ]