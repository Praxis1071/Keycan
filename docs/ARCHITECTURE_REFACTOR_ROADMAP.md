# Keycan Mimari İyileştirme Yol Haritası

Bu belge, mevcut Keycan uygulamasını yeniden yazmadan daha sade, sürdürülebilir ve test edilebilir hale getirmek için uygulanacak teknik planın ana kaynağıdır.

## Değişmez kurallar

- `keycan/core/typing_engine.py` ve yazma motorunun davranışı bu çalışma kapsamında değiştirilmez. Yalnızca mevcut testleriyle doğrulanır.
- Mevcut özellikler, kullanıcı verileri, çalışma geçmişi ve profil ilerlemesi korunur.
- Büyük çaplı yeniden yazım yapılmaz. Her değişiklik küçük, geri alınabilir ve test edilebilir olur.
- Eski veri biçimleri için geçiş/geri uyumluluk yolu olmadan tablo veya dosya silinmez.
- Kullanıcıya görünen davranış, özellikle ders seçimi, ders yönetimi, istatistikler, profil, ayarlar ve yedekleme korunur.
- Gereksiz soyutlama, yeni bağımlılık veya Rust katmanı eklenmez. Performans konusu ancak ölçümle kanıtlanırsa ele alınır.

## Hedef mimari ilkeleri

1. **Hazır ders kataloğu JSON:** Uygulamayla gelen varsayılan ders grupları ve ders metinleri sürümlenmiş JSON dosyalarında tutulur.
2. **Kullanıcı içeriği — karar kapısı:** Hazır kataloğun paket içindeki JSON kaynağı olması kararlaştırılmıştır. Kullanıcının özel grupları ve hazır içerik üzerindeki düzenlemeleri için mevcut SQLite yazma modelinin korunması başlangıç tercihidir. JSON tabanlı kullanıcı deposu/override ancak somut bir gereksinim ve ölçülebilir fayda gösterilirse ayrıca değerlendirilecektir; bu geçiş önceden kabul edilmiş değildir.
3. **SQLite çalışma verileri:** Yazma oturumları, istatistikler ve geçmiş SQLite'ta kalır. Ders içeriğinin JSON'a taşınması çalışma geçmişini SQLite'tan çıkarmak anlamına gelmez.
4. **Yedekleme:** JSON tabanlı, sürüm numarası ve doğrulama bilgisi olan dışa aktarma biçimi kullanılır. Yedek, hem kullanıcı ders içeriğini hem de SQLite çalışma verilerini kapsar; geri yükleme önce doğrulanır ve mevcut verinin üzerine yazmadan önce güvenli geri dönüş noktası oluşturur.
5. **Servis sınırı:** GUI, JSON dosyalarını veya SQL sorgularını doğrudan yönetmez. Ders işlemleri ders servisi; kalıcı çalışma verileri veri katmanı üzerinden yürütülür.
6. **Kararlı kimlikler:** JSON ders/grup kayıtlarında değişmeyen kimlikler bulunur. İsim veya sıralama değişikliği geçmiş çalışma kayıtlarının bağını koparmaz.
7. **Atomik yazım:** JSON güncellemeleri geçici dosyaya yazılıp doğrulandıktan sonra atomik olarak değiştirilir. Bozuk/eksik dosya sessizce varsayılanla ezilmez.

Önerilen hedef iskelet (inceleme sonunda gerekli olmayan klasörler eklenmeyecek):

```text
keycan/
├── app.py
├── window.py
├── core/
│   └── typing_engine.py       # korunacak
├── data/
│   ├── database.py
│   └── repositories/
├── gui/
│   ├── pages/
│   ├── dialogs/
│   └── widgets/
├── services/
│   ├── lessons.py
│   ├── preferences.py
│   ├── translations.py
│   └── progression.py
├── resources/
│   └── lessons/
│       ├── tr/
│       └── en/
└── utils/
```

## Aşamalar

