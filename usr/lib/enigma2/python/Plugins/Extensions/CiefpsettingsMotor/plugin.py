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

# Kompatibilnost za Python 2 i Python 3
try:
    from urllib import parse as urlparse  # Python 3
except ImportError:
    import urlparse  # Python 2

PLUGIN_VERSION = "v1.9"
PLUGIN_NAME = "CiefpsettingsMotor"
PLUGIN_DESC = "Download, unzip and install ciefpsettings motor from GitHub"
PLUGIN_ICON = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpsettingsMotor/icon.png"
PLUGIN_LOGO = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpsettingsMotor/logo.png"

GITHUB_API_URL = "https://api.github.com/repos/ciefp/ciefpsettings-enigma2-zipped/contents/"
STATIC_NAMES = ["ciefp-E2-75E-34W"]

def to_unicode(s):
    if sys.version_info[0] < 3:
        return s.decode('utf-8') if isinstance(s, str) else s
    return s

class CiefpSettingsScreen(Screen):
    skin = """
    <screen name="CiefpSettingsScreen" position="center,center" size="1200,600" title="Ciefp Settings Motor">
        <widget name="logo" position="10,10" size="1200,450" transparent="1" alphatest="on" />
        <widget name="menu" position="10,440" size="1200,30" scrollbarMode="showOnDemand" />
        <widget name="status" position="10,480" size="1200,60" font="Regular;26" halign="center" valign="center" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["logo"] = Pixmap()
        self["menu"] = MenuList([])
        self["status"] = Label("Ready to install settings. Press OK on your remote and wait...")
        self["actions"] = ActionMap(
            ["OkCancelActions"],
            {
                "ok": self.ok_pressed,
                "cancel": self.close,
            },
        )
        self.available_files = {}
        self.onLayoutFinish.append(self.set_logo)
        self.onLayoutFinish.append(self.fetch_file_list)

    def set_logo(self):
        logo_path = PLUGIN_LOGO
        if os.path.exists(logo_path):
            self["logo"].instance.setPixmapFromFile(logo_path)
        else:
            self["status"].setText("Logo file not found.")

    def fetch_file_list(self):
        try:
            self["status"].setText("Fetching available lists from GitHub...")
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()

            files = response.json()
            for file in files:
                file_name = file.get("name", "")
                for static_name in STATIC_NAMES:
                    if file_name.startswith(static_name):
                        self.available_files[static_name] = file_name

            sorted_files = sorted(self.available_files.keys(), key=lambda x: STATIC_NAMES.index(x))
            if sorted_files:
                self["menu"].setList(sorted_files)
                self["status"].setText("Select a channel list to download.")
            else:
                self["status"].setText("No valid lists found on GitHub.")
        except requests.exceptions.RequestException as e:
            self["status"].setText("Network error: " + to_unicode(str(e)))
        except Exception as e:
            self["status"].setText("Error processing lists: " + to_unicode(str(e)))

    def ok_pressed(self):
        selected_item = self["menu"].getCurrent()
        if selected_item:
            self.download_and_install(selected_item)

    def download_and_install(self, selected_item):
        file_name = self.available_files.get(selected_item)
        if not file_name:
            self["status"].setText("Error: No file found for {0}.".format(selected_item))
            return

        url = "https://github.com/ciefp/ciefpsettings-enigma2-zipped/raw/refs/heads/master/" + file_name
        download_path = "/tmp/" + file_name
        extract_path = "/tmp/" + selected_item

        try:
            self["status"].setText("Downloading {0}...".format(file_name))
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)

            self["status"].setText("Extracting {0}...".format(file_name))
            with zipfile.ZipFile(download_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            self.copy_files(extract_path)
            self.reload_settings()
            self["status"].setText("{0} installed successfully!".format(selected_item))
        except requests.exceptions.RequestException as e:
            self["status"].setText("Download error: " + to_unicode(str(e)))
        except Exception as e:
            self["status"].setText("Installation error: " + to_unicode(str(e)))
        finally:
            if os.path.exists(download_path):
                os.remove(download_path)
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)

    def copy_files(self, path):
        dest_enigma2 = "/etc/enigma2/"
        dest_tuxbox = "/etc/tuxbox/"

        for root, dirs, files in os.walk(path):
            for file in files:
                source_file = os.path.join(root, file)
                if file == "satellites.xml":
                    shutil.move(source_file, os.path.join(dest_tuxbox, file))
                elif file.endswith(".tv") or file.endswith(".radio") or file == "lamedb":
                    shutil.move(source_file, os.path.join(dest_enigma2, file))

    def reload_settings(self):
        try:
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
            self.session.open(MessageBox, "Reload successful! New settings are now active.  ..::ciefpsettings::..", MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            self.session.open(MessageBox, "Reload failed: " + to_unicode(str(e)), MessageBox.TYPE_ERROR, timeout=5)

def main(session, **kwargs):
    session.open(CiefpSettingsScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=PLUGIN_NAME,
            description="{0} ({1})".format(PLUGIN_DESC, PLUGIN_VERSION),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=PLUGIN_ICON,
            fnc=main
        )
    ]
