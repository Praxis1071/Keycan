# Keycan – Stabilizasyon Hata Kaydı

Bu dosya, 31 Ekim 2026 tarihinde yapılan kullanıcı testleri ve kod incelemesi sırasında belirlenen sorunları takip etmek için oluşturulmuştur.

## Kapsam ve kurallar

- Bu belge hata envanteridir; tek başına bir düzeltme veya değişiklik talimatı değildir.
- Kullanıcı tarafından gerçek kullanımda doğrulanan sorunlar ile yalnızca kod incelemesinde görülen riskler ayrı tutulur.
- Henüz çalışma zamanı kanıtı bulunmayan ihtimaller kesin hata gibi sunulmaz.
- Düzeltmeler küçük ve izole olmalı; her düzeltmeden sonra ilgili testler ve regresyon kontrolleri çalıştırılmalıdır.
- Sorunsuz çalıştığı kullanıcı tarafından doğrulanan özellikler korunmalıdır.
- Bu kayıt oluşturulurken uygulama kodunda hiçbir değişiklik yapılmamıştır.

---

## Hata özeti

| ID | Alan | Durum | Öncelik |
|---|---|---|---|
| KC-001 | Gizlilik modu – oturum sonuçlarının gösterilmesi | Kod düzeltmesi uygulandı; GTK çalışma zamanı testi bekleniyor | Yüksek |
| KC-002 | Gizlilik modu – sonuçların istatistiklere kaydedilmesi | Kayıt hata yönetimi ve transaction güvenliği düzeltildi; kullanıcı testi bekleniyor | Kritik |
| KC-003 | Yedek/istatistik içe aktarma | Kod düzeltildi; varsayılan ders ve kimlik çakışması regresyon testleri geçti | Yüksek |
| KC-004 | İngilizce arayüzde eksik çeviriler | Tek çeviri kaynağı ve widget kapsamı düzeltildi; CI testleri geçti | Orta |
| KC-005 | İstatistik/profil ilerlemesi sıfırlama adı ve fotoğraf kaldırma seçeneği | Arayüz ve fotoğraf işlemleri uygulandı; GTK çalışma zamanı testi bekleniyor | Orta |

---

## KC-001 – Gizlilik modu açıkken oturum sonuçlarının gösterilmemesi

**Durum:** Kullanıcı testiyle doğrulandı.

**Belirti:**
- Yazım metnini karartma seçeneği açıkken çalışma başlatılıp tamamlandığında sol altta doğru, yanlış ve toplam kelime sayıları gösterilmiyor.

**Beklenen davranış:**
- Gizlilik modu yalnızca yazılan metnin görünürlüğünü etkilemeli.
- Oturum tamamlandığında doğru, yanlış ve toplam kelime sayıları normal moddaki gibi gösterilmeli.
- Gizlilik etiketi sonuçların gösterilmesi sırasında kaldırılmamalı.

**İncelemede görülen kod noktaları:**
- `keycan/window.py` – `_apply_privacy_state()`
- `keycan/window.py` – `_render_input_results()`

**Kod incelemesindeki bulgu:**
- `_render_input_results()` içinde metin aralığına uygulanan tüm etiketleri kaldıran `buffer.remove_all_tags(start, end)` çağrısı bulunuyor.
- Bu çağrı doğru/yanlış biçimlendirme etiketleriyle birlikte gizlilik için kullanılan `privacy-hidden` etiketini de kaldırabilir.
- Dolayısıyla sonuçların çizilmesi sırasında gizlilik etiketinin kaybolması riski kod seviyesinde görülmüştür.

**Henüz doğrulanması gerekenler:**
- Sonuçların sol altta gösterilmemesinin doğrudan bu etiket temizleme işleminden mi, yoksa sonuç hesaplama/arayüz güncelleme akışından mı kaynaklandığı çalışma anında doğrulanmalı.
- Gizlilik modu açık ve kapalıyken aynı metinle sonuç hesaplama çıktıları karşılaştırılmalı.

**İlgili regresyon kontrolleri:**
- Gizlilik kapalı: sonuç sayaçları görünür ve doğru olmalı.
- Gizlilik açık: sonuç sayaçları görünür ve doğru olmalı; yazılan metin gizli kalmalı.
- Oturum tamamlandıktan sonra gizlilik durumu bozulmamalı.

