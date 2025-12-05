from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.screenmanager import SlideTransition
from kivy.properties import StringProperty, NumericProperty
from datetime import datetime

class HabitCard(MDCard):
    habit_id = None
    nombre = StringProperty("")
    descripcion = StringProperty("")
    sesiones = NumericProperty(0)
    racha = NumericProperty(0)
    total_min = NumericProperty(0)
    objetivo = NumericProperty(30)
    
    def __init__(self, **kwargs):
        self.habit_id = kwargs.pop('habit_id', None)
        
        # Extraer valores antes de llamar a super()
        nombre_value = kwargs.pop('nombre', "")
        descripcion_value = kwargs.pop('descripcion', "")
        sesiones_value = kwargs.pop('sesiones', 0)
        racha_value = kwargs.pop('racha', 0)
        total_min_value = kwargs.pop('total_min', 0)
        objetivo_value = kwargs.pop('objetivo', 30)
        
        super().__init__(**kwargs)
        
        # Asignar valores después de inicializar
        self.nombre = nombre_value
        self.descripcion = descripcion_value
        self.sesiones = sesiones_value
        self.racha = racha_value
        self.total_min = total_min_value
        self.objetivo = objetivo_value
        
        # Crear menú contextual
        self.menu = None
        self.crear_menu_contextual()
    
    def crear_menu_contextual(self):
        menu_items = [
            {
                "text": "Editar",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.editar_habito(),
            },
            {
                "text": "Eliminar",
                "viewclass": "OneLineListItem", 
                "on_release": lambda: self.eliminar_habito(),
            },
        ]
        
        self.menu = MDDropdownMenu(
            caller=self,
            items=menu_items,
            width_mult=4,
        )
    
    def editar_habito(self):
        self.menu.dismiss()
        # Buscar la pantalla InicioScreen
        if hasattr(self, 'app') and hasattr(self.app, 'gestor_pantallas'):
            for screen in self.app.gestor_pantallas.screens:
                if isinstance(screen, InicioScreen):
                    screen.editar_habito_dialog(self.habit_id)
                    break
    
    def eliminar_habito(self):
        self.menu.dismiss()
        # Buscar la pantalla InicioScreen
        if hasattr(self, 'app') and hasattr(self.app, 'gestor_pantallas'):
            for screen in self.app.gestor_pantallas.screens:
                if isinstance(screen, InicioScreen):
                    screen.eliminar_habito_dialog(self.habit_id)
                    break
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.button == 'right':  # Click derecho para menú contextual
                if self.menu:
                    self.menu.open()
                return True
        return super().on_touch_down(touch)
    
    def on_release(self):
        # Solo para click normal (izquierdo)
        pass

