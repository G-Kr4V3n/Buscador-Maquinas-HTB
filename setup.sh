#!/bin/bash

# Instalar dependencias de Python
pip install -r requirements.txt

# Instalar paquetes del sistema (requiere sudo)
sudo apt update
sudo apt install -y js-beautify moreutils

echo "Instalación completada."