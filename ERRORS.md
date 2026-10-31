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
| KC-001 | Gizlilik modu – oturum sonuçlarının gösterilmesi | Kullanıcı tarafından doğrulandı; kodda kuvvetli neden adayı bulundu | Yüksek |
| KC-002 | Gizlilik modu – sonuçların istatistiklere kaydedilmesi | Kullanıcı tarafından doğrulandı; çalışma zamanı kök nedeni henüz kesin değil | Kritik |
| KC-003 | Yedek/istatistik içe aktarma | Kullanıcı tarafından doğrulandı; varsayılan ders kimlik eşleştirmesinde kod kusuru adayı bulundu | Yüksek |
| KC-004 | İngilizce arayüzde eksik çeviriler | Kullanıcı tarafından doğrulandı; çeviri mimarisinde eksiklikler bulundu | Orta |
| KC-005 | Profil fotoğrafını kaldırma ve profili sıfırlama seçenekleri | Kullanıcı tarafından doğrulandı; arayüzde seçenekler eksik | Orta |

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

## KC-005 – Profil fotoğrafını kaldırma ve profili sıfırlama seçeneklerinin eksikliği

**Durum:** Kullanıcı tarafından gerçek kullanımda doğrulandı; kod incelemesi arayüzdeki eksikliği destekliyor.

**Belirti:**
- Profil sekmesinde daha önce seçilmiş profil fotoğrafı görüntülenmeye devam ediyor.
- Profil fotoğrafını kaldırmak için bir seçenek bulunmuyor.
- Kullanıcı profilini varsayılan/boş duruma döndürebileceği bir işlem de bulamıyor.

**Beklenen davranış:**
- Profil bölümünde “Profil fotoğrafı seç” düğmesinin yanında veya yakınında “Profil fotoğrafını kaldır” seçeneği bulunmalı.
- Fotoğraf kaldırıldığında kayıtlı fotoğraf dosyası ve profil fotoğrafı referansı güvenli biçimde temizlenmeli; avatar varsayılan görünümüne dönmeli.
- Ayarlar bölümüne “Profili sıfırla” gibi ayrı ve açıkça tanımlanmış bir seçenek eklenmeli.
- Profil sıfırlama işlemi öncesinde, hangi profil verilerinin silineceğini açıklayan onay istenmeli.
- Profil sıfırlama yalnızca profil verilerini (en azından profil adı ve fotoğrafı; kapsamı uygulamadaki profil alanlarına göre netleştirilecek) etkilemeli. İstatistikler, çalışma geçmişi, ders grupları ve metinler korunmalı.
- Fotoğraf kaldırma ile tüm profili sıfırlama birbirinden bağımsız işlemler olmalı.

**Kod incelemesinde görülen noktalar:**
- `keycan/gui/profile.py` içinde “Profil fotoğrafı seç” düğmesi ve fotoğraf seçme/kopyalama akışı bulunuyor.
- Profil fotoğrafı uygulamanın veri dizininde `profile-photo.*` adıyla saklanıyor.
- İncelenen profil arayüzünde fotoğrafı kaldıran bir düğme/işlem görünmüyor.
- `keycan/gui/settings2.py` içinde istatistikleri sıfırlama ve ders içeriklerini sıfırlama işlemleri mevcut; profil sıfırlama seçeneği bulunmuyor.

**Henüz netleştirilecekler:**
- “Profili sıfırla” işleminin profil adı, fotoğrafı ve ileride eklenecek diğer kişisel profil tercihleri üzerindeki kesin kapsamı.
- Profil fotoğrafı dosyası silinemediğinde arayüzün ve profil kaydının tutarlı kalması.
- Fotoğraf kaldırma veya profil sıfırlama sonrasında profil sekmesinin anında yenilenmesi.
- Profil sıfırlamanın istatistikleri ve ders verilerini kesinlikle değiştirmediğinin test edilmesi.

**İlgili regresyon kontrolleri:**
- Fotoğraf seçme ve uygulamayı yeniden başlatınca fotoğrafın yüklenmesi.
- Fotoğrafı kaldırınca varsayılan avatarın görünmesi ve yeniden başlatma sonrasında fotoğrafın geri gelmemesi.
- Profili sıfırlayınca profil alanlarının varsayılan hâle dönmesi.
- Profil sıfırlama sonrasında istatistiklerin, çalışma geçmişinin, ders gruplarının ve metinlerin aynen korunması.
- İptal edilen onay penceresinde hiçbir profil verisinin silinmemesi.

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

Her hata için kök neden doğrulanmadan kod değiştirilmeyecek. Düzeltmelerden sonra ilgili otomatik testler ve yukarıdaki başarılı kullanıcı senaryoları tekrar çalıştırılacak.

## Değişiklik geçmişi

- 2026-10-31: Kullanıcı testleri ve statik kod incelemesi temel alınarak ilk hata envanteri oluşturuldu. Bu kayıt sırasında uygulama kodunda değişiklik yapılmadı.
- 2026-10-31: Profil fotoğrafını kaldırma ve profili sıfırlama seçeneklerinin eksikliği KC-005 olarak eklendi. Yalnızca hata kaydı güncellendi.
