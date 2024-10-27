#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#
#    GitHub: https://github.com/Jhanfer/archimedes-converter
#    Archimedes: deb to arch converter
#    Copyright (C) 2024  Jhanfer
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   Archimedes-converter  Copyright (C) 2024  Jhanfer
#   This program comes with ABSOLUTELY NO WARRANTY.
#   This is free software, and you are welcome to redistribute it
#   under certain conditions; See the GNU General Public License 
#   for more details <https://www.gnu.org/licenses/gpl-3.0.en.html>.
#
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import argparse
import shutil
from tempfile import mkdtemp
import shlex
import re
import datetime

parser = argparse.ArgumentParser(description="Script para convertir .deb en paquetes instalables de Arch Linux",
                                usage="Por favor, ponga una ruta de archivo a convertir. Use -h para ayuda")
pkgrel=1
class Archimedes():
    def commands(self, *command_tuple:tuple):
        """Verifica si existen la variable PATH
        y busca los comandos en ella"""
        path = os.getenv("PATH") #Variable de entorno PATH (donde están los comandos para encontrar las aplicaciones)
        if path is not None:
            path_list = path.split(os.pathsep) #devuelve una lista de toddas las direcciones del PATH (el "os.pathsep" es literalmente ":")
        else:
            print("No es posible encontrar el PATH...")
            sys.exit(1)

        if not len(command_tuple) == 0: #verifica si hay comandos en "command_tuple"
            for command in command_tuple:
                error = True
                for paths in path_list: #itera sobre la lista de paths
                    command_path = os.path.join(paths, command) #combina el path y el comando 
                    if os.access(command_path, os.X_OK): #verifica si es accesible la ruta generada en "command_path"
                        error = False
                        break
                if error == True:
                    print(f"El comando \"{command}\" no ha sido encontrado")
                    sys.exit(1)
        else:
            print("No se han detectado comandos...")
            sys.exit(1)


    def write_archcontrol(self, path, pkginfo):
        """Escribe el archivo "PKGINFO".

        "PKGINFO" Es un archivo que contiene información que retorna
        write_archcontrol()"""
        try:
            fd = os.open(path, os.O_RDWR|os.O_CREAT) #abre el archivo con todos los nombres de los archivos del directorio
        except IOError:
            print(f"No se puede escribir en \"{path}\" ")
            sys.exit(1)
        if pkginfo["url"]:
            url = pkginfo["url"]
        else:
            url = "<http://www.archlinux.org>"

        #escribe el archivo PKGINFO con los siguientes datos:
        _ = os.write(fd, str.encode("# Generado por Archimedes\n"))
        _ = os.write(fd, str.encode(f"pkgname = {pkginfo["package"]}\n"))
        _ = os.write(fd, str.encode(f"pkgver = {pkginfo["version"]}-{pkgrel}\n"))
        _ = os.write(fd, str.encode(f"pkgdesc = \"{pkginfo["description"][:24]}\"\n"))
        _ = os.write(fd, str.encode(f"packager = \"Arch Linux, Archimedes <http://www.archlinux.org>\"\n"))
        _ = os.write(fd, str.encode(f"size = {pkginfo["installed-size"]}\n"))
        _ = os.write(fd, str.encode(f"arch = {pkginfo["architecture"]}\n"))
        _ = os.write(fd, str.encode(f"license = None\n"))
        _ = os.write(fd, str.encode(f"url = {url}\n"))
        _ = os.write(fd, str.encode(f"builddate = {pkginfo["builddate"]}\n"))
        _ = os.write(fd, str.encode(f"{"\n".join(f"depend = {i}" for i in pkginfo["depends"])}"))

        os.close(fd)


    def change_dependencies(self, dep):
        """Cambia algunas dependecias de Debian a dependecias
        de ArchLinux"""
        debian_to_arch = {
            "libasound2": "alsa-lib",
            "libatk-bridge2.0-0": "at-spi2-atk",
            "libatk1.0-0": "atk",
            "libatspi2.0-0": "at-spi2-core",
            "libc6": "glibc",
            "libcairo2": "cairo",
            "libcurl3-gnutls": "curl",
            "libcurl3-nss": "curl",
            "libcurl4": "curl",
            "libcurl3": "curl",
            "libdbus-1-3": "dbus",
            "libdrm2": "libdrm",
            "libexpat1": "expat",
            "libgbm1": "mesa",
            "libglib2.0-0": "glib2",
            "libgtk-3-0": "gtk3",
            "libgtk-4-1": "gtk4",
            "libnspr4": "nspr",
            "libnss3": "nss",
            "libpango-1.0-0": "pango",
            "libx11-6": "libx11",
            "libxcb1": "libxcb",
            "libxcomposite1": "libxcomposite",
            "libxdamage1": "libxdamage",
            "libxext6": "libxext",
            "libxfixes3": "libxfixes",
            "libxkbcommon0": "libxkbcommon",
            "libxkbfile1": "libxkbfile",
            "libxrandr2": "libxrandr",
            "libxrender1": "libxrender",
            "libxtst6": "libxtst",
            "libxt6": "libxt",
            "libxcursor1": "libxcursor",
            "libxi6": "libxi",
            "libxinerama1": "libxinerama",
            "libxft2": "libxft",
            "libxfont2": "libxfont2",
        }

        base_name = re.match(r'^([^>=]+)', dep).group(1) #separa las depenedencias de las versiones
        arch_name = debian_to_arch.get(base_name, base_name) #busca su equivalente de arch
        return arch_name


    def read_control(self,path):
        """Leer información de archivo control
        y devuelve un diccionario con la información
        relevante para armar el PKGINFO"""
        try:
            file = os.open(path,os.O_RDONLY) #lectura del archivo en solo lectura
            os.lseek(file, 0, 0) #mueve el puntero al inicio del archivo
            read_file = os.read(file, 100000).decode("utf-8") #lee el archivo de 0 al caracter "100000" y utiliza la función "decode()" para convertir los bytes a texto
            
        except IOError:
            print(f"No se puede leer información de la dirección {path}")
            sys.exit(1)

        # formateo de las lineas del archivo
        files = read_file.strip("\n")
        # Patrón para encontrar campos y sus valores usando expresiones regulares: Valor = clave
        patron = r'([\w-]+):\s*(.*?)(?=\n[\w-]+:|$)'
        # Encontrar todas las coincidencias
        coincidencias = re.finditer(patron, files, re.DOTALL)
        #mapeo de campos arquitecturas
        architectures = {
            "amd64": "x86_64",
            "i686": "i686",
            "i386":"i686"
        }
        #unix timestamp
        date = datetime.datetime.now()
        unix_timestamp = datetime.datetime.timestamp(date)*1000
        #mapeo de campos
        mapped_fields = {
            "architecture": "",
            "package": "",
            "description": "",
            "maintainer": "",
            "installed-size": "",
            "version": "",
            "builddate":f"{int(unix_timestamp)}",
            "depends":[],
            "license":"",
            "url":""
        }        

        # Procesar cada coincidencia
        for match in coincidencias:
            field = match.group(1).lower() #campo 
            value = match.group(2).strip() #valor del campo

            if field in mapped_fields: #verifica si está presente en el mapeo de campos

                if field == "architecture": 
                    mapped_fields[field] = architectures.get(value, "any") #retorna la arquitectura correcta

                elif field == "hompage" or field == "url":
                    mapped_fields[field] = value

                elif field == "depends":
                    depends = value.split(", ")
                    for i in depends:
                        nombre,*version = i.split(">=")
                        version = "".join(version)
                        f_name = re.sub(r'[^\w.>=-]', '', nombre)
                        f_version = re.sub(r'[^\w.>=-]', '', version)
                        arch_dep = self.change_dependencies(f_name)
                        if arch_dep.count('lib') > 1:
                            libs = re.findall(r'lib[a-zA-Z0-9-]+(?=[lib]|$)', arch_dep)
                            """no está en uso"""
                            continue
                        else:
                            mapped_fields["depends"].append(f"{arch_dep}")

                elif field == "version":
                    try:
                        version, _ = value.split("-")
                        mapped_fields[field] = f"{version}_{_}"
                    except:
                        mapped_fields[field] = value

                else:
                    mapped_fields[field] = value
            else:
                continue
        
        if not mapped_fields["description"] and not mapped_fields["installed-size"]: #verifica si está description y size
            print("Falta información necesaria")
            sys.exit(1)
            
        os.close(file) #cierra el archivo
        
        return mapped_fields

    def command_handler(self,*arg) -> dict:
        """Manejador de comandos y eventos
        y retorna el input y output del archivo"""
        
        #maneja los argumentos: ruta de archivo y comando -help
        parser.add_argument("input_deb_file", help="ruta de archivo a convertir", type=str)
        args = parser.parse_args()
        path = args.input_deb_file

        if not os.path.isfile(path) and not os.access(path,os.F_OK): #verifica si es una ruta de archivo válida
            print("Por favor, ingrese una ruta correcta...")
            sys.exit(1)
        
        _, file_extension = os.path.splitext(path) #rompe la ruta del archivo y la extensión del archivo
        
        if file_extension != ".deb": #verifica si la extensión del archivo es ".deb"
            print("No es un archivo \".deb\" ")
            sys.exit(1)

        return {"input_file":os.path.abspath(path),"output_file":f"{_}.pkg.tar.gz"} #devuelve la ruta del archivo entrante y genera una ruta de salida con la extensión "pkg.tar.gz"

    def change_dir(self,directory):
        """Cambia el directorio"""
        try:
            os.chdir(directory)
        except OSError:
            print(f"No es posible acceder al directorio {directory}")
            sys.exit(1)

    def convert(self, input_file:str, output_file:str):
        (input_tempdir, output_tempdir) = (mkdtemp(), mkdtemp()) #crea directorios temporales de entrada y salida

        print(os.path.basename(input_file))

        try:
            self.change_dir(input_tempdir) #accede al directorio temporal

            #extraer el archivo deb. Importante usar shlex para escapar correctamente la cadena de texto
            os.system(f"ar x {shlex.quote(input_file)}") #esto es una linea de codigo utilizable en bash que extrae el archivo
            
            print(f"creando archivos temporales\ninput: {input_tempdir}\noutput: {output_tempdir}")
            
            if os.path.exists("data.tar.gz"): #comprueba si existe el archivo "data.tar.gz"
                data_path = "data.tar.gz"
            else:
                for item in os.listdir("."): #crea una lista de los archivos en el directorio, después busca si existe "data.tar"
                    if item.find("data.tar") == 0: #esto va a encontrar el data.tar.xz si existiese y lo asigna a data_path
                        data_path = item
                        break

                if data_path == "":
                    print(f"No se encontraron datos en {input_file}")
                    sys.exit(1)

            #extraer el "data.tar" de la carpeta temporal en la carpeta de salida temporal  
            os.system(f"tar -xf {shlex.quote(os.path.join(input_tempdir, data_path)) } -C {shlex.quote(output_tempdir)}") #esto es una linea de codigo utilizable en bash
            
            #extraer archivo control en la carpeta temporal
            control_file = os.path.join(input_tempdir, "control.tar.gz") #dirección del archivo control
            if os.path.isfile(control_file): #comprobar si es un archivo o si existe
                os.system(f"tar -xf {shlex.quote(control_file)}") #extración del archivo control
            else:
                control_file = os.path.join(input_tempdir, "control.tar.xz") #por si está en otro formato
                if os.path.isfile(control_file): #comprobar si es un archivo o si existe
                    os.system(f"tar -xf {shlex.quote(control_file)}") #extración del archivo control
                else:
                    print("El archivo control no ha sido encontrado...")
                    sys.exit(1)

            deb_info = self.read_control(os.path.join(input_tempdir, "control")) #lee el archivo control y retorna la información necesaria para crear el "PKGINFO"
            
            os.chdir(output_tempdir) #cambiamos de directorio

            os.system("find . -type f | sed -e \'s/^\\.\\///\' > .FILELIST") #crea un archivo con una lista de los nombres de los archivos dentro del directorio y sus subcarpetas
            self.write_archcontrol(f"{output_tempdir}/.PKGINFO", deb_info) #crea el archivo PKGINFO en el directorio temporal de salida con los datos extraidos de "deb_info"
            os.system(f"tar -zvcf {shlex.quote(output_file)} * .PKGINFO .FILELIST") #crea el instalador "pkg.tar.gz" usando el "PKGINFO" y "FILELIST" y lo deja en la ruta de salida "output_file"
            print("Hecho!")
            print()
            print(f"Su archivo se encuentra en: {output_file}")
        except:
            print("Algo ha fallado.")
        finally:
            #elimina los directorios temporales
            shutil.rmtree(input_tempdir, True) 
            shutil.rmtree(output_tempdir, True)

if __name__ == "__main__":
    archimedes = Archimedes() #inicializa la clase
    try:
        DATA = archimedes.command_handler() #inicializa el manejador de argumentos y los guarda en "DATA"
        archimedes.commands("ar", "tar", "find", "sed") #inicializa la búsqueda de los comandos
        archimedes.convert(DATA["input_file"],DATA["output_file"]) #inicializa la conversión con los datos extraidos del manejador de argumentos
    except KeyboardInterrupt:
        print("Abortando...")

# vim:ai:et:sw=4:ts=4:sts=4:tw=78:fenc=utf-8