---

## KC-002 – Gizlilik modu açıkken çalışma sonuçlarının istatistiklere kaydedilmemesi

**Durum:** Kullanıcı testiyle doğrulandı; kesin çalışma zamanı kök nedeni henüz belirlenmedi.

**Belirti:**
- Gizlilik modu açıkken tamamlanan çalışma istatistik geçmişine eklenmiyor.

**Beklenen davranış:**
- Gizlilik modu yalnızca metnin ekranda gösterilmesini kontrol etmeli.
- Çalışma süresi, doğru/yanlış kelime ve karakter sayıları, hız ve doğruluk gibi sonuçlar normal modla aynı kurallarla kaydedilmeli.
- Kullanıcı gizlilik modunu açtığı için istatistik kaydı kaybolmamalı.

**İncelenecek kod noktaları:**
- `keycan/window.py` – `_on_input_changed()`
- `keycan/window.py` – `_finish_now()`
- `keycan/data/database.py` – `save_result()`
- `keycan/data/database_runtime.py` – çalışma zamanı veritabanı metotları

**Kod incelemesindeki bulgular:**
- İncelenen akışta gizlilik seçeneğinin doğrudan `save_result()` çağrısını engellediği bir koşul görülmedi.
- Metin tamponunun içeriği `Gtk.TextBuffer.get_text(..., True)` ile okunuyor; bu kullanım görünürlüğü kapatılmış karakterleri de okumaya izin verir.
- `_finish_now()` içinde `self.finished = True` ataması veritabanı kaydından önce yapılıyor. Kayıt sırasında hata oluşursa oturum tamamlanmış olarak kalabilir ve normal tamamlama akışı yeniden çalışmayabilir.
- Bu sıralama kayıt hatasının kullanıcıya yansıtılmasını ve tekrar denenmesini zorlaştırabilir; fakat kullanıcının gördüğü hatanın kesin sebebi olduğu henüz kanıtlanmadı.

**Henüz doğrulanması gerekenler:**
- Gizlilik açık/kapalı oturumlarda `save_result()` çağrısına ulaşılıp ulaşılmadığı.
- `save_result()` çağrısının hata verip vermediği ve varsa hata mesajı.
- Oturum sonucunun hesaplanması sırasında gizlilik moduna bağlı boş/eksik veri oluşup oluşmadığı.
- Veritabanında kayıt oluşmadığında işlem öncesi/sonrası satır sayısı.

**İlgili regresyon kontrolleri:**
- Her iki gizlilik durumunda da birer oturum tamamlanmalı.
- İki oturum da veritabanına tam birer kayıt eklemeli.
- Aynı oturum için çift kayıt oluşmamalı.
- Kayıt başarısızlığı uygulamayı kilitlememeli veya oturumu sessizce kaybettirmemeli.

---

## KC-003 – İstatistikleri/yedeği içe aktarma işleminin çalışmaması

**Durum:** Kullanıcı testiyle doğrulandı; veri eşleştirmesinde somut risk bulundu.

**Belirti:**
- Ayarlar bölümünden istatistikleri dışa aktarma ve sıfırlama çalışıyor.
- Daha önce dışa aktarılan yedeği içe aktarma işlemi çalışmıyor.

**Beklenen davranış:**
- Keycan tarafından dışa aktarılan geçerli yedek tekrar içe aktarılabilmeli.
- Özel ders grupları, dersler ve çalışma geçmişi doğru ilişkilendirilmeli.
- Varsayılan derslere ait çalışma geçmişi de başka bir veritabanına taşındığında korunmalı.
- Bozuk/uyumsuz dosya uygulamayı çökertmemeli ve veritabanında yarım aktarım bırakmamalı.

**İncelenecek kod noktaları:**
- `keycan/gui/settings2.py` – içe aktarma dosya seçimi ve çağrı akışı
- `keycan/data/database_runtime.py` – `_export_data()` ve içe aktarma metodu
- `keycan/data/database.py` – veritabanı şeması ve kayıt işlemleri

