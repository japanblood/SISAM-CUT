import mysql.connector
import customtkinter as ctk
import tkinter.ttk as ttk
from tkinter import messagebox
import tkintermapview
import requests
import time
import os
import shutil
import json
from tkinter import filedialog
from PIL import Image
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF
ctk.set_appearance_mode("System")  # Modo: "System" (estándar), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Temas: "blue" (estándar), "green", "dark-blue"

SESSION_FILE = "session.json"
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root",
    "database": "SISAM"
}

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self._verificar_db()

    def _get_connection(self):
        return mysql.connector.connect(**self.config)

    def _verificar_db(self):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'incidencias'")
            if not cursor.fetchone():
                print("La tabla 'incidencias' no existe. Ejecuta setup_db_mariadb.py primero.")
                return
            
            try:
                cursor.execute("SHOW COLUMNS FROM incidencias LIKE 'evidencia_foto'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE incidencias ADD COLUMN evidencia_foto TEXT")
                    conn.commit()
            except mysql.connector.Error:
                pass # La columna ya existe o error
        except Exception as e:
            print(f"Error de base de datos: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def registrar_usuario(self, nombre, correo, password):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_rol FROM roles WHERE nombre_rol = 'Alumno'")
            res = cursor.fetchone()
            id_rol = res[0] if res else 3
                
            query = "INSERT INTO usuarios (nombre, correo, password_hash, id_rol) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (nombre, correo, password, id_rol))
            conn.commit()
            return True, "Usuario registrado con éxito."
        except mysql.connector.Error as e:
            return False, f"Error al registrar usuario: {e}"
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def autenticar_usuario(self, correo_o_nombre, password):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            # Buscar por correo o por nombre (para que admins puedan entrar con su nombre)
            query = """SELECT u.id_usuario, u.nombre, u.correo, r.nombre_rol 
                       FROM usuarios u LEFT JOIN roles r ON u.id_rol = r.id_rol 
                       WHERE (u.correo = %s OR u.nombre = %s) AND u.password_hash = %s"""
            cursor.execute(query, (correo_o_nombre, correo_o_nombre, password))
            return cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"Error al autenticar: {e}")
            return None
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def obtener_incidencias_por_usuario(self, id_usuario):
        query = "SELECT id_incidencia, fecha_registro, tipo_contaminacion, ubicacion_exacta, posibles_responsables FROM incidencias WHERE id_reportero = %s ORDER BY fecha_registro DESC"
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (id_usuario,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Error al obtener incidencias del usuario: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
                
    def registrar_administrador(self, nombre, password):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_rol FROM roles WHERE nombre_rol = 'Administrador'")
            res = cursor.fetchone()
            id_rol = res[0] if res else 1
            # Correo generado automáticamente para admins (no requieren correo)
            import uuid
            correo_auto = f"admin_{uuid.uuid4().hex[:8]}@sisam.local"
            query = "INSERT INTO usuarios (nombre, correo, password_hash, id_rol) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (nombre, correo_auto, password, id_rol))
            conn.commit()
            new_id = cursor.lastrowid
            return True, "Administrador registrado con éxito.", new_id, correo_auto
        except mysql.connector.Error as e:
            return False, f"Error al registrar administrador: {e}", None, None
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def obtener_todos_usuarios(self):
        query = """SELECT u.id_usuario, u.nombre, u.correo, r.nombre_rol 
                   FROM usuarios u LEFT JOIN roles r ON u.id_rol = r.id_rol
                   ORDER BY r.nombre_rol, u.nombre"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Error al obtener usuarios: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def eliminar_usuario(self, id_usuario):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Desvincular incidencias del usuario antes de eliminar
            cursor.execute("UPDATE incidencias SET id_reportero = NULL WHERE id_reportero = %s", (id_usuario,))
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            conn.commit()
            return True, "Usuario eliminado con éxito."
        except mysql.connector.Error as e:
            return False, f"Error al eliminar usuario: {e}"
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def eliminar_incidencia(self, id_incidencia):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incidencias WHERE id_incidencia = %s", (id_incidencia,))
            conn.commit()
            return True, "Incidencia eliminada con éxito."
        except mysql.connector.Error as e:
            return False, f"Error al eliminar incidencia: {e}"
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def modificar_incidencia(self, id_incidencia, tipo, ubicacion, descripcion, responsables, acciones):
        query = """UPDATE incidencias SET tipo_contaminacion=%s, ubicacion_exacta=%s,
                   descripcion_hechos=%s, posibles_responsables=%s, acciones_realizadas=%s
                   WHERE id_incidencia=%s"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (tipo, ubicacion, descripcion, responsables, acciones, id_incidencia))
            conn.commit()
            return True, "Incidencia actualizada con éxito."
        except mysql.connector.Error as e:
            return False, f"Error al modificar incidencia: {e}"
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def registrar_incidencia(self, tipo_contaminacion, ubicacion, descripcion, responsables, acciones, id_reportero, ruta_foto=""):
        query = """
            INSERT INTO incidencias (tipo_contaminacion, ubicacion_exacta, descripcion_hechos, posibles_responsables, acciones_realizadas, evidencia_foto, id_reportero)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (tipo_contaminacion, ubicacion, descripcion, responsables, acciones, ruta_foto, id_reportero))
            conn.commit()
            return True, "Incidencia registrada con éxito."
        except mysql.connector.Error as e:
            return False, f"Error al registrar: {e}"
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def obtener_incidencias(self):
        query = "SELECT id_incidencia, fecha_registro, tipo_contaminacion, ubicacion_exacta, posibles_responsables FROM incidencias ORDER BY fecha_registro DESC"
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Error al obtener incidencias: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def obtener_incidencia_por_id(self, id_incidencia):
        query = "SELECT * FROM incidencias WHERE id_incidencia = %s"
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (id_incidencia,))
            return cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"Error al obtener incidencia: {e}")
            return None
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def obtener_estadisticas_dashboard(self):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total
            cursor.execute("SELECT COUNT(*) FROM incidencias")
            total = cursor.fetchone()[0]
            
            # Mes actual
            hoy = datetime.date.today()
            mes_actual = f"{hoy.year}-{hoy.month:02d}%"
            cursor.execute("SELECT COUNT(*) FROM incidencias WHERE fecha_registro LIKE %s", (mes_actual,))
            total_mes = cursor.fetchone()[0]
            
            # Por tipo
            cursor.execute("SELECT tipo_contaminacion, COUNT(*) FROM incidencias GROUP BY tipo_contaminacion")
            por_tipo = cursor.fetchall()
            
            # Top tipo
            top_tipo = "N/A"
            if por_tipo:
                top_tipo = max(por_tipo, key=lambda x: x[1])[0]
                
            # Recientes (últimas 3)
            cursor.execute("SELECT id_incidencia, fecha_registro, tipo_contaminacion, ubicacion_exacta FROM incidencias ORDER BY fecha_registro DESC LIMIT 3")
            recientes = cursor.fetchall()
            
            return {
                "total": total,
                "total_mes": total_mes,
                "top_tipo": top_tipo,
                "por_tipo": por_tipo,
                "recientes": recientes
            }
        except mysql.connector.Error as e:
            print(f"Error al obtener estadísticas: {e}")
            return {"total": 0, "total_mes": 0, "top_tipo": "N/A", "por_tipo": [], "recientes": []}
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def obtener_meses_disponibles(self):
        query = "SELECT DISTINCT DATE_FORMAT(fecha_registro, '%Y-%m') FROM incidencias ORDER BY fecha_registro DESC"
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            meses = [row[0] for row in cursor.fetchall() if row[0]]
            return meses if meses else ["Sin registros"]
        except mysql.connector.Error as e:
            print(f"Error al obtener meses: {e}")
            return ["Error"]
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def obtener_incidencias_por_mes(self, mes_anio):
        query = """
            SELECT id_incidencia, fecha_registro, tipo_contaminacion, ubicacion_exacta, descripcion_hechos 
            FROM incidencias 
            WHERE DATE_FORMAT(fecha_registro, '%Y-%m') = %s
            ORDER BY fecha_registro ASC
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (mes_anio,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Error al obtener incidencias del mes: {e}")
            return []
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = DatabaseManager(DB_CONFIG)
        self.usuario_actual = None

        self.title("SISAM-CUT - Gestión de Incidencias")
        self.geometry("900x600")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.verificar_sesion()

    def verificar_sesion(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r') as f:
                    data = json.load(f)
                    self.usuario_actual = data
                self.mostrar_app_principal()
            except Exception:
                self.mostrar_login()
        else:
            self.mostrar_login()

    def mostrar_login(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Reset grid configuration to single column for auth
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=0)
            
        self.auth_frame = FrameAuth(self.main_container, self.db, self)
        self.auth_frame.grid(row=0, column=0, sticky="nsew")

    def iniciar_sesion(self, usuario):
        # Asegurarse que todos los valores sean serializables en JSON
        session_data = {k: (int(v) if hasattr(v, '__int__') and not isinstance(v, bool) else str(v) if v is not None else None) for k, v in usuario.items()}
        self.usuario_actual = session_data
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f)
        self.mostrar_app_principal()

    def cerrar_sesion(self):
        respuesta = messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas cerrar la sesión?")
        if respuesta:
            self.usuario_actual = None
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            self.mostrar_login()

    def mostrar_app_principal(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
            
        self.main_container.grid_columnconfigure(0, weight=0)
        self.main_container.grid_columnconfigure(1, weight=1)
        
        self.sidebar_frame = ctk.CTkFrame(self.main_container, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        # La expansión de fila se configura al final para el selector de tema

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SISAM-CUT", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard Principal", command=self.mostrar_frame_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_nueva_incidencia = ctk.CTkButton(self.sidebar_frame, text="Registrar Incidencia", command=self.mostrar_frame_nueva)
        self.btn_nueva_incidencia.grid(row=2, column=0, padx=20, pady=10)

        self.btn_ver_incidencias = ctk.CTkButton(self.sidebar_frame, text="Ver Incidencias", command=self.mostrar_frame_ver)
        self.btn_ver_incidencias.grid(row=3, column=0, padx=20, pady=10)

        self.btn_reportes = ctk.CTkButton(self.sidebar_frame, text="Generar Reportes", command=self.mostrar_frame_reportes)
        self.btn_reportes.grid(row=4, column=0, padx=20, pady=10)
        
        self.btn_perfil = ctk.CTkButton(self.sidebar_frame, text="Mi Perfil", command=self.mostrar_frame_perfil)
        self.btn_perfil.grid(row=5, column=0, padx=20, pady=10)
        
        self.btn_salir = ctk.CTkButton(self.sidebar_frame, text="Cerrar Sesión", fg_color="#d9534f", hover_color="#c9302c", command=self.cerrar_sesion)
        self.btn_salir.grid(row=6, column=0, padx=20, pady=10)

        # Tema y selector al fondo
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Tema:", anchor="w")
        self.appearance_mode_label.grid(row=10, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.cambiar_tema)
        self.appearance_mode_optionemenu.grid(row=11, column=0, padx=20, pady=(10, 20))

        # Configurar expansión de fila para empujar el tema al fondo
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.frame_dashboard = FrameDashboard(self.content_frame, self.db)
        self.frame_nueva = FrameNuevaIncidencia(self.content_frame, self.db, self)
        self.frame_ver = FrameVerIncidencias(self.content_frame, self.db)
        self.frame_reportes = FrameReportes(self.content_frame, self.db)
        self.frame_perfil = FramePerfil(self.content_frame, self.db, self)
        self.frame_usuarios = FrameUsuarios(self.content_frame, self.db, self)

        # Mostrar botón Usuarios solo para administradores
        es_admin = self.usuario_actual and self.usuario_actual.get('nombre_rol') == 'Administrador'
        if es_admin:
            self.btn_usuarios = ctk.CTkButton(self.sidebar_frame, text="Usuarios",
                                              command=self.mostrar_frame_usuarios)
            self.btn_usuarios.grid(row=5, column=0, padx=20, pady=10)
            self.btn_perfil.grid(row=6, column=0, padx=20, pady=10)
            self.btn_salir.grid(row=7, column=0, padx=20, pady=10)

        self.mostrar_frame_dashboard()
        
    def mostrar_frame_dashboard(self):
        self.ocultar_frames()
        self.frame_dashboard.grid(row=0, column=0, sticky="nsew")
        self.frame_dashboard.cargar_dashboard()

    def mostrar_frame_nueva(self):
        self.ocultar_frames()
        self.frame_nueva.grid(row=0, column=0, sticky="nsew")
        
    def mostrar_frame_ver(self):
        self.ocultar_frames()
        self.frame_ver.grid(row=0, column=0, sticky="nsew")
        es_admin = self.usuario_actual and self.usuario_actual.get('nombre_rol') == 'Administrador'
        self.frame_ver.cargar_datos(es_admin=es_admin)

    def mostrar_frame_reportes(self):
        self.ocultar_frames()
        self.frame_reportes.grid(row=0, column=0, sticky="nsew")
        self.frame_reportes.cargar_datos()
        
    def mostrar_frame_perfil(self):
        self.ocultar_frames()
        self.frame_perfil.grid(row=0, column=0, sticky="nsew")
        self.frame_perfil.cargar_datos()
        
    def ocultar_frames(self):
        self.frame_dashboard.grid_forget()
        self.frame_nueva.grid_forget()
        self.frame_ver.grid_forget()
        self.frame_reportes.grid_forget()
        self.frame_perfil.grid_forget()
        self.frame_usuarios.grid_forget()

    def mostrar_frame_usuarios(self):
        self.ocultar_frames()
        self.frame_usuarios.grid(row=0, column=0, sticky="nsew")
        self.frame_usuarios.cargar_datos()

    def cambiar_tema(self, nuevo_tema: str):
        ctk.set_appearance_mode(nuevo_tema)


class FrameDashboard(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db
        
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.label_titulo = ctk.CTkLabel(self, text="Dashboard SISAM-CUT", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.grid(row=0, column=0, columnspan=3, padx=20, pady=20, sticky="w")
        
        # Tarjetas Superiores
        self.frame_tarjetas = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_tarjetas.grid(row=1, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        self.frame_tarjetas.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Widgets para tarjetas (se actualizan en cargar_dashboard)
        self.lbl_val_total = ctk.StringVar(value="0")
        self.lbl_val_mes = ctk.StringVar(value="0")
        self.lbl_val_tipo = ctk.StringVar(value="N/A")
        
        color_fondo_tarjeta = ("#e0e0e0", "#2b2b2b")
        
        self.crear_tarjeta(self.frame_tarjetas, "Total Histórico", self.lbl_val_total, 0, color_fondo_tarjeta)
        self.crear_tarjeta(self.frame_tarjetas, "Reportes este Mes", self.lbl_val_mes, 1, color_fondo_tarjeta)
        self.crear_tarjeta(self.frame_tarjetas, "Tipo más Frecuente", self.lbl_val_tipo, 2, color_fondo_tarjeta)
        
        # Panel Inferior (Gráfica y Recientes)
        self.frame_inferior = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_inferior.grid(row=2, column=0, columnspan=3, padx=20, pady=20, sticky="nsew")
        self.frame_inferior.grid_columnconfigure(0, weight=2)
        self.frame_inferior.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=3) # Darle más espacio al panel inferior
        
        # Contenedor para Gráfica
        self.frame_grafica = ctk.CTkFrame(self.frame_inferior)
        self.frame_grafica.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        # Contenedor para Recientes
        self.frame_recientes = ctk.CTkFrame(self.frame_inferior)
        self.frame_recientes.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        ctk.CTkLabel(self.frame_recientes, text="Últimos Reportes", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.inner_recientes = ctk.CTkFrame(self.frame_recientes, fg_color="transparent")
        self.inner_recientes.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.canvas_widget = None

    def crear_tarjeta(self, master, titulo, variable, columna, color):
        tarjeta = ctk.CTkFrame(master, corner_radius=10, fg_color=color)
        tarjeta.grid(row=0, column=columna, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(tarjeta, text=titulo, font=ctk.CTkFont(size=14)).pack(pady=(10, 0))
        ctk.CTkLabel(tarjeta, textvariable=variable, font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(5, 10))

    def cargar_dashboard(self):
        stats = self.db.obtener_estadisticas_dashboard()
        
        # Actualizar Tarjetas
        self.lbl_val_total.set(str(stats["total"]))
        self.lbl_val_mes.set(str(stats["total_mes"]))
        self.lbl_val_tipo.set(str(stats["top_tipo"]))
        
        # Actualizar Lista Recientes
        for widget in self.inner_recientes.winfo_children():
            widget.destroy()
            
        for inc in stats["recientes"]:
            # inc: id, fecha, tipo, ubicacion
            fecha_raw = inc[1]
            if hasattr(fecha_raw, 'strftime'):
                fecha_corta = fecha_raw.strftime('%Y-%m-%d')
            else:
                fecha_corta = str(fecha_raw).split()[0] if fecha_raw else ""
            texto = f"#{inc[0]} - {inc[2]}\n{fecha_corta} | {inc[3][:20]}..."
            lbl = ctk.CTkLabel(self.inner_recientes, text=texto, justify="left", fg_color=("#e0e0e0", "#2b2b2b"), corner_radius=5)
            lbl.pack(fill="x", pady=5, ipadx=5, ipady=5)
            
        if not stats["recientes"]:
            ctk.CTkLabel(self.inner_recientes, text="No hay reportes aún.").pack(pady=20)
            
        # Dibujar Gráfica de Pastel
        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()
            
        por_tipo = stats["por_tipo"]
        if por_tipo:
            labels = [x[0] for x in por_tipo]
            sizes = [x[1] for x in por_tipo]
            
            # Definir mapa de colores vibrantes
            colores_vibrantes = {
                "Aire": "#00d2ff",      # Azul cielo brillante
                "Agua": "#0047ff",      # Azul profundo vibrante
                "Suelo": "#ff6a00",     # Naranja vibrante
                "Acústica": "#ffea00",  # Amarillo neón/oro
                "Residuos Sólidos": "#ff003c", # Rojo intenso
                "Otro": "#b200ff"       # Púrpura eléctrico
            }
            colores_grafica = [colores_vibrantes.get(lbl, "#00ff00") for lbl in labels]
            
            # Usar mismo gris del panel de recientes
            bg_color = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#e0e0e0"
            text_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"
            
            fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
            fig.patch.set_facecolor(bg_color)
            
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colores_grafica, autopct='%1.1f%%', startangle=140, 
                                              textprops=dict(color=text_color))
            
            plt.setp(autotexts, size=10, weight="bold", color='#333333')
            ax.axis('equal') # Pastel circular
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=self.frame_grafica)
            canvas.draw()
            self.canvas_widget = canvas
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig) # Liberar memoria
        else:
            ctk.CTkLabel(self.frame_grafica, text="No hay datos para mostrar gráfica.").pack(expand=True)


class FrameNuevaIncidencia(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager, app):
        super().__init__(master)
        self.db = db
        self.app = app

        self.grid_columnconfigure(1, weight=1)

        # Título
        self.label_titulo = ctk.CTkLabel(self, text="Registrar Nueva Incidencia", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="w")

        # Formulario
        self.label_tipo = ctk.CTkLabel(self, text="Tipo de Contaminación:")
        self.label_tipo.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.entry_tipo = ctk.CTkOptionMenu(self, values=["Aire", "Agua", "Suelo", "Acústica", "Residuos Sólidos", "Otro"])
        self.entry_tipo.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        self.label_ubicacion = ctk.CTkLabel(self, text="Ubicación Exacta:")
        self.label_ubicacion.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        
        self.frame_ubicacion = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_ubicacion.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        self.frame_ubicacion.grid_columnconfigure(0, weight=1)
        
        self.entry_ubicacion = ctk.CTkEntry(self.frame_ubicacion, placeholder_text="Ej. Coordenadas o Dirección")
        self.entry_ubicacion.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.btn_mapa = ctk.CTkButton(self.frame_ubicacion, text="Obtener por Mapa", command=self.abrir_mapa, width=120)
        self.btn_mapa.grid(row=0, column=1)

        self.label_desc = ctk.CTkLabel(self, text="Descripción de Hechos:")
        self.label_desc.grid(row=3, column=0, padx=20, pady=10, sticky="nw")
        self.entry_desc = ctk.CTkTextbox(self, height=100)
        self.entry_desc.grid(row=3, column=1, padx=20, pady=10, sticky="ew")

        self.label_resp = ctk.CTkLabel(self, text="Posibles Responsables:")
        self.label_resp.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        self.entry_resp = ctk.CTkEntry(self, placeholder_text="Personas o grupos involucrados")
        self.entry_resp.grid(row=4, column=1, padx=20, pady=10, sticky="ew")

        self.label_acciones = ctk.CTkLabel(self, text="Acciones Realizadas:")
        self.label_acciones.grid(row=5, column=0, padx=20, pady=10, sticky="nw")
        self.entry_acciones = ctk.CTkTextbox(self, height=60)
        self.entry_acciones.grid(row=5, column=1, padx=20, pady=10, sticky="ew")

        # Fotografía
        self.rutas_fotos = []
        self.label_foto = ctk.CTkLabel(self, text="Evidencia (Máx 3):")
        self.label_foto.grid(row=6, column=0, padx=20, pady=10, sticky="w")
        
        self.frame_foto = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_foto.grid(row=6, column=1, padx=20, pady=10, sticky="ew")
        self.btn_foto = ctk.CTkButton(self.frame_foto, text="Adjuntar Fotografía", command=self.seleccionar_foto, width=150)
        self.btn_foto.pack(side="left", padx=(0,10))
        self.lbl_foto_nombre = ctk.CTkLabel(self.frame_foto, text="0 archivos seleccionados")
        self.lbl_foto_nombre.pack(side="left")

        self.btn_guardar = ctk.CTkButton(self, text="Guardar Registro", command=self.guardar_incidencia)
        self.btn_guardar.grid(row=7, column=0, columnspan=2, padx=20, pady=30)

    def abrir_mapa(self):
        respuesta = messagebox.askyesno("Permiso de Ubicación", "¿Permites que SISAM-CUT acceda a tu ubicación para el mapa interactivo?")
        
        if not respuesta:
            return # Si rechaza el permiso, no se abre el mapa ni se hace nada más
            
        # Coordenadas por defecto (Centro Universitario de Tonalá - CUTonalá)
        lat, lon = 20.566720, -103.226342
        
        # Crear ventana superior
        self.map_window = ctk.CTkToplevel(self)
        self.map_window.title("Seleccionar Ubicación")
        self.map_window.geometry("600x550")
        self.map_window.grab_set() # Foco en esta ventana
        
        # Etiqueta de instrucción
        lbl_instruccion = ctk.CTkLabel(self.map_window, text="¿Tu ubicación actual es donde ocurrió la incidencia?\n(Puedes hacer clic en el mapa para ajustar el pin)", font=ctk.CTkFont(weight="bold"))
        lbl_instruccion.pack(pady=10)
        
        # Mapa
        self.map_widget = tkintermapview.TkinterMapView(self.map_window, corner_radius=0)
        # Usar Google Maps como servidor de mapas (Evita bloqueos o lentitud de OpenStreetMap que dejan el mapa en blanco)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=es&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.map_widget.pack(fill="both", expand=True, padx=10, pady=10)
        self.map_widget.set_position(lat, lon)
        self.map_widget.set_zoom(15)
        
        # Marcador inicial
        self.current_marker = self.map_widget.set_marker(lat, lon, text="Incidencia")
        
        # Evento clic en el mapa
        def on_map_click(coords):
            if self.current_marker:
                self.current_marker.delete()
            self.current_marker = self.map_widget.set_marker(coords[0], coords[1], text="Incidencia")
            
        self.map_widget.add_right_click_menu_command(label="Mover Pin aquí", command=lambda coords: on_map_click(coords), pass_coords=True)
        self.map_widget.add_left_click_map_command(on_map_click)
        
        # Botones inferiores
        btn_frame = ctk.CTkFrame(self.map_window, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def confirmar():
            if self.current_marker:
                pos = self.current_marker.position
                self.entry_ubicacion.delete(0, "end")
                self.entry_ubicacion.insert(0, f"{pos[0]:.6f}, {pos[1]:.6f}")
            self.map_window.destroy()
            
        ctk.CTkButton(btn_frame, text="Confirmar Ubicación (Sí)", command=confirmar).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="gray", command=self.map_window.destroy).pack(side="left", padx=10)

    def seleccionar_foto(self):
        if len(self.rutas_fotos) >= 3:
            messagebox.showwarning("Límite alcanzado", "Ya has seleccionado el máximo de 3 imágenes.")
            return
            
        ruta = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        if ruta:
            self.rutas_fotos.append(ruta)
            cantidad = len(self.rutas_fotos)
            texto = f"{cantidad} archivo(s) seleccionado(s)"
            if cantidad == 3:
                texto += " (Máximo)"
            self.lbl_foto_nombre.configure(text=texto)

    def guardar_incidencia(self):
        tipo = self.entry_tipo.get()
        ubicacion = self.entry_ubicacion.get().strip()
        desc = self.entry_desc.get("1.0", "end-1c").strip()
        resp = self.entry_resp.get().strip()
        acciones = self.entry_acciones.get("1.0", "end-1c").strip()

        if not ubicacion or not desc:
            messagebox.showwarning("Campos incompletos", "La ubicación y la descripción son obligatorias.")
            return

        # Manejo de múltiples fotos
        rutas_guardadas = []
        if self.rutas_fotos:
            os.makedirs("evidencias_sisam", exist_ok=True)
            for i, ruta in enumerate(self.rutas_fotos):
                if os.path.exists(ruta):
                    ext = os.path.splitext(ruta)[1]
                    nombre_unico = f"evidencia_{int(time.time())}_{i}{ext}"
                    ruta_guardada = os.path.join("evidencias_sisam", nombre_unico)
                    try:
                        shutil.copy(ruta, ruta_guardada)
                        rutas_guardadas.append(ruta_guardada)
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo guardar una imagen: {e}")
        
        # Guardar las rutas separadas por comas
        evidencia_string = ",".join(rutas_guardadas)

        id_reportero = self.app.usuario_actual["id_usuario"]
        exito, mensaje = self.db.registrar_incidencia(tipo, ubicacion, desc, resp, acciones, id_reportero, evidencia_string)
        
        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self.limpiar_formulario()
        else:
            messagebox.showerror("Error", mensaje)

    def limpiar_formulario(self):
        self.entry_ubicacion.delete(0, "end")
        self.entry_desc.delete("1.0", "end")
        self.entry_resp.delete(0, "end")
        self.entry_acciones.delete("1.0", "end")
        self.entry_tipo.set("Aire")
        self.rutas_fotos = []
        self.lbl_foto_nombre.configure(text="0 archivos seleccionados")


class FrameVerIncidencias(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.label_titulo = ctk.CTkLabel(self, text="Listado de Incidencias Registradas", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        # Usar ttk.Treeview para la tabla
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2a2d2e",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#343638")
        style.map('Treeview', background=[('selected', '#22559b')])

        columnas = ("ID", "Fecha", "Tipo", "Ubicación", "Responsables")
        self.tree = ttk.Treeview(self, columns=columnas, show="headings")
        
        # Definir encabezados
        self.tree.heading("ID", text="ID")
        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("Tipo", text="Tipo Contaminación")
        self.tree.heading("Ubicación", text="Ubicación")
        self.tree.heading("Responsables", text="Responsables")

        # Ajustar ancho de columnas
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Fecha", width=120, anchor="center")
        self.tree.column("Tipo", width=120, anchor="center")
        self.tree.column("Ubicación", width=150, anchor="w")
        self.tree.column("Responsables", width=150, anchor="w")

        self.tree.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=1, column=1, pady=(0, 20), sticky="ns")
        
        # Botones de acción
        self.frame_botones = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botones.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        
        ctk.CTkButton(self.frame_botones, text="Ver Detalles", command=self.ver_detalles).pack(side="left", padx=10)
        self.btn_editar = ctk.CTkButton(self.frame_botones, text="Editar", fg_color="#f0ad4e", hover_color="#ec971f", command=self.editar_incidencia)
        self.btn_editar.pack(side="left", padx=10)
        self.btn_borrar = ctk.CTkButton(self.frame_botones, text="Eliminar", fg_color="#d9534f", hover_color="#c9302c", command=self.eliminar_incidencia)
        self.btn_borrar.pack(side="left", padx=10)

    def ver_detalles(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Por favor, selecciona una incidencia de la lista.")
            return
            
        item = self.tree.item(selected[0])
        id_incidencia = item['values'][0]
        
        detalles = self.db.obtener_incidencia_por_id(id_incidencia)
        if not detalles:
            messagebox.showerror("Error", "No se encontraron los detalles.")
            return
            
        # detalles: id_incidencia(0), fecha(1), tipo(2), ubicacion(3), desc(4), resp(5), acciones(6), id_reportero(7), evidencia_foto(8/9)
        
        win_detalles = ctk.CTkToplevel(self)
        win_detalles.title(f"Detalles de Incidencia #{id_incidencia}")
        win_detalles.geometry("550x650")
        win_detalles.grab_set()
        
        scrollable_frame = ctk.CTkScrollableFrame(win_detalles)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Campos
        fecha_val = detalles[1]
        if hasattr(fecha_val, 'strftime'):
            fecha_val = fecha_val.strftime('%Y-%m-%d %H:%M:%S')
        campos = [
            ("Fecha:", fecha_val),
            ("Tipo:", detalles[2]),
            ("Ubicación:", detalles[3]),
            ("Responsables:", detalles[5]),
            ("Descripción:", detalles[4]),
            ("Acciones Realizadas:", detalles[6])
        ]
        
        for i, (titulo, valor) in enumerate(campos):
            lbl_tit = ctk.CTkLabel(scrollable_frame, text=titulo, font=ctk.CTkFont(weight="bold"))
            lbl_tit.pack(anchor="w", pady=(10, 0))
            
            # Usar textbox para campos largos
            if titulo in ["Descripción:", "Acciones Realizadas:"]:
                txt = ctk.CTkTextbox(scrollable_frame, height=80)
                txt.insert("1.0", valor if valor else "N/A")
                txt.configure(state="disabled") # Solo lectura
                txt.pack(fill="x", pady=(5, 10))
            else:
                lbl_val = ctk.CTkLabel(scrollable_frame, text=valor if valor else "N/A", wraplength=400, justify="left")
                lbl_val.pack(anchor="w", pady=(0, 10))
                
        # --- Imágenes de evidencia ---
        evidencia_string = detalles[-1] if len(detalles) > 8 and isinstance(detalles[-1], str) else ""
        rutas_fotos = [r for r in evidencia_string.split(",") if r.strip()] if evidencia_string else []
        
        if rutas_fotos:
            lbl_tit_foto = ctk.CTkLabel(scrollable_frame, text="Evidencia Fotográfica:", font=ctk.CTkFont(weight="bold"))
            lbl_tit_foto.pack(anchor="w", pady=(10, 5))
            
            for ruta in rutas_fotos:
                if os.path.exists(ruta):
                    try:
                        img = Image.open(ruta)
                        img.thumbnail((400, 300))
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        lbl_img = ctk.CTkLabel(scrollable_frame, text="", image=ctk_img)
                        lbl_img.pack(pady=5)
                    except Exception as e:
                        lbl_err = ctk.CTkLabel(scrollable_frame, text=f"Error al cargar imagen: {os.path.basename(ruta)}", text_color="red")
                        lbl_err.pack(pady=5)

        btn_cerrar = ctk.CTkButton(win_detalles, text="Cerrar", command=win_detalles.destroy)
        btn_cerrar.pack(pady=10)

    def cargar_datos(self, es_admin=False):
        # Mostrar/ocultar botones admin
        if es_admin:
            self.btn_editar.pack(side="left", padx=10)
            self.btn_borrar.pack(side="left", padx=10)
        else:
            self.btn_editar.pack_forget()
            self.btn_borrar.pack_forget()
            
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        registros = self.db.obtener_incidencias()
        for row in registros:
            row = list(row)
            if hasattr(row[1], 'strftime'):
                row[1] = row[1].strftime('%Y-%m-%d %H:%M')
            self.tree.insert("", "end", values=row)

    def eliminar_incidencia(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una incidencia.")
            return
        item = self.tree.item(selected[0])
        id_inc = item['values'][0]
        respuesta = messagebox.askyesno("Confirmar", f"¿Eliminar incidencia #{id_inc}? Esta acción no se puede deshacer.")
        if respuesta:
            exito, msg = self.db.eliminar_incidencia(id_inc)
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.cargar_datos(es_admin=True)
            else:
                messagebox.showerror("Error", msg)

    def editar_incidencia(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una incidencia.")
            return
        item = self.tree.item(selected[0])
        id_inc = item['values'][0]
        detalles = self.db.obtener_incidencia_por_id(id_inc)
        if not detalles:
            messagebox.showerror("Error", "No se encontraron los detalles.")
            return

        win = ctk.CTkToplevel(self)
        win.title(f"Editar Incidencia #{id_inc}")
        win.geometry("500x480")
        win.grab_set()

        ctk.CTkLabel(win, text=f"Editar Incidencia #{id_inc}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        ctk.CTkLabel(win, text="Tipo de Contaminación:").pack(anchor="w", padx=20)
        opt_tipo = ctk.CTkOptionMenu(win, values=["Aire", "Agua", "Suelo", "Acústica", "Residuos Sólidos", "Otro"])
        opt_tipo.set(detalles[2] if detalles[2] else "Aire")
        opt_tipo.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(win, text="Ubicación:").pack(anchor="w", padx=20)
        entry_ubic = ctk.CTkEntry(win)
        entry_ubic.insert(0, detalles[3] if detalles[3] else "")
        entry_ubic.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(win, text="Descripción:").pack(anchor="w", padx=20)
        txt_desc = ctk.CTkTextbox(win, height=80)
        txt_desc.insert("1.0", detalles[4] if detalles[4] else "")
        txt_desc.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(win, text="Responsables:").pack(anchor="w", padx=20)
        entry_resp = ctk.CTkEntry(win)
        entry_resp.insert(0, detalles[5] if detalles[5] else "")
        entry_resp.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(win, text="Acciones Realizadas:").pack(anchor="w", padx=20)
        txt_acc = ctk.CTkTextbox(win, height=60)
        txt_acc.insert("1.0", detalles[6] if detalles[6] else "")
        txt_acc.pack(fill="x", padx=20, pady=5)

        def guardar():
            exito, msg = self.db.modificar_incidencia(
                id_inc,
                opt_tipo.get(),
                entry_ubic.get().strip(),
                txt_desc.get("1.0", "end-1c").strip(),
                entry_resp.get().strip(),
                txt_acc.get("1.0", "end-1c").strip()
            )
            if exito:
                messagebox.showinfo("Éxito", msg)
                win.destroy()
                self.cargar_datos(es_admin=True)
            else:
                messagebox.showerror("Error", msg)

        ctk.CTkButton(win, text="Guardar Cambios", command=guardar).pack(pady=15)

class FrameReportes(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db
        self.app = app
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.label_titulo = ctk.CTkLabel(self, text="Centro de Generación de Reportes", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Filtro
        self.frame_filtro = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_filtro.grid(row=1, column=0, pady=20)
        
        ctk.CTkLabel(self.frame_filtro, text="Selecciona el mes:").pack(side="left", padx=10)
        
        self.combo_meses = ctk.CTkComboBox(self.frame_filtro, values=["Cargando..."], width=150)
        self.combo_meses.pack(side="left", padx=10)
        
        self.btn_descargar = ctk.CTkButton(self.frame_filtro, text="Descargar PDF", fg_color="#28a745", hover_color="#218838", command=self.generar_pdf)
        self.btn_descargar.pack(side="left", padx=20)
        
    def cargar_datos(self):
        meses = self.db.obtener_meses_disponibles()
        self.combo_meses.configure(values=meses)
        if meses and meses[0] not in ["Error", "Sin registros"]:
            self.combo_meses.set(meses[0])
        else:
            self.combo_meses.set("Sin registros")
            
    def generar_pdf(self):
        mes_seleccionado = self.combo_meses.get()
        if not mes_seleccionado or mes_seleccionado in ["Sin registros", "Error", "Cargando..."]:
            messagebox.showwarning("Aviso", "No hay un mes válido seleccionado.")
            return
            
        registros = self.db.obtener_incidencias_por_mes(mes_seleccionado)
        
        if not registros:
            messagebox.showinfo("Vacío", f"No se encontraron registros para el mes {mes_seleccionado}.")
            return
            
        ruta_guardado = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Reporte_Mensual_SISAM_{mes_seleccionado}.pdf",
            title="Guardar Reporte Mensual",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if not ruta_guardado:
            return # Cancelado por el usuario
            
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Título
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, txt=f"Reporte Mensual SISAM-CUT ({mes_seleccionado})", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", size=11)
            
            for idx, r in enumerate(registros, 1):
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, txt=f"Incidencia #{r[0]} - {r[2]}", ln=True)
                
                pdf.set_font("Arial", size=10)
                # Limpiar textos para fpdf (latin-1)
                fecha = str(r[1]).encode('latin-1', 'replace').decode('latin-1')
                ubic = str(r[3]).encode('latin-1', 'replace').decode('latin-1')
                desc = str(r[4]).encode('latin-1', 'replace').decode('latin-1') if r[4] else "Sin descripcion."
                
                pdf.cell(0, 6, txt=f"Fecha: {fecha}", ln=True)
                pdf.cell(0, 6, txt=f"Ubicacion: {ubic}", ln=True)
                pdf.multi_cell(0, 6, txt=f"Descripcion: {desc}")
                pdf.ln(5)
                
            pdf.output(ruta_guardado)
            messagebox.showinfo("Éxito", f"Reporte PDF generado exitosamente en:\n{ruta_guardado}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al generar el PDF:\n{str(e)}")



class FrameAuth(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager, app):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.app = app
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.frame_login = FrameLogin(self, self.db, self.app, self.mostrar_registro, self.mostrar_registro_admin)
        self.frame_registro = FrameRegistro(self, self.db, self.app, self.mostrar_login)
        self.frame_registro_admin = FrameRegistroAdmin(self, self.db, self.app, self.mostrar_login)
        
        self.mostrar_login()
        
    def mostrar_login(self):
        self.frame_registro.grid_forget()
        self.frame_registro_admin.grid_forget()
        self.frame_login.grid(row=0, column=0)
        
    def mostrar_registro(self):
        self.frame_login.grid_forget()
        self.frame_registro_admin.grid_forget()
        self.frame_registro.grid(row=0, column=0)
        
    def mostrar_registro_admin(self):
        self.frame_login.grid_forget()
        self.frame_registro.grid_forget()
        self.frame_registro_admin.grid(row=0, column=0)

class FrameLogin(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager, app, callback_registro, callback_registro_admin):
        super().__init__(master)
        self.db = db
        self.app = app
        self.callback_registro = callback_registro
        self.callback_registro_admin = callback_registro_admin
        
        ctk.CTkLabel(self, text="Iniciar Sesión", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 20), padx=50)
        
        self.entry_correo = ctk.CTkEntry(self, placeholder_text="Correo o Nombre", width=250)
        self.entry_correo.pack(pady=10)
        
        self.entry_password = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=250)
        self.entry_password.pack(pady=10)
        
        ctk.CTkButton(self, text="Entrar", command=self.login).pack(pady=20)
        ctk.CTkButton(self, text="Crear Cuenta de Alumno", fg_color="transparent", border_width=1, command=self.callback_registro).pack(pady=10)
        ctk.CTkButton(self, text="Crear Cuenta de Administrador", fg_color="transparent", border_width=1, command=self.callback_registro_admin).pack(pady=5)
        
    def login(self):
        correo = self.entry_correo.get()
        password = self.entry_password.get()
        
        if not correo or not password:
            messagebox.showwarning("Error", "Llenar todos los campos.")
            return
            
        usuario = self.db.autenticar_usuario(correo, password)
        if usuario:
            self.app.iniciar_sesion(usuario)
        else:
            messagebox.showerror("Error", "Credenciales inválidas.")

class FrameRegistro(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager, app, callback_login):
        super().__init__(master)
        self.db = db
        self.app = app
        self.callback_login = callback_login
        
        ctk.CTkLabel(self, text="Registro de Alumno", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 20), padx=50)
        
        self.entry_nombre = ctk.CTkEntry(self, placeholder_text="Nombre Completo", width=250)
        self.entry_nombre.pack(pady=10)
        
        self.entry_correo = ctk.CTkEntry(self, placeholder_text="Correo Electrónico", width=250)
        self.entry_correo.pack(pady=10)
        
        self.entry_password = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=250)
        self.entry_password.pack(pady=10)
        
        ctk.CTkButton(self, text="Registrar", command=self.registrar).pack(pady=20)
        ctk.CTkButton(self, text="Volver al Login", fg_color="transparent", border_width=1, command=self.callback_login).pack(pady=10)
        
    def registrar(self):
        nombre = self.entry_nombre.get()
        correo = self.entry_correo.get()
        password = self.entry_password.get()
        
        if not nombre or not correo or not password:
            messagebox.showwarning("Error", "Llenar todos los campos.")
            return
            
        exito, msg = self.db.registrar_usuario(nombre, correo, password)
        if exito:
            messagebox.showinfo("Éxito", msg)
            # Iniciar sesión automáticamente después de registrarse
            usuario = self.db.autenticar_usuario(correo, password)
            if usuario:
                self.app.iniciar_sesion(usuario)
            else:
                self.callback_login()
        else:
            messagebox.showerror("Error", msg)

class FramePerfil(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager, app):
        super().__init__(master)
        self.db = db
        self.app = app
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Datos del usuario
        self.frame_datos = ctk.CTkFrame(self)
        self.frame_datos.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.lbl_nombre = ctk.CTkLabel(self.frame_datos, text="", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_nombre.pack(pady=10)
        
        self.lbl_correo = ctk.CTkLabel(self.frame_datos, text="")
        self.lbl_correo.pack(pady=5)
        
        self.lbl_rol = ctk.CTkLabel(self.frame_datos, text="")
        self.lbl_rol.pack(pady=5)
        
        # Tabla de reportes
        ctk.CTkLabel(self, text="Mis Incidencias Reportadas", font=ctk.CTkFont(size=18, weight="bold")).grid(row=1, column=0, pady=10)
        
        self.frame_tabla = ctk.CTkFrame(self)
        self.frame_tabla.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.frame_tabla.grid_columnconfigure(0, weight=1)
        self.frame_tabla.grid_rowconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", rowheight=25, fieldbackground="#343638")
        style.map('Treeview', background=[('selected', '#22559b')])
        
        columnas = ("ID", "Fecha", "Tipo", "Ubicación", "Responsables")
        self.tree = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings")
        
        for col in columnas:
            self.tree.heading(col, text=col)
            
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Fecha", width=120, anchor="center")
        self.tree.column("Tipo", width=120, anchor="center")
        self.tree.column("Ubicación", width=150, anchor="w")
        self.tree.column("Responsables", width=150, anchor="w")
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        self.scrollbar = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
    def cargar_datos(self):
        usuario = self.app.usuario_actual
        if not usuario: return
        
        self.lbl_nombre.configure(text=f"Nombre: {usuario.get('nombre', '')}")
        self.lbl_correo.configure(text=f"Correo: {usuario.get('correo', '')}")
        self.lbl_rol.configure(text=f"Rol: {usuario.get('nombre_rol', 'Alumno')}")
        
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        registros = self.db.obtener_incidencias_por_usuario(usuario.get('id_usuario'))
        for row in registros:
            row = list(row)
            if hasattr(row[1], 'strftime'):
                row[1] = row[1].strftime('%Y-%m-%d %H:%M')
            self.tree.insert("", "end", values=row)


class FrameRegistroAdmin(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager, app, callback_login):
        super().__init__(master)
        self.db = db
        self.app = app
        self.callback_login = callback_login
        
        ctk.CTkLabel(self, text="Registro de Administrador", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(40, 10), padx=50)
        ctk.CTkLabel(self, text="Requiere contraseña de administrador", text_color="gray").pack(pady=(0, 15))
        
        self.entry_nombre = ctk.CTkEntry(self, placeholder_text="Nombre Completo", width=250)
        self.entry_nombre.pack(pady=10)
        
        self.entry_clave_admin = ctk.CTkEntry(self, placeholder_text="Contraseña de Admin", show="*", width=250)
        self.entry_clave_admin.pack(pady=10)
        
        self.entry_password = ctk.CTkEntry(self, placeholder_text="Contraseña de acceso", show="*", width=250)
        self.entry_password.pack(pady=10)
        
        ctk.CTkButton(self, text="Registrar Administrador", command=self.registrar).pack(pady=20)
        ctk.CTkButton(self, text="Volver al Login", fg_color="transparent", border_width=1, command=self.callback_login).pack(pady=5)
        
    def registrar(self):
        nombre = self.entry_nombre.get().strip()
        clave_admin = self.entry_clave_admin.get()
        password = self.entry_password.get()
        
        if not nombre or not clave_admin or not password:
            messagebox.showwarning("Error", "Todos los campos son obligatorios.")
            return
        
        if clave_admin != "2510":
            messagebox.showerror("Error", "Contraseña de administrador incorrecta.")
            return
            
        exito, msg, new_id, correo_auto = self.db.registrar_administrador(nombre, password)
        if exito:
            messagebox.showinfo("Éxito", msg)
            # Login automático como administrador
            usuario = self.db.autenticar_usuario(correo_auto, password)
            if usuario:
                self.app.iniciar_sesion(usuario)
            else:
                self.callback_login()
        else:
            messagebox.showerror("Error", msg)


class FrameUsuarios(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager, app):
        super().__init__(master)
        self.db = db
        self.app = app
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self, text="Gestión de Usuarios", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=20, pady=20, sticky="w")
        
        # Tabla de usuarios
        self.frame_tabla = ctk.CTkFrame(self)
        self.frame_tabla.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.frame_tabla.grid_columnconfigure(0, weight=1)
        self.frame_tabla.grid_rowconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", rowheight=25, fieldbackground="#343638")
        style.map('Treeview', background=[('selected', '#22559b')])
        
        cols = ("ID", "Nombre", "Correo", "Rol")
        self.tree = ttk.Treeview(self.frame_tabla, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Nombre", width=150, anchor="w")
        self.tree.column("Correo", width=200, anchor="w")
        self.tree.column("Rol", width=100, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        sb = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        
        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=10)
        
        ctk.CTkButton(btn_frame, text="Eliminar Usuario", fg_color="#d9534f", hover_color="#c9302c",
                      command=self.eliminar_usuario).pack(side="left", padx=10)
        
    def cargar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        registros = self.db.obtener_todos_usuarios()
        for row in registros:
            self.tree.insert("", "end", values=row)
            
    def eliminar_usuario(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona un usuario de la lista.")
            return
        item = self.tree.item(selected[0])
        id_usuario = item['values'][0]
        nombre_usuario = item['values'][1]
        
        # No permitir borrarse a sí mismo
        if id_usuario == self.app.usuario_actual.get('id_usuario'):
            messagebox.showwarning("No permitido", "No puedes eliminar tu propia cuenta.")
            return
            
        respuesta = messagebox.askyesno("Confirmar", f"¿Eliminar al usuario '{nombre_usuario}'? Esta acción no se puede deshacer.")
        if respuesta:
            exito, msg = self.db.eliminar_usuario(id_usuario)
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.cargar_datos()
            else:
                messagebox.showerror("Error", msg)


if __name__ == "__main__":
    app = App()
    app.mainloop()
