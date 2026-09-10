# DSS Swing Trading con Business Analytics e IA Multimodal (MVP)

Prototipo (MVP) desplegable en **Vercel (plan free)** del sistema de soporte a la toma de decisiones
para inversiones en la modalidad de **Swing Trading**, descrito en la documentación del Equipo 7.

**Costo total: S/ 0.00** · Metodología: TDSP (Fase de prototipado).

---

## Funcionalidades

- **Indicadores técnicos** en vivo (Yahoo Finance vía `yfinance`): SMA20/SMA50, RSI14,
  MACD (12,26,9) y ATR14.
- **Benchmark econométrico ARIMA**: test ADF, orden `(p,d,q)` por AIC y pronóstico a 5 ruedas.
- **Inferencia multimodal** con **Google Gemini Flash** (contexto técnico + imagen de noticia por URL)
  que devuelve `prediccion` (ALCISTA/NEUTRAL/BAJISTA), `probabilidad`, `nivel_riesgo`,
  `resumen_noticia` y `justificacion_tecnica` en JSON.
- **Motor de señales**: BUY/HOLD/SELL con Stop-Loss (`cierre - 1.5*ATR`) y Take-Profit (`cierre + 3*ATR`).
- **Backtesting** simplificado con partición 70/15/15, fricción del 0.1%, Win Rate,
  Maximum Drawdown, Sharpe y comparación contra Buy & Hold.
- **Dashboard web** (HTML + Vanilla JS + Chart.js) con KPIs, gráficos y panel IA.

## Estructura

```
main.py               # FastAPI (entrypoint para Vercel)
vercel.json           # Cron diario: /api/refresh a las 22:00 UTC
app/
  cache.py            # Caché LRU en memoria (1h) anti rate-limit de Yahoo
  data.py             # Descarga OHLCV (yfinance) + series para gráficos
  indicators.py       # SMA, RSI, MACD, ATR
  arima_benchmark.py  # ADF + ARIMA (con fallback de tendencia)
  gemini_client.py    # Imagen por URL -> base64 -> Gemini (degradación elegante)
  signal_engine.py    # Reglas BUY/HOLD/SELL + SL/TP
  backtest.py         # Simulación 70/15/15 + fricción
public/               # Dashboard (se sirve estático en Vercel)
scripts/smoke.py      # Smoke test del pipeline (validar local/dipositivo)
```

## Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e .        # Windows
# .venv/bin/python -m pip install -e .          # Linux/macOS

.venv\Scripts\python -m uvicorn main:app --port 8000
# Abrir http://localhost:8000  (API docs en http://localhost:8000/docs)
```

Validación rápida del pipeline (red real):

```bash
.venv\Scripts\python scripts\smoke.py
```

## Variables de entorno

| Variable           | Requerida | Descripción                                        |
|--------------------|-----------|----------------------------------------------------|
| `GEMINI_API_KEY`   | No        | Key de Google AI Studio. Sin ella el sistema degrada a análisis técnico. |
| `GEMINI_MODEL`     | No        | Modelo (default: `gemini-2.5-flash`)               |

## Despliegue en Vercel (free)

1. Instala la CLI y vincula el proyecto:
   ```bash
   npm i -g vercel
   vercel
   ```
2. Configura la variable de entorno (obligatorio para la inferencia IA):
   ```bash
   vercel env add GEMINI_API_KEY
   # Luego: vercel env add GEMINI_MODEL (opcional)
   vercel --prod
   ```
   También puede hacerse desde el panel: *Project → Settings → Environment Variables*,
   y *Redeploy*.
3. Verifica:
   - Dashboard: `https://<tu-proyecto>.vercel.app/`
   - API docs: `https://<tu-proyecto>.vercel.app/docs`
   - Smoke test contra producción: `python scripts/smoke.py` (ajustando los hosts si se expande).

> **Nota Hobby (free)**: el cron de `/api/refresh` se ejecuta **1 vez al día** (22:00 UTC,
> tiempo del cierre de NY), sin reintentos. La actualización principal de datos es **bajo demanda**.

## Endpoints

| Método | Ruta                          | Descripción                                        |
|--------|-------------------------------|----------------------------------------------------|
| GET    | `/api/health`                 | Estado y presencia de la key de Gemini             |
| GET    | `/api/indicators?ticker=&period=` | OHLCV + indicadores + series para gráficos       |
| GET    | `/api/forecast?ticker=&period=`  | Pronóstico ARIMA 5 ruedas (ADF, orden, AIC)      |
| POST   | `/api/analyze`                | Body `{ticker, period?, image_url?}` → resultado IA |
| GET    | `/api/signal?ticker=&period=&image_url=` | Señal final + SL/TP + explicación         |
| GET    | `/api/backtest?ticker=`       | Métricas de la simulación histórica                |
| GET    | `/api/refresh?tickers=SPY,AAPL,NVDA,MSFT` | Pre-cálculo/refresco (manual o cron)         |

## Alcance ético

Prototipo académico de investigación. No constituye asesoría de inversión personalizada,
no ejecuta órdenes con dinero real y las señales son simulaciones de apoyo al análisis humano.