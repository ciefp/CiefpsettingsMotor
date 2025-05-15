from __future__ import print_function
import sys
import os
import shutil
import zipfile
import requests
from enigma import eTimer, eDVBDB
from Screens.Screen import Screen
from datetime import datetime
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList

# Handle urllib.parse for Python 2 and 3
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse

PLUGIN_VERSION = "v2.3"
PLUGIN_NAME = "CiefpSettingsMotor"
PLUGIN_DESC = "Download, unzip and install ciefpsettings motor from GitHub"
PLUGIN_ICON = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpsettingsMotor/icon.png"
PLUGIN_LOGO = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpsettingsMotor/logo.png"
GITHUB_API_URL = "https://api.github.com/repos/ciefp/ciefpsettings-enigma2-zipped/contents/"
STATIC_NAMES = ["ciefp-E2-75E-34W"]

def to_unicode(s):
    """Convert string to unicode for Python 2, return as-is for Python 3."""
    if sys.version_info[0] < 3:
        return s.decode('utf-8') if isinstance(s, str) else s
    return s

class CiefpSettingsScreen(Screen):
    skin = """
    <screen name="CiefpSettingsScreen" position="center,center" size="1200,600" title="..:: Ciefp Settings Motor ::..">
        <widget name="logo" position="10,10" size="1200,480" transparent="1" alphatest="on" />
        <widget name="menu" position="10,480" size="1200,45" font="Regular;20" halign="center" valign="center" />
        <widget name="status" position="10,520" size="1200,60" font="Regular;26" halign="center" valign="center" />
        <widget name="version_info" position="10,560" size="1200,40" font="Regular;20" halign="center" valign="center" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["logo"] = Pixmap()
        self["menu"] = MenuList([])
        self["status"] = Label("Ready to install settings. Press OK on your remote and wait...")
        self["version_info"] = Label("")
        self["actions"] = ActionMap(
            ["OkCancelActions"],
            {
                "ok": self.ok_pressed,
                "cancel": self.close,
            }
        )
        self.available_files = {}
        self.existing_user_bouquets = set()
        self.onLayoutFinish.append(self.set_logo)
        self.onLayoutFinish.append(self.fetch_file_list_and_show_version)

    def set_logo(self):
        logo_path = PLUGIN_LOGO
        if os.path.exists(logo_path):
            self["logo"].instance.setPixmapFromFile(logo_path)
        else:
            self["status"].setText("Logo file not found.")

    def fetch_file_list_and_show_version(self):
        try:
            self["status"].setText("Fetching available lists from GitHub...")
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            files = response.json()

            found_version = None
            for file in files:
                if isinstance(file, dict) and "name" in file:
                    file_name = file["name"]
                    for static_name in STATIC_NAMES:
                        if file_name.startswith(static_name):
                            self.available_files[static_name] = file_name
                            found_version = file_name

            sorted_files = sorted(self.available_files.keys(), key=lambda x: STATIC_NAMES.index(x))
            if sorted_files:
                self["menu"].setList(sorted_files)
                self["status"].setText("Select a channel list to download.")
                if found_version:
                    self["version_info"].setText("Available version {}".format(found_version))
            else:
                self["status"].setText("No valid lists found on GitHub.")
                self["version_info"].setText("No available version found")
        except requests.exceptions.RequestException as e:
            self["status"].setText("Network error: {}".format(to_unicode(str(e))))
            self["version_info"].setText("Error fetching version information")
        except Exception as e:
            self["status"].setText("Error processing lists: {}".format(to_unicode(str(e))))
            self["version_info"].setText("Error fetching version information")

    def ok_pressed(self):
        selected_item = self["menu"].getCurrent()
        if selected_item:
            self.download_and_install(selected_item)

    def download_and_install(self, selected_item):
        file_name = self.available_files.get(selected_item)
        if not file_name:
            self["status"].setText("Error: No file found for {}.".format(selected_item))
            return
        url = "https://github.com/ciefp/ciefpsettings-enigma2-zipped/raw/refs/heads/master/" + file_name
        download_path = "/tmp/" + file_name
        extract_path = "/tmp/" + selected_item
        try:
            self.identify_existing_user_bouquets()
            self["status"].setText("Downloading {}...".format(file_name))
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()
            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            self["status"].setText("Extracting {}...".format(file_name))
            with zipfile.ZipFile(download_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
            self.copy_files(extract_path)
            self.reload_settings()
            self["status"].setText("{} installed successfully!".format(selected_item))
        except requests.exceptions.RequestException as e:
            self["status"].setText("Download error: {}".format(to_unicode(str(e))))
        except Exception as e:
            self["status"].setText("Installation error: {}".format(to_unicode(str(e))))
        finally:
            if os.path.exists(download_path):
                os.remove(download_path)
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)

    def identify_existing_user_bouquets(self):
        dest_enigma2 = "/etc/enigma2/"
        prefixes = ("userbouquet.buket", "userbouquet.ciefp", "userbouquet.ciefpsettings", 
                    "userbouquet.link", "userbouquet.marker")
        if os.path.exists(dest_enigma2):
            for file in os.listdir(dest_enigma2):
                if (file.endswith(".tv") or file.endswith(".radio")) and not any(file.startswith(prefix) for prefix in prefixes):
                    self.existing_user_bouquets.add(file)
        print("[DEBUG] Existing user bouquets: {}".format(self.existing_user_bouquets))

    def copy_files(self, path):
        dest_enigma2 = "/etc/enigma2/"
        dest_tuxbox = "/etc/tuxbox/"
        new_bouquets = []

        for root, dirs, files in os.walk(path):
            for file in files:
                source_file = os.path.join(root, file)
                if file == "satellites.xml":
                    shutil.move(source_file, os.path.join(dest_tuxbox, file))
                elif file == "lamedb":
                    shutil.move(source_file, os.path.join(dest_enigma2, file))
                elif file == "bouquets.tv":
                    new_bouquets_path = source_file
                elif file.endswith(".tv") or file.endswith(".radio"):
                    dest_path = os.path.join(dest_enigma2, file)
                    shutil.move(source_file, dest_path)
                    new_bouquets.append(file)

        if new_bouquets:
            self.update_bouquets_tv(dest_enigma2, new_bouquets_path, new_bouquets)

    def update_bouquets_tv(self, dest_enigma2, new_bouquets_path, new_bouquets):
        existing_bouquets_path = os.path.join(dest_enigma2, "bouquets.tv")
        temp_bouquets_path = os.path.join(dest_enigma2, "bouquets.tv.tmp")

        existing_lines = []
        if os.path.exists(existing_bouquets_path):
            with open(existing_bouquets_path, 'r') as f:
                existing_lines = f.readlines()

        new_lines = []
        if os.path.exists(new_bouquets_path):
            with open(new_bouquets_path, 'r') as f:
                new_lines = f.readlines()

        updated_lines = []
        for line in new_lines:
            if "FROM BOUQUET" in line:
                bouquet_file = line.split('"')[1]
                if bouquet_file in new_bouquets:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        for line in existing_lines:
            if "FROM BOUQUET" in line:
                bouquet_file = line.split('"')[1]
                if bouquet_file in self.existing_user_bouquets and not any(bouquet_file in existing_line for existing_line in updated_lines):
                    updated_lines.append(line)

        with open(temp_bouquets_path, 'w') as f:
            updated_lines = [line if line.endswith('\n') else line + '\n' for line in updated_lines]
            f.writelines(updated_lines)
        shutil.move(temp_bouquets_path, existing_bouquets_path)

    def reload_settings(self):
        try:
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
            self.session.open(MessageBox, "Reload successful! New settings are now active.  ..::ciefpsettings::..", MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            self.session.open(MessageBox, "Reload failed: {}".format(to_unicode(str(e))), MessageBox.TYPE_ERROR, timeout=5)

def main(session, **kwargs):
    session.open(CiefpSettingsScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=PLUGIN_NAME,
            description="{} ({})".format(PLUGIN_DESC, PLUGIN_VERSION),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=PLUGIN_ICON,
            fnc=main
        )
    ]