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
- Ders gruplarını yeniden adlandırma
- Metin ekleme, düzenleme, silme ve sıralama
- Varsayılan içerikleri geri yükleme
- Tüm ders ve metinleri sıfırlama
- İstatistik ve içerik verilerini içe/dışa aktarma
- Kopyala/yapıştır ve metin aktarımı açıklarının engellenmesi

### ✅ Aşama 4 — 2.3.x Bakım ve Hata Düzeltmeleri
Bu aşama yeni bir özellik geliştirme aşaması değildir. 2.2.0 sonrasında kullanıcı tarafından bildirilen kullanım ve kararlılık sorunları giderilmiş, mevcut özelliklerin güvenilirliği artırılmıştır.

- GTK4 widget hiyerarşisi ve yeniden ebeveynleme kaynaklı çökme sorunlarının giderilmesi
- Ders grubu listesinin güvenli biçimde yenilenmesi
- Runtime çeviri backreference hatasının giderilmesi
- Ders grubu yönetiminde yeniden adlandırma akışının iyileştirilmesi
- Mevcut özelliklerin bozulmasını önleyen bakım çalışmaları

Responsive arayüz ve temel stabilizasyon çalışmaları tamamlanmıştır; ayrı bir gelecek hedefi değildir.

---

## ✅ Aşama 5 — Gelişmiş İstatistikler

Keycan'ın mevcut istatistik altyapısını daha ayrıntılı bir performans analiz sistemine dönüştürmek.

- Günlük / haftalık / aylık / yıllık / tüm zamanlar istatistikleri
- Uzun dönemli WPM gelişimi
- Uzun dönemli doğruluk gelişimi
- Toplam çalışma süresi
- Toplam kelime / karakter
- Ders bazlı performans
- Ayrıntılı dönem filtreleri
- İstatistik ekranının Genel, Gelişim, Dersler ve Rekorlar olarak ayrıştırılması
- Dönem karşılaştırmaları
- Rekor geçmişi
- Ayrıntılı performans analizi
- Otomatik istatistik test altyapısı

---

## ✅ Aşama 6 — Kullanıcı Deneyimi

- Sistem / açık / koyu tema seçenekleri
- Tema değişikliğinin anında uygulanması
- Tema tercihinin kalıcı olarak saklanması
- Türkçe / İngilizce dil sistemi
- Dil değişikliğinin uygulama yeniden başlatılmadan anında uygulanması
- Dil tercihinin kalıcı olarak saklanması
- Merkezi ve GTK arayüzünden bağımsız çeviri kataloğu
- Dinamik oluşturulan arayüz metinlerinin çevrilmesi
- Preferences ve translation servislerinin `main.py` dışında tutulması
- Stage 6 otomatik testleri ve CI Python modül doğrulaması
- Atomik preference dosyası yazımı
- GTK4 widget hiyerarşisi ve ders grubu yönetimi kararlılık düzeltmeleri

---

## ✅ Aşama 7 — Profil, XP, Seviye ve Rozet Sistemi

Sidebar'da İstatistikler'den bağımsız, ayrı bir **Profil** bölümü oluşturuldu.

- Yerel ve hesap gerektirmeyen XP sistemi
- Tamamlanan çalışmalardan deterministik XP hesaplama
- XP tabanlı seviye sistemi ve ilerleme çubuğu
- Mevcut ve en uzun çalışma serisinin takibi
- Çalışma sayısı, XP ve ilerleme özeti
- 12 kilometre taşından oluşan başarı rozeti sistemi
- Rozetlerin mevcut çalışma geçmişinden otomatik türetilmesi
- Profil verilerinin SQLite çalışma geçmişinden beslenmesi
- İstatistikler ile profil ilerlemesinin ayrı tutulması
- Türkçe / İngilizce profil arayüzü
- Mevcut GTK4 + libadwaita tasarımına uyumlu profil ekranı
- Stage 7 progression ve persistence davranışları için otomatik testler

---

## ✅ Aşama 8 — Gelişmiş Yerel Profil

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
- Profil üzerinden son çalışma geçmişinin görüntülenmesi
- Profilin mevcut çalışma ve istatistik altyapısıyla bağlantısının genişletilmesi
- Online hesap veya bulut senkronizasyonu olmadan yerel profil yapısının geliştirilmesi

