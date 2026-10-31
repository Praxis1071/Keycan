# Keycan Geliştirme Yol Haritası

Keycan'ın mevcut durumu ve onaylanan mimari iyileştirme planı.

## 🧭 Tamamlanan Aşamalar

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
- GTK4 widget hiyerarşisi ve yeniden ebeveynleme kaynaklı çökme sorunlarının giderilmesi
- Ders grubu listesinin güvenli biçimde yenilenmesi
- Runtime çeviri backreference hatasının giderilmesi
- Ders grubu yönetiminde yeniden adlandırma akışının iyileştirilmesi
- Mevcut özelliklerin bozulmasını önleyen bakım çalışmaları

### ✅ Aşama 5 — Gelişmiş İstatistikler
- Günlük / haftalık / aylık / yıllık / tüm zamanlar istatistikleri
- Uzun dönemli WPM ve doğruluk gelişimi
- Toplam çalışma süresi, kelime ve karakter
- Ders bazlı performans ve dönem filtreleri
- İstatistik ekranının Genel, Gelişim, Dersler ve Rekorlar olarak ayrıştırılması
- Dönem karşılaştırmaları, rekor geçmişi ve performans analizi
- Otomatik istatistik test altyapısı

### ✅ Aşama 6 — Kullanıcı Deneyimi
- Sistem / açık / koyu tema seçenekleri
- Tema değişikliğinin anında uygulanması ve kalıcı saklanması
- Türkçe / İngilizce dil sistemi
- Dil değişikliğinin yeniden başlatma gerektirmeden uygulanması
- Merkezi çeviri kataloğu
- Preferences ve translation servislerinin ana uygulama dosyasından ayrılması
- Otomatik testler, CI doğrulaması ve atomik preference yazımı

### ✅ Aşama 7 — Profil, XP, Seviye ve Rozet Sistemi
- Yerel XP ve seviye sistemi
- Çalışma serilerinin takibi
- Başarı rozetleri
- Profil ilerlemesinin SQLite çalışma geçmişinden beslenmesi
- Türkçe / İngilizce profil arayüzü ve otomatik testler

### ✅ Aşama 8 — Gelişmiş Yerel Profil
- Kullanıcı adı ve profil fotoğrafı
- Profil bilgilerinin yerel saklanması
- Çalışma, süre, hız, doğruluk ve ders ilerleme özeti
- Son çalışma geçmişi
- Online hesap veya bulut senkronizasyonu olmadan yerel profil

### ✅ Aşama 9 — Klavye Rehberi
- On parmak yazma, doğru oturuş ve el pozisyonu
- Başlangıç sırası ve parmak görevleri
- Klavye sıraları ve boşluk tuşu kullanımı
- Klavyeye bakmadan yazma, doğruluk ve hız
- Yaygın başlangıç hataları ve pratik yönlendirmesi

---

## 🚧 Aşama 10 — Mimari İyileştirme ve Ders İçeriği Yenileme

Bu aşamanın amacı mevcut Keycan özelliklerini koruyarak kod tabanını sadeleştirmek, ders içeriklerini yönetilebilir JSON dosyalarına taşımak ve veri sorumluluklarını netleştirmektir. Büyük çaplı yeniden yazım yapılmayacaktır.

### 10.1 — Mimari ve bağımlılık analizi
- [ ] Tüm modüllerin sorumluluklarını, import ilişkilerini ve çalışma zamanındaki bağımlılıklarını çıkarmak
- [ ] Uygulama başlangıç akışını ve veritabanı başlatma/migration sırasını belgelemek
- [ ] GUI, servis, veri erişimi ve yazma motoru sınırlarını belirlemek
- [x] Mevcut testleri ve CI kontrollerini başlangıç referansı olarak çalıştırmak (yedek geri yükleme regresyonu düzeltildi; tam CI paketi geçti)
- [ ] Kullanılmayan, yinelenen veya eski dosyaları import ve davranış kanıtı olmadan silmemek
- [ ] Yazma motorunu kapsam dışında tutmak; mevcut API ve davranışını değiştirmemek

### 10.2 — JSON ders kataloğu ve içerik temizliği
- [x] Ders kataloğu için sürümlenmiş, doğrulanabilir bir JSON şeması tanımlamak (şema sürüm 1)
- [ ] Hazır ders gruplarını ve ders metinlerini JSON kaynaklarına taşımak
- [ ] Uygulama içi erişimi tek bir lesson service üzerinden sağlamak
- [x] Grup adlarını Türkçe/İngilizce harfler ve kelime boşlukları dışında karakter içermeyecek şekilde sadeleştirmek
- [x] Hazır ders metinlerinden sayıları ve noktalama işaretlerini temizlemek; Türkçe karakterleri korumak
- [ ] Metinleri temizlerken kelime sırasını, anlamı, seviye akışını ve tekrarları kontrol etmek
- [x] Boş, yinelenen veya bozulmuş dersleri otomatik doğrulamalarla tespit etmek (boş ders yok; temizleme sonrası iki tekrar korunarak raporlandı)
- [ ] Kullanıcı tarafından oluşturulan ders içeriğinin saklama biçimini ayrıca ele almak; mevcut özel içerikleri kayıpsız taşımadan eski kaynağı kaldırmamak
- [ ] JSON okuma hatalarında uygulamanın çökmesini önlemek ve anlaşılır hata bildirimi sağlamak

