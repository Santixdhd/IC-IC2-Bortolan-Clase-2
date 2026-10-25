# Defensa Conceptual de MQTT y Resolución de la Parte D (D1 a D8 + F2)

---

## 1. ¿Qué es el modelo Pub/Sub y cómo funciona MQTT? (F2)

A diferencia de HTTP —donde un cliente conoce la dirección del servidor, le hace una pregunta directa y se queda esperando la respuesta—, **MQTT** funciona con el modelo **Publicar / Suscribir (Pub/Sub)**:

- **Publisher (Publicador):** Es quien genera el dato (por ejemplo, una Raspberry Pi o un microcontrolador con un sensor de temperatura). Cuando tiene una lectura nueva, simplemente la envía a un canal llamado **topic** y sigue con su trabajo. No sabe quién lo escucha ni cuántos suscriptores hay.
- **Subscriber (Suscriptor):** Es cualquier programa que necesita enterarse cuando llegan datos a un **topic** (por ejemplo, el servicio consumidor que guarda lecturas o un tablero en tiempo real). Se registra ante el broker diciendo *"avisame cada vez que llegue algo a este topic"*.
- **Broker:** Es el intermediario central (como Mosquitto). Recibe todos los mensajes que publican los sensores, mira qué clientes están suscriptos a cada topic y les reenvía el mensaje al instante.

---

## 2. Resolución de los ejercicios de la Parte D

### 🟢 D1 — Ver el mensaje viajar (contra un broker público)
Para probarlo con dos terminales contra el broker público de prueba `test.mosquitto.org`:
- **Terminal 1 (Suscriptor):**
  ```bash
  mosquitto_sub -h test.mosquitto.org -t "unraf/ic2/bortolan/saludo" -v
  ```
- **Terminal 2 (Publicador):**
  ```bash
  mosquitto_pub -h test.mosquitto.org -t "unraf/ic2/bortolan/saludo" -m "Hola desde MQTT"
  ```
El mensaje viaja desde el publicador hacia el broker, y el broker se lo empuja inmediatamente a la Terminal 1.

---

### 🟢 D2 — Publicar sin suscriptores
Si publicamos un mensaje cuando **nadie está suscripto** y recién después abrimos el suscriptor:
- El publicador **no recibe ningún error**: para él la publicación fue exitosa porque el broker la recibió.
- El suscriptor que entra tarde **no ve el mensaje viejo** (salvo que se haya publicado como `retained`). Por defecto, el broker entrega los mensajes únicamente a quienes están escuchando en ese momento y luego los descarta.

---

### 🟡 D3 — Pub/sub (MQTT) vs Request/response (HTTP API)
En **request/response (HTTP)**, el cliente toma la iniciativa: hace un pedido a un servidor específico y espera sincrónicamente una respuesta. En **pub/sub (MQTT)**, los emisores y receptores están desacoplados: uno publica un evento en un topic y el broker lo reparte a todos los interesados que estén escuchando, sean cero, uno o veinte.
- **Cuándo conviene HTTP (request/response):** cuando un usuario o sistema necesita consultar información puntual o ejecutar una validación inmediata (ej. *"dame las últimas 10 lecturas guardadas en la base"* o *"creá este libro y confirmame si los datos son válidos"*).
- **Cuándo conviene MQTT (pub/sub):** cuando dispositivos físicos o sensores emiten lecturas continuas que deben llegar al instante a uno o varios servicios sin acoplarlos entre sí.

---

### 🟡 D4 — Topics, jerarquía y wildcards (`+` vs `#`)
Los topics se organizan como rutas separadas por barras `/` (por ejemplo, `casa/cocina/temp` y `casa/cocina/hum`).
Para suscribirse a varios topics a la vez existen dos **wildcards** (comodines), que solo se usan al **suscribirse** (nunca al publicar):

1. **`+` (comodín de un solo nivel):** reemplaza exactamente una palabra entre barras `/`.
   - Ejemplo: `casa/+/temp` recibe `casa/cocina/temp` y `casa/living/temp`, pero **no** recibe `casa/cocina/heladera/temp`.
2. **`#` (comodín multinivel):** va siempre al final del topic y abarca **todos los niveles restantes** de ahí hacia abajo.
   - Ejemplo: para recibir **todo lo de la cocina** (`casa/cocina/temp`, `casa/cocina/hum`, `casa/cocina/luz/estado`), nos suscribimos a **`casa/cocina/#`** (o `casa/cocina/+` si sabemos que solo hay un nivel debajo).

