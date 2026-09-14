# Keycan Development Roadmap

Keycan'ın uzun vadeli geliştirme planı.

## ✅ Keycan 2.1.0 — Mevcut Sürüm

- GTK4 + libadwaita modern arayüz
- Flatpak desteği
- Ders ve kaynak sistemi
- Ders grubu arama
- Ayarlar sistemi
- Offline çalışma
- SQLite tabanlı veri yönetimi

---

# ⏳ GUI Yenileme ve Responsive Navigasyon Mimarisi

Amaç: Keycan'ın sade ve kullanıcı dostu çalışma deneyimini korurken, farklı ekran boyutlarında sağlam çalışan ve gelecekteki bölümlerin eklenmesine uygun kalıcı bir navigasyon mimarisi oluşturmak.

## Temel tasarım kuralları

- Mevcut yazma çalışma alanının görünümü ve kullanım mantığı gereksiz yere değiştirilmez.
- Sidebar açıldığında ana çalışma alanının geometrisi ve genişliği değişmez; çalışma alanı fiziksel olarak küçültülmez.
- Sidebar, ana içeriği daraltan kalıcı bir kolon yerine overlay/drawer davranışıyla açılır.
- Küçük ekranlarda sidebar mutlaka overlay olarak çalışır.
- Sidebar kapatıldığında çalışma alanı tamamen erişilebilir ve tam genişlikte kalır.
- Responsive davranışlar sabit piksel ölçülerine bağımlı olmadan GTK4/libadwaita yaklaşımıyla kurulacaktır.
- Ana yazma deneyimi, navigasyon işlemlerinden mümkün olduğunca bağımsız tutulacaktır.

## Navigasyon mimarisi

Sidebar, uygulamanın ana navigasyon alanı olacaktır. Sidebar'ın içinde seçilen bölümün ayrıntılı içeriği gösterilmeyecek; yalnızca navigasyon seçenekleri bulunacaktır.

Başlangıç navigasyonu:

- 🏠 Çalışma Alanı
- ⚙ Ayarlar
- 📊 İstatistikler — ileride
- 👤 Profil — ileride

Gelecekte ihtiyaç duyuldukça yeni bölümler aynı navigasyon yapısına eklenebilir.

## Sayfa davranışı

- 🏠 Çalışma Alanı seçildiğinde mevcut yazma çalışma ekranı gösterilir.
- ⚙ Ayarlar seçildiğinde Ayarlar içeriği ana içerik alanında gösterilir.
- 📊 İstatistikler seçildiğinde ileride İstatistikler sayfası ana içerik alanında gösterilir.
- 👤 Profil seçildiğinde ileride Profil sayfası ana içerik alanında gösterilir.
- Seçilen bölümün içeriği sidebar'ın içine gömülmez.
- Navigasyon ile sayfa içeriği birbirinden ayrılmış olacaktır.

## Responsive sidebar

- GNOME/libadwaita uyumlu sidebar/drawer yaklaşımı kullanılacaktır.
- Geniş ekranlarda sidebar açıldığında çalışma alanı küçültülmeyecektir; panel overlay mantığında çalışacaktır.
- Orta ve küçük ekranlarda sidebar çalışma alanının üzerine açılacaktır.
- Sidebar açılıp kapanırken ders kontrollerinin ve yazma alanının yatay ölçüsü değiştirilmemelidir.
- Farklı çözünürlük ve ölçeklendirme değerlerinde taşma, kırpılma ve kontrol çakışmaları test edilecektir.
- HeaderBar üzerindeki sidebar kontrolü, uygulamanın geri kalan kontrollerinden bağımsız ve tutarlı konumda tutulacaktır.

## Sayfa mimarisi

Her ana bölüm ileride bağımsız bir GUI sayfası/bileşeni olarak geliştirilecektir:

