from distutils.core import setup

setup(
    name="CiefpsettingsMotor",
    version="2.1",
    description="Download and install ciefpsettings motor from GitHub",
    packages=["CiefpsettingsMotor"],
    package_data={"CiefpsettingsMotor": ["icon.png", "screens/*.py", "locale/en/LC_MESSAGES/*.mo"]},
)
