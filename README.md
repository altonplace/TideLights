# TODO

# Configuring to run on a Raspberry pi
To run on a raspberry pi
1. Install pip `sudo apt install python3 pip`
1. Install git `sudo apt-get install git`
1. Clone the repository `git clone https://github.com/altonplace/TideLights.git`
1. Install python dependencies 
    1. `sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel --break-system-packages`
    1. `sudo python3 -m pip install --force-reinstall adafruit-blinka --break-system-packages`
1. Install Tide lights service `sudo ./TideLights/Tide_Lts/install/install.sh`

### Interact with the service

Check Status 
`sudo systemctl status tide_lts`
Stop the service 
1. Disable it `sudo systemctl disable tide_lts`
1. Stop it `sudo systemctl stop tide_lts`
Start the service
`sudo systemctl start tide_lts`
Reenable on boot (after stopping)
`sudo systemctl enable tide_lts`

