import time
import board
import busio
import digitalio
import adafruit_ina260
import adafruit_requests as requests
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket
import psycopg2
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K

# External configuration for network settings
NETWORK_CONFIG = {
    "mac": (0x00, 0x01, 0x02, 0x03, 0x04, 0x05),
    "ip": (192, 168, 50, 100),
    "subnet": (255, 255, 255, 0),
    "gateway": (192, 168, 50, 1),
    "dns": (8, 8, 8, 8)
}

# PostgreSQL configuration
POSTGRES_CONFIG = {
    "dbname": "powermonitor",
    "user": "your_username",
    "password": "your_password",
    "host": "your_host_ip",
    "port": "5432"
}

# Unique device identifier
DEVICE_ID = "monitor_01"  # Change this for each device

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
eth = WIZNET5K(spi_bus, cs, is_dhcp=False, mac=NETWORK_CONFIG["mac"])

# Set network configuration
eth.ifconfig = (NETWORK_CONFIG["ip"], NETWORK_CONFIG["subnet"], NETWORK_CONFIG["gateway"], NETWORK_CONFIG["dns"])

# Initialize requests object
requests.set_socket(socket, eth)

# Serial print ethernet values
print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Setup PostgreSQL connection
def connect_postgres():
    conn = psycopg2.connect(
        dbname=POSTGRES_CONFIG["dbname"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"],
        host=POSTGRES_CONFIG["host"],
        port=POSTGRES_CONFIG["port"]
    )
    return conn

# Function to insert power data into PostgreSQL
def insert_power_data(conn, device_id, voltage, current, power):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO power_data (device_id, location, voltage, current, power)
            VALUES (%s, %s, %s, %s, %s);
        """, (device_id, "office", voltage, current, power))
        conn.commit()

# Main loop
conn = connect_postgres()

while True:
    try:
        # Read sensor values
        voltage = ina260.voltage
        current = ina260.current
        power = ina260.power

        # Print readings
        print("Voltage: {:.2f} V".format(voltage))
        print("Current: {:.2f} mA".format(current * 1000))
        print("Power: {:.2f} mW".format(power * 1000))

        # Insert data into PostgreSQL
        insert_power_data(conn, DEVICE_ID, voltage, current, power)
        print("Sent data to PostgreSQL")

    except Exception as e:
        print("Error:", e)

    # Wait for 10 seconds before next reading
    time.sleep(10)
