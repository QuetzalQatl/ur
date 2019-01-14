from flask import Flask, render_template, request, send_file,abort, redirect
from flask_socketio import SocketIO, join_room, leave_room, emit, send
from urllib.request import urlopen
from base64 import b64decode, decodebytes
from urllib.parse import unquote

#from codenames import game
import time
import random
import traceback
import socket
import sys
import os
import json

#this program needs:
#pip install flask flask-socketio eventlet

PORT=5003 # default, can be set at startup by setting the environment variable 'PORT'
LANIP='192.168.99.100' # default, can be set at startup by setting the environment variable 'LANIP'
locationStaticFiles="/static/"
#characters allowed in names:
allowed='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_'
maxnamelen=32

localIP='127.0.0.1'
WANIP=''

# initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(512)
socketio = SocketIO(app)

adminList=['127.0.0.1', '88.159.74.145', '87.209.45.31']

firstColor='W' # B lack or W hite

banList=['66.66.66.66']
playerList=[]
board=['DetermineStart','2222','WWWWWWW','0000000','000000000000000000000000','BBBBBBB','0000000','2222']

def getWideIpAdres():
    try:
        html = urlopen("https://whatsmyip.com/")
        lines=html.readlines()
        html = ''
        for l in lines:
            if l.find(b'Your IP') != -1 and l.find(b'is:') != -1:
                lines2=l.split(b'><')
                for l2 in lines2:
                    if l2.find(b'p class="h1 boldAndShadow">') !=-1 and l2.find(b'</p') !=-1:
                        return l2[27:-3].decode('ascii')
    except:
        traceback.print_exc()
        # perhaps try one or two others
    print ('OMG!!!! Could not find wide ip adres.... Is internet connected/working?')
    return ''

def checkName(strName):
	strName=str(strName)
	if len(strName)==0 or len(strName)>maxnamelen:
		return False
	foundIllegalChar=False
	for s in strName:
		if not s in allowed:
			foundIllegalChar=True
	if foundIllegalChar:
		return False
	if strName.upper()=='ADMIN':
		return False
	if strName.upper()=='STATIC':
		return False
	return True

def stripName(name):
	name=name.strip()
	newname=''
	counter=0
	for n in name:
		if n in allowed:
			newname=newname+n
			counter=counter+1
			if counter==maxnamelen:
				break
	return newname
	
def GetConnectTo(remote_address):
    if (remote_address==localIP):
        return localIP+':'+str(PORT)
    elif (remote_address[:4]=='192.'):
        return LANIP+':'+str(PORT)
    else:
        return WANIP+':'+str(PORT)

def urIndex(request):
	userConnectsTo=GetConnectTo(request.remote_addr)
	a= render_template('ur.html')
	a=a.replace('%%CONNECTTO%%',userConnectsTo)
	if len(playerList)==0:
		bpi2='0000000'
		td='3333'
		gs='WaitingForOtherPlayer'
		if firstColor=='W':
			bpi='WWWWWWW'
		else:
			bpi='BBBBBBB'
	else:
		td='2222'
		gs='DetermineStart'
		if firstColor=='W':
			bpi='BBBBBBB'
			bpi2='WWWWWWW'
		else:
			bpi='WWWWWWW'
			bpi2='BBBBBBB'

	gameVars="""					var blocksArray='RSSS00RSSSSRSSSSRSSS00RS';
	var topPlayerIn='"""+bpi2+"""';
	var topPlayerOut='0000000';
	var onBoard='000000000000000000000000';
	var bottomPlayerIn='"""+bpi+"""';
	var bottomPlayerOut='0000000';
	var topDice='"""+td+"""';
	var bottomDice='2222';
	var gamestate='"""+gs+"""';"""
	a=a.replace('%%GAMEVARS%%',gameVars)
	return a

@app.route('/')
def app_index():
	print (request.remote_addr,'/')
	return urIndex(request)
	
@app.route('/ur')
def app_ur():
	print (request.remote_addr,'/ur')
	return urIndex(request)  

@app.route('/ur/')
def app_urslash():
	print (request.remote_addr,'/ur/')
	return urIndex(request) 

@app.route('/socket.js')
def app_socket():
	print (request.remote_addr, locationStaticFiles+'/socket.js --> /socket.js')
	return send_file(locationStaticFiles+'/socket.js', mimetype='application/javascript')

@app.route('/babylon.js')
def app_babylon():
	print (request.remote_addr, locationStaticFiles+'/babylon.js --> /babylon.js')
	return send_file(locationStaticFiles+'/babylon.js', mimetype='application/javascript')

@app.route('/favicon.ico')
def app_favicon():
	print (request.remote_addr, locationStaticFiles+'/favicon.ico --> /favicon.png')
	return send_file(locationStaticFiles+'/favicon.png', mimetype='image/ico')

@app.route('/wood0.png')
def app_wood0():
	print (request.remote_addr, locationStaticFiles+'/wood0.png --> /wood0.png')
	return send_file(locationStaticFiles+'/wood0.png', mimetype='image/png')

@app.route('/wood1.png')
def app_wood1():
	print (request.remote_addr, locationStaticFiles+'/wood1.png --> /wood1.png')
	return send_file(locationStaticFiles+'/wood1.png', mimetype='image/png')

@app.route('/wood2.png')
def app_wood2():
	print (request.remote_addr, locationStaticFiles+'/wood2.png --> /wood2.png')
	return send_file(locationStaticFiles+'/wood2.png', mimetype='image/png')

@app.route('/wood3.png')
def app_wood3():
	print (request.remote_addr, locationStaticFiles+'/wood3.png --> /wood3.png')
	return send_file(locationStaticFiles+'/wood3.png', mimetype='image/png')

@app.route('/stone.png')
def app_stone():
	print (request.remote_addr, locationStaticFiles+'/stone.png --> /stone.png')
	return send_file(locationStaticFiles+'/stone.png', mimetype='image/png')

@app.route('/rose.png')
def app_rose():
	print (request.remote_addr, locationStaticFiles+'/rose.png --> /rose.png')
	return send_file(locationStaticFiles+'/rose.png', mimetype='image/png')

@app.route('/white.png')
def app_white():
	print (request.remote_addr, locationStaticFiles+'/white.png --> /white.png')
	return send_file(locationStaticFiles+'/white.png', mimetype='image/png')

@app.route('/black.png')
def app_black():
	print (request.remote_addr, locationStaticFiles+'/black.png --> /black.png')
	return send_file(locationStaticFiles+'/black.png', mimetype='image/png')

@socketio.on('getState', namespace='/urlobbie')
def on_getState():
	print('Client '+request.sid+' getState')
	socketio.emit('newState', (board), namespace='/urlobbie')
	
@socketio.on('connect', namespace='/urlobbie')
def on_connect():
	print('Client '+request.sid+' connected')
	#socketio.emit('newState', (board), namespace='/urlobbie')
	
@socketio.on('disconnect', namespace='/urlobbie')
def on_disconnect():
	print('Client '+request.sid+' disconnected')

if __name__ == "__main__":
	try:
		PORT=abs(int(os.getenv('PORT')))
	except:
		pass
	LANIP=os.getenv('LANIP', LANIP)
	WANIP=getWideIpAdres()
	print ()
	print ("The Royal Game Of Ür")
	print ("v0.02")
	print ("localIP="+localIP)
	print ("LANIP="+LANIP)
	print ("WANIP="+WANIP)
	print ("PORT="+str(PORT))
	print ()
		
	try:
		socketio.run(app, debug=False, port=PORT, host="0.0.0.0")
	except Exception as x:
		print(x)
		traceback.print_exc()
