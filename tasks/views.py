from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Task, UserProfile, Tag
from django.utils import timezone
import google.generativeai as genai
from django.conf import settings
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count
import os
import time
import json
from django.core.cache import cache

# API key configuration - multiple methods to ensure it's set
try:
    # First, try to use the key from settings
    GEMINI_API_KEY = settings.GEMINI_API_KEY
    
    # Check if API key is valid
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == '':
        # Try to get it from environment variable as a fallback
        GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY')
        
        if not GEMINI_API_KEY:
            # Hardcode it as a last resort - not recommended for production
            GEMINI_API_KEY = 'AIzaSyCUQC....'
            
    # Configure Gemini API with the API key
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"Gemini API configured successfully with key: {GEMINI_API_KEY[:5]}...")
    
except Exception as e:
    print(f"Error configuring Gemini API: {str(e)}")

# AI Helper Functions
def call_gemini_with_retry(prompt, max_retries=3, delay=5):
    """
    Gemini API'yi retry logic ile çağırır
    """
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')  # Daha az quota kullanan model
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            
            # Quota aşımı durumunda
            if "quota" in error_str.lower() or "429" in error_str:
                if attempt < max_retries - 1:
                    print(f"Quota aşımı, {delay} saniye bekleniyor... (Deneme {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
                else:
                    return get_fallback_suggestion()
            
            # Diğer hatalar için
            print(f"Gemini API hatası: {error_str}")
            return get_fallback_suggestion()
    
    return get_fallback_suggestion()

def get_fallback_suggestion():
    """
    API başarısız olduğunda kullanılacak fallback önerileri
    """
    fallback_suggestions = [
        "🎯 Günlük hedeflerinizi gözden geçirin ve önceliklendirin",
        "📅 Yarın için 3 önemli görev belirleyin",
        "⏰ Pomodoro tekniği ile odaklanma sürenizi artırın",
        "🗂️ Görevlerinizi kategorilere ayırarak düzenleyin",
        "📝 Tamamlanan görevlerinizi gözden geçirin ve başarılarınızı kutlayın",
        "🔄 Periyodik görevlerinizi otomatikleştirmeyi düşünün",
        "📊 Bu hafta tamamladığınız görevleri analiz edin",
        "🎨 Yaratıcı projeler için zaman ayırın",
        "💡 Yeni bir beceri öğrenmeye başlayın",
        "🤝 Takım çalışması gerektiren görevleri önceliklendirin"
    ]
    import random
    return random.choice(fallback_suggestions)

def get_cached_suggestion(user_id, task_data_hash):
    """
    Cache'den öneri al
    """
    cache_key = f"ai_suggestion_{user_id}_{task_data_hash}"
    return cache.get(cache_key)

def set_cached_suggestion(user_id, task_data_hash, suggestion):
    """
    Öneriyi cache'le (1 saat)
    """
    cache_key = f"ai_suggestion_{user_id}_{task_data_hash}"
    cache.set(cache_key, suggestion, 3600)  # 1 saat

def generate_smart_prompt(user, incomplete_tasks, completed_tasks):
    """
    Daha akıllı ve kısa prompt oluştur
    """
    prompt_parts = []
    
    # Kullanıcı bilgileri
    prompt_parts.append(f"Kullanıcı: {user.username}")
    
    # Aktif görevler
    if incomplete_tasks.exists():
        active_tasks = [task.title for task in incomplete_tasks[:5]]  # Max 5 görev
        prompt_parts.append(f"Aktif görevler: {', '.join(active_tasks)}")
    
    # Son tamamlanan görevler
    if completed_tasks.exists():
        recent_completed = [task.title for task in completed_tasks[:3]]  # Max 3 görev
        prompt_parts.append(f"Son tamamlananlar: {', '.join(recent_completed)}")
    
    # Kısa ve net istek
    prompt_parts.append("Bu verilere göre 2-3 kısa ve pratik görev önerisi ver. Türkçe ve emoji kullan.")
    
    return "\n".join(prompt_parts)

@login_required
def home(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date_str = request.POST.get('due_date')
        priority = request.POST.get('priority')
        tags = request.POST.getlist('tags')

        try:
            # Tarih formatını doğru şekilde parse et
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            
            # Zaman dilimi bilgisini ekle
            if settings.USE_TZ:
                due_date = timezone.make_aware(due_date, timezone.get_current_timezone())
                
        except ValueError:
            messages.error(request, 'Geçersiz tarih formatı. Lütfen takvimden seçim yapın.')
            return redirect('home')

        try:
            # Görevi oluştur ve kullanıcıya bağla
            task = Task.objects.create(
                user=request.user,
                title=title,
                description=description,
                due_date=due_date,
                priority=priority
            )
            if tags:
                task.tags.set(tags)  # Etiketleri ekle
            messages.success(request, 'Görev başarıyla eklendi!')
        except Exception as e:
            messages.error(request, f'Hata oluştu: {str(e)}')

        return redirect('home')

    # Görevleri getir
    tasks = Task.objects.filter(user=request.user)
    tags = Tag.objects.all()
    # Kanban için görevleri ayır
    todo = tasks.filter(status='pending')
    in_progress = tasks.filter(status='in_progress')
    done = tasks.filter(status='completed')
    return render(request, 'tasks/index.html', {
        'tasks': tasks,
        'tags': tags,
        'todo': todo,
        'in_progress': in_progress,
        'done': done
    })

# Profil Sayfası
@login_required
def profile(request):
    user = request.user
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)

    if request.method == 'POST':
        profile.work_hours = request.POST.get('work_hours')
        profile.sleep_hours = request.POST.get('sleep_hours')
        profile.preferred_task_time = request.POST.get('preferred_task_time')
        profile.save()
        messages.success(request, 'Profil ayarlarınız başarıyla güncellendi!')
        return redirect('profile')

    # Detaylı görev analizlerini hesapla
    completed_tasks = Task.objects.filter(user=user, completed=True)
    total_tasks = Task.objects.filter(user=user)
    pending_tasks = Task.objects.filter(user=user, completed=False)
    
    # Bu hafta tamamlanan görevler
    week_ago = timezone.now() - timedelta(days=7)
    weekly_tasks = Task.objects.filter(
        user=user, 
        completed=True, 
        created_at__gte=week_ago
    ).count()
    
    # Tamamlama oranı
    completion_rate = (len(completed_tasks) / len(total_tasks) * 100) if total_tasks else 0
    
    # Ortalama tamamlama süresi (gün olarak)
    if completed_tasks:
        total_days = 0
        valid_tasks = 0
        for task in completed_tasks:
            if task.due_date and task.created_at:
                try:
                    days_diff = (task.due_date - task.created_at).days
                    if days_diff >= 0:  # Negatif değerleri filtreleme
                        total_days += days_diff
                        valid_tasks += 1
                except:
                    continue
        avg_completion_time = total_days / valid_tasks if valid_tasks > 0 else 0
    else:
        avg_completion_time = 0

    return render(request, 'tasks/profile.html', {
        'profile': profile,
        'completion_rate': completion_rate,
        'avg_completion_time': avg_completion_time,
        'weekly_tasks': weekly_tasks,
        'total_tasks': len(total_tasks),
        'completed_tasks': len(completed_tasks),
        'pending_tasks': len(pending_tasks),
    })

# Görev Analizi
@login_required
def analyze_task(request, task_id):
    # Görevi bul ve sadece mevcut kullanıcının görevlerini analiz et
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    try:
        # Yapay zeka için prompt oluştur
        prompt = (
            f"Aşağıdaki görevi analiz et ve özelleştirilmiş öneriler sun. "
            f"Öneriler, görevin içeriğine ve detaylarına odaklanmalı. "
            f"Genel tavsiyeler verme, sadece görevle ilgili özel öneriler sun. "
            f"Önerileri kısa ve öz tut, her öneri en fazla 1-2 cümle olsun. "
            f"Çıktıda * yıldız işareti kullanma. "
            f"Görev: {task.title}: {task.description}"
        )
        
        # Yapay zeka modelini kullanarak analiz yap - Updated model name
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Yıldız işaretlerini kaldır
        cleaned_response = response.text.replace('*', '')
        
        # JSON formatında cevap döndür
        return JsonResponse({'analysis': cleaned_response})
    
    except Exception as e:
        return JsonResponse({'analysis': f"Analiz yapılırken bir hata oluştu: {str(e)}. Lütfen daha sonra tekrar deneyin."}, status=500)

# Performans Raporu
@login_required
def performance_report(request):
    user = request.user
    completed_tasks = Task.objects.filter(user=user, completed=True)
    total_tasks = Task.objects.filter(user=user)
    
    if not total_tasks:
        return render(request, 'tasks/performance.html', {'report': "Performans analizi için görev bulunamadı."})
    
    completion_rate = len(completed_tasks) / len(total_tasks) * 100 if total_tasks else 0
    
    try:
        prompt = f"Bu verilere dayanarak bir performans raporu oluştur. Raporu maddeler halinde ve Türkçe olarak yaz: Tamamlanan görevler: {len(completed_tasks)}, Toplam görevler: {len(total_tasks)}, Tamamlanma oranı: {completion_rate:.2f}%"
        
        # Updated model name
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        return render(request, 'tasks/performance.html', {'report': response.text})
    except Exception as e:
        return render(request, 'tasks/performance.html', {'report': f"Performans raporu oluşturulurken bir hata oluştu: {str(e)}"})

# Görev Tamamlama
@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = True
    task.status = 'completed'  # Durumu da güncelle
    task.save()
    return redirect('home')



@login_required
def gantt_chart_data(request):
    user = request.user
    tasks = Task.objects.filter(user=user).values('title', 'created_at', 'due_date', 'priority')
    
    # Görevleri JSON formatına dönüştür
    gantt_data = [
        {
            'task': task['title'],
            'start': task['created_at'].strftime('%Y-%m-%d'),
            'end': task['due_date'].strftime('%Y-%m-%d'),
            'priority': task['priority']
        }
        for task in tasks
    ]
    
    return JsonResponse(gantt_data, safe=False)

# AI Destekli Görev Analizi
@login_required
def ai_task_analysis(request):
    """
    Kullanıcının görev geçmişini analiz eder
    """
    user = request.user
    completed_tasks = Task.objects.filter(user=user, completed=True)
    pending_tasks = Task.objects.filter(user=user, completed=False)
    
    if not completed_tasks.exists():
        return JsonResponse({
            'analysis': "📊 Analiz için yeterli veri yok. Birkaç görevi tamamladıktan sonra tekrar deneyin.",
            'source': 'insufficient_data'
        })
    
    # Cache kontrolü
    cache_key = f"ai_analysis_{user.id}_{completed_tasks.count()}"
    cached_analysis = cache.get(cache_key)
    if cached_analysis:
        return JsonResponse({'analysis': cached_analysis, 'source': 'cache'})
    
    try:
        # Analiz için data hazırla
        total_completed = completed_tasks.count()
        total_pending = pending_tasks.count()
        
        # Son 7 gün
        week_ago = timezone.now() - timedelta(days=7)
        weekly_completed = completed_tasks.filter(created_at__gte=week_ago).count()
        
        # Kategori dağılımı
        categories = completed_tasks.values('category__name').annotate(count=Count('id'))
        
        # Analiz prompt'u
        prompt = f"""
        Kullanıcı analizi:
        - Toplam tamamlanan görev: {total_completed}
        - Bekleyen görev: {total_pending}
        - Son 7 günde tamamlanan: {weekly_completed}
        - Kategoriler: {list(categories)}
        
        Bu verilere göre kısa bir performans analizi ve iyileştirme önerisi ver. Türkçe ve emoji kullan.
        """
        
        analysis = call_gemini_with_retry(prompt)
        
        # Cache'le (30 dakika)
        cache.set(cache_key, analysis, 1800)
        
        return JsonResponse({'analysis': analysis, 'source': 'ai'})
        
    except Exception as e:
        fallback = "📈 Düzenli görev tamamlama alışkanlığınızı sürdürün. Başarılısınız!"
        return JsonResponse({'analysis': fallback, 'source': 'fallback', 'error': str(e)})

# AI Destekli Görev Öncelik Belirleme
@login_required
def ai_prioritize_tasks(request):
    """
    Bekleyen görevleri AI ile önceliklendirir
    """
    user = request.user
    pending_tasks = Task.objects.filter(user=user, completed=False)
    
    if not pending_tasks.exists():
        return JsonResponse({
            'priority_suggestion': "🎉 Tüm görevleriniz tamamlanmış! Yeni görev eklemeyi düşünün.",
            'source': 'no_tasks'
        })
    
    cache_key = f"ai_priority_{user.id}_{pending_tasks.count()}"
    cached_priority = cache.get(cache_key)
    if cached_priority:
        return JsonResponse({'priority_suggestion': cached_priority, 'source': 'cache'})
    
    try:
        # Görev listesi hazırla
        task_list = []
        for task in pending_tasks[:10]:  # Max 10 görev
            due_status = "gecikmiş" if task.due_date and task.due_date < timezone.now() else "zamanında"
            task_list.append(f"- {task.title} (Öncelik: {task.get_priority_display()}, {due_status})")
        
        prompt = f"""
        Aşağıdaki görevleri öncelik sırasına göre düzenle:
        {chr(10).join(task_list)}
        
        En önemli 3 görevi seç ve neden öncelikli olduklarını açıkla. Türkçe ve emoji kullan.
        """
        
        priority_suggestion = call_gemini_with_retry(prompt)
        
        # Cache'le (15 dakika)
        cache.set(cache_key, priority_suggestion, 900)
        
        return JsonResponse({'priority_suggestion': priority_suggestion, 'source': 'ai'})
        
    except Exception as e:
        fallback = "🎯 Geciken görevlerinizi ve yüksek öncelikli görevlerinizi önce tamamlamayı düşünün."
        return JsonResponse({'priority_suggestion': fallback, 'source': 'fallback', 'error': str(e)})

# AI Destekli Zaman Tahmini
@login_required
def ai_time_estimate(request):
    """
    Görev için zaman tahmini yapar
    """
    if request.method == 'POST':
        task_title = request.POST.get('title', '')
        task_description = request.POST.get('description', '')
        
        if not task_title:
            return JsonResponse({'estimate': 'Görev başlığı gerekli', 'source': 'error'})
        
        cache_key = f"ai_estimate_{hash(task_title + task_description)}"
        cached_estimate = cache.get(cache_key)
        if cached_estimate:
            return JsonResponse({'estimate': cached_estimate, 'source': 'cache'})
        
        try:
            prompt = f"""
            Görev: {task_title}
            Açıklama: {task_description}
            
            Bu görevin tamamlanması için gereken süreyi tahmin et. Sadece sayı ve birim ver (örn: "2 saat" veya "30 dakika").
            """
            
            estimate = call_gemini_with_retry(prompt)
            
            # Cache'le (1 gün)
            cache.set(cache_key, estimate, 86400)
            
            return JsonResponse({'estimate': estimate, 'source': 'ai'})
            
        except Exception as e:
            fallback = "1-2 saat"
            return JsonResponse({'estimate': fallback, 'source': 'fallback', 'error': str(e)})
    
    return JsonResponse({'estimate': 'POST metodu gerekli', 'source': 'error'})

@login_required
def ai_assistant(request):
    """
    AI Asistan sayfası
    """
    return render(request, 'tasks/ai_assistant.html')

@login_required  
def calendar_view(request):
    """
    Takvim görünümü - dashboard_views.py'den taşındı
    """
    user = request.user
    tasks = Task.objects.filter(user=user)
    
    # Takvim için görev verileri
    calendar_events = []
    for task in tasks:
        # Renk belirleme
        if task.completed:
            color = '#10B981'  # yeşil - tamamlanan
        elif task.due_date and task.due_date < timezone.now():
            color = '#EF4444'  # kırmızı - geciken
        elif task.priority == 1:  # Yüksek öncelik
            color = '#F59E0B'  # sarı - yüksek öncelik
        else:
            color = '#3B82F6'  # mavi - normal
            
        calendar_events.append({
            'title': task.title,
            'start': task.due_date.date() if task.due_date else timezone.now().date(),
            'color': color,
            'completed': task.completed,
            'priority': task.priority
        })
    
    return render(request, 'tasks/calendar.html', {
        'calendar_events': calendar_events
    })

def kanban_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    tasks = Task.objects.filter(user=request.user)
    todo = tasks.filter(status='pending')
    in_progress = tasks.filter(status='in_progress')
    done = tasks.filter(status='completed')
    return render(request, 'tasks/kanban.html', {
        'todo': todo,
        'in_progress': in_progress,
        'done': done
    })