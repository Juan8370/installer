#!/usr/bin/python3
import subprocess
import sys
import os
import shutil

# Definimos las librerías necesarias en una lista
REQUIRED_PACKAGES = ['git', 'nodejs', 'npm','python3-dateutil']
BASE_PATH = '/usr/local/device'

def system_update_and_upgrade():
    '''Se realiza la actualizacion del software de la maquina'''
    print("Actualizando lista de paquetes y mejorando el sistema...")
    try:
        subprocess.run(['apt', 'update'], check=True)
        subprocess.run(['apt', 'upgrade', '-y'], check=True)
        print("Sistema actualizado correctamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error durante la actualización del sistema: {e}")
        sys.exit(1)
def check_and_install(packages):
    '''Se realiza la instalacion de las dependencias necesarias'''
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
    """ Verifica o crea el directorio base y lo asigna como directorio actual (CWD) """
    if not os.path.exists(base_path):
        try:
            os.makedirs(base_path)
            print(f"Directorio base creado: {base_path}")
           
            # Solicitar nombre del dispositivo y crear device.id
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
    """ Crea los subdirectorios necesarios dentro del directorio base """
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
    """
    Clona un repositorio en el path especificado.
    Si ya existe, realiza un pull para actualizarlo.
    """
    full_path = os.path.join(os.getcwd(), install_path)
   
    if os.path.exists(full_path):
        print(f"El repositorio ya existe en: {full_path}")
       
        # Nos aseguramos de que el directorio sea un repositorio válido
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
    """
    Copia una lista de archivos desde un directorio origen a un directorio destino.
    Crea la estructura completa del directorio si no existe.
    """
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
            # Verificamos si el directorio padre existe en el destino, si no, lo creamos.
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
        # Asignar permisos de ejecución al script
        print(f"Asignando permisos de ejecución al archivo: {service_file_path}")
        subprocess.run(['chmod', '+x', service_file_path], check=True)

        # Si el enlace ya existe, eliminarlo primero
        if os.path.islink(target_link) or os.path.exists(target_link):
            os.remove(target_link)
            print(f"Eliminado enlace o archivo previo: {target_link}")

        # Crear enlace simbólico
        subprocess.run(['ln', '-s', service_file_path, target_link], check=True)
        print(f"Enlace simbólico creado: {target_link}")

        # Recargar systemd para detectar el nuevo servicio
        subprocess.run(['systemctl', 'daemon-reload'], check=True)

        # Habilitar el servicio para que arranque al inicio
        subprocess.run(['systemctl', 'enable', service_filename], check=True)

        # Iniciar el servicio ahora
        subprocess.run(['systemctl', 'start', service_filename], check=True)

        print(f"Servicio {service_filename} habilitado e iniciado correctamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al registrar o iniciar el servicio: {e}")
        sys.exit(1)

def overwrite_file(file_path, content):
    """
    Sobrescribe un archivo con el contenido especificado.
   
    :param file_path: Ruta completa del archivo a sobrescribir.
    :param content: Contenido nuevo que se escribirá en el archivo.
    """
    try:
        with open(file_path, 'w') as file:
            file.write(content)
            print(f"Archivo sobrescrito exitosamente: {file_path}")
    except PermissionError:
        print(f"No se pudo sobrescribir el archivo: {file_path}. Permiso denegado.")
    except Exception as e:
        print(f"Error al sobrescribir el archivo: {e}")

def create_file(directory, filename, content):
    """
    Crea un archivo con el contenido especificado en el directorio indicado.
   
    :param directory: Ruta del directorio donde se creará el archivo.
    :param filename: Nombre del archivo a crear.
    :param content: Contenido que se escribirá en el archivo.
    """
    try:
        # Asegurarse de que el directorio exista
        os.makedirs(directory, exist_ok=True)
       
        # Ruta completa del archivo
        file_path = os.path.join(directory, filename)
       
        # Crear y escribir el archivo
        with open(file_path, 'w') as file:
            file.write(content)
       
        print(f"Archivo creado exitosamente: {file_path}")
    except PermissionError:
        print(f"Permiso denegado al crear el archivo en: {directory}")
    except Exception as e:
        print(f"Error al crear el archivo: {e}")


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

    # Reemplazar el usuario estático por el usuario actual
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
    DIRECTORIES= {'python','services','services/dispenser'}
    file_list= {'dispenser.sh','dispenser.json','dispenser.service'}
    ensure_base_directory(BASE_PATH)
    create_directories(DIRECTORIES)
    clone_repository('python/dispenser', 'https://iot.infomediaservice.com/git/python/dispenser-2.4.git')
    copy_files(file_list, '/usr/local/device/python/dispenser/bash', '/usr/local/device/services/dispenser')
    register_and_start_service('/usr/local/device/services/dispenser/dispenser.service')
    print(NOTA)

def accion_vmachine():
    print("Ejecutando acción para VMachine...")

def accion_locker():
    print("Ejecutando acción para Locker...")

def menu():
    options = [
        "ipc.control",
        "ipc.xgraphic",
        "dispenser",
        "VMachine",
        "Locker",
        "Exit"
    ]

    print("Seleccine el servicio a instalar:")
    print("")
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")

    while True:
        try:
            choice = int(input("Ingresa el número de la opción: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print(f"Por favor ingresa un número entre 1 y {len(options)}.")
        except ValueError:
            print("Entrada inválida. Por favor ingresa un número.")

def main():

    if os.geteuid() != 0:
        print("Este script debe ejecutarse como root.")
        sys.exit(1)
    system_update_and_upgrade()
    check_and_install(REQUIRED_PACKAGES)
    while True:
        seleccion = menu()

        if seleccion == "ipc.control":
            accion_ipc_control()
        elif seleccion == "ipc.xgraphic":
            accion_ipc_xgraphic()
        elif seleccion == "dispenser":
            accion_dispenser()
        elif seleccion == "VMachine":
            accion_vmachine()
        elif seleccion == "Locker":
            accion_locker()
        elif seleccion == "Exit":
             sys.exit(1)

if __name__ == "__main__":
   
    main()


