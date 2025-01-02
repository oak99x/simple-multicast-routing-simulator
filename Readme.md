# Multicast Routing Simulator  

#### Topology Description File Format  

#### SUBNET  

`<sid>,<netaddr/mask>`  

#### ROUTER  

`<rid>,<numifs>,<ip1/mask>,<weight1>,<ip2/mask>,<weight2>,<ip3/mask>,<weight3>...`  

#### MGROUP  

`<mid>,<sid1>,<sid2>,...,<sidn>`  

---  

#### Output Format  

#### Unicast Routing Table Header: `#UROUTETABLE`  

**Unicast Routing Entry:**  
`<rid>, <netaddr/mask>,<nexthop>,<ifnum>`  

#### Multicast Routing Table Header: `#MROUTETABLE`  

**Multicast Routing Entry:**  
`<rid>,<mid>,<nexthop1>,<ifnum1>,<nexthop2>,<ifnum2>,...,<nexthopn>,<ifnumn>`  

#### Multicast Group Transmission Header: `#TRACE`  

**mping Message:**  
`<sid|rid> =>> <sid|rid>, ..., <sid|rid> =>> <sid|rid>: mping <mgroupid>;`  

---  
---  

### Command-Line Execution  

Run the simulator from a terminal using:  

`python3 simulador.py topologia.txt s1 g1`  

If you are using Linux and want to execute without typing `python3`:  

#### 1. Grant execution permission to the file:  
In the terminal, execute:  

`chmod +x simulador.py`  

#### 2. Copy the file to `/usr/local/bin/`:  
Copy the file to the `/usr/local/bin/` directory, which is usually in the `PATH`, using the following command:  

`sudo cp simulador.py /usr/local/bin/simulador`  

#### 3. Run the simulator:  
Now, you can execute the simulator directly as a command:  

`simulador topologia.txt s1 g1`  






