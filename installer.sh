#!/bin/bash
# setup command=wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpsettingsMotor/main/installer.sh -O - | /bin/sh

VERSION='1.2'
CHANGELOG='\nFix little bugs\nUpdated Picons List'

PLUGIN_URL="https://github.com/ciefp/CiefpsettingsMotor/archive/refs/heads/main.tar.gz"
TMPPATH="/tmp/CiefpsettingsMotor"
PLUGINPATH="/usr/lib/enigma2/python/Plugins/Extensions/CiefpsettingsMotor"

if [ -d /usr/lib64 ]; then
    PLUGINPATH="/usr/lib64/enigma2/python/Plugins/Extensions/CiefpsettingsMotor"
fi

echo "Detecting Python version..."
if python3 --version &>/dev/null; then
    echo "You have Python3 image"
    PYTHON="PY3"
    Packagerequests="python3-requests"
    Packagesix="python3-six"
else
    echo "You have Python2 image"
    PYTHON="PY2"
    Packagerequests="python-requests"
fi

echo "Checking dependencies..."
if grep -qs "Package: $Packagesix" /var/lib/dpkg/status || grep -qs "Package: $Packagesix" /var/lib/opkg/status; then
    echo "Dependency $Packagesix found."
else
    echo "Installing $Packagesix..."
    opkg update && opkg install $Packagesix
fi

if grep -qs "Package: $Packagerequests" /var/lib/dpkg/status || grep -qs "Package: $Packagerequests" /var/lib/opkg/status; then
    echo "Dependency $Packagerequests found."
else
    echo "Installing $Packagerequests..."
    opkg update && opkg install $Packagerequests
fi

echo "Preparing installation..."
[ -d "$TMPPATH" ] && rm -rf "$TMPPATH"
mkdir -p "$TMPPATH"

echo "Downloading plugin..."
cd "$TMPPATH"
wget "$PLUGIN_URL" -O main.tar.gz
if [ $? -ne 0 ]; then
    echo "Error downloading plugin."
    exit 1
fi

echo "Extracting plugin..."
tar -xzf main.tar.gz
cp -r ciefpsettingsMotor-main/usr /

if [ ! -f /etc/enigma2/CiefpsettingsMotor/user_config.ini ]; then
    mkdir -p /etc/enigma2/CiefpsettingsMotor
    cp "${PLUGINPATH}/user/user_config.ini" /etc/enigma2/CiefpsettingsMotor/user_config.ini
fi

echo "Cleaning up..."
rm -rf "$TMPPATH"

if [ ! -d "$PLUGINPATH" ]; then
    echo "Error: Plugin installation failed!"
    exit 1
fi

echo "#########################################################"
echo "#    CiefpsettingsMotor INSTALLED SUCCESSFULLY          #"
echo "#                 developed by Qu4k3                    #"
echo "#                                                       #"
echo "#                  https://Sat-Club.EU                  #"
echo "#########################################################"
echo "Restarting Enigma2..."
killall -9 enigma2
exit 0
