# Keycan Mimari İnceleme Raporu

**İnceleme dalı:** `refactor/architecture-roadmap`  
**İnceleme türü:** GitHub kaynak kodu ve test/CI tanımlarının statik incelemesi  
**Durum:** İlk denetim tamamlandı; çalışma zamanı doğrulaması bekliyor.

Bu rapor, mevcut kaynak kodunda görülen somut sorumluluk ve bağımlılıkları kaydeder. Henüz hiçbir uygulama kodu değiştirilmemiştir.

## 1. Başlangıç ve veri dosyası

- `keycan/app.py`, `KeycanWindow` oluşturulmadan önce `database_runtime` ve `statistics_runtime` modüllerini yalnızca import yan etkileri için yüklüyor.
- Varsayılan veritabanı yolu kaynak kodu deposunun kökündeki `typing_data.db` dosyasına sabitlenmiş. Dosya yoksa uygulama başlatılmıyor.
- Bu yaklaşım, veritabanı davranışını import sırasına bağlı hale getiriyor ve kurulu/paketlenmiş uygulamada kullanıcı veri dizini ile paket kaynaklarının ayrılmasını zorlaştırıyor.
- `check.sh` de kökteki `typing_data.db` dosyasını doğrudan açıp şema, içerik ve çalışma geçmişi bütünlüğünü kontrol ediyor. Yeni JSON mimarisi geldiğinde bu kontrolün gerçek kullanıcı veri dizinini ve test veritabanlarını da desteklemesi gerekecek.

## 2. Veritabanı sorumlulukları ve runtime patch

- `keycan/data/database.py` yaklaşık 43.5 KB. Şema migrasyonları, grup/ders CRUD işlemleri, JSON yedek içe/dışa aktarma, çalışma kaydı, istatistik sorguları ve performans sorgularını aynı sınıfta topluyor.
- `keycan/data/database_runtime.py` yaklaşık 43 KB ve `Database` sınıfının `__init__`, `sources`, `lessons`, içerik yönetimi, varsayılanları geri yükleme, içe/dışa aktarma ve ilerleme metotlarını sonradan sınıfa atıyor.
- Bu nedenle `database.py` içindeki bazı metotlar runtime modülü yüklendiğinde gölgeleniyor. Uygulamanın doğru davranışı modülün import edilmesine bağlı.
- Testlerin bir bölümü de `database_runtime` modülünü açıkça import ediyor. Refaktör sırasında bu testleri yeni açık API'ye taşımadan runtime dosyasını silmek mevcut test davranışını bozacaktır.
- Doğru çözüm: davranışları `Database` veya uygun servis/repository sınıflarında gerçek metotlara taşımak; sonra eski patch modülünü kaldırmak.

## 3. Yinelenen GUI modülleri

- `window.py`, `keycan.gui.statistics_clean.StatisticsPanel` kullanıyor. `statistics.py` içinde benzer büyüklükte ikinci bir `StatisticsPanel` uygulaması bulunuyor; aktif pencere bu dosyayı import etmiyor.
- `statistics_runtime.py`, `statistics_clean.MetricCard.set_value` metodunu çalışma zamanında değiştirerek eski animasyon zamanlayıcılarının çakışmasını önlüyor. Bu davranış doğrudan `MetricCard` içine, zamanlayıcı yaşam döngüsünü açıkça yöneten normal bir metoda taşınmalı.
- `window.py`, `settings2.SettingsPanel` kullanıyor. `settings.py` aynı isimli fakat daha basit/eski bir panel ve uyumluluk penceresi içeriyor; aktif pencere tarafından import edilmiyor.
- Bu dosyalar yalnızca benzer göründükleri için hemen silinmemeli. Tüm importlar, testler, olası dış kullanım ve içerik farkları doğrulandıktan sonra tek uygulama seçilmeli.

## 4. Pencere ve iş akışı sorumlulukları

