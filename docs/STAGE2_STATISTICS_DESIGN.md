# Keycan — Aşama 2 İstatistikler Sayfası Tasarım Belgesi

Bu belge, Aşama 2'nin uygulama içinde nasıl görünmesi gerektiğini ve kullanıcı tarafından onaylanan son UX kararlarını tanımlar. Aşama 3'te aynı arayüz gerçek SQLite kayıtlarıyla beslenecektir.

## 1. Temel hedef

İstatistikler bir teknik dashboard değil, kullanıcının yazma gelişimini tek bakışta anlayabildiği sade bir **ilerleme ekranı** olacaktır.

Ana dil:
- `Dakikada 42 kelime`
- `%96 doğruluk`
- `Dakikada 210 karakter`
- `5 dakika çalışma`

`WPM` ve `CPM` ana kullanıcı arayüzünde tek başına gösterilmeyecektir.

## 2. Tasarım ilkeleri

GNOME HIG araştırmasından şu ilkeler doğrudan Keycan'a uygulanacaktır:

- Her görünümün net bir odağı olacak.
- Kullanıcı aynı anda gereğinden fazla bilgiyle boğulmayacak.
- Metin kısa ve kolay okunur olacak.
- Teknik sistem terimleri yerine kullanıcının yaptığı işe uygun terimler kullanılacak.
- Dinamik içerik ve geçmiş kayıtları için uyarlanabilir liste kalıpları kullanılacak.
- Geniş ekranlarda içerik sınırsız şekilde yayılmayacak; okunabilir bir maksimum genişlik korunacak.
- Standart GTK4/libadwaita bileşenleri tercih edilecek.

## 3. Bilgi hiyerarşisi

Sayfa üstten alta şu sırayı kullanacaktır:

1. **İstatistikler** — kısa ve anlaşılır açıklama
2. **Genel durum** — çalışma sayısı, toplam süre, toplam kelime, doğruluk
3. **Dönem** — Günlük / Haftalık / Aylık / Yıllık / Tümü
4. **Yazma hızı** — zaman içindeki gelişim grafiği
5. **Doğruluk** — doğru/yanlış kelimeler ve doğruluk yüzdesi
6. **Son çalışmalar** — geçmiş çalışmaların sade tablosu

Gereksiz ikinci derece kartlar, çok sayıda grafik veya teknik ayrıntı eklenmeyecektir.

## 4. Genel durum

Dört temel ölçüm gösterilecektir:

- **Çalışmalar** — tamamlanan çalışma sayısı
- **Toplam süre** — toplam çalışma süresi
- **Toplam kelime** — yazılan toplam kelime
- **Ortalama doğruluk** — çalışmaların genel doğruluk özeti

Aşama 2'de gerçek veri yoksa `Henüz veri yok` gösterilir; sayı uydurulmaz.

## 5. Zaman aralığı

Grafik için beş görünüm bulunacaktır:

- `Günlük`
- `Haftalık`
- `Aylık`
- `Yıllık`
- `Tümü`

Varsayılan görünüm `Haftalık` olacaktır.

`Tümü`, yalnızca bütün çalışmaların tek toplamını göstermeyecek; Aşama 3'te kullanıcının tüm geçmişindeki zaman serisini ve gelişim eğrisini gösterecek şekilde veri katmanına bağlanacaktır.

## 6. Gelişim grafiği

Grafik tek bir sayıyı büyük bir kart olarak göstermek yerine zaman içindeki değişimi görselleştirecektir.

Birincil ölçüm:
- Ortalama yazma hızı: `Dakikada X kelime`

Aşama 3'te grafik noktaları gerçek çalışma kayıtlarından üretilecektir. Dönem seçimine göre zaman serisinin çözünürlüğü değişecektir; örneğin günlük görünüm günleri, aylık görünüm ayları ve tüm geçmiş görünümü kayıtların kapsadığı uzun dönemi gösterebilir.

Aşama 2'de **sahte veri çizilmeyecektir**. Gerçek veri geldiğinde kullanılacak eksen/çizim yüzeyi ve anlaşılır boş durum hazırlanmıştır.

## 7. Doğruluk

Teknik ve kalabalık bir grafik yerine sade bir liste/analiz alanı kullanılacaktır:

- doğru kelimeler
- yanlış kelimeler
- doğruluk yüzdesi

Aşama 3'te gerçek kayıtlar bağlandığında değerler burada gösterilecektir.

## 8. Son çalışmalar tablosu

Geçmiş çalışmaların ana listesi:

| Tarih | Ders | Süre | Sonuç | Doğruluk | Hız |
|---|---|---|---|---|---|
| 17 Eylül 2026, 18:30 | Ders 12 | 5 dakika | 184 kelime | %96 | Dakikada 37 kelime |

Bu satır yalnızca tasarım örneğidir; uygulama Aşama 2'de bu veriyi göstermeyecektir.

