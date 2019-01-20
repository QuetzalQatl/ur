from flask import Flask, render_template, request, send_file,abort, redirect
from flask_socketio import SocketIO, join_room, leave_room, emit, send
from urllib.request import urlopen
from base64 import b64decode, decodebytes
from urllib.parse import unquote
from random import randint

#from codenames import game
import time
import datetime
import random
import traceback
import socket
import sys
import os
import json

PORT=5003 # default, can be set at startup by setting the environment variable 'PORT'
locationStaticFiles="/static/"

playerList={}
boardSetupDefault={'adminStones':7, 'playerStones':7, 'allowOvershoot':False, 'allowBackwards':False, 'route':'Short', 'startRule':'Roll', 'adminColor':'Black'}
boardSetup=boardSetupDefault
boardDefault={ 'legalMoves':[],'adminOut':0, 'adminIn':0, 'playerOut':0, 'playerIn':0, 'adminDices':'0000', 'playerDices':'0000', 'gameState':'setup', 'board':'000000000000000000000000'}
board=boardDefault
routes={'player':{'Short':[19,18,17,16,8,9,10,11,12,13,14,15,23,22], 'Long':[19,18,17,16,8,0,1,9,10,2,3,11,12,13,14,6,7,15,23,22]}, 'admin':{'Short':[3,2,1,0,8,9,10,11,12,13,14,15,7,6], 'Long':[3,2,1,0,8,16,17,9,10,18,19,11,12,13,14,22,23,15,7,6]}}
roseNrs=[0,6,11,16,22]
whiteWonMessages=['White Has Won!!','Yezzz! White Won!','White White Won Won','Black Gone, White Won','White, oh yeah!','omg omg omg White Won!','Another Win for White!','You can always count on White']
blackWonMessages=['Black Has Won!!','Yippy! Black Won!','Black Won BAM!','White Gone, Black Won','Black, oh yeah!','omg omg omg Black Won!','Another Win for Black!','You can always count on Black']

# initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(512)
socketio = SocketIO(app)

advSetting={'logToFile':True, 'logFileName':'logs.txt'}

def log(*text):
	try:
		str2=''
		first=True
		for t in text:
			if first:
				str2=str2+str(t)
				first=False
			else:
				str2=str2+', '+str(t)
		if advSetting['logToFile']:
			with open(locationStaticFiles+advSetting['logFileName'], "a+") as f:
				f.write(str2+'\n')
		print(str2)		
	except Exception as x:
		print(x)
		traceback.print_exc()

def get4TossWithTotal():
	d=[]
	total=0
	for i in range (0,4):
		a=randint(0,1)
		if a==0:
			d.append('G')
			total=total+1
		else:
			d.append('R')	
	#total=3  # to check draws on throwforstart
	d.append(total)
	return d

def getPlaceInList(item, list):
	count=0
	for l in list:
		if item==l:
			return count
		count=count+1
	return -1

def placeOnBoard(what, where):
	#log ('placeOnBoard:', what, where)
	l=[]
	for letter in board['board']:
		l.append(letter)
	l[where]=what
	str=''
	for letter in l:
		str=str+letter
	#log('newboard:', str)
	board['board']=str

def getLegalMoves(player):
	l={}
	rolled=player['lastRoll']
	
	if rolled==0:#throw zero: no moves. 
		return l
	
	color='0'
	otherColor='0'
	
	if player['isAdmin'] or player['isPlayer']:
		if player['isAdmin']:
			route=routes['admin'][boardSetup['route']]
			piecesOut=board['adminOut']
			color=boardSetup['adminColor'][0]
			if color=='B':
				otherColor='W'
			else:
				otherColor='B'
		else:
			route=routes['player'][boardSetup['route']]
			piecesOut=board['playerOut']
			otherColor=boardSetup['adminColor'][0]
			if otherColor=='B':
				color='W'
			else:
				color='B'
				
	if piecesOut>0 and board['board'][route[rolled-1]]!=color:#setup possible?
		l[-1]=route[rolled-1]
	
	count=0
	for r in route:#on board?
		b=board['board'][r]
		log(r, b, color, b==color)
		if b==color:
			log(count+rolled, len(route))
			if count+rolled<len(route):#move still on board
				log('smaller then len route')
				if board['board'][route[count+rolled]]!=color:
					log('not the same color')
					if not(board['board'][route[count+rolled]]==otherColor and route[count+rolled] in roseNrs):
						log('not occupied rose: add ')
						l[route[count]]=route[count+rolled]
			#'allowOvershoot':False, 'allowBackwards':False,
			elif count+rolled==len(route):#exact out
				log('count+rolled==len(route)')
				l[route[count]]=-2
			else: #overshoots?
				log('overshoots?')
				if boardSetup['allowOvershoot']:
					log('yes')
					l[route[count]]=-2
				else:
					log('no')
		count=count+1
	log('legal Moves:', l)
	return l

