# Keycan — Güncel Mimari Denetim Raporu

**Denetim tarihi:** 2026-11-01  
**İncelenen dal:** `architecture/maintenance-refactor` (başlangıç noktası: main)  
**Temel sürüm:** v2.5.0  
**Denetim türü:** GitHub kaynak kodu, mevcut mimari belgeler, test tanımları ve GitHub Actions sonuçlarının statik incelemesi  
**Durum:** Statik denetim ve ilk iki refactor adımı branch üzerinde uygulandı; yerel GTK masaüstü doğrulaması ayrıca yapılmalı.

Bu rapor, güncel main dalına göre önceki mimari raporundaki eski dal ve test bilgilerini düzeltir. Kaynak kodu üzerinden görülebilen durum ile masaüstünde gerçekten çalıştırılması gereken kontroller birbirinden ayrı tutulur.

## 1. Genel mimari

Keycan; Python, GTK4 ve libadwaita tabanlı Linux masaüstü uygulamasıdır. Ana giriş noktası main.py üzerinden keycan.app.main() akışına gider. Kod tabanında GUI, core, data, services, resources ve utils sorumlulukları için ayrılmış modüller vardır.

Mevcut klasör ayrımı yararlı bir başlangıçtır. Öncelikli sorun yeni klasörler eklemek değil; mevcut sınıfların sorumluluklarını, veri sahipliğini ve geçiş/uyumluluk sınırlarını açık hâle getirmektir.

## 2. Ders kataloğu ve kalıcı veri sınırları

Güncel ve onaylanmış yaklaşım:

- Paketlenmiş varsayılan ders kataloğu: keycan/resources/lessons/ altında sürümlenmiş JSON.
- GUI'nin hazır katalog okuma sınırı: LessonService.
- Kullanıcı tarafından oluşturulan gruplar, düzenlenebilir içerik, sıralama/silme durumu ve kişisel değişiklikler: mevcut SQLite tabanlı model.
- Yazma oturumları, istatistik girdileri, profil ilerlemesi ve çalışma geçmişi: SQLite.
- JSON yedekleme: canlı veri deposu değil; sürümlü dışa aktarma/geri yükleme sözleşmesi.

Kullanıcı içeriğini JSON'a taşıma kararı alınmış değildir. Bu yönde bir migrasyon, ancak mevcut SQLite modelinin yetersizliği kanıtlanır ve ayrı tasarım/güvenlik kapısından geçerse gündeme alınabilir.

## 3. Veritabanı sınıf sınırı

- `database.py` temel `Database` sınıfını, şema migrasyonlarını ve istatistik/oturum sorgularını içerir.
- Önceki uygulama yolu, `database_runtime.py` içindeki kayıt fonksiyonuyla metotları çalışma anında `Database` sınıfına atıyordu. Bu yöntem kaldırıldı.
- Yeni `ManagedDatabase`, temel `Database` sınıfından türeyen açık bir alt sınıftır. İçerik CRUD, varsayılan içerik snapshot/restore, ilerleme özeti ve JSON yedekleme davranışları bu uygulama sınıfında sunulur.
- `app.py` artık kayıt fonksiyonu çağırmaz; pencere doğrudan `ManagedDatabase` kullanır.
- `LessonService` tür sözleşmesi de `ManagedDatabase` API'sini açıkça belirtir.
- Temel `Database` sınıfı, `database_runtime.py` import edildiğinde değişmez. Bu davranış alt süreç regresyon testiyle doğrulanır.

`managed_database.py` içindeki uygulama işlemleri artık `ManagedDatabase` sınıfında normal metotlar olarak tanımlıdır; sınıf gövdesinde sonradan fonksiyon ataması veya runtime monkey-patch yoktur. Eski `database_runtime.py` yalnızca uyumluluk dışa aktarımıdır.
## 4. Ders kataloğu servisi

- Paketlenmiş Türkçe katalog JSON olarak bulunur.
- LessonService, katalog içeriği ile SQLite'taki kullanıcı tarafından değiştirilmiş değerler arasında uyumluluk sınırı sağlar.
- GUI'nin katalog JSON dosyasını doğrudan okuması hedeflenmez.
- Katalog bulunamaz veya geçersiz olursa uygulamanın açılışını engellemeyen fallback davranışı ve kullanıcıya durum bildirimi bulunur.
- Hazır içerik kimlikleri ve sıralaması geçmiş kayıtları etkilemeyecek şekilde korunmalıdır.

Katalog doğrulaması, yinelenen kimlikler, bozuk kaynak, eksik kaynak ve kullanıcı tarafından yeniden adlandırılmış/düzenlenmiş içerik senaryoları testlerle korunmalıdır.

## 5. GUI ve pencere sorumlulukları

- `window.py` ana pencere, sayfa navigasyonu, ders seçimi ve yazma oturumu yaşam döngüsünü koordine eder. Üretim penceresi artık `_BaseKeycanWindow` üzerine açık `KeycanWindow` sınıfı olarak kuruludur; runtime sınıf alias'ı ve yinelenen kaynak yükleme metotları kaldırılmıştır.
- Bu dosyanın sorumluluklarını azaltmak mantıklıdır; ancak GTK sinyalleri, widget yaşam döngüsü, zamanlayıcılar ve kapanışta bekleyen kayıtlar nedeniyle büyük bir yeniden yazım yapılmamalıdır.
- Ana pencerenin CSS, widget yerleşimi ve tercih popover'ı `gui/window_layout.py` içine taşındı; `window.py` yaklaşık 850 satırdan 585 satıra küçüldü.
- Kelime/karakter/doğruluk ölçümleri ve kayıt payload'ı GTK penceresinden `core/session_metrics.py` içine taşındı.
- Editörün gizlilik görünümü, sonuç renklendirme ve metin buffer sunumu `gui/workspace.py` sorumluluğuna alındı. Pencere bu işlemleri workspace API'si üzerinden çağırır.
- Oturum başlatma, zamanlayıcı, GTK buffer'ın oturum sonunda okunması ve kapanışta bekleyen kayıt uyarısı hâlâ pencerededir. Veritabanına kaydetme ve başarısız kayıt kuyruğunu yeniden deneme `services/session_recorder.py` tarafından yönetilir.
- Sonraki ayrıştırma adayları ders seçimi/yükleme ve çalışma oturumu yaşam döngüsüdür.
- Yalnızca gerçek ve bağımsız sorumluluklar için yeni sınıf/servis oluşturulmalıdır.

