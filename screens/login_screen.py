from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import SlideTransition

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None  # Se asignará desde main.py
    
    def on_pre_enter(self):
        # Limpiar campos al entrar
        if hasattr(self.ids, 'email'):
            self.ids.email.text = ""
        if hasattr(self.ids, 'contrasena'):
            self.ids.contrasena.text = ""
        if hasattr(self.ids, 'error_form'):
            self.ids.error_form.text = ""
    
    def login(self):
        email = self.ids.email.text
        password = self.ids.contrasena.text
        
        if not email or not password:
            self.ids.error_form.text = "Por favor completa todos los campos"
            return
        
        # Intentar login con la base de datos
        result = self.app.db.login_user(email, password)
        
        if result["success"]:
            # Guardar usuario en la app principal
            self.app.current_user = result["user"]
            self.ids.error_form.text = "" 
            self.manager.current = 'inicio'
            self.manager.transition = SlideTransition(direction='left')
        else:
            self.ids.error_form.text = result["message"]
    
    def go_to_registro(self):
        self.manager.current = 'registro'
        self.manager.transition = SlideTransition(direction='right')