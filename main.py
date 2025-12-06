from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.text import LabelBase
import os

from database import BaseDatos
from screens.login_screen import LoginScreen
from screens.registro_screen import RegisterScreen
from screens.inicio_screen import InicioScreen
from screens.detalle_habito_screen import DetalleHabitoScreen  # NUEVO NOMBRE

Window.size = (360, 640)

class HabitTrackerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        try:
            self.base_datos = BaseDatos()
            print("Base de datos conectada")
        except Exception as e:
            print(f" No se pudo conectar a la base de datos: {e}")
            exit(1)
        
        self.usuario_actual = None
        self.habito_seleccionado = None
        self.gestor_pantallas = ScreenManager()
    
    def build(self):
        # REGISTRAR FUENTE DE ICONOS
        try:
            ruta_actual = os.path.dirname(os.path.abspath(__file__))
            ruta_fuente = os.path.join(ruta_actual, "assets", "materialdesignicons-webfont.ttf")
            
            if os.path.exists(ruta_fuente):
                LabelBase.register(name="MaterialDesignIcons", fn_regular=ruta_fuente)
                print("Fuente de iconos registrada")
            else:
                print("No se encontró la fuente de iconos")
                # Usar iconos de texto si no hay fuente
        except Exception as e:
            print(f"Error al registrar fuente: {e}")
        
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        
        self.cargar_archivos_kv()
        
        pantalla_login = LoginScreen(name='login')
        pantalla_registro = RegisterScreen(name='registro')
        pantalla_inicio = InicioScreen(name='inicio')
        pantalla_detalle = DetalleHabitoScreen(name='detalle_habito')  # NUEVO NOMBRE
        
        pantalla_login.app = self
        pantalla_registro.app = self
        pantalla_inicio.app = self
        pantalla_detalle.app = self
        
        self.gestor_pantallas.add_widget(pantalla_login)
        self.gestor_pantallas.add_widget(pantalla_registro)
        self.gestor_pantallas.add_widget(pantalla_inicio)
        self.gestor_pantallas.add_widget(pantalla_detalle)
        
        return self.gestor_pantallas
    
    def cargar_archivos_kv(self):
        Builder.load_file('screens/login_screen.kv')
        Builder.load_file('screens/registro_screen.kv')
        Builder.load_file('screens/inicio_screen.kv')
        Builder.load_file('screens/detalle_habito_screen.kv')  # CARGAR EL NUEVO KV
    
    def cambiar_pantalla(self, nombre_pantalla, direccion='left'):
        self.gestor_pantallas.transition = SlideTransition(direction=direccion)
        self.gestor_pantallas.current = nombre_pantalla
    
    def cerrar_sesion(self):
        self.usuario_actual = None
        self.habito_seleccionado = None
        self.cambiar_pantalla('login', direccion='right')
    
    def on_stop(self):
        if hasattr(self, 'base_datos'):
            self.base_datos.cerrar_conexion()
        return super().on_stop()

if __name__ == '__main__':
    HabitTrackerApp().run()