import psycopg2
import bcrypt
from psycopg2.extras import RealDictCursor

class Database:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host="localhost",
                database="habitos_bd",
                user="postgres", 
                password="master.1",
                port="5432"
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("conectado")
            self.crear_tablas()
        except Exception as e:
            print(f"Error: {e}")
            raise
    
    def crear_tablas(self):
        try:
            # Tabla de usuarios
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índice para búsquedas rápidas para la validacion de credenciales
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users(username)
            """)
            
            self.conn.commit()
            print("tablas creadas")
            
        except Exception as e:
            print(f"Error {e}")
            self.conn.rollback()
    
    # metodos de login y registro con contraseña encriptada cuando se registra
    def hash_contrasena(self, password):
        # Generar salt, hash y convertirlos a string ára guardar
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verificar_contrasena(self, password, hashed_password):
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except:
            return False
    
    def registrar_user(self, username, email, password):
        try:
            # Verificar si el usuario ya existe
            self.cursor.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email)
            )
            
            if self.cursor.fetchone():
                return {"success": False, "message": "Usuario o email ya existen"}
            
            # Encriptar contraseña
            password_hash = self.hash_contrasena(password)
            
            # Insertar nuevo usuario
            self.cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, username, email, created_at
            """, (username, email, password_hash))
            
            new_user = self.cursor.fetchone()
            self.conn.commit()
            
            print(f"Usuario registrado: {username}")
            return {
                "success": True, 
                "user": new_user,
                "message": "Registro exitoso"
            }
            
        except Exception as e:
            self.conn.rollback()
            return {"success": False, "message": f"Error: {e}"}
    
    def login_user(self, username_or_email, password):
        try:
            # Buscar usuario por username o email
            self.cursor.execute("""
                SELECT id, username, email, password_hash 
                FROM users 
                WHERE username = %s OR email = %s
            """, (username_or_email, username_or_email))
            
            user = self.cursor.fetchone()
            
            if not user:
                return {"success": False, "message": "Usuario no encontrado"}
            
            # Verificar contraseña encriptada
            if self.verificar_contrasena(password, user['password_hash']):
                print(f"exito: {user['username']}")
                return {
                    "success": True,
                    "user": {
                        "id": user['id'],
                        "username": user['username'],
                        "email": user['email']
                    },
                    "message": "Login exitoso"
                }
            else:
                return {"success": False, "message": "Contraseña incorrecta"}
                
        except Exception as e:
            print(f"Error: {e}")
            return {"success": False, "message": f"Error: {e}"}
    
    def usuario_existe(self, username, email):
        try:
            self.cursor.execute("""
                SELECT username, email FROM users 
                WHERE username = %s OR email = %s
            """, (username, email))
            
            existing = self.cursor.fetchall()
            usernames = [u['username'] for u in existing]
            emails = [u['email'] for u in existing]
            
            return {
                "username_exists": username in usernames,
                "email_exists": email in emails
            }
        except Exception as e:
            print(f"Error verificando usuario: {e}")
            return {"username_exists": False, "email_exists": False}
    
    def close(self):
        self.cursor.close()
        self.conn.close()