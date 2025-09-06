#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

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

# === GENERAR CLAVE RSA PARA SSH ===
print("🔑 Generando clave RSA para SSH...")

ssh_dir_host = Path.home() / ".ssh"
ssh_dir_host.mkdir(mode=0o700, exist_ok=True)

private_key = ssh_dir_host / "rpi"
public_key = ssh_dir_host / "rpi.pub"

if not private_key.exists():
    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", str(private_key), "-N", ""], check=True)
    print(f"Clave RSA generada en {private_key}")
else:
    print(f"Clave RSA existente encontrada en {private_key}")

# Copiar clave pública al dispositivo SD para SSH
ssh_dir_device = os.path.join(home_path, ".ssh")
os.makedirs(ssh_dir_device, exist_ok=True)
authorized_keys = os.path.join(ssh_dir_device, "authorized_keys")

with open(public_key, 'r') as pub:
    pub_key_data = pub.read()

with open(authorized_keys, 'w') as auth:
    auth.write(pub_key_data)
os.chmod(authorized_keys, 0o600)

print(f"Clave pública copiada a {authorized_keys} para acceso SSH sin contraseña.")
print("✅ ROOT configurado correctamente con SSH.")

print("\n🎉 La tarjeta SD ha sido configurada con éxito.")