- `keycan/window.py` yaklaşık 38.7 KB ve hem üst seviye pencere/navigasyon hem de çalışma oturumunun önemli bölümünü yönetiyor.
- Aynı sınıfta sayfa yerleşimi, tema/dil uygulaması, ders grubu ve ders yükleme, klavye olayları, metin alanı değişiklikleri, süre sayacı, doğruluk renklendirmesi, oturumun bitirilmesi, kayıt tekrar denemesi ve bekleyen kayıtlarla güvenli kapanış bulunuyor.
- `window.py` şu an veritabanından doğrudan `sources`, `lessons`, `lesson`, `save_result` çağırıyor.
- İlk ayrıştırılacak sorumluluklar: ders seçimi/yükleme ve çalışma oturumu kaydetme akışları. GTK sinyalleri ve widget yaşam döngüsü nedeniyle her çıkarım küçük yapılmalı.
- `TypingEngine` zaten ayrı modülde; bu çalışma boyunca davranışına müdahale edilmeyecek.

## 5. Test ve CI tabanı

- Mevcut testler yazma motoru, temel veritabanı, istatistikler, içerik yönetimi, tercihler, çeviriler ve ilerleme sistemi için ayrı dosyalara sahip.
- `check.sh` sözdizimi derlemesi, canlı `typing_data.db` bütünlük kontrolleri ve seçili testleri çalıştırıyor.
- GitHub Actions; Stage 5, Stage 6, Stage 7 ve tüm testler için regresyon işi içeriyor.
- Bazı CI sözdizimi listeleri yeni/eskimiş dosya adlarına doğrudan bağlı. Modül taşıma veya silme sırasında `check.sh` ve workflow listeleri aynı değişiklikte güncellenmeli.
- Bu inceleme ortamında depo yerel çalışma kopyası olarak mevcut olmadığından Python testleri ve GTK uygulama açılışı henüz çalıştırılmadı. Bu rapordaki bulgular statik incelemeye dayanıyor; dinamik test sonucu gibi yorumlanmamalı.

## 6. Dokümantasyon tutarsızlıkları

- `ROADMAP.md` mevcut aşama 0–9'u tamamlanmış gösteriyor.
- `docs/DEVELOPMENT_PLAN.md` daha eski bir geliştirme sırasını ve tamamlanmamış Stage 3–5 maddelerini anlatıyor.
- `docs/MIGRATION_MAP.md` ve `docs/MIGRATION_PLAN.md` 2.1.0 dönemine ve artık farklılaşmış hedef dosya adlarına dayanıyor.
- `docs/BACKUP_POLICY.md` de 2.1.0'ı güncel kararlı referans olarak belirtiyor.
- Yeni mimari planı tek güncel uygulama kaynağı olmalı. Eski belgeler hemen silinmemeli; yeni planla karşılaştırılıp arşivlenmeli veya açıkça eski oldukları belirtilmeli.

## 7. Önerilen uygulama sırası ve risk kontrolü

1. Önce test tabanını ve gerçek veritabanı içerik sayımlarını kaydet.
2. JSON şemasını ve kararlı kimlik modelini tanımla; mevcut veri üzerinde yalnızca okuma/önizleme yap.
3. Ders servisinin JSON okuma/doğrulama/yazma testlerini SQLite'a dokunmadan oluştur.
4. Eski ders tablolarını JSON'a tek seferlik, tekrarlanabilir ve yedekli biçimde aktar.
5. Çalışma geçmişini ders içeriği dosyalarından bağımsızlaştırmadan eski tabloları kaldırma.
6. Monkey-patch'leri ve yinelenen modülleri davranış testleriyle sırayla kaldır.
7. `window.py` sorumluluklarını küçük adımlarla ayır.
8. Son olarak veri katmanı, paket yolları, CI ve belgeleri birlikte güncelle.

## 8. Aşama 0'ın kalan işleri

- Testleri gerçek proje ortamında çalıştırmak ve sonuçları kaydetmek.
- GTK4/libadwaita uygulamasının açılış, sayfa geçişi ve kapanışını doğrulamak.
- SQLite tablolarının ve ilişkilerinin güncel sayımlarını kaydetmek.
- JSON dışa aktarma dosyasının gerçek içeriğini ve mevcut yedek sözleşmesini doğrulamak.
- Her aktif GUI bileşeninin çağırdığı veritabanı metotlarını tamamıyla eşlemek.

Bu kontroller tamamlanmadan içerik migrasyonuna başlanmayacaktır.
