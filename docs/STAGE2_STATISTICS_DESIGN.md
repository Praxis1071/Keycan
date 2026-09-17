# Keycan — Aşama 2 İstatistikler Sayfası Tasarım Belgesi

Bu belge, İstatistikler sayfasının kodlanmasından önce kabul edilen UX ve bilgi hiyerarşisini tanımlar. Aşama 2'nin amacı önce doğru ekran yapısını kesinleştirmek, Aşama 3'te ise bu yapıyı gerçek SQLite verileriyle beslemektir.

## 1. Temel hedef

İstatistikler sayfası kullanıcının yazma gelişimini teknik terimlere ihtiyaç duymadan anlamasını sağlamalıdır.

Ana dil:
- `Dakikada 42 kelime`
- `%96 doğruluk`
- `Dakikada 210 karakter`
- `5 dakika çalışma`

`WPM` ve `CPM` ana kullanıcı arayüzünde tek başına gösterilmeyecektir.

## 2. Sayfa düzeni

Sayfa üstten alta şu bilgi hiyerarşisini kullanacaktır:

1. Sayfa başlığı ve kısa açıklama
2. Genel özet kartları
3. Zaman aralığı seçici: `Günlük`, `Haftalık`, `Aylık`
4. Yazma gelişimi grafiği
5. Doğruluk / doğru-yanlış analizi
6. `Çalışmalarım` geçmiş tablosu

İlk sürümde gereksiz çok sayıda grafik veya ayar eklenmeyecektir.

## 3. Genel özet kartları

İlk sürüm için dört temel özet:

- **Toplam çalışma** — tamamlanan çalışma sayısı
- **Toplam süre** — toplam çalışma süresi
- **Toplam kelime** — yazılan toplam kelime
- **Ortalama doğruluk** — tamamlanan çalışmaların doğruluk özeti

Kartlar kısa tutulacak; ham alan adları kullanıcıya gösterilmeyecektir.

## 4. Zaman aralığı

Grafik ve özetlerde üç görünüm bulunacaktır:

- `Günlük`
- `Haftalık`
- `Aylık`

Varsayılan görünüm `Haftalık` olacaktır; böylece kullanıcının son günlerdeki ilerlemesi tek bakışta anlaşılabilir. Veri katmanı seçilen döneme göre yeniden sorgulanabilecek şekilde tasarlanacaktır.

## 5. Ana gelişim grafiği

Grafiğin amacı tek bir teknik değer göstermek değil, zaman içindeki gelişimi anlaşılır biçimde göstermektir.

Birincil ölçüm:
- Ortalama yazma hızı: `Dakikada X kelime`

Grafik noktalarının üzerine gelindiğinde/tıklandığında ilgili dönem için:
- çalışma sayısı
- ortalama hız
- ortalama doğruluk

gösterilebilecektir.

Grafik veri üretimi Aşama 3'te gerçek SQLite kayıtlarından yapılacaktır.

## 6. Doğruluk analizi

Ayrı bir bölümde:

- doğru kelimeler
- yanlış kelimeler
- doğruluk yüzdesi

anlaşılır biçimde gösterilecektir.

Burada mümkün olduğunca teknik grafik yerine kolay okunabilen oran/özet kullanılacaktır.

## 7. Çalışmalarım tablosu

Geçmiş çalışmaların ana listesi:

| Tarih | Ders | Süre | Sonuç | Doğruluk | Hız |
|---|---|---|---|---|---|
| 17 Eylül 2026, 18:30 | Ders 12 | 5 dakika | 184 kelime | %96 | Dakikada 37 kelime |

Kurallar:
- En yeni çalışma üstte olacaktır.
- Teknik sütun adları kullanılmayacaktır.
- Kaynak/ders snapshot bilgileri kullanılacaktır.
- Tablo boşsa kullanıcıya anlaşılır bir boş durum mesajı gösterilecektir.
- Çok sayıda kayıt için sayfalama veya kontrollü listeleme daha sonra değerlendirilebilir.

## 8. Boş durum

Henüz çalışma yapılmadıysa sahte istatistik gösterilmeyecektir.

Örnek mesaj:

> Henüz tamamlanmış bir çalışma yok.
> İlk çalışmanı tamamladığında ilerlemen burada görünecek.

## 9. Veri ve mimari sınırlar

Aşama 2'de:
- XP, seviye veya rozet hesaplanmayacaktır.
- Profil kodlanmayacaktır.
- Yeni çalışma metriği icat edilmeyecektir.
- SQLite şeması gereksiz yere değiştirilmemelidir.
- Yazma alanının davranışı değiştirilmemelidir.

Aşama 1'de hazırlanan çalışma kayıtları İstatistikler sayfasının tek temel veri kaynağı olacaktır.

## 10. Erişim ve gezinme

Mevcut overlay sidebar korunacaktır. Navigasyona `İstatistikler` öğesi eklenecek ve İstatistikler ayrı bir `Gtk.Stack` sayfası olacaktır.

Çalışma Alanı'nın geometrisi sidebar açılıp kapandığında bozulmamalıdır.

## 11. Responsive davranış

- Geniş ekranda özet kartları yatay dizilebilir.
- Dar ekranda kartlar alt alta veya iki sütun halinde düzenlenebilir.
- Tablo dar ekranda okunabilirliğini kaybetmemelidir; gerekirse sütunlar sadeleştirilecektir.
- Grafik yatay alanı doldurmalı, sabit piksel genişliğine bağlı olmamalıdır.

## 12. Aşama 2 tamamlanma kriterleri

Aşama 2 tamamlandı sayılmadan Aşama 3 koduna geçilmeyecektir.

Kontrol listesi:
- [x] Bilgi hiyerarşisi belirlendi.
- [x] Kullanıcı dili belirlendi.
- [x] Özet kartları belirlendi.
- [x] Günlük/haftalık/aylık yapı belirlendi.
- [x] Gelişim grafiğinin amacı belirlendi.
- [x] Doğruluk analizi belirlendi.
- [x] `Çalışmalarım` tablosu belirlendi.
- [x] Boş durum belirlendi.
- [x] Responsive yaklaşım belirlendi.
- [x] Sidebar entegrasyon noktası belirlendi.
- [ ] Tasarımın uygulama içinde kodlanması.
- [ ] Arayüzün görsel/stabilite kontrolü.
- [ ] Aşama 3'e geçmeden önce planın yeniden değerlendirilmesi.

**Durum:** Tasarım tanımlandı; uygulama kodlaması henüz başlatılmadı.
