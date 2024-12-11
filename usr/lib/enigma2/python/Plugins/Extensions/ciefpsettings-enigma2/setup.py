from distutils.core import setup

setup(
    name="ciefpsettings-enigma2",
    version="1.2",
    description="Download and install ciefpsettings motor from GitHub",
    packages=["ciefpsettings-enigma2"],
    package_data={"ciefpsettings-enigma2": ["icon.png", "screens/*.py", "locale/en/LC_MESSAGES/*.mo"]},
)
