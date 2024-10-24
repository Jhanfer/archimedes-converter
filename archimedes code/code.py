#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) Jhanfer
# GitHub: https://github.com/Jhanfer/archimedes-converter

# Este script es gratuito; Puedes redistribuirlo y/o modificarlo pero
# bajo los términos de la Licencia Pública General GNU versión 3 (GPLv3),
# publicado por la Free Software Foundation.

# Este programa se distribuye con la esperanza de que sea útil, pero
# SIN NINGUNA GARANTÍA, ni siquiera la garantía de que sea 
# IDONEIDAD PARA UN USO PARTICULAR.


import sys
import os
import argparse
from shutil import rmtree
from tempfile import mkdtemp
from getopt import gnu_getopt, GetoptError
import shlex


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

        if not len(command_tuple) == 0:
            for command in command_tuple:
                error = True

                for paths in path_list:
                    command_path = os.path.join(paths, command)
                    if os.access(command_path, os.X_OK):
                        error = False
                        break

                if error == True:
                    print(f"El comando \"{command}\" no ha sido encontrado")
                    sys.exit(1)
        else:
            print("No se han detectado comandos...")
            sys.exit(1)

    def command_handler(self,*arg) -> dict:
        """Manejador de comandos y eventos
        y retorna el input y output del archivo"""
        parser.add_argument("input_deb_file", help="ruta de archivo a convertir", type=str)
        args = parser.parse_args()
        path = args.input_deb_file

        if not os.path.isfile(path) and not os.access(path,os.F_OK):
            print("Por favor, ingrese una ruta correcta...")
            sys.exit(1)
        
        _, file_extension = os.path.splitext(path)
        if file_extension != ".deb":
            print("No es un archivo \".deb\" ")
            sys.exit(1)
        
        return {"input_file":os.path.abspath(path),"output_file":f"{_}.pkg"}

    def convert(self, input_file:str, output_file:str):
        pass

if __name__ == "__main__":
    archimedes = Archimedes()
    try:
        DATA = archimedes.command_handler()
        archimedes.commands('ar', 'tar', 'find', 'sed')
        archimedes.convert(
            DATA["input_file"],
            DATA["output_file"]
        )
    except KeyboardInterrupt:
        print("Abortando...")

# vim:ai:et:sw=4:ts=4:sts=4:tw=78:fenc=utf-8
