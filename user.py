import socket
import sys
import select
import os
import time
import datetime

#global variables
PORT = 58039
CSName = 'localhost'
logged_in = False
login_in_session = False


def argParse(args):
	global PORT
	global CSName
	if len(args) == 5 and args[1]=="-n" and args[3]=="-p":
		try:
			PORT = int(args[4])
			CSName = args[2]
		except ValueError:
			print "Wrong usage of command arguments."
			exit()
	if len(args) == 3:
		if args[1]=="-p":
			try:
				PORT = int(args[2])
			except ValueError:
				print "Wrong usage of command arguments."
				exit()
		elif args[1]=="-n":
			CSName = args[2]


def socketReconnect(sock):
	try:
		sock.connect((CSName, PORT))
	except socket.error, e:
		print "Error in connecting to server: %s" % e
		exit()


# AUT reply handler
def autReplyHandler(reply, loginOp):
	global logged_in
	reply_chunks = reply.split(" ")
	print reply #delete afterwards
	if len(reply_chunks) == 2 and reply_chunks[0]=="AUR":
		print reply_chunks[1] #delete afterwards
		if reply_chunks[1].strip() in ("OK", "NEW"):
			if loginOp:
				logged_in = True
				login_in_session = True
			print "User is logged in."
			return True
		elif reply_chunks[1].strip() == "NOK":
			if loginOp:
				logged_in = False
			print "Password incorrect."
			return False
		else:
			print "Wrong answer from server."
			return False
	else:
		print "Error from server"
		return False

# aut Handler
def autHandler(sock, auth_msg, loginOp):
	try:
		sent_bytes = sock.send(auth_msg)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(auth_msg) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = sock.send(auth_msg[sent_bytes - 1 : ])
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
	else:
		try:
			reply = sock.recv(1024)
		except socket.error, e:
			print "Error in receiving message from server: %s" % e
			exit()
		if reply == 0:
			sock.close()
			print "socket has closed."
		else:
			return autReplyHandler(reply, loginOp)

# dlu reply handler
def dluReplyHandler(CSreply):
	reply_chunks = CSreply.split(" ")
	print CSreply #delete afterwards
	if len(reply_chunks) == 2 and reply_chunks[0]=="DLR":
		if reply_chunks[1].strip() == "OK":
			print "User deleted successfully."
		elif reply_chunks[1].strip()=="NOK":
			print "User deletion unsuccessful."
	else:
		print "Error from server."

# dlu handler
def dluHandler(sock, auth_msg):
	if not login_in_session:
		auth = autHandler(sock, auth_msg, False)
	if not auth:
		print "Operation unsuccessful."
		return
	dlu_msg = "DLU\n"
	try:
		sent_bytes = sock.send(dlu_msg)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(dlu_msg) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = sock.send(dlu_msg[sent_bytes - 1 : ])
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
	try:
		reply = sock.recv(1024)
	except socket.error, e:
		print "Error in receiving message from server: %s" % e
		exit()
	if reply == 0:
		sock.close()
		print "socket has closed"
	else:
		dluReplyHandler(reply)


# Backup reply
def bckReplyHandler(sock, CSreply, auth_msg):
	reply_chunks = CSreply.split(" ")
	if reply_chunks[0] == "BKR":
		if len(reply_chunks) == 2:
			if reply_chunks[1] == "ERR":
				print "Request not formulated correctly."
			elif reply_chunks[1] == "EOF":
				print "Request cannot be answered."
		elif len(reply_chunks) > 4:
			ip_bs = reply_chunks[1]
			port_bs = reply_chunks[2]
			sock.close()
			login_in_session = False
			try:
				bs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				bs_socket.connect((ip_bs, port_bs))
			except socket.error, e:
				print "Error in creating socket: %s" % e
				exit()

			auth = autHandler(bs_socket, auth_msg, False)
			if not auth:
				print "Operation unsuccessful."
				return
			no_files = reply_chunks[3]
			#send UPL

# backup handler
def bckHandler(sock, auth_msg, bck_msg):
	if not login_in_session:
		auth = autHandler(sock, auth_msg, False)
	if not auth:
		print "Operation unsuccessful."
		return
	try:
		sent_bytes = sock.send(bck_msg)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(bck_msg) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = sock.send(bck_msg[sent_bytes - 1 : ])
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
	try:
		reply = sock.recv(1024)
	except socket.error, e:
		print "Error in receiving message from server: %s" % e
		exit()
	if reply == 0:
		sock.close()
		print "socket has closed"
	else:
		bckReplyHandler(sock, reply, auth_msg)

