#!/usr/bin/python3
import subprocess
import sys
import os
import shutil
import argparse
import stat

# Definimos las librerías necesarias en una lista
REQUIRED_PACKAGES = ['git', 'nodejs', 'npm', 'python3-dateutil']
BASE_PATH = '/usr/local/device'

def system_update_and_upgrade():
    print("Actualizando lista de paquetes y mejorando el sistema...")
    try:
        #subprocess.run(['apt', 'update'], check=True)
        #subprocess.run(['apt', 'upgrade', '-y'], check=True)
        print("Sistema actualizado correctamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error durante la actualización del sistema: {e}")
        sys.exit(1)

def check_and_install(packages):
    for package in packages:
        print(f"Verificando: {package}")
        result = subprocess.run(['dpkg', '-s', package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode != 0:
            print(f"{package} no está instalado. Instalando...")
            try:
                subprocess.run(['apt', 'install', '-y', package], check=True)
                print(f"{package} instalado correctamente.")
            except subprocess.CalledProcessError as e:
                print(f"Error al instalar {package}: {e}")
                sys.exit(1)
        else:
            print(f"{package} ya está instalado.")

def ensure_base_directory(base_path):
    if not os.path.exists(base_path):
        try:
            os.makedirs(base_path)
            print(f"Directorio base creado: {base_path}")
            device_name = input("Introduce el nombre del dispositivo: ").strip()
            device_id_path = os.path.join(base_path, "device.id")
            with open(device_id_path, "w") as f:
                f.write(device_name + "\n")
            print(f"Archivo device.id creado en: {device_id_path}")
        except PermissionError:
            print(f"No se pudo crear el directorio base: {base_path}. Permiso denegado.")
            sys.exit(1)
    else:
        print(f"El directorio base ya existe: {base_path}")
    os.chdir(base_path)
    print(f"Directorio actual asignado: {os.getcwd()}")

def create_directories(directories):
    for directory in directories:
        path = os.path.join(os.getcwd(), directory)
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                print(f"Directorio creado: {path}")
            except PermissionError:
                print(f"No se pudo crear el directorio: {path}. Permiso denegado.")
                sys.exit(1)
        else:
            print(f"El directorio ya existe: {path}")

def clone_repository(install_path, repo_url):
    full_path = os.path.join(os.getcwd(), install_path)
    if os.path.exists(full_path):
        print(f"El repositorio ya existe en: {full_path}")
        if os.path.exists(os.path.join(full_path, ".git")):
            try:
                print(f"Actualizando el repositorio en: {full_path}")
                subprocess.run(['git', '-C', full_path, 'pull'], check=True)
                print("Repositorio actualizado exitosamente.")
            except subprocess.CalledProcessError as e:
                print(f"Error al actualizar el repositorio: {e}")
                sys.exit(1)
        else:
            print(f"El directorio {full_path} no parece ser un repositorio de Git.")
    else:
        try:
            print(f"Clonando el repositorio en: {full_path}")
            subprocess.run(['git', 'clone', repo_url, full_path], check=True)
            print("Repositorio clonado exitosamente.")
        except subprocess.CalledProcessError as e:
            print(f"Error al clonar el repositorio: {e}")
            sys.exit(1)

def copy_files(file_list, source_path, destination_path):
    if not os.path.exists(destination_path):
        try:
            os.makedirs(destination_path, exist_ok=True)
            print(f"Directorio destino creado: {destination_path}")
        except PermissionError:
            print(f"No se pudo crear el directorio: {destination_path}. Permiso denegado.")
            sys.exit(1)
    for file_name in file_list:
        src_file = os.path.join(source_path, file_name)
        dest_file = os.path.join(destination_path, file_name)
        if os.path.exists(src_file):
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(src_file, dest_file)
            print(f"Archivo copiado: {src_file} -> {dest_file}")
        else:
            print(f"El archivo {file_name} no existe en el directorio origen.")

def register_and_start_service(service_file_path):
    if not os.path.isfile(service_file_path):
        print(f"Error: El archivo {service_file_path} no existe.")
        sys.exit(1)
    service_filename = os.path.basename(service_file_path)
    target_link = os.path.join("/etc/systemd/system", service_filename)
    try:
        print(f"Asignando permisos de ejecución al archivo: {service_file_path}")
        subprocess.run(['chmod', '+x', service_file_path], check=True)
        if os.path.islink(target_link) or os.path.exists(target_link):
            os.remove(target_link)
            print(f"Eliminado enlace o archivo previo: {target_link}")
        subprocess.run(['ln', '-s', service_file_path, target_link], check=True)
        print(f"Enlace simbólico creado: {target_link}")
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'enable', service_filename], check=True)
        subprocess.run(['systemctl', 'start', service_filename], check=True)
        print(f"Servicio {service_filename} habilitado e iniciado correctamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al registrar o iniciar el servicio: {e}")
        sys.exit(1)

