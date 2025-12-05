# screens/register_screen.py
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.uix.screenmanager import SlideTransition
import re

class RegisterScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None  # Se asignará desde main.py
    
    def on_pre_enter(self):
        # Limpiar campos al entrar
        self.ids.username.text = ""
        self.ids.email.text = ""
        self.ids.contrasena.text = ""
        self.ids.confirmar_contra.text = ""
        self.ids.error_form.text = ""
    
    def validate_form(self):
        username = self.ids.username.text.strip()
        email = self.ids.email.text.strip()
        contrasena = self.ids.contrasena.text
        confirm = self.ids.confirmar_contra.text
        
        # Validaciones
        if not username or not email or not contrasena:
            return "Por favor completa todos los campos"
        
        if len(username) < 3:
            return "El usuario debe tener al menos 3 caracteres"
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Email inválido"
        
        if len(contrasena) < 6:
            return "La contraseña debe tener al menos 6 caracteres"
        
        if contrasena != confirm:
            return "Las contraseñas no coinciden"
        
        return None
    
    def registrar(self):
        # Validar formulario
        error = self.validate_form()
        if error:
            self.ids.error_form.text = error
            return
        
        username = self.ids.username.text.strip()
        email = self.ids.email.text.strip()
        contrasena = self.ids.contrasena.text
        
        # Registrar usuario
        result = self.app.base_datos.registrar_usuario(username, email, contrasena)
        
        if result["exito"]:
            self.show_success("¡Registro exitoso!\nAhora puedes iniciar sesión")
        else:
            self.ids.error_form.text = result["message"]
    
    def show_success(self, message):
        self.dialog = MDDialog(
            text=message,
            buttons=[
                MDFlatButton(
                    text="Iniciar Sesión",
                    on_release=self.go_to_login
                )
            ]
        )
        self.dialog.open()
    
    def go_to_login(self, *args):
        if hasattr(self, 'dialog'):
            self.dialog.dismiss()
        self.manager.current = 'login'
        self.manager.transition = SlideTransition(direction='left')
    
    def go_back(self):
        self.manager.current = 'login'
        self.manager.transition = SlideTransition(direction='left')