def urIndex(request):
	return render_template('ur.html')

@app.route('/')
def app_index():
	log (request.remote_addr,'/')
	return urIndex(request)
	
@app.route('/ur')
def app_ur():
	log (request.remote_addr,'/ur')
	return urIndex(request)  

@app.route('/ur/')
def app_urslash():
	log (request.remote_addr,'/ur/')
	return urIndex(request) 

@app.route('/logs.txt')
def app_logs():
	#log (request.remote_addr, locationStaticFiles+'/logs.txt --> /logs.txt')
	return send_file(locationStaticFiles+'/logs.txt', mimetype='text/plain')

@app.route('/socket.js')
def app_socket():
	#log (request.remote_addr, locationStaticFiles+'/socket.js --> /socket.js')
	return send_file(locationStaticFiles+'/socket.js', mimetype='application/javascript')

@app.route('/babylon.js')
def app_babylon():
	#log (request.remote_addr, locationStaticFiles+'/babylon.js --> /babylon.js')
	return send_file(locationStaticFiles+'/babylon.js', mimetype='application/javascript')

@app.route('/favicon.ico')
def app_favicon():
	#log (request.remote_addr, locationStaticFiles+'/favicon.ico --> /favicon.png')
	return send_file(locationStaticFiles+'/favicon.png', mimetype='image/ico')

@app.route('/wood0.png')
def app_wood0():
	#log (request.remote_addr, locationStaticFiles+'/wood0.png --> /wood0.png')
	return send_file(locationStaticFiles+'/wood0.png', mimetype='image/png')

@app.route('/wood1.png')
def app_wood1():
	#log (request.remote_addr, locationStaticFiles+'/wood1.png --> /wood1.png')
	return send_file(locationStaticFiles+'/wood1.png', mimetype='image/png')

@app.route('/wood2.png')
def app_wood2():
	#log (request.remote_addr, locationStaticFiles+'/wood2.png --> /wood2.png')
	return send_file(locationStaticFiles+'/wood2.png', mimetype='image/png')

@app.route('/wood3.png')
def app_wood3():
	#log (request.remote_addr, locationStaticFiles+'/wood3.png --> /wood3.png')
	return send_file(locationStaticFiles+'/wood3.png', mimetype='image/png')

@app.route('/wood4.png')
def app_wood4():
	#log (request.remote_addr, locationStaticFiles+'/wood4.png --> /wood4.png')
	return send_file(locationStaticFiles+'/wood4.png', mimetype='image/png')

@app.route('/wood5.png')
def app_wood5():
	#log (request.remote_addr, locationStaticFiles+'/wood5.png --> /wood5.png')
	return send_file(locationStaticFiles+'/wood5.png', mimetype='image/png')

@app.route('/wood6.png')
def app_wood6():
	#log (request.remote_addr, locationStaticFiles+'/wood6.png --> /wood6.png')
	return send_file(locationStaticFiles+'/wood6.png', mimetype='image/png')

@app.route('/wood7.png')
def app_wood7():
	#log (request.remote_addr, locationStaticFiles+'/wood7.png --> /wood7.png')
	return send_file(locationStaticFiles+'/wood7.png', mimetype='image/png')

@app.route('/stone.png')
def app_stone():
	#log (request.remote_addr, locationStaticFiles+'/stone.png --> /stone.png')
	return send_file(locationStaticFiles+'/stone.png', mimetype='image/png')

@app.route('/rose.png')
def app_rose():
	#log (request.remote_addr, locationStaticFiles+'/rose.png --> /rose.png')
	return send_file(locationStaticFiles+'/rose.png', mimetype='image/png')

@app.route('/white.png')
def app_white():
	#log (request.remote_addr, locationStaticFiles+'/white.png --> /white.png')
	return send_file(locationStaticFiles+'/white.png', mimetype='image/png')

@app.route('/black.png')
def app_black():
	#log (request.remote_addr, locationStaticFiles+'/black.png --> /black.png')
	return send_file(locationStaticFiles+'/black.png', mimetype='image/png')