### Aşama 0 — Mimari ve bağımlılık denetimi
**Durum: Kısmen tamamlandı — kaynak/CI incelemesi mevcut; GTK masaüstü çalışma zamanı doğrulaması ayrıca gerekli**

İlk statik bulgular: [Mimari İnceleme Raporu](ARCHITECTURE_AUDIT.md). Rapor, henüz çalıştırılmamış testleri başarılı gibi göstermemek için statik inceleme ile dinamik doğrulamayı ayrı tutar.

- Gerçek giriş noktalarını, modül importlarını ve çalışma zamanı bağımlılıklarını çıkar.
- `window.py`, `database.py`, `database_runtime.py`, istatistik ve ayar modüllerinin sorumluluklarını haritala.
- Uygulama içi veri akışını (ders seçimi, ders düzenleme, oturum kaydı, istatistik, profil, yedekleme) takip et.
- Mevcut testleri ve CI komutlarını çalıştır; mümkün değilse eksik sistem bağımlılıklarını açıkça kaydet.
- Mevcut davranışların ve veri tablolarının envanterini çıkar.
- Eski plan belgelerindeki çelişkileri belirle; henüz çalışan kodu silme.

**Çıkış koşulu:** Bağımlılık haritası, veri akışı, test tabanı ve risk listesi yazılı hale gelmeden veri taşıma başlamaz.

### Aşama 1 — JSON ders formatı ve servis tasarımı
**Durum: Kısmen tamamlandı — paketlenmiş Türkçe katalog ve okuma servisi main dalında mevcut; ek doğrulamalar sürüyor**

- Paketlenmiş hazır ders kataloğu için açık, sürümlenmiş JSON şemasını koru; ek dil katalogları yalnızca gerçekten yerelleştirilmiş ders içeriği mevcutsa eklenir.
- Her grup ve ders için kararlı kimlik, ad, sıra ve metin alanlarını tanımla.
- Kullanıcı içeriklerinin mevcut SQLite tabanlı yazma modelini ve hazır ders kataloğu JSON okuma sınırını doğrula. JSON kullanıcı deposu/override seçeneğini ancak gerekçeli karşılaştırma ve ayrı onay sonrasında ele al.
- JSON katalog yükleme, şema doğrulama, yinelenen kimlik kontrolü ve hata raporlamayı LessonService sınırında tut. Paketlenmiş salt-okunur katalog için yazma akışı ekleme.
- GUI'nin mevcut veritabanı API'sinden yeni servis API'sine geçiş sözleşmesini belirle.
- JSON formatı için birim testleri ekle.

**Çıkış koşulu:** Eski içerik değiştirilmeden JSON örnekleri doğrulanır; yükleme ve kaydetme testleri geçer.

### Aşama 2 — Ders grupları ve metinlerinin sadeleştirilmesi
**Durum: Kısmen tamamlandı — paketlenmiş katalogda temizlenmiş içerik ve kimlik/sıra karşılaştırmaları mevcut; kalan kalite kontrolü ayrıca yapılmalı**

- Mevcut JSON/SQLite ders içeriğini analiz et ve önce değişiklik önizleme raporu üret.
- Grup adları ve ders başlıklarından sayıları, noktalama ve gereksiz açıklamaları temizle; yalnızca Türkçe/İngilizce harfler ve kelime ayırmak için tek boşluk bırak.
- Ders metinlerinde rakam ve noktalama işaretlerini kaldır; Türkçe karakterleri (`ç ğ ı ö ş ü`) koru, boşlukları normalize et.
- Metin anlamını bozabilecek birleşmeler, boş kalan metinler, yinelenen içerikler ve çok kısa dersler için otomatik rapor üret.
- Temizleme işlemini yalnızca önizleme ve doğrulama sonrasında uygula; orijinal içerik yedeği sakla.

**Çıkış koşulu:** Her ders için önce/sonra karşılaştırması ve doğrulama raporu bulunur; kaybolan/boşalan içerik yoktur veya açıkça çözümlenmiştir.