## 6. Yinelenen modüller

- Aktif GUI uygulaması settings2.py ve statistics_clean.py modüllerini kullanır.
- settings.py ve statistics.py artık aktif settings2.py ve statistics_clean.py modüllerine yönlendiren küçük uyumluluk dışa aktarımlarıdır; yinelenen uygulama kodu kaldırılmıştır.
- statistics_runtime.py içindeki eski MetricCard müdahalesi aktif uygulama yolundan çıkarılmış, davranış MetricCard içine taşınmıştır.
- database_runtime.py yalnızca managed_database.py içindeki sınıfı dışa aktaran küçük bir uyumluluk modülüdür.

## 7. Test ve CI durumu

- GitHub Actions iş akışı Stage 5, Stage 6, Stage 7 ve tam regresyon kontrollerini içerir.
- Stabilizasyon PR #2 (fix/stabilization-kc-001-005) 2026-10-31 tarihinde main dalına birleştirilmiştir.
- PR doğrulama açıklamasında 45 testin geçtiği ve Stage 5, Stage 6, Stage 7 ile tam regresyon işlerinin başarılı olduğu bildirilmiştir.
- Bu raporun hazırlanması sırasında main üzerindeki 2026-11-01 dokümantasyon commit'inin GitHub Actions çalışması da başarılı sonuçlanmıştır.
- Bu CI sonuçları, GTK masaüstü etkileşimlerinin elle test edildiği anlamına gelmez.

## 8. Stabilizasyon kaydıyla ilişki

KC-001–KC-005 düzeltmeleri main'e alınmıştır. Ayrıntılı hata geçmişi ve manuel doğrulama notları [ERRORS.md](../ERRORS.md) dosyasında tutulur.

Özellikle gizlilik modu, fotoğraf seçme/kaldırma ve canlı dil değişimi gibi GTK arayüz akışlarının gerçek masaüstünde kullanıcı tarafından kontrol edilmesi gerekir. Otomatik testlerin geçtiği durumlarda bile bu manuel kontroller tamamlanmış gibi işaretlenmemelidir.

## 9. Öncelikli mimari riskler

1. `window.py` dosyasının oturum zamanlaması, GTK yaşam döngüsü ve kapanış koordinasyonunu da yönetmesi; kayıt kuyruğu artık `SessionRecorder` servisindedir.
2. Veritabanı taban sınıfı ile uygulama alt sınıfındaki tarihsel/örtüşen CRUD API'lerinin uyumluluk sınırlarının belgelenmesi.
3. GTK masaüstü etkileşimlerinin otomatik Xvfb smoke testi ve kullanıcının gerçek masaüstü denemesiyle doğrulanması.
4. JSON katalog, SQLite kullanıcı içeriği ve JSON yedekleme rollerinin dokümantasyonda karıştırılma riski.
5. Flatpak veri yolu, ilk kurulum/var olan kullanıcı verisi geçişi ve yedek geri yükleme senaryolarının her sürümde regresyon testine ihtiyaç duyması.

## 10. Sonraki adım ve kapsam sınırı

Runtime sınıf mutasyonu kaldırılmış, managed veritabanı davranışları normal alt sınıf metotlarına dönüştürülmüş ve eski import yolları uyumluluk dışa aktarımlarıyla korunmuştur. Saf oturum ölçümleri `core/session_metrics.py` içine; editör gizliliği ve sonuç renklendirme ise `gui/workspace.py` içine ayrılmıştır. CI'da 52 depo kontrolü, 72 pytest testi ve Ruff F821 denetimi başarıyla tamamlanmıştır. GTK/Xvfb smoke testi son layout ayrıştırmasından sonra da başarılıdır. GTK/Xvfb smoke testi başarılı: pencere ve sayfalar oluşturuldu; içerik yöneticisi açıldı; gizlilik etiketi ve canlı dil değişimi kontrol edildi; örnek yazım oturumu SQLite'a kaydedildi, başarısız kayıt yeniden denendi ve aynı oturum kimliğiyle tek kayıt doğrulandı; sonuç mesajı kontrol edildi. Beş CI işi de başarılı. `SessionRecorder` başarısız kayıtları sabit oturum kimliğiyle kuyruğa alıp yeniden dener; birim ve GTK smoke testleri bu akışı doğrular.

Bu çalışma sırasında:

- keycan/core/typing_engine.py davranışı değiştirilmeyecek.
- Kullanıcı veritabanı üzerinde doğrudan deney yapılmayacak; testler geçici kopyalar kullanacak.
- Kullanıcı içeriği SQLite'tan JSON'a taşınmayacak.
- Eski modüller, tablolar veya dosyalar yalnızca isim benzerliği nedeniyle silinmeyecek.
- GTK çalışma zamanı testi yapılmadıysa bu açıkça raporlanacak.
