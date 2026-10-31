"""GTK widget translation helpers backed by the shared translation catalog."""

from __future__ import annotations

from gi.repository import Adw, Gtk

from keycan.services.translations import translate


def apply_to_widget_tree(root: Gtk.Widget, language: str) -> None:
    """Translate application-owned widget labels without touching lesson data."""
    stack = [root]
    while stack:
        widget = stack.pop()
        stack.extend(_children(widget))

        if isinstance(widget, Gtk.Label):
            _set_text(widget, language)
        elif isinstance(widget, Gtk.Button):
            _set_text(widget, language)
            _set_tooltip(widget, language)
        elif isinstance(widget, Gtk.ToggleButton):
            _set_text(widget, language)
        elif isinstance(widget, (Gtk.Entry, Gtk.SearchEntry)):
            _set_placeholder(widget, language)
        elif isinstance(widget, Gtk.SpinButton):
            _set_tooltip(widget, language)
        elif isinstance(widget, Adw.EntryRow):
            title = widget.get_title()
            if title:
                widget.set_title(translate(title, language))
        elif isinstance(widget, Adw.SwitchRow):
            _set_title_subtitle(widget, language)
        elif isinstance(widget, Adw.ComboRow):
            _set_title_subtitle(widget, language)
            _translate_string_list(widget.get_model(), language)
        elif isinstance(widget, Adw.ActionRow):
            _set_title_subtitle(widget, language)
        elif isinstance(widget, Adw.PreferencesGroup):
            _set_title_description(widget, language)


def _children(widget: Gtk.Widget) -> list[Gtk.Widget]:
    result = []
    child = widget.get_first_child()
    while child is not None:
        result.append(child)
        child = child.get_next_sibling()
    return result


def _set_text(widget: Gtk.Widget, language: str) -> None:
    if not hasattr(widget, "get_label") or not hasattr(widget, "set_label"):
        return
    current = widget.get_label()
    if current:
        widget.set_label(translate(current, language))


def _set_tooltip(widget: Gtk.Widget, language: str) -> None:
    tooltip = widget.get_tooltip_text()
    if tooltip:
        widget.set_tooltip_text(translate(tooltip, language))


def _set_placeholder(widget: Gtk.Widget, language: str) -> None:
    placeholder = widget.get_placeholder_text()
    if placeholder:
        widget.set_placeholder_text(translate(placeholder, language))


def _translate_string_list(model, language: str) -> None:
    if not isinstance(model, Gtk.StringList):
        return
    for index in range(model.get_n_items()):
        item = model.get_string(index)
        translated = translate(item, language)
        if translated != item:
            model.splice(index, 1, [translated])


def _set_title_subtitle(row, language: str) -> None:
    title, subtitle = row.get_title(), row.get_subtitle()
    if title:
        row.set_title(translate(title, language))
    if subtitle:
        row.set_subtitle(translate(subtitle, language))


def _set_title_description(group: Adw.PreferencesGroup, language: str) -> None:
    title, description = group.get_title(), group.get_description()
    if title:
        group.set_title(translate(title, language))
    if description:
        group.set_description(translate(description, language))
