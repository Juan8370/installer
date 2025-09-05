#!/usr/bin/env python3
import os
import shutil
import subprocess

# === CONFIGURACIÓN PREDETERMINADA ===
BOOT_PATH = "/media/juan/bootfs"
ROOT_PATH = "/media/juan/rootfs"

USERNAME = "infomedia"
PASSWORD = "iotmedia"
SSID = "Juan Rodriguez"
WIFI_PASS = "12345678"

# === VALIDAR RUTAS ===
if not os.path.isdir(BOOT_PATH):
    print(f"❌ BOOT no existe: {BOOT_PATH}")
    exit(1)

if not os.path.isdir(ROOT_PATH):
    print(f"❌ ROOT no existe: {ROOT_PATH}")
    exit(1)

# === HOSTNAME ===
hostname = input("Nombre del dispositivo (hostname): ").strip()

# === GENERAR HASH DE CONTRASEÑA ===
print("🔐 Generando hash de contraseña...")
result = subprocess.run(['openssl', 'passwd', '-6', PASSWORD], stdout=subprocess.PIPE, text=True, check=True)
password_hash = result.stdout.strip()

# === CONFIGURAR BOOT ===
print("⚙️ Configurando BOOT...")

# Habilitar SSH
open(os.path.join(BOOT_PATH, 'ssh'), 'w').close()

# Habilitar VNC
with open(os.path.join(BOOT_PATH, 'vnc.txt'), 'w') as f:
    f.write("enabled=1\n")

# Crear userconf
with open(os.path.join(BOOT_PATH, 'userconf'), 'w') as f:
    f.write(f"{USERNAME}:{password_hash}\n")

# Configurar hostname
with open(os.path.join(BOOT_PATH, 'hostname'), 'w') as f:
    f.write(hostname + '\n')

# Configurar Wi-Fi
with open(os.path.join(BOOT_PATH, 'wpa_supplicant.conf'), 'w') as f:
    f.write(f"""country=CO
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{SSID}"
    psk="{WIFI_PASS}"
    key_mgmt=WPA-PSK
}}""")

print("✅ BOOT configurado correctamente.")

# === CONFIGURAR ROOT ===
print("⚙️ Copiando archivo iot.installer.py y creando device.id...")

# Crear carpeta home si no existe
home_path = os.path.join(ROOT_PATH, "home", USERNAME)
os.makedirs(home_path, exist_ok=True)

# Copiar el script iot.installer.py
script_src = os.path.join(os.path.dirname(__file__), "iot.installer.py")
script_dst = os.path.join(home_path, "iot.installer.py")

if not os.path.isfile(script_src):
    print(f"❌ No se encontró iot.installer.py en {script_src}")
    exit(1)

shutil.copy2(script_src, script_dst)
os.chmod(script_dst, 0o755)

# Crear /usr/local/device/device.id
device_path = os.path.join(ROOT_PATH, "usr/local/device")
os.makedirs(device_path, exist_ok=True)
with open(os.path.join(device_path, "device.id"), 'w') as f:
    f.write(hostname + '\n')

print("✅ ROOT configurado correctamente.")
print("\n🎉 La tarjeta SD ha sido configurada con éxito.")