Kurallar:
- En yeni çalışma üstte olacaktır.
- Teknik sütun adları kullanılmayacaktır.
- Kaynak/ders snapshot bilgileri kullanılacaktır.
- Tablo boşsa anlaşılır boş durum mesajı gösterilecektir.
- Çok sayıda kayıt için uyarlanabilir liste görünümü değerlendirilecektir.

## 9. Tercihler

Çalışma alanının en altındaki mevcut durum/metin boyutu çubuğunda `Tercihler` butonu **tam ortada** yer alacaktır:

`Durum  |  Tercihler  |  Metin boyutu`

Tercihler sidebar sayfası değildir. Aktif çalışma oturumuna ait hızlı seçenekleri açan sade bir popover'dır.

İçerik:

- **Yazım metnini karart** — yazarken girilen metni gizler
- **Geri tuşunu devre dışı bırak** — yazarken önceki karakteri silmeyi engeller

Bu iki seçenek genel `Ayarlar` sayfasında tekrar edilmeyecektir.

Tercihler yüzeyinde standart libadwaita switch row kalıbı kullanılacaktır.

## 10. Boş durum

Henüz çalışma yapılmadıysa sahte istatistik gösterilmeyecektir.

Örnek:

> Henüz tamamlanmış bir çalışma yok.
> İlk çalışmanı tamamladığında ilerlemen burada görünecek.

## 11. Animasyon

Animasyonlar işlevsel ve hafif olacaktır:

- bölüm geçişleri kısa bir açılma/geçiş ile görünebilir
- gerçek veri geldiğinde grafik ve değerler yumuşak biçimde güncellenebilir
- sürekli hareket, neon efektleri ve dikkat dağıtan animasyonlar kullanılmayacaktır
- pencere boyutu değişirken düzenin sert biçimde sıçramaması hedeflenecektir

## 12. Sidebar ve ikonlar

Overlay sidebar korunacaktır. Tüm ana navigasyon öğeleri ikon + metin ile gösterilecektir:

- `keyboard-symbolic` — Çalışma Alanı
- `view-statistics-symbolic` — İstatistikler
- `preferences-system-symbolic` — Ayarlar

Sidebar açılıp kapandığında çalışma alanının geometrisi değişmemelidir.

## 13. Yazma alanı güvenliği

Çalışma sırasında metin kopyalama/yapıştırma bir hızlandırma yolu olmamalıdır. GTK4 TextView yerleşik clipboard eylemleri kullanılarak:

- kopyalama
- kesme
- yapıştırma
- clipboard üzerinden kısayol kullanımı
- undo/redo ile yazılan metni değiştirme

çalışma alanında kapatılacaktır. Ayrıca PRIMARY clipboard/orta tuş ve sürükle-bırak yolları da kapatılacaktır.

Normal klavye ile yazma korunacaktır. `Geri tuşunu devre dışı bırak` tercihi kapalıysa normal geri tuşu çalışmaya devam eder.

## 14. Veri ve mimari sınırlar

Aşama 2'de:
- XP, seviye veya rozet hesaplanmayacaktır.
- Profil kodlanmayacaktır.
- Yeni çalışma metriği icat edilmeyecektir.
- SQLite şeması gereksiz yere değiştirilmemelidir.
- Gerçek istatistik verisi uydurulmayacaktır.

Aşama 1'de hazırlanan çalışma kayıtları Aşama 3'ün temel veri kaynağı olacaktır.

## 15. Responsive davranış

- Geniş ekranda içerik okunabilir maksimum genişlikte tutulacaktır.
- Dar ekranda liste ve özet alanları alt alta akmalıdır.
- Grafik mevcut genişliği doldurmalı ve sabit pencere genişliğine bağlı olmamalıdır.
- Geçmiş tablosu dar ekranda taşma yaratmamalı; gerektiğinde uyarlanabilir liste/yatay kaydırma kullanılmalıdır.
- Sidebar overlay olarak kalmalı ve çalışma alanını sıkıştırmamalıdır.

## 16. Aşama 2 uygulama durumu

- [x] Sade ilerleme ekranı yaklaşımı uygulandı.
- [x] Genel durum bölümü hazırlandı.
- [x] Günlük/haftalık/aylık/yıllık/tümü seçimi hazırlandı.
- [x] Gerçek veri için grafik çizim yüzeyi hazırlandı.
- [x] Doğruluk analizi hazırlandı.
- [x] Son çalışmalar tablosu için sade yapı hazırlandı.
- [x] Tercihler butonu alt çubuğun tam ortasına yerleştirildi.
- [x] Ekranı karartma tercihi Tercihler'e taşındı.
- [x] Geri tuşunu devre dışı bırakma tercihi eklendi.
- [x] Sidebar ikonları standart symbolic ikonlarla düzenlendi.
- [x] Clipboard, PRIMARY/orta tuş ve sürükle-bırak yolları ele alındı.
- [ ] Repo-local statik/runtime kontrolleri tamamlanmalı.
- [ ] Kullanıcı tarafında gerçek GTK görsel/stabilite testi yapılmalı.

**Durum:** Aşama 2 kodu güncellendi. Gerçek SQLite bağlantısı Aşama 3'te yapılacaktır.