```text
Sidebar navigation
├── 🏠 Çalışma Alanı
├── ⚙ Ayarlar
├── 📊 İstatistikler
└── 👤 Profil

Main content
└── Seçilen sayfanın içeriği
```

Bu yapı, yeni özelliklerin sidebar veya mevcut çalışma alanına gereksiz müdahale yapılmadan eklenmesini sağlayacaktır.

---

# ⏳ Mevcut GUI'nin Stabilizasyonu

Sidebar ve sayfa mimarisi uygulanırken öncelik stabilite olacaktır.

- Mevcut ders/metin seçimi korunacak.
- Ders grubu araması korunacak.
- Mevcut yazma motoruna gereksiz değişiklik yapılmayacak.
- Ayarlar içeriği korunacak; yalnızca yeni sayfa mimarisine taşınacaktır.
- Mevcut sonuç gösterimi korunacak.
- Veritabanı ve ders kaynaklarının içeriği değiştirilmeden GUI çalışması sürdürülecektir.
- Her önemli GUI değişikliğinden önce geri dönüş noktası oluşturulacaktır.

---

# ⏳ Çalışma Alanı Geliştirmeleri

Mevcut kullanıcı dostu çalışma ekranı korunacaktır.

Korunacak yapı:

- Ders grubu / metin / süre kontrolleri
- Kaynak metin alanı
- Kullanıcı yazma alanı
- Alt durum ve metin boyutu kontrolleri
- Mevcut gizlilik davranışı
- Mevcut doğru/yanlış sonuç gösterimi

## Yeni geliştirmeler

- Yazma hızı hesaplama
- Süre sonunda hız bilgisini sonuçlara ekleme
- Doğru, yanlış, toplam kelime ve hız verilerini kaydetme
- Gelecekte Dashboard/İstatistikler için çalışma verisi altyapısı oluşturma

---

# ⏳ Keycan 2.2.x — Kullanıcı Özelleştirme

- Opsiyonel geri tuşu devre dışı bırakma seçeneği
- Kullanıcı veritabanı sistemi
  - Hazır veritabanı dosyası yükleme
  - Uygulama içinden yeni veritabanı oluşturma
  - Veritabanına isim verme
  - Kopyala-yapıştır ile metin ekleme
  - Kullanıcının kendi metnini yazabilmesi

---

# ⏳ Keycan 2.3.x — Kullanıcı İlerlemesi ve İstatistikler

- Çalışma geçmişi
- Günlük/haftalık/aylık istatistikler
- Grafikler
- Toplam kelime, doğru/yanlış analizleri
- Ortalama hız takibi
- Gelişim raporları
- İstatistiklerin ayrı bir navigasyon sayfasında gösterilmesi

---

# ⏳ XP, Seviye ve Rozet Sistemi

- Çalışma performansına göre XP kazanımı
- Seviye sistemi
- Başarı rozetleri
- Düzenli çalışma motivasyonu
- İleride İstatistikler ve Profil sayfalarıyla entegrasyon

---

# ⏳ Profil Sistemi

- Kullanıcı profil sayfası
- Temel kullanıcı bilgileri
- Çalışma özeti
- Seviye ve XP bilgileri
- Başarı rozetleri
- İlerleme verilerinin profille ilişkilendirilmesi

---

# ⏳ Kullanıcı Dostu Geliştirmeler

- Tema sistemi
- Dil sistemi (varsayılan Türkçe, opsiyonel İngilizce)
- Veri yedekleme ve geri yükleme
- Çalışma takvimi
- Odak/Pomodoro modu

---

# 🔮 Keycan 3.0 — Katiplik Sistemi

- Katiplik sınavına yönelik çalışma modu
- Sınav mantığına uygun değerlendirme
- Profesyonel sınav deneyimi

Bu roadmap, kullanıcı geri bildirimleri ve teknik gereksinimler doğrultusunda güncellenebilir. Yeni özellik eklenmeden önce mimari ve stabilite etkisi değerlendirilmelidir.
