import json
import board
import busio
import digitalio
import adafruit_ina260
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_requests as requests
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket

# Load configuration from config.json
with open("/config.json", "r") as f:
    config = json.load(f)

# Extract configuration items
network_config = config['network']
postgresql_url = config['postgresql']['url']
device_id = config['device']['device_id']
location = config['device']['location']

# Network Configuration
mac = tuple(network_config['mac'])
ip_address = tuple(network_config['ip'])
subnet_mask = tuple(network_config['subnet'])
gateway_address = tuple(network_config['gateway'])
dns_server = tuple(network_config['dns'])

# SPI0 and Reset pin setup
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17
W5x00_RSTn = board.GP20

# Setup I2C for INA260
i2c = busio.I2C(board.GP1, board.GP0)
ina260 = adafruit_ina260.INA260(i2c)

# LED for status indication
led = digitalio.DigitalInOut(board.GP25)
led.direction = digitalio.Direction.OUTPUT

# Ethernet reset pin setup
ethernetRst = digitalio.DigitalInOut(W5x00_RSTn)
ethernetRst.direction = digitalio.Direction.OUTPUT

# SPI bus and chip select setup
cs = digitalio.DigitalInOut(SPI0_CSn)
spi_bus = busio.SPI(SPI0_SCK, MOSI=SPI0_TX, MISO=SPI0_RX)

# Reset W5500 and initialize ethernet interface
ethernetRst.value = False
time.sleep(1)
ethernetRst.value = True
eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=mac)

# Set network configuration
eth.ifconfig = (ip_address, subnet_mask, gateway_address, dns_server)

# Initialize requests object
requests.set_socket(socket, eth)

# Serial print ethernet values
print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Function to send power data to PostgREST (and then to PostgreSQL)
def send_power_data(device_id, voltage, current, power, timestamp):
    data = {
        "device_id": device_id,
        "location": location,
        "voltage": voltage,
        "current": current,
        "power": power,
        "timestamp": timestamp
    }
    try:
        response = requests.post(postgresql_url, json=data)
        print("Sent data to PostgREST:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data to PostgREST:", e)

# Main loop
while True:
    try:
        # Read sensor values
        voltage = ina260.voltage
        current = ina260.current
        power = ina260.power
        timestamp = time.time()  # Current time in seconds since the epoch

        # Print readings
        print("Voltage: {:.2f} V".format(voltage))
        print("Current: {:.2f} mA".format(current * 1000))
        print("Power: {:.2f} mW".format(power * 1000))

        # Send data to PostgREST
        send_power_data(device_id, voltage, current, power, timestamp)

    except Exception as e:
        print("Error:", e)

    # Wait for 10 seconds before next reading
    time.sleep(10)