### 10.3 — JSON yedekleme ve veri geçişi
- [ ] Ders kataloğu, kullanıcı içeriği ve kullanıcı çalışma verilerinin sınırlarını tanımlamak
- [ ] JSON dışa aktarma/içe aktarma biçimini sürümlendirmek
- [ ] Yedeklerde kimlikleri ve çalışma geçmişi bağlantılarını korumak
- [ ] Tekrarlı içe aktarmanın mükerrer kayıt oluşturmamasını sağlamak
- [ ] İçe aktarmayı doğrulama ve işlem/geri alma güvenliğiyle gerçekleştirmek
- [ ] Eski SQLite verileri için geriye dönük, kayıpsız geçiş yolu ve yedek oluşturmak
- [ ] Eski veri biçimleriyle uyumluluk testleri eklemek

### 10.4 — Yinelenen modüller ve runtime müdahaleleri
- [ ] `database.py` / `database_runtime.py` sorumluluklarını karşılaştırmak
- [ ] `statistics.py`, `statistics_clean.py` ve `statistics_runtime.py` kullanımını doğrulamak
- [ ] `settings.py` / `settings2.py` kullanımını doğrulamak
- [ ] Monkey-patching yerine açık sınıf/metot veya bağımlılık enjeksiyonu kullanmak
- [ ] Tekrarlanan kodu birleştirmek; kullanılmayan eski modülleri ancak tüm referanslar temizlendikten sonra kaldırmak
- [ ] Uygulama başlatma sırasını sadeleştirmek

### 10.5 — Pencere ve GUI sorumlulukları
- [ ] `window.py` içindeki sayfa oluşturma, olay yönetimi ve iş mantığını ayırmak
- [ ] Mevcut sayfa ve widget modüllerini ihtiyaç oldukça düzenlemek
- [ ] GUI katmanının doğrudan SQL ve JSON ayrıntılarıyla uğraşmasını önlemek
- [ ] Sadece gerçek sorumluluk ayrımı sağlayan modüller oluşturmak; gereksiz soyutlama eklememek
- [ ] Görsel tasarımı ve kullanıcı akışını değiştirmeden refactor yapmak

### 10.6 — Veritabanı ve servis katmanı
- [ ] SQLite'ı çalışma geçmişi, istatistik, profil ve diğer ilişkisel kullanıcı verileri için korumak
- [ ] Veri erişimini GUI'den ayırmak ve sorguları ilgili repository/data katmanında toplamak
- [ ] Servislerin iş kurallarını yönetmesini, repository katmanının kalıcı veri erişimini yönetmesini sağlamak
- [ ] Şema migration'larını açık, test edilebilir ve geriye dönük güvenli hale getirmek
- [ ] Veritabanı açılışında dosyanın varlığına gereksiz bağımlılığı kaldırma seçeneğini incelemek; ilk kurulum davranışını güvenli tasarlamak

### 10.7 — Doğrulama ve tamamlanma kapısı
- [ ] Her alt aşamadan önce ve sonra otomatik testleri çalıştırmak
- [ ] Ders seçimi, çalışma başlatma/tamamlama, özel içerik CRUD, istatistik, profil, ayarlar ve çevirileri regresyon testleriyle doğrulamak
- [ ] JSON şema, içerik temizliği, içe/dışa aktarma ve migration testleri eklemek
- [ ] Uygulama başlangıcı ve temel GTK arayüz akışını kontrol etmek
- [ ] Veri kaybı, geçmiş eşleşme bozulması veya yazma motoru davranış farkı varsa aşamayı tamamlanmış saymamak
- [ ] Her alt aşamayı ayrı ve geri alınabilir commitlerle ilerletmek
- [ ] Son aşamada eski ve kullanılmayan kodu kaldırmadan önce referans taraması ve tam test yapmak

### Aşama 10 uygulama stratejisi
1. Önce mevcut davranışın testlerle referansını al; hiçbir dosyayı varsayımla silme.
2. Önce JSON şeması, katalog okuyucusu ve doğrulama testlerini ekle; ardından içerikleri dönüştür.
3. JSON ve SQLite arasında geçici uyumluluk katmanı kur; uygulama çalışırken tek seferde veri kaynağını değiştirme.
4. Kullanıcı içerikleri ve çalışma geçmişini kimlik eşlemesiyle taşı; yedek doğrulanmadan eski veriyi silme.
5. Yinelenen modülleri küçük adımlarla birleştir; her adımda import ve regresyon testlerini çalıştır.
6. GUI refactor'ını veri katmanı istikrarlı hale geldikten sonra yap.
7. Her alt aşama sonunda değişiklik özeti, test sonuçları ve kalan riskleri kaydet.

**Kapsam dışı:** `keycan/core/typing_engine.py` üzerinde özellik, algoritma, performans veya mimari değişikliği yapılmayacaktır. Yalnızca mevcut testleri çalıştırılarak davranışının korunduğu doğrulanacaktır.

## 📌 Yol Haritasının Sınırları
- Katiplik modu
- Online hesap ve online özellikler
- Bulut senkronizasyonu
- Odak / Pomodoro modu
- Akıllı eğitim / adaptif ders sistemi
- Gerçek performans darboğazı ölçülmeden Rust veya başka bir dil eklenmesi

Yeni özelliklerden önce mevcut mimarinin korunması, veri güvenliği ve bakım kolaylığı önceliklidir.
