# Keycan ⌨️

**Keycan**, Linux sistemler için geliştirilmiş modern, hızlı ve kullanıcı dostu bir on parmak klavye pratik uygulamasıdır.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Flatpak-orange.svg)

---

## 🚀 Özellikler

- **Çeşitli Egzersizler:** Farklı zorluk seviyelerinde kelime ve cümle pratikleri.
- **Yerel Veritabanı:** İlerlemenizi ve verilerinizi tamamen çevrimdışı (SQLite) saklar.
- **Modern Arayüz:** PyQt6 ile yazılmış temiz ve responsive tasarım.
- **Flatpak Desteği:** Tüm Linux dağıtımlarında izole ve sorunsuz çalışma garantisi.

---

## 🛠️ Kurulum ve Çalıştırma Seçenekleri

Uygulamayı 3 farklı yöntemle çalıştırabilirsiniz:

### Seçenek 1: Hazır Flatpak Paketi İle Kurulum (En Kolay)

Sisteminizde `flatpak` yüklü olması yeterlidir. Derlemeye ihtiyaç duymadan hazır `.flatpak` dosyasını indirip kurabilirsiniz:

```bash
# Hazır paket dosyasını yükleyin
flatpak install keycan.flatpak

# Uygulamayı başlatın
flatpak run org.keycan.Keycan

Seçenek 2: Kaynak Koddan Kendiniz Flatpak Derleyin

Flatpak paketini yerelde kendiniz derleyip kurmak isterseniz:
Bash

# KDE SDK bağımlılığını indirin
flatpak install flathub org.kde.Platform//6.8 org.kde.Sdk//6.8 -y

# Uygulamayı derleyin ve kullanıcı dizinine kurun
flatpak-builder --user --install --force-clean build-dir org.keycan.Keycan.yml

# Uygulamayı çalıştırın
flatpak run org.keycan.Keycan

Seçenek 3: Doğrudan Python Kaynak Kodundan Çalıştırma

Geliştiriciler veya Flatpak kullanmak istemeyenler doğrudan Python betiğini çalıştırabilir:
Bash

# Repoyu klonlayın
git clone [https://github.com/Praxis1071/Keycan.git](https://github.com/Praxis1071/Keycan.git)
cd Keycan

# Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
python main.py

📜 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için LICENSE dosyasına göz atabilirsiniz.