---

### 🔴 D5 — Diseño de esquema de topics para una casa (3 ambientes × 2 sensores)
Supongamos una casa con **3 ambientes** (`cocina`, `living`, `dormitorio`) y **2 tipos de sensor** en cada uno (`temperatura`, `humedad`).
Diseñamos la jerarquía **`casa/<ambiente>/<tipo_sensor>`**:

- `casa/cocina/temperatura`
- `casa/cocina/humedad`
- `casa/living/temperatura`
- `casa/living/humedad`
- `casa/dormitorio/temperatura`
- `casa/dormitorio/humedad`

**Por qué esta jerarquía cumple los 3 requisitos:**
1. **Suscribirse a TODO lo de la casa:** `casa/#`
2. **Suscribirse a un ambiente específico (ej. solo cocina):** `casa/cocina/#` (o `casa/cocina/+`)
3. **Suscribirse a un tipo de sensor en todos los ambientes (ej. todas las temperaturas):** `casa/+/temperatura`

---

### 🟡 D6 — Niveles de QoS (Quality of Service)
MQTT define 3 niveles de garantía de entrega entre el cliente y el broker:
- **QoS 0 (*At most once* / "como salga"):** se envía una sola vez sin confirmación (`ACK`). Es el más rápido y liviano, pero si hay un microcorte se pierde.
- **QoS 1 (*At least once* / "al menos una vez"):** el emisor reintenta hasta recibir confirmación. Garantiza que el mensaje llega, aunque podría llegar duplicado si se pierde el `ACK`.
- **QoS 2 (*Exactly once* / "exactamente una vez"):** usa un apretón de manos de 4 pasos para asegurar que llegue una única vez, sin pérdida ni duplicación (es el más costoso en tráfico).

**Elección por caso de uso:**
- **Sensor de temperatura que publica cada 2 segundos -> QoS 0:** si se pierde una lectura aislada no importa, porque 2 segundos después llega la siguiente actualizada y ahorramos ancho de banda y batería.
- **Comando crítico `"abrir la puerta"` -> QoS 1 o QoS 2:** es un evento único que no se repite solo; perderlo significa que la puerta no se abre (y si la acción no es idempotente, como destrabar/trabar con el mismo pulso, conviene **QoS 2** para que no se ejecute dos veces).

---

### 🟡 D7 — Mensajes retenidos (`retained`)
Cuando un publicador envía un mensaje con el flag **`retained = True`**, el broker guarda **la última copia de ese mensaje** asociada a ese topic.
- **Diferencia con D2:** si un suscriptor nuevo se conecta media hora más tarde, no tiene que esperar a que el sensor vuelva a publicar; apenas se suscribe, el broker le entrega inmediatamente ese último mensaje retenido.
- **Quién se beneficia:** cualquier panel de monitoreo o servicio recién iniciado que necesite conocer enseguida **"el último estado conocido"** de un sensor (ej. si una alarma está encendida o cuál fue la última medición de un sensor que reporta cada 1 hora).

---

### 🔴 D8 — MQTT (Pub/Sub) vs Preguntar todo el tiempo (Polling HTTP)
Imaginemos **1000 sensores** que solo tienen una novedad importante cada **10 minutos (600 segundos)**, pero queremos enterarnos con a lo sumo **1 segundo** de demora:

- **Con Polling HTTP (preguntar cada 1 segundo):**
  - El servidor recibe **`1000 pedidos por segundo`** (`60.000 pedidos por minuto`, `3.600.000 por hora`).
  - Como cada sensor cambia recién cada 600 segundos, el **`99.83%` de las peticiones HTTP son inútiles** (abren cabeceras HTTP, consultan y responden *"no hay nada nuevo"*).
  - La demora promedio es de `0.5 s` (hasta `1 s`), a costa de saturar la red y el servidor.
- **Con MQTT (Pub/Sub):**
  - Mientras los sensores no tienen datos nuevos, el tráfico de datos es **0 mensajes** (solo un paquete minúsculo de *keep-alive* cada tanto sobre una conexión TCP ya abierta).
  - Cuando un sensor mide un cambio, publica **1 único mensaje** y el broker lo entrega en pocos milisegundos. En 10 minutos viajan solo **1000 mensajes reales** en vez de **600.000 consultas vacías**.
  - Por eso **Pub/Sub escala a miles de dispositivos IoT** con menor latencia y una fracción mínima de consumo de CPU y red.
