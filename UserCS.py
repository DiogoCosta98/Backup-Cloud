import sys
import socket
import os

def AUThandler(user, password):
	AUTstatus = userlistcheck(user, password)
	server_response = "AUR " + AUTstatus + "\n"
	return server_response

def userlistcheck(user, password):
	file_name = user + ".txt"
	userfile = open(file_name, "a+")
	
	line = userfile.readline()
	if line:
		if password == line.strip():
			userfile.close()
			return "OK"
			
		userfile.close()
		return "NOK"
		
	userfile.write(password)
	userfile.close()
	return "NEW"

def DLUhandler(s, tcp_sockets):
	for connection in tcp_sockets:
		if connection['socket'] == s:
			user = connection['user']
			
	DLUstatus = backuplistcheck(user)
	if DLUstatus == "OK":
		deleteuser(user)
	else:
		DLUstatus = "NOK"
		
	server_response = "DLR "+ DLUstatus + "\n"
	return server_response
	
def backuplistcheck(user):
	dir_name = "./" + user
	if os.path.exists(dir_name):
		return "NOK"
	return "OK"

def deleteuser(user):
	file_name = user + ".txt" 
	os.remove(file_name)

def RSThandler(user, dir_name):
	dir_path = user + "/" + dir_name
	if os.path.exists(dir_path):
		file_path = dir_path + "/IP_Port.txt"
		
		getIPport = open(file_path, "r")
		BSinfo = getIPport.readline()
		IP_port = BSinfo.strip().split(":")
		getIPport.close()
		
		try:
			checkBSstatus = open("BS_list.txt", "r")
			BSlist = checkBSstatus.readlines()
			checkBSstatus.close()
			for BS in BSlist:
				IP_port_test = BS.strip().split(":")
				if IP_port_test[0] == IP_port[0] and IP_port_test[1] == IP_port[1]:
					response = "RSR " + IP_port[0] + " " + IP_port[1] + "\n"
					return response
			return "RSR EOF\n"
		except IOError:
			return "RSR EOF\n"
	else:
		return "RSR ERR\n"

def LSDhandler(user):
	if backuplistcheck(user) == "OK":
		return "LDR 0\n", 1
	else:
		dir_name = "./" + user
		dirlist = os.listdir(dir_name)
		N = 0
		dirname = ""
		for directory in dirlist:
			N+=1
			dirname = dirname + directory + " "
		response = "LDR " + str(N) + " " + dirname.strip() + "\n"
		return response
			
def LSFhandler(user, dir_name):
	data = RSThandler(user, dir_name)
	data_split = data.split(" ")
	if data_split[1] == "EOF\n" or data_split[1] == "ERR\n":
		return False, 0, 0
	else:
		return True, data_split[1], int(data_split[2])
		
		
def BCKhandler(user, dir_name):
	response = RSThandler(user, dir_name)
	if response == "RSR ERR\n":
		return False
	return True


def LSUhandler(user):
	BSfile = open("BS_list.txt", "r")
	line = BSfile.readline()
	BSfile.close()
	if line:
		ip_port = line.split(":")
		ip = ip_port[0]
		port = ip_port[1]
	
		file_name = user + ".txt"
		userfile = open(file_name, "a+")
		line = userfile.readline()
		userfile.close()
		password = line.strip()
		return "LSU " + user + " " + password + "\n", ip, int(port)
	else:
		return "ERR",0,0


	
	
	
	
	
