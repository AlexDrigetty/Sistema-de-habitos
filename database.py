import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

class BaseDatos:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="habitos_bd",
            user="postgres",
            password="master.1",
            port="5432",
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        print("Conectado a la base de datos")
        self.crear_tablas()

    def crear_tablas(self):
        try:
            # Tabla de usuarios
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    contrasena VARCHAR(255) NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de hábitos
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS habitos (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    objetivo_diario_minutos INTEGER DEFAULT 30,
                    categoria VARCHAR(50) DEFAULT 'Salud',
                    icono VARCHAR(50) DEFAULT 'run',
                    color VARCHAR(20) DEFAULT '#3b82f6',
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de sesiones
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sesiones (
                    id SERIAL PRIMARY KEY,
                    habito_id INTEGER NOT NULL REFERENCES habitos(id) ON DELETE CASCADE,
                    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
                    hora_inicio TIMESTAMP,
                    hora_fin TIMESTAMP,
                    duracion_segundos INTEGER NOT NULL,
                    completada BOOLEAN DEFAULT TRUE,
                    notas TEXT,
                    UNIQUE(habito_id, fecha, hora_inicio)
                )
            """)
            
            # Tabla de recordatorios
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS recordatorios (
                    id SERIAL PRIMARY KEY,
                    habito_id INTEGER NOT NULL REFERENCES habitos(id) ON DELETE CASCADE,
                    activo BOOLEAN DEFAULT FALSE,
                    hora_inicio TIME,
                    hora_fin TIME
                )
            """)
            
            # Índices para mejor rendimiento
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_habitos_usuario ON habitos(usuario_id)
            """)
            
            self.conn.commit()
            print("Tablas creadas exitosamente")
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error creando tablas: {e}")

    # =================== MÉTODOS DE USUARIOS ===================
    def encriptar_contrasena(self, contrasena):
        sal = bcrypt.gensalt()
        encriptada = bcrypt.hashpw(contrasena.encode("utf-8"), sal)
        return encriptada.decode("utf-8")

    def verificar_contrasena(self, contrasena, contrasena_encriptada):
        try:
            return bcrypt.checkpw(contrasena.encode("utf-8"), contrasena_encriptada.encode("utf-8"))
        except Exception:
            return False

    def registrar_usuario(self, nombre_usuario, email, contrasena):
        try:
            self.cursor.execute(
                "SELECT id FROM usuarios WHERE nombre_usuario=%s OR email=%s",
                (nombre_usuario, email),
            )
            if self.cursor.fetchone():
                return {"exito": False, "mensaje": "Usuario o email ya existen"}

            contrasena_encriptada = self.encriptar_contrasena(contrasena)
            self.cursor.execute("""
                INSERT INTO usuarios (nombre_usuario, email, contrasena)
                VALUES (%s, %s, %s)
                RETURNING id, nombre_usuario, email, fecha_creacion
            """, (nombre_usuario, email, contrasena_encriptada))
            usuario = self.cursor.fetchone()
            self.conn.commit()
            print(f"Usuario registrado: {nombre_usuario}")
            return {"exito": True, "usuario": usuario}
        except Exception as e:
            self.conn.rollback()
            return {"exito": False, "mensaje": str(e)}

    def iniciar_sesion(self, usuario_o_email, contrasena):
        try:
            self.cursor.execute("""
                SELECT id, nombre_usuario, email, contrasena
                FROM usuarios
                WHERE nombre_usuario=%s OR email=%s
            """, (usuario_o_email, usuario_o_email))
            usuario = self.cursor.fetchone()
            if not usuario:
                return {"exito": False, "mensaje": "Usuario no encontrado"}

            if self.verificar_contrasena(contrasena, usuario["contrasena"]):
                return {"exito": True, "usuario": {
                    "id": usuario["id"],
                    "nombre_usuario": usuario["nombre_usuario"],
                    "email": usuario["email"],
                }}
            return {"exito": False, "mensaje": "Contraseña incorrecta"}
        except Exception as e:
            return {"exito": False, "mensaje": str(e)}

    # =================== MÉTODOS DE HÁBITOS ===================
    def crear_habito(self, usuario_id, nombre, descripcion="", objetivo_minutos=30, categoria="Salud"):
        try:
            # Mapear categoría a icono y color
            mapeo_categorias = {
                "Salud": {"icono": "dumbbell", "color": "#10b981"},
                "Aprendizaje": {"icono": "book-open", "color": "#3b82f6"},
                "Productividad": {"icono": "trending-up", "color": "#f59e0b"},
                "Bienestar": {"icono": "leaf", "color": "#06b6d4"}
            }
            
            categoria_info = mapeo_categorias.get(categoria, {"icono": "checkbox-blank-circle", "color": "#3b82f6"})
            
            self.cursor.execute("""
                INSERT INTO habitos (usuario_id, nombre, descripcion, objetivo_diario_minutos, categoria, icono, color)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, nombre, descripcion, objetivo_diario_minutos, categoria, icono, color, fecha_creacion
            """, (usuario_id, nombre, descripcion, objetivo_minutos, categoria, categoria_info["icono"], categoria_info["color"]))
            
            habito = self.cursor.fetchone()
            
            # Crear recordatorio por defecto
            self.cursor.execute("""
                INSERT INTO recordatorios (habito_id)
                VALUES (%s)
            """, (habito['id'],))
            
            self.conn.commit()
            return habito
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error creando hábito: {e}")
            return None

    def obtener_habitos_usuario(self, usuario_id):
        try:
            self.cursor.execute("""
                SELECT h.*, 
                    COUNT(s.id) as total_sesiones,
                    COALESCE(SUM(s.duracion_segundos), 0) as total_segundos,
                    COALESCE(MAX(s.fecha), h.fecha_creacion::date) as ultima_sesion
                FROM habitos h
                LEFT JOIN sesiones s ON h.id = s.habito_id
                WHERE h.usuario_id = %s
                GROUP BY h.id
                ORDER BY h.id DESC
            """, (usuario_id,))
            
            habitos = self.cursor.fetchall()
            
            # Calcular rachas para cada hábito
            for habito in habitos:
                racha = self.calcular_racha_habito(habito['id'])
                habito['racha_dias'] = racha
            
            return habitos
            
        except Exception as e:
            print(f"Error obteniendo hábitos: {e}")
            return []

    def obtener_habito_por_id(self, habito_id):
        try:
            self.cursor.execute("""
                SELECT h.*, 
                    COUNT(s.id) as total_sesiones,
                    COALESCE(SUM(s.duracion_segundos), 0) as total_segundos
                FROM habitos h
                LEFT JOIN sesiones s ON h.id = s.habito_id
                WHERE h.id = %s
                GROUP BY h.id
            """, (habito_id,))
            
            habito = self.cursor.fetchone()
            
            if habito:
                # Calcular estadísticas adicionales
                habito['racha_dias'] = self.calcular_racha_habito(habito_id)
                habito['promedio_minutos'] = self.calcular_promedio_minutos(habito_id)
                habito['minutos_hoy'] = self.obtener_minutos_hoy(habito_id)
            
            return habito
            
        except Exception as e:
            print(f"Error obteniendo hábito: {e}")
            return None

    def eliminar_habito(self, habito_id):
        try:
            self.cursor.execute("DELETE FROM habitos WHERE id = %s", (habito_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error eliminando hábito: {e}")
            return False

    # =================== MÉTODOS DE SESIONES ===================
    def registrar_sesion(self, habito_id, duracion_segundos, hora_inicio=None, hora_fin=None, notas=""):
        try:
            if hora_inicio is None:
                hora_inicio = datetime.now()
            
            self.cursor.execute("""
                INSERT INTO sesiones (habito_id, fecha, hora_inicio, hora_fin, duracion_segundos, notas)
                VALUES (%s, CURRENT_DATE, %s, %s, %s, %s)
                RETURNING id
            """, (habito_id, hora_inicio, hora_fin, duracion_segundos, notas))
            
            sesion = self.cursor.fetchone()
            self.conn.commit()
            
            return sesion
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error registrando sesión: {e}")
            return None

    def obtener_sesiones_habito(self, habito_id, limite=7):
        try:
            self.cursor.execute("""
                SELECT fecha, duracion_segundos, hora_inicio, hora_fin, notas
                FROM sesiones
                WHERE habito_id = %s
                ORDER BY fecha DESC
                LIMIT %s
            """, (habito_id, limite))
            
            return self.cursor.fetchall()
            
        except Exception as e:
            print(f"Error obteniendo sesiones: {e}")
            return []

    def obtener_minutos_hoy(self, habito_id):
        try:
            self.cursor.execute("""
                SELECT SUM(duracion_segundos) as total_segundos
                FROM sesiones
                WHERE habito_id = %s AND fecha = CURRENT_DATE
            """, (habito_id,))
            
            resultado = self.cursor.fetchone()
            if resultado and resultado['total_segundos']:
                return resultado['total_segundos'] // 60
            return 0
            
        except Exception as e:
            print(f"Error obteniendo minutos hoy: {e}")
            return 0

    # =================== MÉTODOS DE ESTADÍSTICAS ===================
    def calcular_racha_habito(self, habito_id):
        try:
            self.cursor.execute("""
                SELECT fecha FROM sesiones 
                WHERE habito_id = %s 
                ORDER BY fecha DESC
                LIMIT 7
            """, (habito_id,))
            
            sesiones = self.cursor.fetchall()
            
            if not sesiones:
                return 0
            
            hoy = datetime.now().date()
            racha = 0
            
            # Verificar si hoy hubo sesión
            if sesiones[0]['fecha'] == hoy:
                racha = 1
                # Verificar días consecutivos anteriores
                for i in range(1, len(sesiones)):
                    fecha_esperada = hoy - timedelta(days=i)
                    if sesiones[i]['fecha'] == fecha_esperada:
                        racha += 1
                    else:
                        break
            
            return racha
            
        except Exception as e:
            print(f"Error calculando racha: {e}")
            return 0

    def calcular_promedio_minutos(self, habito_id):
        try:
            self.cursor.execute("""
                SELECT AVG(duracion_segundos) as promedio_segundos
                FROM sesiones
                WHERE habito_id = %s
            """, (habito_id,))
            
            resultado = self.cursor.fetchone()
            if resultado and resultado['promedio_segundos']:
                return int(resultado['promedio_segundos'] // 60)
            return 0
            
        except Exception as e:
            print(f"Error calculando promedio: {e}")
            return 0

# En la clase BaseDatos, añade este método:

    def obtener_estadisticas_usuario(self, usuario_id):
        try:
            self.cursor.execute("""
                SELECT 
                    COUNT(DISTINCT h.id) as total_habitos,
                    COUNT(DISTINCT s.id) as total_sesiones,
                    COALESCE(SUM(s.duracion_segundos), 0) as total_segundos
                FROM habitos h
                LEFT JOIN sesiones s ON h.id = s.habito_id
                WHERE h.usuario_id = %s
            """, (usuario_id,))
            
            stats = self.cursor.fetchone()
            
            if not stats:
                return {
                    'total_habitos': 0,
                    'total_sesiones': 0,
                    'total_segundos': 0,
                    'racha_total': 0
                }
            
            # Calcular racha total
            racha_total = self.calcular_racha_total(usuario_id)
            
            return {
                'total_habitos': stats['total_habitos'],
                'total_sesiones': stats['total_sesiones'],
                'total_segundos': stats['total_segundos'],
                'racha_total': racha_total
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                'total_habitos': 0,
                'total_sesiones': 0,
                'total_segundos': 0,
                'racha_total': 0
            }
        
    def calcular_racha_total(self, usuario_id):
        try:
            self.cursor.execute("""
                SELECT DISTINCT s.fecha 
                FROM sesiones s
                JOIN habitos h ON s.habito_id = h.id
                WHERE h.usuario_id = %s
                ORDER BY s.fecha DESC
                LIMIT 7
            """, (usuario_id,))
            
            fechas_sesiones = self.cursor.fetchall()
            
            if not fechas_sesiones:
                return 0
            
            hoy = datetime.now().date()
            racha = 0
            
            # Verificar si hoy hubo sesión
            if fechas_sesiones[0]['fecha'] == hoy:
                racha = 1
                # Verificar días consecutivos anteriores
                for i in range(1, len(fechas_sesiones)):
                    fecha_esperada = hoy - timedelta(days=i)
                    if fechas_sesiones[i]['fecha'] == fecha_esperada:
                        racha += 1
                    else:
                        break
            
            return racha
            
        except Exception as e:
            print(f"Error calculando racha total: {e}")
            return 0

    # =================== MÉTODOS DE RECORDATORIOS ===================
    def actualizar_recordatorio(self, habito_id, activo, hora_inicio=None, hora_fin=None):
        try:
            self.cursor.execute("""
                UPDATE recordatorios 
                SET activo = %s, hora_inicio = %s, hora_fin = %s
                WHERE habito_id = %s
            """, (activo, hora_inicio, hora_fin, habito_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error actualizando recordatorio: {e}")
            return False

    def obtener_recordatorio(self, habito_id):
        try:
            self.cursor.execute("""
                SELECT activo, hora_inicio, hora_fin
                FROM recordatorios
                WHERE habito_id = %s
            """, (habito_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error obteniendo recordatorio: {e}")
            return None

    def cerrar_conexion(self):
        self.cursor.close()
        self.conn.close()
        print("Conexión cerrada")