**Kod incelemesindeki bulgu:**
- Dışa aktarma sırasında varsayılan ders grupları/dersler için `default:<id>` biçiminde anahtar üretilebiliyor.
- Çalışma sonuçları dışa aktarılırken `lesson_key` değerinin `l.custom_key` alanından alınması, bu alan varsayılan derslerde boş olduğunda tutarlı bir anahtar üretmeyebilir.
- İçe aktarma eşleştirmesi önce anahtar, ardından eski kimlik ve diğer alanlar üzerinden ilerliyor.
- Bu durum özellikle farklı bir veritabanına/kuruluma taşınan varsayılan ders sonuçlarının doğru dersle eşleştirilmesini bozabilir.
- Mevcut `tests/test_custom_content.py` yedek geri yükleme testi özel ders grubu senaryosunu kapsıyor; varsayılan ders çalışma geçmişinin farklı veritabanına taşınması ayrıca doğrulanmalı.

**Henüz doğrulanması gerekenler:**
- Kullanıcının içe aktarmaya çalıştığı yedek dosyasının biçimi ve hata anındaki arayüz davranışı.
- İçe aktarma dosyasının okunması, JSON çözümlemesi, şema doğrulaması ve veritabanına yazılması aşamalarından hangisinde hata oluştuğu.
- Aynı veritabanına ve temiz/farklı veritabanına aktarma sonuçlarının karşılaştırılması.
- Varsayılan ve özel ders sonuçlarının ayrı ayrı eşleştirilmesi.
- Aktarımın transaction/rollback davranışı.

**İlgili regresyon kontrolleri:**
- Özel ders grubu ve çalışma geçmişi round-trip.
- Varsayılan ders ve çalışma geçmişi round-trip.
- Aynı yedeğin farklı/temiz veritabanına aktarılması.
- Yinelenen kayıt ve çakışan ders senaryoları.
- Bozuk JSON, eksik alan ve desteklenmeyen sürüm.
- Hata sırasında rollback ve mevcut verinin korunması.

---

## KC-004 – İngilizce dil seçildiğinde arayüzün tamamının çevrilmemesi

**Durum:** Kullanıcı testiyle doğrulandı; çeviri mimarisinde eksiklik bulundu.

**Belirti:**
- Türkçe ve İngilizce dil seçenekleri çalışıyor.
- İngilizce seçildiğinde arayüzün büyük bölümü çevriliyor ancak bazı metinler Türkçe kalıyor.

**Beklenen davranış:**
- Uygulamanın kendi arayüz metinleri İngilizce seçildiğinde tutarlı biçimde İngilizce gösterilmeli.
- Kullanıcının oluşturduğu ders/grup/metin içerikleri çevrilmemeli.
- Dil değiştirme ve uygulamayı yeniden başlatma davranışı tutarlı olmalı.

**İncelenecek kod noktaları:**
- `keycan/services/i18n.py`
- `keycan/services/translations.py`
- Dilin uygulandığı pencere, sayfa ve dinamik widget oluşturma noktaları

**Kod incelemesindeki bulgular:**
- `i18n.py` içinde ayrı bir `TRANSLATIONS` sözlüğü bulunuyor.
- Ayrıca `translations.py` dosyasında başka bir çeviri mekanizması mevcut.
- Widget ağacı çevirisi `i18n.py` içindeki sözlüğü kullanıyor; iki kaynağın kapsamı aynı değil.
- `apply_to_widget_tree()` belirli GTK/Libadwaita widget türlerini işliyor. Örneğin `Adw.SwitchRow` için açık bir çeviri dalı görünmüyor.
- Bu nedenle çeviri sözlüğünde karşılığı olsa dahi bazı widget metinleri çevrilmeden kalabilir.

**Henüz doğrulanması gerekenler:**
- Uygulamanın tüm sayfalarındaki çevrilmeden kalan metinlerin tam listesi.
- Dinamik olarak sonradan oluşturulan widget'ların dil değişiminden etkilenip etkilenmediği.
- Çeviri kaynaklarının hangi ekranlarda ve hangi sırayla çağrıldığı.
- Türkçeye geri dönüldüğünde daha önce çevrilmiş metinlerin doğru geri yüklenmesi.

