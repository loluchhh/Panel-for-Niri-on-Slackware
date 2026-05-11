#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GtkLayerShell, GLib, Gdk
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import threading
import json

class Clock(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        date_and_day_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.date_label = Gtk.Label()
        self.day_label = Gtk.Label()
        date_and_day_box.pack_start(self.date_label, False, False, 0)
        date_and_day_box.pack_start(self.day_label, False, False, 0)

        self.time_label = Gtk.Label()

        self.pack_start(date_and_day_box, False, False, 0)
        self.pack_start(self.time_label, False, False, 0)

        self.update()
        GLib.timeout_add_seconds(1, self.update)

    def update(self):
        now = datetime.now(ZoneInfo("Europe/Prague"))
        self.time_label.set_markup(
            f'<span font="12" weight="bold">{now.strftime("%H:%M:%S")}</span>'
        )
        self.date_label.set_markup(
                f'<span font="8.5" weight="normal">{now.strftime("%Y.%m.%d")}</span>'
        )
        self.day_label.set_markup(
            f'<span font="8.5" weight="normal">{now.strftime("%A")}</span>'
        )
        return True


class Battery(Gtk.EventBox):
    def __init__(self):
        super().__init__()
        #self.get_style_context().add_class('section')

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add(box)

        self.icon_label = Gtk.Label()
        self.percent_label = Gtk.Label()

        box.pack_start(self.icon_label, False, False, 0)
        box.pack_start(self.percent_label, False, False, 0)

        self.connect("button-press-event", self.on_click)

        self.update()
        GLib.timeout_add_seconds(30, self.update)

    def read_battery(self):
        try:
            with open("/sys/class/power_supply/BAT0/capacity") as f:
                capacity = int(f.read().strip())
            with open("/sys/class/power_supply/BAT0/status") as f:
                status = f.read().strip()
            return capacity, status
        except:
            return None, None

    def on_click(self, widget, event):
        # Здесь будет попап с подробной информацией
        pass

    def update(self):
        capacity, status = self.read_battery()

        if capacity is None:
            self.icon_label.set_text("?")
            self.percent_label.set_text("N/A")
            return True

        # Иконка в зависимости от уровня и статуса
        if status == "Charging":
            if capacity == 100:
                icon = "\U000f0085"
            elif 90 <= capacity < 100:
                icon = "\U000f008b"
            elif 80 <= capacity < 90:
                icon = "\U000f008a"
            elif 70 <= capacity < 80:
                icon = "\U000f089e"
            elif 60 <= capacity < 70:
                icon = "\U000f0089"
            elif 50 <= capacity < 60:
                icon = "\U000f089d"
            elif 40 <= capacity < 50:
                icon = "\U000f0088"
            elif 30 <= capacity < 40:
                icon = "\U000f0087"
            elif 20 <= capacity < 30:
                icon = "\U000f0086"
            elif 10 <= capacity < 20:
                icon = "\U000f089c"
            else:
                icon = "\U000f089f"
        else:
            if capacity == 100:
                icon = "\U000f0079"
            elif 90 <= capacity < 100:
                icon = "\U000f0082"
            elif 80 <= capacity < 90:
                icon = "\U000f0081"
            elif 70 <= capacity < 80:
                icon = "\U000f0080"
            elif 60 <= capacity < 70:
                icon = "\U000f007f"
            elif 50 <= capacity < 60:
                icon = "\U000f007e"
            elif 40 <= capacity < 50:
                icon = "\U000f007d"
            elif 30 <= capacity < 40:
                icon = "\U000f007c"
            elif 20 <= capacity < 30:
                icon = "\U000f007b"
            elif 10 <= capacity < 20:
                icon = "\U000f007a"
            else:
                icon = "\U000f10cd"

        self.icon_label.set_markup(
            f'<span font="12">{icon}</span>'
        )
        self.percent_label.set_markup(
            f'<span font="12" foreground="#ffffff">{capacity}%</span>'
        )

        return True


class KeyboardLayout(Gtk.EventBox):
    def __init__(self):
        super().__init__()

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add(box)

        self.keyboard_label = Gtk.Label()
        keyboard_icon = "\U000f030c"
        self.keyboard_label.set_markup(
            f'<span font="12">{keyboard_icon}</span>'
        )
        self.layout_label = Gtk.Label()
        box.pack_start(self.keyboard_label, False, False, 0)
        box.pack_start(self.layout_label, False, False, 0)

        self.connect("button-press-event", self.on_click)

        # Список раскладок
        self.layouts = self.get_layouts()

        self.update_by_index(0)

        # Слушаем event stream в отдельном потоке
        threading.Thread(target=self.listen_events, daemon=True).start()

    def get_layouts(self):
        try:
            result = subprocess.run(
                ['niri', 'msg', 'keyboard-layouts'],
                capture_output=True, text=True
            )
            layouts = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or 'Keyboard layouts' in line:
                    continue
                name = line.lstrip('*').split(maxsplit=1)[-1][:2].upper()
                layouts.append(name) 
            return layouts
        except:
            return ["??"]

    def update_by_index(self, idx):
        if idx < len(self.layouts):
            layout = self.layouts[idx]
        else:
            layout = "??"
        self.layout_label.set_markup(
            f'<span font="12">{layout}</span>'
        )

    def listen_events(self):
        proc = subprocess.Popen(
            ['niri', 'msg', '--json', 'event-stream'],
            stdout=subprocess.PIPE, text=True
        )
        for line in proc.stdout:
            try:
                event = json.loads(line)
                if 'KeyboardLayoutSwitched' in event:
                    idx = event['KeyboardLayoutSwitched']['idx']
                    GLib.idle_add(self.update_by_index, idx)
            except:
                pass

    def on_click(self, widget, event):
        subprocess.run(['niri', 'msg', 'action', 'switch-layout', 'next'])


class PowerButton(Gtk.EventBox):
    def __init__(self):
        super().__init__()

        box = Gtk.Box()
        box.set_margin_end(6)

        label = Gtk.Label()
        label.set_markup(
            f'<span font="16">\ue36e</span>'
        )
        box.add(label)
        self.add(box)

        self.connect("button-press-event", self.on_click)

    def on_click(self, widget, event):
        pass


class Volume(Gtk.EventBox):
    def __init__(self):
        super().__init__()

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add(box)

        self.icon_label = Gtk.Label()
        self.vol_label = Gtk.Label()
        self.vol_label.set_size_request(36, -1)
        self.vol_label.set_xalign(0.0)
        spacer = Gtk.Box()
        spacer.set_size_request(6, -1)

        box.pack_start(self.icon_label, False, False, 0)
        box.pack_start(spacer, False, False, 0)
        box.pack_start(self.vol_label, False, False, 4)
        #self.vol_label.set_size_request(36, -1)
        #self.vol_label.set_xalign(0.0)

        self.connect("button-press-event", self.on_click)
        self.connect("scroll-event", self.on_scroll)

        # Включаем обработку скролла
        self.add_events(Gdk.EventMask.SCROLL_MASK)

        self.update()
        GLib.timeout_add_seconds(2, self.update)

    def get_volume(self):
        try:
            result = subprocess.run(
                ['pactl', 'get-sink-volume', '@DEFAULT_SINK@'],
                capture_output=True, text=True
            )
            # Берём первый процент из строки
            for part in result.stdout.split():
                if '%' in part:
                    return int(part.strip('%'))
        except:
            pass
        return 0

    def is_muted(self):
        try:
            result = subprocess.run(
                ['pactl', 'get-sink-mute', '@DEFAULT_SINK@'],
                capture_output=True, text=True
            )
            return 'yes' in result.stdout
        except:
            return False

    def update(self):
        vol = self.get_volume()
        muted = self.is_muted()

        if muted:
            icon = "\uf2a0"  # muted
            color = "#888888"
        elif vol > 66:
            icon = "\uf028"  # high
            color = "#ffffff"
        elif vol > 33:
            icon = "\uf027"  # medium
            color = "#ffffff"
        else:
            icon = "\uf026"  # low
            color = "#ffffff"

        self.icon_label.set_markup(f'<span font="16" foreground="{color}">{icon}</span>')
        self.vol_label.set_markup(f'<span font="12" foreground="{color}">{vol}%</span>')

        return True

    def on_click(self, widget, event):
        subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', 'toggle'])
        self.update()

    def on_scroll(self, widget, event):
        if event.direction.value_name == 'GDK_SCROLL_UP':
            subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '+5%'])
        # Ограничиваем 100%
            vol = self.get_volume()
            if vol > 100:
                subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '100%'])
        elif event.direction.value_name == 'GDK_SCROLL_DOWN':
            subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-5%'])
        self.update()


