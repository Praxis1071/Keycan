# Keycan ⌨️

Keycan, Linux sistemleri için geliştirilmiş modern, hızlı ve kullanıcı dostu bir **on parmak klavye pratik uygulamasıdır**.

## 🚀 Özellikler

- **On Parmak Klavye Pratiği:** Klavye kullanımını geliştirmek için kelime ve cümle egzersizleri.
- **Çeşitli Egzersizler:** Farklı zorluk seviyelerinde pratik yapma imkânı.
- **Yerel Veritabanı:** Egzersiz verileri ve ilerleme bilgileri SQLite ile yerel olarak saklanır.
- **Çevrimdışı Kullanım:** Temel kullanım için internet bağlantısı gerekmez.
- **Modern Arayüz:** PyQt6 ile hazırlanmış kullanıcı arayüzü.
- **Linux Odaklı:** Linux masaüstü sistemleri için tasarlanmıştır.
- **Flatpak:** Uygulama Flatpak üzerinden paketlenebilir ve dağıtılabilir.

## 🛠️ Kurulum

### Flatpak ile

Flatpak kurulu bir Linux sisteminde uygulamayı yerel olarak derleyip kurmak için:

```bash
flatpak install flathub org.kde.Platform//6.8 org.kde.Sdk//6.8 -y
flatpak-builder --user --install --force-clean build-dir org.keycan.Keycan.yml
```

Ardından uygulamayı çalıştırın:

```bash
flatpak run org.keycan.Keycan
```

### Python ile çalıştırma

Kaynak koddan çalıştırmak için:

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
├── org.keycan.Keycan.yml
├── DakikaProgramlari.spec
├── build.sh
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

GitHub: https://github.com/Praxis1071

---

**Keycan** — On parmak klavye pratiği için Linux uygulaması. ⌨️
