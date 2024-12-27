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
from contextlib import contextmanager
from DATA.deb_arch_equivalent_dependencies import debian_to_arch
import hashlib


parser = argparse.ArgumentParser(description="Script para convertir .deb en paquetes instalables de Arch Linux. Desarrollado por Jhanfer ❤",
                                usage="Por favor, ponga una ruta de archivo a convertir. Use -h para ayuda",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)

pkgrel=1
class Archimedes():

    def calculate_checksums(self,file_path):
        """Calcula el checksum SHA-256 de un archivo"""
        checksums = {} #creamos un diccionario donde se guardarán los checksums
        algorithm = hashlib.sha256() #se inicializa el algoritmo
        
        try:
            file = os.open(file_path, os.O_RDONLY) #abre el archivo original
            os.lseek(file, 0,0) #pone el puntero al inicio
            while True:
                chunk = os.read(file,8192) #lee el archivo en bloques de 8192 Bytes, osea, 8,129 Kilobytes
                algorithm.update(chunk) #actualiza el hash concatenando cada bloque leido anteriormente
                if not chunk:
                    break
            checksums[chunk] = algorithm.hexdigest() #guarda el hash en formato hexadecimal en el diccionario de checksum 

            return checksums
        except:
            print("Algo ha fallado al calcular el checksum")

    def write_checksum(self, path:str,file_name:str,check_sum:dict):
        """Crea y escribe en el archivo .CHECKSUMS"""
        try:
            fd = os.open(path, os.O_RDWR|os.O_CREAT) #crea el archivo de 
        except IOError:
            print(f"No se puede escribir los checksums en \"{path}\" ")
            sys.exit(1)
        
        _ = os.write(fd, str.encode(f"#Checksums calculados y escritos por Archimedes\n"))
        _ = os.write(fd, str.encode(f"SHA256 {file_name} {check_sum[b""]}"))
        os.close(fd)


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
            if "<" in pkginfo["maintainer"]:
                _, splited = pkginfo["maintainer"].split("<")
            else:
                splited = pkginfo["maintainer"]
            url = f"<{splited}"

        #escribe el archivo PKGINFO con los siguientes datos:
        _ = os.write(fd, str.encode("# Generado por Archimedes\n"))
        _ = os.write(fd, str.encode(f"pkgname = {pkginfo["package"]}\n"))
        _ = os.write(fd, str.encode(f"pkgver = {pkginfo["version"]}-{pkgrel}\n"))
        _ = os.write(fd, str.encode(f"pkgdesc = {pkginfo["description"]}\n"))
        _ = os.write(fd, str.encode(f"packager = \"Arch Linux, Archimedes <https://github.com/Jhanfer/archimedes-converter>\"\n"))
        _ = os.write(fd, str.encode(f"size = {pkginfo["installed-size"]}\n"))
        _ = os.write(fd, str.encode(f"arch = {pkginfo["architecture"]}\n"))
        _ = os.write(fd, str.encode(f"category = {pkginfo["section"]}\n"))
        _ = os.write(fd, str.encode(f"license = unknown\n"))
        _ = os.write(fd, str.encode(f"url = \"{url}\"\n"))
        _ = os.write(fd, str.encode(f"builddate = {pkginfo["builddate"]}\n"))
        _ = os.write(fd, str.encode(f"{"\n".join(f"depend = {i}" for i in pkginfo["depends"])}"))

        os.close(fd)


    def change_dependencies(self, dep):
        """Cambia algunas dependecias de Debian a dependecias
        de ArchLinux"""

        #se traslada diccionario "debian_to_arch" para limpieza del código
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
            "i386":"i686",
            "armv7l": "armv7l",
            "aarch64": "arm64",
            "ppc64le": "ppc64le",
            "s390x": "s390x"
        }
        #unix timestamp
        date = datetime.datetime.now()
        unix_timestamp = int(datetime.datetime.timestamp(date))
        #mapeo de campos 
        mapped_fields = {
            "architecture": "",
            "package": "",
            "description": "",
            "maintainer": "",
            "installed-size": "",
            "version": "",
            "builddate":f"{unix_timestamp}",
            "depends":[],
            "license":"",
            "url":"",
            "section":""
        }        

        # Procesar cada coincidencia
        for match in coincidencias:
            field = match.group(1).lower()  # campo 
            value = match.group(2).strip()  # valor del campo


            if field in mapped_fields: #verifica si está presente en el mapeo de campos
                #se cambian los if-elif-else por match-case
                match field:
                    case "architecture": 
                        mapped_fields[field] = architectures.get(value, "any") #retorna la arquitectura correcta

                    case "homepage" | "url":
                        _, splited = value.split("<")
                        mapped_fields[field] = f"<{splited}"

                    case "depends":
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
                    
                    case "description":
                        mapped_fields[field] = value.replace('\n', '').replace('\r', '')

                    case "version":
                        try:
                            version, _ = value.split("-")
                            mapped_fields[field] = f"{version}_{_}"
                        except:
                            mapped_fields[field] = value

                    case _:
                        mapped_fields[field] = value
            else:
                continue
        
        if not mapped_fields["description"] and not mapped_fields["installed-size"]: #verifica si está description y size
            print("Falta información necesaria")
            sys.exit(1)

        os.close(file) #cierra el archivo
        
        return mapped_fields
    

    def change_dir(self,directory):
        """Cambia el directorio"""
        try:
            os.chdir(directory)
        except OSError:
            print(f"No es posible acceder al directorio {directory}")

    @contextmanager #creamos el manejador de contextos para los archivos temporales
    def temp_directories(self): #elimina los archivos temporales independientemente de cómo acabe el código
        #crea directorios temporales de entrada y salida
        input_tempdir = mkdtemp()
        output_tempdir = mkdtemp()
        try:
            yield input_tempdir, output_tempdir #se utiliza el controlador de llamada yield
        finally:
            shutil.rmtree(input_tempdir, True) 
            shutil.rmtree(output_tempdir, True)

    def command_executer(self, *, input_file:str=None,input_dir:str=None, output_dir:str=None,output_file:str=None, **kwarg):
        """Ejecutador de comandos del sistema y manejo de errores"""
        try:
            if kwarg["options"] == "ar_command_extract":
                #extraer el archivo deb. Importante usar shlex para escapar correctamente la cadena de texto
                os.system(f"ar x {shlex.quote(input_file)}")#esto es una linea de codigo utilizable en bash que extrae el archivo

            elif kwarg["options"] == "tar_command_extract":
                #extraer el "data.tar" de la carpeta temporal en la carpeta de salida temporal  
                os.system(f"tar -xf {input_dir} -C {shlex.quote(output_dir)}") #esto es una linea de codigo utilizable en bash
            elif kwarg["options"] == "make_pkg":
                context = os.system(f"ionice -c2 -n7 nice -n 19 bsdtar -zvcf {shlex.quote(output_file)} * .PKGINFO .FILELIST .CHECKSUMS") #crea el instalador "pkg.tar.gz" usando el "PKGINFO" y "FILELIST" y lo deja en la ruta de salida "output_file"
                os.system("clear")
                return context
            elif kwarg["options"] == "make_pkginfo":
                os.system("find . -type f | sed -e \'s/^\\.\\///\' > .FILELIST") #crea un archivo con una lista de los nombres de los archivos dentro del directorio y sus subcarpetas
        except:
            print("Algo ha fallado")
            sys.exit(1)

    def check_tar_gz(self, input_file:str):
        """Comprobador de data.tar.gz o data.tar.xz"""
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

        return data_path

    def convert(self, input_file:str, output_file:str, context) -> tuple:
        """Crea archivos PKGINFO y FILELIST.
        
        Convierte el .deb en un paquete de arch
        """
        print("\nIniciando conversión. Por favor, sea paciente y no teclee en la terminal.\n")    
        with self.temp_directories() as (input_tempdir, output_tempdir): #llama al gestor de contexto de archivos temporales
            print(f"Convirtiendo archivo {os.path.basename(input_file)}")
            print(f"Creando archivos temporales\nInput: {input_tempdir}\nOutput: {output_tempdir}\n")
            self.change_dir(input_tempdir) #accede al directorio temporal para posteriormente ser eliminado
            
            self.command_executer(input_file=input_file,options="ar_command_extract") #llama al extractor de archivos

            data_path = self.check_tar_gz(input_file)
            
            self.command_executer(input_dir=shlex.quote(os.path.join(input_tempdir, data_path)),output_dir=output_tempdir, options="tar_command_extract") #llama al extractor de archivos

            #extraer archivo control en la carpeta temporal
            control_file = os.path.join(input_tempdir, "control.tar.gz") #dirección del archivo control
            if os.path.isfile(control_file): #comprobar si es un archivo o si existe
                self.command_executer(input_dir=control_file,output_dir=input_tempdir,options="tar_command_extract") #llama al extractor de archivos
            else:
                control_file = os.path.join(input_tempdir, "control.tar.xz") #por si está en otro formato
                if os.path.isfile(control_file): #comprobar si es un archivo o si existe
                    os.system(f"tar -xf {shlex.quote(control_file)}") #extración del archivo control
                else:
                    print("El archivo control no ha sido encontrado...")
                    sys.exit(1)
            deb_info = self.read_control(os.path.join(input_tempdir, "control")) #lee el archivo control y retorna la información necesaria para crear el "PKGINFO"
            os.chdir(output_tempdir) #cambiamos de directorio
            
            self.command_executer(options="make_pkginfo") #llama al ejecutador de comandos para crear el PKGINFO
            self.write_archcontrol(f"{output_tempdir}/.PKGINFO", deb_info) #crea el archivo PKGINFO en el directorio temporal de salida con los datos extraidos de "deb_info"
            
            
            checksums = self.calculate_checksums(file_path=input_file) #calculamos el checksum del archivo original
            self.write_checksum(path=f"{output_tempdir}/.CHECKSUMS", file_name=input_file.split("/")[-1],check_sum=checksums) #se crea el archivo .CHECKSUMS pasandole el nombre del archivo original, la ruta donde se escribirá y los checksums calculados
            self.command_executer(output_file=output_file,options="make_pkg") #se crea el PKG
            
            output,_ = os.path.split(output_file)

        return output, context

    def convert_iterator(self, DATA:dict):
        """Iterador para la función convert"""
        if DATA: #comprueba si existe el diccionario
            if type(DATA["input_file"]) == list: #comprueba si el diccionario tiene listas
                for input in DATA["input_file"]: #itera sobre la lista de rutas, convirtiendo los archivos respectivamente
                    file_path, _ = input.split(".deb") #se extrae el .deb de la ruta de entrada
                    output_file = f"{file_path}.pkg.tar.gz" #se genera la ruta de salida
                    output, context = self.convert(input, output_file, context="list_end")
                return output, context

            elif type(DATA["input_file"]) == str and type(DATA["output_file"]) == str: #comprueba si el diccionario tiene cadenas
                output, context = self.convert(DATA["input_file"],DATA["output_file"], context="string_end")
                return output, context
            else:
                output, context = self.convert(DATA["input_file"],DATA["output_file"], context="string_end")
                return output, context

    def simple_gui(self, path):
        """GUI simple"""
        os.system("clear")
        #se cran las listas para guardar las rutas de entrada y salida, además de los nombres
        input_deb_path = []
        output_deb_path = []
        input_deb_names = []
        
        file_path, file = os.path.split(path) #rompe la ruta del archivo y la extensión del archivo
        file_name, file_extension = os.path.splitext(file) #extrae el nombre del archivo y su extensión

        if file:
            #confirmamos que sea .deb
            if not file_extension != ".deb":
                input_file_path = f"{os.path.abspath(os.path.join(file_path,file))}" #rescatamos la ruta de entrada
                output_file_path = f"{os.path.abspath(os.path.join(file_path,file_name))}.pkg.tar.gz" #creamos la ruta de salida
                self.convert_iterator({"input_file":input_file_path,"output_file":output_file_path}) #se usa el iterador de convert
                print(f"\nSu archivo se encuentra en {output_file_path}")
                print("Adiós! Gracias por usar Archimedes :D")
                sys.exit(1)
            else:
                print("ponga un archivo con extensión válido")
                sys.exit(1)
        
        if not file: #si no es una ruta.deb 
            files_lista:list = os.listdir(path) #lista los archivos existentes en el directorio
            for i in files_lista: #iteramos en la lista de archivos
                if i.endswith(".deb"): #busca los que terminan por .deb 
                    _, file_extension = os.path.splitext(i) #separamos la ruta de su extensión
                    input_deb_path.append(os.path.abspath(f"{file_path}/{i}")) #juntamos la ruta de entrada y el nombre del archivo
                    output_deb_path.append(os.path.abspath(f"{file_path}/{_}.pkg.tar.gz")) #creamos la ruta de salida con la ruta de entrada, el nombre del archivo sin el .deb y el .pkg.tar.gz
                    input_deb_names.append(f"{i}") #creamos la lista de nombres
            
            while True:
                if input_deb_path and output_deb_path: #comprobamos que se hayan creado las listas
                    print("\nArchivos \".deb\" encontrados en la ruta:\n")
                    extension = 0
                    for names in input_deb_names: #iteramos sobre los nombres para enseñarlos en pantalla
                        extension += 1
                        print(f"{extension}. {names}")
                    print("\nEscriba \"all\" para convertirlos a todos o el número del archivo que desee convertir. Presione cualquier tecla para cerrar:")
                
                    select = input("\n") #se le pide al usuario una opción
                    os.system("clear")
                    match select:
                        case "all": #se convierten todos los archivos pasandole las listas completas
                            self.convert_iterator({"input_file":input_deb_path,"output_file":""}) #no se le pasan las rutas de salida porque en este caso las genera automáticamente
                            print(f"\n### Su archivo se encuentra en {file_path} ###")
                            continue
                        case _: #se convierte solo el archivo que se selecciona
                            if select.isdigit():
                                self.convert_iterator({"input_file":input_deb_path[int(select)-1],"output_file":output_deb_path[int(select)-1]})
                                print(f"\n### Su archivo se encuentra en {file_path} ###")
                                continue
                            else:
                                os.system("clear")
                                print("Adiós! Gracias por usar Archimedes :D")
                                sys.exit(1)
                else:
                    print("Faltan input_deb_path and output_deb_path")
                    sys.exit(1)

        else:
            print("ponga un archivo o directorio")
            sys.exit(1)

    def command_handler(self,*arg) -> dict:
        """Manejador de comandos y eventos
        y retorna el path del archivo"""
        
        #maneja los argumentos: ruta de archivo y comando -help
        parser.add_argument("input_deb_file", help="Ruta del archivo a convertir (.deb). Es obligatorio ingresar este dato, porque sin él no es posible localizar el archivo. El resultado del Script de Archimedes guardará el archivo convertido en la misma carpeta que el archivo original.", type=str)
        args = parser.parse_args()
        path = args.input_deb_file

        if not os.path.isfile(path) and not os.access(path,os.F_OK): #verifica si es una ruta de archivo válida
            print("Por favor, ingrese una ruta correcta...")
            sys.exit(1)
        
        return path



if __name__ == "__main__": 
    archimedes = Archimedes() #inicializa la clase
    try:
        PATH = archimedes.command_handler() #inicializa el manejador de argumentos y los guarda en "DATA"
        archimedes.commands("ar", "bsdtar", "find", "sed") #inicializa la búsqueda de los comandos
        DATA = archimedes.simple_gui(PATH)
    except KeyboardInterrupt:
        print("Abortando...")

# vim:ai:et:sw=4:ts=4:sts=4:tw=78:fenc=utf-8