class Brightness(Gtk.EventBox):
    def __init__(self):
        super().__init__()
      
        self.backlight_path = "/sys/class/backlight/amdgpu_bl1/"

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add(box)

        self.icon_label = Gtk.Label()
        self.icon_label.set_xalign(0.0)
        self.bri_label = Gtk.Label()
        self.bri_label.set_size_request(42, -1)
        spacer = Gtk.Box()
        spacer.set_size_request(5, -1)

        box.pack_start(self.icon_label, False, False, 0)
        box.pack_start(spacer, False, False, 0)
        box.pack_start(self.bri_label, False, False, 0)

        self.connect("scroll-event", self.on_scroll)
        self.add_events(Gdk.EventMask.SCROLL_MASK)

        self.max_brightness = self.read_file("max_brightness")

        self.update()
        GLib.timeout_add_seconds(2, self.update)

    def read_file(self, filename):
        try:
            with open(self.backlight_path + filename) as f:
                return int(f.read().strip())
        except:
            return 1

    def get_percent(self):
        current = self.read_file("brightness")
        return int(current / self.max_brightness * 100)

    def set_brightness(self, percent):
        percent = max(5, min(100, percent))
        value = int(percent / 100 * self.max_brightness)
        try:
            with open(self.backlight_path + "brightness", "w") as f:
                f.write(str(value))
        except:
            pass

    def update(self):
        percent = self.get_percent()

        if percent > 66:
            icon = "\U000f00e0"  # высокая
        elif percent > 33:
            icon = "\U000f00df"  # средняя
        else:
            icon = "\U000f00de"  # низкая

        self.icon_label.set_markup(f'<span font="16">{icon}</span>')
        self.bri_label.set_markup(f'<span font="12">{percent}%</span>')

        return True

    def on_scroll(self, widget, event):
        percent = self.get_percent()
        if event.direction.value_name == 'GDK_SCROLL_UP':
            self.set_brightness(percent + 5)
        elif event.direction.value_name == 'GDK_SCROLL_DOWN':
            self.set_brightness(percent - 5)
        self.update()


