## Redes de Computadores Avançadas - Prof. Tiago Coelho Ferreto

# Simulador de roteamento multicast

### Integrantes do grupo:

- **Jeniffer Aparecida Klein Bittencourt**
- **Mateus de Carvalho de Freitas**

---
---

#### Formato do arquivo de descrição de topologia

#### SUBNET

`<sid>,<netaddr/mask>`

#### ROUTER

`<rid>,<numifs>,<ip1/mask>,<weight1>,<ip2/mask>,<weight2>,<ip3/mask>,<weight3>...`

#### MGROUP

`<mid>,<sid1>,<sid2>,...,<sidn>`

---
#### Formato de saída

#### Cabeçalho das tabelas de roteamento unicast: `#UROUTETABLE`

**Entrada de roteamento unicast:**  
`<rid>, <netaddr/mask>,<nexthop>,<ifnum>`

#### Cabeçalho das tabelas de roteamento multicast: `#MROUTETABLE`

**Entrada de roteamento multicast:**  
`<rid>,<mid>,<nexthop1>,<ifnum1>,<nexthop2>,<ifnum2>,...,<nexthopn>,<ifnumn>`

#### Cabeçalho da transmissão para o grupo multicast: `#TRACE`

**Mensagem mping:**  
`<sid|rid> =>> <sid|rid>, ..., <sid|rid> =>> <sid|rid>: mping <mgroupid>;`

---
---

### Exexução partir de um terminal por linha de comando

`python3 simulador.py topologia.txt s1 g1`

Se estiver usando Linux e quiser executar sem digitar python3:

#### 1. Dar permissão de execução ao arquivo:
No terminal, execute:

`chmod +x simulador.py`

#### 2. Copiar o arquivo para `/usr/local/bin/`:
Copie o arquivo para o diretório `/usr/local/bin/`, que geralmente está no `PATH`, usando o seguinte comando:

`sudo cp simulador.py /usr/local/bin/simulador`

#### 3. Executar o simulador:
Agora, você poderá executar o simulador diretamente como um comando:

`simulador topologia.txt s1 g1`





