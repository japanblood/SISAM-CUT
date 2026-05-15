# SISAM-CUT API Backend

Este repositorio contiene la API REST para el sistema SISAM-CUT, permitiendo la comunicación entre la base de datos centralizada y los clientes (PC y Móvil).

## Tecnologías Utilizadas

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Rápido, moderno y de alto rendimiento).
- **Servidor**: [Uvicorn](https://www.uvicorn.org/) (Servidor ASGI para Python).
- **Base de Datos**: MariaDB / MySQL.
- **Validación de Datos**: Pydantic.

---

## Dependencias Necesarias

Para instalar todas las librerías necesarias para que la API funcione, ejecuta el siguiente comando:

```bash
pip install fastapi uvicorn mysql-connector-python pydantic python-multipart python-dotenv
```

### 🛠️ ¿Para qué sirve cada librería?
1.  ⚡ **fastapi**: Es el "cerebro" de nuestra API. Se encarga de recibir las peticiones de los celulares o PCs y decidir qué hacer con ellas.
2.  🖥️ **uvicorn**: Es el "motor" o servidor. FastAPI sabe qué hacer, pero Uvicorn es quien mantiene la API encendida y escuchando en internet.
3.  🗄️ **mysql-connector-python**: Es el "traductor". Permite que nuestra API en Python pueda hablar y entenderse con la base de datos MariaDB.
4.  🛡️ **pydantic**: Es el "guardia de seguridad". Revisa que los datos que envían los usuarios (ej. que el correo tenga un '@', que la contraseña no esté vacía) tengan el formato correcto antes de dejarlos pasar.
5.  📸 **python-multipart**: Es el "cargador". Necesario específicamente para poder recibir archivos pesados, como las fotografías de las evidencias.
6.  🔐 **python-dotenv**: Es la "caja fuerte". Nos permite guardar contraseñas (como la de la base de datos `root`) en un archivo oculto llamado `.env` para que no queden expuestas en el código.

---

## Estructura Sugerida

```text
api_sisam/
├── main.py              # Punto de entrada de FastAPI
├── database.py          # Lógica de conexión a MariaDB
├── models.py            # Modelos de Pydantic (Esquemas)
├── routes/              # Endpoints (usuarios, incidencias, reportes)
└── .env                 # Variables de entorno (Credenciales)
```

---

## Cómo Ejecutar (Desarrollo)

Una vez instaladas las dependencias y configurada la base de datos, puedes iniciar el servidor con:

```bash
uvicorn main:app --reload
```

El servidor estará disponible por defecto en `http://127.0.0.1:8000`.
Puedes acceder a la documentación interactiva en: `http://127.0.0.1:8000/docs`.
