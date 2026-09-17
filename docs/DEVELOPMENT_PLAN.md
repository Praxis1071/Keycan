# Keycan — Onaylı Geliştirme Planı

Bu belge, 17 Eylül 2026 tarihinde belirlenen ve kullanıcı tarafından açıkça onaylanan Keycan geliştirme sürecinin kalıcı referansıdır.

## Temel çalışma kuralı

Keycan'a rastgele özellik eklenmeyecektir. Her aşama önce tasarlanacak, uygulanacak, mevcut mimari ve stabilite açısından kontrol edilecek; ancak bundan sonra bir sonraki aşamaya geçilecektir.

Ana yazma deneyimi korunacak ve yeni bölümler mevcut çalışma alanına gereksiz bağımlılık oluşturmayacak şekilde geliştirilecektir.

## Aşamalar

### Aşama 0 — Mevcut durum ve mimari kontrolü

- Mevcut GUI, yazma motoru ve SQLite yapısını incele.
- Mevcut davranışları ve korunması gereken parçaları belirle.
- Yeni özellik eklemeden önce mimari etkileri değerlendir.
- İstatistik ve profil için mevcut veri altyapısındaki eksikleri tespit et.

**Durum:** Tamamlandı.

### Aşama 1 — Çalışma oturumu veri modeli

Her tamamlanan yazma çalışmasının istatistiklerde anlamlı biçimde gösterilebilmesi için hangi verilerin saklanacağı kesin olarak tanımlanacaktır.

Planlanan temel çalışma kaydı:

- çalışma kimliği
- çalışma tarihi/zamanı
- çalışılan ders kimliği
- çalışma sırasında kullanılan kaynak adı
- ders/metin adı veya kullanıcıya gösterilen ders bilgisi
- çalışma süresi
- hedef metindeki toplam kelime
- kullanıcının yazdığı toplam kelime
- doğru kelime sayısı
- yanlış kelime sayısı
- toplam karakter
- doğru karakter sayısı
- yanlış karakter sayısı
- dakikadaki kelime değeri (ham veri; kullanıcı arayüzünde teknik kısaltma olarak gösterilmeyecek)
- dakikadaki karakter değeri (ham veri; kullanıcı arayüzünde teknik kısaltma olarak gösterilmeyecek)
- doğruluk yüzdesi

### Kullanıcıya gösterilecek dil

`WPM` ve `CPM` gibi tek başına teknik kısaltmalar ana kullanıcı arayüzünde kullanılmayacaktır.

Örnek:

- `42 WPM` yerine **Dakikada 42 kelime**
- `96% accuracy` yerine **%96 doğruluk**
- `CPM` yerine gerektiğinde **Dakikada X karakter**

Ham ölçüm alanları veri katmanında tutulabilir; kullanıcı arayüzü bunları anlaşılır Türkçe ifadelerle sunacaktır.

### Çalışmalarım tablosu için hedef veri

İstatistikler sayfasında geçmiş çalışmalar ayrı ayrı görülebilecektir. Tablonun ilk tasarımında şu bilgiler hedeflenmektedir:

| Alan | Kullanıcıya gösterim |
|---|---|
| Tarih | 17 Eylül 2026, 18:30 |
| Ders | Ders 12 |
| Süre | 5 dakika |
| Sonuç | 184 kelime |
| Doğruluk | %96 |
| Hız | Dakikada 37 kelime |

Tablo tasarımında gereksiz teknik alanlar gösterilmeyecek; ayrıntılı veriler gerektiğinde çalışma ayrıntısında kullanılabilecektir.

### Aşama 1 tasarım ilkeleri

- İstatistikler sonradan hesaplanabilecek şekilde yeterli ham veri saklanmalıdır.
- Aynı çalışma kaydında mümkün olduğunca o anki çalışmayı tanımlayan bilgiler korunmalıdır.
- Ders veya kaynak adları ileride değişse bile geçmiş kayıtların anlamı bozulmamalıdır.
- Gelecekte günlük, haftalık ve aylık grafikler üretilebilmelidir.
- Profil, XP ve rozet sistemi aynı temel çalışma kayıtlarını kullanabilmelidir.
- Veri modeli kullanıcı arayüzünden bağımsız tutulmalıdır.