**İlgili regresyon kontrolleri:**
- Ana pencere, çalışma alanı, istatistikler, profil, klavye rehberi ve ayarlar.
- Dinamik açılan iletişim pencereleri ve yönetim ekranları.
- Türkçe → İngilizce → Türkçe geçişi.
- Kullanıcı tarafından oluşturulmuş ders/grup/metin adlarının değişmeden kalması.


---

## KC-005 – İstatistikleri/profil ilerlemesini sıfırlama adının ve fotoğraf kaldırma seçeneğinin eksikliği

**Durum:** Kullanıcı tarafından gerçek kullanımda doğrulandı; kod incelemesi mevcut davranışı destekliyor.

**Belirti:**
- Ayarlardaki “İstatistikleri sıfırla” işlemi çalışma geçmişini temizliyor. Profilde çalışma geçmişinden hesaplanan seviye, XP, rozet ve ilerleme bilgileri de doğal olarak sıfırlanıyor.
- Bu nedenle mevcut işlem adının kapsamı tam anlatması için “İstatistikleri ve profili sıfırla” olarak değiştirilmesi gerekiyor.
- Profil sekmesinde daha önce seçilmiş fotoğraf görüntülenmeye devam ediyor ve fotoğrafı kaldırmak için ayrı bir seçenek bulunmuyor.

**Beklenen davranış:**
- Ayarlar bölümündeki “İstatistikleri sıfırla” seçeneğinin adı **“İstatistikleri ve profili sıfırla”** olarak değiştirilmeli.
- Bu işlem istatistik/çalışma geçmişini temizlemeli; bu geçmişten hesaplanan profil seviye, XP, rozet ve ilerleme bilgileri de sıfırlanmalı.
- Bu işlem profil adı veya profil fotoğrafını silmemeli. Profil fotoğrafını kaldırmak ayrı ve bağımsız bir işlem olmalı.
- Profil bölümünde “Profil fotoğrafı seç” düğmesinin yanında veya yakınında **“Profil fotoğrafını kaldır”** seçeneği bulunmalı.
- Fotoğraf kaldırıldığında kayıtlı fotoğraf dosyası ve profil fotoğrafı referansı güvenli biçimde temizlenmeli; avatar varsayılan görünümüne dönmeli.
- Fotoğraf kaldırma işlemi istatistikleri, çalışma geçmişini, profil adını, ders gruplarını veya metinleri etkilememeli.

**Kod incelemesinde görülen noktalar:**
- `keycan/gui/profile.py` içinde “Profil fotoğrafı seç” düğmesi ve fotoğraf seçme/kopyalama akışı bulunuyor.
- Profil fotoğrafı uygulamanın veri dizininde `profile-photo.*` adıyla saklanıyor.
- İncelenen profil arayüzünde fotoğrafı kaldıran bir düğme/işlem görünmüyor.
- `keycan/gui/settings2.py` içinde istatistikleri sıfırlama işlemi mevcut.
- `keycan/data/database.py` içindeki `reset_statistics()` metodu `practice_results` kayıtlarını siliyor. Profildeki seviye, XP, rozet ve ilerleme bilgileri bu çalışma kayıtlarından hesaplandığı için onlar da sıfırlanıyor.
- Profil adı ve fotoğrafı ayrı bir `profile.json` dosyasında saklanıyor; istatistikleri sıfırlama işlemi bunları silmiyor.

**Henüz netleştirilecekler:**
- Fotoğraf dosyası silinemediğinde profil kaydının ve arayüzün tutarlı kalması.
- Fotoğraf kaldırma sonrasında profil sekmesinin anında yenilenmesi.
- Fotoğraf kaldırma işleminin uygulama yeniden başlatıldıktan sonra da kalıcı olması.

**İlgili regresyon kontrolleri:**
- “İstatistikleri ve profili sıfırla” işlemi sonrasında istatistikler ile bunlardan hesaplanan profil ilerleme bilgilerinin sıfırlanması.
- Bu işlem sonrasında profil adının ve profil fotoğrafının korunması.
- Fotoğrafı kaldırınca varsayılan avatarın görünmesi ve yeniden başlatma sonrasında fotoğrafın geri gelmemesi.
- Fotoğraf kaldırma işlemi sonrasında istatistiklerin, çalışma geçmişinin, profil adının, ders gruplarının ve metinlerin aynen korunması.
- Fotoğraf seçme işleminin ve seçilen fotoğrafın uygulama yeniden başlatıldığında yüklenmesinin çalışmaya devam etmesi.

