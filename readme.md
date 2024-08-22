# PowerMon v1

#### Workflow:
<kbd>Power Mon</kbd> -> <kbd>PPostgREST</kbd> -> <kbd>WPostgrSQL</kbd> -> <kbd>Grafana</kbd>

- Power Monitor: Collects data (voltage, current, power) using the W5500-EVB-Pico and INA260 sensor.
- PostgREST API: The Power Monitor sends this data via HTTP POST requests to a PostgREST endpoint.
- PostgreSQL: PostgREST handles the database interactions, inserting the received data into the appropriate table in PostgreSQL.
- Grafana: Grafana connects directly to PostgreSQL, querying the stored data to generate visualizations.

#### Circuit Python
Testing with v 9.1.1
https://circuitpython.org/board/wiznet_w5500_evb_pico/

#### Why Use PostgREST?
Simplifies CircuitPython Code: CircuitPython doesn’t natively support PostgreSQL. By using PostgREST, you can send HTTP requests, which CircuitPython supports, instead of trying to establish a direct database connection.
Decouples Application Logic: Using an API like PostgREST allows you to manage your database interactions separately, which can be beneficial for maintenance, scalability, and security.

![image](https://github.com/user-attachments/assets/49db55b6-98e4-4d5e-9223-cae198268a41)

![image](https://github.com/user-attachments/assets/1d418f4b-2c21-498d-a3a9-77d56ef51cfd)

![image](https://github.com/user-attachments/assets/057e570e-4e86-4cdd-adf8-f6acd81baa16)

![image](https://github.com/user-attachments/assets/1290b31a-7428-418c-a1e6-01e867cbc7c5)


#### Product Links:
https://docs.wiznet.io/Product/iEthernet/W5500/w5500-evb-pico
https://wiznet.io/products/evaluation-boards/w5500-evb-pico
