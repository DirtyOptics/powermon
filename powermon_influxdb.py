import time
import board
import busio
import digitalio
import adafruit_ina260
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import adafruit_requests as requests
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool  # Correct import
import json

# Load configuration from config.json
with open("/config.json", "r") as f:
    config = json.load(f)

# Extract configuration items
network_config = config['network']
influxdb_url = config['influxdb']['url']  # Updated to use InfluxDB URL
influxdb_token = config['influxdb']['token']  # Token for authentication
device_id = config['device']['device_id']
location = config['device']['location']

# Network Configuration
dhcp_enabled = network_config.get('dhcp_enabled', False)  # Static IP is configured
mac = network_config['mac']  # Use MAC address directly from the config as a string
static_ip = tuple(network_config['ip'])
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

if dhcp_enabled:
    # Try to initialize ethernet interface with DHCP
    eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=mac)

    # Check if DHCP was successful by verifying the assigned IP address
    if eth.pretty_ip(eth.ip_address) == "0.0.0.0":
        # DHCP failed, so set a static IP configuration
        print("DHCP failed, falling back to static IP.")
        eth.ifconfig = (static_ip, subnet_mask, gateway_address, dns_server)
    else:
        print("DHCP assigned IP:", eth.pretty_ip(eth.ip_address))
else:
    # Always use static IP configuration
    eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=mac)
    eth.ifconfig = (static_ip, subnet_mask, gateway_address, dns_server)
    print("Static IP configuration used:", eth.pretty_ip(eth.ip_address))

# Initialize requests object with socketpool
pool = socketpool.SocketPool(eth)  # Create a socket pool
requests_session = requests.Session(pool, eth)  # Correct way to initialize requests

# Serial print ethernet values
print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Function to send power data to InfluxDB
def send_power_data_to_influxdb(device_id, voltage, current, power, timestamp):
    # Format data in InfluxDB line protocol
    data = "power_data,device_id={} location={},voltage={:.2f},current={:.2f},power={:.2f} {}".format(
        device_id, location, voltage, current, power, int(timestamp)
    )
    
    headers = {
        "Authorization": f"Token {influxdb_token}",
        "Content-Type": "application/octet-stream"
    }
    
    try:
        response = requests_session.post(influxdb_url, headers=headers, data=data)  # Use requests_session for HTTP requests
        print("Sent data to InfluxDB:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send data to InfluxDB:", e)
        # Additional debugging information
        print(f"Error type: {type(e).__name__}, Arguments: {e.args}")

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

        # Send data to InfluxDB
        send_power_data_to_influxdb(device_id, voltage, current, power, timestamp)

    except Exception as e:
        print("Error:", e)

    # Wait for 10 seconds before next reading
    time.sleep(10)
