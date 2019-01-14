import socket, threading, time
from urllib.request import urlopen
from base64 import b64decode
from urllib.parse import unquote
import traceback

adminList=['127.0.0.1', '88.159.74.145', '87.209.45.31']
portNr=5023
playerList=[]
banList=['66.66.66.66']
boardNames=[]

# settings for recv function:
recvBufferSize=8192 # size of memory block(s) to allocate for reads. 
recvIntervalTimer=0.1 # sleep time between read attempts

recvFirstTimeout=5 # nr of seconds to allow for first data to be read. 
# When nothing after this amount: disconnect.

recvTimeout=2 # after getting some data, wait this amount of seconds for any more possible data.
# When nothing after this amount: disconnect.

# locations textures:
locationFiles="C:\Roelie\DFProject\SharpProject\server\server\static\\"
locationBoardFiles="C:\Roelie\DFProject\SharpProject\server\server\\boards\\"
locationPrivateFiles="C:\Roelie\DFProject\SharpProject\server\server\\private\\"


def getWideIpAdres():
	try:
		html = urlopen("https://whatsmyip.com/")
		lines=html.readlines()
		for l in lines:
			if l.find(b'Your IP') != -1 and l.find(b'is:') != -1:
				lines2=l.split(b'><')
				for l2 in lines2:
					if l2.find(b'p class="h1 boldAndShadow">') !=-1 and l2.find(b'</p') !=-1:
						return (l2[27:-3])
	except:
		traceback.print_exc()
	# perhaps try one or two others
	return b"127.0.0.1"	

def getLanIpAdres():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80)) # some random adres, dont have to be a real adres
    return s.getsockname()[0].encode()

def recv(socket):
    #make socket non blocking
    socket.setblocking(0)
     
    #total data partwise in an array
    total_data=[];
    data='';
     
    #beginning time
    begin=time.time()
    while 1:
        #if you got some data, then break after timeout
        if total_data and time.time()-begin > recvTimeout:
            break
         
        #if you got no data at all, wait a little longer
        elif time.time()-begin > recvFirstTimeout:
            break
         
        #recv something
        try:
            data = socket.recv(recvBufferSize)
            if data:
                total_data.append(data)
                #change the beginning time for measurement
                begin=time.time()
            else:
                #sleep for sometime to indicate a gap
                time.sleep(recvIntervalTimer)
        except:
            pass
     
    #join all parts to make final string
    return b''.join(total_data)

def handleServer():
	while True:
		clientSock, clientAdres = serverSock.accept()
		if clientAdres[0] in banList:
			print ('Banned ip tried to get in: '+clientAdres[0])
			clientSock.close()
		else:
			thread_client = threading.Thread(target = handleUserInput, args=[clientSock, clientAdres])
			thread_client.start()

def sendHtmlFromFile(clientSock,filePath, replaceList=[]):
	try:
		f = open(filePath, "rb")
	except:
		print ('file not found: '+filePath)
		traceback.print_exc()
		try:
			f.close()
		except:
			pass
		clientSock.send(b'HTTP/1.0 404 Not Found\r\n')
		return
	htmlFile=f.read()
	f.close()
	htmlFile=htmlFile.decode()
	for listItem in replaceList:
		htmlFile=htmlFile.replace(listItem[0],listItem[1])
	htmlFile= htmlFile.encode()
	if htmlFile != b'':
		clientSock.send(b'HTTP/1.0 200 OK\r\n')
		clientSock.send(b"Content-Type: text/html\r\n\r\n")
		clientSock.send(htmlFile)
	else:
		clientSock.send(b'HTTP/1.0 404 Not Found\r\n')

def sendFile(clientSock, filePath):
	found=False
	if filePath[-4:].lower()=='.png':
		typeText=b"Content-Type: image/png\r\n\r\n"
		found=True
	elif filePath[-4:].lower()=='.jpg':
		typeText=b"Content-Type: image/jpg\r\n\r\n"
		found=True
	elif filePath[-4:].lower()=='.gif':
		typeText=b"Content-Type: image/gif\r\n\r\n"
		found=True
	elif filePath[-3:].lower()=='.js':
		typeText=b"Content-Type: application/javascript\r\n\r\n"
		found=True
	if found==False:
		print ('unknown file format: '+filePath)
		clientSock.send(b'HTTP/1.0 404 Not Found\r\n')
		return

	try:
		f = open(filePath, "rb")
	except:
		print ('file not found: '+filePath)
		clientSock.send(b'HTTP/1.0 404 Not Found\r\n')
		traceback.print_exc()
		try:
			f.close()
		except:
			pass
		return
	
	clientSock.send(b'HTTP/1.0 200 OK\r\n')
	clientSock.send(typeText)
	clientSock.send(f.read())
	f.close()	

