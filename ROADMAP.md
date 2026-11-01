# Keycan Geliştirme Yol Haritası

Keycan'ın mevcut durumu ve gelecekteki geliştirme planı.

## 🧭 Aşama Durumu

### ✅ Aşama 0 — Temel Mimari
- GTK4 + libadwaita tabanlı uygulama yapısı
- SQLite tabanlı yerel veri altyapısı
- Temel uygulama ve pencere mimarisi

### ✅ Aşama 1 — Temel Yazma Deneyimi
- On parmak klavye pratiği
- Ders ve metin seçimi
- Ayarlanabilir çalışma süresi
- Doğru / yanlış sonuçları
- Yazma deneyiminin temel ayarları

### ✅ Aşama 2 — İstatistik ve Veri Altyapısı
- SQLite tabanlı çalışma sonuçlarının kaydedilmesi
- Çalışma geçmişi
- Temel istatistikler
- Aktivite verilerinin tutulması

### ✅ Aşama 3 — İçerik ve Veri Yönetimi
- Yerleşik ve özel ders grupları
- Ders gruplarını yeniden adlandırma
- Metin ekleme, düzenleme, silme ve sıralama
- Varsayılan içerikleri geri yükleme
- Tüm ders ve metinleri sıfırlama
- Veritabanı katmanında JSON yedekleme/geri yükleme uyumluluğu (kullanıcı arayüzündeki seçenekler daha sonra kaldırıldı)
- Kopyala/yapıştır ve metin aktarımı açıklarının engellenmesi

### ✅ Aşama 4 — 2.3.x Bakım ve Hata Düzeltmeleri
Bu aşama yeni bir özellik geliştirme aşaması değildir. 2.2.0 sonrasında kullanıcı tarafından bildirilen kullanım ve kararlılık sorunları giderilmiş, mevcut özelliklerin güvenilirliği artırılmıştır.

- GTK4 widget hiyerarşisi ve yeniden ebeveynleme kaynaklı çökme sorunlarının giderilmesi
- Ders grubu listesinin güvenli biçimde yenilenmesi
- Runtime çeviri backreference hatasının giderilmesi
- Ders grubu yönetiminde yeniden adlandırma akışının iyileştirilmesi
- Mevcut özelliklerin bozulmasını önleyen bakım çalışmaları

Responsive arayüz ve temel stabilizasyon çalışmaları tamamlanmıştır; ayrı bir gelecek hedefi değildir.

---

## ✅ Aşama 5 — Gelişmiş İstatistikler

Keycan'ın mevcut istatistik altyapısını daha ayrıntılı bir performans analiz sistemine dönüştürmek.

- Günlük / haftalık / aylık / yıllık / tüm zamanlar istatistikleri
- Uzun dönemli WPM gelişimi
- Uzun dönemli doğruluk gelişimi
- Toplam çalışma süresi
- Toplam kelime / karakter
- Ders bazlı performans
- Ayrıntılı dönem filtreleri
- İstatistik ekranının Genel, Gelişim, Dersler ve Rekorlar olarak ayrıştırılması
- Dönem karşılaştırmaları
- Rekor geçmişi
- Ayrıntılı performans analizi
- Otomatik istatistik test altyapısı

---

## ✅ Aşama 6 — Kullanıcı Deneyimi

- Sistem / açık / koyu tema seçenekleri
- Tema değişikliğinin anında uygulanması
- Tema tercihinin kalıcı olarak saklanması
- Türkçe / İngilizce dil sistemi
- Dil değişikliğinin uygulama yeniden başlatılmadan anında uygulanması
- Dil tercihinin kalıcı olarak saklanması
- Merkezi ve GTK arayüzünden bağımsız çeviri kataloğu
- Dinamik oluşturulan arayüz metinlerinin çevrilmesi
- Preferences ve translation servislerinin `main.py` dışında tutulması
- Stage 6 otomatik testleri ve CI Python modül doğrulaması
- Atomik preference dosyası yazımı
- GTK4 widget hiyerarşisi ve ders grubu yönetimi kararlılık düzeltmeleri

