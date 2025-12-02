from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from database import Database
from screens.login_screen import LoginScreen
from screens.registro_screen import RegisterScreen
from screens.inicio_screen import InicioScreen

Window.size = (360, 640)

class HabitTrackerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Inicializar base de datos
        try:
            self.db = Database()
        except Exception as e:
            print(f"No se pudo conectar a la base de datos: {e}")
            exit(1)
        
        # Variables de estado
        self.current_user = None
        self.screen_manager = ScreenManager()
    
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        
        # Cargar archivos kv
        self.cargar_archivos_kv()
        
        # Crear pantallas
        login_screen = LoginScreen(name='login')
        register_screen = RegisterScreen(name='registro')
        main_screen = InicioScreen(name='inicio')
        
        # Pasar referencia de la app a las pantallas
        login_screen.app = self
        register_screen.app = self
        main_screen.app = self
        
        # Agregar pantallas al manager
        self.screen_manager.add_widget(login_screen)
        self.screen_manager.add_widget(register_screen)
        self.screen_manager.add_widget(main_screen)
        
        return self.screen_manager
    
    def cargar_archivos_kv(self):
        Builder.load_file('screens/login_screen.kv')
        Builder.load_file('screens/registro_screen.kv')
        Builder.load_file('screens/inicio_screen.kv')
    
    def cambiar_pantallas(self, screen_name, direction='left'):
        self.screen_manager.transition = SlideTransition(direction=direction)
        self.screen_manager.current = screen_name
    
    def logout(self):
        self.current_user = None
        self.cambiar_pantallas('login', direction='right')
    
    def on_stop(self):
        if hasattr(self, 'db'):
            self.db.close()
        return super().on_stop()

if __name__ == '__main__':
    HabitTrackerApp().run()