# TP0: Docker + Comunicaciones + Concurrencia

## Parte 1: Introducción a Docker

### Ejercicio N.º 1:

#### Solución

Para la solución se utiliza un script the Python y la biblioteca [Jinja](https://jinja.palletsprojects.com/en/stable/).
La plantilla se encuentra en `templates/docker-compose-dev.yaml.jinja`

En este momento se decide utilizar la menor cantidad de variables posible en la plantilla, sabiendo que en los
siguientes ejercicios se pueden ir agregando las nuevas variables a medida que se necesiten.

Se puede utilizar el generador de la siguiente manera:

```
./generar-compose.sh <output_file> <n_clients>
```

#### Tests

![img.png](.assets/ej1-tests.png)

### Ejercicio N.º 2:

#### Solución

Se realizaron los siguientes cambios.

- Se modifica la plantilla utilizada para generar el yaml para el _docker compose_ (
  `templates/docker-compose-dev.yaml.jinja`).
    - Se agregan _docker volumes_ de tipo [Bind Mounts](https://docs.docker.com/engine/storage/bind-mounts/).
    - Se remueve, del environment, la configuración del nivel de logs.
- Se modifica el _client Dockerfile_, eliminando el `COPY` del archivo de configuración.
- Se modifica el Makefile, removiendo el `flag --build` de `docker-compose-up` para no forzar el _rebuild_ de las
  imágenes.

#### Tests

![img.png](.assets/ej2-tests.png)

### Ejercicio N.º 3:

#### Solución

Ya se dispone de un network configurado en el yaml del docker compose. Este network se llama "tp0_testing_net". Se
puede verificar con el comando `docker network ls`.

Para no utilizar Netcat dentro del host, se busca por ejecutar la prueba en un contenedor temporal basado en la imagen
de [busybox](https://hub.docker.com/_/busybox).

La validación del servidor puede realizarse de la siguiente manera.

```bash
docker run --rm --network="tp0_testing_net" busybox sh -c "echo 'custom message' | nc server 12345"
```

Este comando envìa un mensaje al puerto 12345 del servidor.

Para automatizar esta validación, se crea el archivo `validar-echo-server.sh` que ejecuta dicho comando y verifica que
se reciba la respuesta adecuada.

#### Tests

![img.png](.assets/ej3-tests.png)

### Ejercicio N.º 4:

#### Solución

En el servidor, se realizan las siguientes modificaciones.

- Se agregan métodos `__enter__` y `__exit__` en el objeto Server para manejar la creación y destrucción.
- Desde el main se usa el objeto Server en un bloque `with`.
- Se utiliza un handler para la señal SIGTERM que, mediante un flag, interrumpe el bucle principal.
- Se agrega un timeout para que la llamada a `accept()` no sea bloqueante indefinidamente.
    - Cerrar el socket no es suficiente para interrumpir `accept()`.
    - Este timeout debería que ser menor al tiempo de espera de `docker compose stop`.

En el cliente, se realizan las siguientes modificaciones.

- Se agrega el handler para la señal SIGTERM en la función NewClient que construye el objeto Client.
- Se utiliza un flag para detener el bucle principal del cliente.

#### Tests

![img.png](.assets/ej4-tests.png)

## Parte 2: Repaso de Comunicaciones

### Ejercicio N.º 5:

#### Solución

Se implementó la comunicación entre cliente y servidor para registrar apuestas.

El protocolo de comunicación es el siguiente:

1. El cliente envía un mensaje con el siguiente formato. Comienza con un número de 2 bytes que indica el largo del
   mensaje y continúa con los valores de la apuesta separados por un delimitador `|`.
    ```
    <largo mensaje><id agencia>|<nombre>|<apellido>|<documento>|<nacimiento>|<numero>
    ```
2. El servidor parsea el mensaje, registra la apuesta y responde un ACK (un entero) con el número de la apuesta.
    ```
    <numero>
    ```
3. Luego, el cliente recibe el ACK y cierra la conexión.

![img.png](.assets/ej5-protocol.png)

Por el momento, no se cuenta con una política de retries, y cada cliente realiza un único intento de comunicación. Se
entiende que una política de reintentos podría ser implementada en futuras iteraciones.

Como extra, se modifica la plantilla del `docker compose` para que se autogeneren las diferentes apuestas que
transmiten los clientes.

![img.png](.assets/ej5-csv.png)

#### Tests

![img.png](.assets/ej5-tests.png)

### Ejercicio N.º 6:

#### Solución

El protocolo de comunicación sufrió las siguientes modificaciones.

- Al comienzo de un batch de mensajes se envía la cantidad total de bytes del batch.
- Si esa cantidad es cero, significa que no hay más apuestas para enviar.
- El ACK por cada batch corresponde al último número de apuesta del batch.

![img.png](.assets/ej6-protocol.png)

Estimación del Max Batch Size por defecto.

Se cuenta con el siguiente formato de mensaje:

```
<largo mensaje><id agencia>|<nombre>|<apellido>|<documento>|<nacimiento>|<numero>
```

Estimemos un tamaño aproximado para cada campo.

- `largo mensaje`: 2 bytes (valor fijo)
- `id agencia`: 4 bytes (valor fijo)
- `nombre`: 50 bytes
- `apellido`: 50 bytes
- `documento`: 4 bytes (valor fijo)
- `nacimiento`: 10 bytes (valor fijo)
- `numero`: 4 bytes (valor fijo)

Por lo tanto, el tamaño total del mensaje es de 124 bytes, a lo que se suman 5 bytes de los delimitadores `|`. Dando un
total de 129 bytes.

Si se considera un tamaño máximo de 8kB (8192 bytes) para el batch de mensajes, se puede estimar el Max Batch Size como:
`8192 bytes / 129 bytes = 63 mensajes (apuestas)`.

#### Tests

![img.png](.assets/ej6-tests.png)

### Ejercicio N.º 7:

#### Solución

La comunicación del final de carga por parte de los clientes ya fue implementada en el punto anterior. Para este punto,
se modifica levemente el servidor para que entienda si finalizó la carga de todos los clientes que se esperan.

Se modificó ligeramente el protocolo de comunicación para distinguir entre dos tipos de mensajes.

- Si el mensaje comienza con `L`, indica que es un mensaje de carga.
- Si el mensaje comienza con `W`, indica que es un mensaje de control de ganadores.

![img.png](.assets/ej7-protocolo-1.png)

El protocolo para la comunicación de los ganadores (mensaje enviado por el servidor) es el siguiente.

```
<largo mensaje><documento 1>|<documento 2>|<documento 3>
```

![img.png](.assets/ej7-protocolo-2.png)

No se implementa un ACK para el control de ganadores, ya que el cliente se encarga de intentar (con una cantidad de
reintentos definida) hasta obtener la respuesta. El servidor simplemente ignora el mensaje si aún no se pueden conocer
los ganadores.

#### Tests

![img.png](.assets/ej7-tests.png)

## Parte 3: Repaso de Concurrencia

### Ejercicio N.º 8:

#### Solución

Para la implementación del procesado de los mensajes en paralelo, se utiliza la biblioteca estándar de Python:
multiprocessing. Esta nos permite crear procesos y ejecutarlos en paralelo, entre otras cosas. Hacemos uso de las
siguientes herramientas.

- `multiprocessing.Lock`. Se utiliza para sincronizar la lectura y escritura del archivo _bets.csv_.
- `multiprocessing.Manager`. Se utiliza para los diccionarios concurrentes que permiten la sincronización de los
  procesos. Por ejemplo, para saber cuando todos los clientes terminaron de enviar sus apuestas.
- `multiprocessing.Process`. Se utiliza para crear los procesos.

#### Tests

![img.png](.assets/ej8-tests.png)