@app.route('/roll1.wav')
def app_rollWav1():	
	return send_file(locationStaticFiles+'/roll1.wav', mimetype='audio/wav')

@app.route('/roll2.wav')
def app_rollWav2():	
	return send_file(locationStaticFiles+'/roll2.wav', mimetype='audio/wav')

@app.route('/roll3.wav')
def app_rollWav3():	
	return send_file(locationStaticFiles+'/roll3.wav', mimetype='audio/wav')


@socketio.on('getState', namespace='/urlobbie')
def on_getState():
	log('Client '+request.sid+' getState')
	p=playerList[request.sid]
	b=board
	b['gameState']=p['gameState']
	socketio.emit('newState', (b), room=request.sid, namespace='/urlobbie')
	
@socketio.on('whoAmI', namespace='/urlobbie')
def on_getState():
	log('Client '+request.sid+' whoAmI')
	youare='observer'
	player=playerList[request.sid]
	if player['isAdmin']:
		youare='admin'
	if player['isPlayer']:
		youare='player'
	socketio.emit('newSetting', ('youAre', youare), room=request.sid, namespace='/urlobbie')
	
@socketio.on('startGame', namespace='/urlobbie')
def on_startGame():
	log('Client '+request.sid+' startGame')
	board['adminOut']=int(boardSetup['adminStones'])
	board['playerOut']=int(boardSetup['playerStones'])
	board['adminIn']=0
	board['playerIn']=0
	hasAdmin=False
	hasPlayer=False
	for player, vars in playerList.items():
		if vars['isAdmin']==True:
			board['adminDices']='SSSS'
			hasAdmin=True
		elif vars['isPlayer']==True:
			board['playerDices']='SSSS'
			hasPlayer=True
	if boardSetup['startRule']=='Roll':
		board['gameState']='rollForStart'
		board['adminOut']=0
		board['playerOut']=0
	elif boardSetup['startRule']=='Random':
		if randint(0,1)==0:
			board['gameState']='adminThrow'
			board['playerDices']='RRRR'
		else:
			board['gameState']='playerThrow'
			board['adminDices']='RRRR'
	elif boardSetup['startRule']=='Black':
		if boardSetup['adminColor']=='Black':
			board['gameState']='adminThrow'
			board['playerDices']='RRRR'
		else:
			board['gameState']='playerThrow'
			board['adminDices']='RRRR'
	elif boardSetup['startRule']=='White':
		if boardSetup['adminColor']=='White':
			board['gameState']='adminThrow'
			board['playerDices']='RRRR'
		else:
			board['gameState']='playerThrow'
			board['adminDices']='RRRR'
	log('emit newState: ', str(board))
	socketio.emit('newState', (board), namespace='/urlobbie')

