# Keycan — Aşama 2 İstatistikler Sayfası Tasarım Belgesi

Bu belge, Aşama 2'nin uygulama içinde nasıl görünmesi gerektiğini ve kullanıcı tarafından onaylanan son UX kararlarını tanımlar. Aşama 3'te aynı arayüz gerçek SQLite kayıtlarıyla beslenecektir.

## 1. Temel hedef

İstatistikler bir "teknik dashboard" değil, kullanıcının yazma gelişimini tek bakışta anlayabildiği sade bir **ilerleme ekranı** olacaktır.

Ana dil:
- `Dakikada 42 kelime`
- `%96 doğruluk`
- `Dakikada 210 karakter`
- `5 dakika çalışma`

`WPM` ve `CPM` ana kullanıcı arayüzünde tek başına gösterilmeyecektir.

## 2. Onaylanan bilgi hiyerarşisi

Sayfa üstten alta şu sırayı kullanacaktır:

1. **İstatistikler** — kısa ve anlaşılır açıklama
2. **Genel durum** — çalışma sayısı, toplam süre, toplam kelime, doğruluk
3. **Yazma hızın** — Günlük / Haftalık / Aylık seçici + gelişim grafiği
4. **Doğruluk** — doğru/yanlış kelime dengesi ve doğruluk yüzdesi
5. **Son çalışmaların** — geçmiş çalışmaların sade tablosu

Gereksiz ikinci derece kartlar, çok sayıda grafik veya teknik ayrıntı eklenmeyecektir.

## 3. Genel durum

Dört temel ölçüm gösterilecektir:

- **Çalışma** — tamamlanan çalışma sayısı
- **Toplam süre** — toplam çalışma süresi
- **Kelime** — yazılan toplam kelime
- **Doğruluk** — genel doğruluk özeti

Bu alan kısa tutulacak ve ham veritabanı alan adlarını göstermeyecektir.

## 4. Zaman aralığı

Grafik için üç görünüm bulunacaktır:

- `Günlük`
- `Haftalık`
- `Aylık`

Varsayılan görünüm `Haftalık` olacaktır. Seçim, Aşama 3'te aynı veri arayüzü üzerinden dönem sorgusunu değiştirecektir.

## 5. Gelişim grafiği

Grafik tek bir sayıyı büyük bir kart olarak göstermek yerine zaman içindeki değişimi görselleştirecektir.

Birincil ölçüm:
- Ortalama yazma hızı: `Dakikada X kelime`

Aşama 3'te grafik noktaları gerçek çalışma kayıtlarından üretilecektir. Bir nokta seçildiğinde ilgili dönem için çalışma sayısı, ortalama hız ve ortalama doğruluk gösterilebilecek şekilde tasarlanacaktır.

Aşama 2'de **sahte veri çizilmeyecektir**. Bunun yerine gerçek veri geldiğinde kullanılacak eksen/çizim yüzeyi ve anlaşılır boş durum hazırlanacaktır.

## 6. Doğruluk

Teknik ve kalabalık bir grafik yerine sade bir analiz alanı kullanılacaktır:

- doğru kelimeler
- yanlış kelimeler
- doğruluk yüzdesi

Aşama 3'te gerçek kayıtlar bağlandığında oran ve değerler burada gösterilecektir.

## 7. Son çalışmaların tablosu

Geçmiş çalışmaların ana listesi:

| Tarih | Ders | Süre | Sonuç | Doğruluk | Hız |
|---|---|---|---|---|---|
| 17 Eylül 2026, 18:30 | Ders 12 | 5 dakika | 184 kelime | %96 | Dakikada 37 kelime |

Kurallar:
- En yeni çalışma üstte olacaktır.
- Teknik sütun adları kullanılmayacaktır.
- Kaynak/ders snapshot bilgileri kullanılacaktır.
- Tablo boşsa anlaşılır boş durum mesajı gösterilecektir.
- Çok sayıda kayıt için kontrollü listeleme daha sonra değerlendirilebilir.

## 8. Boş durum

