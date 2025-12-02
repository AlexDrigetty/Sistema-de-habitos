from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList, OneLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.uix.screenmanager import SlideTransition
from datetime import datetime

class HabitItem(OneLineAvatarIconListItem):
    def __init__(self, habit_id, text, **kwargs):
        super().__init__(text=text, **kwargs)
        self.habit_id = habit_id
        self.add_widget(IconLeftWidget(icon="checkbox-blank-circle-outline"))
        
        # Estilos personalizados para el item
        self.theme_text_color = "Custom"
        self.text_color = (1, 1, 1, 1) 
        self.bg_color = (0.15, 0.15, 0.15, 1) 

class InicioScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user_id = None 
    
    def on_pre_enter(self):
        # Verificar que tenemos usuario
        if self.app and self.app.current_user:
            self.current_user_id = self.app.current_user["id"]
            username = self.app.current_user.get("username", "Usuario")
            
            # Actualizar label de bienvenida
            if hasattr(self.ids, 'bienvenido'):
                self.ids.bienvenido.text = f"Bienvenido, {username}"
            
            self.load_habits()
        else:
            print("No hay usuario autenticado")
    
    def load_habits(self):
        try:
            # Verificar si el ID existe antes de usarlo
            if hasattr(self.ids, 'habits_list'):
                # Limpiar lista actual
                self.ids.habits_list.clear_widgets()
                
                # Obtener hábitos del usuario
                habits = self.app.db.get_user_habits(self.current_user_id)
                
                if not habits:
                    # Mostrar mensaje si no hay hábitos
                    self.ids.habits_list.add_widget(
                        MDLabel(
                            text="No tienes hábitos aún.\n\n¡Agrega uno para empezar!",
                            halign="center",
                            valign="middle",
                            theme_text_color="Custom",
                            text_color=(0.6, 0.6, 0.6, 1),
                            font_style="H6",
                            size_hint_y=None,
                            height=200
                        )
                    )
                else:
                    # Agregar cada hábito a la lista
                    for habit in habits:
                        item = HabitItem(
                            habit_id=habit['id'],
                            text=habit['name']
                        )
                        item.bind(on_release=self.view_habit_detail)
                        self.ids.habits_list.add_widget(item)
            else:
                print("No se encontró habitos en lista en la pantalla")
                
        except Exception as e:
            print(f"Error cargando hábitos: {e}")

    def logout(self):
        if self.app:
            self.app.logout()