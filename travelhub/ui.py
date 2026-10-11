#!/usr/bin/env python3
"""Окно TravelHub: вход, роли, заявки, экскурсии и лавка."""

import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Adw, Gdk, GdkPixbuf, Gtk, Pango

from travelhub import db, matching

ROLE_ORDER = ("admin", "guide", "producer", "tourist")
REGION_TONE = {
    "karelia": "th-karelia",
    "altai": "th-altai",
    "golden_ring": "th-ring",
    "kaliningrad": "th-amber",
    "baikal": "th-baikal",
    "other": "th-pine",
}
CSS = """
@define-color accent_bg_color #c45c38;
@define-color accent_fg_color #fffaf3;
@define-color accent_color #a34b30;
@define-color window_bg_color #f3ecdf;
@define-color window_fg_color #1c2b29;
@define-color view_bg_color #f3ecdf;
@define-color view_fg_color #1c2b29;
@define-color card_bg_color #fffdf8;
@define-color card_fg_color #1c2b29;
@define-color headerbar_bg_color #14332f;
@define-color headerbar_fg_color #f6f1e6;
@define-color popover_bg_color #fffdf8;
@define-color popover_fg_color #1c2b29;
@define-color dialog_bg_color #fffdf8;
@define-color dialog_fg_color #1c2b29;

.error-text { color: #8c3d32; font-weight: 700; }

.th-titlebar {
  background: #14332f;
  color: #f6f1e6;
  box-shadow: none;
}
.th-mast {
  background: #14332f;
  padding: 4px 18px 14px;
}
.th-mast label { color: #f6f1e6; }
.th-wordmark {
  font-family: "Noto Serif";
  font-size: 26px;
  font-weight: 700;
}
.th-kicker {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
}
.th-kicker-ink { color: #8c3d32; }
.th-nav {
  background: transparent;
  color: #d7e6e1;
  border-radius: 999px;
  padding: 6px 12px;
  font-weight: 700;
}
.th-nav:checked {
  background: #c45c38;
  color: #fffaf3;
}
.th-nav label { color: #d7e6e1; }
.th-nav:checked label { color: #fffaf3; }
.th-quiet label { color: #f6f1e6; }
.th-quiet {
  background: transparent;
  color: #f6f1e6;
  border-radius: 999px;
  border: 1px solid rgba(246, 241, 230, 0.35);
  padding: 4px 12px;
}
.th-paper { background: #f3ecdf; }
.th-display {
  font-family: "Noto Serif";
  font-size: 32px;
  font-weight: 700;
  color: #1c2b29;
}
.th-meta { color: #6d6256; }
.th-sheet { background: transparent; }

.th-strips { background: transparent; }
.th-strips row {
  background: #fffdf8;
  border-radius: 16px;
  margin-bottom: 8px;
  border: 1px solid rgba(28, 43, 41, 0.08);
}
.th-strips row:selected { background: #fff1e6; }
.th-strip { padding: 10px 12px; }
.th-strip-title {
  font-family: "Noto Serif";
  font-size: 16px;
  font-weight: 700;
  color: #1c2b29;
}
.th-stamp {
  background: #14332f;
  color: #f6f1e6;
  border-radius: 14px;
  font-family: "Noto Serif";
  font-weight: 700;
  min-width: 46px;
  padding: 8px 4px;
}
.th-pill {
  background: #f3e2d4;
  color: #8c3d32;
  border-radius: 999px;
  padding: 4px 10px;
  font-weight: 700;
  font-size: 12px;
}

.th-board { background: transparent; }
flowboxchild { background: transparent; padding: 4px; }
.th-card {
  background: #fffdf8;
  border-radius: 18px;
}
.th-band { padding: 14px 16px 16px; border-radius: 18px 18px 0 0; }
.th-band label { color: #fffaf3; }
.th-card-title {
  font-family: "Noto Serif";
  font-size: 20px;
  font-weight: 700;
}
.th-card-body { padding: 12px 16px 14px; }
.th-price {
  font-family: "Noto Serif";
  font-size: 18px;
  font-weight: 700;
  color: #8c3d32;
}
.th-karelia { background: #1f6b5a; }
.th-altai { background: #c4842a; }
.th-ring { background: #8c3d32; }
.th-amber { background: #b86a22; }
.th-baikal { background: #2f6f8f; }
.th-pine { background: #14332f; }
.th-stamp.th-karelia,
.th-stamp.th-altai,
.th-stamp.th-ring,
.th-stamp.th-amber,
.th-stamp.th-baikal,
.th-stamp.th-pine { color: #fffaf3; }

.th-stat {
  background: #fffdf8;
  border-radius: 18px;
  padding: 12px 14px;
}
.th-stat-num {
  font-family: "Noto Serif";
  font-size: 28px;
  font-weight: 700;
  color: #1c2b29;
}
.th-person {
  background: #fffdf8;
  border-radius: 16px;
  padding: 10px 12px;
}

.th-app { background: #f3ecdf; }
.th-poster { background: #14332f; padding: 36px 32px; }
.th-poster label { color: #f6f1e6; }
.th-poster-title {
  font-family: "Noto Serif";
  font-size: 54px;
  font-weight: 700;
}
.th-form {
  background: #f3ecdf;
  padding: 36px 28px;
}
.th-seg {
  background: transparent;
  border-radius: 999px;
  padding: 6px 14px;
  font-weight: 700;
}
.th-seg:checked {
  background: #14332f;
  color: #f6f1e6;
}
.stat-card {
  background: #fffdf8;
  border-radius: 14px;
  padding: 10px 12px;
}
"""


def asset_path(name):
    roots = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(meipass)
    roots.append(os.path.dirname(os.path.abspath(__file__)))
    for root in roots:
        path = os.path.join(root, "assets", name)
        if os.path.exists(path):
            return path
    return os.path.join(roots[-1], "assets", name)


def logo_paintable(size):
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(asset_path("logo.png"), size, size)
    return Gdk.Texture.new_for_pixbuf(pixbuf)


def logo_image(size):
    image = Gtk.Image.new_from_paintable(logo_paintable(size))
    image.set_pixel_size(size)
    image.set_valign(Gtk.Align.CENTER)
    return image


def alert(parent, heading, body=""):
    dialog = Adw.AlertDialog(heading=heading)
    if body:
        dialog.set_body(body)
        dialog.set_prefer_wide_layout(True)
    dialog.add_response("ok", "Понятно")
    dialog.set_default_response("ok")
    dialog.present(parent)


def confirm(parent, heading, body, on_yes):
    dialog = Adw.AlertDialog(heading=heading, body=body)
    dialog.add_response("cancel", "Не надо")
    dialog.add_response("yes", "Да")
    dialog.set_response_appearance("yes", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")

    def on_response(_dialog, response):
        if response == "yes":
            on_yes()

    dialog.connect("response", on_response)
    dialog.present(parent)


def money(value):
    return f"{int(value):,}".replace(",", " ") + " ₽"


def rating_text(count, average):
    if not count:
        return "нет оценок"
    return f"{float(average):.1f}"


def selected_index(widget, count):
    index = widget.get_selected()
    if index is None or int(index) >= count:
        return 0
    return int(index)


def scrolled(child):
    widget = Gtk.ScrolledWindow()
    widget.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    widget.set_vexpand(True)
    widget.set_hexpand(True)
    widget.set_child(child)
    return widget


def field_label(text):
    label = Gtk.Label(label=text, xalign=0)
    label.add_css_class("dim-label")
    return label


def text_view(min_height=120):
    view = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, accepts_tab=False)
    view.set_left_margin(8)
    view.set_right_margin(8)
    view.set_top_margin(6)
    view.set_bottom_margin(6)
    scroll = Gtk.ScrolledWindow(min_content_height=min_height)
    scroll.set_child(view)
    scroll.add_css_class("card")
    return view, scroll


def text_of(view):
    buffer = view.get_buffer()
    return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)


def int_spin(lower, upper, value, step=1):
    button = Gtk.SpinButton.new_with_range(lower, upper, step)
    button.set_digits(0)
    button.set_numeric(True)
    button.set_value(value)
    return button


def clear_box(box):
    child = box.get_first_child()
    while child is not None:
        nxt = child.get_next_sibling()
        box.remove(child)
        child = nxt


def card_label(text):
    label = Gtk.Label(label=text, xalign=0, yalign=0, wrap=True, selectable=True)
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    card.add_css_class("th-card-body")
    card.append(label)
    return card, label


class RouteStrip(Gtk.ListBoxRow):
    def __init__(self, values):
        super().__init__()
        self.values = tuple(values)
        box = Gtk.Box(spacing=12)
        box.add_css_class("th-strip")
        stamp = Gtk.Label(label=str(values[0]))
        stamp.add_css_class("th-stamp")
        stamp.set_valign(Gtk.Align.CENTER)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
        title = Gtk.Label(label=str(values[1]), xalign=0, ellipsize=Pango.EllipsizeMode.END)
        title.add_css_class("th-strip-title")
        meta_parts = [str(item) for item in values[2:-1] if str(item) not in ("", "—")]
        meta = Gtk.Label(label="  ·  ".join(meta_parts), xalign=0, ellipsize=Pango.EllipsizeMode.END)
        meta.add_css_class("th-meta")
        pill = Gtk.Label(label=str(values[-1]))
        pill.add_css_class("th-pill")
        pill.set_valign(Gtk.Align.CENTER)
        text.append(title)
        if meta_parts:
            text.append(meta)
        box.append(stamp)
        box.append(text)
        box.append(pill)
        self.set_child(box)


class LabeledDrop(Gtk.DropDown):
    def __init__(self, pairs):
        self._ids = [key for key, _label in pairs]
        labels = [label for _key, label in pairs]
        super().__init__(model=Gtk.StringList.new(labels or ["—"]))
        self.set_selected(0)

    def value(self):
        if not self._ids:
            return None
        index = self.get_selected()
        if index is None or int(index) >= len(self._ids):
            return self._ids[0]
        return self._ids[int(index)]

    def set_value(self, key):
        if key in self._ids:
            self.set_selected(self._ids.index(key))


