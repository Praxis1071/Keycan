# Keycan ⌨️

Keycan, Linux sistemleri için geliştirilmiş modern, hızlı ve kullanıcı dostu bir **on parmak klavye pratik uygulamasıdır**.

## 🚀 Özellikler

- **On Parmak Klavye Pratiği:** Klavye kullanımını geliştirmek için kelime ve cümle egzersizleri.
- **Çeşitli Egzersizler:** Farklı zorluk seviyelerinde pratik yapma imkânı.
- **Yerel Veritabanı:** Egzersiz verileri ve ilerleme bilgileri SQLite ile yerel olarak saklanır.
- **Çevrimdışı Kullanım:** Temel kullanım için internet bağlantısı gerekmez.
- **Modern Arayüz:** PyQt6 ile hazırlanmış kullanıcı arayüzü.
- **Linux Odaklı:** Linux masaüstü sistemleri için tasarlanmıştır.
- **Flatpak Desteği:** Uygulama Flatpak ile paketlenebilir ve dağıtılabilir.

## 🛠️ Kurulum ve Çalıştırma

Keycan'ı Linux sisteminizde **3 farklı şekilde** kurup çalıştırabilirsiniz. Size en uygun yöntemi seçin.

### 1. 📦 Hazır Flatpak Paketi — Önerilen

En kolay yöntemdir. GitHub Releases bölümünden `.flatpak` paketini indirin.

İndirdiğiniz dosyanın bulunduğu klasörde terminal açın:

```bash
flatpak install ./Keycan.flatpak
```

Kurulum tamamlandıktan sonra:

```bash
flatpak run org.keycan.Keycan
```

> **Önerilen yöntem:** Teknik bilgi gerektirmez ve uygulamayı Flatpak üzerinden izole bir ortamda çalıştırır.

---

### 2. 🔨 Kaynak Koddan Flatpak ile Kurulum

Keycan'ın kaynak kodunu indirip Flatpak paketini kendiniz oluşturabilirsiniz.

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
```

Ardından çalıştırın:

```bash
flatpak run org.keycan.Keycan
```

> **Bu yöntem**, geliştiriciler ve projeyi kaynak koddan incelemek veya değiştirmek isteyen kullanıcılar için uygundur.

---

### 3. 🐍 Python ile Kaynak Koddan Çalıştırma

Flatpak kullanmadan uygulamayı doğrudan Python ortamında çalıştırmak için:

```bash
git clone https://github.com/Praxis1071/Keycan.git
cd Keycan
```

Gerekli Python paketlerini yükleyin:

```bash
pip install -r requirements.txt
```

Uygulamayı başlatın:

```bash
python main.py
```

> **Bu yöntem**, kaynak kod üzerinde geliştirme ve test yapmak isteyenler için uygundur.

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

GitHub: https://github.com/Praxis1071/Keycan

---

**Keycan** — On parmak klavye pratiği için Linux uygulaması. ⌨️