### Aşama 1 uygulama sonucu

Çalışma sonuçlarının SQLite'a kaydedilmesi veri modeliyle uyumlu hale getirildi.

Eklenen/aktif kullanılan çalışma alanları:

- `completed_at`
- `source_name_snapshot`
- `lesson_title_snapshot`
- `target_word_count`
- `typed_word_count`
- `total_characters`
- `correct_characters`
- `wrong_characters`
- `accuracy_percent`
- mevcut hız alanları (`words_per_minute`, `characters_per_minute`)

Yeni çalışma kayıtları kaynak ve ders adlarını o anki haliyle saklayarak geçmiş kayıtların daha sonra değişen ders/kaynak adlarından etkilenmesini önleyecek şekilde tasarlanmıştır.

Hız, doğruluk ve karakter ölçümleri çalışma tamamlandığı anda hesaplanır. Eski veritabanları için migration mevcut sütunları koruyarak eksik alanları ekler. SQLite migration uyumluluğu nedeniyle `completed_at` eski satırlarda boş bırakılabilir; yeni kayıtlar ekleme sırasında `CURRENT_TIMESTAMP` ile oluşturulur.

**Durum:** Tamamlandı.

### Aşama 2 — İstatistikler sayfası UX tasarımı

İstatistikler sayfası kodlanmadan önce görünüm ve bilgi hiyerarşisi kesinleştirilecektir.

Hedef yapı:

- genel çalışma özeti
- anlaşılır istatistik kartları/tablosu
- yazma gelişimini gösteren grafikler
- günlük/haftalık/aylık görünüm
- **Çalışmalarım** geçmiş tablosu
- doğru/yanlış ve doğruluk analizi
- ortalama ve gelişim bilgileri

Grafik ve tablolar kullanıcıya doğrudan anlam ifade eden Türkçe başlıklarla sunulacaktır.

**Durum:** Bekliyor.

### Aşama 3 — Gerçek SQLite verilerinin istatistiklere bağlanması

- Tamamlanan çalışma kayıtları gerçek verilerle doldurulacak.
- İstatistikler SQLite üzerinden okunacak.
- Çalışmalarım tablosu gerçek geçmişi gösterecek.
- Grafikler gerçek çalışma verilerinden üretilecek.
- Eski kayıtlar için geriye dönük uyumluluk korunacak.

**Durum:** Bekliyor.

### Aşama 4 — Profil sayfası

- Temel kullanıcı bilgileri
- Çalışma özeti
- İstatistiklerden gelen ilerleme bilgileri
- İleride seviye/XP/rozet alanları
- Profil ile çalışma geçmişi arasında tutarlı veri bağlantısı

**Durum:** Bekliyor.

### Aşama 5 — XP, seviye ve rozet sistemi

- Çalışmalardan XP kazanımı
- Seviye sistemi
- Başarı rozetleri
- İstatistikler ve Profil ile entegrasyon

XP sistemi, temel çalışma ve istatistik veri altyapısı güvenilir hale gelmeden uygulanmayacaktır.

**Durum:** Bekliyor.

## Aşama geçiş kuralı

Bir aşama tamamlandı sayılmadan sonraki aşamanın koduna başlanmaz.

Her aşama sonunda:

1. Yapılan değişiklikler kontrol edilir.
2. Mevcut özelliklerin bozulmadığı doğrulanır.
3. Veri/mimari uyumluluk kontrol edilir.
4. Gerekirse geri dönüş noktası oluşturulur.
5. Sonraki aşamaya geçmeden önce plan yeniden değerlendirilir.

## İlgili mevcut roadmap

Bu belge, `ROADMAP.md` içindeki uzun vadeli planı daha kontrollü bir uygulama sırasına dönüştüren çalışma belgesidir. `ROADMAP.md` gelecekteki özelliklerin genel listesini, bu belge ise kabul edilmiş uygulama sırasını ve tasarım kararlarını tanımlar.