class UserDialog(Adw.Window):
    def __init__(self, parent, user_id, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.user_id = user_id
        self.on_saved = on_saved
        self.set_default_size(460, 640)
        self.set_title("Пользователь")
        record = db.get_user(user_id) if user_id else None

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(
            Adw.WindowTitle(
                title="Новый пользователь" if record is None else record["full_name"],
                subtitle="Учётная запись",
            )
        )
        save = Gtk.Button(label="Сохранить")
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda *_: self._save())
        header.pack_end(save)
        toolbar.add_top_bar(header)

        page = Adw.PreferencesPage()
        account = Adw.PreferencesGroup(title="Учётная запись")
        self.name = Adw.EntryRow(title="ФИО")
        self.login = Adw.EntryRow(title="Логин")
        self.password = Adw.PasswordEntryRow(title="Пароль" if record is None else "Новый пароль")
        self.about = Adw.EntryRow(title="О себе")
        account.add(self.name)
        account.add(self.login)
        account.add(self.password)
        account.add(self.about)
        page.add(account)

        access = Adw.PreferencesGroup(
            title="Доступ",
            description="Направление и регион гида учитываются, когда заявка назначается сама.",
        )
        self.role = Adw.ComboRow(title="Роль")
        self.role.set_model(Gtk.StringList.new([db.ROLE_RU[item] for item in ROLE_ORDER]))
        self.specialty = Adw.ComboRow(title="Направление")
        self.specialty.set_model(Gtk.StringList.new([db.THEME_RU[item] for item in db.THEMES]))
        self.region = Adw.ComboRow(title="Регион")
        self.region.set_model(Gtk.StringList.new([db.REGION_RU[item] for item in db.REGIONS]))
        self.active = Adw.SwitchRow(title="Активен", active=True)
        access.add(self.role)
        access.add(self.specialty)
        access.add(self.region)
        access.add(self.active)
        page.add(access)
        toolbar.set_content(page)
        self.set_content(toolbar)

        if record:
            self.name.set_text(record["full_name"])
            self.login.set_text(record["login"])
            self.login.set_sensitive(False)
            self.about.set_text(record["about"])
            self.role.set_selected(ROLE_ORDER.index(record["role"]))
            self.specialty.set_selected(db.THEMES.index(record["specialty"]))
            self.region.set_selected(db.REGIONS.index(record["region"]))
            self.active.set_active(bool(record["is_active"]))
        else:
            self.role.set_selected(ROLE_ORDER.index("tourist"))
            self.specialty.set_selected(db.THEMES.index("other"))
            self.region.set_selected(db.REGIONS.index("other"))

    def _save(self):
        full_name = self.name.get_text().strip()
        role = ROLE_ORDER[selected_index(self.role, len(ROLE_ORDER))]
        specialty = db.THEMES[selected_index(self.specialty, len(db.THEMES))]
        region = db.REGIONS[selected_index(self.region, len(db.REGIONS))]
        is_active = self.active.get_active()
        password = self.password.get_text()
        if self.user_id == self.parent_window.user["id"] and not is_active:
            alert(self, "Нельзя отключить свою учётную запись")
            return
        if self.user_id is None:
            ok, message = db.create_user(
                self.login.get_text(),
                password,
                full_name,
                role=role,
                specialty=specialty,
                region=region,
                about=self.about.get_text(),
                is_active=1 if is_active else 0,
            )
        else:
            fields = {
                "full_name": full_name,
                "role": role,
                "specialty": specialty,
                "region": region,
                "about": self.about.get_text(),
                "is_active": 1 if is_active else 0,
            }
            if password:
                fields["password"] = password
            ok, message = db.update_user(self.user_id, **fields)
        if not ok:
            alert(self, "Не сохранено", message)
            return
        self.close()
        self.on_saved(self.user_id, message)


class ReviewBox(Gtk.Box):
    def __init__(self, window, kind, target_id, title):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        self.kind = kind
        self.target_id = target_id
        self.group = Adw.PreferencesGroup(title=title)
        self.append(self.group)
        self._rows = []

    def reload(self):
        for row in self._rows:
            self.group.remove(row)
        self._rows.clear()
        user = self.window.user
        existing = db.find_review(user["id"], self.kind, self.target_id)
        if existing:
            subtitle = f"{existing['rating']} из 5"
            if existing["body"]:
                subtitle += f" — {existing['body']}"
            row = Adw.ActionRow(title="Ваша оценка", subtitle=subtitle)
            self.group.add(row)
            self._rows.append(row)
            self.set_visible(True)
            return
        if not db.can_review(user["id"], self.kind, self.target_id):
            self.set_visible(False)
            return
        self.set_visible(True)
        stars = LabeledDrop(
            (
                (5, "5 — отлично"),
                (4, "4 — хорошо"),
                (3, "3 — нормально"),
                (2, "2 — слабо"),
                (1, "1 — плохо"),
            )
        )
        note = Adw.EntryRow(title="Комментарий, можно пустым")
        button = Gtk.Button(label="Сохранить оценку")
        button.add_css_class("suggested-action")
        button.set_halign(Gtk.Align.START)
        button.set_margin_top(6)
        button.set_margin_bottom(6)
        button.set_margin_start(12)

        def save(_button):
            ok, message = db.add_review(
                user["id"], self.kind, self.target_id, stars.value(), note.get_text()
            )
            if not ok:
                alert(self.window, "Оценка не сохранена", message)
                return
            self.window.notify(message)
            self.reload()

        button.connect("clicked", save)
        wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        wrap.set_margin_start(12)
        wrap.set_margin_end(12)
        wrap.set_margin_bottom(8)
        wrap.append(stars)
        wrap.append(note)
        wrap.append(button)
        self.group.add(wrap)
        self._rows.append(wrap)


class RequestDialog(Adw.Window):
    def __init__(self, parent, request_id, on_changed):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.request_id = request_id
        self.on_changed = on_changed
        self.ready = False
        self.set_default_size(740, 720)
        request = db.get_request(request_id)
        if not request or not self._can_view(request):
            return
        self._build()
        self.ready = True
        self.reload()

    def _can_view(self, request):
        user = self.parent_window.user
        if user["role"] == "admin":
            return True
        if user["id"] == request["tourist_id"]:
            return True
        return user["role"] == "guide" and request["guide_id"] in (None, user["id"])

    def _build(self):
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.heading = Adw.WindowTitle(title="Заявка", subtitle="")
        header.set_title_widget(self.heading)
        toolbar.add_top_bar(header)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        self.meta = Gtk.Label(xalign=0, wrap=True, selectable=True)
        body.append(self.meta)
        self.desc_card, self.desc = card_label("")
        body.append(self.desc_card)

        self.actions = Gtk.Box(spacing=8)
        self.done_btn = Gtk.Button(label="Завершить")
        self.done_btn.add_css_class("suggested-action")
        self.done_btn.connect("clicked", lambda *_: self._status("done"))
        self.cancel_btn = Gtk.Button(label="Отменить заявку")
        self.cancel_btn.connect("clicked", lambda *_: self._status("cancelled"))
        self.actions.append(self.done_btn)
        self.actions.append(self.cancel_btn)
        body.append(self.actions)

        self.take_btn = Gtk.Button(label="Взять заявку")
        self.take_btn.add_css_class("suggested-action")
        self.take_btn.connect("clicked", lambda *_: self._take())
        body.append(self.take_btn)

        self.admin_box = Gtk.Box(spacing=8)
        guides = db.list_guides(only_active=True)
        if guides:
            self.guide_drop = LabeledDrop(
                [
                    (item["id"], f"{item['full_name']} · {db.THEME_RU[item['specialty']]}")
                    for item in guides
                ]
            )
            self.guide_drop.set_hexpand(True)
            manual = Gtk.Button(label="Назначить")
            manual.connect("clicked", lambda *_: self._assign_manual())
            self.admin_box.append(self.guide_drop)
            self.admin_box.append(manual)
        else:
            self.guide_drop = None
        auto = Gtk.Button(label="Подобрать гида")
        auto.connect("clicked", lambda *_: self._assign_auto())
        self.admin_box.append(auto)
        body.append(self.admin_box)

        self.messages_group = Adw.PreferencesGroup(title="Переписка")
        self.messages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.messages_group.add(self.messages_box)
        self.message_view, message_scroll = text_view(72)
        send = Gtk.Button(label="Отправить")
        send.connect("clicked", lambda *_: self._send())
        self.composer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.composer.append(message_scroll)
        self.composer.append(send)
        self.messages_group.add(self.composer)
        body.append(self.messages_group)

        self.review = ReviewBox(self.parent_window, "guide", 0, "Оценка гида")
        body.append(self.review)

        self.history_group = Adw.PreferencesGroup(title="Журнал")
        self.history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.history_group.add(self.history_box)
        body.append(self.history_group)
        toolbar.set_content(scrolled(body))
        self.set_content(toolbar)

    def reload(self):
        request = db.get_request(self.request_id)
        if not request:
            self.close()
            return
        user = self.parent_window.user
        self.heading.set_title(f"№{request['id']} · {request['title']}")
        self.heading.set_subtitle(db.REQUEST_STATUS_RU[request["status"]])
        self.set_title(request["title"])
        when = request["preferred_date"] or "дата не важна"
        guide = request["guide_name"] or "не назначен"
        self.meta.set_text(
            f"{db.THEME_RU[request['theme']]} · {db.REGION_RU[request['region']]} · "
            f"{db.PRIORITY_RU[request['priority']]}\n"
            f"Турист: {request['tourist_name']} · Гид: {guide}\n"
            f"Людей: {request['people']} · Дата: {when} · Создана: {request['created_at']}"
        )
        self.desc.set_text(request["description"] or "Без описания")
        open_request = request["status"] in ("new", "assigned")
        is_guide = user["role"] == "guide" and request["guide_id"] == user["id"]
        is_admin = user["role"] == "admin"
        self.done_btn.set_visible(is_admin or is_guide)
        self.done_btn.set_sensitive(request["status"] == "assigned")
        can_cancel = open_request and (
            is_admin or is_guide or user["id"] == request["tourist_id"]
        )
        self.cancel_btn.set_visible(can_cancel)
        self.actions.set_visible(self.done_btn.get_visible() or can_cancel)
        self.take_btn.set_visible(
            user["role"] == "guide" and request["guide_id"] is None and request["status"] == "new"
        )
        self.admin_box.set_visible(is_admin and open_request)
        if self.guide_drop is not None and request["guide_id"] is not None:
            self.guide_drop.set_value(request["guide_id"])
        self.composer.set_visible(
            open_request
            and (
                is_admin
                or user["id"] == request["tourist_id"]
                or is_guide
            )
        )
        self.review.target_id = request["guide_id"] or 0
        self.review.reload()
        self._show_messages()
        self._show_history()

    def _show_messages(self):
        clear_box(self.messages_box)
        messages = db.list_messages(self.request_id)
        if not messages:
            empty = Gtk.Label(label="Пока нет сообщений", xalign=0)
            empty.add_css_class("dim-label")
            self.messages_box.append(empty)
            return
        for message in messages:
            block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            block.add_css_class("card")
            block.add_css_class("stat-card")
            who = Gtk.Label(label=f"{message['user_name']} · {message['created_at']}", xalign=0)
            who.add_css_class("dim-label")
            text = Gtk.Label(label=message["body"], xalign=0, wrap=True, selectable=True)
            block.append(who)
            block.append(text)
            self.messages_box.append(block)

    def _show_history(self):
        clear_box(self.history_box)
        events = db.list_history("request", self.request_id)
        if not events:
            empty = Gtk.Label(label="Пока пусто", xalign=0)
            empty.add_css_class("dim-label")
            self.history_box.append(empty)
            return
        for event in events:
            who = event["user_name"] or "система"
            self.history_box.append(
                Adw.ActionRow(title=event["action"], subtitle=f"{event['created_at']} · {who}")
            )

    def _finish(self, message):
        self.reload()
        self.on_changed()
        if message:
            self.parent_window.notify(message)

    def _status(self, status):
        if status == "cancelled":
            confirm(self, "Отменить заявку?", "Вернуть её в работу уже не получится.", lambda: self._apply_status(status))
            return
        self._apply_status(status)

    def _apply_status(self, status):
        ok, message = db.set_request_status(self.request_id, status, self.parent_window.user["id"])
        if not ok:
            alert(self, "Не удалось", message)
            return
        self._finish(message)

    def _take(self):
        ok, message = db.take_request(self.request_id, self.parent_window.user["id"])
        if not ok:
            alert(self, "Не удалось", message)
            return
        self._finish(message)

    def _assign_manual(self):
        if self.guide_drop is None or self.guide_drop.value() is None:
            alert(self, "Нет активных гидов")
            return
        ok, message = db.assign_request(
            self.request_id,
            self.guide_drop.value(),
            self.parent_window.user["id"],
            note="вручную",
        )
        if not ok:
            alert(self, "Не удалось", message)
            return
        self._finish("Гид назначен")

    def _assign_auto(self):
        guide, debug = matching.distribute(self.request_id, self.parent_window.user["id"])
        self._finish("Гид назначен" if guide else "Гид не назначен")
        alert(self, "Подбор гида", "\n".join(debug))

    def _send(self):
        ok, message = db.add_message(self.request_id, self.parent_window.user["id"], text_of(self.message_view))
        if not ok:
            alert(self, "Не отправлено", message)
            return
        self.message_view.get_buffer().set_text("")
        self._finish(message)