Henüz çalışma yapılmadıysa sahte istatistik gösterilmeyecektir.

Örnek:

> Henüz tamamlanmış bir çalışma yok.
> İlk çalışmanı tamamladığında ilerlemen burada görünecek.

## 9. Animasyon

Animasyonlar işlevsel ve hafif olacaktır:

- sayfa bölümleri kısa bir açılma/geçiş ile görünebilir
- gerçek veri geldiğinde grafik ve değerler yumuşak biçimde güncellenebilir
- sürekli hareket, neon efektleri ve dikkat dağıtan animasyonlar kullanılmayacaktır
- GTK/libadwaita'nın animasyon ve erişilebilirlik davranışlarıyla çelişen özel efektler eklenmeyecektir

## 10. Sidebar ve ikonlar

Overlay sidebar korunacaktır. Tüm ana navigasyon öğeleri ikon + metin ile gösterilecektir:

- `keyboard-symbolic` — Çalışma Alanı
- `view-statistics-symbolic` — İstatistikler
- `preferences-system-symbolic` — Ayarlar

Sidebar açılıp kapandığında çalışma alanının geometrisi değişmemelidir.

## 11. Yazma alanı güvenliği

Çalışma sırasında metin kopyalama/yapıştırma bir hızlandırma yolu olmamalıdır. GTK4'ün TextView yerleşik clipboard eylemleri kullanılarak:

- kopyalama
- kesme
- yapıştırma
- clipboard üzerinden kısayol kullanımı
- undo/redo ile yazılan metni değiştirme

çalışma alanında kapatılacaktır. Normal klavye ile yazma ve mevcut backspace davranışı korunacaktır.

Ayrıca sürükle-bırak/PRIMARY clipboard gibi alternatif yollar gözden geçirilecek ve kullanıcı tarafından kolayca aşılabilecek bir loophole bırakılmayacaktır.

## 12. Veri ve mimari sınırlar

Aşama 2'de:
- XP, seviye veya rozet hesaplanmayacaktır.
- Profil kodlanmayacaktır.
- Yeni çalışma metriği icat edilmeyecektir.
- SQLite şeması gereksiz yere değiştirilmemelidir.
- Gerçek istatistik verisi uydurulmayacaktır.

Aşama 1'de hazırlanan çalışma kayıtları Aşama 3'ün tek temel veri kaynağı olacaktır.

## 13. Responsive davranış

- Geniş ekranda genel durum ölçümleri yatay düzenlenebilir.
- Dar ekranda ölçümler otomatik olarak alt satırlara geçmelidir.
- Grafik mevcut genişliği doldurmalı ve sabit pencere genişliğine bağlı olmamalıdır.
- Geçmiş tablo dar ekranda taşma yaratmamalı; gerekirse yatay kaydırma kullanılmalıdır.
- Sidebar overlay olarak kalmalı ve çalışma alanını sıkıştırmamalıdır.

## 14. Aşama 2 tamamlanma kriterleri

- [x] Bilgi hiyerarşisi belirlendi.
- [x] Sade ilerleme ekranı yaklaşımı onaylandı.
- [x] Kullanıcı dili belirlendi.
- [x] Günlük/haftalık/aylık yapı belirlendi.
- [x] Gelişim grafiğinin amacı ve boş durumu belirlendi.
- [x] Doğruluk analizi belirlendi.
- [x] `Son çalışmaların` tablosu belirlendi.
- [x] Animasyon yaklaşımı belirlendi.
- [x] Sidebar ikonları belirlendi.
- [x] Kopyala/yapıştır güvenliği belirlendi.
- [x] Responsive yaklaşım belirlendi.
- [ ] Uygulama kodu son UX kararlarına göre tamamen doğrulanmalı.
- [ ] Arayüzün görsel/stabilite kontrolü kullanıcı tarafında yapılmalı.
- [ ] Aşama 3'e geçmeden önce plan yeniden değerlendirilmelidir.

**Durum:** Kullanıcı tarafından onaylanan tasarım uygulandı; gerçek SQLite bağlantısı Aşama 3'te yapılacaktır.