---

## Uygulanan düzeltmeler ve doğrulama durumu

Aşağıdaki kayıtlar, yukarıdaki hata bölümlerindeki ilk statik inceleme notlarının ardından yapılan düzeltmeleri gösterir.

### KC-001 – Sonuç gösterimi

- Gizlilik etiketi oturum tamamlandığında da korunuyor.
- Doğru/yanlış biçimlendirme etiketleri uygulandıktan sonra gizlilik etiketi yeniden uygulanıyor; sonuç çizimi sırasında kaldırılıp açıkta kalmıyor.
- Sonuç sayaçlarının arayüzde gösterilmesi veritabanı kaydının başarılı olmasına bağlı olmaktan çıkarıldı.
- Doğru/yanlış/toplam sayaçları her durumda temel sonuç mesajında gösteriliyor; kayıt, profil yenileme veya sonuç çizimi hatası varsa ek hata bilgisi sayaçların yanına ekleniyor.
- **Kalan kontrol:** GTK arayüzünde gizlilik açık ve kapalı oturumlar tamamlanarak metnin gizli kaldığı ve sayaçların göründüğü doğrulanmalı.

### KC-002 – İstatistik kaydı

- Oturum sonucu kaydedilirken oluşan hatalar artık sessizce kaybolmuyor; kullanıcıya hata metni gösteriliyor.
- Veritabanına kayıt, sonuç etiketleri çizilmeden önce yapılıyor. Böylece arayüzdeki etiket/renk çizimi hatası istatistik kaydını engelleyemiyor.
- Veritabanı INSERT/COMMIT işlemi başarısız olursa açık transaction rollback ediliyor.
- GTK4 belgelerine göre get_text(..., True) gizli karakterleri de döndürür; uygulama bu parametreyi zaten kullanıyordu. Gizlilik modunun metni boşalttığına dair kanıt bulunmadı.
- **Kalan kontrol:** Gizlilik açık ve kapalı iki ayrı oturum tamamlanmalı ve her ikisinin de istatistik geçmişine kaydedildiği doğrulanmalı. Kayıt başarısızsa gösterilen hata mesajı kök nedeni belirlemek için kullanılmalı. Bu nedenle KC-002 henüz tamamen kapatılmadı.

### KC-003 – Yedek içe aktarma

- Varsayılan grup ve derslerin anahtarları çalışma geçmişi kayıtlarına da yazılıyor.
- Varsayılan grup/ders kimlikleri artık yalnızca ID varlığına göre değil, varsayılan/özel niteliği ve grup ilişkisi kontrol edilerek eşleştiriliyor.
- Varsayılan grup içindeki özel derslerin niteliği yedekte ayrıca korunuyor.
- Eski yedeklerde boş anahtar bulunan sonuçlar için kaynak grup ID eşleştirmesi eklendi.
- Varsayılan ders geçmişinin round-trip aktarımı ve aynı ID'ye sahip özel grubun ezilmemesi için regresyon testleri eklendi.
- **Doğrulama:** GitHub Actions tam test paketi başarılı.

### KC-004 – İngilizce çeviriler

- Yinelenen çeviri sözlüğü ve fonksiyon kaldırıldı; widget çevirisi ile dinamik metinler ortak çeviri kataloğunu kullanıyor.
- Adw.EntryRow, Adw.SwitchRow, Gtk.SearchEntry ve Gtk.SpinButton için çeviri kapsamı tamamlandı; mevcut widget desteği korundu.
- Klavye rehberinin metinleri, istatistik ekranındaki dinamik değerler, profil ilerleme metinleri ve etkinlik takviminin ay/gün etiketleri ile araç ipuçları da çevriliyor.
- Yeni profil fotoğrafı ve sıfırlama metinleri ortak kataloğa eklendi.
- Ayarlar ve ders içerik yönetimi pencerelerindeki dosya seçme başlıkları, onay pencereleri ve işlem durumları çevriliyor; ana penceredeki dil değişikliği açık içerik yöneticisine de aktarılıyor.
- **Doğrulama:** Çeviri round-trip testleri ve GitHub Actions tam test paketi başarılı. Tüm ekranların İngilizce/Türkçe görsel kontrolü hâlâ gerekli.