def checkName(strName):
	strName=str(strName)
	if len(strName)==0 or len(strName)>63:
		return False
	allowedChars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_'
	foundIllegalChar=False
	for s in strName:
		if not s in allowedChars:
			foundIllegalChar=True
	if foundIllegalChar:
		return False
	if strName.upper()=='ADMIN':
		return False
	if strName.upper()=='BOARDS':
		return False
	if strName.upper()=='STATIC':
		return False
	return True

def getRecord(strBoardName):
	try:
		with open(locationBoardFiles+strBoardName+'.txt', "r") as f:
			lines=f.readlines()
		lines=lines[0].split(',')
		print (strBoardName)
		print (lines[len(lines)-2].strip())
		return lines[len(lines)-2].strip()
	except Exception as x:
		print(x)
		traceback.print_exc()
		return '0'

def saveRecord(strBoardName, strRecord):
	result=False
	try:
		with open(locationBoardFiles+strBoardName+'.txt', "r") as f:
			lines=f.readlines()
		lines=lines[0].split(',')
		if len(lines[len(lines)-2].strip()):
			oldSplit1=lines[len(lines)-2].split(' left in ')
			newSplit1=strRecord.split(' left in ')
			oldLines=int(oldSplit1[0].strip())
			newLines=int(newSplit1[0].strip())
			if newLines<oldLines:
				lines[len(lines)-2]=strRecord
				result=True		
			elif newLines==oldLines:
				oldSplit2=oldSplit1[1].split(' by: ')
				oldTime=oldSplit2[0].strip()
				newSplit2=newSplit1[1].split(' by: ')
				newTime=newSplit2[0].strip()
		else:
			lines[len(lines)-2]=strRecord
			result=True
		if result:
			with open(locationBoardFiles+strBoardName+'.txt', "w") as f:
				first=True
				for line in lines:
					if first: 
						f.write(line.strip())
						first=False
					else:
						f.write(', '+line.strip())
	except Exception as x:
		print(x)
		traceback.print_exc()		

