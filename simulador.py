import sys
import heapq
from ipaddress import ip_network, ip_interface

subnets = {}
routers = {}
multicast_groups = {}

unicast_table = []
mcast_table = []
trace = []

# Função auxiliar para extrair os 3 primeiros octetos de um IP
def extract_prefix(ip):
    return '.'.join(ip.split('.')[:3])

class Router:
    def __init__(self, rid):
        self.rid = rid
        self.interfaces = []
        self.neighbors = {}

    def add_interface(self, ip_mask, weight):
            iface_num = len(self.interfaces)  # O número da interface será o índice da lista
            self.interfaces.append((iface_num, ip_mask, weight))
    
    def belongs_to_router(self, ip_mask):
        return any(ip_interface(iface[1]).ip.exploded == ip_interface(ip_mask).ip.exploded for iface in self.interfaces)
    
    def add_neighbor(self, neighbor, ip_mask, iface_num, weight):
        self.neighbors[neighbor] = (ip_mask, iface_num, weight)

    def __lt__(self, other):
        return self.rid < other.rid

def parse_topology(filename):
    with open(filename, 'r') as file:
        current_section = None
        for line in file:
            line = line.strip()
            if line.startswith("#"):
                current_section = line
                continue

            # Leitura das subnets
            if current_section == "#SUBNET":
                sid, netaddr = line.split(',')
                subnets[sid] = ip_network(netaddr)  # Armazena como rede

            # Leitura dos roteadores
            elif current_section == "#ROUTER":
                parts = line.split(',')
                rid = parts[0]  # ID do roteador, ex: r1
                router = Router(rid)

                # Processa as interfaces do roteador
                for i in range(2, len(parts), 2):
                    ip_mask = parts[i]  # Ex: 10.0.0.1/8
                    weight = int(parts[i+1])  # Ex: 1
                    
                    # Verificar o prefixo da subrede e adicionar uma nova subrede se não existir
                    # ip = ip_interface(ip_mask).ip.exploded
                    subnet_prefix = extract_prefix(ip_interface(ip_mask).ip.exploded) # '.'.join(ip.split('.')[:3])
                    if not any(subnet_prefix in str(subnet) for subnet in subnets.values()):
                        subnet_id = f"s{len(subnets) + 1}"
                        subnets[subnet_id] = ip_network(ip_mask, strict=False)
                        
                    router.add_interface(ip_mask, weight)

                routers[rid] = router  # Adiciona o objeto Router à lista de roteadores

            # Leitura dos grupos multicast
            elif current_section == "#MGROUP":
                parts = line.split(',')
                mid = parts[0]  # ID do grupo multicast, ex: g1
                multicast_groups[mid] = parts[1:]  # Lista de subnets associadas ao grupo
    
    # Link neighbors based on shared subnets
    for r1 in routers.values():
        for r2 in routers.values():
            if r1 != r2:
                for iface_num1, ip_mask1, weight1 in r1.interfaces:
                    for iface_num2, ip_mask2, weight2 in r2.interfaces:
                        # Extrai os 3 primeiros octetos de cada IP
                        ip1_prefix = extract_prefix(ip_interface(ip_mask1).ip.exploded)
                        ip2_prefix = extract_prefix(ip_interface(ip_mask2).ip.exploded)
                        
                        # Compara os 3 primeiros octetos
                        if ip1_prefix == ip2_prefix:
                            r1.add_neighbor(r2.rid, ip_mask2, iface_num1, weight1)
                            r2.add_neighbor(r1.rid, ip_mask1, iface_num2, weight2)

# Função para verifica se o roteador tem uma conexão direta com a sub-rede
def is_direta(router, subnet):
    subnet_prefix = extract_prefix(ip_interface(subnet).ip.exploded)
    # Itera sobre as interfaces para comparar o prefixo da sub-rede e capturar o iface_num
    for iface_num, ip_mask, weight in router.interfaces:
        if subnet_prefix == extract_prefix(ip_interface(ip_mask).ip.exploded):
            return iface_num
        
    return False
    
def dijkstra(start_rid, subnet):
    distances = {rid: float('inf') for rid in routers}
    distances[start_rid] = 0
    previous_nodes = {}
    
    # Lista para armazenar caminhos com conexões diretas
    direct_connections = []
    
    priority_queue = [(0, start_rid)]
    while priority_queue:
        current_distance, current_rid = heapq.heappop(priority_queue)

        if current_distance > distances[current_rid]:
            continue
        
        # Verifica se o roteador atual tem uma conexão direta com a sub-rede
        is_direta_result = is_direta(routers[current_rid], subnet)
        if is_direta_result is not False:
            direct_connections.append((current_distance, current_rid))

        for neighbor, (ip_mask_destino, iface_num_origem, weight) in routers[current_rid].neighbors.items():
            distance = current_distance + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = (current_rid, ip_mask_destino, iface_num_origem, distance)
                heapq.heappush(priority_queue, (distance, neighbor))
    
    # Reconstrói o caminho de menor custo
    path = None
    
    if direct_connections:
        best_connection = min(direct_connections, key=lambda x: x[0])
        _, best_rid = best_connection
        
        while best_rid != start_rid:
            path = previous_nodes.get(best_rid)
            best_rid = path[0]

    return path

def build_unicast_table(routers, subnets):
    for rid, router in routers.items():
        for _, subnet in subnets.items():
            # verifica interfaces diretamente conectadas
            iface_num = is_direta(router, subnet)
            if iface_num is not False:
                unicast_table.append((rid, subnet, '0.0.0.0', iface_num, 0))
                continue
            
            _, iface_destino, iface_num_origem, distance = dijkstra(rid, subnet)
            
            unicast_table.append((rid, subnet, ip_interface(iface_destino).ip.exploded, iface_num_origem, distance))