class Workspaces(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        self.buttons = {}  # id -> кнопка
        self.active_id = None

        self.load_workspaces()
        threading.Thread(target=self.listen_events, daemon=True).start()

    def load_workspaces(self):
        try:
            result = subprocess.run(
                ['niri', 'msg', '--json', 'workspaces'],
                capture_output=True, text=True
            )
            workspaces = json.loads(result.stdout)
            for ws in workspaces:
                self.add_button(ws['id'], ws['idx'], ws['is_active'])
        except:
            pass

    def add_button(self, ws_id, idx, is_active):
        btn = Gtk.Button()
        btn.get_style_context().add_class('ws-btn')
        if is_active:
            btn.get_style_context().add_class('ws-active')
            self.active_id = ws_id
        btn.connect('clicked', self.on_click, ws_id)
        self.buttons[ws_id] = btn
        self.pack_start(btn, False, False, 0)
        btn.show()

    def set_active(self, ws_id):
        # Снимаем активный класс со старой кнопки
        if self.active_id and self.active_id in self.buttons:
            self.buttons[self.active_id].get_style_context().remove_class('ws-active')
        # Ставим на новую
        if ws_id in self.buttons:
            self.buttons[ws_id].get_style_context().add_class('ws-active')
        self.active_id = ws_id

    def listen_events(self):
        proc = subprocess.Popen(
            ['niri', 'msg', '--json', 'event-stream'],
            stdout=subprocess.PIPE, text=True
        )
        for line in proc.stdout:
            try:
                event = json.loads(line)
                if 'WorkspaceActivated' in event:
                    ws_id = event['WorkspaceActivated']['id']
                    GLib.idle_add(self.set_active, ws_id)
            except:
                pass

    def on_click(self, btn, ws_id):
        subprocess.run(['niri', 'msg', 'action', 'focus-workspace', str(ws_id)])


class Panel(Gtk.Window):
    def __init__(self):
        super().__init__()

        # --- Layer Shell: прикрепляем к экрану ---
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)

        # Прикрепляем к верху и бокам
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)

        # Отступ сверху — панель не вплотную к краю
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 6)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 6)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 6)

        # НЕ резервируем место — панель плавает поверх окон
        GtkLayerShell.set_exclusive_zone(self, -1)

        # --- CSS стили ---
        css = b"""
        window {
            font-family: JetBrainsMono Nerd Font;
            background-color: rgba(255, 250, 205, 0.5);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .panel-box {
            padding: 2px 12px;
            min-height: 32px;
        }
        .section {
            background-color: rgba(255, 255, 255, 0.07);
            border-radius: 8px;
            padding: 2px 8px;
        }
        .panel-separator {
            background-color: rgba(0, 0, 0, 0.2);
            min-width: 1px;
            border-radius: 2px;
            margin-top: 6px;
        }
        .right-box {
            border: 4px solid rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 2px 8px;
            margin-top: -2px;
            margin-bottom: -2px;
            margin-right: -12px;
        }
        .ws-btn {
            background: transparent;
            border: 2px solid rgba(255, 255, 255, 0.5);
            border-radius: 999px;
            padding: 0px;
            min-width: 8px;
            min-height: 8px;
        }
        .ws-active {
            background: rgba(255, 255, 255, 0.9);
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # --- Основной контейнер: три блока ---
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.get_style_context().add_class('panel-box')
        self.add(root)

        # SEPARATOR
        def make_separator():
            separator = Gtk.Box()
            separator.set_size_request(8, -1)
            return separator

        # LEFT BLOCK
        self.left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.slackware_label = Gtk.Label()
        self.slackware_label.set_markup(
            f'<span font="20">\uf318</span>'
        )
        self.left.pack_start(self.slackware_label, False, False, 8)

        self.workspaces = Workspaces()
        self.left.pack_start(self.workspaces, False, False, 0)

        root.pack_start(self.left, False, False, 0)

        # Центр (часы)
        self.center = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.set_center_widget(self.center)

        # RIGHT BLOCK
        self.right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.right.get_style_context().add_class('right-box')

        self.power = PowerButton()
        self.right.pack_end(self.power, False, False, 0)
        self.right.pack_end(make_separator(), False, False, 0)

        #self.battery_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        
        self.battery = Battery()
        self.right.pack_end(self.battery, False, False, 0)
        self.right.pack_end(make_separator(), False, False, 0)

        self.keyboard = KeyboardLayout()
        self.right.pack_end(self.keyboard, False, False, 0)
        self.right.pack_end(make_separator(), False, False, 0)

        self.volume = Volume()
        self.right.pack_end(self.volume, False, False, 0)
        self.right.pack_end(make_separator(), False, False, 0)

        self.brightness = Brightness()
        self.right.pack_end(self.brightness, False, False, 0)

        root.pack_end(self.right, False, False, 0)

        self.clock = Clock()
        self.center.add(self.clock)

        self.show_all()

def on_activate(app):
    panel = Panel()
    app.add_window(panel)  # регистрируем окно в приложении

app = Gtk.Application()
app.connect('activate', on_activate)
app.run()


