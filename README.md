# 🔧 CRM Servicio Técnico — IA Powered

Sistema CRM con inteligencia artificial para gestión de servicio técnico. Lee e interpreta correos de Gmail, extrae datos de clientes, gestiona presupuestos y notifica por Telegram.

## ✨ Funcionalidades

- 📧 **Gmail integrado** — Lee, interpreta y redacta correos automáticamente con IA
- 🤖 **IA con Claude** — Extrae datos de envío (nombre, teléfono, dirección) de los correos
- 📊 **Google Sheets** — Base de conocimiento para responder consultas
- 💰 **Gestión de presupuestos** — Registra y hace seguimiento de presupuestos aceptados/rechazados
- 👥 **Base de clientes** — Historial completo de cada cliente con todos sus antecedentes
- 📱 **Bot Telegram** — Notificaciones en tiempo real y control desde Telegram
- 🖥️ **Dashboard web** — Panel de control desplegado en Railway

## 🏗️ Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11 + FastAPI |
| Base de datos | PostgreSQL |
| IA | Claude (Anthropic) |
| Email | Gmail API (OAuth2) |
| Sheets | Google Sheets API |
| Telegram | python-telegram-bot |
| Frontend | React + Tailwind CSS |
| Deploy | Railway |

## 🚀 Despliegue rápido en Railway

### 1. Clonar repositorio
```bash
git clone https://github.com/TU_USUARIO/crm-servicio-tecnico.git
cd crm-servicio-tecnico
```

### 2. Variables de entorno
Copia `.env.example` a `.env` y completa los valores:
```bash
cp .env.example .env
```

### 3. Desplegar en Railway
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login y deploy
railway login
railway init
railway up
```

### 4. Configurar base de datos
```bash
railway run python -m db.init_db
```

## 🔑 Configuración de APIs

### Gmail API
1. Ir a [Google Cloud Console](https://console.cloud.google.com)
2. Crear proyecto → Habilitar Gmail API + Sheets API
3. Crear credenciales OAuth2 → Descargar `credentials.json`
4. Ejecutar `python scripts/auth_google.py` para obtener el token

### Telegram Bot
1. Hablar con [@BotFather](https://t.me/botfather) en Telegram
2. Crear bot → Copiar el token
3. Agregar `TELEGRAM_BOT_TOKEN` al `.env`

### Anthropic (Claude)
1. Ir a [console.anthropic.com](https://console.anthropic.com)
2. Crear API Key
3. Agregar `ANTHROPIC_API_KEY` al `.env`

## 📁 Estructura del proyecto

```
crm-servicio-tecnico/
├── api/                    # FastAPI backend
│   ├── main.py             # Entry point
│   ├── routers/            # Endpoints REST
│   │   ├── clients.py      # CRUD clientes
│   │   ├── emails.py       # Gestión correos
│   │   ├── budgets.py      # Presupuestos
│   │   └── shipments.py    # Datos de envío
│   ├── models/             # Modelos Pydantic
│   └── services/           # Lógica de negocio
├── ai/                     # Motor de IA
│   ├── email_reader.py     # Interpreta emails
│   ├── email_writer.py     # Redacta respuestas
│   ├── data_extractor.py   # Extrae datos de clientes
│   └── budget_analyzer.py  # Analiza presupuestos
├── telegram/               # Bot de Telegram
│   └── bot.py
├── db/                     # Base de datos
│   ├── models.py           # Modelos SQLAlchemy
│   ├── database.py         # Conexión
│   └── init_db.py          # Inicialización
├── workers/                # Tareas periódicas
│   └── gmail_poller.py     # Polling de Gmail
├── dashboard/              # Frontend React
│   └── src/
├── scripts/                # Scripts de utilidad
│   └── auth_google.py
├── .env.example
├── requirements.txt
├── Dockerfile
├── railway.toml
└── docker-compose.yml
```

## 📱 Comandos del Bot Telegram

| Comando | Función |
|---------|---------|
| `/start` | Iniciar bot |
| `/clientes` | Ver últimos clientes |
| `/pendientes` | Emails sin responder |
| `/presupuestos` | Resumen de presupuestos |
| `/buscar [nombre]` | Buscar cliente |
| `/stats` | Estadísticas del día |

## 🗂️ Google Sheets — Estructura recomendada

El sistema espera estas hojas en tu Google Sheets:

- **Servicios** — Lista de servicios y precios
- **FAQs** — Preguntas frecuentes y respuestas
- **Zonas_envio** — Costos y tiempos por zona
- **Garantias** — Políticas de garantía

## 📄 Licencia

MIT