---

## ✅ Aşama 7 — Profil, XP, Seviye ve Rozet Sistemi

Sidebar'da İstatistikler'den bağımsız, ayrı bir **Profil** bölümü oluşturuldu.

- Yerel ve hesap gerektirmeyen XP sistemi
- Tamamlanan çalışmalardan deterministik XP hesaplama
- XP tabanlı seviye sistemi ve ilerleme çubuğu
- Mevcut ve en uzun çalışma serisinin takibi
- Çalışma sayısı, XP ve ilerleme özeti
- 12 kilometre taşından oluşan başarı rozeti sistemi
- Rozetlerin mevcut çalışma geçmişinden otomatik türetilmesi
- Profil verilerinin SQLite çalışma geçmişinden beslenmesi
- İstatistikler ile profil ilerlemesinin ayrı tutulması
- Türkçe / İngilizce profil arayüzü
- Mevcut GTK4 + libadwaita tasarımına uyumlu profil ekranı
- Stage 7 progression ve persistence davranışları için otomatik testler

---

## ✅ Aşama 8 — Gelişmiş Yerel Profil

Aşama 7'de oluşturulan temel Profil sisteminin daha kapsamlı ve kişiselleştirilebilir hale getirilmesi.

- Kullanıcının kendi ismini girebilmesi
- Profil fotoğrafı seçebilme ve değiştirebilme
- Profil bilgilerinin yerel olarak saklanması
- Profil fotoğrafının yerel olarak saklanması
- Profil özeti
  - Toplam çalışma sayısı
  - Toplam çalışma süresi
  - Genel yazma hızı
  - Genel doğruluk
  - Tamamlanan dersler
  - Genel ilerleme
- Profil üzerinden son çalışma geçmişinin görüntülenmesi
- Profilin mevcut çalışma ve istatistik altyapısıyla bağlantısının genişletilmesi
- Online hesap veya bulut senkronizasyonu olmadan yerel profil yapısının geliştirilmesi

---

## ✅ Aşama 9 — Klavye Rehberi

Sidebar'da İstatistikler ve Profil'den bağımsız, ayrı bir **Klavye Rehberi** bölümü oluşturulacak.

Kullanıcının 10 parmak yazmayı öğrenmesine yardımcı olan, açıklayıcı ve uygulamaya dönük bir rehber alanı olacak.

- 10 parmak yazma nedir?
- Doğru oturuş ve el pozisyonu
- Başlangıç / home row
- F ve J tuşlarındaki yön bulma çıkıntıları
- Sol el parmaklarının görevleri
- Sağ el parmaklarının görevleri
- Hangi parmağın hangi tuşa bastığı
- Üst sıra, ana sıra ve alt sıra tuşları
- Boşluk tuşu ve başparmak kullanımı
- Klavyeye bakmadan yazma
- Doğruluk ve hız ilişkisi
- Yeni başlayanların sık yaptığı hatalar
- Rehberden öğrenilenleri Çalışma Alanında pratiğe taşıma

---

## 🏗️ Aşama 10 — Mimari İyileştirme, Stabilizasyon ve Depo Kalitesinin Artırılması

Aşama 0–9 ile tamamlanan kullanıcı özellikleri korunarak Keycan'ın kod tabanı, veri yönetimi, test altyapısı, paketleme süreci ve dokümantasyonu iyileştirilecektir.

Bu aşama yeni kullanıcı özellikleri ekleme veya uygulamayı baştan yazma çalışması değildir. Öncelik; mevcut uygulamayı daha güvenilir, sürdürülebilir, bakımı kolay ve dağıtıma hazır hâle getirmektir.

### Değişmez kurallar

