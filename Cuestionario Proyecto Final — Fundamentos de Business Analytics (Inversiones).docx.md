# **Cuestionario de Evaluación — Proyecto Final de Fundamentos de Business Analytics / BI (Inversiones)**

Fecha de elaboración: Oct 6, 2026 · Entrega de los equipos: \[indicar fecha y hora\]

## **Instrucciones para los equipos**

1. **Cada integrante envía este cuestionario completo.** Las respuestas deben ser **idénticas a las del equipo**. El docente compara los envíos entre integrantes y cualquier diferencia se considera una inconsistencia. Sugerencia: un integrante redacta, el equipo valida y todos copian y envían.  
2. **Todo debe poder verificarse en línea:** tablero publicado en una URL pública, modelo y servicios funcionando en línea y código en un repositorio de GitHub accesible al docente.  
3. Cada afirmación se respalda con **evidencia** (enlace, captura, resultado de métricas o video). Sin evidencia se considera no cumplida.  
4. **Requisitos eliminatorios:** el proyecto debe incluir los **tres reportes** — descriptivo, predictivo y prescriptivo — donde el **predictivo usa un modelo de Machine Learning** entrenado por el equipo y el **prescriptivo usa la API de un modelo de lenguaje (LLM)** para recomendar.  
5. **Nunca escribas claves de API, contraseñas o tokens** en este cuestionario ni en el repositorio. Indica solo el nombre de la variable de entorno.  
6. El proyecto es académico. Ninguna recomendación del sistema constituye asesoría financiera personalizada y nunca debe ejecutar operaciones reales de compra o venta.

## **A. Datos del integrante y del equipo**

| Campo | Respuesta |
| :---- | :---- |
| A1. Código y nombres completos del integrante |  |
| A2. Número de equipo |  |
| A3. Integrantes y rol de cada uno |  |
| A4. Tema de inversión (acciones a largo plazo, opciones, penny stocks, day trading, swing trading, scalping, criptomonedas, ETF, fondos mutuos, metales, otro) |  |
| A5. Nombre del proyecto / producto |  |
| A6. URL pública del tablero en línea |  |
| A7. URL del repositorio de GitHub |  |
| A8. URL del video demostrativo (3 a 5 minutos) |  |

## **B. Problema de negocio y usuario**

* **B1.** ¿Qué decisión de inversión ayuda a tomar el proyecto y quién es el inversionista usuario (perfil, experiencia, capital típico)?  
* **B2.** Perfil de riesgo y horizonte de inversión que atiende (corto, mediano o largo plazo).  
* **B3.** Preguntas de negocio concretas que responderán el reporte descriptivo, el predictivo y el prescriptivo (al menos dos por cada uno).  
* **B4.** Indicadores de éxito del proyecto (por ejemplo: rentabilidad simulada frente a una estrategia de referencia, caída máxima, aciertos del modelo).  
* **B5.** Objetivo general y objetivos específicos (máximo tres).

## **C. Datos, calidad y las 3V**

* **C1.** Completa la tabla de fuentes de datos.

| Fuente (nombre y enlace) | Tipo (estructurado / no estructurado) | Variables o campos | Frecuencia de actualización | Límite o costo de la API | Licencia / permiso de uso |
| :---- | :---- | :---- | :---- | :---- | :---- |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

* **C2.** Demuestra con **cifras** que cumplen las 3V: **Volumen** (cantidad de registros o MB), **Velocidad** (con qué frecuencia llegan o se actualizan los datos) y **Variedad** (tipos y formatos distintos).  
* **C3.** Proceso ETL: ¿cómo extraen, limpian y transforman los datos? Describe el tratamiento de valores faltantes, duplicados, valores atípicos y ajustes por división de acciones (*splits*) o dividendos.  
* **C4.** ¿Dónde se almacenan los datos (base de datos, archivos) y cómo se mantienen actualizados de forma automática?  
* **C5.** Calidad de datos: ¿qué validaciones aplican y qué porcentaje de registros descartaron?  
* **C6.** Si usan datos no estructurados (noticias, redes sociales), ¿cómo los convierten en variables utilizables (por ejemplo, análisis de sentimiento)?

## **D. Metodología y gestión**

* **D1.** Metodología de ciencia de datos (CRISP-DM, CRISP-ML(Q), TDSP u otra) y cómo aplicó el equipo cada fase.  
* **D2.** Cronograma real de implementación (semanas 4 a 14): hitos entregados y pendientes.  
* **D3.** ¿Qué hizo cada integrante? Enlaza sus aportes en el repositorio.

## **E. Reporte DESCRIPTIVO (¿qué pasó?)**

* **E1.** Lista de indicadores (KPI) del reporte, con su fórmula y la pregunta de negocio que responde cada uno (mínimo 6).  
* **E2.** Visualizaciones incluidas (series de tiempo, comparativos, mapas de calor, distribuciones, riesgo) y por qué cada una es adecuada.  
* **E3.** Filtros e interacción disponibles (activo, periodo, perfil de riesgo).  
* **E4.** Herramienta usada (Power BI, Streamlit, Dash u otra) y cómo se **publica en línea** para que el docente lo abra sin instalar nada.  
* **E5.** ¿Cada cuánto se actualiza el reporte y de dónde toma los datos?  
* **E6.** Tres hallazgos de negocio que se descubren con este reporte (describe y adjunta captura).

## **F. Reporte PREDICTIVO (¿qué pasará?) con Machine Learning**

