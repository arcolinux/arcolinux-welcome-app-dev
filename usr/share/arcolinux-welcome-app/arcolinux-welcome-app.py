#!/usr/bin/env python3
# =================================================================
# =          Authors: Brad Heffernan & Erik Dubois                =
# =================================================================
import gi
import os
import GUI
import conflicts

# import wnck
import subprocess
import threading
import webbrowser
import shutil
import socket
from time import sleep
from queue import Queue

gi.require_version("Gtk", "3.0")
gi.require_version("Wnck", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib, Wnck  # noqa

REMOTE_SERVER = "www.google.com"


class Main(Gtk.Window):
    def __init__(self):
        super(Main, self).__init__(title="ArcoLinux Welcome App")
        self.set_border_width(10)
        self.set_default_size(860, 250)
        self.set_icon_from_file(os.path.join(GUI.base_dir, "images/arcolinux.png"))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.results = ""
        if not os.path.exists(GUI.home + "/.config/arcolinux-welcome-app/"):
            os.mkdir(GUI.home + "/.config/arcolinux-welcome-app/")
            with open(GUI.Settings, "w") as f:
                f.write("autostart=True")
                f.close()

        # a queue to store package install progress
        self.pkg_queue = Queue()

        # default pacman lockfile
        self.pacman_lockfile = "/var/lib/pacman/db.lck"

        # full cmd path to run an application
        self.app_cmd = None

        # get the username of the user running the welcome app
        self.sudo_username = os.getlogin()

        # store the package name to install
        self.package = None

        GUI.GUI(self, Gtk, GdkPixbuf)

        if GUI.username == GUI.user:
            threading.Thread(
                target=self.internet_notifier, args=(), daemon=True
            ).start()

    def on_mirror_clicked(self, widget):
        threading.Thread(target=self.mirror_update, daemon=True).start()

    def on_update_clicked(self, widget):
        print("Clicked")

    def on_grub_clicked(self, widget):
        bootloader_file = "/etc/calamares/modules/bootloader-grub.conf"

        self.app_cmd = [
            "sudo",
            "cp",
            bootloader_file,
            "/etc/calamares/modules/bootloader.conf",
        ]
        threading.Thread(target=self.run_app, daemon=True).start()

    def on_systemboot_clicked(self, widget):
        bootloader_file = "/etc/calamares/modules/bootloader-systemd.conf"

        self.app_cmd = [
            "sudo",
            "cp",
            bootloader_file,
            "/etc/calamares/modules/bootloader.conf",
        ]
        threading.Thread(target=self.run_app, daemon=True).start()

    def on_ai_clicked(self, widget):
        settings_beginner_file = "/etc/calamares/settings-beginner.conf"
        packages_no_sys_update_file = (
            "/etc/calamares/modules/packages-no-system-update.conf"
        )
        clamares_polkit = "/usr/bin/calamares_polkit"

        self.app_cmd = [
            "sudo",
            "cp",
            settings_beginner_file,
            "/etc/calamares/settings.conf",
        ]
        threading.Thread(target=self.run_app, daemon=True).start()

        self.app_cmd = [
            "sudo",
            "cp",
            packages_no_sys_update_file,
            "/etc/calamares/modules/packages.conf",
        ]

        threading.Thread(target=self.run_app, daemon=True).start()
        subprocess.Popen([clamares_polkit, "-d"], shell=False)

    def on_aica_clicked(self, widget):
        settings_adv_file = "/etc/calamares/settings-advanced.conf"
        system_update_file = "/etc/calamares/modules/packages-system-update.conf"
        clamares_polkit = "/usr/bin/calamares_polkit"

        self.app_cmd = [
            "sudo",
            "cp",
            "/etc/calamares/settings-advanced.conf",
            "/etc/calamares/settings.conf",
        ]
        threading.Thread(target=self.run_app, daemon=True).start()

        self.app_cmd = [
            "sudo",
            "cp",
            system_update_file,
            "/etc/calamares/modules/packages.conf",
        ]
        threading.Thread(target=self.run_app, daemon=True).start()

        subprocess.Popen([clamares_polkit, "-d"], shell=False)

    def on_gp_clicked(self, widget):
        self.package = "gparted"
        self.app_cmd = ["/usr/bin/gparted"]
        self.pacman_cmd = [
            "sudo",
            "pacman",
            "-Sy",
            "gparted",
            "--noconfirm",
            "--needed",
        ]

        if not os.path.exists(self.pacman_lockfile):
            if self.check_package_installed(self.package):
                threading.Thread(target=self.run_app, daemon=True).start()
            else:
                md = Gtk.MessageDialog(
                    parent=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="%s was not found" % self.package,
                    title="Warning",
                )
                md.format_secondary_markup("Would you like to install it?")
                response = md.run()
                md.destroy()

                if response == Gtk.ResponseType.YES:
                    threading.Thread(
                        target=self.check_package_queue, daemon=True
                    ).start()
                    threading.Thread(target=self.install_package, daemon=True).start()
        else:
            print(
                "[ERROR]: Pacman lockfile found %s, is another pacman process running?"
                % self.pacman_lockfile
            )
            md = Gtk.MessageDialog(
                parent=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Pacman lockfile found %s, is another pacman process running?"
                % self.pacman_lockfile,
                title="Warning",
            )
            md.run()
            md.destroy()

    def on_buttonatt_clicked(self, widget):
        self.package = "archlinux-tweak-tool-git"
        self.app_cmd = [
            "sudo",
            "-u",
            self.sudo_username,
            "/usr/bin/archlinux-tweak-tool",
        ]
        self.pacman_cmd = [
            "sudo",
            "pacman",
            "-Sy",
            "archlinux-tweak-tool-git",
            "--noconfirm",
            "--needed",
        ]
        if not os.path.exists(self.pacman_lockfile):
            if not self.check_package_installed(self.package):
                md = Gtk.MessageDialog(
                    parent=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="%s was not found" % "Arch Linux Tweak Tool",
                    title="Warning",
                )
                md.format_secondary_markup("Would you like to install it?")
                response = md.run()
                md.destroy()

                if response == Gtk.ResponseType.YES:
                    threading.Thread(
                        target=self.check_package_queue, daemon=True
                    ).start()
                    threading.Thread(target=self.install_package, daemon=True).start()
            else:
                threading.Thread(target=self.run_app, daemon=True).start()

        else:
            print(
                "[ERROR]: Pacman lockfile found %s, is another pacman process running?"
                % self.pacman_lockfile
            )
            md = Gtk.MessageDialog(
                parent=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Pacman lockfile found %s, is another pacman process running?"
                % self.pacman_lockfile,
                title="Warning",
            )
            md.run()
            md.destroy()

    def check_package_installed(self, package):
        pacman_cmd = ["pacman", "-Qi", package]
        try:
            process = subprocess.run(
                pacman_cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            if process.returncode == 0:
                # package is installed
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            # package is not installed
            return False

    def on_buttonarandr_clicked(self, widget):
        self.app_cmd = ["/usr/bin/arandr"]
        self.package = "arandr"
        self.pacman_cmd = ["sudo", "pacman", "-Sy", "arandr", "--noconfirm", "--needed"]

        if not os.path.exists(self.pacman_lockfile):
            if not self.check_package_installed(self.package):
                md = Gtk.MessageDialog(
                    parent=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="%s was not found\n" % self.package,
                    title="Warning",
                )
                md.format_secondary_markup("Would you like to install it?")
                response = md.run()
                md.destroy()

                if response == Gtk.ResponseType.YES:
                    threading.Thread(
                        target=self.check_package_queue, daemon=True
                    ).start()
                    threading.Thread(target=self.install_package, daemon=True).start()

            else:
                threading.Thread(target=self.run_app, daemon=True).start()
        else:
            print(
                "[ERROR]: Pacman lockfile found %s, is another pacman process running?"
                % self.pacman_lockfile
            )
            md = Gtk.MessageDialog(
                parent=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Pacman lockfile found %s, is another pacman process running?"
                % self.pacman_lockfile,
                title="Warning",
            )
            md.run()
            md.destroy()

    def on_button_sofi_clicked(self, widget):
        self.app_cmd = ["sudo", "-u", self.sudo_username, "/usr/bin/sofirem"]
        self.package = "sofirem-git"
        self.pacman_cmd = [
            "sudo",
            "pacman",
            "-Sy",
            "sofirem-git",
            "--noconfirm",
            "--needed",
        ]

        if not os.path.exists(self.pacman_lockfile):
            if not self.check_package_installed(self.package):
                md = Gtk.MessageDialog(
                    parent=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="%s was not found" % "Sofirem",
                    title="Warning",
                )
                md.format_secondary_markup("Would you like to install it?")
                response = md.run()
                md.destroy()

                if response == Gtk.ResponseType.YES:
                    threading.Thread(
                        target=self.check_package_queue, daemon=True
                    ).start()
                    threading.Thread(target=self.install_package, daemon=True).start()
            else:
                threading.Thread(target=self.run_app, daemon=True).start()
        else:
            print(
                "[ERROR]: Pacman lockfile found %s, is another pacman process running?"
                % self.pacman_lockfile
            )
            md = Gtk.MessageDialog(
                parent=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Pacman lockfile found %s, is another pacman process running?"
                % self.pacman_lockfile,
                title="Warning",
            )
            md.run()
            md.destroy()

    def check_package_queue(self):
        while True:
            status = self.pkg_queue.get()
            try:
                if status == 0:
                    self.run_app()
                    break
                if status == 1:
                    print("[ERROR]: Package %s install failed" % self.package)
                    break

                sleep(0.2)
            except Exception as e:
                print("[ERROR]: Exception in check_package_queue(): %s" % e)
            finally:
                self.pkg_queue.task_done()

    def install_package(self):
        try:
            with subprocess.Popen(
                self.pacman_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
            ) as process:
                while True:
                    if process.poll() is not None:
                        break

                    for line in process.stdout:
                        print(line.strip())

                if self.check_package_installed(self.package):
                    self.pkg_queue.put(0)
                    print("[INFO]: Pacman package install completed")
                else:
                    self.pkg_queue.put(1)
                    print("[ERROR]: Pacman package install failed")

        except Exception as e:
            print("[ERROR]: Exception in install_package(): %s" % e)
        finally:
            self.pkg_queue.put(None)

    def run_app(self):
        process = subprocess.run(
            self.app_cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        # for debugging print stdout to console
        if GUI.DEBUG is True:
            print(process.stdout)

    def statup_toggle(self, widget):
        if widget.get_active() is True:
            if os.path.isfile(GUI.dot_desktop):
                shutil.copy(GUI.dot_desktop, GUI.autostart)
        else:
            if os.path.isfile(GUI.autostart):
                os.unlink(GUI.autostart)
        self.save_settings(widget.get_active())

    def save_settings(self, state):
        with open(GUI.Settings, "w") as f:
            f.write("autostart=" + str(state))
            f.close()

    def load_settings(self):
        line = "True"
        if os.path.isfile(GUI.Settings):
            with open(GUI.Settings, "r") as f:
                lines = f.readlines()
                for i in range(len(lines)):
                    if "autostart" in lines[i]:
                        line = lines[i].split("=")[1].strip().capitalize()
                f.close()
        return line

    def on_link_clicked(self, widget, link):
        t = threading.Thread(target=self.weblink, args=(link,))
        t.daemon = True
        t.start()

    def on_social_clicked(self, widget, event, link):
        t = threading.Thread(target=self.weblink, args=(link,))
        t.daemon = True
        t.start()

    def on_info_clicked(self, widget, event):
        window_list = Wnck.Screen.get_default().get_windows()
        state = False
        for win in window_list:
            if "Information" in win.get_name():
                state = True
        if not state:
            w = conflicts.Conflicts()
            w.show_all()

    def weblink(self, link):
        webbrowser.open_new_tab(link)

    def is_connected(self):
        try:
            host = socket.gethostbyname(REMOTE_SERVER)
            s = socket.create_connection((host, 80), 2)
            s.close()
            return True
        except:  # noqa
            pass
        return False

    def tooltip_callback(self, widget, x, y, keyboard_mode, tooltip, text):
        tooltip.set_text(text)
        return True

    def on_launch_clicked(self, widget, event, link):
        if os.path.isfile("/usr/bin/archlinux-tweak-tool"):
            self.app_cmd = "/usr/bin/archlinux-tweak-tool"
            threading.Thread(target=self.run_app, daemon=True).start()

        else:
            print("att")
            md = Gtk.MessageDialog(
                parent=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Not Found!",
            )
            md.format_secondary_markup(
                "<b>ArcoLinux Tweak Tool</b> was not found on your system\n\
Do you want to install it?"
            )

            result = md.run()

            md.destroy()

            if result in (Gtk.ResponseType.OK, Gtk.ResponseType.YES):
                t1 = threading.Thread(target=self.installATT, args=())
                t1.daemon = True
                t1.start()

    def internet_notifier(self):
        bb = 0
        dis = 0
        while True:
            if not self.is_connected():
                dis = 1
                GLib.idle_add(self.button8.set_sensitive, False)
                GLib.idle_add(
                    self.cc.set_markup,
                    "<span foreground='orange'><b><i>Not connected to internet</i></b> \nCalamares will <b>not</b> install additional software</span>",
                )  # noqa
            else:
                if bb == 0 and dis == 1:
                    GLib.idle_add(self.button8.set_sensitive, True)
                    GLib.idle_add(self.cc.set_text, "")
                    bb = 1
            sleep(3)

    # def mirror_reload(self):
    #     md = Gtk.MessageDialog(parent=self,
    #                            flags=0,
    #                            message_type=Gtk.MessageType.INFO,
    #                            buttons=Gtk.ButtonsType.YES_NO,
    #                            text="You are now connected")
    #     md.format_secondary_markup("Would you like to update the <b>Arch Linux</b> mirrorlist?")
    #     response = md.run()

    #     if response == Gtk.ResponseType.YES:
    #         GLib.idle_add(self.cc.set_markup, "<span foreground='orange'><b><i>Updating your mirrorlist</i></b> \nThis may take some time, please wait...</span>")  # noqa
    #         t = threading.Thread(target=self.mirror_update)
    #         t.daemon = True
    #         t.start()
    #     md.destroy()

    def mirror_update(self):
        GLib.idle_add(
            self.cc.set_markup,
            "<span foreground='orange'><b><i>Updating your mirrorlist</i></b> \nThis may take some time, please wait...</span>",
        )  # noqa
        GLib.idle_add(self.button8.set_sensitive, False)
        subprocess.run(
            [
                "pkexec",
                "/usr/bin/reflector",
                "--age",
                "6",
                "--latest",
                "21",
                "--fastest",
                "21",
                "--threads",
                "21",
                "--sort",
                "rate",
                "--protocol",
                "https",
                "--save",
                "/etc/pacman.d/mirrorlist",
            ],
            shell=False,
        )
        print("FINISHED!!!")
        GLib.idle_add(self.cc.set_markup, "<b>DONE</b>")
        GLib.idle_add(self.button8.set_sensitive, True)

    # def btrfs_update(self):
    #    if GUI.DEBUG:
    #        path = "/home/bheffernan/Repos/GITS/XFCE/hefftor-calamares-oem-config/calamares/modules/partition.conf"
    #    else:
    #        path = "/etc/calamares/modules/partition.conf"

    #    with open(path, "r") as f:
    #        lines = f.readlines()
    #        f.close()
    #    data = [x for x in lines if "defaultFileSystemType" in x]
    #    pos = lines.index(data[0])

    #    lines[pos] = "defaultFileSystemType:  \"ext4\"\n"

    #    with open(path, "w") as f:
    #        f.writelines(lines)
    #        f.close()

    #    GLib.idle_add(self.MessageBox,"Success", "Your filesystem has been changed.")

    # def finished_mirrors(self):
    #     md = Gtk.MessageDialog(parent=self,
    #                            flags=0,
    #                            message_type=Gtk.MessageType.INFO,
    #                            buttons=Gtk.ButtonsType.OK,
    #                            text="Finished")
    #     md.format_secondary_markup("Mirrorlist has been updated!")
    #     md.run()
    #     md.destroy()
    #     GLib.idle_add(self.cc.set_markup, "")
    #     GLib.idle_add(self.button8.set_sensitive, True)

    def MessageBox(self, title, message):
        md = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        md.format_secondary_markup(message)
        md.run()
        md.destroy()

    def installATT(self):
        subprocess.call(
            [
                "pkexec",
                "/usr/bin/pacman",
                "-S",
                "archlinux-tweak-tool-git",
                "--noconfirm",
            ],
            shell=False,
        )
        GLib.idle_add(
            self.MessageBox,
            "Success!",
            "<b>ArcoLinux Tweak Tool</b> has been installed successfully",
        )  # noqa

    # def get_message(self, title, message):
    #     t = threading.Thread(target=self.fetch_notice,


#                              args=(title, message,))
#     t.daemon = True
#     t.start()
#     t.join()

# def fetch_notice(self, title, message):
#     try:
#         url = 'https://bradheff.github.io/notice/notice'
#         req = requests.get(url, verify=True, timeout=1)

#         if req.status_code == requests.codes.ok:
#             if not len(req.text) <= 1:
#                 title.set_markup(
#                 "<big><b><u>Notice</u></b></big>")
#                 message.set_markup(req.text)
#                 self.results = True
#             else:
#                 self.results = False
#         else:
#             self.results = False
#     except:
#         self.results = False


if __name__ == "__main__":
    w = Main()
    w.connect("delete-event", Gtk.main_quit)
    w.show_all()
    Gtk.main()
