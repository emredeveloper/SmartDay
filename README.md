# SmartDay

SmartDay, günlük görevlerinizi kolayca yönetebileceğiniz, modern ve kullanıcı dostu bir görev takip uygulamasıdır. Kanban panosu, AI destekli analiz ve önceliklendirme, takvim ve Pomodoro gibi verimlilik araçları içerir.

## Özellikler
- Kanban panosu ile görevlerinizi sürükle-bırak kolaylığında yönetin
- Görevleri durumuna göre (Yapılacaklar, Devam Edenler, Tamamlananlar) ayırın
- "Tamamlandı" butonu ile görevlerinizi hızlıca tamamlayın
- AI ile görev analizi ve akıllı önceliklendirme
- Takvim ve Pomodoro zamanlayıcı desteği

## Kurulum
1. Gerekli paketleri yükleyin:
   ```
   pip install -r requirements.txt
   ```
2. Veritabanı migrasyonlarını çalıştırın:
   ```
   python manage.py migrate
   ```
3. Sunucuyu başlatın:
   ```
   python manage.py runserver
   ```
4. Tarayıcıda `http://localhost:8000/` adresine gidin.

## Giriş (Login)

1. Kayıt olduktan sonra giriş yapmak için ana sayfada veya `/login/` adresinde kullanıcı adı ve şifrenizi girin.
2. Örnek giriş ekranı:

```
Kullanıcı Adı: demo
Şifre: demo12345
```

> Not: İlk kez giriş yapacaksanız önce kayıt olmanız gerekir. Kayıt için `/register/` adresini kullanabilirsiniz.