def overwrite_file(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
            print(f"Archivo sobrescrito exitosamente: {file_path}")
    except PermissionError:
        print(f"No se pudo sobrescribir el archivo: {file_path}. Permiso denegado.")
    except Exception as e:
        print(f"Error al sobrescribir el archivo: {e}")

def create_file(directory, filename, content):
    try:
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, filename)
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Archivo creado exitosamente: {file_path}")
    except PermissionError:
        print(f"Permiso denegado al crear el archivo en: {directory}")
    except Exception as e:
        print(f"Error al crear el archivo: {e}")

def copy_directory(source_path, destination_path):
    """
    Copia recursivamente un directorio completo.
    Si el destino existe, lo sobrescribe.
    """
    try:
        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
        print(f"Directorio copiado: {source_path} -> {destination_path}")
    except PermissionError:
        print(f"No se pudo copiar el directorio: {destination_path}. Permiso denegado.")
        sys.exit(1)
    except Exception as e:
        print(f"Error al copiar directorio: {e}")
        sys.exit(1)

def set_executable(file_path):
    try:
        subprocess.run(['chmod', '+x', file_path])
        print(f"Permiso de ejecución asignado a: {file_path}")
    except Exception as e:
        print(f"Error al asignar permiso de ejecución a {file_path}: {e}")

def npm_install(carpeta):
    """
    Ejecuta 'npm install' en la carpeta especificada.
    """
    if not os.path.exists(carpeta):
        print(f"Error: la carpeta {carpeta} no existe")
        sys.exit(1)
    
    try:
        print(f"Ejecutando 'npm install' en {carpeta}...")
        subprocess.run(['npm', 'install'], cwd=carpeta, check=True)
        print(f"'npm install' completado en {carpeta}")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar 'npm install' en {carpeta}: {e}")
        sys.exit(1)


def habilitar_electron():
    electron_path = "/usr/local/device/nodejs/OpenBeer/node_modules/electron/dist"
    chrome_sandbox = os.path.join(electron_path, "chrome-sandbox")

    if not os.path.exists(chrome_sandbox):
        print(f"Error: no se encuentra {chrome_sandbox}")
        sys.exit(1)

    try:
        # Cambiar propietario a root:root
        subprocess.run(['sudo', 'chown', 'root:root', chrome_sandbox], check=True)
        print(f"Propietario de {chrome_sandbox} cambiado a root:root")

        # Asignar permisos 4755 (setuid root)
        subprocess.run(['sudo', 'chmod', '4755', chrome_sandbox], check=True)
        print(f"Permisos de {chrome_sandbox} establecidos en 4755")
    except subprocess.CalledProcessError as e:
        print(f"Error al habilitar Electron: {e}")
        sys.exit(1)
# ====================
# Acciones disponibles
# ====================

def accion_ipc_control():
    DIRECTORIES= {'nodejs','services','services/ipc.control'}
    file_list= {'application.sh','config/ipc.control.json','mqtt.ipc.control.service'}
    ensure_base_directory(BASE_PATH)
    create_directories(DIRECTORIES)
    clone_repository('nodejs/ipc.control', 'https://mqtt.infomediaservice.com/git/nodejs/ipc.control.git')
    copy_files(file_list, '/usr/local/device/nodejs/ipc.control', '/usr/local/device/services/ipc.control')
    register_and_start_service('/usr/local/device/services/ipc.control/mqtt.ipc.control.service')

def accion_ipc_xgraphic():
    import getpass
    current_user = getpass.getuser()
    DIRECTORIES = ['nodejs', 'services', 'services/ipc.control']
    file_list= {'application.sh','config/ipc.xgraphic.json','mqtt.ipc.xgraphic.service','ipc.xgraphic.pid'}
    content = ''' 
    [Unit]
    Description=Service and filesystem as regular User
    After=network.target

    [Service]
    Environment="DISPLAY=:0"
    Environment="XAUTHORITY=/home/infomedia/.Xauthority"
    Type=forking
    Restart=always
    RestartSec=1
    SuccessExitStatus=143
    ExecStart=/usr/local/device/nodejs/ipc.xgraphic/application.sh start
    ExecStop=/usr/local/device/nodejs/ipc.xgraphic/application.sh stop
    ExecReload=/usr/local/device/nodejs/ipc.xgraphic/application.sh restart
    User=infomedia

    [Install]
    WantedBy=multi-user.target
    '''
    content = content.replace('User=infomedia', f'Environment="XAUTHORITY=/home/{current_user}/.Xauthority"')
    content = content.replace('User=infomedia', f'User={current_user}')
    ensure_base_directory(BASE_PATH)
    create_directories(DIRECTORIES)
    clone_repository('nodejs/ipc.xgraphic', 'https://mqtt.infomediaservice.com/git/nodejs/ipc.xgraphic.git')
    copy_files(file_list, '/usr/local/device/nodejs/ipc.xgraphic/', '/usr/local/device/services/ipc.xgraphic')
    overwrite_file('/usr/local/device/services/ipc.xgraphic/mqtt.ipc.xgraphic.service', content)
    register_and_start_service('/usr/local/device/services/ipc.xgraphic/mqtt.ipc.xgraphic.service')

