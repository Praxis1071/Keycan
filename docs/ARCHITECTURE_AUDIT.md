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

**Kalan iş:** `database_runtime.py` içindeki modül düzeyi fonksiyonlar hâlâ alt sınıf metotlarına bağlanır. Bunları okunabilir sınıf metotlarına veya uygun repository/service bileşenlerine taşımak sonraki, ayrı bir sadeleştirme adımıdır.
## 4. Ders kataloğu servisi

- Paketlenmiş Türkçe katalog JSON olarak bulunur.
- LessonService, katalog içeriği ile SQLite'taki kullanıcı tarafından değiştirilmiş değerler arasında uyumluluk sınırı sağlar.
- GUI'nin katalog JSON dosyasını doğrudan okuması hedeflenmez.
- Katalog bulunamaz veya geçersiz olursa uygulamanın açılışını engellemeyen fallback davranışı ve kullanıcıya durum bildirimi bulunur.
- Hazır içerik kimlikleri ve sıralaması geçmiş kayıtları etkilemeyecek şekilde korunmalıdır.

Katalog doğrulaması, yinelenen kimlikler, bozuk kaynak, eksik kaynak ve kullanıcı tarafından yeniden adlandırılmış/düzenlenmiş içerik senaryoları testlerle korunmalıdır.

## 5. GUI ve pencere sorumlulukları

- window.py ana pencere, navigasyon ve çalışma alanı koordinasyonunun yanında ders seçimi ve yazma oturumu yaşam döngüsünün önemli bölümünü yönetir.
- Bu dosyanın sorumluluklarını azaltmak mantıklıdır; ancak GTK sinyalleri, widget yaşam döngüsü, zamanlayıcılar ve kapanışta bekleyen kayıtlar nedeniyle büyük bir yeniden yazım yapılmamalıdır.
- İlk ayrıştırma adımı olarak kelime/karakter/doğruluk ölçümleri ve kayıt payload'ı GTK penceresinden çıkarılarak `core/session_metrics.py` içine taşındı. Oturum başlatma, zamanlayıcı, GTK buffer okuma ve kapanışta bekleyen kayıt yönetimi hâlâ pencerededir.
- Sonraki ayrıştırma adayları ders seçimi/yükleme ve çalışma oturumu yaşam döngüsüdür.
- Yalnızca gerçek ve bağımsız sorumluluklar için yeni sınıf/servis oluşturulmalıdır.

## 6. Yinelenen modüller

- Aktif GUI uygulaması settings2.py ve statistics_clean.py modüllerini kullanır.
- settings.py ve statistics.py eski/alternatif uygulamalar olarak depoda tutulmaktadır; silinmeden önce import, test, paketleme ve olası uyumluluk referansları aranmalıdır.
- statistics_runtime.py içindeki eski MetricCard müdahalesi aktif uygulama yolundan çıkarılmış, davranış MetricCard içine taşınmıştır.
- database_runtime.py ise hâlâ önemli uyumluluk davranışları içerir ve ayrı ele alınmalıdır.

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

1. `window.py` dosyasının pencere koordinasyonunun ötesinde çalışma oturumu ve ders akışlarını da yönetmesi.
2. `managed_database.py` içindeki alt sınıf metotlarının hâlâ modül düzeyindeki fonksiyonlara bağlanması.
3. Eski/aktif settings ve statistics modüllerinin çiftlerinin bulunması.
4. JSON katalog, SQLite kullanıcı içeriği ve JSON yedekleme rollerinin dokümantasyonda karıştırılma riski.
5. Flatpak veri yolu, ilk kurulum/var olan kullanıcı verisi geçişi ve yedek geri yükleme senaryolarının her sürümde regresyon testine ihtiyaç duyması.

## 10. Sonraki adım ve kapsam sınırı

İlk uygulama adımı olarak runtime sınıf mutasyonu kaldırılmış ve `ManagedDatabase` alt sınıfına geçilmiştir. Branch CI doğrulaması `check.sh` için 52 kontrolü ve tam pytest paketi için 70 testi başarıyla tamamlamıştır. `window.py` içindeki saf oturum ölçüm hesaplamaları `core/session_metrics.py` içine ayrılmıştır. Sonraki adım, GTK buffer/zamanlayıcı/kapanış yaşam döngüsünü koruyarak oturum koordinasyonunu ve ders yükleme akışını daha küçük bileşenlere ayırmak; ayrıca eski GUI modüllerinin kullanımını kesinleştirmektir.

Bu çalışma sırasında:

- keycan/core/typing_engine.py davranışı değiştirilmeyecek.
- Kullanıcı veritabanı üzerinde doğrudan deney yapılmayacak; testler geçici kopyalar kullanacak.
- Kullanıcı içeriği SQLite'tan JSON'a taşınmayacak.
- Eski modüller, tablolar veya dosyalar yalnızca isim benzerliği nedeniyle silinmeyecek.
- GTK çalışma zamanı testi yapılmadıysa bu açıkça raporlanacak.
