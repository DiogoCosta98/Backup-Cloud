import sys
import socket
import os

def BSHandler(data):
	#Backup Server instructions handler
	data_split = data.split(" ")
	#REG Handler
	if(data_split[0] == "REG"):
		if len(data_split) == 3:
			register_BSlist(data_split[1],data_split[2].strip())
			return "RGR OK\n"
		else:
			return "RGR ERR\n"
	#UNR Handler
	if(data_split[0] == "UNR"):
		if len(data_split) == 3:
			if unregister_BSlist(data_split[1],data_split[2]):
				return "UAR OK\n"
			else:
				return "UAR NOK\n"
		else:
			return "UAR ERR\n"		

def register_BSlist(BSip, BSport):
	BSfile = open("BS_list.txt", "a+")
	new_BS = BSip + ":" + BSport + "\n"
	BSfile.write(new_BS)
	
def unregister_BSlist(BSip, BSport):
	inlist = 0
	BSfile = open("BS_list.txt", "a+")
	lines = BSfile.readlines()
	BSfile.close()
	
	BSfile = open("BS_list.txt", "w")
	for line in lines:
		IP_port = (line.strip()).split(":")
		if(IP_port[0] == BSip and IP_port[1] == BSport):
			inlist = 1
		else:
			BSfile.write(line)
			
			
	return inlist
			
def LFDHandler(data, addr):
	words = data.split(" ")
	
	instruction = "LFD " + str(addr[0]) + " " + str(addr[1])
	for x in range(1,len(words)):
		instruction = instruction + " " + words[x]
	instruction = instruction + "\n"
	return instruction

def LURHandler(addr, s, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			user = connection['user']
			string = connection['backupinst']
			
	string_split = string.split(" ")	
	subdir = user +	"/" + string_split[1]
	
	if not(os.path.exists(user)):
		os.mkdir(user)
	os.mkdir(subdir)
	
	file_path = subdir + "/IP_Port.txt"
	writeIPport = open(file_path, "w")
	IPport = addr[0]+ ":" + str(addr[1])
	writeIPport.write(IPport)
	writeIPport.close()
	
	response = "BKR " + addr[0] + " " + str(addr[1])
 	for x in range(2,len(string_split)):
		response = response + " " + string_split[x]
		
	return response + "\n"

def BCKLFDhandler(data, s, addr, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			string = connection['backupinst']
	
	tobackup = []
	inbackup = []
	LFD = data.split(" ")
	for x in range(2, len(LFD), 4):
		inbackup.append({'file': LFD[x], 'date': LFD[x+1], 'time': LFD[x+2], 'size': LFD[x+3].strip()})
	
	BCK = string.split(" ")
	for x in range(3, len(BCK), 4):
		tobackup.append({'file': BCK[x], 'date': BCK[x+1], 'time': BCK[x+2], 'size': BCK[x+3].strip()})
	
	N, inst = check_newfiles(inbackup,tobackup, 0)
	
	server_response = "BKR " + addr[0] + " " + str(addr[1]) + " " + str(N)
	for data in inst:
		server_response = server_response + " " + data['file'] + " " + data['date'] + " " + data['time'] + " " + data['size']
	
	server_response = server_response + "\n"
	return server_response
	
	

def check_newfiles(inbackup, tobackup, N):
	inst = []
	for tobackup_name in tobackup:
		backedup = False
		for backedup_name in inbackup:
			if tobackup_name['file']==backedup_name['file']:
				N, inst = check_updatedfiles(backedup_name, tobackup_name, N, inst)
				backedup = True
				break;
		if not backedup:
			N+=1
			inst.append(tobackup_name)
	return N, inst

def check_updatedfiles(inbackup, tobackup, N, inst):
	if int(inbackup['size']) != int(tobackup['size']):
		inst.append(tobackup)
		N+=1
	elif isnotsamedate(inbackup['date'].split("."),tobackup['date'].split(".")):
		inst.append(tobackup)
		N+=1
	elif isnotsametime(inbackup['time'].split(":"),tobackup['time'].split(":")):
		inst.append(tobackup)
		N+=1
		
	return N, inst
	
def isnotsamedate(inbackup_dmy, tobackup_dmy):
	for x in range(2,-1,-1):
		if int(inbackup_dmy[x]) < int(tobackup_dmy[x]):
			return True
	return False

def isnotsametime(inbackup_hms, tobackup_hms):
	for x in range(0,3):
		if int(inbackup_hms[x]) < int(tobackup_hms[x]):
			return True
	return False
	
def deleteuserdir(s, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			dir_name = connection['backupinst']
			user = connection['user']
			
	dir_path = user + "/" + dir_name
	if os.path.exists(dir_path):
		file_path = dir_path + "/IP_Port.txt"
		os.remove(file_path)
	os.rmdir(dir_path)
	
	if len(os.listdir(user))==0:
		os.rmdir(user)
	