# restore reply Handler
def rstReplyHandler(sock, reply, auth_msg):
	reply_chunks = CSreply.split(" ")
	if reply_chunks[0] == "RSR" and len(reply_chunks) == 3:
		ip_bs = reply_chunks[1]
		port_bs = reply_chunks[2]
		if reply_chunks[1] == "ERR":
			print "Request not formulated correctly."
		elif reply_chunks[1] == "EOF":
			print "Request cannot be answered."
		else:
			sock.close()
			login_in_session = False
			try:
				bs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				bs_socket.connect((ip_bs, port_bs))
			except socket.error, e:
				print "Error in creating socket: %s" % e
				exit()

			auth = autHandler(bs_socket, auth_msg, False)
			if not auth:
				print "Operation unsuccessful"
				return
			#send RSB message

# restore Handler
def rstHandler(sock, auth_msg, dir):
	if not login_in_session:
		auth = autHandler(sock, auth_msg, False)
	if not auth:
		print "Operation unsuccessful"
	rst_msg = "RST " + dir + "\n"
	try:
		sent_bytes = sock.send(rst_msg)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(rst_msg) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = sock.send(rst_msg[sent_bytes - 1 : ])
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
	try:
		reply = sock.recv(1024)
	except socket.error, e:
		print "Error in receiving message from server: %s" % e
		exit()
	if reply == 0:
		sock.close()
		print "socket has closed"
	else:
		rstReplyHandler(sock, reply, auth_msg)

# dirlist reply Handler
def lsdReplyHandler(CSreply):
	reply_chunks = CSreply.split(" ")
	if len(reply_chunks) >= 2 and reply_chunks[0]=="LDR":
		if reply_chunks[1].strip() == "0":
			print "Request for list of directories was unsuccessful."
		else:
			n = int(reply_chunks[1])
			i = 2
			for i in range(2, n):
				print reply_chunks[i]
	else:
		print "Error from server."

# dirlist handler
def lsdHandler(sock, auth_msg):
	if not login_in_session:
		auth = autHandler(sock, auth_msg, False)
	if not auth:
		print "Operation unsuccessful."
		return
	lsd_msg = "LSD\n"
	try:
		sent_bytes = sock.send(lsd_msg)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(lsd_msg) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = sock.send(lsd_msg[sent_bytes - 1 : ])
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
	try:
		reply = sock.recv(1024)
	except socket.error, e:
		print "Error in receiving message from server: %s" % e
		exit()
	if reply == 0:
		sock.close()
		print "socket has closed"
	else:
		lsdReplyHandler(reply)

# filelist reply Handler
def lsfReplyHandler(CSreply, cs_socket):
	reply_chunks = CSreply.split(" ")
	if len(reply_chunks) > 4 and reply_chunks[0]=="LFD":
		ip_bs = reply_chunks[2]
		port_bs = reply_chunks[3]
		no_files = int(reply_chunks[4])
		cs_socket.close()
		login_in_session = False
		try:
			bs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			bs_socket.connect((ip_bs, port_bs))
		except socket.error, e:
			print "Error in creating socket: %s" % e
			exit()

		auth = autHandler(bs_socket, auth_msg, False)
		if not auth:
			print "Operation unsuccessful"
			return
		#send RSB message

	elif len(reply_chunks) == 2 and reply_chunks[0] == "LFD" and reply_chunks[1].strip() == "NOK":
		print "Request for list of files was unsuccessful."
	else:
		print "Error from server."

# dirlist handler
def lsfHandler(sock, auth_msg, dir):
	if not login_in_session:
		auth = autHandler(sock, auth_msg, False)
	if not auth:
		print "Operation unsuccessful."
		return
	lsf_msg = "LSF " + dir + "\n"
	try:
		sent_bytes = sock.send(lsf_msg)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(lsf_msg) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = sock.send(lsf_msg[sent_bytes - 1 : ])
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
	try:
		reply = sock.recv(1024)
	except socket.error, e:
		print "Error in receiving message from server: %s" % e
		exit()
	if reply == 0:
		sock.close()
		print "socket has closed"
	else:
		lsfReplyHandler(reply, sock)

# delete reply Handler
def delReplyHandler(CSreply, cs_socket):
	reply_chunks = CSreply.split(" ")
	if len(reply_chunks) == 2 and reply_chunks[0]=="DDR":
		if reply_chunks[1].strip() == "OK":
			print "User deleted successfully."
		elif reply_chunks[1].strip()=="NOK":
			print "User deletion unsuccessful."
	else:
		print "Error from server."