def handleUserInput(clientSock, clientAdres):
	try:
		userConnectsTo='http://'+wideIp.decode()+':'+str(portNr)+'/'
		if str(clientAdres[0])[0:3]=='127':
			userConnectsTo='http://'+localIp.decode()+':'+str(portNr)+'/'
		elif str(clientAdres[0])[0:3]=='192':
			userConnectsTo='http://'+lanIp.decode()+':'+str(portNr)+'/'
		
		data = recv(clientSock)
		if data:
			dataStr=data.decode()
			if dataStr[:4].upper()=="GET ":
				if dataStr[4:6]=="/ ":
					print (str(clientAdres[0])+' GET / ')
					clientSock.send(b'HTTP/1.0 200 OK\r\n')
					clientSock.send(b"Content-Type: text/html\r\n\r\n")
					clientSock.send(b'<html><body><h1>Hello World</body></html>')
				elif dataStr[4:17]=="/favicon.ico ":
					print (str(clientAdres[0])+' GET /favicon.ico ')
					sendFile(clientSock, locationFiles+'favicon.png')
				elif dataStr[4:15]=="/stone.png ":
					print (str(clientAdres[0])+' GET /stone.png ')
					sendFile(clientSock, locationFiles+'stone.png')
				elif dataStr[4:16]=="/babylon.js ":
					print (str(clientAdres[0])+' GET /babylon.js ')
					sendFile(clientSock, locationFiles+'babylon.js')
				elif dataStr[4:10]=="/test ":
					print (str(clientAdres[0])+' GET /test ')
					sendHtmlFromFile(clientSock,locationFiles+'test.html',[('%%USERCONNECTSTO%%', userConnectsTo)])
				elif dataStr[4:9]=="/peg " or dataStr[4:10]=="/peg/ ":
					print (str(clientAdres[0])+' GET /peg ')
					if len(boardNames)>0:
						strPics='<center><table style="width:100%"><tr valign="middle"><th>name:</th><th>preview:</th><th>record:</th></tr>\n'
						for name in boardNames:
							strPics=strPics+'<tr valign="middle"><td align="center">'+name+'</td><td align="center"><a href="'+userConnectsTo+'peg/'+name+'"><img src="'+userConnectsTo+'boards/'+name+'.png" /></a></td><td align="center">'+getRecord(name)+'</td></tr>\n'
						strPics=strPics+'</table></center>'
						sendHtmlFromFile(clientSock,locationFiles+'peg.html',[('%%PICS%%', strPics)])
					else:
						clientSock.send(b'HTTP/1.0 200 OK\r\n')
						clientSock.send(b"Content-Type: text/html\r\n\r\n")
						clientSock.send(b'<html><body><h1>No boards defined. Goto /peg/admin to create some!</body></html>')
				elif dataStr[4:15]=="/peg/admin ":
					print (str(clientAdres[0])+' GET /peg/admin ')
					if clientAdres[0] in adminList:
						sendHtmlFromFile(clientSock,locationFiles+'pegadmin.html',[('%%USERCONNECTSTO%%', userConnectsTo)])
					else:
						clientSock.send(b'HTTP/1.0 404 Not Found\r\n')
				
				elif dataStr[4:9]=="/peg/":
					a=dataStr[9:].find(' ')
					strName=dataStr[9:9+a]
					if checkName(strName) and strName in boardNames:
						print (str(clientAdres[0])+' GET /peg/'+strName)
						with open(locationBoardFiles+strName+'.txt', "r") as f:
							lines=f.readlines()
						lines=lines[0].split(',')
						lines[0]=lines[0].strip()
						lines[1]=lines[1].strip()
						lines[2]=lines[2].strip()
						lines[len(lines)-2]=lines[len(lines)-2].strip()
						strVARS="""		boardName='"""+lines[0]+"""';
		var boardSize="""+lines[2]+""";
		var boardType='"""+lines[1]+"""';
		var boardRecord='"""+lines[len(lines)-2]+"""';
		var boardArray=["""
						counter=0
						nrOfSpots=(len(lines)-5)/3
						while counter<nrOfSpots:
							x=lines[3+counter*3]
							y=lines[4+counter*3]
							type=lines[5+counter*3]
							strVARS=strVARS+'['+str(x)+','+str(y)+',"'+type.strip()+'", false],'
							counter=counter+1
						strVARS=strVARS+'];'
						sendHtmlFromFile(clientSock,locationFiles+'peggame.html',[('%%USERCONNECTSTO%%', userConnectsTo),('%%VARS%%', strVARS)])
					else:
						clientSock.send(b'HTTP/1.0 404 Not Found\r\n')
				elif dataStr[4:12]=="/boards/":
					a=dataStr[12:].find(' ')
					print (str(clientAdres[0])+' GET /boards/'+dataStr[12:8+a]+'.png')
					sendFile(clientSock, locationBoardFiles+dataStr[12:8+a]+'.png')
				else:
					clientSock.send(b'HTTP/1.0 404 Not Found\r\n')
					print (str(clientAdres[0])+' Unknown request: ')
					print (dataStr)
			elif dataStr[:5].upper()=="POST ":
				response=[400,b'Bad Request']
				
				if dataStr[5:14]=="/savepeg ":
					dataStr=dataStr.split('\r\n\r\n')
					data=dataStr[1].split('&')
					data2=data[0].split('=')
					data3=data[1].split('=')
					boardName=''
					record=''
					if data3[0]=='boardName':
						boardName=data3[1]
					if data2[0]=='boardName':
						boardName=data2[1]
					if data3[0]=='record':
						record=data3[1]
					if data2[0]=='record':
						record=data2[1]
					record=unquote(record)
					record=record.replace('+', ' ')
					if len(record) and len(boardName):
						print ('record: '+record)			 				
						print ('boardName: '+boardName)			 				
						saveRecord(boardName,record)
					response=[303,b'<html><body><script>window.location.href="'+userConnectsTo.encode()+b'peg";</script></body></html>\n\n']	
						
				if clientAdres[0] in adminList:
					if dataStr[5:16]=="/peg/admin ":
						dataStr=dataStr.replace('&png=data%3Aimage%2Fpng%3Bbase64','')
						a=dataStr.find('saveStr')
						saveStr=dataStr[a+8:].split('%2C')
						if (checkName(saveStr[0])):
							try:
								with open(locationBoardFiles+saveStr[0]+'.txt', "w") as f:
									for l in saveStr:
										f.write(l+', ')
										if len(l)==0:
											break
							except:
								response=[500,b'Internal Server Error']
								print ('file error saving: '+locationFiles+saveStr[0]+'.txt')
								print ('disk full? writing rights ok?')
								traceback.print_exc()
							pngData=saveStr[len(saveStr)-1]
							try:
								with open(locationBoardFiles+saveStr[0]+'.png', "wb") as f:
									pngData2=unquote(pngData)
									while len(pngData2)%4>0:
										pngData2=pngData2+'='
									f.write(b64decode(pngData2))
							except:
								response=[500,b'Internal Server Error']
								print ('file error saving: '+locationFiles+saveStr[0]+'.png')
								print ('disk full? writing rights ok?')
								traceback.print_exc()
							found=False
							for name in boardNames:
								if saveStr[0].upper()==name.upper():
									found=True
									break
							if not found:
								boardNames.append(saveStr[0])
								with open(locationPrivateFiles+'boardNames.txt', "w") as f:
									for name in boardNames:
										f.write(name+'\n')
							print (str(clientAdres[0])+' POST /peg/admin ')
							response=[303,b'<html><body><script>window.location.href="'+userConnectsTo.encode()+b'peg";</script></body></html>\n\n']	
						else:
							print (str(clientAdres[0])+' Unknown request: ')
							print (dataStr)
							response=[400,b'Bad Request']
				if response[0]==303: 
					clientSock.send(b'HTTP/1.0 '+str(response[0]).encode()+b' \r\n')
					clientSock.send(b"Content-Type: text/html\r\n\r\n")
					clientSock.send(response[1])
				else:
					clientSock.send(b'HTTP/1.0 '+str(response[0]).encode()+b' '+response[1]+b'\r\n')
					clientSock.send(b"Content-Type: text/html\r\n\r\n")
					clientSock.send(b'<html><body><h1>'+response[1]+b'</body></html>')
		clientSock.close()
	except Exception as x:
		print(x)
		traceback.print_exc()

