#!/usr/bin/env python3

"""
Archivo principal para la búsqueda de máquinas.
"""
import subprocess
import sys
import os
import hashlib
import requests
import json
from pwn import *



# Configuracion de las pwontools
context.log_level = 'info'

# Configuracion de los colores 

class colors:
    GREEN = log.success
    RED = log.failure
    BLUE = log.info
    YELLOW = log.warning
    PURPLE = log.indented
    CYAN = log.debug
    
def help_panel():
    
    log.info("\n\tEste es el panel de ayuda")
    log.info("\tu) Buscar actualizaciones de la herramienta")
    log.info("\tm) Buscar por nombre de máquina '-m <nombre>'")
    log.info("\td) Buscar por dificultad <dificultad>\n")
    log.info("\ts) Buscar por sistema operativo <sistema>\n")
    log.info("\tt) Buscar por técnica <técnica>\n")
    
    
# Función para descargar 


def download_with_progress(url, filename):
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with log.progress(f"Descargando {filename}") as p:
            with open(filename, 'wb') as file:
                downloaded = 0
                for data in response.iter_content(chunk_size=1024):
                    size = file.write(data)
                    downloaded += size
                    p.status(f"{downloaded}/{total_size} bytes ({downloaded/total_size:.1%})")
                
        return True
    except Exception as e:
        log.failure(f"Error en la descarga: {e}")
        return False
                    




# Función para actualizar archivos
def update_files():
    main_url = "https://htbmachines.github.io/bundle.js"
    
    if not os.path.exists("bundle.js"):
        log.info("\n[+] Descargando archivo por primera vez...")
        if download_with_progress(main_url, "bundle.js"): # type: ignore
            with log.progress("Formateando archivo..."):
                subprocess.run(["js-beautify", "bundle.js", "--outfile", "bundle.js"], stdout=subprocess.PIPE)
            log.success("\n[+] Archivo descargado y formateado correctamente")
    else:
        print("\n[+] Comprobando actualizaciones...")
        
        # Calcular hash del archivo actual
        with open("bundle.js", "rb") as f:
            md5_original = hashlib.md5(f.read()).hexdigest()
        
        # Descargar temporalmente con barra de progreso
        if download_with_progress(main_url, "bundle_temp.js"): # type: ignore
            with log.progress("Formateando archivo temporal..."):
                subprocess.run(["js-beautify", "bundle_temp.js", "--outfile", "bundle_temp.js"], stdout=subprocess.PIPE)
            
            # Calcular hash del nuevo archivo
            with open("bundle_temp.js", "rb") as f:
                md5_temp = hashlib.md5(f.read()).hexdigest()
            
            if md5_original == md5_temp:
                log.success("[+] No hay actualizaciones disponibles")
                os.remove("bundle_temp.js")
            else:
                log.info("[+] Actualizando archivos...")
                os.remove("bundle.js")
                os.rename("bundle_temp.js", "bundle.js")
                log.success("[+] Archivos actualizados correctamente")

# Función para buscar máquina por nombre
def search_machine(name):
    if not os.path.exists("bundle.js"):
        log.failure("[!] Primero debes descargar los datos (opción -u)")
        return
    
    log.info(f"\n[+] Buscando máquina {name}\n")
    
    try:
        with open("bundle.js", "r") as f:
            data = f.read()
            
        results = []
        lines = data.split('\n')
        found = False
        
        with log.progress("Buscando máquina...") as p:
            for i, line in enumerate(lines):
                p.status(f"Procesando línea {i+1}/{len(lines)}")
                if f'name: "{name}"' in line:
                    found = True
                elif found and 'resuelta:' in line:
                    break
                elif found:
                    results.append(line)
        
        if not results:
            log.failure(f"\n[!] No se encontró la máquina {name}\n")
        else:
            log.success(f"\n[+] Resultados para {name}:\n")
            for line in results:
                cleaned = line.strip().replace("'", "").replace(",", "")
                if not any(x in cleaned for x in ['id:', 'sku:', 'resuelta:']):
                    log.indented(cleaned)
    except Exception as e:
        log.failure(f"Error en la búsqueda: {e}")

# Función para buscar por dificultad
def search_difficulty(difficulty):
    if not os.path.exists("bundle.js"):
        log.failure("[!] Primero debes descargar los datos (opción -u)")
        return
    
    levels = {
        "insane": (log.failure, "Insane"),
        "difícil": (log.warning, "Difícil"),
        "fácil": (log.success, "Fácil")
    }
    
    log.info("\n[+] Niveles de dificultad:")
    for level_func, level_name in levels.values():
        level_func(f"- {level_name}")
    
    log.info(f"\n[+] Buscando máquinas con dificultad {difficulty}\n")
    
    try:
        with open("bundle.js", "r") as f:
            data = f.read()
            
        machines = []
        current_machine = {}
        lines = data.split('\n')
        
        # Parseamos todas las máquinas con barra de progreso
        with log.progress("Analizando máquinas...") as p:
            for i, line in enumerate(lines):
                p.status(f"Procesando línea {i+1}/{len(lines)}")
                line = line.strip()
                if 'name:' in line:
                    current_machine['name'] = line.split('name:')[1].strip().strip('",')
                elif 'dificultad:' in line:
                    current_machine['dificultad'] = line.split('dificultad:')[1].strip().strip('",')
                elif 'so:' in line:
                    current_machine['so'] = line.split('so:')[1].strip().strip('",')
                elif '}' in line and current_machine:
                    if 'dificultad' in current_machine and current_machine['dificultad'].lower() == difficulty.lower():
                        machines.append(current_machine)
                    current_machine = {}
        
        if not machines:
            log.failure(f"\n[!] No se encontraron máquinas con dificultad {difficulty}\n")
        else:
            log.success(f"\n[+] Resultados ({len(machines)} máquinas):\n")
            for machine in machines:
                log.info(f"Nombre: {machine['name']}")
                levels.get(machine['dificultad'].lower(), (log.info,))[0](f"Dificultad: {machine['dificultad']}")
                log.info(f"Sistema: {machine.get('so', 'N/A')}")
                log.indented("-"*50)
                
    except Exception as e:
        log.failure(f"Error en la búsqueda: {e}")

