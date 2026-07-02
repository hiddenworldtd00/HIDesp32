"""
Contrôleur ESP32 - Gestion complète des fonctionnalités ESP32
"""
import serial
import serial.tools.list_ports
import time
import threading
import json
from typing import Callable, Optional, Dict, List

class ESP32Controller:
    """Contrôleur principal pour les opérations ESP32"""
    
    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.connected = False
        self.port_name = ""
        self.callbacks: Dict[str, List[Callable]] = {}
        self.read_thread: Optional[threading.Thread] = None
        self.running = False
        self.device_info = {}
        
    def scan_ports(self) -> List[Dict]:
        """Scanne tous les ports série disponibles"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'vid': port.vid,
                'pid': port.pid
            })
        return ports
    
    def find_esp32_port(self) -> Optional[str]:
        """Trouve automatiquement le port ESP32"""
        for port in serial.tools.list_ports.comports():
            # ESP32 utilise généralement des chips CP210x, CH340, ou FTDI
            if any(x in port.description.lower() for x in 
                   ['cp210', 'ch340', 'ch341', 'ftdi', 'usb-serial', 'uart']):
                return port.device
            # Vérification par VID/PID
            if port.vid in [0x10C4, 0x1A86, 0x0403]:  # Silicon Labs, QinHeng, FTDI
                return port.device
        return None
    
    def connect(self, port: str, baudrate: int = 115200, timeout: int = 2) -> bool:
        """Connecte à l'ESP32"""
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=2
            )
            self.port_name = port
            self.connected = True
            self.running = True
            
            # Démarrer le thread de lecture
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            # Envoyer commande d'identification
            time.sleep(0.5)
            self.send_command("IDENTIFY")
            
            return True
        except Exception as e:
            print(f"Erreur connexion: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Déconnecte l'ESP32"""
        self.running = False
        self.connected = False
        if self.read_thread:
            self.read_thread.join(timeout=1)
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_port = None
    
    def _read_loop(self):
        """Boucle de lecture des données série"""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        self._process_received_data(data)
            except Exception as e:
                if self.running:
                    print(f"Erreur lecture: {e}")
            time.sleep(0.01)
    
    def _process_received_data(self, data: str):
        """Traite les données reçues de l'ESP32"""
        try:
            # Essayer de parser comme JSON
            if data.startswith('{'):
                json_data = json.loads(data)
                self._trigger_callback('data', json_data)
            else:
                self._trigger_callback('raw', data)
                
                # Détection des informations device
                if "ESP32" in data or "Chip" in data:
                    self.device_info['chip'] = data
        except:
            self._trigger_callback('raw', data)
    
    def send_command(self, command: str, params: Optional[Dict] = None) -> bool:
        """Envoie une commande à l'ESP32"""
        if not self.connected or not self.serial_port:
            return False
        
        try:
            if params:
                cmd = json.dumps({"cmd": command, "params": params}) + "\n"
            else:
                cmd = command + "\n"
            
            self.serial_port.write(cmd.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Erreur envoi commande: {e}")
            return False
    
    def register_callback(self, event: str, callback: Callable):
        """Enregistre un callback pour un événement"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, data):
        """Déclenche les callbacks pour un événement"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Erreur callback: {e}")
    
    # === FONCTIONNALITÉS ESP32 ===
    
    def set_gpio(self, pin: int, state: bool):
        """Contrôle une broche GPIO"""
        return self.send_command("GPIO_SET", {"pin": pin, "state": state})
    
    def read_gpio(self, pin: int):
        """Lit l'état d'une broche GPIO"""
        return self.send_command("GPIO_READ", {"pin": pin})
    
    def set_pwm(self, pin: int, duty: int, frequency: int = 1000):
        """Configure PWM sur une broche"""
        return self.send_command("PWM_SET", {
            "pin": pin, 
            "duty": duty, 
            "freq": frequency
        })
    
    def read_adc(self, pin: int):
        """Lit la valeur ADC"""
        return self.send_command("ADC_READ", {"pin": pin})
    
    def set_dac(self, pin: int, value: int):
        """Configure la sortie DAC"""
        return self.send_command("DAC_SET", {"pin": pin, "value": value})
    
    def scan_i2c(self):
        """Scanne les périphériques I2C"""
        return self.send_command("I2C_SCAN")
    
    def scan_wifi(self):
        """Scanne les réseaux WiFi"""
        return self.send_command("WIFI_SCAN")
    
    def connect_wifi(self, ssid: str, password: str):
        """Connecte au WiFi"""
        return self.send_command("WIFI_CONNECT", {
            "ssid": ssid, 
            "password": password
        })
    
    def start_ap(self, ssid: str, password: str, channel: int = 1):
        """Démarre un point d'accès"""
        return self.send_command("WIFI_AP", {
            "ssid": ssid,
            "password": password,
            "channel": channel
        })
    
    def start_bluetooth(self):
        """Démarre le Bluetooth"""
        return self.send_command("BT_START")
    
    def send_bluetooth(self, data: str):
        """Envoie des données Bluetooth"""
        return self.send_command("BT_SEND", {"data": data})
    
    def start_ble(self):
        """Démarre le BLE"""
        return self.send_command("BLE_START")
    
    def set_ble_service(self, uuid: str, characteristics: List[Dict]):
        """Configure un service BLE"""
        return self.send_command("BLE_SERVICE", {
            "uuid": uuid,
            "characteristics": characteristics
        })
    
    def start_webserver(self, port: int = 80):
        """Démarre un serveur web"""
        return self.send_command("WEB_START", {"port": port})
    
    def send_web_response(self, client_id: int, data: str):
        """Envoie une réponse web"""
        return self.send_command("WEB_RESPOND", {
            "client": client_id,
            "data": data
        })
    
    def deep_sleep(self, seconds: int):
        """Met en veille profonde"""
        return self.send_command("DEEP_SLEEP", {"seconds": seconds})
    
    def light_sleep(self, seconds: int):
        """Met en veille légère"""
        return self.send_command("LIGHT_SLEEP", {"seconds": seconds})
    
    def get_chip_info(self):
        """Obtient les informations du chip"""
        return self.send_command("CHIP_INFO")
    
    def restart(self):
        """Redémarre l'ESP32"""
        return self.send_command("RESTART")
    
    def set_cpu_frequency(self, freq_mhz: int):
        """Définit la fréquence CPU"""
        return self.send_command("CPU_FREQ", {"freq": freq_mhz})
    
    def get_free_heap(self):
        """Obtient la mémoire libre"""
        return self.send_command("FREE_HEAP")
    
    def read_temperature(self):
        """Lit la température interne"""
        return self.send_command("TEMP_READ")
    
    def read_hall_sensor(self):
        """Lit le capteur Hall"""
        return self.send_command("HALL_READ")
    
    def touch_read(self, pin: int):
        """Lit le capteur tactile"""
        return self.send_command("TOUCH_READ", {"pin": pin})
    
    def dac_cosine_wave(self, pin: int, frequency: int, amplitude: int = 255):
        """Génère une onde cosinus sur DAC"""
        return self.send_command("DAC_COSINE", {
            "pin": pin,
            "freq": frequency,
            "amp": amplitude
        })
    
    def ledc_setup(self, channel: int, frequency: int, resolution: int):
        """Configure LEDC"""
        return self.send_command("LEDC_SETUP", {
            "channel": channel,
            "freq": frequency,
            "resolution": resolution
        })
    
    def ledc_attach_pin(self, pin: int, channel: int):
        """Attache une broche à LEDC"""
        return self.send_command("LEDC_ATTACH", {
            "pin": pin,
            "channel": channel
        })
    
    def ledc_write(self, channel: int, duty: int):
        """Écrit une valeur LEDC"""
        return self.send_command("LEDC_WRITE", {
            "channel": channel,
            "duty": duty
        })
    
    def rmt_tx(self, pin: int, data: List[int], frequency: int = 38000):
        """Transmission RMT (Remote Control)"""
        return self.send_command("RMT_TX", {
            "pin": pin,
            "data": data,
            "freq": frequency
        })
    
    def rmt_rx(self, pin: int, timeout: int = 1000):
        """Réception RMT"""
        return self.send_command("RMT_RX", {
            "pin": pin,
            "timeout": timeout
        })
    
    def sigma_delta_setup(self, pin: int, channel: int):
        """Configure Sigma-Delta"""
        return self.send_command("SIGMA_DELTA_SETUP", {
            "pin": pin,
            "channel": channel
        })
    
    def sigma_delta_write(self, channel: int, duty: int):
        """Écrit Sigma-Delta"""
        return self.send_command("SIGMA_DELTA_WRITE", {
            "channel": channel,
            "duty": duty
        })
    
    def mcpwm_setup(self, unit: int, timer: int, frequency: int):
        """Configure MCPWM"""
        return self.send_command("MCPWM_SETUP", {
            "unit": unit,
            "timer": timer,
            "freq": frequency
        })
    
    def pcnt_setup(self, unit: int, channel: int, pin: int):
        """Configure PCNT (Pulse Counter)"""
        return self.send_command("PCNT_SETUP", {
            "unit": unit,
            "channel": channel,
            "pin": pin
        })
    
    def i2s_setup(self, port: int, mode: str, sample_rate: int, bits: int):
        """Configure I2S"""
        return self.send_command("I2S_SETUP", {
            "port": port,
            "mode": mode,
            "sample_rate": sample_rate,
            "bits": bits
        })
    
    def spi_setup(self, host: int, mosi: int, miso: int, sck: int, cs: int):
        """Configure SPI"""
        return self.send_command("SPI_SETUP", {
            "host": host,
            "mosi": mosi,
            "miso": miso,
            "sck": sck,
            "cs": cs
        })
    
    def uart_setup(self, port: int, tx: int, rx: int, baudrate: int):
        """Configure UART"""
        return self.send_command("UART_SETUP", {
            "port": port,
            "tx": tx,
            "rx": rx,
            "baudrate": baudrate
        })
    
    def twai_setup(self, tx: int, rx: int, baudrate: int = 125000):
        """Configure TWAI (CAN)"""
        return self.send_command("TWAI_SETUP", {
            "tx": tx,
            "rx": rx,
            "baudrate": baudrate
        })
    
    def secure_boot_enable(self):
        """Active le Secure Boot"""
        return self.send_command("SECURE_BOOT_ENABLE")
    
    def flash_encryption_enable(self):
        """Active le chiffrement Flash"""
        return self.send_command("FLASH_ENC_ENABLE")
    
    def efuse_read(self, block: int):
        """Lit un bloc eFuse"""
        return self.send_command("EFUSE_READ", {"block": block})
    
    def nvs_read(self, namespace: str, key: str):
        """Lit depuis NVS"""
        return self.send_command("NVS_READ", {
            "namespace": namespace,
            "key": key
        })
    
    def nvs_write(self, namespace: str, key: str, value: str):
        """Écrit dans NVS"""
        return self.send_command("NVS_WRITE", {
            "namespace": namespace,
            "key": key,
            "value": value
        })
    
    def ota_update(self, url: str):
        """Met à jour via OTA"""
        return self.send_command("OTA_UPDATE", {"url": url})
    
    def mdns_setup(self, hostname: str, service: str, port: int):
        """Configure mDNS"""
        return self.send_command("MDNS_SETUP", {
            "hostname": hostname,
            "service": service,
            "port": port
        })
    
    def sntp_sync(self, server: str = "pool.ntp.org"):
        """Synchronise l'heure via SNTP"""
        return self.send_command("SNTP_SYNC", {"server": server})
