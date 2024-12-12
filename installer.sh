#!/bin/bash
##setup command=wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpsettingsMotor/main/installer.sh -O - | /bin/sh

######### Only This 2 lines to edit with new version ######
version='1.3'
changelog='\nFix little bugs\nUpdated Picons List'
##############################################################

TMPPATH=/tmp/CiefpsettingsMotor

if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/CiefpsettingsMotor
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/CiefpsettingsMotor
fi

# check depends packages
if [ -f /var/lib/dpkg/status ]; then
   STATUS=/var/lib/dpkg/status
   OSTYPE=DreamOs
else
   STATUS=/var/lib/opkg/status
   OSTYPE=Dream
fi
echo ""
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "You have Python3 image"
    PYTHON=PY3
    Packagesix=python3-six
    Packagerequests=python3-requests
else
    echo "You have Python2 image"
    PYTHON=PY2
    Packagerequests=python-requests
fi

if [ $PYTHON = "PY3" ]; then
    if grep -qs "Package: $Packagesix" $STATUS ; then
        echo "Dependency python3-six found."
    else
        opkg update && opkg install python3-six
    fi
fi
echo ""
if grep -qs "Package: $Packagerequests" $STATUS ; then
    echo "Dependency $Packagerequests found."
else
    echo "Need to install $Packagerequests"
    echo ""
    if [ $OSTYPE = "DreamOs" ]; then
        apt-get update && apt-get install python-requests -y
    elif [ $PYTHON = "PY3" ]; then
        opkg update && opkg install python3-requests
    elif [ $PYTHON = "PY2" ]; then
        opkg update && opkg install python-requests
    fi
fi
echo ""

## Remove tmp directory
[ -d $TMPPATH ] && rm -rf $TMPPATH

## Remove old plugin directory
[ -d $PLUGINPATH ] && rm -rf $PLUGINPATH

# Download and install plugin
mkdir -p $TMPPATH
cd $TMPPATH
set -e
if [ -f /var/lib/dpkg/status ]; then
   echo "# Your image is OE2.5/2.6 #"
   echo ""
   echo ""
else
   echo "# Your image is OE2.0 #"
   echo ""
   echo ""
fi

# Download and extract
wget https://github.com/ciefp/CiefpsettingsMotor/archive/refs/heads/main.tar.gz
tar -xzf main.tar.gz

# Verify directory exists before copying
if [ -d "CiefpsettingsMotor-main/usr" ]; then
    cp -r CiefpsettingsMotor-main/usr /
else
    echo "Error: Directory 'CiefpsettingsMotor-main/usr' does not exist."
    exit 1
fi

# Create configuration file if not exists
if [ ! -f /etc/enigma2/CiefpsettingsMotor/user_config.ini ]; then
    mkdir -p /etc/enigma2/CiefpsettingsMotor
    cp -r ${PLUGINPATH}/user/user_config.ini /etc/enigma2/CiefpsettingsMotor/user_config.ini
fi

set +e
cd
sleep 2

### Check if plugin installed correctly
if [ ! -d $PLUGINPATH ]; then
    echo "Something went wrong... Plugin not installed"
    exit 1
fi

rm -rf $TMPPATH > /dev/null 2>&1
sync
echo ""
echo ""
echo "#########################################################"
echo "#    CiefpsettingsMotor INSTALLED SUCCESSFULLY          #"
echo "#                 developed by Qu4k3                    #"
echo "#                                                       #"
echo "#                  https://Sat-Club.EU                  #"
echo "#########################################################"
echo "#           your Device will RESTART Now                #"
echo "#########################################################"
sleep 5
killall -9 enigma2
exit 0
