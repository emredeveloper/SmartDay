# tasks/admin.py
from django.contrib import admin
from .models import Task, Tag, UserProfile, Category, TaskComment, PomodoroSession

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'priority', 'status', 'due_date', 'completed']
    list_filter = ['completed', 'priority', 'status', 'category', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    list_editable = ['completed', 'status', 'priority']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('user', 'title', 'description', 'category')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'due_date', 'estimated_duration', 'actual_duration', 'start_time', 'end_time')
        }),
        ('Durum ve Öncelik', {
            'fields': ('status', 'priority', 'completed')
        }),
        ('Ek Bilgiler', {
            'fields': ('notes', 'attachment', 'tags'),
            'classes': ('collapse',)
        })
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'icon']
    search_fields = ['name']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'work_hours', 'sleep_hours', 'preferred_task_time']
    list_filter = ['preferred_task_time']

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment', 'task__title', 'user__username']

@admin.register(PomodoroSession)
class PomodoroSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'start_time', 'duration', 'completed']
    list_filter = ['completed', 'start_time']
    search_fields = ['user__username', 'task__title']