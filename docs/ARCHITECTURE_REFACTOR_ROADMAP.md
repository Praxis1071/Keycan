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
**Durum: Kısmen tamamlandı — database runtime monkey-patch kaldırıldı; yinelenen modül denetimi sürüyor**

- `database_runtime.py` içindeki `Database` sınıfına çalışma anında metot atama mekanizması kaldırıldı. Uygulama artık açık `ManagedDatabase(Database)` alt sınıfını kullanıyor.
- Uygulama başlangıcındaki `install_database_runtime()` çağrısı kaldırıldı; `app.py` artık import sırasına bağlı veritabanı kaydı yapmıyor.
- İçerik yönetimi, ilerleme ve yedekleme API'sini kullanan testler `ManagedDatabase` ile çalışacak şekilde güncellendi.
- Alt süreç regresyon testi, `database_runtime.py` import edildiğinde temel `Database` sınıfının değişmediğini ve managed API'nin alt sınıfta bulunduğunu doğruluyor.
- `database.py` / `database_runtime.py`, `statistics.py` / `statistics_clean.py`, `settings.py` / `settings2.py` için tüm import ve çağrı noktalarını doğrula.
- Yalnızca kullanılmadığı kanıtlanan veya yerine geçen dosyaları kaldır; uyumluluk gerekiyorsa geçici ince bir yönlendirme katmanı kullan.
- Managed alt sınıfındaki modül düzeyi fonksiyonları daha sonra normal sınıf metotlarına taşı; bu adım ayrı testlerle yürütülmeli.

**Doğrulama:** İlk refactor commit'inde GitHub Actions tüm dört işi başarıyla tamamladı; `check.sh` 52 kontrolü, tam pytest paketi 67 testi geçti. GTK masaüstü etkileşimleri henüz elle doğrulanmadı.

**Çıkış koşulu:** Runtime monkey-patch olmadan uygulama ve testler çalışır; yinelenen modüllerin kaldırılması için kullanım/uyumluluk kanıtı bulunur; hiçbir özellik kaybolmaz.

### Aşama 5 — `window.py` sorumluluklarını azaltma
**Durum: Bekliyor**

- Pencereyi sayfa yerleşimi ve üst seviye koordinasyonla sınırla.
- Ders seçimi/yükleme, çalışma oturumu yaşam döngüsü, oturum kaydı ve sayfa yenileme sorumluluklarını mevcut davranışlarına göre küçük bileşenlere ayır.
- GUI widget'ları GUI katmanında; iş kuralları servislerde; kalıcı veri erişimi veri katmanında kalsın.
- Her çıkarımda mevcut sinyal bağlantıları, GTK widget yaşam döngüsü ve kapanışta bekleyen kayıtlar korunmalı.
- Gereksiz controller/factory/manager sınıfları oluşturma; yalnızca bağımsız sorumlulukları ayır.

**Çıkış koşulu:** `window.py` küçülür; çalışma alanı ve pencere davranışı değişmez; GTK başlangıç/kapanış ve oturum testleri geçer.

### Aşama 6 — Veritabanı ve servis katmanlarını düzenleme
**Durum: Bekliyor**

- SQLite şema migrasyonlarını tek ve izlenebilir yerde topla.
- SQL sorgularını GUI'den uzaklaştır; gerekli yerlerde repository kullan.
- İstatistik/profil/ilerleme hesaplarını veri erişiminden ayır.
- Bağlantı kapanışı, transaction, hata yönetimi ve yedek geri yükleme davranışını netleştir.
- Tercihler, çeviri, ders ve ilerleme servislerinin tek sorumluluklu olmasını sağla.
- Kullanıcı verisi dizini ve paket kaynakları yollarını birbirinden ayır; uygulama kaynak kodu dizinine yazma zorunluluğunu kaldır.

**Çıkış koşulu:** Servis ve repository testleri geçer; mevcut istatistik, profil, tema, dil ve içerik davranışları korunur.

### Aşama 7 — Entegrasyon, regresyon ve dokümantasyon
**Durum: Bekliyor**

- Tam test paketini ve CI iş akışını çalıştır.
- GTK uygulamasının açılış, sayfa geçişleri, ders pratiği, oturum kaydı ve kapanış akışını kontrol et.
- JSON bozuk dosya, eski DB'den geçiş, yinelenen kimlik, yedek alma/geri yükleme ve yarım kalan yazım senaryolarını test et.
- `typing_engine.py` değişmediğini diff üzerinden doğrula ve mevcut yazma motoru testlerini çalıştır.
- Eski/çelişkili migration belgelerini güncel mimari belgesine yönlendir veya arşivle.
- Kurulum, paketleme ve yedekleme belgelerini yeni veri yollarına göre güncelle.

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
