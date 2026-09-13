# Keycan ⌨️

Keycan, Linux masaüstü sistemleri için geliştirilmiş modern ve kullanıcı dostu bir **on parmak klavye pratik uygulamasıdır**.

Keycan ile farklı ders gruplarındaki metinleri seçebilir, çalışma süresini belirleyebilir ve yazma pratiği yapabilirsiniz. Uygulama temel kullanımda çevrimdışı çalışır ve verileri yerel SQLite veritabanında tutar.

## 🚀 Geliştirme Yol Haritası

Keycan'ın uzun vadeli hedefleri:

### ✅ Keycan 2.1.0

- GTK4 + libadwaita modern arayüz
- Flatpak desteği
- Ders ve kaynak sistemi
- Ders grubu arama
- Ayarlar sistemi
- Offline çalışma
- SQLite tabanlı veri yönetimi

### ⏳ Keycan 2.2.x — Kullanıcı Özelleştirme

- Opsiyonel geri tuşu devre dışı bırakma seçeneği
- Kullanıcı veritabanı desteği
  - Hazır veritabanı yükleme
  - Uygulama içinden yeni veritabanı oluşturma
  - Veritabanına isim verme
  - Kopyala-yapıştır ile içerik ekleme
  - Kullanıcının kendi derslerini oluşturabilmesi

### ⏳ Keycan 2.3.x — Dashboard ve İlerleme Sistemi

- Kullanıcı çalışma geçmişi
- Günlük/haftalık/aylık grafikler
- Toplam kelime, doğru ve yanlış analizleri
- Çalışma süresi takibi
- Kullanıcı gelişim raporları

### ⏳ XP, Seviye ve Rozet Sistemi

- Çalışma performansına göre XP kazanımı
- Seviye sistemi
- Başarı rozetleri
- Kullanıcının gelişimini takip eden motivasyon sistemi

### ⏳ Kullanıcı Dostu Geliştirmeler

- Tema sistemi
- Veri yedekleme ve geri yükleme
- Çalışma takvimi
- Odak/Pomodoro modu
- Kullanıcı profili

### 🔮 Keycan 3.0 — Katiplik Sistemi

- Katiplik sınavına yönelik özel çalışma modu
- Sınav mantığına uygun değerlendirme sistemi
- Profesyonel sınav deneyimi

Detaylı roadmap için: [ROADMAP.md](ROADMAP.md)

## ✨ Özellikler

- **On Parmak Klavye Pratiği** — Kelime ve cümlelerden oluşan ders metinleriyle pratik.
- **Ders ve Metin Seçimi** — Kaynaklara göre düzenlenmiş ders grupları.
- **Ders Grubu Arama** — Ders grubu adları içinde arama yaparak istediğiniz kaynağa hızlıca ulaşabilirsiniz.
- **Ayarlanabilir Süre** — Çalışma süresi 1–180 dakika arasında seçilebilir.
- **Doğru / Yanlış Sonuçları** — Süre sonunda yazılan kelimeler sonuç olarak renklendirilir.
- **Büyük/Küçük Harf Bağımsızlığı** — Kelime karşılaştırmasında harf büyüklüğü önemsenmez.
- **Noktalama İşaretlerini Yok Sayma** — Kelime eşleştirmesinde noktalama işaretleri zorunlu değildir.
- **Karışık Sırada Yazma** — Kelimelerin metindeki sırasını takip etmek zorunlu değildir.
- **Metin Boyutu** — Ders ve yazma alanlarının yazı boyutu ayarlanabilir.
- **Yazım Metnini Karart** — Yazarken kendi yazdığınız metni gizleyerek yalnızca hedef metne odaklanabilirsiniz.
- **Yerel SQLite Veritabanı** — Dersler ve çalışma sonuçları yerel olarak saklanır.
- **Çevrimdışı Kullanım** — Temel uygulama kullanımı internet bağlantısı gerektirmez.
- **GTK4 + libadwaita** — Modern Linux masaüstü arayüzü.
- **Flatpak** — Linux dağıtımları için izole ve taşınabilir paketleme.

## 🛠️ Teknolojiler

- Python
- GTK4
- libadwaita
- PyGObject
- SQLite
- Flatpak
- GNOME Platform 50