class TourDialog(Adw.Window):
    def __init__(self, parent, tour_id, on_changed):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.tour_id = tour_id
        self.on_changed = on_changed
        self.ready = False
        self.set_default_size(740, 720)
        tour = db.get_tour(tour_id)
        if not tour:
            return
        self._build()
        self.ready = True
        self.reload()

    def _build(self):
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.heading = Adw.WindowTitle(title="Экскурсия", subtitle="")
        header.set_title_widget(self.heading)
        toolbar.add_top_bar(header)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        self.meta = Gtk.Label(xalign=0, wrap=True, selectable=True)
        body.append(self.meta)
        self.desc_card, self.desc = card_label("")
        body.append(self.desc_card)

        self.book_box = Gtk.Box(spacing=8)
        self.people = int_spin(1, 20, 1)
        self.book_btn = Gtk.Button(label="Забронировать")
        self.book_btn.add_css_class("suggested-action")
        self.book_btn.connect("clicked", lambda *_: self._book())
        self.book_box.append(self.people)
        self.book_box.append(self.book_btn)
        body.append(self.book_box)

        self.cancel_booking_btn = Gtk.Button(label="Снять мою бронь")
        self.cancel_booking_btn.connect(
            "clicked",
            lambda *_: confirm(self, "Снять бронь?", "Место вернётся в экскурсию.", self._cancel_booking),
        )
        body.append(self.cancel_booking_btn)

        self.manage_box = Gtk.Box(spacing=8)
        complete = Gtk.Button(label="Завершить экскурсию")
        complete.add_css_class("suggested-action")
        complete.connect("clicked", lambda *_: self._tour_status("completed"))
        cancel = Gtk.Button(label="Отменить экскурсию")
        cancel.connect(
            "clicked",
            lambda *_: confirm(
                self,
                "Отменить экскурсию?",
                "Действующие брони туристов тоже будут сняты.",
                lambda: self._tour_status("cancelled"),
            ),
        )
        self.manage_box.append(complete)
        self.manage_box.append(cancel)
        body.append(self.manage_box)

        self.people_group = Adw.PreferencesGroup(title="Кто записан")
        self.people_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.people_group.add(self.people_box)
        body.append(self.people_group)

        self.shop_group = Adw.PreferencesGroup(title="Лавка этого региона")
        self.shop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.shop_group.add(self.shop_box)
        body.append(self.shop_group)

        self.tour_review = ReviewBox(self.parent_window, "tour", self.tour_id, "Оценка экскурсии")
        self.guide_review = ReviewBox(self.parent_window, "guide", 0, "Оценка гида")
        body.append(self.tour_review)
        body.append(self.guide_review)
        toolbar.set_content(scrolled(body))
        self.set_content(toolbar)

    def reload(self):
        tour = db.get_tour(self.tour_id)
        if not tour:
            self.close()
            return
        user = self.parent_window.user
        self.heading.set_title(tour["title"])
        self.heading.set_subtitle(db.TOUR_STATUS_RU[tour["status"]])
        self.set_title(tour["title"])
        score = rating_text(tour["review_count"], tour["review_avg"])
        seats = "—"
        if tour["status"] in ("open", "full"):
            seats = f"{tour['seats_left']} из {tour['capacity']}"
        self.meta.set_text(
            f"{db.THEME_RU[tour['theme']]} · {db.REGION_RU[tour['region']]} · {tour['tour_date']}\n"
            f"Гид: {tour['guide_name']} · оценка гида: {score}\n"
            f"{money(tour['price'])} · {tour['duration_hours']} ч · места: {seats}"
        )
        self.desc.set_text(tour["description"] or "Без описания")
        mine = db.confirmed_booking(tour["id"], user["id"]) if user["role"] == "tourist" else None
        can_book = user["role"] == "tourist" and tour["status"] == "open" and mine is None and tour["seats_left"] > 0
        self.book_box.set_visible(can_book)
        if can_book:
            self.people.set_range(1, max(1, int(tour["seats_left"])))
            self.people.set_value(1)
        self.cancel_booking_btn.set_visible(mine is not None)
        self._my_booking = mine
        can_manage = tour["status"] in ("open", "full") and (
            user["role"] == "admin" or (user["role"] == "guide" and tour["guide_id"] == user["id"])
        )
        self.manage_box.set_visible(can_manage)
        self.people_group.set_visible(
            user["role"] == "admin" or (user["role"] == "guide" and tour["guide_id"] == user["id"])
        )
        self._show_people()
        self._show_shop(tour["region"])
        self.guide_review.target_id = tour["guide_id"]
        self.tour_review.reload()
        self.guide_review.reload()

    def _show_people(self):
        clear_box(self.people_box)
        rows = [
            row
            for row in db.list_bookings(tour_id=self.tour_id)
            if row["status"] != "cancelled"
        ]
        if not rows:
            empty = Gtk.Label(label="Пока никто не записан", xalign=0)
            empty.add_css_class("dim-label")
            self.people_box.append(empty)
            return
        for row in rows:
            self.people_box.append(
                Adw.ActionRow(
                    title=f"{row['tourist_name']} · {row['people']} чел.",
                    subtitle=db.BOOKING_STATUS_RU[row["status"]],
                )
            )

    def _show_shop(self, region):
        clear_box(self.shop_box)
        products = db.list_products(region=region, only_market=True)[:4]
        if not products:
            empty = Gtk.Label(label="У местных производителей пока нет товаров", xalign=0)
            empty.add_css_class("dim-label")
            self.shop_box.append(empty)
            return
        for product in products:
            stock = "нет в наличии" if product["stock"] <= 0 else f"остаток {product['stock']}"
            self.shop_box.append(
                Adw.ActionRow(
                    title=f"{product['name']} · {money(product['price'])}",
                    subtitle=f"{product['producer_name']} · {stock}",
                )
            )

    def _book(self):
        booking_id, error = db.book_tour(self.tour_id, self.parent_window.user["id"], int(self.people.get_value()))
        if error:
            alert(self, "Не записались", error)
            return
        self.reload()
        self.on_changed()
        self.parent_window.notify(f"Бронь №{booking_id} оформлена")

    def _cancel_booking(self):
        if not self._my_booking:
            return
        ok, message = db.cancel_booking(self._my_booking["id"], self.parent_window.user["id"])
        if not ok:
            alert(self, "Не удалось", message)
            return
        self.reload()
        self.on_changed()
        self.parent_window.notify(message)

    def _tour_status(self, status):
        ok, message = db.set_tour_status(self.tour_id, status, self.parent_window.user["id"])
        if not ok:
            alert(self, "Не удалось", message)
            return
        self.reload()
        self.on_changed()
        self.parent_window.notify(message)


