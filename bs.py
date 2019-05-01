import socket
import sys
import os
from select import select
from datetime import datetime
import datetime
import time


#defaults
HOST = socket.gethostbyname(socket.gethostname())
BSport = 59000
CSname = socket.gethostbyname(socket.gethostname())
CSport = 58039

#global variables
AUTH = False
User = ''
RG = False

#handlers
#User - BS

#AUT
def BSAUThandler(user, password):
        AUTstatus = BSuserlistcheck(user, password)
        if(AUTstatus == "OK"):
            global AUTH
            global User
            AUTH = True
            User = user
            server_response = "AUR " + AUTstatus + "\n"
        return server_response


def BSuserlistcheck(user, password):
    file_name = user + ".txt"
    exists = os.path.isfile(file_name)
    if exists:
        userfile = open(file_name, "a+")
        line = userfile.readline()
        if password == line.strip():
            userfile.close()
            return "OK"

        userfile.close()
        return "NOK"
#

#UPL

def UPLhandler(data):
    inst = data
    clinst_split = inst.split()
    dir = clinst_split[1]
    N = clinst_split[2]
    #find or create path to directory
    if not os.path.isdir(dir):
        os.makedirs(dir)
    #compute string
    string = data.replace("UPL " + dir + " " + N + " ", "")
    for i in range(0,N):
        compute_string = string.split()
        name = compute_string[0]
        f = open(name+".txt", "wb")
        raw_date = datetime.strptime(compute_string[1] + compute_string[2])
        dat = time.mktime(raw_date.timetuple())
        size = compute_string[3]
        string = string.replace(name + " " + dat + " " + size + " " , "")
        string_size = len(string)
        chunked =  [ string[i:i+size] for i in range(0, string_size, size) ]
        f.write(chunked[0])
        f.close()
        os.utime(dir + "/" + name, (dat, dat))
        string = string.replace(chunked[0] + " ", "")




#

#rsb
def RSBhandler(dir):
    global User
    direct_path = os.path.join(User, dir)
    if os.path.isdir(direct_path):
        counter = 0
        substring = ""
        for file in os.listdir(direct_path):
            counter += 1
            file_path = os.path.join(direct_path, file)
            time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d.%m.%Y %H:%M:%S")
            size = os.path.getsize(file_path)
            f = open(file_path, "rb")
            substring += " " +file+ " " + time + " " + str(size) + " " + f.read() 
            f.close()
        string = counter + substring + "\n"
        return "RBR " + string
    return "RBR ERR\n"
#

#BS - CS
def REGhandler(IPBS, portBS):
    return "REG "+ IPBS + " " + str(portBS) + "\n"

def RGRhandler(status):
    if (status == "OK"):
        global RG 
        RG = True
    return 0

def UNRhandler(IPBS, portBS):
    global RG
    if (not RG):
        return ''
    return "UNR " + IPBS + " " + str(portBS) + "\n"

def UARhandler(status):
    if (status == "OK"):
        global RG
        RG = False
    return 0

#lsf
def LSFhandler(user, dir):
    directory_path = os.path.join(user, dir)
    if os.path.isdir(directory_path):
        counter = 0
        substring = ""
        for file in os.listdir(directory_path):
            counter += 1
            file_path = os.path.join(directory_path, file)
            time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d.%m.%Y %H:%M:%S")
            size = os.path.getsize(file_path)
            substring += file+ " " + time + " " + str(size) + " "
        string = counter + " " + substring + "\n"
        return "LFD " + string 
    return "LFD ERR\n"
#

#lsu
def LSUhandler(user, password):
    file_name = user + ".txt"
    exists = os.path.isfile(file_name)
    if exists:
        return "LUR NOK\n"
    userfile = open(file_name, "a+")
    os.makedirs(file_name)
    userfile.write(password)
    userfile.close()
    return "LUR OK\n"
#

