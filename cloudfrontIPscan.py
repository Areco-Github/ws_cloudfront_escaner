import ipcalc
import socket, random, re
import threading
import requests, sys, time, os
import json

bg = ''
G = bg + '\033[32m'
O = bg + '\033[33m'
GR = bg + '\033[37m'
R = bg + '\033[31m'

print(O + '''
\tCLOUDFRONT WEBSOCKET ESCANER
\tBy : ARECO-NET
\t  versión más rápida (usando threading)
''' + GR)

# Validar dominio
def dominio_valido(dominio):
    partes = dominio.strip().split(".")
    return len(partes) >= 2 and all(partes)

# Función para pedir el dominio con validación
def pedir_dominio():
    while True:
        dominio_input = input(f"{G}[+] Ingresá el dominio cloudfront que se usará en el Host:\n> {GR}").strip()
        if dominio_input == "0":
            print("🔙 Volviendo al menú...")
            return None
        if not dominio_valido(dominio_input):
            print(f"{R}[!] Dominio inválido. Asegúrate de ingresar un dominio como 'ejemplo.com'.")
            continue
        return dominio_input

# Verificar si el archivo de dominio existe
if os.path.exists("dominio.txt"):
    with open("dominio.txt", "r") as file:
        custom_domain = file.read().strip()
else:
    # Solicitar el dominio si no está guardado
    custom_domain = pedir_dominio()
    if custom_domain:
        with open("dominio.txt", "w") as file:
            file.write(custom_domain)

# Preguntar si se desea editar el dominio
print(f"Dominio guardado: {custom_domain}")
editar_dominio = input(f"¿Deseas editar el dominio? (s/n): {GR}")
if editar_dominio.lower() == "s":
    custom_domain = pedir_dominio()
    if custom_domain:
        with open("dominio.txt", "w") as file:
            file.write(custom_domain)

def update():
    statement = f"[{R}!{GR}] {O}Observa que los rangos de IP se actualizan semanalmente\n {G}¿Deseás actualizar los rangos de IP?{G} "
    for chr in statement:
        sys.stdout.write(chr)
        sys.stdout.flush()
        time.sleep(0.1)
    decision = input(f'[y/n]\n< :{GR}')
    if decision.upper() == 'Y':
        os.system('rm .firstusage.log')
    else:
        return 0
    return decision.upper()

ipdict = {}

def createlog():
    if os.path.exists('.firstusage.log'):
        arg = 'r'
        updating = update()
        if updating == 'Y':
            arg = 'a+'
            status = '[*] actualizando'
    else:
        status = '¡Hola!'
        arg = 'a+'
    with open('.firstusage.log', arg) as f:
        if len(f.read()) < 1:
            input(f'-{G}{status}{GR}\n{R}[!] Conectate a Wi-Fi o datos móviles para actualizar la lista de rangos de IP y presioná Enter{GR}')
            url = 'https://d7uri8nf7uskq.cloudfront.net/tools/list-cloudfront-ips'
            req = requests.get(url).text
            data = json.loads(req)
            ranges = data['CLOUDFRONT_GLOBAL_IP_LIST'] + data['CLOUDFRONT_REGIONAL_EDGE_IP_LIST']
            input(f'{G}[#]Desactiva el Wi-Fi o corta los datos\n y luego presioná Enter para continuar')
            f.write(str(ranges))
        else:
            with open('.firstusage.log', arg) as f:
                ranges = f.read().replace('[', '').replace(']', '').replace('\'', '').split(',')
    return ranges

def save(x, nombre_archivo):
    with open(f'{nombre_archivo}.txt', 'a') as fl:
        fl.write(str(x) + '\n')

def scanner(host, nombre_archivo):
    sock = socket.socket()
    sock.settimeout(2)
    try:
        sock.connect((str(host), 80))
        payload = 'GET / HTTP/1.1\r\nHost: {}\r\n\r\n'.format(host)
        sock.send(payload.encode())
        response = sock.recv(1024).decode('utf-8', 'ignore')
        for data in response.split('\r\n'):
            data = data.split(':')
            if re.match(r'HTTP/\d(\.\d)?', data[0]):
                print('response status : {}{}{}'.format(O, data[0], GR))
            if data[0] == 'Server':
                try:
                    if 'cloudfront' in data[1].lower():
                        print('{}server : {}\nFound working {}..'.format(G, host, GR))
                        save(f'{host} === opened', nombre_archivo)
                        payloadsnd(host)
                except Exception as e:
                    print(e)
    except Exception as e:
        print(e)

def auto_replace(server, ip):
    packet = server.recv(1024).decode('utf-8', 'ignore')
    status = packet.split('\n')[0]
    if re.match(r'HTTP/\d(\.\d)? 101', status):
        print(f'{O}[TCP] response : {G}{status}{GR}')
        save(f'{ip} response ==== {status}')
    else:
        if re.match(r'HTTP/\d(\.\d)? \d\d\d ', status):
            server.send(b'HTTP/1.1 200 Connection established\r\n\r\n')
            print(f'{O}[TCP] response : {R}{status}{GR}')
            return auto_replace(server, ip)

def payloadsnd(ip):
    port = 80
    sc = socket.socket()
    sc.connect((str(ip), port))
    payload = f'GET / HTTP/1.0\r\nHost: {custom_domain}\r\n\r\n'
    sc.send(payload.encode())
    auto_replace(sc, ip)

def Main():
    ipdict = {}
    
    # Solicitar el nombre del archivo para guardar las IPs
    nombre_archivo = input(f"{G}[+] Ingresa el nombre del archivo para guardar las IPs funcionales:\n> {GR}")
    print(f"Guardando las IPs en: {nombre_archivo}.txt")

    ranges = createlog()
    for k, v in enumerate(ranges):
        ipdict[k] = v.strip()
    for choose in range(len(ipdict)):
        iprange = []
        cidr = ipdict[choose]
        print(cidr)
        for ip in ipcalc.Network(cidr):
            iprange.append(ip)
        for index in range(len(iprange)):
            try:
                print("{}[INFO] Escanendo... ({}/{}) [{}]{}".format(
                    R, index + 1, len(iprange), iprange[index], GR))
                sc = threading.Thread(target=scanner, args=(iprange[index], nombre_archivo))
                sc.start()
            except KeyboardInterrupt:
                print('{}Verificación abortada por el usuario{}'.format(R, GR))
                break

if __name__ == "__main__":
    Main()
