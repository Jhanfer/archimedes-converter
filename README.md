# Archimedes Converter

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10-green.svg)

Archimedes es una herramienta de línea de comandos que permite convertir paquetes Debian (.deb) a paquetes instalables de Arch Linux (.pkg.tar.gz).

## 🚀 Características

- Conversión directa de paquetes .deb a formato .pkg.tar.gz
- Mapeo automático de dependencias de Debian a Arch Linux
- Soporte para múltiples formatos de compresión (gz, xz)
- Generación automática de metadatos, checksums y archivos de control
- Compatible con diferentes arquitecturas (amd64, i686)

## 📋 Requisitos Previos

El script requiere los siguientes comandos disponibles en el sistema:
- `ar`
- `tar`
- `find`
- `sed`
- Python 3.10

## 🔧 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Jhanfer/archimedes-converter.git

# Entrar al directorio
cd archimedes-converter

# Entrar a la carpeta del script
cd archimedes

# Dar permisos de ejecución
chmod +x archimedes-converter.py
```

## 💻 Uso

```bash
./archimedes-converter.py <ruta de archivo .deb> o <ruta de directorio> 
```

### Ejemplos

```bash
# Convertir un paquete .deb
./archimedes-converter.py /home/<usuario>/Descargas/archivo.deb

# Convertir varios paquetes .deb
./archimedes-converter.py /home/<usuario>/Descargas/

# Mostrar ayuda
./archimedes-converter.py --help
```
## ⭐ Recomendación:
Se recomienda utilizar linea de comandos para evitar posibles errores de instalación:
```bash
sudo pacman -U <nombre del paquete convertido>
```



## 🔍 Proceso de Conversión

1. Extracción del paquete .deb
2. Análisis del archivo de control
3. Mapeo de dependencias a equivalentes de Arch Linux
4. Generación de archivos .PKGINFO, .FILELIST y .CHECKSUMS
5. Creación del paquete final .pkg.tar.gz7

## 📦 Soporte de Dependencias

El conversor incluye mapeo automático para bibliotecas comunes:
- libasound2 → alsa-lib
- libatk1.0-0 → atk
- libc6 → glibc
- libcairo2 → cairo
- Y muchas más...

## ⚠️ Limitaciones

- No todos los paquetes Debian tienen equivalentes directos en Arch Linux
- Algunas dependencias pueden requerir ajuste manual
- No se garantiza la funcionalidad completa de todos los paquetes convertidos

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, siéntete libre de:
1. Hacer fork del proyecto
2. Crear una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Hacer commit de tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. Hacer push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia GPL-3.0 - ver el archivo [LICENSE](LICENSE) para más detalles.

## ✨ Agradecimientos

- A la comunidad de Arch Linux por su extensa documentación.
- A todos los contribuyentes y testers del proyecto.

## 👤 Autor

**Jhanfer**
- GitHub: [@Jhanfer](https://github.com/Jhanfer)

---

⌨️ con ❤️ por [Jhanfer](https://github.com/Jhanfer)
