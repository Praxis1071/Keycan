# Keycan ⌨️

Keycan, Linux sistemleri için geliştirilmiş modern, hızlı ve kullanıcı dostu bir **on parmak klavye pratik uygulamasıdır**.

## 🚀 Özellikler

- **On Parmak Klavye Pratiği:** Klavye kullanımını geliştirmek için kelime ve cümle egzersizleri.
- **Çeşitli Egzersizler:** Farklı zorluk seviyelerinde pratik yapma imkânı.
- **Yerel Veritabanı:** Egzersiz verileri ve ilerleme bilgileri SQLite ile yerel olarak saklanır.
- **Çevrimdışı Kullanım:** Temel kullanım için internet bağlantısı gerekmez.
- **Modern Arayüz:** Mevcut sürüm PyQt6 ile hazırlanmıştır; GTK4 + libadwaita geçişi planlanmaktadır.
- **Linux Odaklı:** Linux masaüstü sistemleri için tasarlanmıştır.
- **Flatpak:** Projenin güncel paketleme ve dağıtım hedefi Flatpak'tır.

## 🛠️ Kurulum ve Çalıştırma

### 1. 📦 Hazır Flatpak Paketi — Önerilen

GitHub Releases bölümünden `.flatpak` paketini indirin.

```bash
flatpak install ./Keycan.flatpak
flatpak run org.keycan.Keycan
```

### 2. 🔨 Kaynak Koddan Flatpak ile Kurulum

Gerekli Flatpak runtime ve SDK'yı kurun:

```bash
flatpak install flathub org.freedesktop.Platform//26.08 org.freedesktop.Sdk//26.08
```

Projeyi indirin:

```bash
git clone https://github.com/Praxis1071/Keycan.git
cd Keycan
```

Uygulamayı derleyip kurun:

```bash
flatpak-builder --user --install --force-clean build-dir org.keycan.Keycan.yml
flatpak run org.keycan.Keycan
```

### 3. 🐍 Python ile Kaynak Koddan Çalıştırma

```bash
git clone https://github.com/Praxis1071/Keycan.git
cd Keycan
pip install -r requirements.txt
python main.py
```

## 📁 Proje Yapısı

```text
Keycan/
├── main.py
├── data_loader.py
├── typing_data.db
├── requirements.txt
├── org.keycan.Keycan.desktop
├── org.keycan.Keycan.png
├── org.keycan.Keycan.svg
├── org.keycan.Keycan.yml
├── check.sh
├── BUILD-INSTRUCTIONS.txt
└── LICENSE
```

## 🧰 Teknolojiler

- Python
- PyQt6
- SQLite
- Flatpak

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Ayrıntılar için [`LICENSE`](LICENSE) dosyasına bakabilirsiniz.

## 👤 Geliştirici

**Praxis1071**

GitHub: https://github.com/Praxis1071/Keycan

---

**Keycan** — On parmak klavye pratiği için Linux uygulaması. ⌨️
