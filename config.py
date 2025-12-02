import os

class Config:
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'habitos_bd',
        'user': 'postgres',
        'password': 'master.1',
        'port': '5432'
    }
    
    APP_NAME = "HabitTracker"
    SECRET_KEY = "clave-secreta-para-sesiones"