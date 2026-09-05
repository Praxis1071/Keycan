# Keycan ⌨️

Keycan, Linux masaüstü sistemleri için geliştirilmiş modern ve kullanıcı dostu bir **on parmak klavye pratik uygulamasıdır**.

Keycan ile farklı ders gruplarındaki metinleri seçebilir, çalışma süresini belirleyebilir ve yazma pratiği yapabilirsiniz. Uygulama temel kullanımda çevrimdışı çalışır ve verileri yerel SQLite veritabanında tutar.

## ✨ Özellikler

- **On Parmak Klavye Pratiği** — Kelime ve cümlelerden oluşan ders metinleriyle pratik.
- **Ders ve Metin Seçimi** — Kaynaklara göre düzenlenmiş ders grupları.
- **Ayarlanabilir Süre** — Çalışma süresi 1–180 dakika arasında seçilebilir.
- **Doğru / Yanlış Sonuçları** — Süre sonunda yazılan kelimeler sonuç olarak renklendirilir.
- **Büyük/Küçük Harf Bağımsızlığı** — Kelime karşılaştırmasında harf büyüklüğü önemsenmez.
- **Noktalama İşaretlerini Yok Sayma** — Kelime eşleştirmesinde noktalama işaretleri zorunlu değildir.
- **Karışık Sırada Yazma** — Kelimelerin metindeki sırasını takip etmek zorunlu değildir.
- **Metin Boyutu** — Ders ve yazma alanlarının yazı boyutu ayarlanabilir.
- **Yazım Metnini Karart** — Yazarken kendi yazdığınız metni gizleyerek yalnızca hedef metne odaklanabilirsiniz.
- **Yerel SQLite Veritabanı** — Dersler ve çalışma sonuçları yerel olarak saklanır.
- **Çevrimdışı Kullanım** — Temel uygulama kullanımı internet bağlantısı gerektirmez.
- **GTK4 + libadwaita** — Modern Linux masaüstü arayüzü.
- **Flatpak** — Linux dağıtımları için izole ve taşınabilir paketleme.

## 🛠️ Teknolojiler

- Python
- GTK4
- libadwaita
- PyGObject
- SQLite
- Flatpak
- GNOME Platform 50

## 📦 Kurulum

### Hazır Flatpak paketi

GitHub Releases bölümündeki `.flatpak` paketini kullanabilirsiniz.

```bash
flatpak install ./Keycan.flatpak
flatpak run org.keycan.Keycan
```

### Kaynak koddan Flatpak ile derleme

CachyOS/Arch tabanlı sistemlerde gerekli araçları kurun:

```bash
sudo pacman -S flatpak flatpak-builder
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

GNOME 50 Platform ve SDK'yı kurun:

```bash
flatpak install flathub org.gnome.Platform//50 org.gnome.Sdk//50
```

Projeyi alın:

```bash
git clone https://github.com/Praxis1071/Keycan.git
cd Keycan
```

Derleyip kurun:

```bash
flatpak-builder --user --install --force-clean build-dir org.keycan.Keycan.gtk4.yml
```

Çalıştırın:

```bash
flatpak run org.keycan.Keycan
```

## 🧪 Geliştirici Kontrolü

Proje kök dizininde:

```bash
./check.sh
```

Bu kontrol Python sözdizimini, SQLite bütünlüğünü, ders/kaynak verilerini ve çalışma sonucu şemasını denetler.

## 📁 Proje Yapısı

```text
Keycan/
├── gtk_main.py
├── data_loader.py
├── typing_data.db
├── keycan-gtk4-wrapper
├── org.keycan.Keycan.gtk4.yml
├── org.keycan.Keycan.desktop
├── org.keycan.Keycan.svg
├── org.keycan.Keycan.png
├── check.sh
├── BUILD-INSTRUCTIONS.txt
├── LICENSE
└── README.md
```

### Veri yükleyici

`data_loader.py`, eski ders kaynaklarını SQLite veritabanına aktarmak için kullanılan yardımcı araçtır. Mevcut ders, kaynak ve kimlik ilişkileri korunur.

## 🔐 Veri ve izinler

Keycan temel kullanım için internet erişimine ihtiyaç duymaz. Flatpak sürümünde uygulama yalnızca ihtiyaç duyduğu masaüstü/sistem erişimleriyle çalışacak şekilde paketlenir.

Çalışma veritabanı kullanıcı veri dizininde tutulur; böylece Flatpak paketinin salt okunur uygulama alanına yazma ihtiyacı oluşmaz.

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Ayrıntılar için [`LICENSE`](LICENSE) dosyasına bakabilirsiniz.

## 👤 Geliştirici

**Praxis1071**

GitHub: https://github.com/Praxis1071/Keycan

---

**Keycan** — Linux için on parmak klavye pratiği. ⌨️
