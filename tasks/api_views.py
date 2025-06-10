from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Task, Category, PomodoroSession
import json
from datetime import datetime, timedelta
from django.utils import timezone

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class TaskAPIView(View):
    def get(self, request):
        """Görevleri listele"""
        tasks = Task.objects.filter(user=request.user)
        
        # Filtreleme
        status = request.GET.get('status')
        category = request.GET.get('category')
        priority = request.GET.get('priority')
        
        if status:
            tasks = tasks.filter(status=status)
        if category:
            tasks = tasks.filter(category_id=category)
        if priority:
            tasks = tasks.filter(priority=priority)
        
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'due_date': task.due_date.isoformat(),
                'completed': task.completed,
                'category': task.category.name if task.category else None,
                'tags': [tag.name for tag in task.tags.all()]
            })
        
        return JsonResponse({'tasks': task_list})
    
    def post(self, request):
        """Yeni görev oluştur"""
        try:
            data = json.loads(request.body)
            
            task = Task.objects.create(
                user=request.user,
                title=data['title'],
                description=data.get('description', ''),
                due_date=datetime.fromisoformat(data['due_date'].replace('Z', '+00:00')),
                priority=data.get('priority', 2),
                category_id=data.get('category_id') if data.get('category_id') else None
            )
            
            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'message': 'Görev başarıyla oluşturuldu'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class TaskDetailAPIView(View):
    def get(self, request, task_id):
        """Tek görev detayı"""
        task = get_object_or_404(Task, id=task_id, user=request.user)
        
        return JsonResponse({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'due_date': task.due_date.isoformat(),
            'completed': task.completed,
            'category': task.category.name if task.category else None,
            'estimated_duration': str(task.estimated_duration) if task.estimated_duration else None,
            'actual_duration': str(task.actual_duration) if task.actual_duration else None,
            'notes': task.notes,
            'tags': [tag.name for tag in task.tags.all()]
        })
    
    def put(self, request, task_id):
        """Görev güncelle"""
        try:
            task = get_object_or_404(Task, id=task_id, user=request.user)
            data = json.loads(request.body)
            
            # Güncelleme
            task.title = data.get('title', task.title)
            task.description = data.get('description', task.description)
            task.status = data.get('status', task.status)
            task.priority = data.get('priority', task.priority)
            task.completed = data.get('completed', task.completed)
            task.notes = data.get('notes', task.notes)
            
            if 'due_date' in data:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Görev başarıyla güncellendi'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def delete(self, request, task_id):
        """Görev sil"""
        try:
            task = get_object_or_404(Task, id=task_id, user=request.user)
            task.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Görev başarıyla silindi'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

@login_required
def categories_api(request):
    """Kategorileri listele"""
    categories = Category.objects.all()
    category_list = []
    
    for category in categories:
        category_list.append({
            'id': category.id,
            'name': category.name,
            'color': category.color,
            'icon': category.icon
        })
    
    return JsonResponse({'categories': category_list})

@csrf_exempt
@login_required
def pomodoro_api(request):
    """Pomodoro oturumu kaydet"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            session = PomodoroSession.objects.create(
                user=request.user,
                task_id=data.get('task_id') if data.get('task_id') else None,
                duration=data.get('duration', 25),
                completed=data.get('completed', True)
            )
            
            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'message': 'Pomodoro oturumu kaydedildi'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    # GET - Pomodoro istatistikleri
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    today_sessions = PomodoroSession.objects.filter(
        user=request.user,
        start_time__date=today,
        completed=True
    ).count()
    
    week_sessions = PomodoroSession.objects.filter(
        user=request.user,
        start_time__date__gte=week_ago,
        completed=True
    ).count()
    
    total_focus_time = sum([
        session.duration for session in PomodoroSession.objects.filter(
            user=request.user,
            start_time__date=today,
            completed=True
        )
    ])
    
    return JsonResponse({
        'today_sessions': today_sessions,
        'week_sessions': week_sessions,
        'total_focus_time': total_focus_time
    })
