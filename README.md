# Keycan ⌨️

Keycan, Linux masaüstü sistemleri için geliştirilmiş modern ve kullanıcı dostu bir **on parmak klavye pratik uygulamasıdır**.

Farklı ders gruplarındaki metinlerle yazma pratiği yapabilir, çalışma süresini belirleyebilir ve sonuçlarını yerel olarak takip edebilirsiniz. Keycan temel kullanımda çevrimdışı çalışır ve verileri yerel SQLite veritabanında saklar.

## 🚀 Keycan 2.3.0

Keycan 2.3.0 ile önceki sürümdeki kullanım ve kararlılık sorunları giderildi; ders grubu yönetimi, istatistik ekranı ve Türkçe/İngilizce arayüz deneyimi iyileştirildi.

### ✨ Öne Çıkanlar

- 📊 Yenilenen istatistikler ve GitHub tarzı yıllık aktivite grafiği
- 📚 Yerleşik ve özel ders gruplarını yönetme
- ✏️ Ders gruplarını yeniden adlandırma
- ✏️ Metin ekleme, düzenleme, silme ve sıralama
- 🔄 Varsayılan Keycan içeriklerini geri yükleme
- 🗑️ Tüm ders ve metinleri sıfırlama
- 💾 İstatistik ve içerik verilerini içe/dışa aktarma
- 🌐 Türkçe / English dil sistemi
- 🎨 Sistem / Açık / Koyu tema seçimi
- 🛠️ GTK4 kararlılık ve runtime düzeltmeleri
- 📦 GTK4 + libadwaita tabanlı Flatpak paketi

## ✨ Özellikler

- On Parmak Klavye Pratiği
- Ders ve Metin Seçimi
- Ders Grubu Arama
- Ders Grubu Yönetimi ve Yeniden Adlandırma
- Ayarlanabilir Çalışma Süresi
- Doğru / Yanlış Sonuçları
- Çalışma Geçmişi ve İstatistikler
- GitHub tarzı aktivite takvimi
- Ders ve metin yönetimi
- Veri yedekleme, içe/dışa aktarma
- Büyük/Küçük Harf Bağımsızlığı
- Noktalama İşaretlerini Yok Sayma
- Karışık Sırada Yazma
- Metin Boyutu Ayarı
- Sistem / Açık / Koyu tema seçimi
- Türkçe / English dil seçimi (hemen uygulanır ve kalıcıdır)
- Kopyala/yapıştır kullanımının engellenmesi
- Yerel ve çevrimdışı veri yönetimi
- GTK4 + libadwaita
- Flatpak

## 🛠️ Teknolojiler

- Python
- GTK4
- libadwaita
- PyGObject
- SQLite
- Flatpak
- GNOME Platform 50

## 📦 İndirme

En güncel sürüm için GitHub Releases sayfasındaki Flatpak paketini kullanabilirsiniz.

## 📄 Lisans

Keycan, **GNU General Public License v3 veya sonrası (GPL-3.0-or-later)** altında dağıtılan özgür ve açık kaynaklı bir yazılımdır.

Ayrıntılar için [LICENSE](LICENSE) dosyasına bakın.

## 🗺️ Geliştirme Yol Haritası

Keycan'ın güncel geliştirme planı:

| Aşama | Konu | Durum |
|---|---|---|
| 0 | 🏗️ Temel Mimari | ✅ Tamamlandı |
| 1 | ⌨️ Temel Yazma Deneyimi | ✅ Tamamlandı |
| 2 | 📊 İstatistik ve Veri Altyapısı | ✅ Tamamlandı |
| 3 | 📚 İçerik ve Veri Yönetimi | ✅ Tamamlandı |
| 4 | 🔧 2.3.x Bakım ve Hata Düzeltmeleri | ✅ Tamamlandı |
| 5 | 📈 Gelişmiş İstatistikler | ✅ Tamamlandı |
| 6 | 🎨 Kullanıcı Deneyimi | ✅ Tamamlandı |
| 7 | 👤 Profil, XP, Seviye ve Rozet Sistemi | ⏳ Planlandı |
| 8 | 🧑 Gelişmiş Yerel Profil | ⏳ Planlandı |
| 9 | 📖 Klavye Rehberi | ⏳ Planlandı |

### Aşama 5 — Gelişmiş İstatistikler ✅

- Günlük / haftalık / aylık / yıllık ve tüm zamanlar filtreleri
- Genel, Gelişim, Dersler ve Rekorlar bölümleri
- Uzun dönemli WPM ve doğruluk gelişimi
- Toplam çalışma süresi ve toplam kelime / karakter
- Ders bazlı performans
- Ayrıntılı dönem filtreleri ve dönem karşılaştırmaları
- Rekor geçmişi
- Performans özeti ve hız tutarlılığı analizi
- İstatistik verileri için otomatik test altyapısı

### Aşama 6 — Kullanıcı Deneyimi ✅

- Sistem / Açık / Koyu tema seçenekleri (hemen uygulanır)
- Türkçe / English dil sistemi (hemen uygulanır ve kalıcıdır)
- Tema ve dil tercihlerini ana uygulama mantığından ayrı tutan merkezi ayar altyapısı
- GTK arayüzünden ayrıştırılmış merkezi çeviri kataloğu
- Tema/dil tercihlerinin atomik ve güvenli yerel olarak saklanması
- Dinamik oluşturulan arayüz metinlerinin de çevrilmesi
- Stage 6 için otomatik testler ve Python modül doğrulaması
- GTK4 widget hiyerarşisi ve ders grubu yönetimi için kararlılık düzeltmeleri

### Aşama 7 — Profil, XP, Seviye ve Rozet Sistemi

Sidebar'da İstatistikler'den bağımsız ayrı bir Profil bölümü oluşturulacak. Profil; XP, seviye, seviye ilerlemesi, rozetler ve çalışma serisini gösterecek ve bu veriler mevcut istatistiklerden beslenecek.

### Aşama 8 — Gelişmiş Yerel Profil

Profilin kişiselleştirilmesi ve genişletilmesi planlanıyor. Kullanıcı kendi ismini ve profil fotoğrafını belirleyebilecek; profil yerel olarak saklanacak ve genel çalışma özeti ile ilerleme geçmişini gösterecek.

Ayrıntılı roadmap için [ROADMAP.md](ROADMAP.md) dosyasına bakın.

> Not: Katiplik modu, online özellikler, bulut senkronizasyonu, Odak/Pomodoro ve akıllı/adaptif eğitim sistemi mevcut yol haritasında yer almamaktadır.
