# This class stores static information about the app, and is displayed in the about window
import os
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GdkPixbuf

base_dir = os.path.dirname(os.path.realpath(__file__))
program_name = "Arco Linux Welcome App"
version = "dev-0.1"
website = "https://arcolinux.info"


class AboutDialog(Gtk.Dialog):
    def __init__(self, debug, **kwargs):
        super().__init__(**kwargs)

        self.set_border_width(10)
        self.set_resizable(False)

        headerbar = Gtk.HeaderBar()
        headerbar.set_title(program_name)
        headerbar.set_show_close_button(True)

        headerbar.pack_start(
            Gtk.Image().new_from_pixbuf(
                GdkPixbuf.Pixbuf().new_from_file_at_size(
                    os.path.join(base_dir, "images/arcolinux.png"), 16, 16
                )
            )
        )

        if debug is True:
            desc = (
                f"<b>Arco Linux installer</b>\n"
                f"We advise to clean the computer with GParted before installing.\n"
                f"During the Calamares installation many options will be open to you.\n\n"
                f"<b>You have the freedom of choice.</b>\n\n"
                f"We communicate with our community via a diversity of social media.\n"
                f"Do join us to learn the latest news, ask questions or for casual talk.\n"
                f"Telegram is for chitchat - Discord is for assistance.\n"
                f"We have a forum for the longer and more technical questions.\n\n"
            )
        else:
            desc = (
                f"We communicate with our community via a diversity of social media.\n"
                f"Do join us to learn the latest news, ask questions or for casual talk.\n"
                f"Telegram is for chitchat - Discord is for assistance.\n"
                f"We have a forum for the longer and more technical questions.\n\n"
            )

        self.set_titlebar(headerbar)

        label_about_desc = Gtk.Label(xalign=0, yalign=0)
        label_about_desc.set_markup(desc)
        label_about_desc.set_halign(Gtk.Align.CENTER)
        label_about_desc.set_justify(Gtk.Justification.CENTER)

        self.vbox.pack_start(
            Gtk.Image().new_from_pixbuf(
                GdkPixbuf.Pixbuf().new_from_file_at_size(
                    os.path.join(base_dir, "images/arcolinux.png"), 64, 64
                )
            ),
            False,
            False,
            0,
        )
        self.vbox.pack_start(label_about_desc, False, True, 0)

        self.set_modal(True)

        self.connect("response", self.on_response)

        # bug in the license button appearing, but it doesn't do anything
        # remove all the buttons, then later add a close button

        button_close = Gtk.Button(label="Close")
        button_close.connect("clicked", self.on_response)
        button_close.set_halign(Gtk.Align.END)

        self.vbox.pack_end(button_close, False, False, 0)

    def on_response(self, dialog):
        self.destroy()
