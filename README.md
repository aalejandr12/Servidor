# PurrCrafter 🐾

Tu herramienta amigable para manipular archivos PDF de forma inteligente.

## 🌟 Características

- **Unir por Nombre**: Organiza y combina PDFs según su nombre de archivo
- **Unir por Contenido**: Fusiona PDFs basándose en el contenido de los documentos
- **Interfaz Intuitiva**: Diseño moderno y fácil de usar
- **Procesamiento Inteligente**: Reconocimiento automático de patrones y códigos

## 🚀 Demo en Vivo

Visita: [https://tu-usuario.github.io/purrcrafter](https://tu-usuario.github.io/purrcrafter)

## 🛠️ Tecnologías

### Frontend
- HTML5, CSS3, JavaScript
- Tailwind CSS
- Material Icons
- Responsive Design

### Backend (API)
- Python 3.8+
- Flask
- PyPDF2/pypdf
- Algoritmos de procesamiento de texto

## 📁 Estructura del Proyecto

```
purrcrafter/
├── docs/              # Frontend (GitHub Pages)
│   ├── index.html     # Página principal
│   ├── unir-nombre.html
│   ├── unir-contenido.html
│   ├── exito.html
│   ├── terminos.html
│   ├── privacidad.html
│   ├── css/
│   └── js/
├── main.py            # Servidor principal
├── pdf_extractor_*.py # Módulos de procesamiento
└── requirements.txt   # Dependencias Python
```

## 🔧 Instalación Local

### Prerrequisitos
- Python 3.8+
- pip

### Backend (API)
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/purrcrafter.git
cd purrcrafter

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\\Scripts\\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python main.py
```

### Frontend
El frontend está en la carpeta `docs/` y se sirve automáticamente desde GitHub Pages.

Para desarrollo local, puedes usar cualquier servidor web estático:
```bash
cd docs
python -m http.server 8080
```

## 📋 Uso

1. **Selecciona el modo**: Por nombre o por contenido
2. **Sube tus PDFs**: Arrastra y suelta o selecciona archivos
3. **Define el orden**: Especifica cómo unir los documentos
4. **Procesa**: ¡Obtén tu PDF unificado!

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Contacto

- Email: contact@purrcrafter.com
- Website: [purrcrafter.com](https://purrcrafter.com)

---

Hecho con ❤️ por el equipo de PurrCrafter