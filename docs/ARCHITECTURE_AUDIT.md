# Keycan — Güncel Mimari Denetim Raporu

**Denetim tarihi:** 2026-11-01  
**İncelenen dal:** main  
**Temel sürüm:** v2.5.0  
**Denetim türü:** GitHub kaynak kodu, mevcut mimari belgeler, test tanımları ve GitHub Actions sonuçlarının statik incelemesi  
**Durum:** Statik denetim güncellendi; yerel GTK masaüstü doğrulaması ayrıca yapılmalı.

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

## 3. Veritabanı runtime uyumluluk katmanı

- database.py temel şema, migrasyon ve veritabanı davranışlarını içerir.
- database_runtime.py hâlâ bazı Database davranışlarını açık bir kayıt fonksiyonu üzerinden sınıfa ekleyen geçiş/uyumluluk katmanıdır.
- Önceki raporda belirtildiği gibi bunun yalnızca import yan etkisiyle çalıştığı ifadesi artık güncel değildir: kayıt açıkça yapılmaktadır.
- Buna rağmen metotların iki dosya arasında bölünmüş olması ve sınıf davranışının kayıt sırasına bağlı kalması hâlâ mimari borçtur.
- database_runtime.py kaldırılmadan önce her metot, çağrı noktası, test ve yan etki karşılaştırılmalıdır.

**Öneri:** Kayıt mekanizmasını hemen silme. Önce metotları tek tek gerçek sınıf metotlarına veya gerekli servis/repository sınırlarına taşı; her adımda ilgili testleri çalıştır.

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
- İlk ayrıştırma adayları ders seçimi/yükleme ve çalışma oturumu kayıt akışlarıdır.
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

1. database_runtime.py içindeki uyumluluk metotlarının Database sınıfına kayıt yoluyla eklenmesi.
2. window.py dosyasının pencere koordinasyonunun ötesinde çalışma oturumu ve ders akışlarını da yönetmesi.
3. Eski/aktif settings ve statistics modüllerinin çiftlerinin bulunması.
4. JSON katalog, SQLite kullanıcı içeriği ve JSON yedekleme rollerinin dokümantasyonda karıştırılma riski.
5. Flatpak veri yolu, ilk kurulum/var olan kullanıcı verisi geçişi ve yedek geri yükleme senaryolarının her sürümde regresyon testine ihtiyaç duyması.

## 10. Sonraki adım ve kapsam sınırı

İlk uygulama adımı, kodu değiştirmeden güncel main için bağımlılık/import haritasını ve database_runtime.py metot envanterini tamamlamaktır. Ardından her risk için küçük, test edilebilir değişiklikler planlanabilir.

Bu çalışma sırasında:

- keycan/core/typing_engine.py davranışı değiştirilmeyecek.
- Kullanıcı veritabanı üzerinde doğrudan deney yapılmayacak; testler geçici kopyalar kullanacak.
- Kullanıcı içeriği SQLite'tan JSON'a taşınmayacak.
- Eski modüller, tablolar veya dosyalar yalnızca isim benzerliği nedeniyle silinmeyecek.
- GTK çalışma zamanı testi yapılmadıysa bu açıkça raporlanacak.