#dlb
def DLBhandler(user, dir):
    direct_path = os.path.join(user,dir)
    if os.path.isdir(direct_path):
        for file in os.listdir(direct_path):
            file_path = os.path.join(direct_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(direct_path)
        if os.listdir(user) == []:
            os.rmdir(user)
            os.remove(user+".txt")
            global AUTH
            global User
            AUTH = False
            User = ''
        return "DLR OK\n"
    else:
        return "DLR NOK\n", 0
#

def UserHandler(data):
    inst = data
    clinst_split = inst.split()
    if (clinst_split[0] == "AUT" and len(clinst_split) == 3):
        user = clinst_split[1]
        password = clinst_split[2]
        server_response = BSAUThandler(user, password)
        return server_response

    elif (clinst_split[0] == "UPL" ):
        server_response = UPLhandler(data)
        return server_response

    elif clinst_split[0] == "RSB" :
        if len(clinst_split) == 2:
            global User
            server_response = RSBhandler(User, clinst_split[1])
        else:
            server_response = "RBR ERR\n"
        return server_response
    return "ERR\n"


def CSHandler(data):
    inst = data
    clinst_split = inst.split()
    if (clinst_split[0] == "LSF" and len(clinst_split) == 3):
        server_response = LSFhandler(clinst_split[1], clinst_split[2])
        return server_response

    elif (clinst_split[0] == "LSU" and len(clinst_split) == 3):
        user = clinst_split[1]
        password = clinst_split[2]
        server_response= LSUhandler(user, password)
        return server_response

    elif (clinst_split[0] == "DLB" and len(clinst_split) == 3):
        user = clinst_split[1]
        password = clinst_split[2]
        server_response = DLBhandler(user, password)
        return(server_response)

    elif (clinst_split[0] == "RGR" ):
        RGRhandler(clinst_split[1])
    elif (clinst_split[0] == "UAR" ):
        UARhandler(clinst_split[1])
    else:
        return "ERR\n"

#sending packets
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





#matching inputs
if len(sys.argv) > 1:
    for i in range(0, len(sys.argv)-1):
        if sys.argv[i] == "-b":
            BSport = sys.argv[i+1]
        elif sys.argv[i] == "-n":
            CSname = sys.argv[i+1]
        elif sys.argv[i] == "-p":
            CSport = sys.argv[i+1]


#realwork

#Makes available a TCP server port BSport

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

tcp.bind((HOST, BSport))

tcp.listen(5)

#Makes available a UDP server port BSport

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

udp.bind((HOST, BSport))

register = REGhandler(HOST, BSport)
print register

sendpacketudp(udp,register, (CSname, CSport))

#Listen to UDP and TCP requests in parallel

inputs = [tcp,udp]

try:
    while True:
        print "Entrei em loop\n"
        inputready, outputready, exceptready = select(inputs, [], [])
        for s in inputready:
            if s == tcp:
                newconn, client_addr = tcp.accept()
                inputs.append(newconn)
            elif s == udp:
                data = ""
                package, addr = s.recvfrom(1024)
                data = package
                while ('\n' not in package):
                    package, addr = s.recvfrom(1024)
                    data = data + package
                print str(addr) + " says " + data +"\n"
                server_response = CSHandler(data)
                print server_response
                if server_response:
                    print "sending : " + server_response +"\n"
                    sendpacketudp(s,server_response, addr)
            elif s in inputs:
                try:
                    package = s.recv(1024)
                    inst = package
                except socket.error:
                    inputs.remove(s)
                    s.close()
                if inst:
                    while ('\n' not in package):
                        package = s.recv(1024)
                        inst = inst + package
                    # Instructions Handler
                    if (AUTH == True):
                        print inst
                        server_response = UserHandler(inst)    
                        sendpackettcp(s, server_response)
                    else:
                        print "NOT AUT"
except (KeyboardInterrupt, SystemExit):
    server_response = UNRhandler(HOST, BSport)
    if (server_response):
        udp.sendto(server_response, (CSname,CSport))
        data, addr = udp.recvfrom(1024)
        print data
