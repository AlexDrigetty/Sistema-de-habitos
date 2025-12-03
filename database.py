import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="habitos_bd",
            user="postgres",
            password="master.1",
            port="5432",
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        print("conectado")
        self.crear_tablas()

    def crear_tablas(self):
        try:
            # tabla de usuarios
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    contrasena VARCHAR(255) NOT NULL,
                    fecha_crea TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # tabla de hábitos
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS habitos (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                    titulo VARCHAR(100) NOT NULL,
                    fecha_crea TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # tabla de progreso diario
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS progreso_habitos (
                    id SERIAL PRIMARY KEY,
                    habito_id INTEGER NOT NULL REFERENCES habitos(id) ON DELETE CASCADE,
                    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
                    realizadas BOOLEAN NOT NULL DEFAULT TRUE,
                    UNIQUE(habito_id, fecha)
                )
            """)
            # índice
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username ON usuarios(username)
            """)
            self.conn.commit()
            print("tablas creadas")
        except Exception as e:
            self.conn.rollback()
            print(f"Error creando tablas: {e}")

    # Auth 
    def hash_contrasena(self, password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verificar_contrasena(self, password, hashed_password):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    def registrar_user(self, username, email, password):
        try:
            self.cursor.execute(
                "SELECT id FROM usuarios WHERE username=%s OR email=%s",
                (username, email),
            )
            if self.cursor.fetchone():
                return {"success": False, "message": "Usuario o email ya existen"}

            contrasena = self.hash_contrasena(password)
            self.cursor.execute("""
                INSERT INTO usuarios (username, email, contrasena)
                VALUES (%s, %s, %s)
                RETURNING id, username, email, fecha_crea
            """, (username, email, contrasena))
            user = self.cursor.fetchone()
            self.conn.commit()
            print(f"Usuario registrado: {username}")
            return {"success": True, "user": user}
        except Exception as e:
            self.conn.rollback()
            return {"success": False, "message": str(e)}

    def login_user(self, username_or_email, password):
        try:
            self.cursor.execute("""
                SELECT id, username, email, contrasena
                FROM usuarios
                WHERE username=%s OR email=%s
            """, (username_or_email, username_or_email))
            user = self.cursor.fetchone()
            if not user:
                return {"success": False, "message": "Usuario no encontrado"}

            if self.verificar_contrasena(password, user["contrasena"]):
                return {"success": True, "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                }}
            return {"success": False, "message": "Contraseña incorrecta"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def add_habit(self, user_id, titulo):
        try:
            self.cursor.execute("""
                INSERT INTO habitos (user_id, titulo)
                VALUES (%s, %s)
                RETURNING id, titulo, fecha_crea
            """, (user_id, titulo))
            habit = self.cursor.fetchone()
            self.conn.commit()
            return habit
        except Exception as e:
            self.conn.rollback()
            print(f"Error guardando hábito: {e}")
            return None

    def get_user_habits(self, user_id):
        try:
            self.cursor.execute("""
                SELECT id, titulo
                FROM habitos
                WHERE user_id=%s
                ORDER BY id DESC
            """, (user_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo hábitos: {e}")
            return []

    def update_habit_titulo(self, habito_id, new_titulo):
        try:
            self.cursor.execute(
                "UPDATE habitos SET titulo=%s WHERE id=%s",
                (new_titulo, habito_id)
            )
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            self.conn.rollback()
            return {"success": False, "message": str(e)}

    def update_habit_title(self, habito_id, new_titulo):  # Alias para compatibilidad
        return self.update_habit_titulo(habito_id, new_titulo)

    def marcar_habito(self, habito_id):
        try:
            self.cursor.execute("""
                INSERT INTO progreso_habitos (habito_id, fecha, realizadas)
                VALUES (%s, CURRENT_DATE, TRUE)
                ON CONFLICT (habito_id, fecha)
                DO UPDATE SET realizadas = TRUE
            """, (habito_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error marcando hábito: {e}")
            self.conn.rollback()
            return False

    def get_daily_progress(self, user_id):
        try:
            self.cursor.execute("SELECT COUNT(*) AS n FROM habitos WHERE user_id=%s", (user_id,))
            total = self.cursor.fetchone()["n"]

            self.cursor.execute("""
                SELECT COUNT(*) AS n
                FROM habitos h
                JOIN progreso_habitos p ON h.id=p.habito_id
                WHERE h.user_id=%s AND p.fecha=CURRENT_DATE AND p.realizadas IS TRUE
            """, (user_id,))
            completed = self.cursor.fetchone()["n"]
            return total, completed
        except Exception:
            return 0, 0

    def close(self):
        self.cursor.close()
        self.conn.close()