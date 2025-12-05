from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
import time

class DetalleHabitoScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.habito_actual = None
        self.temporizador_activo = False
        self.tiempo_inicio = None
        self.tiempo_transcurrido = 0
        self.evento_temporizador = None
        self.recordatorio_activo = False
    
    def on_pre_enter(self):
        if self.app and hasattr(self.app, 'habito_seleccionado'):
            self.habito_actual = self.app.habito_seleccionado
            self.actualizar_pantalla()
    
    def actualizar_pantalla(self):
        if not self.habito_actual:
            return
        
        if hasattr(self.ids, 'nombre_habito'):
            self.ids.nombre_habito.text = self.habito_actual['nombre']
        
        if hasattr(self.ids, 'descripcion_habito'):
            desc = self.habito_actual.get('descripcion', '')
            self.ids.descripcion_habito.text = desc
        
        self.actualizar_barra_progreso()
        self.actualizar_estadisticas()
    
    def obtener_estadisticas_habito(self):
        if self.app and self.habito_actual and hasattr(self.app, 'base_datos'):
            habito_completo = self.app.base_datos.obtener_habito_por_id(self.habito_actual['id'])
            if habito_completo:
                return {
                    'minutos_hoy': habito_completo.get('minutos_hoy', 0),
                    'total_minutos': habito_completo.get('total_segundos', 0) // 60,
                    'racha_dias': habito_completo.get('racha_dias', 0),
                    'promedio_minutos': habito_completo.get('promedio_minutos', 0)
                }
        return {'minutos_hoy': 0, 'total_minutos': 0, 'racha_dias': 0, 'promedio_minutos': 0}
    
    def actualizar_barra_progreso(self):
        if not self.habito_actual:
            return
        
        estadisticas = self.obtener_estadisticas_habito()
        objetivo = self.habito_actual.get('objetivo_diario_minutos', 30)
        hoy = estadisticas.get('minutos_hoy', 0)
        porcentaje = min(100, int((hoy / objetivo) * 100)) if objetivo > 0 else 0
        
        if hasattr(self.ids, 'barra_progreso'):
            self.ids.barra_progreso.value = porcentaje
        
        if hasattr(self.ids, 'progreso_texto'):
            self.ids.progreso_texto.text = f"{porcentaje}%"
        
        if hasattr(self.ids, 'progreso_minutos'):
            self.ids.progreso_minutos.text = f"{hoy}/{objetivo} min"
    
    def actualizar_estadisticas(self):
        estadisticas = self.obtener_estadisticas_habito()
        
        if hasattr(self.ids, 'hoy_valor'):
            self.ids.hoy_valor.text = f"{estadisticas['minutos_hoy']}m"
        
        if hasattr(self.ids, 'total_valor'):
            self.ids.total_valor.text = f"{estadisticas['total_minutos']}m"
        
        if hasattr(self.ids, 'racha_valor'):
            self.ids.racha_valor.text = f"{estadisticas['racha_dias']}d"
        
        if hasattr(self.ids, 'promedio_valor'):
            self.ids.promedio_valor.text = f"{estadisticas['promedio_minutos']}m"
    
    def iniciar_temporizador(self):
        if not self.temporizador_activo:
            self.temporizador_activo = True
            self.tiempo_inicio = time.time()
            
            if hasattr(self.ids, 'boton_iniciar'):
                self.ids.boton_iniciar.disabled = True
            
            if hasattr(self.ids, 'boton_detener'):
                self.ids.boton_detener.disabled = False
            
            self.evento_temporizador = Clock.schedule_interval(self.actualizar_temporizador, 0.1)
    
    def detener_temporizador(self):
        if self.temporizador_activo:
            self.temporizador_activo = False
            tiempo_final = time.time()
            duracion_segundos = int(tiempo_final - self.tiempo_inicio)
            
            self.guardar_sesion(duracion_segundos)
            self.actualizar_barra_progreso()
            self.actualizar_estadisticas()
            
            if hasattr(self.ids, 'boton_iniciar'):
                self.ids.boton_iniciar.disabled = False
            
            if hasattr(self.ids, 'boton_detener'):
                self.ids.boton_detener.disabled = True
            
            if hasattr(self.ids, 'display_tiempo'):
                self.ids.display_tiempo.text = "00:00:00"
            
            if self.evento_temporizador:
                Clock.unschedule(self.evento_temporizador)
    
    def actualizar_temporizador(self, dt):
        if self.temporizador_activo and self.tiempo_inicio:
            tiempo_actual = time.time()
            duracion = int(tiempo_actual - self.tiempo_inicio)
            
            horas = duracion // 3600
            minutos = (duracion % 3600) // 60
            segundos = duracion % 60
            
            if hasattr(self.ids, 'display_tiempo'):
                self.ids.display_tiempo.text = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    
    def guardar_sesion(self, duracion_segundos):
        if self.habito_actual and self.app and hasattr(self.app, 'base_datos'):
            resultado = self.app.base_datos.registrar_sesion(
                self.habito_actual['id'],
                duracion_segundos
            )
            
            if resultado:
                print(f"Sesión registrada: {duracion_segundos} segundos")
    
    def activar_recordatorio(self, activo):
        self.recordatorio_activo = activo
        
        if hasattr(self.ids, 'boton_activar'):
            self.ids.boton_activar.md_bg_color = (0.16, 0.73, 0.51, 0.2) if activo else (0, 0, 0, 0)
        
        if hasattr(self.ids, 'boton_desactivar'):
            self.ids.boton_desactivar.md_bg_color = (1, 0.3, 0.3, 0.2) if not activo else (0, 0, 0, 0)
    
    def guardar_recordatorio(self):
        if not hasattr(self.ids, 'campo_hora_inicio') or not hasattr(self.ids, 'campo_hora_fin'):
            return
        
        hora_inicio = self.ids.campo_hora_inicio.text
        hora_fin = self.ids.campo_hora_fin.text
        
        if not hora_inicio or not hora_fin:
            print("Error: Debes ingresar horas de inicio y fin")
            return
        
        if self.habito_actual and self.app and hasattr(self.app, 'base_datos'):
            resultado = self.app.base_datos.actualizar_recordatorio(
                self.habito_actual['id'],
                self.recordatorio_activo,
                hora_inicio,
                hora_fin
            )
            
            if resultado:
                print(f"Recordatorio guardado: {hora_inicio} - {hora_fin}")
    
    def volver_atras(self):
        self.manager.current = 'inicio'
        self.manager.transition.direction = 'right'