---

## ✅ Aşama 9 — Klavye Rehberi

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

## 🏗️ Aşama 10 — Mimari İyileştirme ve Veri Katmanının Modernizasyonu

Aşama 0–9 ile tamamlanan kullanıcı özellikleri korunarak mevcut mimari kontrollü ve aşamalı biçimde iyileştirilecektir. Bu çalışma yeni özellik geliştirme veya baştan yazım değildir.

**Temel kurallar**
- Yazma motoru (`keycan/core/typing_engine.py`) değiştirilmeyecek.
- Mevcut özellikler, kullanıcı verileri, istatistikler ve profil ilerlemesi korunacak.
- Her aşama test edilmeden sonraki aşamaya geçilmeyecek.
- Büyük ve geri dönüşü zor değişiklikler yerine küçük, izole refaktörler yapılacak.

**Alt aşamalar**
1. **Mimari ve bağımlılık denetimi:** Modül importları, veri akışları, sorumluluklar, test tabanı ve riskler belgelenecek.
2. **JSON ders formatı:** Hazır ders kataloğu JSON'a taşınacak; kullanıcı içerikleri ve hazır içerik düzenlemeleri kullanıcı veri dizinindeki JSON deposunda tutulacak. Şema doğrulama, kararlı kimlikler ve atomik yazım eklenecek.
3. **Ders içeriklerini sadeleştirme:** Grup adları ve ders başlıkları yalnızca Türkçe/İngilizce harfler ve kelime arası boşluk içerecek. Metinlerden sayılar ve noktalama kaldırılacak; Türkçe karakterler korunacak. Önce karşılaştırmalı önizleme ve doğrulama raporu üretilecek.
4. **Ders verisini JSON'a taşıma:** Eski SQLite içeriği kayıpsız dönüştürülecek. Çalışma geçmişi ve profil verileri korunacak; eski tablolar doğrulama tamamlanmadan silinmeyecek.
5. **Yinelenen modüller ve runtime müdahaleleri:** Monkey-patch kullanımı kaldırılacak; yinelenen veritabanı, istatistik ve ayar modülleri import/çağrı analiziyle sadeleştirilecek.
6. **Pencere sorumluluklarını azaltma:** `window.py` yalnızca üst seviye pencere ve koordinasyon görevlerini üstlenecek; bağımsız sorumluluklar mevcut davranış korunarak ayrılacak.
7. **Veritabanı ve servis katmanları:** SQL erişimi GUI'den ayrılacak; şema migrasyonları, transaction, hata yönetimi ve servis sorumlulukları düzenlenecek.
8. **Entegrasyon ve regresyon:** Tam test paketi, CI, GTK açılış/kapanış, JSON geçişi, yedekleme/geri yükleme ve eski verilerle uyumluluk doğrulanacak.

Ayrıntılı uygulama sırası, hedef veri modeli, güvenlik kapıları ve her aşamanın tamamlanma koşulları: [Mimari İyileştirme Yol Haritası](docs/ARCHITECTURE_REFACTOR_ROADMAP.md).

**Durum:** Plan eklendi. İlk olarak mimari ve bağımlılık denetimi yürütülecek.

## 🏁 Mevcut Yol Haritasının Durumu

Aşama 0–9 tamamlandı. Aşama 10, yeni özelliklerden önce mevcut uygulamanın mimarisini, veri yönetimini ve sürdürülebilirliğini iyileştirmeye odaklanır.

## 📌 Yol Haritasının Sınırları

Bu roadmap, Keycan'ın mevcut hedeflerini ve onaylanan gelecek geliştirmelerini tanımlar. Aşağıdaki fikirler mevcut roadmap'e dahil değildir:

- Katiplik modu
- Online hesap ve online özellikler
- Bulut senkronizasyonu
- Odak / Pomodoro modu
- Akıllı eğitim / adaptif ders sistemi

Yeni özellikler eklenmeden önce mevcut mimarinin korunması ve kullanıcı geri bildirimlerinin değerlendirilmesi önceliklidir.