def accion_dispenser():
    NOTA= '''
    NOTA:
    Recuerde cambiar la configuracion de la maquina en el archivo dispenser.json de acuerdo a las necesidades de la maquina.
    Para que funcione correctamente, se debe tener el hardware correctamente instalado.
    '''
    DIRECTORIES= {'python','services','services/dispenser-2.4'}
    file_list= {'dispenser.sh','dispenser.json','dispenser.service'}
    ensure_base_directory(BASE_PATH)
    create_directories(DIRECTORIES)
    clone_repository('python/dispenser-2.4', 'https://iot.infomediaservice.com/git/python/dispenser-2.4.git')
    copy_files(file_list, '/usr/local/device/python/dispenser-2.4/bash', '/usr/local/device/services/dispenser-2.4')
    register_and_start_service('/usr/local/device/services/dispenser-2.4/dispenser.service')
    print(NOTA)

def accion_vmachine():
    print("Ejecutando acción para VMachine...")

def accion_locker():
    print("Ejecutando acción para Locker...")

def accion_openbeer():
    import getpass
    current_user = getpass.getuser()

    DIRECTORIES = {'nodejs', 'services', 'services/dispenser.front'}
    ensure_base_directory(BASE_PATH)
    create_directories(DIRECTORIES)

    # Clonar y preparar proyecto
    clone_repository('nodejs/dispenser.front', 'https://github.com/Juan8370/dispenser.front.git')
    npm_install('nodejs/dispenser.front')
    copy_directory('/usr/local/device/nodejs/dispenser.front/dispenser.front', '/usr/local/device/services/dispenser.front')
    register_and_start_service('/usr/local/device/services/dispenser.front/dispenser.front.service')
    set_executable('/usr/local/device/services/dispenser.front/dispenser.front.sh')

    # Crear carpeta autostart si no existe
    autostart_path = f"/home/{current_user}/.config/lxsession/LXDE-pi"
    os.makedirs(autostart_path, exist_ok=True)
    desktop_file_path = os.path.join(autostart_path, "dispenser.front.desktop")

    # Contenido del archivo .desktop
    desktop_content = f"""[Desktop Entry]
Type=Application
Name=dispenser.front Kiosk
Exec=chromium-browser --noerrdialogs --disable-infobars --kiosk --incognito \\
  --disable-translate \\
  --no-first-run \\
  --fast \\
  --fast-start \\
  --disable-pinch \\
  --overscroll-history-navigation=0 \\
  --disable-features=Translate,AutofillAssistant,PasswordManager,NotificationIndicators \\
  http://127.0.0.1:5500
X-GNOME-Autostart-enabled=true
"""

    # Guardar archivo .desktop
    with open(desktop_file_path, 'w') as f:
        f.write(desktop_content)
    os.chmod(desktop_file_path, 0o755)
    print(f"Archivo de autostart creado: {desktop_file_path}")

    # Mensaje final
    print("""
NOTA:
El proyecto dispenser.front se ha instalado.
Se iniciará automáticamente en Chromium en modo kiosco al iniciar sesión en LXDE.
Recuerde revisar y ajustar la configuración en:
  /usr/local/device/services/dispenser.front/dispenser.front.json
""")



# ====================
# Main con argparse
# ====================

def main():
    if os.geteuid() != 0:
        print("Este script debe ejecutarse como root.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Instalador de servicios IoT")
    parser.add_argument(
        "servicio",
        choices=["ipc.control", "ipc.xgraphic", "dispenser", "VMachine", "Locker","openbeer"],
        help="Servicio a instalar"
    )
    args = parser.parse_args()

    system_update_and_upgrade()
    check_and_install(REQUIRED_PACKAGES)

    if args.servicio == "ipc.control":
        accion_ipc_control()
    elif args.servicio == "ipc.xgraphic":
        accion_ipc_xgraphic()
    elif args.servicio == "dispenser":
        accion_dispenser()
    elif args.servicio == "openbeer":
        accion_openbeer()
    elif args.servicio == "VMachine":
        accion_vmachine()
    elif args.servicio == "Locker":
        accion_locker()

if __name__ == "__main__":
    main()