# delete handler
def delHandler(sock, auth_msg, dir):
	if not login_in_session:
		auth = autHandler(sock, auth_msg, False)
	if not auth:
		print "Operation unsuccessful."
		return
	del_msg = "DEL " + dir + "\n"
	try:
		sent_bytes = sock.send(del_msg)
	except socket.error, e:
		print "Error in sending message to server: %s" % e
		exit()
	remaining = len(del_msg) - sent_bytes
	while remaining != 0:
		try:
			sent_bytes = sock.send(del_msg[sent_bytes - 1 : ])
		except socket.error, e:
			print "Error in sending message to server: %s" % e
			exit()
		remaining = remaining - sent_bytes
	try:
		reply = sock.recv(1024)
	except socket.error, e:
		print "Error in receiving message from server: %s" % e
		exit()
	if reply == 0:
		sock.close()
		print "socket has closed"
	else:
		lsfReplyHandler(reply, sock)

def openSocketCS():
	try:
		cs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		cs_socket.connect((CSName, PORT))
	except socket.error, e:
		print "Error creating socket: %s" % e
		exit()
	login_in_session = False
	return cs_socket



#main function
if len(sys.argv) > 1:
	argParse(sys.argv)

try:
	cs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	cs_socket.connect((CSName, PORT))
except socket.error, e:
	print "Error creating socket: %s" % e
	exit()


while True:
	user_input = raw_input("")
	input_chunks = user_input.strip().split(" ")
	command = input_chunks[0]

	if command == "login":
		if len(input_chunks) == 3:
			username = input_chunks[1]
			password = input_chunks[2]
			auth_msg = "AUT " + username + " " + password + "\n"
			print auth_msg
			#send auth msg to CS
			autHandler(cs_socket, auth_msg, True)
			print logged_in
		else:
			print "Usage of login command: login [username] [password]"
	elif command == "deluser":
		if logged_in:
			dluHandler(cs_socket, auth_msg)
		else:
			print "User needs to be logged in."

	elif command == "backup":
		if len(input_chunks) != 2:
			print "Usage of backup command: backup [dir]"
		elif logged_in:
			if os.path.isdir(input_chunks[1]):
				dir_entries = os.listdir(input_chunks[1])
				bck_msg = "BCK " + input_chunks[1] + " " + str(len(dir_entries))
				for entry in dir_entries:
					file_path = os.path.join(input_chunks[1], entry)
					try:
						time = time.localtime(os.path.getmtime(file_path))
					except os.error, e:
						print "Error in path of file: %s" % e
						exit()
					date_time = datetime.datetime.fromtimestamp(time).strftime("%d.%m.%Y %H:%M:%S")
					bck_msg += " " + entry + " " + time + " " + str(size)
				bckHandler(cs_socket, auth_msg, bck_msg + "\n")
				cs_socket = openSocketCS()
			else:
				print input_chunks[1] + " is not a directory."
		else:
			print "User needs to be logged in."

	elif command == "restore":
		if len(input_chunks) != 2:
			print "Usage of restore command: restore [dir]"
		elif logged_in:
			if os.path.isdir(input_chunks[1]):
				rstHandler(cs_socket, auth_msg, input_chunks[1])
			else:
				print input_chunks[1] + " is not a directory."
		else:
			print "User needs to be logged in."

	elif command == "dirlist":
		if logged_in:
			lsdHandler(cs_socket, auth_msg)
		else:
			print "User needs to be logged in."

	elif command == "filelist":
		if len(input_chunks) != 2:
			print "Usage of restore command: restore [dir]"
		if logged_in:
			if os.path.isdir(input_chunks[1]):
				lsfHandler(cs_socket, auth_msg, input_chunks[1])
			else:
				print input_chunks[1] + " is not a directory."
		else:
			print "User needs to be logged in."

	elif command == "delete":
		if len(input_chunks) != 2:
			print "Usage of restore command: delete [dir]"
		if logged_in:
			if os.path.isdir(input_chunks[1]):
				delHandler(cs_socket, auth_msg, input_chunks[1])
			else:
				print input_chunks[1] + " is not a directory."
		else:
			print "User needs to be logged in."
	elif command == "logout":
		logged_in = False
		print "User is logged out."
	elif command == "exit":
		cs_socket.close()
		exit()
	else:
		print "Invalid command."