@socketio.on('movesTo', namespace='/urlobbie')
def on_movesTo(what):
	log('Client '+request.sid+' movesTo', what)
	hasAdmin=playerList[request.sid]['isAdmin']
	hasPlayer=playerList[request.sid]['isPlayer']
	emitNewState=False	
	log(boardSetup)
	log(board)
	log ('hasAdmin', hasAdmin)
	log ('hasPlayer', hasPlayer)
	if hasAdmin:
		routeNrs=routes['admin'][boardSetup['route']] # boardSetup['route'] = either Short or Long
		color=boardSetup['adminColor'][0]
		if color=='B':
			otherColor='W'
		else:
			otherColor='B'
	else:
		routeNrs=routes['player'][boardSetup['route']] # boardSetup['route'] = either Short or Long
		otherColor=boardSetup['adminColor'][0]
		if otherColor=='B':
			color='W'
		else:
			color='B'
			
	log ('color', color,'otherColor', otherColor)
	if what=='adminOut' or what=='playerOut' or what=='nothing':
		what=-2
	log(what, board['legalMoves'])
	l=board['legalMoves']
	log ('l',l)
	if what in l:
		if (hasAdmin and board['gameState']=='adminMoveTo') or (hasPlayer and board['gameState']=='playerMoveTo'):
			if what==-2:
				if hasAdmin:
					board['adminIn']=board['adminIn']+1
					board['gameState']='playerThrow'
				elif hasPlayer:
					board['playerIn']=board['playerIn']+1
					board['gameState']='adminThrow'
			elif what<24:
				if board['board'][what]==otherColor:
					if hasAdmin:
						board['playerOut']=board['playerOut']+1
					elif hasPlayer:
						board['adminOut']=board['adminOut']+1
				placeOnBoard(color, what)
				log(hasAdmin, hasPlayer, what, roseNrs, what in roseNrs)
				if hasAdmin:
					board['gameState']='playerThrow'
					if what in roseNrs:
						board['gameState']='adminThrow'
				elif hasPlayer:
					board['gameState']='adminThrow'
					if what in roseNrs:
						board['gameState']='playerThrow'
			log('found legit choice')
			log ('emitting: ',board)
			socketio.emit('newState', (board), namespace='/urlobbie')
			winner=False
			winnerColor='0'
			if str(board['adminIn'])==boardSetup['adminStones']:
				winner=True
				winnerColor=boardSetup['adminColor'][0]
				log('winnerColor', winnerColor)
			if str(board['playerIn'])==boardSetup['playerStones']:				
				winner=True
				winnerColor=boardSetup['adminColor'][0]
				log('winnerColor', winnerColor)
				if winnerColor=='B':
					winnerColor='W'
				else:
					winnerColor='B'
				log('winnerColor', winnerColor)
			if winner:
				log('winner')
				if winnerColor=='W':
					log('W')
					log(whiteWonMessages)
					r=randint(0,len(whiteWonMessages)-1)
					log(r)
					message=whiteWonMessages[r]
					log(message)
				else:
					log('B')
					log(blackWonMessages)
					r=randint(0,len(blackWonMessages)-1)
					log(r)
					message=blackWonMessages[r]
					log(message)
				socketio.sleep(2.4)
				board['adminIn']=0
				board['playerIn']=0
				board['adminOut']=int(boardSetup['adminStones'])
				board['playerOut']=int(boardSetup['playerStones'])
				board['board']='000000000000000000000000'
				board['playerDices']='SSSS'
				board['adminDices']='SSSS'
				board['gameState']='setup'
				socketio.emit('winner', (message), namespace='/urlobbie')

@socketio.on('moves', namespace='/urlobbie')
def on_moves(what):
	log('Client '+request.sid+' moves', what)
	hasAdmin=playerList[request.sid]['isAdmin']
	hasPlayer=playerList[request.sid]['isPlayer']
	emitNewState=False	
	log(boardSetup)
	log(board)
	log ('hasAdmin', hasAdmin)
	log ('hasPlayer', hasPlayer)
	if hasAdmin:
		color=boardSetup['adminColor'][0]
		if color=='B':
			otherColor='W'
		else:
			otherColor='B'
	else:
		otherColor=boardSetup['adminColor'][0]
		if otherColor=='B':
			color='W'
		else:
			color='B'
			
	log ('color', color,'otherColor', otherColor)
	if what=='adminOut' or what=='playerOut':
		what=-1
	log(what, board['legalMoves'])
		
	if what in board['legalMoves']:
		if (board['gameState']=='playerMove' and hasPlayer) or (board['gameState']=='adminMove' and hasAdmin):
			if what==-1:
				if hasPlayer:
					board['playerOut']=board['playerOut']-1
				else:
					board['adminOut']=board['adminOut']-1
					
			placeOnBoard('0', what)
			rolled=playerList[request.sid]['lastRoll']
			if hasPlayer:
				board['gameState']='playerMoveTo'
				routeNrs=routes['player'][boardSetup['route']] # boardSetup['route'] = either Short or Long
			elif board['gameState']=='adminMove':
				board['gameState']='adminMoveTo'
				routeNrs=routes['admin'][boardSetup['route']] # boardSetup['route'] = either Short or Long
			board['legalMoves']=[]
			currentPlace=getPlaceInList(what, routeNrs)
			if currentPlace+rolled<len(routeNrs):
				board['legalMoves'].append(routeNrs[currentPlace+rolled])
			elif currentPlace+rolled==len(routeNrs):
				board['legalMoves'].append(-2)
			else:
				if boardSetup['allowOvershoot']:
					board['legalMoves'].append(-2)
					
			log ('emitting: ',board)
			socketio.emit('newState', (board), namespace='/urlobbie')