class TourCreateDialog(Adw.Window):
    def __init__(self, parent, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.on_saved = on_saved
        self.set_default_size(520, 640)
        self.set_title("Новая экскурсия")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Новая экскурсия", subtitle="Её увидят туристы"))
        save = Gtk.Button(label="Опубликовать")
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda *_: self._save())
        header.pack_end(save)
        toolbar.add_top_bar(header)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_start(16)
        form.set_margin_end(16)
        form.set_margin_top(12)
        form.set_margin_bottom(16)
        group = Adw.PreferencesGroup(title="Маршрут")
        self.title_row = Adw.EntryRow(title="Название")
        self.date_row = Adw.EntryRow(title="Дата, ГГГГ-ММ-ДД")
        group.add(self.title_row)
        group.add(self.date_row)
        form.append(group)
        form.append(field_label("Описание"))
        self.description, desc_scroll = text_view(120)
        form.append(desc_scroll)
        themes = [(key, db.THEME_RU[key]) for key in db.THEMES if key != "other"]
        regions = [(key, db.REGION_RU[key]) for key in db.REGIONS if key != "other"]
        self.theme = LabeledDrop(themes)
        self.region = LabeledDrop(regions)
        user = parent.user
        if user["specialty"] in db.THEMES and user["specialty"] != "other":
            self.theme.set_value(user["specialty"])
        if user["region"] in db.REGIONS and user["region"] != "other":
            self.region.set_value(user["region"])
        self.hours = int_spin(1, 16, 4)
        self.price = int_spin(100, 200_000, 3000, 100)
        self.capacity = int_spin(1, 40, 8)
        form.append(self._pair("Направление", self.theme, "Регион", self.region))
        form.append(self._pair("Часы", self.hours, "Мест", self.capacity))
        price_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        price_box.append(field_label("Цена, ₽"))
        price_box.append(self.price)
        form.append(price_box)
        toolbar.set_content(scrolled(form))
        self.set_content(toolbar)

    def _pair(self, left_caption, left, right_caption, right):
        row = Gtk.Box(spacing=12)
        for caption, widget in ((left_caption, left), (right_caption, right)):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            row.append(box)
        return row

    def _save(self):
        tour_id, error = db.create_tour(
            self.title_row.get_text(),
            text_of(self.description),
            self.theme.value(),
            self.region.value(),
            self.date_row.get_text(),
            int(self.hours.get_value()),
            int(self.price.get_value()),
            int(self.capacity.get_value()),
            self.parent_window.user["id"],
        )
        if error:
            alert(self, "Не опубликовано", error)
            return
        self.close()
        self.on_saved(tour_id)


class ProductDialog(Adw.Window):
    def __init__(self, parent, product_id, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.product_id = product_id
        self.on_saved = on_saved
        self.ready = product_id is None
        product = db.get_product(product_id) if product_id else None
        if product_id and not product:
            return
        self.ready = True
        self.set_default_size(480, 620)
        self.set_title("Товар")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(
            Adw.WindowTitle(
                title="Новый товар" if product is None else product["name"],
                subtitle="Лавка",
            )
        )
        save = Gtk.Button(label="Сохранить")
        save.add_css_class("suggested-action")
        save.connect("clicked", lambda *_: self._save())
        header.pack_end(save)
        toolbar.add_top_bar(header)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_start(16)
        form.set_margin_end(16)
        form.set_margin_top(12)
        form.set_margin_bottom(16)
        group = Adw.PreferencesGroup(title="Карточка")
        self.name = Adw.EntryRow(title="Название")
        group.add(self.name)
        form.append(group)
        form.append(field_label("Описание"))
        self.description, desc_scroll = text_view(100)
        form.append(desc_scroll)
        self.category = LabeledDrop(list(db.PRODUCT_CATEGORY_RU.items()))
        self.price = int_spin(1, 500_000, 500, 10)
        self.stock = int_spin(0, 10_000, 10)
        self.active = Adw.SwitchRow(title="Показывать в лавке", active=True)
        picks = Gtk.Box(spacing=12)
        for caption, widget in (
            ("Категория", self.category),
            ("Цена, ₽", self.price),
            ("Остаток", self.stock),
        ):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            picks.append(box)
        form.append(picks)
        form.append(self.active)
        toolbar.set_content(scrolled(form))
        self.set_content(toolbar)
        if product:
            self.name.set_text(product["name"])
            self.description.get_buffer().set_text(product["description"])
            self.category.set_value(product["category"])
            self.price.set_value(product["price"])
            self.stock.set_value(product["stock"])
            self.active.set_active(bool(product["is_active"]))

    def _save(self):
        fields = {
            "name": self.name.get_text(),
            "description": text_of(self.description),
            "category": self.category.value(),
            "price": int(self.price.get_value()),
            "stock": int(self.stock.get_value()),
            "is_active": self.active.get_active(),
        }
        if self.product_id is None:
            product_id, error = db.create_product(
                self.parent_window.user["id"],
                fields["name"],
                fields["description"],
                fields["category"],
                fields["price"],
                fields["stock"],
            )
            ok, message = (error is None), (error or "Товар добавлен")
            saved_id = product_id
        else:
            ok, message = db.update_product(self.product_id, self.parent_window.user["id"], **fields)
            saved_id = self.product_id
        if not ok:
            alert(self, "Не сохранено", message)
            return
        self.close()
        self.on_saved(saved_id, message)


class BuyDialog(Adw.Window):
    def __init__(self, parent, product_id, on_saved):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.on_saved = on_saved
        self.ready = False
        self.product = db.get_product(product_id)
        if not self.product or not self.product["is_active"] or self.product["stock"] <= 0:
            return
        self.ready = True
        self.set_default_size(420, 320)
        self.set_title("Заказ")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title=self.product["name"], subtitle=self.product["producer_name"]))
        toolbar.add_top_bar(header)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(12)
        box.set_margin_bottom(16)
        self.people = int_spin(1, min(20, int(self.product["stock"])), 1)
        self.total = Gtk.Label(xalign=0)
        self.total.add_css_class("title-2")
        self.people.connect("value-changed", lambda *_: self._sum())
        box.append(Gtk.Label(label=self.product["description"] or "Без описания", xalign=0, wrap=True))
        box.append(field_label(f"Сколько штук, на складе {self.product['stock']}"))
        box.append(self.people)
        box.append(self.total)
        button = Gtk.Button(label="Оформить заказ")
        button.add_css_class("suggested-action")
        button.connect("clicked", lambda *_: self._buy())
        box.append(button)
        toolbar.set_content(box)
        self.set_content(toolbar)
        self._sum()

    def _sum(self):
        qty = int(self.people.get_value())
        self.total.set_text(money(self.product["price"] * qty))

    def _buy(self):
        order_id, error = db.create_order(
            self.parent_window.user["id"], self.product["id"], int(self.people.get_value())
        )
        if error:
            alert(self, "Заказ не оформлен", error)
            return
        self.close()
        self.on_saved(order_id)


class OrderDialog(Adw.Window):
    def __init__(self, parent, order_id, on_changed):
        super().__init__(transient_for=parent, modal=True, destroy_with_parent=True)
        self.parent_window = parent
        self.order_id = order_id
        self.on_changed = on_changed
        self.ready = False
        order = db.get_order(order_id)
        user = parent.user
        if not order:
            return
        if user["role"] != "admin" and user["id"] not in (order["tourist_id"], order["producer_id"]):
            return
        self._build(order)
        self.ready = True
        self.reload()

    def _build(self, order):
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.heading = Adw.WindowTitle(title=f"Заказ №{order['id']}", subtitle="")
        header.set_title_widget(self.heading)
        toolbar.add_top_bar(header)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_start(16)
        body.set_margin_end(16)
        body.set_margin_top(12)
        body.set_margin_bottom(16)
        self.meta = Gtk.Label(xalign=0, wrap=True, selectable=True)
        body.append(self.meta)
        self.actions = Gtk.Box(spacing=8)
        self.action_buttons = {}
        for status, caption in (
            ("accepted", "Принять"),
            ("ready", "Готов к выдаче"),
            ("completed", "Выдан"),
            ("cancelled", "Отменить"),
        ):
            button = Gtk.Button(label=caption)
            if status == "completed":
                button.add_css_class("suggested-action")
            button.connect("clicked", lambda _, value=status: self._status(value))
            self.action_buttons[status] = button
            self.actions.append(button)
        body.append(self.actions)
        self.reviews = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        body.append(self.reviews)
        self.history_group = Adw.PreferencesGroup(title="Журнал")
        self.history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.history_group.add(self.history_box)
        body.append(self.history_group)
        toolbar.set_content(scrolled(body))
        self.set_content(toolbar)

    def reload(self):
        order = db.get_order(self.order_id)
        if not order:
            self.close()
            return
        user = self.parent_window.user
        self.heading.set_subtitle(db.ORDER_STATUS_RU[order["status"]])
        self.meta.set_text(
            f"{order['items_label'] or '—'}\n"
            f"Сумма: {money(order['total'])}\n"
            f"Турист: {order['tourist_name']} · Производитель: {order['producer_name']}\n"
            f"Создан: {order['created_at']}"
        )
        is_producer = user["role"] == "producer" and user["id"] == order["producer_id"]
        is_admin = user["role"] == "admin"
        is_tourist = user["id"] == order["tourist_id"]
        allowed = set(db.ORDER_FLOW[order["status"]])
        for status, button in self.action_buttons.items():
            visible = status in allowed
            if status == "cancelled":
                visible = visible and (is_admin or is_producer or (is_tourist and order["status"] == "new"))
            else:
                visible = visible and (is_admin or is_producer)
            button.set_visible(visible)
        self.actions.set_visible(any(button.get_visible() for button in self.action_buttons.values()))
        clear_box(self.reviews)
        if order["status"] == "completed":
            for item in order["items"]:
                box = ReviewBox(self.parent_window, "product", item["product_id"], f"Оценка: {item['name']}")
                box.reload()
                self.reviews.append(box)
        clear_box(self.history_box)
        events = db.list_history("order", self.order_id)
        if not events:
            empty = Gtk.Label(label="Пока пусто", xalign=0)
            empty.add_css_class("dim-label")
            self.history_box.append(empty)
        for event in events:
            who = event["user_name"] or "система"
            self.history_box.append(
                Adw.ActionRow(title=event["action"], subtitle=f"{event['created_at']} · {who}")
            )

    def _status(self, status):
        def apply():
            ok, message = db.set_order_status(self.order_id, status, self.parent_window.user["id"])
            if not ok:
                alert(self, "Не удалось", message)
                return
            self.reload()
            self.on_changed()
            self.parent_window.notify(message)

        if status == "cancelled":
            confirm(self, "Отменить заказ?", "Товар вернётся на склад.", apply)
            return
        apply()


