from django.urls import path
from . import views


urlpatterns = [ path('', views.RegisterView.as_view(), name='register'),
                path('login/', views.LoginView.as_view(), name='login'),
                path('user-verification/', views.UserView.as_view(), name='user-verification'),
                path('workspace/', views.WorkspaceView.as_view(), name='workspace'),
                path('notification/', views.NotificationView.as_view(), name='notification'),
                path('get-project-info/', views.get_project_info, name='get-project-info'),
                path('get-tasks/', views.get_tasks, name='get-tasks'),
                path('get-task-info/', views.get_task_info, name='get-task-info'),
                path('get-task-executors/', views.get_task_executors, name='get-task-executors'),
                path('search-for-users/', views.search_for_users, name='search-for-users'),
                path('password-reset/', views.PasswordView.as_view(), name='password-reset'),
                path('password-reset-confirmation/', views.PasswordView.as_view(), name='password-reset-confirmation'),
                path('password-change/', views.PasswordView.as_view(), name='password-change') ]