@socketio.on('throwDices', namespace='/urlobbie')
def on_throwDices():
	log('Client '+request.sid+' throwDices')
	hasAdmin=playerList[request.sid]['isAdmin']
	hasPlayer=playerList[request.sid]['isPlayer']
	log(boardSetup)
	emitNewState=False	
	emitReRoll=False
	log(board)
	
	if board['gameState']=='adminThrow' or board['gameState']=='playerThrow':
		d=get4TossWithTotal()
		log (d[0],d[1],d[2],d[3], 'total: ', d[4])
		if board['gameState']=='adminThrow' and hasAdmin:
			board['adminDices']=d[0]+d[1]+d[2]+d[3]
			playerList[request.sid]['hasRolled']=True
			playerList[request.sid]['lastRoll']=d[4]	
			board['legalMoves']=getLegalMoves(playerList[request.sid])
			if len(board['legalMoves']):
				board['gameState']='adminMove'
			else:
				board['gameState']='playerThrow'
		
			emitNewState=True
			
		elif board['gameState']=='playerThrow' and hasPlayer:
			board['playerDices']=d[0]+d[1]+d[2]+d[3]
			playerList[request.sid]['hasRolled']=True
			playerList[request.sid]['lastRoll']=d[4]
			board['legalMoves']=getLegalMoves(playerList[request.sid])
			if len(board['legalMoves']):
				board['gameState']='playerMove'
			else:
				board['gameState']='adminThrow'
		
			emitNewState=True
			
	elif board['gameState']=='rollForStart':
		if boardSetup['startRule']=='Roll' and (hasAdmin or hasPlayer):
			emitNewState=True
			log (playerList[request.sid])
			if not playerList[request.sid]['hasRolled']:
				d=get4TossWithTotal()
				log (d[0],d[1],d[2],d[3], 'total: ', d[4])
					
				playerList[request.sid]['hasRolled']=True
				playerList[request.sid]['lastRoll']=d[4]
				
				if hasAdmin:
					board['adminDices']=d[0]+d[1]+d[2]+d[3]
					for sid in playerList:
						for key, value in playerList[sid].items():
							if key=='isPlayer' and value==True and playerList[sid]['hasRolled']:
								emitReRoll=True
								log ("playerList[sid]['lastRoll']", playerList[sid]['lastRoll'])
								log ("playerList[request.sid]['lastRoll']", playerList[request.sid]['lastRoll'])
								if playerList[sid]['lastRoll']<playerList[request.sid]['lastRoll']:
									board['gameState']='adminThrow'
									board['adminOut']=int(boardSetup['adminStones'])
									board['playerOut']=int(boardSetup['playerStones'])
									log ('emit adminThrow')
								elif playerList[sid]['lastRoll']>playerList[request.sid]['lastRoll']:
									board['gameState']='playerThrow'
									board['adminOut']=int(boardSetup['adminStones'])
									board['playerOut']=int(boardSetup['playerStones'])
									log ('emit playerThrow')
								else:
									log ('emit rollforstart')
									
				elif hasPlayer:
					board['playerDices']=d[0]+d[1]+d[2]+d[3]
					for sid in playerList:
						for key, value in playerList[sid].items():
							if key=='isAdmin' and value==True and playerList[sid]['hasRolled']:
								emitReRoll=True
								log ("playerList[sid]['lastRoll']", playerList[sid]['lastRoll'])
								log ("playerList[request.sid]['lastRoll']", playerList[request.sid]['lastRoll'])
								if playerList[sid]['lastRoll']<playerList[request.sid]['lastRoll']:
									board['gameState']='playerThrow'
									board['adminOut']=int(boardSetup['adminStones'])
									board['playerOut']=int(boardSetup['playerStones'])
									log ('emit playerThrow')
								elif playerList[sid]['lastRoll']>playerList[request.sid]['lastRoll']:
									board['gameState']='adminThrow'
									board['adminOut']=int(boardSetup['adminStones'])
									board['playerOut']=int(boardSetup['playerStones'])
									log ('emit adminThrow')
								else:
									log ('emit rollforstart')
	if emitNewState:
		rolList=['roll1.wav', 'roll2.wav', 'roll3.wav']
		r=randint(0,2)
		socketio.emit('sound', (rolList[r]), namespace='/urlobbie')
		log ('emitting: ',board)
		log(datetime.datetime.now())
		socketio.emit('newState', (board), namespace='/urlobbie')
		if emitReRoll:
			socketio.sleep(1.0)
			if board['gameState']=='adminThrow':
				board['adminDices']='SSSS'
			elif board['gameState']=='playerThrow':
				board['playerDices']='SSSS'
			elif board['gameState']=='rollForStart':
				board['playerDices']='SSSS'
				board['adminDices']='SSSS'
			playerList[sid]['hasRolled']=False
			playerList[request.sid]['hasRolled']=False
			playerList[sid]['lastRoll']=0
			playerList[request.sid]['lastRoll']=0
			log ('emitReRoll: ',board)
			log(datetime.datetime.now())
			socketio.emit('newState', (board), namespace='/urlobbie')

