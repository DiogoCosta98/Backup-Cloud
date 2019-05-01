import sys
import socket
import os
from UserCS import *
from BSCS import *
from select import select
    
def ParseArgs(args):
	if args[1] == "-p" and len(sys.argv)==3 and str.isdigit(args[2]):
		return int(args[2])
	else:
		sys.exit("Wrong arguments usage.")	

def change_user(s, user, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			connection['user'] = user
	
def change_udp(s, ip, port, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			connection['udp_ip'] = ip
			connection['udp_port'] = port

def change_backup(s, boolean, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			connection['backup'] = boolean
			
def change_backupinst(s, inst, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			connection['backupinst'] = inst
			
def find_user(s, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			return connection['user']

def find_socket(tcp_sockets, addr):
	for connection in tcp_sockets:
		if connection['udp_ip'] == addr[0] and connection['udp_port'] == addr[1]:
			return connection['socket']
			
def find_backup(tcp_sockets, addr):
	for connection in tcp_sockets:
		if connection['udp_ip'] == addr[0] and connection['udp_port'] == addr[1]:
			return connection['backup']
			
def issocketunblock(s, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s and connection['user'] == 'none':
			return False
		elif connection['socket'] == s and connection['user'] != 'none':
			return True

def sendpackettcp(s, server_response):
	try:
		sent_bytes = s.send(server_response)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(server_response) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = s.send(server_response[sent_bytes - 1 : ])
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
		
def sendpacketudp(s, server_response, addr):
	try:
		sent_bytes = s.sendto(server_response,addr)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(server_response) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = s.sendto(server_response[sent_bytes - 1 : ], addr)
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
		
		
HOST = ''
PORT = 58039

tcp_sockets = []
#Parse Optional Argument [-p CSport]
if len(sys.argv)>1:
	PORT = ParseArgs(sys.argv)
	lines = user_list.readlines()
	
# create tcp socket
tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.bind((HOST,PORT))
tcp.listen(5)

# create udp socket
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind((HOST,PORT))

inputs = [tcp,udp]

#Listen to UDP and TCP requests in parallel
while True:
	inputready,outputready,exceptready = select(inputs,[],[])
	for s in inputready:
		if s == tcp:
			newconn, client_addr = tcp.accept()  
			inputs.append(newconn)
			tcp_sockets.append({'socket': newconn, 'user': 'none', 'udp_port': 'none', 'udp_ip': 'none', 'backup': False, 'backupinst': 'none'})
		elif s == udp:
			data = ""
			package, addr = s.recvfrom(1024)
			data = package
			while('\n' not in package):
				package, addr = s.recvfrom(1024)
				data = data + package
				
			#Handle "LFD" insctruction from BS
			if data.split(" ")[0] == "LFD":
				#"LFD" from BS as a result of "LSF" from the user
				if not(find_backup(tcp_sockets,addr)):
					server_response = LFDHandler(data, addr)
					s = find_socket(tcp_sockets, addr)
					sendpackettcp(s, server_response)
				#"LFD" from BS as a result of "BCK" from the user
				else:
					s = find_socket(tcp_sockets, addr)
					server_response = BCKLFDhandler(data, s, addr, tcp_sockets)
					sendpackettcp(s, server_response)
				change_backup(s, False, tcp_sockets)
				change_backupinst(s, 'none', tcp_sockets)
				change_user(s, 'none', tcp_sockets)
				change_udp(s, 'none', 'none', tcp_sockets)
				
			#Handle "LUR" instruction from BS
			elif data.split(" ")[0] == "LUR":
				if data.split(" ")[1] == "OK\n":
					s = find_socket(tcp_sockets, addr)
					server_response = LURHandler(addr, s, tcp_sockets)
					sendpackettcp(s, server_response)
				else:
					s = find_socket(tcp_sockets, addr)
					sendpackettcp(s, "BKR EOF\n")
				change_backup(s, False, tcp_sockets)
				change_backupinst(s, 'none', tcp_sockets)
				change_user(s, 'none', tcp_sockets)
				change_udp(s, 'none', 'none', tcp_sockets)
			
			#Handle "DBR" instruction from BS
			elif data.split(" ")[0] == "DBR":
				s = find_socket(tcp_sockets, addr)
				if data.split(" ")[1] == "OK\n":
					deleteuserdir(s, tcp_sockets)
					sendpackettcp(s, "DDR OK\n")
				elif data.split(" ")[1] == "NOK\n":
					sendpackettcp(s, "DDR NOK\n")
				change_backupinst(s, 'none', tcp_sockets)
				change_user(s, 'none', tcp_sockets)
				change_udp(s, 'none', 'none', tcp_sockets)
			#Handle all other instructions from BS
			else:
				server_response = BSHandler(data)
				if server_response:
					sendpacketudp(s, server_response, addr)
		elif s in inputs:
			inst = ""
			try:
				package = s.recv(1024)
				inst = package
			except socket.error:
				inputs.remove(s)
				s.close()
				tcp_sockets = [x for x in tcp_sockets if x['socket'] in inputs]
			if inst:
				while('\n' not in package):
					package = s.recv(1024)
					inst = inst + package
					
				#Instructions Handler
				clinst_split = inst.split(" ")
				#Handle "AUT user pass" instruction
				if(clinst_split[0] == "AUT" and len(clinst_split)==3):
					server_response = AUThandler(clinst_split[1], clinst_split[2].strip())
					if(server_response.split(" ")[1] == "OK\n"):
						change_user(s, clinst_split[1], tcp_sockets)
					sendpackettcp(s, server_response)
	
				#Handle "DLU" instruction
				elif(clinst_split[0] == "DLU\n" and len(clinst_split)==1 and issocketunblock(s,tcp_sockets)):
					server_response = DLUhandler(s, tcp_sockets)
					change_user(s, 'none', tcp_sockets)
					sendpackettcp(s, server_response)
				
				#Handle "RST" instruction
				elif(clinst_split[0] == "RST" and len(clinst_split)==2 and issocketunblock(s,tcp_sockets)):
					if len(clinst_split) == 2:
						server_response = RSThandler(find_user(s,tcp_sockets), clinst_split[1])
					else:
						server_response = "RST ERR\n"
					change_user(s, 'none', tcp_sockets)
					sendpackettcp(s, server_response)
				
				#Handle "LSD" instruction
				elif(clinst_split[0] == "LSD\n" and len(clinst_split) == 1 and issocketunblock(s,tcp_sockets)):
					server_response = LSDhandler(find_user(s,tcp_sockets))
					change_user(s, 'none', tcp_sockets)
					sendpackettcp(s, server_response)
					
				#Handle "LSF" instruction
				elif(clinst_split[0] == "LSF" and len(clinst_split) == 2 and issocketunblock(s,tcp_sockets)):
					LSFrequest, ip, port = LSFhandler(find_user(s,tcp_sockets), clinst_split[1].strip())
					if LSFrequest:
						server_response = "LSF " + find_user(s,tcp_sockets) + " " + clinst_split[1].strip() + "\n"
						change_udp(s, ip, port, tcp_sockets)
						sendpacketudp(udp, server_response, (ip,port))
					else:
						sendpackettcp(s, "LFD NOK\n")
						change_user(s, 'none', tcp_sockets)
						
				#Handle "BCK" instruction
				elif(clinst_split[0] == "BCK" and issocketunblock(s,tcp_sockets)):
					if(BCKhandler(find_user(s,tcp_sockets), clinst_split[1])):
						LSFrequest, ip, port = LSFhandler(find_user(s,tcp_sockets), clinst_split[1])
						if LSFrequest:
							server_response = "LSF " + find_user(s,tcp_sockets) + " " + clinst_split[1] + "\n"
							change_udp(s, ip, port, tcp_sockets)
							change_backup(s, True, tcp_sockets)
							change_backupinst(s, inst, tcp_sockets)
							sendpacketudp(udp, server_response, (ip,port))
						else:
							sendpackettcp(s, "BKR ERR\n")
							change_user(s, 'none', tcp_sockets)
					else:
						server_response, ip, port = LSUhandler(find_user(s,tcp_sockets))
						if server_response.split(" ")[0] == "LSU":
							change_udp(s, ip, port, tcp_sockets)
							change_backup(s, True, tcp_sockets)
							change_backupinst(s, inst, tcp_sockets)
							sendpacketudp(udp, server_response, (ip,port))
						else:
							sendpackettcp(s, "BKR EOF\n")
							change_user(s, 'none', tcp_sockets)
							
				#Handle "DEL" instruction
				elif(clinst_split[0] == "DEL" and len(clinst_split) == 2 and issocketunblock(s,tcp_sockets)):
					LSFrequest, ip, port = LSFhandler(find_user(s,tcp_sockets), clinst_split[1].strip())
					if LSFrequest:
						server_response = "DLB " + find_user(s,tcp_sockets) + " " + clinst_split[1].strip() + "\n"
						change_udp(s, ip, port, tcp_sockets)
						change_backupinst(s, clinst_split[1].strip(), tcp_sockets)
						sendpacketudp(udp, server_response, (ip,port))
					else:
						sendpackettcp(s, "DEL NOK\n")
						change_user(s, 'none', tcp_sockets)
				#Handle wrong instructions
				else:
					change_user(s, 'none', tcp_sockets)
					sendpackettcp(s, "ERR\n")
					


