from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

# 1) Carga de credenciales
load_dotenv(dotenv_path="OPENAI_API.env")
api_key    = os.getenv("GEMINI_API_KEY")
email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("GMAIL_APP_PASSWORD")
email_to   = os.getenv("EMAIL_TO")

# 2) Definir horarios de cursos
cursos = {
    "Inteligencia Artificial": {
        "days": ["Mon", "Sun"],
        "times": {"Mon": "18:00–22:00", "Sun": "08:00–14:00"},
        "lugar": {"Mon": "Auditorio CINAR", "Sun": "Aula 101"}
    },
    "Inteligencia Artificial - Virtual": {
        "days": ["Mon", "Tue", "Thu"],
        "times": {"Mon": "18:00–22:00", "Tue": "18:00–22:00", "Thu": "18:00–22:00"},
        "lugar": {"Mon": "Plataforma https://imaster.academy/login/index.php", 
                  "Tue": "Plataforma https://imaster.academy/login/index.php", 
                  "Thu": "Plataforma https://imaster.academy/login/index.php"}
    }
}

# 3) Calcular día siguiente
mañana = datetime.now() + timedelta(days=1)
dia_abbr = mañana.strftime("%a")  # "Mon", "Tue", ...

# 4) Construir texto base
parrafos = []
for nombre, info in cursos.items():
    if dia_abbr in info["days"]:
        hora = info["times"][dia_abbr]
        lugar = info["lugar"][dia_abbr]
        parrafos.append(
            f"📚 *{nombre}*\n"
            f"🗓 Fecha: {mañana.strftime('%A, %d de %B')}\n"
            f"⏰ Horario: {hora}\n"
            f"📍 Lugar/Acceso: {lugar}\n"
        )
if not parrafos:
    print("No hay clases mañana. No se envía correo.")
    exit()

texto_crudo = "\n\n".join(parrafos)

# 5) Prompt
prompt = (
    "Eres un asistente que genera recordatorios de clase para campistas de TalentoTech. "
    "Reescribe el siguiente texto en un correo de párrafos motivadores y amistosos que incluya emojis referentes al curso. "
    "No puedes hacer referencia a comida ni usar la palabra 'Camper', usa 'campistas' en su lugar. "
    "Separa por curso si hay más de uno:\n\n" + texto_crudo
)

# 6) Consulta a Gemini (modelo gratuito: gemini-pro)
headers = {
    "Content-Type": "application/json"
}
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

payload = {
    "contents": [
        {
            "parts": [{"text": prompt}]
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)

if response.status_code != 200:
    print("Error al comunicarse con Gemini:", response.text)
    exit()

data = response.json()
cuerpo = data["candidates"][0]["content"]["parts"][0]["text"]

# 7) Preparar correo
email = EmailMessage()
email["From"]    = email_user
email["To"]      = email_to
email["Subject"] = f"Recordatorios de clases para {mañana.strftime('%A %d/%m/%Y')}"
email.set_content(cuerpo)

# 8) Enviar correo
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_pass)
        smtp.send_message(email)
    print("Correo enviado con éxito.")
except Exception as e:
    print("Error al enviar el correo:", e)
