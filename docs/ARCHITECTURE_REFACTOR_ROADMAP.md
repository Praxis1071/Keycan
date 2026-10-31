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
2. **Kullanıcı içeriği JSON:** Kullanıcının oluşturduğu gruplar ve hazır içerik üzerinde yaptığı değişiklikler kullanıcı veri dizinindeki JSON içerik deposunda tutulur. Paket içindeki varsayılan JSON dosyaları doğrudan değiştirilmez.
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
**Durum: Devam ediyor — statik kaynak incelemesi yapıldı, çalışma zamanı doğrulaması bekliyor**

İlk statik bulgular: [Mimari İnceleme Raporu](ARCHITECTURE_AUDIT.md). Rapor, henüz çalıştırılmamış testleri başarılı gibi göstermemek için statik inceleme ile dinamik doğrulamayı ayrı tutar.

- Gerçek giriş noktalarını, modül importlarını ve çalışma zamanı bağımlılıklarını çıkar.
- `window.py`, `database.py`, `database_runtime.py`, istatistik ve ayar modüllerinin sorumluluklarını haritala.
- Uygulama içi veri akışını (ders seçimi, ders düzenleme, oturum kaydı, istatistik, profil, yedekleme) takip et.
- Mevcut testleri ve CI komutlarını çalıştır; mümkün değilse eksik sistem bağımlılıklarını açıkça kaydet.
- Mevcut davranışların ve veri tablolarının envanterini çıkar.
- Eski plan belgelerindeki çelişkileri belirle; henüz çalışan kodu silme.

**Çıkış koşulu:** Bağımlılık haritası, veri akışı, test tabanı ve risk listesi yazılı hale gelmeden veri taşıma başlamaz.

### Aşama 1 — JSON ders formatı ve servis tasarımı
**Durum: Bekliyor**

- Türkçe ve İngilizce hazır ders katalogları için açık bir JSON şeması belirle.
- Her grup ve ders için kararlı kimlik, ad, sıra ve metin alanlarını tanımla.
- Kullanıcı içerikleri ve hazır içerik üzerindeki düzenlemeler için kullanıcı veri dizininde ayrı JSON deposu/override yaklaşımı oluştur.
- JSON yükleme, şema doğrulama, yinelenen kimlik kontrolü, hata raporlama ve atomik kaydetmeyi tek ders servisinde topla.
- GUI'nin mevcut veritabanı API'sinden yeni servis API'sine geçiş sözleşmesini belirle.
- JSON formatı için birim testleri ekle.

**Çıkış koşulu:** Eski içerik değiştirilmeden JSON örnekleri doğrulanır; yükleme ve kaydetme testleri geçer.

### Aşama 2 — Ders grupları ve metinlerinin sadeleştirilmesi
**Durum: Bekliyor**

- Mevcut JSON/SQLite ders içeriğini analiz et ve önce değişiklik önizleme raporu üret.
- Grup adları ve ders başlıklarından sayıları, noktalama ve gereksiz açıklamaları temizle; yalnızca Türkçe/İngilizce harfler ve kelime ayırmak için tek boşluk bırak.
- Ders metinlerinde rakam ve noktalama işaretlerini kaldır; Türkçe karakterleri (`ç ğ ı ö ş ü`) koru, boşlukları normalize et.
- Metin anlamını bozabilecek birleşmeler, boş kalan metinler, yinelenen içerikler ve çok kısa dersler için otomatik rapor üret.
- Temizleme işlemini yalnızca önizleme ve doğrulama sonrasında uygula; orijinal içerik yedeği sakla.

**Çıkış koşulu:** Her ders için önce/sonra karşılaştırması ve doğrulama raporu bulunur; kaybolan/boşalan içerik yoktur veya açıkça çözümlenmiştir.

### Aşama 3 — Ders içeriğinin JSON'a taşınması
**Durum: Bekliyor**

- Hazır dersleri paket içindeki JSON kataloglarına taşı.
- Kullanıcı tarafından oluşturulan grupları ve düzenlemeleri kullanıcı veri dizinindeki JSON deposuna taşı.
- SQLite'taki eski ders tablolarını ilk geçişte silme; geçiş sırasında eski veriyi JSON'a dönüştür ve kayıt sayısı/kimlik/metin karşılaştırması yap.
- Çalışma geçmişi için kararlı ders kimlikleri ve mevcut snapshot alanları üzerinden ilişkiyi koru. Eski `lesson_id` kayıtlarını kayıpsız dönüştürmeden hiçbir tabloyu kaldırma.
- Eski veritabanıyla açılışta güvenli, tek seferlik geçiş uygula; geçiş tamamlanma işareti ve tekrar çalıştırma güvenliği ekle.
- İçerik ekleme, düzenleme, silme, sıralama, varsayılanları geri yükleme ve yedekleme akışlarını JSON servisine bağla.

**Çıkış koşulu:** Eski ve yeni içerik sayıları/kimlikleri karşılaştırılır; tüm CRUD ve geri yükleme testleri geçer; geçmiş ve profil sayıları değişmez.

### Aşama 4 — Runtime monkey-patch ve yinelenen modülleri sadeleştirme
**Durum: Bekliyor**

- `database_runtime.py` ve `statistics_runtime.py` içindeki çalışma zamanı sınıf/metot değiştirmelerini belirle.
- Bu davranışları uygun sınıf veya serviste açık, normal metotlara dönüştür.
- `database.py` / `database_runtime.py`, `statistics.py` / `statistics_clean.py`, `settings.py` / `settings2.py` için tüm import ve çağrı noktalarını doğrula.
- Yalnızca kullanılmadığı kanıtlanan veya yerine geçen dosyaları kaldır; uyumluluk gerekiyorsa geçici ince bir yönlendirme katmanı kullan.
- Uygulama başlangıcındaki yan etkili importları kaldır.

**Çıkış koşulu:** Monkey-patch olmadan uygulama ve testler çalışır; hiçbir özellik kaybolmaz; gereksiz dosyalar için kullanım kanıtı bulunur.

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