# Función para buscar por sistema operativo
def search_system(system):
    if not os.path.exists("bundle.js"):
        log.failure("[!] Primero debes descargar los datos (opción -u)")
        return
    
    log.info(f"\n[+] Buscando máquinas con sistema {system}\n")
    
    try:
        with open("bundle.js", "r") as f:
            data = f.read()
            
        machines = []
        current_machine = {}
        lines = data.split('\n')
        
        with log.progress("Analizando máquinas...") as p:
            for i, line in enumerate(lines):
                p.status(f"Procesando línea {i+1}/{len(lines)}")
                line = line.strip()
                if 'name:' in line:
                    current_machine['name'] = line.split('name:')[1].strip().strip('",')
                elif 'so:' in line:
                    current_machine['so'] = line.split('so:')[1].strip().strip('",')
                elif 'dificultad:' in line:
                    current_machine['dificultad'] = line.split('dificultad:')[1].strip().strip('",')
                elif '}' in line and current_machine:
                    if 'so' in current_machine and current_machine['so'].lower() == system.lower():
                        machines.append(current_machine)
                    current_machine = {}
        
        if not machines:
            log.failure(f"\n[!] No se encontraron máquinas con sistema {system}\n")
        else:
            log.success(f"\n[+] Resultados ({len(machines)} máquinas):\n")
            for machine in machines:
                log.info(f"Nombre: {machine['name']}")
                log.info(f"Sistema: {machine['so']}")
                log.info(f"Dificultad: {machine.get('dificultad', 'N/A')}")
                log.indented("-"*50)
                
    except Exception as e:
        log.failure(f"Error en la búsqueda: {e}")

# Función para buscar por técnica    
def search_tecnica(skill):
    log.info(f"\n[+] Buscando máquinas con técnica {skill}\n")
    if not os.path.exists("bundle.js"):
        log.failure("[!] Primero debes descargar los datos (opción -u)")
        return
    try: 
        with open("bundle.js", "r") as f:
            data = f.read()
            
        machines = []
        current_machine = {}
        lines = data.split('\n')
        
        with log.progress("Analizando máquinas...") as p:
            for i, line in enumerate(lines):
                p.status(f"Procesando línea {i+1}/{len(lines)}")
                line = line.strip()
                if 'name:' in line:
                    current_machine['name'] = line.split('name:')[1].strip().strip('",')
                elif 'ip:' in line:
                    current_machine['ip'] = line.split('ip:')[1].strip().strip('",')
                elif 'so:' in line:
                    current_machine['so'] = line.split('so:')[1].strip().strip('",')
                elif 'skills:' in line:
                    current_machine['skills'] = line.split('skills:')[1].strip().strip('",')
                elif 'dificultad:' in line:
                    current_machine['dificultad'] = line.split('dificultad:')[1].strip().strip('",')
                elif '}' in line and current_machine:
                    if 'skills' in current_machine and skill.lower() in current_machine['skills'].lower():
                        machines.append(current_machine)
                    current_machine = {}
        
        if not machines:
            log.failure(f"\n[!] No se encontraron máquinas con la skill {skill}\n")
        else:
            log.success(f"\n[+] Resultados ({len(machines)} máquinas):\n")
            for machine in machines:
                log.info(f"Name: {machine.get('name', 'N/A')}")
                log.info(f"IP: {machine.get('ip', 'N/A')}")
                log.info(f"SO: {machine.get('so', 'N/A')}")
                log.info(f"Dificultad: {machine.get('dificultad', 'N/A')}")
                log.info(f"Skills: {machine.get('skills', 'N/A')}")
                log.indented("-"*50)
    except Exception as e:  
        log.failure(f"Error en la búsqueda: {e}")


# Manejo de argumentos
if __name__ == "__main__":
    if len(sys.argv) == 1:
        help_panel()
    else:
        if "-u" in sys.argv:
            update_files()
        elif "-m" in sys.argv:
            try:
                name = sys.argv[sys.argv.index("-m") + 1]
                search_machine(name)
            except IndexError:
                log.failure("[!] Debes especificar un nombre de máquina")
        elif "-d" in sys.argv:
            try:
                difficulty = sys.argv[sys.argv.index("-d") + 1]
                search_difficulty(difficulty)
            except IndexError:
                log.failure("[!] Debes especificar una dificultad")
        elif "-s" in sys.argv:
            try:
                system = sys.argv[sys.argv.index("-s") + 1]
                search_system(system)
                
            except IndexError:
                log.failure("[!] Debes especificar un sistema operativo")
        elif "-t" in sys.argv:
            try:
                skill = sys.argv[sys.argv.index("-t") + 1]
                search_tecnica(skill)
            except IndexError:
                log.failure("[!] Debes especificar una técnica")
        elif "-h" in sys.argv:
            help_panel()
        else:
            help_panel()

        




