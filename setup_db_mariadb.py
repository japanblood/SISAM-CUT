import mysql.connector

# Credenciales de MariaDB proporcionadas
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "SISAM"

def inicializar_sistema():
    # Nos conectamos a MariaDB
    conexion = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conexion.cursor()

    # Crear la base de datos si no existe (por si acaso)
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")

    # 1. Crear tabla de Roles (Admin, Docente, Alumno) 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id_rol INT PRIMARY KEY AUTO_INCREMENT,
        nombre_rol VARCHAR(255) UNIQUE NOT NULL
    )""")

    # 2. Crear tabla de Usuarios con Seguridad 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INT PRIMARY KEY AUTO_INCREMENT,
        nombre VARCHAR(255) NOT NULL,
        correo VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        id_rol INT,
        FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
    )""")

    # 3. Crear tabla de Incidencias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidencias (
        id_incidencia INT PRIMARY KEY AUTO_INCREMENT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tipo_contaminacion VARCHAR(255) NOT NULL,
        ubicacion_exacta VARCHAR(255) NOT NULL,
        descripcion_hechos TEXT,
        posibles_responsables VARCHAR(255),
        acciones_realizadas TEXT,
        resultados_obtenidos TEXT,
        id_reportero INT,
        evidencia_foto TEXT,
        FOREIGN KEY (id_reportero) REFERENCES usuarios(id_usuario)
    )""")

    # 4. Tabla de Mediciones Técnicas (Normativa Ambiental) 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mediciones (
        id_medicion INT PRIMARY KEY AUTO_INCREMENT,
        id_incidencia INT,
        pm25 FLOAT, pm10 FLOAT, so2 FLOAT, no2 FLOAT, o3 FLOAT, co FLOAT, metales_pesados VARCHAR(255),
        FOREIGN KEY (id_incidencia) REFERENCES incidencias(id_incidencia)
    )""")

    # Insertar roles básicos si no existen 
    # En MariaDB usamos INSERT IGNORE
    cursor.execute("INSERT IGNORE INTO roles (nombre_rol) VALUES ('Administrador'), ('Docente'), ('Alumno')")

    conexion.commit()
    conexion.close()
    print("✅ Base de datos SISAM-CUT en MariaDB creada y configurada con éxito.")

if __name__ == "__main__":
    inicializar_sistema()
