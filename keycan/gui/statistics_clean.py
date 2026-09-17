"""Clean, SQLite-backed statistics dashboard for Keycan."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, GLib, Gtk

if TYPE_CHECKING:
    from keycan.data.database import Database

MONTHS = ("Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık")
WEEKDAYS = ("Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz")


class ProgressChart(Gtk.DrawingArea):
    def __init__(self) -> None:
        super().__init__()
        self.set_content_width(760)
        self.set_content_height(290)
        self.set_hexpand(True)
        self.set_draw_func(self._draw)
        self.points: list[tuple[str, float]] = []
        self.value_suffix = ""
        self.progress = 1.0

    def set_points(self, points: list[tuple[str, float]], value_suffix: str = "") -> None:
        self.points = [p for p in points if math.isfinite(p[1])]
        self.value_suffix = value_suffix
        self.progress = 0.0 if self.points else 1.0
        self.queue_draw()
        if self.points:
            GLib.timeout_add(16, self._animate)

    def _animate(self) -> bool:
        self.progress = min(1.0, self.progress + 0.055)
        self.queue_draw()
        return self.progress < 1.0

    def _draw(self, _area, cr, width: int, height: int, _data=None) -> None:
        left, right = 58.0, max(59.0, width - 22.0)
        top, bottom = 20.0, max(21.0, height - 48.0)
        cw, ch = right - left, bottom - top
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.14)
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = bottom - ch * fraction
            cr.move_to(left, y); cr.line_to(right, y); cr.stroke()
        if not self.points:
            return
        values = [v for _, v in self.points]
        minimum, maximum = min(values), max(values)
        if math.isclose(minimum, maximum):
            pad = max(1.0, abs(maximum) * 0.08)
            minimum, maximum = minimum - pad, maximum + pad
        cr.set_font_size(10)
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.75)
        for fraction in (0.0, 0.5, 1.0):
            value = minimum + (maximum - minimum) * fraction
            y = bottom - ch * fraction
            cr.move_to(4, y + 4); cr.show_text(f"{value:.0f}{self.value_suffix}")
        visible = max(1, int(math.ceil(len(self.points) * self.progress)))
        coords = []
        cr.set_source_rgba(0.18, 0.52, 0.78, 0.95)
        cr.set_line_width(2.6)
        for index, (_label, value) in enumerate(self.points[:visible]):
            x = left if len(self.points) == 1 else left + cw * index / (len(self.points) - 1)
            y = bottom - ch * ((value - minimum) / (maximum - minimum))
            coords.append((x, y))
            if index == 0: cr.move_to(x, y)
            else: cr.line_to(x, y)
        cr.stroke()
        for x, y in coords:
            cr.arc(x, y, 3.6, 0, math.tau); cr.fill()
        cr.set_source_rgba(0.45, 0.45, 0.45, 0.75)
        for index, (label, _value) in enumerate(self.points):
            if len(self.points) > 10 and index not in (0, len(self.points) - 1): continue
            x = left if len(self.points) == 1 else left + cw * index / (len(self.points) - 1)
            cr.move_to(max(left, x - 20), height - 14); cr.show_text(label)


class MetricCard(Gtk.Box):
    def __init__(self, title: str) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        self.add_css_class("card")
        self.set_hexpand(True)
        header = Gtk.Label(label=title)
        header.set_xalign(0)
        header.add_css_class("dim-label")
        header.set_margin_top(14); header.set_margin_start(14); header.set_margin_end(14)
        self.append(header)
        self.value = Gtk.Label(label="0")
        self.value.set_xalign(0); self.value.add_css_class("title-2")
        self.value.set_margin_start(14); self.value.set_margin_end(14); self.value.set_margin_bottom(14)
        self.append(self.value)
        self._target = 0.0

    def set_value(self, value: float, formatter=None, suffix: str = "") -> None:
        self._target = max(0.0, value)
        formatter = formatter or (lambda n: f"{n:.0f}")
        self.value.set_text(f"{formatter(0)}{suffix}")
        current = 0.0
        def tick() -> bool:
            nonlocal current
            current += max(0.5, (self._target - current) * 0.18)
            if abs(self._target - current) < 0.5: current = self._target
            self.value.set_text(f"{formatter(current)}{suffix}")
            return current != self._target
        GLib.timeout_add(16, tick)


class ActivityHeatmap(Gtk.DrawingArea):
    def __init__(self) -> None:
        super().__init__(); self.set_content_width(900); self.set_content_height(190); self.set_hexpand(True); self.set_draw_func(self._draw)
        self.year = datetime.now().year; self.days: dict[date, dict[str, object]] = {}; self._cell_size = 12.0; self._gap = 4.0; self._left = 38.0; self._top = 26.0
        motion = Gtk.EventControllerMotion(); motion.connect("motion", self._on_motion); motion.connect("leave", self._on_leave); self.add_controller(motion)

    def set_data(self, year: int, days: list[dict[str, object]]) -> None:
        self.year = year; self.days = {item["date"]: item for item in days}; self.queue_draw()
    def _calendar_start(self) -> date:
        first = date(self.year, 1, 1); return first - timedelta(days=first.weekday())
    def _weeks(self) -> int:
        start = self._calendar_start(); return ((date(self.year, 12, 31) - start).days // 7) + 1
    def _intensity(self, item, maximum: float) -> int:
        if not item: return 0
        duration = float(item["duration_seconds"])
        if maximum <= 0 or duration <= 0: return 1
        ratio = duration / maximum
        return 1 if ratio <= .25 else 2 if ratio <= .5 else 3 if ratio <= .75 else 4
    @staticmethod
    def _rounded_rect(cr, x, y, size, radius) -> None:
        cr.new_sub_path(); cr.arc(x+radius,y+radius,radius,math.pi,1.5*math.pi); cr.arc(x+size-radius,y+radius,radius,1.5*math.pi,2*math.pi); cr.arc(x+size-radius,y+size-radius,radius,0,.5*math.pi); cr.arc(x+radius,y+size-radius,radius,.5*math.pi,math.pi); cr.close_path()
    def _draw(self, _area, cr, width, height, _data=None) -> None:
        weeks = self._weeks(); usable = max(100.0, width-self._left-12); cell = min(16.0,max(8.0,(usable-(weeks-1)*4)/weeks)); gap=max(2.0,min(4.0,cell*.30)); self._cell_size=cell; self._gap=gap
        maximum=max((float(x["duration_seconds"]) for x in self.days.values()),default=0); start=self._calendar_start(); cr.set_font_size(10); cr.set_source_rgba(.45,.45,.45,.82)
        for row,label in enumerate(WEEKDAYS):
            if row not in (0,2,4,6): continue
            cr.move_to(0,self._top+row*(cell+gap)+cell*.78); cr.show_text(label)
        last_month=None
        for week in range(weeks):
            week_start=start+timedelta(days=week*7)
            if week_start.month != last_month and week_start.year==self.year:
                cr.move_to(self._left+week*(cell+gap),12); cr.show_text(MONTHS[week_start.month-1]); last_month=week_start.month
            for row in range(7):
                day=week_start+timedelta(days=row)
                if day.year!=self.year: continue
                level=self._intensity(self.days.get(day),maximum); x=self._left+week*(cell+gap); y=self._top+row*(cell+gap); self._rounded_rect(cr,x,y,cell,max(2,cell*.18))
                cr.set_source_rgba(.45,.45,.45,.18) if level==0 else cr.set_source_rgba(.18,.52,.78,(.24,.42,.62,.82)[level-1]); cr.fill()
        legend_y=min(height-14,self._top+7*(cell+gap)+18); cr.set_source_rgba(.45,.45,.45,.82); cr.move_to(self._left,legend_y+cell*.78); cr.show_text("Daha az"); x=self._left+52
        for level in range(5):
            self._rounded_rect(cr,x,legend_y,cell,max(2,cell*.18)); cr.set_source_rgba(.45,.45,.45,.18) if level==0 else cr.set_source_rgba(.18,.52,.78,(.24,.42,.62,.82)[level-1]); cr.fill(); x+=cell+gap
        cr.set_source_rgba(.45,.45,.45,.82); cr.move_to(x+4,legend_y+cell*.78); cr.show_text("Daha fazla")
    def _on_motion(self,_controller,x,y):
        week=int((x-self._left)/(self._cell_size+self._gap)); row=int((y-self._top)/(self._cell_size+self._gap))
        if week<0 or week>=self._weeks() or row<0 or row>=7: self.set_tooltip_text(None); return
        day=self._calendar_start()+timedelta(days=week*7+row)
        if day.year!=self.year: self.set_tooltip_text(None); return
        item=self.days.get(day)
        if not item: text=f"{day.day} {MONTHS[day.month-1]} {day.year}\nÇalışma yok"
        else: text=f"{day.day} {MONTHS[day.month-1]} {day.year}\n{int(item['sessions'])} çalışma · {self._duration_text(float(item['duration_seconds']))}\nOrtalama hız: Dakikada {float(item['average_speed']):.0f} kelime · Doğruluk: %{float(item['accuracy_percent']):.0f}"
        self.set_tooltip_text(text)
    def _on_leave(self,_controller): self.set_tooltip_text(None)
    @staticmethod
    def _duration_text(seconds):
        total=max(0,int(round(seconds)))
        if total<60:return f"{total} sn"
        minutes,remainder=divmod(total,60)
        if minutes<60:return f"{minutes} dk" if remainder==0 else f"{minutes} dk {remainder} sn"
        hours,minutes=divmod(minutes,60); return f"{hours} sa {minutes} dk" if minutes else f"{hours} sa"


class StatisticsPanel(Gtk.Box):
    PERIODS=("Günlük","Haftalık","Aylık","Yıllık","Tümü")
    def __init__(self,database: Database)->None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL,spacing=0); self.set_hexpand(True); self.set_vexpand(True); self.db=database; self.selected_period="Haftalık"; self.activity_year=datetime.now().year; self._build(); self.refresh()
    @staticmethod
    def _revealed(child,delay):
        r=Gtk.Revealer(); r.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE); r.set_transition_duration(220); r.set_reveal_child(False); r.set_child(child); GLib.timeout_add(delay,lambda:(r.set_reveal_child(True),GLib.SOURCE_REMOVE)[1]); return r
    @staticmethod
    def _section(title,subtitle=None):
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=3); label=Gtk.Label(label=title); label.set_xalign(0); label.add_css_class("title-2"); box.append(label)
        if subtitle:
            d=Gtk.Label(label=subtitle); d.set_xalign(0); d.set_wrap(True); d.add_css_class("dim-label"); box.append(d)
        return box
    def _build(self):
        scroll=Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC); scroll.set_hexpand(True); scroll.set_vexpand(True); self.append(scroll)
        content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=22); content.set_hexpand(True); content.set_margin_top(28); content.set_margin_bottom(40); content.set_margin_start(20); content.set_margin_end(20); scroll.set_child(content)
        content.append(self._revealed(self._header(),40)); content.append(self._revealed(self._period(),80)); content.append(self._revealed(self._metrics(),120)); content.append(self._revealed(self._speed(),160)); content.append(self._revealed(self._accuracy(),200)); content.append(self._revealed(self._activity(),240)); content.append(self._revealed(self._records(),280)); content.append(self._revealed(self._progress(),320)); content.append(self._revealed(self._history(),360))
    def _header(self): return self._section("İstatistikler","Yazma gelişimini tek bakışta takip et.")
    def _period(self):
        s=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8); s.append(self._section("Dönem")); c=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=0); c.add_css_class("linked"); self.period_buttons=[]; prev=None
        for p in self.PERIODS:
            b=Gtk.ToggleButton(label=p); b.set_hexpand(True); b.set_active(p==self.selected_period); b.set_group(prev) if prev else None; b.connect("toggled",self._on_period_toggled,p); c.append(b); self.period_buttons.append(b); prev=b
        s.append(c); return s
    def _metrics(self):
        g=Gtk.Grid(); g.set_row_spacing(10); g.set_column_spacing(10); self.metric_cards=tuple(MetricCard(x) for x in ("Ortalama hız","Doğruluk","Çalışma süresi","Çalışma sayısı"))
        for i,card in enumerate(self.metric_cards): g.attach(card,i,0,1,1)
        return g
    def _speed(self):
        s=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); s.append(self._section("Yazma hızı","Çalışmalarındaki hız değişimi")); f=Gtk.Frame(); f.add_css_class("card"); b=Gtk.Box(orientation=Gtk.Orientation.VERTICAL); b.set_margin_top(12); b.set_margin_bottom(12); b.set_margin_start(12); b.set_margin_end(12); self.chart=ProgressChart(); b.append(self.chart); self.chart_empty=Gtk.Label(label="Tamamlanmış çalışmalar burada grafik olarak görünecek."); self.chart_empty.add_css_class("dim-label"); b.append(self.chart_empty); f.set_child(b); s.append(f); return s
    def _accuracy(self):
        s=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); s.append(self._section("Doğruluk","Doğru ve yanlış kelimeleri birlikte gör")); f=Gtk.Frame(); f.add_css_class("card"); b=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12); b.set_margin_top(18); b.set_margin_bottom(18); b.set_margin_start(18); b.set_margin_end(18); self.accuracy_value=Gtk.Label(label="%0"); self.accuracy_value.add_css_class("title-1"); self.accuracy_value.set_xalign(0); b.append(self.accuracy_value); self.accuracy_bar=Gtk.ProgressBar(); self.accuracy_bar.set_show_text(False); b.append(self.accuracy_bar); split=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=18); self.correct_label=Gtk.Label(label="Doğru: 0"); self.correct_label.set_xalign(0); self.wrong_label=Gtk.Label(label="Yanlış: 0"); self.wrong_label.set_xalign(0); split.append(self.correct_label); split.append(self.wrong_label); b.append(split); f.set_child(b); s.append(f); return s
    def _activity(self):
        s=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); s.append(self._section("Çalışma takvimi","Yıl boyunca yaptığın pratikleri GitHub tarzı katkı görünümünde takip et.")); f=Gtk.Frame(); f.add_css_class("card"); o=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12); o.set_margin_top(14); o.set_margin_bottom(14); o.set_margin_start(14); o.set_margin_end(14); c=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=8); c.append(Gtk.Label(label="Yıl")); self.activity_year_dropdown=Gtk.DropDown(); self.activity_year_dropdown.connect("notify::selected",self._on_activity_year_changed); c.append(self.activity_year_dropdown); o.append(c); self.activity_summary=Gtk.Label(label="Henüz çalışma yok"); self.activity_summary.set_xalign(0); self.activity_summary.add_css_class("dim-label"); o.append(self.activity_summary); self.activity_heatmap=ActivityHeatmap(); o.append(self.activity_heatmap); f.set_child(o); s.append(f); return s
    def _records(self):
        s=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); s.append(self._section("Kişisel rekorlar","Seçili dönemdeki en yüksek değerlerin")); g=Gtk.Grid(); g.set_row_spacing(10); g.set_column_spacing(10); self.record_values=[]
        for i,title in enumerate(("En yüksek hız","En yüksek doğruluk","En uzun çalışma","En yoğun gün")):
            card=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6); card.add_css_class("card"); card.set_hexpand(True); name=Gtk.Label(label=title); name.set_xalign(0); name.set_margin_top(12); name.set_margin_start(12); name.set_margin_end(12); name.add_css_class("dim-label"); card.append(name); value=Gtk.Label(label="—"); value.set_xalign(0); value.set_wrap(True); value.add_css_class("heading"); value.set_margin_start(12); value.set_margin_bottom(12); card.append(value); self.record_values.append(value); g.attach(card,i,0,1,1)
        s.append(g); return s
    def _progress(self):
        s=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); s.append(self._section("Gelişim","İlk ve son çalışmaların arasındaki değişim")); g=Adw.PreferencesGroup(); self.progress_speed=Adw.ActionRow(); self.progress_speed.set_title("Yazma hızı"); self.progress_speed.set_subtitle("Yeterli veri olduğunda gösterilir"); g.add(self.progress_speed); self.progress_accuracy=Adw.ActionRow(); self.progress_accuracy.set_title("Doğruluk"); self.progress_accuracy.set_subtitle("Yeterli veri olduğunda gösterilir"); g.add(self.progress_accuracy); s.append(g); return s
    def _history(self):
        s=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10); s.append(self._section("Son çalışmalar","Tamamlanan çalışmaların ayrıntıları")); f=Gtk.Frame(); f.add_css_class("card"); self.history_box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL); self.history_empty=Gtk.Label(label="Henüz tamamlanmış çalışma yok"); self.history_empty.add_css_class("dim-label"); self.history_empty.set_margin_top(18); self.history_empty.set_margin_bottom(18); self.history_box.append(self.history_empty); f.set_child(self.history_box); s.append(f); return s
    def _on_period_toggled(self,b,p):
        if b.get_active(): self.selected_period=p; self.refresh()
    def _on_activity_year_changed(self,d,_p):
        m=d.get_model(); i=d.get_selected()
        if m is None or i==Gtk.INVALID_LIST_POSITION:return
        try:self.activity_year=int(m.get_item(i).get_string())
        except (AttributeError,ValueError):return
        self._refresh_activity()
    @staticmethod
    def _duration_text(seconds):
        total=max(0,int(round(seconds)))
        if total<60:return f"{total} sn"
        minutes,remainder=divmod(total,60)
        if minutes<60:return f"{minutes} dk" if remainder==0 else f"{minutes} dk {remainder} sn"
        hours,minutes=divmod(minutes,60); return f"{hours} sa {minutes} dk" if minutes else f"{hours} sa"
    @staticmethod
    def _date_text(value): return f"{value.day} {MONTHS[value.month-1]} {value.year}, {value:%H:%M}"
    @staticmethod
    def _clear_box(box):
        child=box.get_first_child()
        while child:
            nxt=child.get_next_sibling(); child.unparent(); child=nxt
    def _refresh_activity_years(self):
        years=self.db.practice_activity_years(); current=datetime.now().year
        if current not in years: years.insert(0,current)
        years=sorted(set(years),reverse=True)
        if self.activity_year not in years:self.activity_year=years[0]
        self.activity_year_dropdown.set_model(Gtk.StringList.new([str(y) for y in years])); self.activity_year_dropdown.set_selected(years.index(self.activity_year))
    def _refresh_activity(self):
        data=self.db.practice_activity(self.activity_year); self.activity_heatmap.set_data(self.activity_year,data)
        if not data:self.activity_summary.set_text(f"{self.activity_year}: Henüz çalışma yapılmadı."); return
        self.activity_summary.set_text(f"{self.activity_year}: {len(data)} aktif gün · {sum(int(x['sessions']) for x in data)} çalışma · {self._duration_text(sum(float(x['duration_seconds']) for x in data))} toplam süre")
    def _set_records(self,history):
        if not history:
            for l in self.record_values:l.set_text("—")
            return
        fastest=max(history,key=lambda x:float(x["words_per_minute"])); accurate=max(history,key=lambda x:float(x["accuracy_percent"])); longest=max(history,key=lambda x:float(x["duration_seconds"])); by_day={}
        for item in history:
            day=item["completed_at"].date(); by_day[day]=by_day.get(day,0)+float(item["duration_seconds"])
        busiest=max(by_day.items(),key=lambda x:x[1]); self.record_values[0].set_text(f"Dakikada {float(fastest['words_per_minute']):.0f} kelime"); self.record_values[1].set_text(f"%{float(accurate['accuracy_percent']):.0f}"); self.record_values[2].set_text(self._duration_text(float(longest["duration_seconds"]))); self.record_values[3].set_text(f"{busiest[0].day} {MONTHS[busiest[0].month-1]}")
    def _set_progress(self,history):
        if len(history)<2:
            self.progress_speed.set_subtitle("En az iki çalışma olduğunda karşılaştırma gösterilir"); self.progress_accuracy.set_subtitle("En az iki çalışma olduğunda karşılaştırma gösterilir"); return
        ordered=sorted(history,key=lambda x:x["completed_at"]); first,latest=ordered[0],ordered[-1]; sd=float(latest["words_per_minute"])-float(first["words_per_minute"]); ad=float(latest["accuracy_percent"])-float(first["accuracy_percent"]); self.progress_speed.set_subtitle(f"İlk: Dakikada {float(first['words_per_minute']):.0f} kelime  →  Son: Dakikada {float(latest['words_per_minute']):.0f} kelime  ({'+' if sd>=0 else ''}{sd:.0f})"); self.progress_accuracy.set_subtitle(f"İlk: %{float(first['accuracy_percent']):.0f}  →  Son: %{float(latest['accuracy_percent']):.0f}  ({'+' if ad>=0 else ''}{ad:.0f} puan)")
    def _set_history(self,history):
        self._clear_box(self.history_box)
        if not history:self.history_box.append(self.history_empty); return
        header=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10); header.set_margin_top(10); header.set_margin_bottom(10); header.set_margin_start(16); header.set_margin_end(16)
        for title in ("Tarih","Ders","Süre","Sonuç","Doğruluk","Hız"):
            l=Gtk.Label(label=title); l.set_xalign(0); l.set_hexpand(True); l.add_css_class("dim-label"); header.append(l)
        self.history_box.append(header); self.history_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        for item in history:
            row=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=10); row.set_margin_top(9); row.set_margin_bottom(9); row.set_margin_start(16); row.set_margin_end(16)
            for value in (self._date_text(item["completed_at"]),str(item["lesson_title"] or "Ders"),self._duration_text(float(item["duration_seconds"])),f"{int(item['typed_word_count'])} kelime",f"%{float(item['accuracy_percent']):.0f}",f"Dakikada {float(item['words_per_minute']):.0f} kelime"):
                l=Gtk.Label(label=value); l.set_xalign(0); l.set_hexpand(True); l.set_wrap(True); row.append(l)
            self.history_box.append(row)
    def refresh(self):
        stats=self.db.practice_statistics(self.selected_period); practices=int(stats["practices"]); duration=float(stats["duration_seconds"]); accuracy=float(stats["accuracy_percent"]); points=list(stats["speed_points"]); history=list(stats["history"]); avg=sum(float(v) for _,v in points)/len(points) if points else 0
        self.metric_cards[0].set_value(avg,lambda n:f"{n:.0f}"," kelime/dk"); self.metric_cards[1].set_value(accuracy,lambda n:f"%{n:.0f}"); self.metric_cards[2].set_value(duration/60,lambda n:self._duration_text(n*60)); self.metric_cards[3].set_value(practices); self.chart.set_points(points); self.chart_empty.set_visible(not bool(points)); self.accuracy_value.set_text(f"%{accuracy:.0f}"); self.accuracy_bar.set_fraction(max(0,min(1,accuracy/100))); self.correct_label.set_text(f"Doğru: {int(stats['correct_words'])}"); self.wrong_label.set_text(f"Yanlış: {int(stats['wrong_words'])}"); self._refresh_activity_years(); self._refresh_activity(); self._set_records(history); self._set_progress(history); self._set_history(history)
