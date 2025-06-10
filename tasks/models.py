from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone

# Etiket Modeli
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Etiket Adı")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Etiket"
        verbose_name_plural = "Etiketler"

# Kategori Modeli
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    color = models.CharField(max_length=7, default="#3B82F6", verbose_name="Renk Kodu")  # Hex color
    icon = models.CharField(max_length=50, default="📋", verbose_name="İkon")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"

# Görev Modeli
class Task(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Yüksek'),
        (2, 'Orta'),
        (3, 'Düşük'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı", null=True)
    title = models.CharField(max_length=200, verbose_name="Başlık")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    due_date = models.DateTimeField(verbose_name="Bitiş Tarihi")
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2, verbose_name="Öncelik")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Durum")
    completed = models.BooleanField(default=False, verbose_name="Tamamlandı")
    estimated_duration = models.DurationField(null=True, blank=True, verbose_name="Tahmini Süre")
    actual_duration = models.DurationField(null=True, blank=True, verbose_name="Gerçek Süre")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="Başlangıç Zamanı")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Bitiş Zamanı")
    notes = models.TextField(blank=True, verbose_name="Notlar")
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True, verbose_name="Dosya Eki")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Etiketler")
    
    def get_priority_display_color(self):
        colors = {1: 'text-red-600', 2: 'text-yellow-600', 3: 'text-green-600'}
        return colors.get(self.priority, 'text-gray-600')
    
    def is_overdue(self):
        return self.due_date < timezone.now() and not self.completed
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date', '-priority']
        verbose_name = "Görev"
        verbose_name_plural = "Görevler"

# Kullanıcı Profili Modeli
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    work_hours = models.IntegerField(default=8, verbose_name="Günlük Çalışma Saati")
    sleep_hours = models.IntegerField(default=8, verbose_name="Günlük Uyku Saati")
    preferred_task_time = models.CharField(max_length=50, verbose_name="Tercih Edilen Görev Zamanı", default="Sabah")

    def __str__(self):
        return self.user.username

# Görev Yorumları
class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name="Yorum")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Görev Yorumu"
        verbose_name_plural = "Görev Yorumları"

# Pomodoro Oturumları
class PomodoroSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=25, verbose_name="Süre (dakika)")
    completed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Pomodoro Oturumu"
        verbose_name_plural = "Pomodoro Oturumları"