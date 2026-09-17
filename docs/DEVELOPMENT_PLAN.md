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

**Durum:** Tamamlandı ve kontrol edildi.

### Aşama 2 — İstatistikler ve çalışma tercihleri

Aşama 2'nin son kullanıcı tasarımı, GNOME Human Interface Guidelines ve GTK4/libadwaita kalıpları araştırıldıktan sonra kullanıcı tarafından açıkça onaylandı.

#### İstatistikler

İstatistikler teknik ve kalabalık bir dashboard değil, kullanıcının yazma gelişimini takip ettiği sade bir ilerleme ekranıdır:

- kısa `İstatistikler` başlığı ve açıklama
- `Genel durum` içinde çalışma sayısı, toplam süre, toplam kelime ve doğruluk
- `Günlük / Haftalık / Aylık / Yıllık / Tümü` dönem seçici
- zaman içindeki yazma hızını gösteren gerçek grafik yüzeyi
- doğru kelimeler, yanlış kelimeler ve doğruluk özeti
- son çalışmalar için sade geçmiş tablosu
- gerçek veri yokken açık ve dürüst boş durum
- dar ve geniş pencerelere uyumlu düzen

`Tümü`, yalnızca toplam değer göstermeyecek; Aşama 3'te tüm çalışma geçmişindeki zaman serisini gösterecek şekilde veri sözleşmesine hazır tutulacaktır.

GNOME HIG araştırmasında her görünümün net bir odağa sahip olması, fazla öğeyle kullanıcıyı boğmamak, kısa ve anlaşılır metin kullanmak ve listeleri/adaptif kalıpları tercih etmek temel ilkeler olarak esas alınmıştır. citeturn1search0turn1search1turn1search3turn1search4turn1search9

GNOME System Monitor'ın kaynak grafiklerini hızlı genel bakış için kullanması ve GNOME Disk Usage Analyzer'ın grafik + yapılandırılmış liste yaklaşımı, Keycan'ın grafik ve geçmiş alanlarının bilgi yoğunluğunu belirlerken referans alınmıştır. citeturn0search0turn0search9

#### Sidebar ikon standardı

Tüm ana navigasyon öğeleri ikon + metin ile gösterilecektir:

- `keyboard-symbolic` — Çalışma Alanı
- `view-statistics-symbolic` — İstatistikler
- `preferences-system-symbolic` — Ayarlar

Mevcut overlay sidebar davranışı korunacaktır; sidebar çalışma alanını sıkıştırmayacaktır.

#### Tercihler

Çalışma alanının en altındaki mevcut **Durum + Tercihler + Metin boyutu** çubuğunda `Tercihler` butonu tam ortada yer alacaktır.

Tercihler, sidebar'daki uygulama ayarlarından ayrı bir çalışma-oturumu hızlı ayar yüzeyidir ve iki seçenek içerir:

- `Yazım metnini karart`
- `Geri tuşunu devre dışı bırak`

Bu iki seçenek genel `Ayarlar` sayfasında tekrarlanmayacaktır. Tercihler açılırken sade bir GTK/libadwaita popover ve standart switch row kalıbı kullanılacaktır. Libadwaita'nın `AdwPreferencesGroup` ve `AdwSwitchRow`/`AdwActionRow` kalıpları kısa tercih listeleri için kullanılabilir. citeturn0search15turn1search6

`AdwToolbarView` alt barı için mevcut GNOME/libadwaita yapısı korunacaktır; alt barın toolbar view içine yerleştirilmesi libadwaita'nın önerdiği kalıpla uyumludur. citeturn0search14

#### Yazma alanı güvenliği

Yazma pratiğinde kopyala/yapıştır ile metin girme veya çalışma sonucunu undo/redo ile değiştirme yolları kapatılacaktır. GTK4 TextView'ın yerleşik clipboard eylemleri devre dışı bırakılacak; PRIMARY clipboard, orta tuş ve sürükle-bırak gibi alternatif yollar da engellenecektir. Normal klavye yazımı korunacaktır.

#### Animasyon

Animasyonlar kısa ve işlevsel olacaktır. Sayfa/bölüm geçişleri veya gerçek verinin grafiğe bağlanması gerektiğinde yumuşak geçişler kullanılabilir; sürekli hareket, neon efektleri ve dikkat dağıtan animasyonlar kullanılmayacaktır. GNOME adaptif tasarım rehberindeki düzgün yeniden boyutlandırma ve standart widget kullanım ilkeleri temel alınacaktır. citeturn1search9

#### Aşama 2 uygulama sonucu

- Sidebar navigasyonu ve ikonları güncellendi.
- İstatistikler ekranı sade ilerleme yaklaşımına göre yeniden düzenlendi.
- Günlük/haftalık/aylık/yıllık/tümü dönem yapısı hazırlandı.
- Grafik yüzeyi ve gerçek veri için açık veri kancaları hazırlandı; sahte istatistik çizilmiyor.
- Doğruluk ve geçmiş alanları sade listeler/tablo yapısıyla hazırlandı.
- Çalışma alanının alt çubuğuna ortalanmış `Tercihler` eklendi.
- Ekranı karartma ve geri tuşunu devre dışı bırakma seçenekleri Tercihler'e taşındı.
- Yazma alanında clipboard kopyalama/kesme/yapıştırma, undo/redo, PRIMARY orta tuş ve sürükle-bırak yolları kapatıldı.

**Durum:** Kod güncellendi. Repo-local statik/runtime kontrolleri ve kullanıcı tarafındaki gerçek GTK görsel testi tamamlanmadan Aşama 3 başlatılmayacaktır.

### Aşama 3 — Gerçek SQLite verilerinin istatistiklere bağlanması

- Tamamlanan çalışma kayıtları gerçek verilerle okunacak.
- Genel durum gerçek SQLite verilerinden hesaplanacak.
- Son çalışmaların tablosu gerçek geçmişi gösterecek.
- Günlük/haftalık/aylık/yıllık/tümü grafik serileri gerçek çalışma verilerinden üretilecek.
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
