# Keycan Geliştirme Yol Haritası

Keycan'ın mevcut durumu ve gelecekteki geliştirme planı.

## 🧭 Aşama Durumu

### ✅ Aşama 0 — Temel Mimari
- GTK4 + libadwaita tabanlı uygulama yapısı
- SQLite tabanlı yerel veri altyapısı
- Temel uygulama ve pencere mimarisi

### ✅ Aşama 1 — Temel Yazma Deneyimi
- On parmak klavye pratiği
- Ders ve metin seçimi
- Ayarlanabilir çalışma süresi
- Doğru / yanlış sonuçları
- Yazma deneyiminin temel ayarları

### ✅ Aşama 2 — İstatistik ve Veri Altyapısı
- SQLite tabanlı çalışma sonuçlarının kaydedilmesi
- Çalışma geçmişi
- Temel istatistikler
- Aktivite verilerinin tutulması

### ✅ Aşama 3 — İçerik ve Veri Yönetimi
- Yerleşik ve özel ders grupları
- Metin ekleme, düzenleme, silme ve sıralama
- Varsayılan içerikleri geri yükleme
- Tüm ders ve metinleri sıfırlama
- İstatistik ve içerik verilerini içe/dışa aktarma
- Kopyala/yapıştır ve metin aktarımı açıklarının engellenmesi

### ✅ Aşama 4 — 2.2.x Bakım ve Hata Düzeltmeleri
Bu aşama yeni bir özellik geliştirme aşaması değildir. Mevcut sürümün kullanımında ortaya çıkan sorunlar ele alınmış ve mevcut 2.2.x sürümü için planlanan bakım çalışmaları tamamlanmıştır.

- Kullanıcı tarafından bildirilen hataların giderilmesi
- Runtime ve kararlılık sorunlarının düzeltilmesi
- Veri kaybına yol açabilecek sorunların giderilmesi
- Gerektiğinde Flatpak ile ilgili sorunların düzeltilmesi
- Mevcut özelliklerin bozulmasını önleyen bakım çalışmaları

Responsive arayüz ve temel stabilizasyon çalışmaları da tamamlanmıştır; ayrı bir gelecek hedefi değildir.

---

## 🔧 Aşama 5 — Gelişmiş İstatistikler

Keycan'ın mevcut istatistik altyapısını daha ayrıntılı bir performans analiz sistemine dönüştürmek.

- Günlük / haftalık / aylık istatistikler
- Uzun dönemli WPM gelişimi
- Uzun dönemli doğruluk gelişimi
- Toplam çalışma süresi
- Toplam kelime / karakter
- Ders bazlı performans
- Ayrıntılı dönem filtreleri
- Dönem karşılaştırmaları
- Rekor geçmişi
- Ayrıntılı performans analizi
- En çok hata yapılan harfleri belirleme

---

## ⏳ Aşama 6 — Kullanıcı Deneyimi

- Tema seçenekleri
- Türkçe / İngilizce dil sistemi

---

## ⏳ Aşama 7 — Profil, XP, Seviye ve Rozet Sistemi

Sidebar'da İstatistikler'den bağımsız, ayrı bir **Profil** bölümü oluşturulacak.

- XP sistemi
- Seviye sistemi
- Seviye ilerlemesi
- Başarı rozetleri
- Çalışma serisi (streak)
- Profil üzerinde XP, seviye, rozet ve streak bilgilerinin gösterilmesi
- Profil sisteminin Aşama 5'teki çalışma ve istatistik verilerinden beslenmesi
- XP, seviye, rozet ve streak bilgilerinin İstatistikler ekranına karıştırılmaması

---

## ⏳ Aşama 8 — Gelişmiş Yerel Profil

Aşama 7'de oluşturulan temel Profil sisteminin daha kapsamlı ve kişiselleştirilebilir hale getirilmesi.

- Kullanıcının kendi ismini girebilmesi
- Profil fotoğrafı seçebilme ve değiştirebilme
- Profil bilgilerinin yerel olarak saklanması
- Profil fotoğrafının yerel olarak saklanması
- Profil özeti
  - Toplam çalışma sayısı
  - Toplam çalışma süresi
  - Genel yazma hızı
  - Genel doğruluk
  - Tamamlanan dersler
  - Genel ilerleme
- Profil üzerinden ilerleme geçmişinin görüntülenmesi
- Profilin mevcut çalışma ve istatistik altyapısıyla bağlantısının genişletilmesi
- Online hesap veya bulut senkronizasyonu olmadan yerel profil yapısının geliştirilmesi

---

## ⏳ Aşama 9 — Klavye Rehberi

Sidebar'da İstatistikler ve Profil'den bağımsız, ayrı bir **Klavye Rehberi** bölümü oluşturulacak.

Kullanıcının 10 parmak yazmayı öğrenmesine yardımcı olan, açıklayıcı ve uygulamaya dönük bir rehber alanı olacak.

- 10 parmak yazma nedir?
- Doğru oturuş ve el pozisyonu
- Başlangıç / home row
- F ve J tuşlarındaki yön bulma çıkıntıları
- Sol el parmaklarının görevleri
- Sağ el parmaklarının görevleri
- Hangi parmağın hangi tuşa bastığı
- Üst sıra, ana sıra ve alt sıra tuşları
- Boşluk tuşu ve başparmak kullanımı
- Klavyeye bakmadan yazma
- Doğruluk ve hız ilişkisi
- Yeni başlayanların sık yaptığı hatalar
- Rehberden öğrenilenleri Çalışma Alanında pratiğe taşıma

---

## 📌 Yol Haritasının Sınırları

Bu roadmap, Keycan'ın mevcut hedeflerini ve onaylanan gelecek geliştirmelerini tanımlar. Aşağıdaki fikirler mevcut roadmap'e dahil değildir:

- Katiplik modu
- Online hesap ve online özellikler
- Bulut senkronizasyonu
- Odak / Pomodoro modu
- Akıllı eğitim / adaptif ders sistemi

Yeni özellikler eklenmeden önce mevcut mimarinin korunması ve kullanıcı geri bildirimlerinin değerlendirilmesi önceliklidir.