### KC-005 – Profil ve fotoğraf

- Ayarlardaki seçenek adı “İstatistikleri ve profili sıfırla” olarak değiştirildi; açıklama ve onay penceresi silinen/korunan verileri belirtiyor.
- Profil fotoğrafı seçme ve kaldırma düğmeleri yan yana yerleştirildi.
- Fotoğraf kaldırma profil dosyasındaki referansı temizliyor, avatarı varsayılan görünüme döndürüyor ve yalnızca uygulamanın kendi fotoğraf dosyasını silmeyi deniyor.
- Fotoğraf kaldırma istatistikleri, profil adını veya ders içeriklerini etkilemiyor.
- **Kalan kontrol:** Fotoğraf seçme/kaldırma ve uygulama yeniden başlatıldıktan sonraki kalıcılık GTK arayüzünde doğrulanmalı.

### Dal ve otomatik test durumu

- Değişiklikler ayrı bir dalda tutuluyor: fix/stabilization-kc-001-005.
- İnceleme PR'si: https://github.com/Praxis1071/Keycan/pull/2
- GitHub Actions Stage 5, Stage 6, Stage 7 ve tam regresyon testi başarılı.
- Bu değişiklikler henüz main dalına alınmadı; GTK arayüzüne bağlı manuel kullanıcı testleri bekleniyor.

---

## Kullanıcı tarafından sorunsuz olduğu doğrulanan alanlar

Aşağıdaki alanlarda kullanıcı testi başarılıdır. Bu özellikler düzeltmeler sırasında regresyon kontrolü olarak korunmalıdır.

1. İstatistik paneli normal kullanımda doğru çalışıyor.
2. Ders gruplarını yönetme: grup silme, metin silme ve grup yeniden adlandırma çalışıyor.
3. İstatistikleri sıfırlama çalışıyor.
4. İstatistikleri dışa aktarma çalışıyor.
5. Tüm ders gruplarını ve metinleri sıfırlama çalışıyor.
6. Varsayılan ders gruplarını ve metinleri geri yükleme çalışıyor.
7. Türkçe ve İngilizce dil seçenekleri seçilebiliyor; sorun eksik çeviri kapsamıyla sınırlı.

---

## Stabilizasyon sıralaması

1. **KC-001 ve KC-002:** Gizlilik modunun sonuç gösterimi ve kayıt akışı birlikte incelenecek. Aynı oturum akışını etkileyebilecekleri için ortak kök neden araştırılacak.
2. **KC-003:** İçe aktarma zinciri dosya okuma aşamasından veritabanı transaction'ına kadar izlenecek; varsayılan/özel ders kimlik eşleştirmesi test edilecek.
3. **KC-004:** Çeviri kaynakları ve widget kapsamı tek tek envanterlenecek; eksik metinler belirlenecek.
4. **KC-005:** Sıfırlama seçeneğinin adı “İstatistikleri ve profili sıfırla” olarak güncellenecek; profil fotoğrafını kaldırma seçeneği eklenecek. İki işlemin birbirinden bağımsız olduğu ve ilgili verileri doğru koruduğu doğrulanacak.

Her hata için kök neden doğrulanmadan kod değiştirilmeyecek. Düzeltmelerden sonra ilgili otomatik testler ve yukarıdaki başarılı kullanıcı senaryoları tekrar çalıştırılacak.

## Değişiklik geçmişi

- 2026-10-31: Kullanıcı testleri ve statik kod incelemesi temel alınarak ilk hata envanteri oluşturuldu. Bu kayıt sırasında uygulama kodunda değişiklik yapılmadı.
- 2026-10-31: Profil fotoğrafını kaldırma ve sıfırlama seçeneğinin kapsamı KC-005 olarak kaydedildi. Kullanıcı kararı doğrultusunda ayrı bir “Profili sıfırla” işlemi yerine mevcut sıfırlama seçeneğinin adı “İstatistikleri ve profili sıfırla” olarak değiştirilecek; fotoğraf kaldırma ayrı tutulacak.
- 2026-10-31: KC-001–KC-005 düzeltmeleri ayrı dalda uygulandı. Varsayılan yedek eşleştirmesi ve çeviri kapsamı için regresyon testleri eklendi; GitHub Actions Stage 5/6/7 ve tam test paketi başarılı. GTK arayüzüyle ilgili kullanıcı doğrulamaları bekleniyor.