@socketio.on('getSettings', namespace='/urlobbie')
def on_getSettings():
	log('Client '+request.sid+' getSettings')
	for key, value in boardSetup.items():
		if key=='allowOvershoot':
			if value==False:
				value='No Overshoot'
			else:
				value='Overshoot'
		elif key=='allowBackwards':
			if value==False:
				value='No AllowBack'
			else:
				value='AllowBack'
		socketio.emit('newSetting', (key, value), room=request.sid, namespace='/urlobbie')

@socketio.on('updateSetting', namespace='/urlobbie')
def on_updateSetting(what, to):
	log('Client '+request.sid+' updateSetting', what, to)
	ok=True
	if what=='adminStones' or what=='playerStones':
		if len(to)>0:
			try:
				nr=int(to)
				if nr<1 or nr>12:
					ok=False
			except:
				ok=False
			if ok:
				socketio.emit('newSetting', (what, to), namespace='/urlobbie')
			else:
				socketio.emit('refusedSetting', (what, 7), room=request.sid, namespace='/urlobbie')
				socketio.emit('newSetting', (what, 7), namespace='/urlobbie')
		else:
			return # dont do anything when nothing is in the box
	else:
		socketio.emit('newSetting', (what, to), namespace='/urlobbie')
	if what=='allowOvershoot':
		if to=='No Overshoot':
			to=False
		else:
			to=True
	if what=='allowBackwards':
		if to=='No AllowBack':
			to=False
		else:
			to=True	
	boardSetup[what]=to
	log (boardSetup)
		
@socketio.on('connect', namespace='/urlobbie')
def on_connect():
	log('Client '+request.sid+' connected')
	args={}
	hasAdmin=False
	hasPlayer=False
	
	for player, vars in playerList.items():
		if vars['isAdmin']==True:
			hasAdmin=True
		elif vars['isPlayer']==True:
			hasPlayer=True

	if not hasAdmin:
		args['isAdmin']=True
		args['isPlayer']=False
		args['gameState']=board['gameState']
		args['hasRolled']=False
		args['lastRoll']=0
		args['comesFrom']=-1
		
		board['adminDices']='SSSS'
		playerList[request.sid]=args
		socketio.emit('newState', (board), namespace='/urlobbie')
	elif not hasPlayer:
		args['isAdmin']=False
		args['isPlayer']=True
		args['gameState']=board['gameState']
		args['hasRolled']=False
		args['lastRoll']=0
		args['comesFrom']=-1

		board['playerDices']='SSSS'
		playerList[request.sid]=args
		socketio.emit('newState', (board), namespace='/urlobbie')
	else:
		args['isAdmin']=False
		args['isPlayer']=False
		args['gameState']=board['gameState']
		args['hasRolled']=False
		args['lastRoll']=0
		args['comesFrom']=-1
		
		playerList[request.sid]=args
	log (playerList)
	
@socketio.on('disconnect', namespace='/urlobbie')
def on_disconnect():
	log('Client '+request.sid+' disconnected')
	global board
	playerList.pop(request.sid)
	hasAdmin=False
	hasPlayer=False
	for player, vars in playerList.items():
		if vars['isAdmin']:
			hasAdmin=True
		elif vars['isPlayer']:
			hasPlayer=True
	if not hasAdmin and not hasPlayer:
		board=boardDefault
		socketio.emit('newState', (board), namespace='/urlobbie')
	if hasAdmin and not hasPlayer:
		board['playerDices']='0000'
		socketio.emit('newState', (board), namespace='/urlobbie')
	if not hasAdmin and hasPlayer:
		board['adminDices']='0000'
		socketio.emit('newState', (board), namespace='/urlobbie')

if __name__ == "__main__":
	try:
		with open(locationStaticFiles+'logs.txt', "w+") as f:
			f.write('')
		PORT=abs(int(os.getenv('PORT')))
	except:
		pass
	log ()
	log ("The Royal Game Of Ür")
	log ("v0.04")
	log ("PORT="+str(PORT))
	log ()
		
	try:	
		socketio.run(app, debug=False, port=PORT, host="0.0.0.0")
	except Exception as x:
		log(x)
		traceback.print_exc()
		
