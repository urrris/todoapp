# Generated by Django 5.0.1 on 2024-07-31 07:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Environment', '0008_alter_user_photo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('FriendRequest', 'Friend request'), ('FriendRequestAccepted', 'Friend request accepted'), ('Unfriending', 'Unfriending'), ('SetProjectCoworker', 'Set as project coworker'), ('DeleteProjectCoworker', 'Delete from project coworkers'), ('AddProjectCoworker', 'Add as project coworker'), ('SetTaskExecutor', 'Set as task executor'), ('DeleteTaskExecutor', 'Delete from task executors'), ('AddTaskExecutor', 'Add as task executor'), ('DeadlineApproaching', 'Task deadline is approaching'), ('DeadlineOver', 'Task deadline is over')], default='FriendRequest')),
                ('project', models.CharField(blank=True, verbose_name='Название проекта')),
                ('task', models.CharField(blank=True, verbose_name='Називание задачи')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='Environment.user')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='Environment.user')),
            ],
            options={
                'verbose_name': 'Уведомление',
                'verbose_name_plural': 'Уведомления',
            },
        ),
    ]