def present_ready(dialog, window, missing):
    if not dialog.ready:
        dialog.close()
        alert(window, missing)
        return
    dialog.present()


class ListPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.window = window
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self._ready = False

    def _bar(self, *widgets):
        bar = Gtk.Box(spacing=8)
        bar.add_css_class("th-toolbar")
        for widget in widgets:
            bar.append(widget)
        self.append(bar)
        return bar

    def _finish_table(self, headers, on_activate=None):
        self.list = Gtk.ListBox()
        self.list.add_css_class("th-strips")
        self.list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list.set_activate_on_single_click(False)
        if on_activate is not None:
            self.list.connect("row-activated", lambda *_: on_activate())
        self.append(scrolled(self.list))
        self.count = Gtk.Label(xalign=0)
        self.count.add_css_class("th-meta")
        self.append(self.count)

    def _selected(self):
        row = self.list.get_selected_row()
        if row is None:
            return None
        return row.values[0]

    def _fill(self, rows, keep=None):
        clear_box(self.list)
        chosen = None
        for values in rows:
            row = RouteStrip(values)
            self.list.append(row)
            if keep is not None and values[0] == keep:
                chosen = row
        if chosen is None:
            chosen = self.list.get_row_at_index(0)
        if chosen is not None:
            self.list.select_row(chosen)
        self.count.set_text(f"{len(rows)} в списке" if rows else "Пока пусто")


class OverviewPage(Gtk.ScrolledWindow):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(8)
        box.set_margin_bottom(20)
        self.stats = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=True,
            max_children_per_line=3,
            min_children_per_line=2,
            column_spacing=10,
            row_spacing=10,
        )
        box.append(self.stats)
        about = Gtk.Label(
            xalign=0,
            wrap=True,
            label=(
                "Заявка уходит гиду сама: сначала совпавшее направление, потом регион, "
                "потом оценка туристов и короткая очередь. На карточке маршрута видна лавка этого края."
            ),
        )
        about.add_css_class("th-meta")
        box.append(about)
        distribute = Gtk.Button(label="Разослать свободные заявки")
        distribute.add_css_class("suggested-action")
        distribute.add_css_class("pill")
        distribute.set_halign(Gtk.Align.START)
        distribute.connect("clicked", lambda *_: self._distribute())
        box.append(distribute)
        heading = Gtk.Label(label="Кто ведёт маршруты", xalign=0)
        heading.add_css_class("th-strip-title")
        box.append(heading)
        self.people = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.append(self.people)
        self.set_child(box)
        self._cards = {}

    def reload(self):
        data = db.stats()
        captions = (
            ("guides", "Гиды в пути"),
            ("unassigned", "Заявки без гида"),
            ("open_tours", "Маршруты"),
            ("active_bookings", "Брони"),
            ("new_orders", "Новые заказы"),
            ("products", "Товары лавки"),
        )
        if not self._cards:
            for key, caption in captions:
                card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                card.add_css_class("th-stat")
                value = Gtk.Label(label="0", xalign=0)
                value.add_css_class("th-stat-num")
                title = Gtk.Label(label=caption.upper(), xalign=0)
                title.add_css_class("th-kicker")
                title.add_css_class("th-kicker-ink")
                card.append(value)
                card.append(title)
                self.stats.append(card)
                self._cards[key] = value
        for key, _caption in captions:
            self._cards[key].set_text(str(data[key]))
        clear_box(self.people)
        guides = db.list_guides(only_active=False)
        if not guides:
            empty = Gtk.Label(label="Активных гидов нет", xalign=0)
            empty.add_css_class("th-meta")
            self.people.append(empty)
            return
        for guide in guides:
            load = db.active_load(guide["id"])
            state = "в пути" if guide["is_active"] else "пауза"
            score = rating_text(guide["review_count"], guide["review_avg"])
            row = Gtk.Box(spacing=12)
            row.add_css_class("th-person")
            initials = "".join(part[0] for part in guide["full_name"].split()[:2])
            bubble = Gtk.Label(label=initials)
            bubble.add_css_class("th-stamp")
            bubble.add_css_class(REGION_TONE.get(guide["region"], "th-pine"))
            bubble.set_valign(Gtk.Align.CENTER)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
            name = Gtk.Label(label=guide["full_name"], xalign=0)
            name.add_css_class("th-strip-title")
            meta = Gtk.Label(
                label=f"{db.THEME_RU[guide['specialty']]}  ·  {db.REGION_RU[guide['region']]}  ·  {state}  ·  {score}",
                xalign=0,
                wrap=True,
            )
            meta.add_css_class("th-meta")
            text.append(name)
            text.append(meta)
            mark = Gtk.Label(label=f"{load} заявки")
            mark.add_css_class("th-pill")
            mark.set_valign(Gtk.Align.CENTER)
            row.append(bubble)
            row.append(text)
            row.append(mark)
            self.people.append(row)

    def _distribute(self):
        assigned, lines = matching.distribute_pending(self.window.user["id"])
        self.reload()
        if not lines:
            self.window.notify("Ожидающих заявок нет")
            return
        alert(self.window, f"Назначено: {assigned}", "\n".join(lines))


class UsersPage(ListPage):
    def __init__(self, window):
        super().__init__(window)
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по имени или логину")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        add = Gtk.Button(label="Добавить")
        add.add_css_class("suggested-action")
        add.connect("clicked", lambda *_: UserDialog(self.window, None, self._saved).present())
        edit = Gtk.Button(label="Изменить")
        edit.connect("clicked", lambda *_: self._edit())
        toggle = Gtk.Button(label="Вкл / выкл")
        toggle.connect("clicked", lambda *_: self._toggle())
        self._bar(self.search, add, edit, toggle)
        self._finish_table((), on_activate=self._edit)
        self._ready = True

    def reload(self, keep=None):
        if not self._ready:
            return
        query = self.search.get_text().strip().casefold()
        ratings = {guide["id"]: guide for guide in db.list_guides(only_active=False)}
        rows = []
        for user in db.list_users():
            blob = f"{user['login']} {user['full_name']}".casefold()
            if query and query not in blob:
                continue
            guide = ratings.get(user["id"])
            score = "—"
            theme = "—"
            if user["role"] == "guide":
                theme = db.THEME_RU[user["specialty"]]
                if guide:
                    score = rating_text(guide["review_count"], guide["review_avg"])
            rows.append(
                (
                    user["id"],
                    user["login"],
                    user["full_name"],
                    db.ROLE_RU[user["role"]],
                    db.REGION_RU[user["region"]],
                    theme,
                    score,
                    "активен" if user["is_active"] else "отключён",
                )
            )
        self._fill(rows, keep)

    def _edit(self):
        user_id = self._selected()
        if user_id is None:
            alert(self.window, "Выберите пользователя")
            return
        UserDialog(self.window, user_id, self._saved).present()

    def _saved(self, user_id, message):
        if user_id == self.window.user["id"]:
            self.window.refresh_session()
            return
        self.reload(keep=user_id)
        self.window.notify(message)

    def _toggle(self):
        user_id = self._selected()
        if user_id is None:
            alert(self.window, "Выберите пользователя")
            return
        record = db.get_user(user_id)
        if user_id == self.window.user["id"] and record["is_active"]:
            alert(self.window, "Нельзя отключить свою учётную запись")
            return
        ok, message = db.update_user(user_id, is_active=0 if record["is_active"] else 1)
        if not ok:
            alert(self.window, "Не удалось", message)
            return
        self.reload(keep=user_id)
        self.window.notify(message)


class RequestsPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        filters = [
            ("all", "Все"),
            ("new", "Новые"),
            ("assigned", "Назначенные"),
            ("done", "Завершённые"),
            ("cancelled", "Отменённые"),
        ]
        if scope == "all":
            filters.append(("free", "Без гида"))
        self.filter = LabeledDrop(filters)
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по теме, туристу, гиду")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        open_btn = Gtk.Button(label="Открыть")
        open_btn.connect("clicked", lambda *_: self._open())
        widgets = [self.filter, self.search, open_btn]
        if scope == "free":
            take = Gtk.Button(label="Взять")
            take.add_css_class("suggested-action")
            take.connect("clicked", lambda *_: self._take())
            widgets.append(take)
        self._bar(*widgets)
        self._finish_table((), on_activate=self._open)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        user = self.window.user
        if self.scope == "mine":
            rows = db.list_requests(tourist_id=user["id"])
        elif self.scope == "queue":
            rows = db.list_requests(guide_id=user["id"])
        elif self.scope == "free":
            rows = [
                request
                for request in db.list_requests(status="new")
                if request["guide_id"] is None
            ]
        else:
            rows = db.list_requests()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        shown = []
        for request in rows:
            if mode == "free" and request["guide_id"] is not None:
                continue
            if mode not in ("all", "free") and request["status"] != mode:
                continue
            blob = " ".join(
                (request["title"], request["tourist_name"] or "", request["guide_name"] or "")
            ).casefold()
            if query and query not in blob:
                continue
            shown.append(
                (
                    request["id"],
                    request["title"],
                    db.THEME_RU[request["theme"]],
                    db.REGION_RU[request["region"]],
                    db.PRIORITY_RU[request["priority"]],
                    request["tourist_name"],
                    request["guide_name"] or "без гида",
                    db.REQUEST_STATUS_RU[request["status"]],
                )
            )
        self._fill(shown)

    def _open(self):
        request_id = self._selected()
        if request_id is None:
            alert(self.window, "Выберите заявку")
            return
        present_ready(RequestDialog(self.window, request_id, self.reload), self.window, "Заявка недоступна")

    def _take(self):
        request_id = self._selected()
        if request_id is None:
            alert(self.window, "Выберите заявку")
            return
        ok, message = db.take_request(request_id, self.window.user["id"])
        if not ok:
            alert(self.window, "Не удалось", message)
            return
        self.window.notify(message)
        self.reload()


class NewRequestPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        clamp = Adw.Clamp(maximum_size=680, tightening_threshold=680)
        clamp.set_margin_top(12)
        clamp.set_margin_bottom(12)
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form.set_margin_start(16)
        form.set_margin_end(16)
        intro = Gtk.Label(
            xalign=0,
            wrap=True,
            label="После отправки заявка сразу уходит свободному гиду. В ответе будет видно, почему выбран он.",
        )
        intro.add_css_class("dim-label")
        form.append(intro)
        group = Adw.PreferencesGroup(title="Заявка гиду")
        self.title_row = Adw.EntryRow(title="Тема")
        self.date_row = Adw.EntryRow(title="Желаемая дата, можно пусто")
        group.add(self.title_row)
        group.add(self.date_row)
        form.append(group)
        form.append(field_label("Что хочется увидеть"))
        self.description, desc_scroll = text_view(120)
        form.append(desc_scroll)
        self.theme = LabeledDrop(list(db.THEME_RU.items()))
        self.region = LabeledDrop(list(db.REGION_RU.items()))
        self.priority = LabeledDrop(list(db.PRIORITY_RU.items()))
        self.priority.set_value("normal")
        self.people = int_spin(1, 20, 2)
        form.append(self._pair("Направление", self.theme, "Регион", self.region))
        form.append(self._pair("Приоритет", self.priority, "Людей", self.people))
        self.error = Gtk.Label(xalign=0, wrap=True, visible=False)
        self.error.add_css_class("error-text")
        form.append(self.error)
        self.submit = Gtk.Button(label="Отправить и подобрать гида")
        self.submit.add_css_class("suggested-action")
        self.submit.add_css_class("pill")
        self.submit.connect("clicked", lambda *_: self._submit())
        form.append(self.submit)
        clamp.set_child(form)
        self.append(scrolled(clamp))

    def reload(self):
        return

    def _pair(self, left_caption, left, right_caption, right):
        row = Gtk.Box(spacing=12)
        for caption, widget in ((left_caption, left), (right_caption, right)):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
            box.append(field_label(caption))
            box.append(widget)
            row.append(box)
        return row

    def _submit(self):
        self.submit.set_sensitive(False)
        try:
            request_id, error = db.create_request(
                self.title_row.get_text(),
                text_of(self.description),
                self.theme.value(),
                self.region.value(),
                int(self.people.get_value()),
                self.date_row.get_text(),
                self.priority.value(),
                self.window.user["id"],
            )
            if error:
                self.error.set_text(error)
                self.error.set_visible(True)
                return
            guide, debug = matching.distribute(request_id, self.window.user["id"])
            self.error.set_visible(False)
            self.title_row.set_text("")
            self.date_row.set_text("")
            self.description.get_buffer().set_text("")
            heading = f"Заявка №{request_id}"
            heading += f" → {guide['full_name']}" if guide else " ждёт гида"
            alert(self.window, heading, "\n".join(debug))
            self.window.notify(heading)
        finally:
            self.submit.set_sensitive(True)


class ToursPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        if scope == "catalog":
            filters = [
                ("actual", "Актуальные"),
                ("open", "Есть места"),
                ("full", "Мест нет"),
                ("completed", "Завершённые"),
                ("all", "Все"),
            ]
        else:
            filters = [
                ("all", "Все"),
                ("open", "Есть места"),
                ("full", "Мест нет"),
                ("completed", "Завершённые"),
                ("cancelled", "Отменённые"),
            ]
        self.filter = LabeledDrop(filters)
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по названию или гиду")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        open_btn = Gtk.Button(label="Открыть")
        open_btn.connect("clicked", lambda *_: self._open())
        widgets = [self.filter, self.search, open_btn]
        if scope == "mine":
            create = Gtk.Button(label="Новая экскурсия")
            create.add_css_class("suggested-action")
            create.connect("clicked", lambda *_: TourCreateDialog(self.window, self._created).present())
            widgets.append(create)
        self._bar(*widgets)
        self.board = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.SINGLE,
            max_children_per_line=2,
            min_children_per_line=1,
            column_spacing=8,
            row_spacing=8,
            homogeneous=True,
        )
        self.board.add_css_class("th-board")
        self.board.set_activate_on_single_click(False)
        self.board.connect("child-activated", lambda *_: self._open())
        self.append(scrolled(self.board))
        self.count = Gtk.Label(xalign=0)
        self.count.add_css_class("th-meta")
        self.append(self.count)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        if self.scope == "mine":
            rows = db.list_tours(guide_id=self.window.user["id"])
        else:
            rows = db.list_tours()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        clear_box(self.board)
        shown = 0
        for tour in rows:
            if mode == "actual" and tour["status"] not in ("open", "full"):
                continue
            if mode not in ("all", "actual") and tour["status"] != mode:
                continue
            blob = f"{tour['title']} {tour['guide_name']}".casefold()
            if query and query not in blob:
                continue
            self.board.append(self._card(tour))
            shown += 1
        first = self.board.get_child_at_index(0)
        if first is not None:
            self.board.select_child(first)
        self.count.set_text(f"{shown} маршрутов" if shown else "Маршрутов нет")

    def _card(self, tour):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("th-card")
        card.tour_id = tour["id"]
        band = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        band.add_css_class("th-band")
        band.add_css_class(REGION_TONE.get(tour["region"], "th-pine"))
        place = Gtk.Label(label=db.REGION_RU[tour["region"]].upper(), xalign=0)
        place.add_css_class("th-kicker")
        title = Gtk.Label(label=tour["title"], xalign=0, wrap=True)
        title.add_css_class("th-card-title")
        band.append(place)
        band.append(title)
        card.append(band)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        body.add_css_class("th-card-body")
        seats = "запись закрыта"
        if tour["status"] in ("open", "full"):
            seats = f"свободно {tour['seats_left']} из {tour['capacity']}"
        meta = Gtk.Label(
            label=f"{tour['tour_date']}  ·  {db.THEME_RU[tour['theme']]}  ·  {tour['duration_hours']} ч",
            xalign=0,
            wrap=True,
        )
        meta.add_css_class("th-meta")
        guide = Gtk.Label(label=tour["guide_name"], xalign=0)
        price = Gtk.Label(label=money(tour["price"]), xalign=0)
        price.add_css_class("th-price")
        foot = Gtk.Box(spacing=8)
        status = Gtk.Label(label=db.TOUR_STATUS_RU[tour["status"]])
        status.add_css_class("th-pill")
        status.set_halign(Gtk.Align.START)
        seats_label = Gtk.Label(label=seats, xalign=0, hexpand=True)
        seats_label.add_css_class("th-meta")
        foot.append(status)
        foot.append(seats_label)
        body.append(meta)
        body.append(guide)
        body.append(price)
        body.append(foot)
        card.append(body)
        return card

    def _open(self):
        selected = self.board.get_selected_children()
        if not selected:
            alert(self.window, "Выберите экскурсию")
            return
        tour_id = selected[0].get_child().tour_id
        present_ready(TourDialog(self.window, tour_id, self.reload), self.window, "Экскурсия не найдена")

    def _created(self, tour_id):
        self.reload()
        self.window.notify(f"Экскурсия №{tour_id} опубликована")


class BookingsPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        self.filter = LabeledDrop(
            (
                ("all", "Все"),
                ("confirmed", "Действующие"),
                ("completed", "Завершённые"),
                ("cancelled", "Снятые"),
            )
        )
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по экскурсии или имени")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        open_btn = Gtk.Button(label="Открыть экскурсию")
        open_btn.connect("clicked", lambda *_: self._open())
        cancel = Gtk.Button(label="Снять бронь")
        cancel.connect("clicked", lambda *_: self._cancel())
        self._bar(self.filter, self.search, open_btn, cancel)
        self._finish_table((), on_activate=self._open)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        user = self.window.user
        if self.scope == "mine":
            rows = db.list_bookings(tourist_id=user["id"])
        elif self.scope == "guide":
            rows = db.list_bookings(guide_id=user["id"])
        else:
            rows = db.list_bookings()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        shown = []
        for booking in rows:
            if mode != "all" and booking["status"] != mode:
                continue
            blob = f"{booking['tour_title']} {booking['tourist_name']} {booking['guide_name']}".casefold()
            if query and query not in blob:
                continue
            shown.append(
                (
                    booking["id"],
                    booking["tour_title"],
                    booking["tour_date"],
                    booking["tourist_name"],
                    booking["guide_name"],
                    booking["people"],
                    money(booking["price"] * booking["people"]),
                    db.BOOKING_STATUS_RU[booking["status"]],
                )
            )
        self._fill(shown)

    def _open(self):
        booking_id = self._selected()
        if booking_id is None:
            alert(self.window, "Выберите бронь")
            return
        booking = db.get_booking(booking_id)
        present_ready(TourDialog(self.window, booking["tour_id"], self.reload), self.window, "Экскурсия не найдена")

    def _cancel(self):
        booking_id = self._selected()
        if booking_id is None:
            alert(self.window, "Выберите бронь")
            return

        def apply():
            ok, message = db.cancel_booking(booking_id, self.window.user["id"])
            if not ok:
                alert(self.window, "Не удалось", message)
                return
            self.window.notify(message)
            self.reload()

        confirm(self.window, "Снять бронь?", "Место вернётся в экскурсию.", apply)


class ProductsPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        self.filter = LabeledDrop([("all", "Все"), *list(db.PRODUCT_CATEGORY_RU.items())])
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по названию или производителю")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        widgets = [self.filter, self.search]
        if scope == "market":
            buy = Gtk.Button(label="Заказать")
            buy.add_css_class("suggested-action")
            buy.connect("clicked", lambda *_: self._buy())
            widgets.append(buy)
        else:
            if scope == "mine":
                add = Gtk.Button(label="Добавить")
                add.add_css_class("suggested-action")
                add.connect("clicked", lambda *_: self._create())
                widgets.append(add)
            edit = Gtk.Button(label="Изменить")
            edit.connect("clicked", lambda *_: self._edit())
            widgets.append(edit)
        self._bar(*widgets)
        self.use_cards = scope == "market"
        if self.use_cards:
            self.board = Gtk.FlowBox(
                selection_mode=Gtk.SelectionMode.SINGLE,
                max_children_per_line=3,
                min_children_per_line=1,
                column_spacing=8,
                row_spacing=8,
                homogeneous=True,
            )
            self.board.add_css_class("th-board")
            self.board.set_activate_on_single_click(False)
            self.board.connect("child-activated", lambda *_: self._buy())
            self.append(scrolled(self.board))
            self.count = Gtk.Label(xalign=0)
            self.count.add_css_class("th-meta")
            self.append(self.count)
        else:
            self._finish_table((), on_activate=self._edit)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        if self.scope == "market":
            rows = db.list_products(only_market=True)
        elif self.scope == "mine":
            rows = db.list_products(producer_id=self.window.user["id"])
        else:
            rows = db.list_products()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        shown = []
        for product in rows:
            if mode != "all" and product["category"] != mode:
                continue
            blob = f"{product['name']} {product['producer_name']}".casefold()
            if query and query not in blob:
                continue
            shown.append(product)
        if self.use_cards:
            clear_box(self.board)
            for product in shown:
                self.board.append(self._card(product))
            first = self.board.get_child_at_index(0)
            if first is not None:
                self.board.select_child(first)
            self.count.set_text(f"{len(shown)} товаров" if shown else "Лавка пуста")
            return
        self._fill(
            [
                (
                    product["id"],
                    product["name"],
                    db.PRODUCT_CATEGORY_RU[product["category"]],
                    money(product["price"]),
                    f"остаток {product['stock']}",
                    db.REGION_RU[product["region"]],
                    product["producer_name"],
                    "в лавке" if product["is_active"] else "скрыт",
                )
                for product in shown
            ]
        )

    def _card(self, product):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("th-card")
        card.product_id = product["id"]
        band = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        band.add_css_class("th-band")
        band.add_css_class(REGION_TONE.get(product["region"], "th-pine"))
        place = Gtk.Label(label=db.REGION_RU[product["region"]].upper(), xalign=0)
        place.add_css_class("th-kicker")
        title = Gtk.Label(label=product["name"], xalign=0, wrap=True)
        title.add_css_class("th-card-title")
        band.append(place)
        band.append(title)
        card.append(band)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        body.add_css_class("th-card-body")
        kind = Gtk.Label(label=db.PRODUCT_CATEGORY_RU[product["category"]], xalign=0)
        kind.add_css_class("th-meta")
        who = Gtk.Label(label=product["producer_name"], xalign=0)
        price = Gtk.Label(label=money(product["price"]), xalign=0)
        price.add_css_class("th-price")
        stock = Gtk.Label(
            label="нет в наличии" if product["stock"] <= 0 else f"на складе {product['stock']}",
            xalign=0,
        )
        stock.add_css_class("th-meta")
        body.append(kind)
        body.append(who)
        body.append(price)
        body.append(stock)
        card.append(body)
        return card

    def _activate(self):
        if self.scope == "market":
            self._buy()
        else:
            self._edit()

    def _selected_product(self):
        if self.use_cards:
            selected = self.board.get_selected_children()
            if not selected:
                alert(self.window, "Выберите товар")
                return None
            return selected[0].get_child().product_id
        product_id = self._selected()
        if product_id is None:
            alert(self.window, "Выберите товар")
            return None
        return product_id

    def _buy(self):
        product_id = self._selected_product()
        if product_id is None:
            return
        present_ready(
            BuyDialog(self.window, product_id, self._bought),
            self.window,
            "Этого товара сейчас нет в наличии",
        )

    def _bought(self, order_id):
        self.reload()
        self.window.notify(f"Заказ №{order_id} оформлен")

    def _create(self):
        dialog = ProductDialog(self.window, None, self._saved)
        if dialog.ready:
            dialog.present()

    def _edit(self):
        product_id = self._selected_product()
        if product_id is None:
            return
        present_ready(ProductDialog(self.window, product_id, self._saved), self.window, "Товар не найден")

    def _saved(self, product_id, message):
        self.reload()
        self.window.notify(message)


class OrdersPage(ListPage):
    def __init__(self, window, scope):
        super().__init__(window)
        self.scope = scope
        self.filter = LabeledDrop(
            (
                ("all", "Все"),
                ("new", "Новые"),
                ("accepted", "Принятые"),
                ("ready", "Готовы"),
                ("completed", "Выданные"),
                ("cancelled", "Отменённые"),
            )
        )
        self.filter.connect("notify::selected", lambda *_: self.reload())
        self.search = Gtk.SearchEntry(placeholder_text="Поиск по товару, туристу, производителю")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", lambda *_: self.reload())
        open_btn = Gtk.Button(label="Открыть")
        open_btn.connect("clicked", lambda *_: self._open())
        self._bar(self.filter, self.search, open_btn)
        self._finish_table((), on_activate=self._open)
        self._ready = True

    def reload(self):
        if not self._ready:
            return
        user = self.window.user
        if self.scope == "mine":
            rows = db.list_orders(tourist_id=user["id"])
        elif self.scope == "incoming":
            rows = db.list_orders(producer_id=user["id"])
        else:
            rows = db.list_orders()
        mode = self.filter.value()
        query = self.search.get_text().strip().casefold()
        shown = []
        for order in rows:
            if mode != "all" and order["status"] != mode:
                continue
            blob = f"{order['items_label'] or ''} {order['tourist_name']} {order['producer_name']}".casefold()
            if query and query not in blob:
                continue
            shown.append(
                (
                    order["id"],
                    order["items_label"] or "—",
                    money(order["total"]),
                    order["tourist_name"],
                    order["producer_name"],
                    order["created_at"],
                    db.ORDER_STATUS_RU[order["status"]],
                )
            )
        self._fill(shown)

    def _open(self):
        order_id = self._selected()
        if order_id is None:
            alert(self.window, "Выберите заказ")
            return
        present_ready(OrderDialog(self.window, order_id, self.reload), self.window, "Заказ недоступен")