---

## 2026-10-31 – Yeni kullanıcı sorunları ve main dalı düzeltmeleri

Bu bölüm, kullanıcının 31 Ekim 2026 tarihinde bildirdiği üç yeni soruna yönelik doğrudan **main** dalında yapılan değişiklikleri kaydeder. Önceki fix/stabilization-kc-001-005 dalı bu çalışmaların temeli olarak kullanılmadı.

### Varsayılan ders grubu adlarının korunması

- Varsayılan içerik geri yüklenirken mevcut ders grubunun display_name alanı artık snapshot'taki eski adla ezilmiyor.
- Varsayılan ders metinleri ilk kurulumdaki snapshot içeriğine döndürülüyor.
- Kullanıcının değiştirdiği ders grubu adı, özel gruplar ve çalışma geçmişi korunuyor.
- Kaynak satırı fiziksel olarak eksikse snapshot adıyla yeniden oluşturuluyor.

### Yedek dışa/içe aktarma

- Yeni yedek biçimi sürüm 3 olarak düzenlendi; sürüm 1 ve 2 içe aktarma desteği korundu.
- Çalışma kayıtlarına kalıcı session_uuid eklendi. Eski kayıtlar veritabanı migration'ında kimlik alıyor; aynı UUID ile tekrar kaydetme/aktarma çift kayıt oluşturmuyor.
- Dışa aktarma artık silinmiş ders gruplarını ve dersleri de yedekliyor. Böylece bu derslere bağlı çalışma geçmişi başka bir veritabanına taşınırken eşleştirilebiliyor.
- İçe aktarma, grup/metin/çalışma kayıtlarını ayrı ayrı sayıyor ve silinme durumlarını aktarım sonunda geri uyguluyor.
- Dosya seçicide kullanıcı iptali gerçek dosya/işlem hatalarından ayrılıyor; dışa/içe aktarma hataları loglanıp arayüzde gösteriliyor.
- Round-trip, farklı kimlik sırası, silinmiş ders geçmişi, aynı zaman damgasındaki özdeş ama farklı oturumlar, tekrarlı import ve eski veritabanı migration senaryoları için regresyon testleri eklendi.

### Gizlilik açıkken istatistik kaydının güvenilirliği

- Oturum bitiminde yazım alanı doğrudan Gtk.TextBuffer.get_text(..., True) ile tekrar okunuyor. Görünmez etiket yalnızca görüntüyü etkiliyor; kayıt için kullanılan metni silmiyor.
- Her oturum sabit UUID ile kaydediliyor. Kayıt hatası oluşursa aynı oturum kimliğiyle güvenli tekrar deneme yapılabiliyor.
- Çalışma alanına “Tekrar kaydet” kontrolü eklendi; başarısız kayıtlar kuyrukta tutuluyor.
- Bekleyen kayıtlar varken uygulama kapatılırsa kayıtların kaybolabileceği konusunda kullanıcı uyarılıyor.
- Başarılı kayıt sonrasında istatistik ve profil görünümleri yenileniyor.

### Doğrulama durumu

- Değişiklikler doğrudan main dalına commit edildi.
- İlgili regresyon testleri ve CI derleme kapsamı güncellendi.
- Bu oturumda test paketini yerel ortamda çalıştırmak mümkün olmadı; GitHub Actions çalışma sonuçları da mevcut bağlantı üzerinden doğrulanamadı. Bu nedenle otomatik testlerin başarılı olduğu henüz iddia edilmiyor.
- GTK çalışma zamanı davranışı (gizlilik modu, yeniden deneme düğmesi, dosya seçiciler ve kapatma uyarısı) ayrıca gerçek masaüstü oturumunda kontrol edilmeli.