- Yazma motorunun (keycan/core/typing_engine.py) davranışı değiştirilmeyecek; yalnızca mevcut testleriyle doğrulanacak.
- Mevcut kullanıcı özellikleri, ders içerikleri, çalışma geçmişi, istatistikler ve profil ilerlemesi korunacak.
- Kullanıcı verisi üzerinde geri dönüşü olmayan işlem yapılmayacak; riskli geçişlerden önce doğrulanabilir yedek alınacak.
- Her değişiklik küçük, izole, gözden geçirilebilir ve geri alınabilir olacak.
- Her aşamanın test ve doğrulama kapısı geçilmeden sonraki aşamaya başlanmayacak.
- Gereksiz soyutlama, bağımlılık, teknoloji veya klasör eklenmeyecek.
- Kullanıcıya görünen davranış ancak açıkça onaylanmış bir hata düzeltmesi gerektiriyorsa değiştirilecek.

### Gelişim planı

1. **Mimari ve bağımlılık denetimi**
   - Giriş noktaları, import zincirleri, modül sorumlulukları ve veri akışları haritalanacak.
   - GUI, servisler, SQLite ve JSON arasındaki mevcut sınırlar incelenecek.
   - Testler, CI iş akışları, paketleme ve bilinen hatalar envanterlenecek.
   - Statik inceleme ile çalışma zamanı doğrulaması ayrı raporlanacak.
   - Mevcut davranışlar ve veri bütünlüğü için başlangıç kontrol listesi oluşturulacak.

2. **Veri mimarisinin netleştirilmesi**
   - Paketle gelen hazır ders kataloğunun JSON kaynakları belirlenecek.
   - Kullanıcı tarafından oluşturulan dersler ve hazır dersler üzerindeki kişisel değişikliklerin kalıcı olarak nerede tutulacağı (mevcut SQLite modeli mi, JSON deposu/override mı) karşılaştırmalı olarak değerlendirilecek; karar veri kaybı riski, kullanım kolaylığı, tutarlılık ve bakım maliyetine göre verilecek.
   - Çalışma oturumları, istatistikler ve geçmiş gibi işlem kayıtlarının SQLite'ta kalması temel yaklaşım olacak.
   - Paketlenmiş hazır ders kataloğunun JSON olması ile kullanıcı tarafından düzenlenebilir içeriğin depolanma biçimi birbirinden ayrı kararlar olarak ele alınacak.
   - JSON ve SQLite'ın görevleri, kararlı kimlikler, şema sürümü, hata davranışı ve yedekleme sözleşmesi açıkça belgelenecek.
   - Herhangi bir veri taşıma kararı verilirse çalışma geçmişi veya profil hesaplamalarının kopmadığı testlerle kanıtlanacak.

3. **Ders kataloğu ve içerik kalitesinin iyileştirilmesi**
   - JSON şeması, kimlik benzersizliği ve içerik doğrulama kuralları testlerle güvence altına alınacak.
   - Ders/grup adları ve metinleri için planlanan sadeleştirme önce yalnızca önizleme ve rapor olarak üretilecek.
   - Türkçe karakterler ve metin anlamı korunacak; boşalan, birleşen veya yinelenen içerikler raporlanacak.
   - Kullanıcı onayı ve yedek olmadan mevcut içerik topluca değiştirilmeyecek.

4. **Veri geçişi ve kalıcılık güvenliği**
   - Önceki aşamada JSON/SQLite sorumlulukları için onaylanan hedef modele göre gerekiyorsa eski SQLite ders içeriği kontrollü ve tekrarlanabilir biçimde taşınacak.
   - Veri taşıma yapılması zorunlu değilse sırf teknoloji değişikliği amacıyla mevcut ve çalışan SQLite kullanıcı içeriği katmanı değiştirilmeden korunacak.
   - Herhangi bir geçişte eski ve yeni veriler kimlik, kayıt sayısı ve içerik karşılaştırmalarıyla doğrulanacak.
   - Geçiş tamamlanmadan eski tablolar silinmeyecek.
   - Transaction, atomik dosya yazımı, bozuk dosya, yarım kalmış işlem, yedek alma/geri yükleme ve geriye dönük uyumluluk test edilecek.

5. **Yinelenen modüller ve runtime müdahalelerinin sadeleştirilmesi**
   - Monkey-patch ve import yan etkileri açıkça tanımlanmış normal metot/servis tasarımına taşınacak.
   - Yinelenen veritabanı, istatistik ve ayar modülleri import/çağrı/test analiziyle karşılaştırılacak.
   - Kullanılmayan dosyalar ancak yerine geçen davranış ve uyumluluk kanıtlandıktan sonra kaldırılacak.