class NuevoHabitoForm(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 15
        self.padding = 10
        self.size_hint_y = None
        self.height = 350
        
        self.nombre_field = MDTextField(
            hint_text="Nombre del hábito",
            mode="rectangle",
            size_hint_y=None,
            height=50
        )
        self.add_widget(self.nombre_field)
        
        self.desc_field = MDTextField(
            hint_text="Descripción (opcional)",
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=80
        )
        self.add_widget(self.desc_field)
        
        self.obj_field = MDTextField(
            hint_text="Objetivo diario (minutos)",
            mode="rectangle",
            size_hint_y=None,
            height=50,
            input_filter="int"
        )
        self.obj_field.text = "30"
        self.add_widget(self.obj_field)
        
        self.cat_field = MDTextField(
            hint_text="Categoría (Salud, Aprendizaje, etc.)",
            mode="rectangle",
            size_hint_y=None,
            height=50
        )
        self.cat_field.text = "Salud"
        self.add_widget(self.cat_field)

class InicioScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None 
        self.current_user_id = None
        self.dialog = None
    
    def on_pre_enter(self):
        if self.app and self.app.usuario_actual:
            self.current_user_id = self.app.usuario_actual["id"]
            username = self.app.usuario_actual.get("nombre_usuario", "Usuario")
            
            if hasattr(self.ids, 'bienvenido'):
                self.ids.bienvenido.text = f"¡Hola, {username}!"
            
            self.cargar_estadisticas()
            self.calcular_progreso_general()
            self.load_habits()
    
    def cargar_estadisticas(self):
        if not self.app or not hasattr(self.app, 'base_datos'):
            return
            
        try:
            estadisticas = self.app.base_datos.obtener_estadisticas_usuario(self.current_user_id)
            
            if hasattr(self.ids, 'sesiones'):
                self.ids.sesiones.text = str(estadisticas.get('total_sesiones', 0))
            
            if hasattr(self.ids, 'tiempo'):
                total_min = estadisticas.get('total_segundos', 0) // 60
                self.ids.tiempo.text = str(total_min)
            
            if hasattr(self.ids, 'racha'):
                self.ids.racha.text = str(estadisticas.get('racha_total', 0))
            
            if hasattr(self.ids, 'hoy'):
                minutos_hoy = self.obtener_minutos_hoy_usuario()
                self.ids.hoy.text = str(minutos_hoy)
                
        except Exception as e:
            print(f"Error cargando estadísticas: {e}")
    
    def calcular_progreso_general(self):
        """Calcula el progreso general de todos los hábitos"""
        if not self.app or not hasattr(self.app, 'base_datos'):
            return
        
        try:
            habits = self.app.base_datos.obtener_habitos_usuario(self.current_user_id)
            
            if not habits:
                # Si no hay hábitos, progreso 0%
                if hasattr(self.ids, 'barra_progreso_general'):
                    self.ids.barra_progreso_general.value = 0
                if hasattr(self.ids, 'progreso_general_porcentaje'):
                    self.ids.progreso_general_porcentaje.text = "0%"
                if hasattr(self.ids, 'progreso_general_texto'):
                    self.ids.progreso_general_texto.text = "Progreso General"
                return
            
            total_objetivo = 0
            total_realizado = 0
            
            for habit in habits:
                objetivo = habit.get('objetivo_diario_minutos', 30)
                total_objetivo += objetivo
                
                # Obtener minutos de hoy para este hábito
                minutos_hoy = self.app.base_datos.obtener_minutos_hoy(habit['id'])
                total_realizado += min(minutos_hoy, objetivo)  # Máximo el objetivo
            
            if total_objetivo > 0:
                porcentaje = int((total_realizado / total_objetivo) * 100)
            else:
                porcentaje = 0
            
            # Actualizar la barra de progreso
            if hasattr(self.ids, 'barra_progreso_general'):
                self.ids.barra_progreso_general.value = porcentaje
            
            if hasattr(self.ids, 'progreso_general_porcentaje'):
                self.ids.progreso_general_porcentaje.text = f"{porcentaje}%"
            
            if hasattr(self.ids, 'progreso_general_texto'):
                self.ids.progreso_general_texto.text = f"Progreso General"
                
        except Exception as e:
            print(f"Error calculando progreso general: {e}")
    
    def obtener_minutos_hoy_usuario(self):
        if not self.app or not hasattr(self.app, 'base_datos'):
            return 0
            
        try:
            habits = self.app.base_datos.obtener_habitos_usuario(self.current_user_id)
            total_minutos_hoy = 0
            
            for habit in habits:
                minutos_hoy = self.app.base_datos.obtener_minutos_hoy(habit['id'])
                total_minutos_hoy += minutos_hoy
            
            return total_minutos_hoy
        except Exception as e:
            print(f"Error obteniendo minutos hoy: {e}")
            return 0
    
    def load_habits(self):
        try:
            if hasattr(self.ids, 'habits_container'):
                self.ids.habits_container.clear_widgets()
                
                if hasattr(self.app, 'base_datos'):
                    habits = self.app.base_datos.obtener_habitos_usuario(self.current_user_id)
                    print(f"Cargando {len(habits)} hábitos para usuario {self.current_user_id}")
                else:
                    habits = []
                
                if not habits:
                    empty_label = MDLabel(
                        text="No tienes hábitos aún.\n\n¡Agrega uno para empezar!",
                        halign="center",
                        valign="middle",
                        theme_text_color="Custom",
                        text_color=(0.6, 0.6, 0.6, 1),
                        font_style="H6",
                        size_hint_y=None,
                        height=200
                    )
                    self.ids.habits_container.add_widget(empty_label)
                else:
                    for habit in habits:
                        sesiones = habit.get('total_sesiones', 0)
                        racha = habit.get('racha_dias', 0)
                        total_min = habit.get('total_segundos', 0) // 60 if habit.get('total_segundos') else 0
                        objetivo = habit.get('objetivo_diario_minutos', 30)
                        desc = habit.get('descripcion', '')
                        
                        card = HabitCard(
                            habit_id=habit['id'],
                            nombre=habit['nombre'],
                            descripcion=desc,
                            sesiones=sesiones,
                            racha=racha,
                            total_min=total_min,
                            objetivo=objetivo
                        )
                        
                        # Asignar referencia a la app
                        card.app = self.app
                        
                        card.bind(on_release=lambda x, h=habit['id']: self.ver_detalle_habito(h))
                        self.ids.habits_container.add_widget(card)
                        
        except Exception as e:
            print(f"Error cargando hábitos: {e}")
            import traceback
            traceback.print_exc()
    
    def ver_detalle_habito(self, habit_id):
        if self.app and hasattr(self.app, 'base_datos'):
            try:
                habito = self.app.base_datos.obtener_habito_por_id(habit_id)
                if habito:
                    self.app.habito_seleccionado = habito
                    self.manager.current = 'detalle_habito'
                    self.manager.transition.direction = 'left'
            except Exception as e:
                print(f"Error al obtener hábito: {e}")

    def add_new_habit(self):
        self.dialog = MDDialog(
            title="Nuevo Hábito",
            type="custom",
            content_cls=NuevoHabitoForm(),
            buttons=[
                MDRaisedButton(
                    text="Cancelar",
                    md_bg_color=(0.6, 0.6, 0.6, 1),
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Crear",
                    md_bg_color=(0.2, 0.5, 0.9, 1),
                    on_release=self.crear_habito
                )
            ],
            size_hint=(0.8, None)
        )
        self.dialog.open()
    
    def crear_habito(self, *args):
        if not self.dialog:
            return
        
        form = self.dialog.content_cls
        
        nombre = form.nombre_field.text.strip()
        descripcion = form.desc_field.text.strip()
        objetivo_text = form.obj_field.text.strip()
        categoria = form.cat_field.text.strip()
        
        if not nombre:
            return
        
        try:
            objetivo = int(objetivo_text) if objetivo_text else 30
        except:
            objetivo = 30
        
        if not categoria:
            categoria = "Salud"
        
        if hasattr(self.app, 'base_datos'):
            habito = self.app.base_datos.crear_habito(
                self.current_user_id,
                nombre,
                descripcion,
                objetivo,
                categoria
            )
            
            if habito:
                self.dialog.dismiss()
                self.cargar_estadisticas()
                self.calcular_progreso_general()
                self.load_habits()
    
    def editar_habito_dialog(self, habit_id):
        """Muestra diálogo para editar hábito"""
        habito = self.app.base_datos.obtener_habito_por_id(habit_id)
        if not habito:
            return
        
        form = NuevoHabitoForm()
        form.nombre_field.text = habito['nombre']
        form.desc_field.text = habito.get('descripcion', '')
        form.obj_field.text = str(habito.get('objetivo_diario_minutos', 30))
        form.cat_field.text = habito.get('categoria', 'Salud')
        
        self.dialog = MDDialog(
            title="Editar Hábito",
            type="custom",
            content_cls=form,
            buttons=[
                MDRaisedButton(
                    text="Cancelar",
                    md_bg_color=(0.6, 0.6, 0.6, 1),
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Guardar Cambios",
                    md_bg_color=(0.2, 0.5, 0.9, 1),
                    on_release=lambda x: self.actualizar_habito(habit_id)
                )
            ],
            size_hint=(0.8, None)
        )
        self.dialog.open()
    
    def actualizar_habito(self, habit_id):
        """Actualiza un hábito existente"""
        if not self.dialog:
            return
        
        form = self.dialog.content_cls
        
        nombre = form.nombre_field.text.strip()
        descripcion = form.desc_field.text.strip()
        objetivo_text = form.obj_field.text.strip()
        categoria = form.cat_field.text.strip()
        
        if not nombre:
            return
        
        try:
            objetivo = int(objetivo_text) if objetivo_text else 30
        except:
            objetivo = 30
        
        if not categoria:
            categoria = "Salud"
        
        if hasattr(self.app, 'base_datos'):
            resultado = self.app.base_datos.actualizar_habito(
                habit_id,
                nombre,
                descripcion,
                objetivo,
                categoria
            )
            
            if resultado:
                self.dialog.dismiss()
                self.cargar_estadisticas()
                self.calcular_progreso_general()
                self.load_habits()
    
    def eliminar_habito_dialog(self, habit_id):
        """Muestra diálogo de confirmación para eliminar hábito"""
        habito = self.app.base_datos.obtener_habito_por_id(habit_id)
        if not habito:
            return
        
        self.dialog = MDDialog(
            title=f"Eliminar '{habito['nombre']}'",
            text="¿Estás seguro de que quieres eliminar este hábito?\nEsta acción no se puede deshacer.",
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    theme_text_color="Custom",
                    text_color=(0.7, 0.7, 0.7, 1),
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Eliminar",
                    md_bg_color=(1, 0.3, 0.3, 1),
                    on_release=lambda x: self.eliminar_habito(habit_id)
                )
            ],
            size_hint=(0.8, None)
        )
        self.dialog.open()
    
    def eliminar_habito(self, habit_id):
        """Elimina un hábito"""
        if hasattr(self.app, 'base_datos'):
            resultado = self.app.base_datos.eliminar_habito(habit_id)
            
            if resultado:
                self.dialog.dismiss()
                self.cargar_estadisticas()
                self.calcular_progreso_general()
                self.load_habits()
    
    def logout(self):
        if self.app:
            self.app.cerrar_sesion()