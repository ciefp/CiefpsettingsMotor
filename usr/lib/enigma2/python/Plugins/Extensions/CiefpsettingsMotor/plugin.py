import os
import requests
from urllib.parse import urljoin
from enigma import eTimer, eDVBDB
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Plugins.Plugin import PluginDescriptor

PLUGIN_VERSION = "v1.6"
PLUGIN_NAME = "CiefpsettingsMotor"
PLUGIN_DESC = "Download and install ciefpsettings motor from GitHub"
PLUGIN_ICON = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpsettingsMotor/icon.png"
GITHUB_API_URL = "https://api.github.com/repos/ciefp/ciefpsettings-enigma2/contents/ciefp-E2-motor-75E-34W"
RAW_BASE_URL = "https://raw.githubusercontent.com/ciefp/ciefpsettings-enigma2/master/ciefp-E2-motor-75E-34W/"
TUXBOX_PATH = "/etc/tuxbox"
ENIGMA2_PATH = "/etc/enigma2"
LOG_PATH = "/tmp/ciefpsettings.log"

# Log helper
def log(message):
    """Write log messages to a file."""
    with open(LOG_PATH, "a") as log_file:
        log_file.write(f"{message}\n")
    print(message)

# File download helper
def download_file(url, destination, retries=3):
    """Download a file from a URL to the specified destination."""
    for attempt in range(retries):
        try:
            log(f"Downloading {url} to {destination} (Attempt {attempt + 1}/{retries})")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(destination, 'wb') as out_file:
                out_file.write(response.content)
            log(f"Successfully downloaded {url}")
            return
        except requests.exceptions.RequestException as e:
            log(f"Error downloading {url} (Attempt {attempt + 1}): {e}")
    log(f"Failed to download {url} after {retries} attempts.")

# Reload settings dynamically
def reload_enigma2_settings():
    """Trigger Enigma2 to reload settings dynamically."""
    try:
        eDVBDB.getInstance().reloadBouquets()
        eDVBDB.getInstance().reloadServicelist()
        log("Enigma2 settings reloaded successfully.")
    except Exception as e:
        log(f"Error reloading Enigma2 settings: {e}")

# Installation process
def install_settings():
    """Download and install settings files."""
    try:
        # Create target directories if they don't exist
        os.makedirs(TUXBOX_PATH, exist_ok=True)
        os.makedirs(ENIGMA2_PATH, exist_ok=True)

        # Fetch file list from GitHub
        log("Fetching file list from GitHub...")
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        files = response.json()

        # Process each file
        for file in files:
            if "name" not in file:
                log(f"Skipping entry without a name: {file}")
                continue
            file_name = file["name"]
            file_url = urljoin(RAW_BASE_URL, file_name)
            log(f"Detected file: {file_name}")

            if file_name == "satellites.xml":
                # Place satellites.xml in /etc/tuxbox
                destination = os.path.join(TUXBOX_PATH, file_name)
                download_file(file_url, destination)
            elif file_name.endswith((".tv", ".radio", "lamedb")):
                # Place .tv, .radio, and lamedb files in /etc/enigma2
                destination = os.path.join(ENIGMA2_PATH, file_name)
                download_file(file_url, destination)
            else:
                log(f"Skipping unsupported file type: {file_name}")

        # Reload Enigma2 settings dynamically
        reload_enigma2_settings()

    except requests.exceptions.RequestException as e:
        log(f"Error fetching file list from GitHub: {e}")
    except Exception as e:
        log(f"Unexpected error: {e}")

# Screen class with logo
from Components.Pixmap import Pixmap  # Dodajemo import za Pixmap

class CiefpSettingsScreen(Screen):
    skin = """
    <screen name="CiefpSettingsScreen" position="center,center" size="900,540" title="Ciefp Settings Motor">
        <widget name="logo" position="10,10" size="900,400" transparent="1" alphatest="on" />
        <widget name="status" position="10,460" size="880,60" font="Regular;26" halign="center" valign="center" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        # Koristimo Pixmap za logotip
        self["logo"] = Pixmap()
        self["status"] = Label("Ready to install settings press OK on your remote then wait ...")
        self["actions"] = ActionMap(
            ["OkCancelActions"],
            {
                "ok": self.download_and_install,
                "cancel": self.close,
            },
        )
        self.timer = eTimer()
        self.timer.callback.append(self.auto_close)

        # Postavljamo logotip nakon inicijalizacije
        self.onLayoutFinish.append(self.set_logo)

    def set_logo(self):
        logo_path = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpsettingsMotor/logo.png"
        if os.path.exists(logo_path):
            self["logo"].instance.setPixmapFromFile(logo_path)  # Prikazujemo sliku ako postoji

    def download_and_install(self):
        self["status"].setText("Downloading and installing settings...")
        try:
            install_settings()
            self["status"].setText("Installation completed! Settings reloaded.")
        except Exception as e:
            self["status"].setText(f"Error: {e}")
        self.timer.start(5000, True)

    def auto_close(self):
        self.close()



# Plugin entry points
def main(session, **kwargs):
    session.open(CiefpSettingsScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=PLUGIN_NAME,
            description=f"{PLUGIN_DESC} ({PLUGIN_VERSION})",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=PLUGIN_ICON,
            fnc=main,
        )
    ]