* **F1.** Define la **variable objetivo** con precisión (por ejemplo: "el precio sube más de 2% en 5 días") y el horizonte de predicción.  
* **F2.** Variables predictoras (*features*), cómo se construyen e indicadores técnicos usados (RSI, MACD, volatilidad, otros).  
* **F3.** Modelo(s) de Machine Learning entrenado(s) (Random Forest, XGBoost, LSTM, regresión u otro): justifica la elección y adjunta el notebook o código de entrenamiento.  
* **F4.** Estrategia de validación: partición **temporal** de los datos, *walk-forward* o validación cruzada para series de tiempo. Explica cómo evitan la **fuga de información** (*data leakage*).  
* **F5.** Completa la tabla de métricas sobre datos que el modelo **no vio** durante el entrenamiento.

| Métrica | Modelo del equipo | Línea base (modelo ingenuo o estrategia de comprar y mantener) |
| :---- | :---- | :---- |
| Exactitud (accuracy) |  |  |
| Precisión y sensibilidad (recall) |  |  |
| F1 o AUC-ROC |  |  |
| Error (MAE o RMSE) si es regresión |  |  |
| Retorno simulado (*backtesting*) incluyendo comisiones |  |  |
| Caída máxima (*max drawdown*) |  |  |

* **F6.** ¿El modelo supera a la línea base? Si no, explica por qué y qué aprendieron. No se penaliza un resultado modesto sino ocultarlo.  
* **F7.** ¿Cómo se **sirve** el modelo en línea (API con Flask o FastAPI, archivo guardado, servicio en la nube) y dónde se ve su resultado en el tablero?  
* **F8.** Limitaciones del modelo, cada cuánto se reentrena y cómo detectan que dejó de funcionar bien.

## **G. Reporte PRESCRIPTIVO (¿qué hacer?) con LLM por API**

* **G1.** ¿Qué modelo de lenguaje usan, con qué proveedor y API, y por qué lo eligieron? Indica el nombre de la variable de entorno donde guardan la clave (sin escribirla).  
* **G2.** **Entradas** que recibe el LLM: predicción del modelo de ML, indicadores del reporte descriptivo, perfil de riesgo y contexto de mercado. Adjunta un ejemplo real de entrada.  
* **G3.** Adjunta el **prompt de sistema** completo y explica cómo lo diseñaron y probaron.  
* **G4.** **Salida estructurada:** ¿qué campos devuelve el LLM (acción sugerida, justificación, riesgos, nivel de confianza, alternativas)? ¿Cómo validan el formato?  
* **G5.** ¿Qué parte de la recomendación la deciden **reglas fijas** (por ejemplo, pérdida máxima aceptada, tamaño de la posición) y qué parte el LLM? Explica por qué.  
* **G6.** ¿Cómo comprueban que la recomendación es coherente con la predicción y con los datos (y que el LLM no inventa cifras)? Describe las validaciones.  
* **G7.** Muestra **tres casos reales**: entrada, recomendación del LLM y análisis crítico de si era razonable.  
* **G8.** Medidas de protección: aviso de que no es asesoría financiera, límite de tokens y de llamadas por día, tratamiento de errores de la API y registro (log) de cada recomendación emitida.  
* **G9.** Costo estimado por 100 recomendaciones.

## **H. Integración de punta a punta y despliegue en línea**

* **H1.** Adjunta el **diagrama de arquitectura** (datos → ETL → modelo de ML → LLM → tablero) con cada componente identificado.  
* **H2.** Explica el flujo completo cuando el usuario abre el tablero: ¿qué se ejecuta, en qué orden y qué pasa si falla un componente?  
* **H3.** Servidor o servicio donde está desplegado cada componente (datos, API del modelo, LLM, tablero) y cómo se actualiza (por ejemplo, GitHub Actions).  
* **H4.** Tipo de proyecto según las plantillas del curso: ☐ Web estática ☐ Aplicación web con IA ☐ Proceso en segundo plano ☐ Otro (indicar cuál).  
* **H5.** ¿El repositorio incluye Dockerfile, archivo .env.example y un README con los pasos para reproducir el proyecto?  
* **H6.** Lista de variables de entorno necesarias (solo nombres, sin valores).  
* **H7.** Acceso para el docente: enlace público o usuario de prueba, sin contraseñas reales de los integrantes.  
* **H8.** Tiempo de carga del tablero y de la recomendación medido en línea.

## **I. Riesgos, ética y cumplimiento**

* **I1.** ¿Qué límites de uso tienen las APIs de datos y del LLM (plan gratuito) y cómo afectan al proyecto?  
* **I2.** ¿Qué riesgos tiene el sistema (resultados pasados no garantizan resultados futuros, sesgos del modelo, dependencia del LLM) y cómo los comunican al usuario?  
* **I3.** ¿Qué hicieron para que el sistema no induzca a decisiones imprudentes (apalancamiento, penny stocks, cripto)?

## **J. Pruebas y evidencias**

* **J1.** Matriz de pruebas con mínimo 6 casos que cubran los tres reportes.  
* **J2.** Capturas del tablero funcionando en la URL pública con el reporte descriptivo, el predictivo y el prescriptivo.  
* **J3.** Un error o falla que encontraron y cómo lo corrigieron.  
* **J4.** Enlace a los notebooks o código que permitan reproducir los resultados.

## **K. Declaración final**

* **K1.** ☐ Declaro que mis respuestas coinciden con las de mi equipo y que el proyecto está **en línea y funcionando** en la URL indicada.  
* **K2.** ☐ Declaro que no incluí claves, contraseñas ni datos personales reales en el repositorio.  
* **K3.** ☐ Declaro que el modelo de ML fue entrenado por nuestro equipo y que el reporte prescriptivo llama realmente a la API de un LLM.  
* **K4.** ☐ Puedo explicar en una sustentación oral el funcionamiento de los tres reportes.