class ShellView(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.window = window
        self._switching = False
        self._navs = []
        mast = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mast.add_css_class("th-mast")
        top = Gtk.Box(spacing=12)
        brand_row = Gtk.Box(spacing=10)
        brand_row.append(logo_image(48))
        brand = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        kicker = Gtk.Label(label="В ПУТИ", xalign=0)
        kicker.add_css_class("th-kicker")
        word = Gtk.Label(label="TravelHub", xalign=0)
        word.add_css_class("th-wordmark")
        brand.append(kicker)
        brand.append(word)
        brand.set_valign(Gtk.Align.CENTER)
        brand_row.append(brand)
        brand_row.set_valign(Gtk.Align.CENTER)
        top.append(brand_row)

        identity = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        identity.set_hexpand(True)
        identity.set_halign(Gtk.Align.END)
        identity.set_valign(Gtk.Align.CENTER)
        self.name_label = Gtk.Label(xalign=1, ellipsize=Pango.EllipsizeMode.END)
        self.name_label.add_css_class("th-strip-title")
        self.meta_label = Gtk.Label(xalign=1)
        self.meta_label.add_css_class("th-kicker")
        logout = Gtk.Button(label="Выйти")
        logout.add_css_class("th-quiet")
        logout.set_halign(Gtk.Align.END)
        logout.connect("clicked", lambda *_: window.show_login())
        identity.append(self.name_label)
        identity.append(self.meta_label)
        identity.append(logout)
        top.append(identity)
        mast.append(top)

        self.nav_box = Adw.WrapBox()
        self.nav_box.set_child_spacing(4)
        self.nav_box.set_line_spacing(4)
        mast.append(self.nav_box)
        self.append(mast)
        self.sync_identity()

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        body.add_css_class("th-paper")
        body.set_vexpand(True)
        intro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        intro.set_margin_start(22)
        intro.set_margin_end(22)
        intro.set_margin_top(18)
        self.kicker = Gtk.Label(xalign=0)
        self.kicker.add_css_class("th-kicker")
        self.kicker.add_css_class("th-kicker-ink")
        self.banner = Gtk.Label(xalign=0)
        self.banner.add_css_class("th-display")
        intro.append(self.kicker)
        intro.append(self.banner)
        body.append(intro)
        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        body.append(self.stack)
        self.append(body)

        self.pages = {}
        menu = self._menu(window.user["role"])
        for key, title, hint, factory in menu:
            page = factory()
            self.pages[key] = page
            self.stack.add_named(page, key)
            button = Gtk.ToggleButton(label=title)
            button.add_css_class("flat")
            button.add_css_class("th-nav")
            button.set_can_shrink(False)
            button.connect("toggled", self._on_nav, key, title, hint)
            self._navs.append(button)
            self.nav_box.append(button)
        self._navs[0].set_active(True)

    def _menu(self, role):
        window = self.window
        if role == "admin":
            return (
                ("overview", "Сводка", "КАК ИДУТ МАРШРУТЫ", lambda: OverviewPage(window)),
                ("users", "Люди", "ТУРИСТЫ, ГИДЫ И МАСТЕРА", lambda: UsersPage(window)),
                ("requests", "Заявки", "КОМУ ДОСТАНЕТСЯ МАРШРУТ", lambda: RequestsPage(window, "all")),
                ("tours", "Маршруты", "ВСЕ ВЫЕЗДЫ", lambda: ToursPage(window, "all")),
                ("bookings", "Брони", "КТО УЖЕ В ПУТИ", lambda: BookingsPage(window, "all")),
                ("orders", "Заказы", "ЛАВКА", lambda: OrdersPage(window, "all")),
                ("products", "Лавка", "ЧТО ВЕЗУТ С МЕСТА", lambda: ProductsPage(window, "all")),
            )
        if role == "guide":
            return (
                ("free", "Свободные", "ЗАЯВКИ БЕЗ ГИДА", lambda: RequestsPage(window, "free")),
                ("queue", "Мои заявки", "ТО, ЧТО ВЫ ВЕДЁТЕ", lambda: RequestsPage(window, "queue")),
                ("tours", "Маршруты", "ВАШЕ РАСПИСАНИЕ", lambda: ToursPage(window, "mine")),
                ("bookings", "Брони", "КТО ЕДЕТ С ВАМИ", lambda: BookingsPage(window, "guide")),
            )
        if role == "producer":
            return (
                ("products", "Лавка", "ОСТАТКИ И ЦЕНЫ", lambda: ProductsPage(window, "mine")),
                ("orders", "Заказы", "КОМУ СОБРАТЬ", lambda: OrdersPage(window, "incoming")),
            )
        return (
            ("tours", "Маршруты", "КУДА ПОЕХАТЬ", lambda: ToursPage(window, "catalog")),
            ("bookings", "Брони", "УЖЕ ВЫБРАННЫЕ ДНИ", lambda: BookingsPage(window, "mine")),
            ("new", "Заявка", "ГИД ПОДБЕРЁТСЯ САМ", lambda: NewRequestPage(window)),
            ("requests", "Мои заявки", "ПЕРЕПИСКА С ГИДОМ", lambda: RequestsPage(window, "mine")),
            ("market", "Лавка", "ЕДА И РЕМЕСЛО КРАЯ", lambda: ProductsPage(window, "market")),
            ("orders", "Заказы", "ЧТО УЖЕ СОБРАНО", lambda: OrdersPage(window, "mine")),
        )

    def _on_nav(self, button, key, title, hint):
        if self._switching:
            return
        if not button.get_active():
            if not any(item.get_active() for item in self._navs):
                self._switching = True
                button.set_active(True)
                self._switching = False
            return
        self._switching = True
        for other in self._navs:
            if other is not button:
                other.set_active(False)
        self._switching = False
        self.banner.set_label(title)
        self.kicker.set_label(hint)
        self.stack.set_visible_child_name(key)
        page = self.pages.get(key)
        if page is not None:
            page.reload()

    def sync_identity(self):
        user = self.window.user
        self.name_label.set_text(user["full_name"])
        text = db.ROLE_RU[user["role"]].upper()
        if user["role"] in ("guide", "producer"):
            text = f"{text}  ·  {db.REGION_RU[user['region']].upper()}"
        self.meta_label.set_text(text)

    def reload_visible(self):
        page = self.stack.get_visible_child()
        if page is not None:
            page.reload()


class LoginView(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=True)
        self.window = window
        self._switching = False
        poster = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        poster.add_css_class("th-poster")
        poster.set_size_request(300, -1)
        poster.set_hexpand(True)
        poster.set_vexpand(True)
        poster_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, valign=Gtk.Align.CENTER, vexpand=True)
        mark = logo_image(88)
        mark.set_halign(Gtk.Align.START)
        poster_inner.append(mark)
        kicker = Gtk.Label(label="МАРШРУТЫ  ·  ГИДЫ  ·  ЛАВКА", xalign=0)
        kicker.add_css_class("th-kicker")
        title = Gtk.Label(label="TravelHub", xalign=0)
        title.add_css_class("th-poster-title")
        lead = Gtk.Label(
            label="Карелия, Алтай, Байкал, Золотое кольцо и Калининград — в одном окне на столе, не в браузере.",
            xalign=0,
            wrap=True,
        )
        poster_inner.append(kicker)
        poster_inner.append(title)
        poster_inner.append(lead)
        for stop in ("Карелия", "Алтай", "Байкал", "Золотое кольцо", "Калининград"):
            item = Gtk.Label(label=f"—   {stop}", xalign=0)
            poster_inner.append(item)
        poster.append(poster_inner)
        self.append(poster)

        form_side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        form_side.add_css_class("th-form")
        form_side.set_hexpand(True)
        form_side.set_vexpand(True)
        form_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, valign=Gtk.Align.CENTER, vexpand=True)
        hello = Gtk.Label(label="В ДОРОГУ", xalign=0)
        hello.add_css_class("th-kicker")
        hello.add_css_class("th-kicker-ink")
        self.form_title = Gtk.Label(label="С возвращением", xalign=0)
        self.form_title.add_css_class("th-display")
        form_inner.append(hello)
        form_inner.append(self.form_title)
        modes = Gtk.Box(spacing=6)
        self.mode_login = Gtk.ToggleButton(label="Вход")
        self.mode_reg = Gtk.ToggleButton(label="Я впервые")
        for button in (self.mode_login, self.mode_reg):
            button.add_css_class("flat")
            button.add_css_class("th-seg")
            modes.append(button)
        self.mode_login.connect("toggled", self._show_login_mode)
        self.mode_reg.connect("toggled", self._show_register_mode)
        form_inner.append(modes)
        self.stack = Gtk.Stack()
        self.stack.add_named(self._login_form(), "login")
        self.stack.add_named(self._register_form(), "register")
        form_inner.append(self.stack)
        form_side.append(form_inner)
        self.append(form_side)
        self.mode_login.set_active(True)

    def _login_form(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        group = Adw.PreferencesGroup()
        self.login = Adw.EntryRow(title="Логин")
        self.password = Adw.PasswordEntryRow(title="Пароль")
        self.login.connect("entry-activated", lambda *_: self.password.grab_focus())
        self.password.connect("entry-activated", lambda *_: self._login())
        group.add(self.login)
        group.add(self.password)
        box.append(group)
        self.login_error = Gtk.Label(xalign=0, wrap=True, visible=False)
        self.login_error.add_css_class("error-text")
        box.append(self.login_error)
        button = Gtk.Button(label="Войти")
        button.add_css_class("suggested-action")
        button.add_css_class("pill")
        button.connect("clicked", lambda *_: self._login())
        box.append(button)
        return box

    def _register_form(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        group = Adw.PreferencesGroup(description="Так появляется турист. Гида и мастера лавки назначает администратор.")
        self.reg_name = Adw.EntryRow(title="ФИО")
        self.reg_login = Adw.EntryRow(title="Логин")
        self.reg_password = Adw.PasswordEntryRow(title="Пароль")
        self.reg_repeat = Adw.PasswordEntryRow(title="Пароль ещё раз")
        self.reg_repeat.connect("entry-activated", lambda *_: self._register())
        group.add(self.reg_name)
        group.add(self.reg_login)
        group.add(self.reg_password)
        group.add(self.reg_repeat)
        box.append(group)
        self.reg_error = Gtk.Label(xalign=0, wrap=True, visible=False)
        self.reg_error.add_css_class("error-text")
        box.append(self.reg_error)
        button = Gtk.Button(label="Зарегистрироваться")
        button.add_css_class("suggested-action")
        button.add_css_class("pill")
        button.connect("clicked", lambda *_: self._register())
        box.append(button)
        return box

    def _show_login_mode(self, button):
        if self._switching:
            return
        if not button.get_active():
            if not self.mode_reg.get_active():
                self._switching = True
                button.set_active(True)
                self._switching = False
            return
        self._switching = True
        self.mode_reg.set_active(False)
        self._switching = False
        self.form_title.set_label("С возвращением")
        self.stack.set_visible_child_name("login")

    def _show_register_mode(self, button):
        if self._switching:
            return
        if not button.get_active():
            if not self.mode_login.get_active():
                self._switching = True
                button.set_active(True)
                self._switching = False
            return
        self._switching = True
        self.mode_login.set_active(False)
        self._switching = False
        self.form_title.set_label("Первый маршрут")
        self.stack.set_visible_child_name("register")

    def _login(self):
        user, error = db.authenticate(self.login.get_text(), self.password.get_text())
        if error:
            self.login_error.set_text(error)
            self.login_error.set_visible(True)
            return
        self.window.show_shell(user)

    def _register(self):
        if self.reg_password.get_text() != self.reg_repeat.get_text():
            self.reg_error.set_text("Пароли не совпадают")
            self.reg_error.set_visible(True)
            return
        ok, message = db.create_user(
            self.reg_login.get_text(),
            self.reg_password.get_text(),
            self.reg_name.get_text(),
            role="tourist",
        )
        if not ok:
            self.reg_error.set_text(message)
            self.reg_error.set_visible(True)
            return
        user, error = db.authenticate(self.reg_login.get_text(), self.reg_password.get_text())
        if error:
            self.reg_error.set_text(error)
            self.reg_error.set_visible(True)
            return
        self.window.show_shell(user)
        self.window.notify("Учётная запись создана")


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application)
        self.set_title("TravelHub")
        self.set_default_size(1200, 780)
        self.user = None
        self.shell = None
        self.add_css_class("th-app")
        self.toast = Adw.ToastOverlay()
        self.toolbar = Adw.ToolbarView()
        self.heading = Gtk.Label(label="")
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        header.add_css_class("th-titlebar")
        header.set_title_widget(self.heading)
        self.toolbar.add_top_bar(header)
        self.toast.set_child(self.toolbar)
        self.set_content(self.toast)
        self.show_login()

    def notify(self, text):
        self.toast.add_toast(Adw.Toast(title=text))

    def show_login(self):
        self.user = None
        self.shell = None
        self.toolbar.set_content(LoginView(self))

    def show_shell(self, user):
        self.user = user
        self.shell = ShellView(self)
        self.toolbar.set_content(self.shell)

    def refresh_session(self):
        fresh = db.get_user(self.user["id"])
        if not fresh or not fresh["is_active"]:
            self.notify("Сессия завершена")
            self.show_login()
            return
        role_changed = fresh["role"] != self.user["role"]
        self.user = fresh
        if role_changed or self.shell is None:
            self.show_shell(fresh)
            self.notify("Роль изменена, меню обновлено")
            return
        self.shell.sync_identity()
        self.shell.reload_visible()
        self.notify("Профиль обновлён")


class TravelApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="ru.travelhub.Desktop")
        self.connect("activate", self._activate)

    def _activate(self, _app):
        if getattr(self, "win", None) is not None:
            self.win.present()
            return
        db.init_db()
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER,
        )
        self.win = MainWindow(self)
        self.win.present()


def main():
    app = TravelApp()
    return app.run(None)