localIp=b'127.0.0.1'				
wideIp=getWideIpAdres()
lanIp=getLanIpAdres()

if __name__ == "__main__":
	try: 
		f = open(locationFiles+'test.txt', "w")
		f.close()
	except:
		print ('make a folder to hold the static files at: \n'+locationBoardFiles)
		exit(1)
		
	try: 
		f = open(locationPrivateFiles+'test.txt', "w")
		f.close()
	except:
		print ('make a folder to hold the private files at: \n'+locationPrivateFiles)
		exit(1)

	try: 
		f = open(locationBoardFiles+'test.txt', "w")
		f.close()
	except:
		print ('make a folder to hold the board files at:  \n'+locationBoardFiles)
		exit(1)
		
	try:
		print ('Boards:')
		with open(locationPrivateFiles+'boardNames.txt', "r") as f:
			strBoardNames=f.readlines()
		for strBoardName in strBoardNames:
			if checkName(strBoardName.strip()):
				print('ADDED: '+strBoardName.strip())			
				boardNames.append(strBoardName.strip())
			else:
				print('REJECTED: '+strBoardName.strip())			
	except:
		print ('none found. Goto /peg/admin to create some!')
	try:
		serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print('peg server at: ')
		print ('Local IP: '+localIp.decode()+':'+str(portNr)+'/peg')
		print ('WAN   IP: '+lanIp.decode()+':'+str(portNr)+'/peg')
		print ('WIDE  IP: '+wideIp.decode()+':'+str(portNr)+'/peg')
		serverSock.bind(('0.0.0.0', portNr))
		serverSock.listen(10)
	except Exception as x:
		print(x)
		traceback.print_exc()
		exit(1)	

	threadServer = threading.Thread(target = handleServer)
	threadServer.start()
	