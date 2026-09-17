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

Her tamamlanan yazma çalışmasının istatistiklerde anlamlı biçimde gösterilebilmesi için gerekli veriler SQLite'a kaydedilecektir.

Temel çalışma kaydı; çalışma zamanı, ders/kaynak snapshot bilgileri, süre, hedef ve yazılan kelime sayıları, doğru/yanlış kelimeler, karakter ölçümleri, dakikadaki kelime/karakter değerleri ve doğruluk yüzdesini içerir.

Kullanıcı arayüzünde `WPM` ve `CPM` gibi tek başına teknik kısaltmalar kullanılmayacaktır. Örnek dil: **Dakikada 42 kelime**, **%96 doğruluk**, **Dakikada 210 karakter**.

### Aşama 1 uygulama sonucu

Çalışma sonuçlarının SQLite'a kaydedilmesi veri modeliyle uyumlu hale getirildi. Yeni kayıtlar kaynak ve ders adlarını o anki haliyle snapshot olarak saklar. Eski veritabanları için migration eksik alanları ekler ve güvenilir biçimde türetilebilen alanları geriye dönük doldurur.

**Durum:** Tamamlandı ve kontrol edildi.

### Aşama 2 — İstatistikler sayfası

Aşama 2'nin son kullanıcı tasarımı kullanıcı tarafından açıkça onaylandı ve kalıcı olarak `docs/STAGE2_STATISTICS_DESIGN.md` dosyasına kaydedildi.

#### Onaylanan yaklaşım

İstatistikler sayfası teknik ve kalabalık bir dashboard yerine sade bir **ilerleme ekranı** olacaktır:

- İstatistikler başlığı ve kısa açıklama
- Genel durum: çalışma, toplam süre, kelime, doğruluk
- Günlük / Haftalık / Aylık dönem seçici
- Yazma hızını zaman içinde gösteren grafik
- Doğruluk: doğru/yanlış kelimeler ve doğruluk yüzdesi
- Son çalışmaların sade geçmiş tablosu
- Gerçek veri yokken anlaşılır boş durum
- Responsive düzen
- Hafif, kısa ve dikkat dağıtmayan geçiş animasyonları

Gerçek SQLite verisi Aşama 3'e kadar bağlanmayacak ve sahte istatistik gösterilmeyecektir.

#### Sidebar ikon standardı

Tüm ana navigasyon öğeleri ikon + metin ile gösterilecektir:

- `keyboard-symbolic` — Çalışma Alanı
- `view-statistics-symbolic` — İstatistikler
- `preferences-system-symbolic` — Ayarlar

Mevcut overlay sidebar davranışı korunacaktır; sidebar çalışma alanını sıkıştırmayacaktır.

#### Yazma alanı güvenliği

Yazma pratiğinde kopyala/yapıştır ile metin girme veya çalışma sonucunu undo/redo ile değiştirme yolları kapatılacaktır. GTK4 TextView'ın yerleşik clipboard eylemleri devre dışı bırakılacak; normal klavye ile yazma ve mevcut backspace davranışı korunacaktır. PRIMARY clipboard ve sürükle-bırak gibi alternatif yollar da dikkate alınacaktır.

#### Aşama 2 uygulama sonucu

- Sidebar navigasyonu ve ikonları güncellendi.
- İstatistikler ekranı sade ilerleme yaklaşımına göre yeniden düzenlendi.
- Grafik yüzeyi ve boş durum hazırlandı; gerçek veri Aşama 3'e bırakıldı.
- Hafif bölüm açılma animasyonları eklendi.
- Yazma alanında clipboard kopyalama/kesme/yapıştırma ve undo/redo eylemleri kapatıldı.
- Kullanıcı arayüzündeki teknik `WPM`/`CPM` kısaltmaları korunmadı.

**Durum:** Uygulama kodu güncellendi; son görsel/stabilite doğrulaması kullanıcı tarafında yapılmalıdır. Aşama 3 henüz başlatılmayacaktır.

### Aşama 3 — Gerçek SQLite verilerinin istatistiklere bağlanması

- Tamamlanan çalışma kayıtları gerçek verilerle okunacak.
- Genel durum gerçek SQLite verilerinden hesaplanacak.
- Son çalışmaların tablosu gerçek geçmişi gösterecek.
- Günlük/haftalık/aylık grafikler gerçek çalışma verilerinden üretilecek.
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

## Aşama geçiş kuralı

Bir aşama tamamlan sayılmadan sonraki aşamanın koduna başlanmaz.

Her aşama sonunda:

1. Yapılan değişiklikler kontrol edilir.
2. Mevcut özelliklerin bozulmadığı doğrulanır.
3. Veri/mimari uyumluluk kontrol edilir.
4. Gerekirse geri dönüş noktası oluşturulur.
5. Sonraki aşamaya geçmeden önce plan yeniden değerlendirilir.

## İlgili mevcut roadmap

`ROADMAP.md` uzun vadeli özellik listesini, bu belge ise kabul edilmiş uygulama sırasını ve tasarım kararlarını tanımlar.
