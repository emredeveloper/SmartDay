# tasks/urls.py
from django.urls import path
from .views import (
    home, performance_report, complete_task, profile, 
    analyze_task, gantt_chart_data, ai_task_analysis, ai_prioritize_tasks, ai_time_estimate, ai_assistant, calendar_view, kanban_view
)
from .auth_views import user_login, user_register, user_logout

urlpatterns = [
    path('', home, name='home'),
    path('login/', user_login, name='login'),
    path('register/', user_register, name='register'),
    path('logout/', user_logout, name='logout'),
    path('calendar/', calendar_view, name='calendar'),
    path('analyze_task/<int:task_id>/', analyze_task, name='analyze_task'),
    path('performance/', performance_report, name='performance_report'),
    path('complete/<int:task_id>/', complete_task, name='complete_task'),
    path('profile/', profile, name='profile'),
    path('ai-assistant/', ai_assistant, name='ai_assistant'),
    path('gantt_chart_data/', gantt_chart_data, name='gantt_chart_data'),
    # AI Features
    path('ai/analysis/', ai_task_analysis, name='ai_analysis'),
    path('ai/prioritize/', ai_prioritize_tasks, name='ai_prioritize'),    path('ai/estimate/', ai_time_estimate, name='ai_time_estimate'),
]

urlpatterns += [
    path('kanban/', kanban_view, name='kanban'),
]