### Aşama 3 — Ders içeriği kaynaklarının güvenli ayrıştırılması
**Durum: Kısmen tamamlandı — hazır derslerin JSON okuma yolu mevcut; kullanıcı içeriği SQLite'ta kalıyor**

- Paketlenmiş hazır ders kataloğunun JSON kaynağı ve LessonService okuma sınırı main dalında zaten bulunur; bu sınırın kapsama ve fallback testlerini koru.
- JSON kataloğundaki grup/ders kimlikleri ve sıralaması ile mevcut SQLite varsayılan içerik snapshot'larını karşılaştır; tarihsel referansların kopmadığını doğrula.
- Kullanıcı tarafından oluşturulan gruplar, düzenlemeler, sıralama/silme durumu ve çalışma geçmişi SQLite'ta kalır. Bu veriler için otomatik JSON migrasyonu yapılmaz.
- Eski SQLite tabloları, snapshot kayıtları veya uyumluluk alanları ancak kullanım analizi, yedek ve geri dönüş yolu ile ayrı testlerden sonra kaldırılabilir.
- LessonService hazır katalog okumalarını yönetir; kullanıcı içeriği CRUD, sıralama, silme/geri yükleme ve yedekleme mevcut SQLite API'siyle uyumlu kalır.

**Çıkış koşulu:** Paketlenmiş katalog ile mevcut kullanıcı içeriği arasındaki sınır testlerle doğrulanır; kullanıcı içeriği migrasyonu ancak ayrı bir karar ve kanıtlanmış ihtiyaç varsa uygulanır. Herhangi bir geçişte CRUD, geri yükleme, geçmiş ve profil tutarlılığı kanıtlanır.

### Aşama 4 — Runtime monkey-patch ve yinelenen modülleri sadeleştirme
**Durum: Tamamlandı — runtime monkey-patch kaldırıldı; yinelenen GUI uygulamaları uyumluluk dışa aktarımlarına dönüştürüldü**

- `database_runtime.py` içindeki `Database` sınıfına çalışma anında metot atama mekanizması kaldırıldı. Uygulama artık `managed_database.py` içindeki açık `ManagedDatabase(Database)` alt sınıfını kullanıyor.
- Eski `database_runtime.py` yolu, eski importları bozmamak için küçük bir uyumluluk dışa aktarımı olarak tutuluyor.
- Uygulama başlangıcındaki `install_database_runtime()` çağrısı kaldırıldı; `app.py` artık import sırasına bağlı veritabanı kaydı yapmıyor.
- İçerik yönetimi, ilerleme ve yedekleme API'sini kullanan testler `ManagedDatabase` ile çalışacak şekilde güncellendi.
- Alt süreç regresyon testi, hem `managed_database.py` hem de uyumluluk modülü import edildiğinde temel `Database` sınıfının değişmediğini ve managed API'nin alt sınıfta bulunduğunu doğruluyor.
- `statistics.py` artık `statistics_clean.py` modülünden; `settings.py` ise `settings2.py` modülünden küçük uyumluluk dışa aktarımları sağlar. Yinelenen uygulama kodu kaldırıldı, eski import yolları korundu.
- `database_runtime.py` da `managed_database.py` için uyumluluk dışa aktarımıdır; aktif kod doğrudan managed modülünü kullanır.
- Managed veritabanı işlemleri normal `ManagedDatabase` sınıf metotları olarak taşındı; testler sınıfın kendi metotlarını sunduğunu doğruluyor.

**Doğrulama:** GitHub Actions'ın beş işi başarıyla tamamlandı: `check.sh` 52 kontrol, tam pytest 72 test, Ruff F821 ve GTK/Xvfb smoke testi. GTK smoke testi gerçek pencereyi, sayfa kurulumunu, ayarlar içindeki ders yönetimini, gizlilik etiketini, dil değişimini ve yazım oturumu kaydını doğruluyor.