# Função para gerar a tabela multicast com base na tabela unicast
def build_multicast_table(unicast_table, multicast_group, start_rid):
    visited_routers = set()
    visited_subnets = set()
    
    # Encontrar as subredes associadas ao grupo multicast
    interested_subnets = multicast_groups[multicast_group]
    
    priority_queue = [(start_rid, 0)]
    heapq.heapify(priority_queue)
    
    while priority_queue:
        current_rid, cost = heapq.heappop(priority_queue)
        
        if current_rid in visited_routers:
            continue  # Se o roteador já foi visitado, pular
        
        visited_routers.add(current_rid)
        
        nexthops = []
        
        # Itera sobre as sub-redes de interesse
        for subnet_id in interested_subnets:
            if subnet_id in visited_subnets:
                continue  # Pular sub-rede já processada
            
            subnet = subnets[subnet_id]
            # Procura entradas na tabela unicast para o roteador atual
            for entry in unicast_table:
                if entry[0] == current_rid and entry[1] == subnet:
                    #verificar se tem alguem que acesa r3 com suto
                    
                    if entry[2] == '0.0.0.0':
                        nexthops.append((entry[2], entry[3], (subnet_id, 0)))
                        visited_subnets.add(subnet_id)
                    else:
                        # Verificar se já existe uma rota com custo menor para a subnet_id em mcast_table
                        exist = False
                        for e in mcast_table:
                            if any(nh[0] == subnet_id and nh[1] <= (cost + entry[4]) for _, _, nh in e[2]):
                                exist = True
                                break
                        
                        if not exist:
                            nexthops.append((entry[2], entry[3], (subnet_id, cost + entry[4])))
                            
                        next_router = next((rid for rid, router in routers.items() if router.belongs_to_router(entry[2])), None)
                        heapq.heappush(priority_queue, (next_router, cost + entry[4]))
        
        if nexthops:
            mcast_table.append((current_rid, multicast_group, nexthops))

# Função para simular o envio da mensagem mping usando a tabela multicast
def simulate_mping(start_subnet, start_rid, multicast_group, mcast_table):
    visited_routers = set()  # Para evitar loops e reenvios desnecessários
    visited_subnets = set()  # Para controlar as sub-redes já atingidas

    # Define as sub-redes interessadas
    interested_subnets = multicast_groups[multicast_group]

    trace.append(([(start_subnet, start_rid)], f"mping {multicast_group}"))
    
    current_rid = start_rid
    visited_routers.add(current_rid)
    
    for sid in interested_subnets:
        nexthops = []
        
        
        for entry in mcast_table:
            if entry[0] == current_rid and entry[1] == multicast_group:
                for iface, _, _ in entry[2]:
                    if iface == '0.0.0.0':
                        nexthops.append((current_rid, sid))
                        visited_subnets.add(sid)
                        visited_routers.add(current_rid)
                    else:
                        router_id = next((rid for rid, router in routers.items() if router.belongs_to_router(iface)), None)
                        nexthops.append((current_rid, router_id))
        
                current_rid = entry[0]
                trace.append((nexthops, f"mping {multicast_group}"))

def simulate_routing(filename, start_subnet, multicast_group):
    parse_topology(filename)

    # Extrai o prefixo da sub-rede inicial (os primeiros 3 octetos do IP)
    start_subnet_prefix = extract_prefix(ip_interface(subnets[start_subnet].network_address).exploded)

    # Determina o roteador inicial com base na sub-rede
    start_router = None
    for rid, router in routers.items():
        # Verifica se o roteador tem alguma interface na sub-rede inicial
        if any(start_subnet_prefix == extract_prefix(ip_interface(ip_mask).ip.exploded) for _, ip_mask, _ in router.interfaces):
            start_router = rid
            break

    if not start_router:
        print(f"Erro: não foi encontrado um roteador com a subrede {start_subnet}")
        return

    # Gerando tabelas
    build_unicast_table(routers, subnets)
    
    # Gerar tabela muticats
    build_multicast_table(unicast_table, multicast_group, start_router)
    
    # Simular mensagem ping
    simulate_mping(start_subnet, start_router, multicast_group, mcast_table)
    
    # Print the unicast routing table for each router
    print("#UROUTETABLE")
    for entry in unicast_table:
        print(f"{entry[0]},{entry[1]},{entry[2]},{entry[3]}")
        
    # Exibe tabela de roteamento multicast
    print("#MROUTETABLE")
    for entry in mcast_table:
        nexthops_str = ','.join(f"{hop[0]},{hop[1]}" for hop in entry[2])
        print(f"{entry[0]},{entry[1]},{nexthops_str}")
    
    # Exibe o trace de mensagens mping
    print("#TRACE")
    for hops, message in trace:
        hop_str = ', '.join(f"{src} => {dst}" for src, dst in hops)
        print(f"{hop_str} : {message};")




if __name__ == "__main__":
    # if len(sys.argv) != 4:
    #     print("Uso: simulador <arquivo_topologia> <subnet_inicial> <multicast_group>")
    #     sys.exit(1)

    # topology_file = sys.argv[1]
    # start_subnet = sys.argv[2]
    # multicast_group = sys.argv[3]
    topology_file = "topologia.txt"
    start_subnet = "s1"
    multicast_group = "g1"

    simulate_routing(topology_file, start_subnet, multicast_group)


# <rid>,  <mid>,  <nexthop1>,<ifnum1>,
#  r1,     g1,    0.0.0.0,1