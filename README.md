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

...