**Çıkış koşulu:** Runtime monkey-patch olmadan uygulama ve testler çalışır; yinelenen modüllerin kaldırılması için kullanım/uyumluluk kanıtı bulunur; hiçbir özellik kaybolmaz.

### Aşama 5 — `window.py` sorumluluklarını azaltma
**Durum: Büyük ölçüde tamamlandı — pencere yerleşimi, editör sunumu, metrikler ve kayıt/yeniden deneme ayrıldı; oturum zamanlaması ve ders seçimi koordinasyonu pencerede bırakıldı**

- Kelime/karakter/doğruluk ölçümleri ve veritabanı kayıt payload'ı `keycan/core/session_metrics.py` içine taşındı; saf hesaplamalar GTK dışında test ediliyor.
- Ana pencerenin CSS, widget yerleşimi ve tercih popover'ı `keycan/gui/window_layout.py` içine taşındı; `window.py` yaklaşık 850 satırdan 585 satıra küçüldü.
- Editör gizlilik görünümü, sonuç renklendirme ve text-buffer sunumu `keycan/gui/workspace.py` içine taşındı; pencere yalnızca oturum durumunu iletir.
- Veritabanı oturum kaydı, başarısız kayıt kuyruğu ve yeniden deneme `keycan/services/session_recorder.py` içine taşındı; pencere kullanıcıya durum/yeniden deneme arayüzünü sunar.
- Pencere artık 585 satırdır ve ana sorumlulukları ayrılmıştır. GTK zamanlayıcısı, ders seçimi ve pencere kapanış koordinasyonu GTK sinyalleriyle sıkı bağlı olduğu için ayrı bir controller'a taşınmadı; gerçek masaüstü testinden sonra ihtiyaç görülürse ayrıca ele alınabilir.
- GUI widget'ları GUI katmanında; iş kuralları servislerde; kalıcı veri erişimi veri katmanında kalsın.
- Her çıkarımda mevcut sinyal bağlantıları, GTK widget yaşam döngüsü ve kapanışta bekleyen kayıtlar korunmalı.
- Gereksiz controller/factory/manager sınıfları oluşturma; yalnızca bağımsız sorumlulukları ayır.

