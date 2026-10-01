"""Stage 9 keyboard guide for Keycan."""
from __future__ import annotations

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gtk

from keycan.services.translations import translate


class KeyboardGuidePanel(Gtk.Box):
    """Readable, compact keyboard-learning reference for Keycan."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.set_halign(Gtk.Align.FILL)
        self._build()

    def _build(self) -> None:
        title = Gtk.Label(label="Klavye Rehberi")
        title.set_xalign(0)
        title.add_css_class("title-1")
        self.append(title)

        intro = Gtk.Label(
            label=(
                "Hızdan önce doğru tekniği öğren. Bu rehber; 10 parmak yazma, "
                "WPM, doğruluk, Türkçe klavye düzenleri, ergonomi ve düzenli "
                "pratik için kısa ve güvenilir bir başvuru kaynağıdır."
            )
        )
        intro.set_xalign(0)
        intro.set_wrap(True)
        intro.set_max_width_chars(110)
        intro.add_css_class("dim-label")
        self.append(intro)

        quick = Gtk.FlowBox()
        quick.set_selection_mode(Gtk.SelectionMode.NONE)
        quick.set_homogeneous(True)
        quick.set_row_spacing(8)
        quick.set_column_spacing(8)
        quick.set_min_children_per_line(1)
        quick.set_max_children_per_line(3)
        quick.set_hexpand(True)
        self.append(quick)

        quick.insert(
            self._card(
                "1. Ana sırayı bul",
                "Sol el ASDF, sağ el JKLŞİ çevresinde başlar. F ve J çıkıntıları elleri bakmadan yeniden konumlandırmana yardım eder.",
            ),
            -1,
        )
        quick.insert(
            self._card(
                "2. Doğruluğu koru",
                "Başlangıçta hız kovalamak yerine hataları azalt. Hareketler otomatikleştikçe hız daha doğal gelir.",
            ),
            -1,
        )
        quick.insert(
            self._card(
                "3. Kısa ve düzenli çalış",
                "Uzun ve yorucu tek seans yerine düzenli, kısa pratikler tekniği korumayı kolaylaştırır.",
            ),
            -1,
        )

        basics = Adw.PreferencesGroup()
        basics.set_title("Temel teknik")
        basics.set_description("Her çalışmada tekrar edebileceğin temel kurallar.")
        self.append(basics)
        self._row(
            basics,
            "Ana sıra",
            "Türkçe Q kullanıyorsan sol el A-S-D-F, sağ el J-K-L-Ş-İ çevresinde konumlanır. Parmaklarını rahat ve hafif kıvrık tut.",
        )
        self._row(
            basics,
            "F ve J çıkıntıları",
            "İşaret parmaklarını F ve J üzerindeki fiziksel çıkıntılarla yeniden hizala. Bu, klavyeye bakmadan başlangıç konumunu bulmayı kolaylaştırır.",
        )
        self._row(
            basics,
            "G ve H",
            "Standart QWERTY tekniğinde G sol işaret, H sağ işaret parmağıyla yazılır. Tuştan sonra parmağı ana sıraya geri getir.",
        )
        self._row(
            basics,
            "Başparmaklar",
            "Boşluk tuşunu rahatça kullan. Hangi başparmağı kullanacağın sabit olmak zorunda değildir; gereksiz gerilimi azaltan yöntemi seç.",
        )
        self._row(
            basics,
            "Gözler",
            "Hedef metne bak. Klavyeye kısa süre bakmak öğrenme sürecinde normaldir; amaç zamanla görsel aramayı azaltmaktır.",
        )

        concepts = Adw.PreferencesGroup()
        concepts.set_title("WPM ve doğruluk")
        concepts.set_description("Sonuç ekranındaki sayıların ne anlama geldiğini öğren.")
        self.append(concepts)
        self._row(
            concepts,
            "WPM nedir?",
            "WPM, Words Per Minute yani dakikadaki kelime sayısıdır. Yaygın test standardında bir kelime 5 karakter/tuş vuruşu kabul edilir.",
        )
        self._row(
            concepts,
            "Yaygın WPM formülü",
            "Karakter tabanlı yaygın formül: WPM = (yazılan karakter sayısı ÷ 5) ÷ dakika. Bu tanım Typing.com'un güncel WPM açıklamasında da kullanılır.",
        )
        self._row(
            concepts,
            "Keycan WPM",
            "Keycan'ın mevcut sonuç hesabı, yazılan kelime sayısını geçen süreye böler. Bu nedenle Keycan değeri ile 5-karakter standardını kullanan başka testler birebir aynı çıkmayabilir.",
        )
        self._row(
            concepts,
            "Doğruluk",
            "Doğruluk, yazarken ne kadar az hata yaptığını gösterir. Hız yükselirken doğruluk belirgin biçimde düşüyorsa önce tekniği ve parmak hareketlerini düzelt.",
        )
        self._row(
            concepts,
            "Sayıları karşılaştırırken",
            "Aynı süre, aynı metin türü ve aynı WPM tanımı kullanılmadıkça iki testin sonuçlarını doğrudan karşılaştırma.",
        )

        fingers = Adw.PreferencesGroup()
        fingers.set_title("Parmak görevleri")
        fingers.set_description(
            "Aşağıdaki harita Türkçe Q düzenindeki harfler için pratik bir başlangıçtır; noktalama ve özel tuşlar işletim sistemi düzenine göre değişebilir."
        )
        self.append(fingers)
        self._row(fingers, "Sol serçe", "Q · A · Z")
        self._row(fingers, "Sol yüzük", "W · S · X")
        self._row(fingers, "Sol orta", "E · D · C")
        self._row(fingers, "Sol işaret", "R · T · F · G · V · B")
        self._row(fingers, "Sağ işaret", "Y · U · H · J · N · M")
        self._row(fingers, "Sağ orta", "I · K")
        self._row(fingers, "Sağ yüzük", "O · L · Ö")
        self._row(fingers, "Sağ serçe", "P · Ğ · Ü · Ş · İ · Ç")
        self._row(
            fingers,
            "Shift",
            "Büyük harf için mümkün olduğunda harfi yazan elin karşı tarafındaki Shift tuşunu kullan; böylece iki el aynı anda sıkışmaz.",
        )

        layouts = Adw.PreferencesGroup()
        layouts.set_title("Türkçe Q ve F düzenleri")
        layouts.set_description(
            "Keycan bir düzeni zorunlu kılmaz. Kullandığın işletim sistemi ve fiziksel klavyedeki düzeni esas al."
        )
        self.append(layouts)
        self._row(
            layouts,
            "Türkçe Q",
            "Q W E R T Y U I O P Ğ Ü\nA S D F G H J K L Ş İ\nZ X C V B N M Ö Ç",
        )
        self._row(
            layouts,
            "Türkçe F",
            "F G Ğ I O D R N H P Q W\nU İ E A Ü T K M L Y Ş X\nJ Ö V C Ç Z S B . ,",
        )
        self._row(
            layouts,
            "Hangi düzen?",
            "Zaten rahat kullandığın düzeni değiştirmek zorunda değilsin. Yeni bir düzene geçeceksen önce düzenin tamamını öğren, sonra hız çalış.",
        )
        self._row(
            layouts,
            "Düzen değiştiğinde",
            "İşletim sistemi giriş düzeni ile fiziksel tuş başlıklarının farklı olması karışıklık yaratabilir. Çalışmaya başlamadan önce aktif giriş düzenini kontrol et.",
        )

        practice = Adw.PreferencesGroup()
        practice.set_title("Önerilen çalışma yolu")
        practice.set_description("Tekniği aşamalı olarak otomatikleştiren sade bir rutin.")
        self.append(practice)
        self._row(
            practice,
            "1 · Konum",
            "Her seansın başında F ve J çıkıntılarını bul, ellerini ana sıraya yerleştir ve birkaç yavaş tekrar yap.",
        )
        self._row(
            practice,
            "2 · Harita",
            "Bir parmağın tuşlarını öğrenirken diğer parmakların ana sıradaki konumunu koru. Her erişimden sonra başlangıç konumuna dön.",
        )
        self._row(
            practice,
            "3 · Doğruluk",
            "Rahat hızda yaz. Hatalı tuşları ve hangi parmakla yazman gerektiğini fark et; sadece daha hızlı basmaya çalışma.",
        )
        self._row(
            practice,
            "4 · Akıcılık",
            "Doğruluk istikrarlı hale gelince kısa süreli hız çalışmaları ekle. Hız uğruna sürekli yanlış parmağa geçme.",
        )
        self._row(
            practice,
            "5 · Gerçek metin",
            "Derslerden sonra farklı kelime ve noktalama içeren gerçek metinlerle çalış. Böylece öğrendiğin hareketleri günlük yazmaya taşırsın.",
        )
        self._row(
            practice,
            "6 · Zor tuşlar",
            "Aynı tuşlarda sürekli hata yapıyorsan bütün hızını artırmak yerine o tuşu içeren kısa tekrarlar yap.",
        )

        ergonomics = Adw.PreferencesGroup()
        ergonomics.set_title("Ergonomi ve mola")
        ergonomics.set_description(
            "Uzun süreli klavye kullanımında rahat ve nötr bir çalışma pozisyonunu hedefle."
        )
        self.append(ergonomics)
        self._row(
            ergonomics,
            "Bilekler",
            "Eller, bilekler ve ön kollar mümkün olduğunca düz ve aynı hizada olsun. Bilekleri sürekli yukarı, aşağı veya yana bükerek çalışma.",
        )
        self._row(
            ergonomics,
            "Omuz ve dirsek",
            "Omuzları gevşek tut; dirsekleri vücuda yakın ve rahat bir açıda konumlandır. Klavyeye ulaşmak için öne doğru uzanma.",
        )
        self._row(
            ergonomics,
            "Klavye yüksekliği",
            "Klavye, bilekleri gereksiz biçimde yukarı bükmeye zorlamayacak şekilde konumlandırılmalı. OSHA, yatay veya hafif negatif eğimi de değerlendirme ölçütleri arasında sayıyor.",
        )
        self._row(
            ergonomics,
            "Oturma ve ekran",
            "Baş ve boyun gövdeyle hizalı, omuzlar rahat, sırt destekli ve ayaklar destekli olsun. Ekrana bakmak için sürekli öne eğilme.",
        )
        self._row(
            ergonomics,
            "Molalar",
            "Aynı pozisyonda uzun süre kalma. OSHA, bilgisayar işinde kısa ve sık molaları; pozisyon değiştirmeyi, ayağa kalkmayı ve hareket etmeyi öneriyor.",
        )
        self._row(
            ergonomics,
            "Ağrı veya uyuşma",
            "Sürekli ağrı, uyuşma, karıncalanma veya güç kaybı gibi belirtileri görmezden gelme. Çalışmayı durdurup uygun bir sağlık profesyonelinden değerlendirme al.",
        )

        mistakes = Adw.PreferencesGroup()
        mistakes.set_title("Yaygın hatalar")
        mistakes.set_description("İlerlemeyi yavaşlatan alışkanlıkları erken fark et.")
        self.append(mistakes)
        self._row(mistakes, "Sürekli klavyeye bakmak", "Önce kısa bölümlerde bakmadan yazmayı dene; zorlandığında hatayı düzeltmek için tekrar bakabilirsin.")
        self._row(mistakes, "Hız uğruna doğruluğu bırakmak", "Hatalar sürekli artıyorsa hızı düşür ve doğru parmak hareketini yeniden kur.")
        self._row(mistakes, "Yanlış parmak kullanmak", "Bir tuşu sürekli aynı yanlış parmakla yazmak kötü alışkanlığı güçlendirebilir. Tuşun görevli parmağını öğren.")
        self._row(mistakes, "Eli ana sıradan uzaklaştırmak", "Her erişimden sonra F/J referansını ve ana sırayı yeniden bul. Elin klavyede dolaşmasına izin verme.")
        self._row(mistakes, "Tek uzun seansa yüklenmek", "Yorgunluk tekniği bozuyorsa seansı kısalt. Düzenli tekrar, sürdürülebilir bir öğrenme ritmi oluşturur.")

        resources = Adw.PreferencesGroup()
        resources.set_title("Güvenilir ve okunabilir kaynaklar")
        resources.set_description(
            "Aşağıdaki bağlantılar WPM hesabı, touch typing, klavye düzenleri ve ergonomi hakkında daha ayrıntılı bilgi verir."
        )
        self.append(resources)
        self._resource(
            resources,
            "WPM ve doğruluk hesabı",
            "Typing.com · WPM formülü, 5 karakterlik kelime tanımı ve doğruluk hesabı.",
            "https://support.typing.com/en/articles/9048321",
        )
        self._resource(
            resources,
            "Touch typing dersleri",
            "Typing.com · başlangıçtan ileri seviyeye güncel ders akışı ve problem tuşu çalışmaları.",
            "https://www.typing.com/student/lessons",
        )
        self._resource(
            resources,
            "Typing testleri",
            "Typing.com · 1, 3 ve 5 dakikalık testler ile WPM ve doğruluk ölçümü.",
            "https://www.typing.com/student/tests",
        )
        self._resource(
            resources,
            "Ergonomi: nötr pozisyon",
            "OSHA · eller, bilekler, dirsekler, omuzlar ve çalışma pozisyonu için ayrıntılı rehber.",
            "https://www.osha.gov/etools/computer-workstations/positions",
        )
        self._resource(
            resources,
            "Ergonomi: klavye ve çalışma süreci",
            "OSHA · klavye yerleşimi, tekrar eden hareketler ve kısa molalar hakkında rehber.",
            "https://www.osha.gov/etools/computer-workstations/work-process",
        )
        self._resource(
            resources,
            "Türkçe Q ve F düzenleri",
            "Microsoft Learn · Türkçe Q ve Türkçe F klavye düzenlerinin güncel sistem tanımları.",
            "https://learn.microsoft.com/th-th/globalization/windows-keyboard-layouts",
        )
        self._resource(
            resources,
            "Türkçe F klavye yerleşimi",
            "Microsoft Learn · Türkçe F düzenindeki tuş yerleşimini doğrudan gösteren referans.",
            "https://learn.microsoft.com/en-us/msdn-files/resources/msdn/goglobal/keyboards/kbdtuf.html",
        )

    @staticmethod
    def _card(title: str, description: str) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.add_css_class("card")
        card.set_margin_top(1)
        card.set_margin_bottom(1)
        card.set_margin_start(1)
        card.set_margin_end(1)
        card.set_size_request(220, 108)
        card.set_hexpand(True)

        heading = Gtk.Label(label=title)
        heading.set_xalign(0)
        heading.add_css_class("heading")
        heading.set_wrap(True)
        card.append(heading)

        body = Gtk.Label(label=description)
        body.set_xalign(0)
        body.set_wrap(True)
        body.set_hexpand(True)
        body.add_css_class("dim-label")
        card.append(body)
        return card

    @staticmethod
    def _row(group: Adw.PreferencesGroup, title: str, description: str) -> None:
        row = Adw.ActionRow()
        row.set_title(title)
        row.set_subtitle(description)
        row.set_subtitle_lines(3)
        group.add(row)

    @staticmethod
    def _resource(
        group: Adw.PreferencesGroup,
        title: str,
        description: str,
        uri: str,
    ) -> None:
        row = Adw.ActionRow()
        row.set_title(title)
        row.set_subtitle(description)
        row.set_subtitle_lines(3)
        link = Gtk.LinkButton.new_with_label(uri, "Oku")
        link.add_css_class("flat")
        row.add_suffix(link)
        row.set_activatable_widget(link)
        group.add(row)

    def set_language(self, language: str) -> None:
        stack = [self]
        while stack:
            widget = stack.pop()
            child = widget.get_first_child()
            while child is not None:
                stack.append(child)
                child = child.get_next_sibling()
            if isinstance(widget, Gtk.Label):
                text = widget.get_text()
                if text:
                    widget.set_text(translate(text, language))
            elif isinstance(widget, Gtk.LinkButton):
                label = widget.get_label()
                if label:
                    widget.set_label(translate(label, language))
            elif isinstance(widget, Adw.ActionRow):
                title = widget.get_title()
                subtitle = widget.get_subtitle()
                if title:
                    widget.set_title(translate(title, language))
                if subtitle:
                    widget.set_subtitle(translate(subtitle, language))
            elif isinstance(widget, Adw.PreferencesGroup):
                title = widget.get_title()
                description = widget.get_description()
                if title:
                    widget.set_title(translate(title, language))
                if description:
                    widget.set_description(translate(description, language))