6. **Pencere ve GUI sorumluluklarının azaltılması**
   - window.py üst seviye pencere, navigasyon ve koordinasyon görevleriyle sınırlandırılacak.
   - Ders seçimi, çalışma oturumu yaşam döngüsü, kayıt ve sayfa güncelleme sorumlulukları gerektiği ölçüde ayrılacak.
   - GTK sinyalleri, widget yaşam döngüsü, uygulama kapanışı ve bekleyen kayıtlar korunacak.
   - Sırf mimari görünmesi için gereksiz controller/manager katmanları oluşturulmayacak.

7. **Veritabanı ve servis katmanlarının iyileştirilmesi**
   - SQL erişimi GUI katmanından ayrılacak; gerekli yerlerde açık repository/servis sınırları kurulacak.
   - Şema migrasyonları, transaction yönetimi, bağlantı yaşam döngüsü ve hata raporlama sadeleştirilecek.
   - Paket kaynakları ile kullanıcının yazılabilir veri dizini ayrılacak.
   - Tercihler, çeviri, ders ve ilerleme servislerinin sorumlulukları netleştirilecek.

8. **Test, CI ve regresyon güvencesi**
   - check.sh ve GitHub Actions iş akışları güncel proje yapısıyla tutarlı tutulacak.
   - Birim testleri, tam regresyon paketi ve veri bütünlüğü kontrolleri güçlendirilecek.
   - GTK açılış/kapanış, sayfa geçişleri, ders yönetimi, yazma oturumu, gizlilik, profil, istatistik ve yedekleme akışları doğrulanacak.
   - Eski verilerden geçiş ve başarısız işlem/rollback senaryoları test edilecek.
   - Başarısız test veya açıklanmamış veri farkı varken sonraki aşamaya geçilmeyecek.

9. **Flatpak, sürümleme ve dokümantasyon**
   - Flatpak manifesti, uygulama sürümü, bağımlılıklar, izinler ve dağıtım çıktıları gözden geçirilecek.
   - Tekrarlanabilir yerel derleme ve doğrulama adımları belgelenecek.
   - Uygun olduğunda GitHub Actions üzerinden otomatik test, paketleme ve release hazırlığı değerlendirilecek.
   - README, kurulum/build talimatları, hata kaydı, mimari belgeler ve yedekleme politikası güncel gerçekle eşleştirilecek.
   - Eski veya birbiriyle çelişen plan belgeleri tek güncel teknik kaynağa yönlendirilecek ya da arşivlenecek.

Ayrıntılı teknik sıra, hedef veri modeli, güvenlik kapıları ve her aşamanın tamamlanma koşulları: [Mimari İyileştirme Yol Haritası](docs/ARCHITECTURE_REFACTOR_ROADMAP.md).

**Durum:** Aşama 10 onaylandı. İlk iş, mevcut mimari denetimini güncel main dalı ve gerçek test sonuçlarıyla tamamlamak; henüz veri migrasyonu veya büyük refaktör başlatılmayacak.

## 🏁 Mevcut Yol Haritasının Durumu

Aşama 0–9 tamamlandı. Aşama 10, yeni özelliklerden önce mevcut uygulamanın mimarisini, veri yönetimini ve sürdürülebilirliğini iyileştirmeye odaklanır.

## 📌 Yol Haritasının Sınırları

Bu roadmap, Keycan'ın mevcut hedeflerini ve onaylanan gelecek geliştirmelerini tanımlar. Aşağıdaki fikirler mevcut roadmap'e dahil değildir:

- Katiplik modu
- Online hesap ve online özellikler
- Bulut senkronizasyonu
- Odak / Pomodoro modu
- Akıllı eğitim / adaptif ders sistemi

Yeni özellikler eklenmeden önce mevcut mimarinin korunması ve kullanıcı geri bildirimlerinin değerlendirilmesi önceliklidir.