**Doğrulama:** [GitHub Actions run 41299726832](https://github.com/Praxis1071/Keycan/actions/runs/41299726832) beş işin tamamını başarıyla tamamladı. GTK/Xvfb smoke testi pencere, sayfalar, içerik yöneticisi, gizlilik, canlı dil değişimi, oturum kaydı, başarısız kayıt yeniden denemesi ve durum mesajını kontrol ediyor. İnsan tarafından gerçek masaüstünde yapılacak kullanım testi hâlâ gereklidir.

**Çıkış koşulu:** `window.py` küçülür; çalışma alanı ve pencere davranışı değişmez; GTK başlangıç/kapanış ve oturum testleri geçer.

### Aşama 6 — Veritabanı ve servis katmanlarını düzenleme
**Durum: Kısmen tamamlandı — temel sınırlar ve servis sorumlulukları netleştirildi; legacy CRUD/transaction denetimi sürüyor**

- Şema migrasyonları ve SQL veri erişimi temel `Database`/`ManagedDatabase` katmanında tutuluyor; GUI doğrudan katalog JSON okumuyor.
- Ders kataloğu ve gösterim isimleri `LessonService`; XP/rozet/seri kuralları `progression.py`; oturum kayıt kuyruğu `SessionRecorder`; tercihler XDG config; profil verisi XDG config/data kullanıyor.
- Flatpak wrapper ilk veritabanını XDG data alanına kopyalıyor; paketlenmiş kaynak DB salt-okunur uygulama alanında kalıyor.
- Tamamlanması gerekenler: `Database` ve `ManagedDatabase` arasındaki tarihsel CRUD API örtüşmelerini çağrı noktalarıyla denetlemek; transaction ve restore hata senaryolarını daha geniş testlerle kapsamak. Bu aşamada uyumluluk metotları silinmedi.

**Çıkış koşulu:** Servis ve repository testleri geçer; mevcut istatistik, profil, tema, dil ve içerik davranışları korunur.

### Aşama 7 — Entegrasyon, regresyon ve dokümantasyon
**Durum: Otomatik doğrulama tamamlandı; gerçek masaüstü kullanıcı testi bekleniyor**

- Tam test paketi, Ruff F821, `check.sh` ve GTK/Xvfb smoke CI başarıyla tamamlandı.
- GTK smoke testi gerçek pencere, sayfalar, içerik yöneticisi, gizlilik, canlı dil değişimi, oturum kaydı ve başarısız kayıt yeniden denemesini kontrol ediyor.
- JSON katalog doğrulaması, eski DB migrasyonları, kimlik eşlemesi ve yedek/geri yükleme regresyonları mevcut pytest paketi ve depo kontrolleriyle kapsanıyor.
- `typing_engine.py` bu branch'te değiştirilmedi.
- Mimari ve yedekleme belgeleri güncellendi; eski planlar arşivlendi.
- Son kalan adım kullanıcının gerçek CachyOS/Flatpak masaüstünde uygulamayı kurup etkileşimli kullanımını doğrulaması.

**Çıkış koşulu:** Test/CI sonuçları raporlanır, veri kaybı yoktur ve kalan bilinen sorunlar belgelenir.

## Her aşamada zorunlu güvenlik kapısı

1. Değişiklik öncesi mevcut durum ve test sonucu kaydedilir.
2. Riskli veri işlemlerinden önce yedek/geri dönüş noktası alınır.
3. Küçük ve tek amaçlı değişiklik yapılır.
4. İlgili birim testleri, ardından tam test paketi çalıştırılır.
5. Eski/yeni veri sayıları ve kritik davranışlar karşılaştırılır.
6. Başarısız test varsa sonraki aşamaya geçilmez; sorun düzeltilir veya değişiklik geri alınır.
7. Her aşamanın sonucu bu belgede güncellenir.

## Bilinçli olarak kapsam dışı

- Yazma motorunu yeniden yazmak veya performans amacıyla Rust'a taşımak.
- GTK arayüzünü baştan tasarlamak.
- Yeni çevrimiçi hesap, bulut senkronizasyonu veya yeni ürün özellikleri eklemek.
- Ölçülmemiş performans varsayımları için optimizasyon yapmak.
- Sırf mimari görünmesi için fazladan katman veya bağımlılık eklemek.


## 2026-11-01 — Güncel kararlar ve uygulama durumu

- Paketlenmiş varsayılan ders kataloğu JSON olarak kalır; GUI katalog dosyalarını doğrudan okumaz, LessonService sınırını kullanır.
- Kullanıcı tarafından oluşturulan içerikler ve hazır içerik üzerindeki kişisel düzenlemeler için SQLite mevcut yazma modeli korunur. Kullanıcı verisini JSON'a taşımak şu an hedef veya zorunlu iş değildir.
- Yazma oturumları, istatistikler ve geçmiş SQLite'ta kalır.
- JSON tabanlı yedekleme/geri yükleme, uygulamanın canlı veri deposu değildir; sürümlü dışa aktarma biçimidir ve geriye dönük uyumluluğu korunmalıdır.
- Main dalında KC-001–KC-005 stabilizasyon PR'si (#2) birleştirilmiştir. İlgili otomatik testler PR doğrulamasında başarılı olmuştur. Gizlilik, profil fotoğrafı ve canlı dil değişimi gibi GTK etkileşimleri için manuel kontrol gereksinimi ayrıca takip edilir.
- Bu belge, ROADMAP.md Aşama 10'un teknik uygulama kaynağıdır. Öncelik çakışırsa ROADMAP'teki güvenlik kuralları ve bu belgede açıklanan veri koruma sınırları geçerlidir.
