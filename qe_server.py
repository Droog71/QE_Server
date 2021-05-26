from flask import send_from_directory
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from waitress import serve
import sqlite3 as lite
import urllib
import threading
import time
import Tkinter
from Tkinter import Button
from Tkconstants import INSIDE, INSERT
import ScrolledText
import sys
import os
import socket
import platform
import requests
import server_var

app = Flask(__name__)
api = Api(app)
window = None

#Creates all the required database tables.
def create_database():
    global app
    
    player_con = lite.connect('player_database.db')
    with player_con:
        player_cur = player_con.cursor()   
        player_cur.execute("CREATE TABLE IF NOT EXISTS players(name TEXT, x FLOAT, y FLOAT, z FLOAT, fx FLOAT, fz FLOAT, red FLOAT, green FLOAT, blue FLOAT)")
        
    chat_con = lite.connect('chat_database.db')
    with chat_con:
        chat_cur = chat_con.cursor()   
        chat_cur.execute("CREATE TABLE IF NOT EXISTS chat(name TEXT, message TEXT)")
        
    block_con = lite.connect('block_database.db')
    with block_con:
        block_cur = block_con.cursor()
        block_cur.execute("CREATE TABLE IF NOT EXISTS blocks(destroy INTEGER, block TEXT, x FLOAT, y FLOAT, z FLOAT, rx FLOAT, ry FLOAT, rz FLOAT, rw FLOAT)")
        
    storage_con = lite.connect('storage_database.db')
    with storage_con:
        storage_cur = storage_con.cursor()
        storage_cur.execute("CREATE TABLE IF NOT EXISTS storage(x FLOAT, y FLOAT, z FLOAT, slot INTEGER, item TEXT, amount INTEGER)")
        
    conduit_con = lite.connect('conduit_database.db')
    with conduit_con:
        conduit_cur = conduit_con.cursor()
        conduit_cur.execute("CREATE TABLE IF NOT EXISTS conduits(x FLOAT, y FLOAT, z FLOAT, range INTEGER)")
        
    power_con = lite.connect('power_database.db')
    with power_con:
        power_cur = power_con.cursor()
        power_cur.execute("CREATE TABLE IF NOT EXISTS power(x FLOAT, y FLOAT, z FLOAT, range INTEGER, dual TEXT)")
        
    machine_con = lite.connect('machine_database.db')
    with machine_con:
        machine_cur = machine_con.cursor()
        machine_cur.execute("CREATE TABLE IF NOT EXISTS machines(x FLOAT, y FLOAT, z FLOAT, speed INTEGER)")
        
    hub_con = lite.connect('hub_database.db')
    with hub_con:
        hub_cur = hub_con.cursor()
        hub_cur.execute("CREATE TABLE IF NOT EXISTS hubs(x FLOAT, y FLOAT, z FLOAT, circuit INTEGER, range INTEGER, stop INTEGER, time INTEGER)")
        
    paint_con = lite.connect("paint_database")
    with paint_con:
        paint_cur = paint_con.cursor()
        paint_cur.execute("CREATE TABLE IF NOT EXISTS paint(block TEXT, red FLOAT, green FLOAT, blue FLOAT)")

#Exits the program.
def end():
    server_log("Exiting in one second...")
    time.sleep(1)
    os._exit(0)

#Executes end function in new thread.
def stop():
    shutdown_thread = threading.Thread(target = end)
    shutdown_thread.daemon = True
    shutdown_thread.start()     

#Handles world download requests from clients.
@app.route('/world', methods = ['GET'])
def get_files():    
    if server_var.local == True:
        if server_var.devel == True:
            world = "localhost.sav"
        else:
            world = get_local_address() + ".sav"
    else:
        world = get_external_address() + ".sav"
        
    if platform.system() == "Linux":
        return send_from_directory(os.path.expanduser('~')+"/.config/unity3d/Droog71/Quantum Engineering/SaveData", world, as_attachment=True)
    if platform.system() == "Windows":
        return send_from_directory(os.path.expanduser('~')+"\AppData\LocalLow\Droog71\Quantum Engineering\SaveData", world, as_attachment=True)
    if platform.system() == "Darwin":
        return send_from_directory(os.path.expanduser('~')+"/Library/Application Support/Droog71/Quantum Engineering/SaveData", world, as_attachment=True)

#Handles player updates from clients.   
@app.route('/players', methods=['POST'])
def receive_player_data():
    inputstr = request.data
    entry = str(inputstr).split("@")[1]
    name = entry.split(":")[0]
    values = entry.split(":")[1]
    x = values.split(",")[0]
    y = values.split(",")[1]
    z = values.split(",")[2]
    fx = values.split(",")[3]
    fz = values.split(",")[4] 
    r = values.split(",")[5]
    g = values.split(",")[6]
    b = values.split(",")[7]
    add_player_data(name, x, y, z, fx, fz, r, g, b)   
    dictToReturn = {'response':str(inputstr)}
    return jsonify(dictToReturn)

#Handles chat messages received from clients.
@app.route('/chat', methods=['POST'])
def receive_chat_data():
    inputstr = request.data
    entry = str(inputstr).split("@")[1]
    name = entry.split(":")[0]
    message = entry.split(":")[1] 
    add_chat_message(name, message)   
    dictToReturn = {'response':str(inputstr)}
    server_log("chat: "+entry)
    return jsonify(dictToReturn)

#Updates blocks instantiated or removed by clients.
@app.route('/blocks', methods=['POST'])
def receive_block_data():
    inputstr = request.data
    entry = str(inputstr).split("@")[1]
    destroy = entry.split(":")[0]
    block = entry.split(":")[1]
    coords = entry.split(":")[2]
    rotation = entry.split(":")[3]
    x = coords.split(",")[0]
    y = coords.split(",")[1]
    z = coords.split(",")[2]
    rx = rotation.split(",")[0]
    ry = rotation.split(",")[1]
    rz = rotation.split(",")[2]
    rw = rotation.split(",")[3]
    add_block_data(destroy, block, x, y, z, rx, ry, rz, rw)        
    dictToReturn = {'response':str(inputstr)}
    server_log("blocks: "+entry)
    return jsonify(dictToReturn)

#Handles storage inventory changes from both host and clients.
@app.route('/storage', methods=['POST'])
def receive_storage_data():
    inputstr = request.data
    entry = str(inputstr).split("@")[1]
    storage_location = entry.split(":")[0]
    storage_x = storage_location.split(",")[0]
    storage_y = storage_location.split(",")[1]
    storage_z = storage_location.split(",")[2]
    slot = entry.split(":")[1].split(";")[0]
    contents = entry.split(";")[1]
    item = contents.split("=")[0]
    amount = contents.split("=")[1]
    add_storage_data(storage_x, storage_y, storage_z, slot, item, amount)        
    dictToReturn = {'response':str(inputstr)}
    server_log("storage: "+entry);
    return jsonify(dictToReturn)

#Updates database when a player reboots a conduit or changes conduit range.
@app.route('/conduits', methods=['POST'])
def receive_conduit_data():
    inputstr = request.data
    entry = str("conduit: "+inputstr).split("@")[1]
    conduit_location = entry.split(":")[0]
    conduit_x = conduit_location.split(",")[0]
    conduit_y = conduit_location.split(",")[1]
    conduit_z = conduit_location.split(",")[2]
    conduit_range = entry.split(":")[1]
    add_conduit_data(conduit_x, conduit_y, conduit_z, conduit_range)        
    dictToReturn = {'response':str(inputstr)}
    server_log("conduit: "+entry);
    return jsonify(dictToReturn)

#Updates database when a player modifies power conduit settings.
@app.route('/power', methods=['POST'])
def receive_power_data():
    inputstr = request.data
    entry = str(inputstr).split("@")[1]
    power_location = entry.split(":")[0]
    power_x = power_location.split(",")[0]
    power_y = power_location.split(",")[1]
    power_z = power_location.split(",")[2]
    power_range = entry.split(":")[1].split(",")[0]
    dual_output = entry.split(":")[1].split(",")[1]
    add_power_data(power_x, power_y, power_z, power_range, dual_output)        
    dictToReturn = {'response':str(inputstr)}
    server_log("power: "+entry);
    return jsonify(dictToReturn)

#Updates database when a player reboots or changes the speed of a machine.
@app.route('/machines', methods=['POST'])
def receive_machine_data():
    inputstr = request.data
    entry = str(inputstr).split("@")[1]
    machine_location = entry.split(":")[0]
    machine_x = machine_location.split(",")[0]
    machine_y = machine_location.split(",")[1]
    machine_z = machine_location.split(",")[2]
    machine_speed = entry.split(":")[1]
    add_machine_data(machine_x, machine_y, machine_z, machine_speed)        
    dictToReturn = {'response':str(inputstr)}
    server_log("machine: "+entry);
    return jsonify(dictToReturn)

#Updates database when a player modifies rail cart hub settings.
@app.route('/hubs', methods=['POST'])
def receive_hub_data():
    inputstr = request.data
    entry = str(inputstr).split("@")[1]
    hub_location = entry.split(":")[0]
    hub_x = hub_location.split(",")[0]
    hub_y = hub_location.split(",")[1]
    hub_z = hub_location.split(",")[2]
    hub_circuit = entry.split(":")[1].split(",")[0]
    hub_range = entry.split(":")[1].split(",")[1]
    hub_stop = entry.split(":")[1].split(",")[2]
    hub_time = entry.split(":")[1].split(",")[3]
    add_hub_data(hub_x, hub_y, hub_z, hub_circuit, hub_range, hub_stop, hub_time)        
    dictToReturn = {'response':str(inputstr)}
    server_log("hubs: "+entry);
    return jsonify(dictToReturn)

#Handles requests to paint blocks over the network.
@app.route('/paint', methods=['POST'])
def receive_paint_data():
    inputstr = request.data
    entry = str(inputstr).split("@")[1]
    block = entry.split(":")[0]
    red = entry.split(":")[1].split(",")[0]
    green = entry.split(":")[1].split(",")[1]
    blue = entry.split(":")[1].split(",")[2]
    add_paint_data(block,red,green,blue)        
    dictToReturn = {'response':str(inputstr)}
    server_log("paint: "+entry);
    return jsonify(dictToReturn)

#Called by app.route function to modify database table.
def add_player_data(name, x, y, z, fx, fz, r, b, g):  
    player_con = lite.connect('player_database.db')
    player_cur = player_con.cursor()
    player_cur.execute("CREATE TABLE IF NOT EXISTS players(name TEXT, x FLOAT, y FLOAT, z FLOAT, fx FLOAT, fz FLOAT, red FLOAT, green FLOAT, blue FLOAT)") 
    player_cur.execute("DELETE FROM players WHERE name = (?)", (name,))
    player_cur.execute("INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",(name, x, y, z, fx, fz, r, b, g))
    server_var.player_updates = server_var.player_updates + 1
    if server_var.player_updates > 1000:
        player_cur.execute("DELETE FROM players WHERE name != (?)", (name,))
        server_var.player_updates = 0
    player_cur.close()
    player_con.commit()   
    player_con.close()

#Called by app.route function to modify database table.
def add_chat_message(name, message):
    chat_con = lite.connect('chat_database.db')
    chat_cur = chat_con.cursor()
    chat_cur.execute("CREATE TABLE IF NOT EXISTS chat(name TEXT, message TEXT)")
    chat_cur.execute("INSERT INTO chat VALUES (?, ?)",(name, message))
    server_var.chat_messages = server_var.chat_messages + 1
    if server_var.chat_messages > 50:
        chat_cur.execute("DELETE FROM chat")
        server_var.chat_messages = 0
    chat_cur.close()
    chat_con.commit()
    chat_con.close()

#Called by app.route function to modify database table. 
def add_block_data(destroy, block, x, y, z, rx, ry, rz, rw):
    if server_var.block_thread_2_busy == False:
        server_var.block_thread_1_busy = True
        server_var.block_time = 0
        block_con = lite.connect('block_database.db')
        block_cur = block_con.cursor()
        block_cur.execute("CREATE TABLE IF NOT EXISTS blocks(destroy INTEGER, block TEXT, x FLOAT, y FLOAT, z FLOAT, rx FLOAT, ry FLOAT, rz FLOAT, rw FLOAT)")
        block_cur.execute("DELETE FROM blocks WHERE x = (?) AND y = (?) AND z = (?)", (x, y, z))
        block_cur.execute("INSERT INTO blocks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",(destroy, block, x, y, z, rx, ry, rz, rw))
        block_cur.close()
        block_con.commit()
        block_con.close()
        server_var.block_thread_1_busy = False

#Called by app.route function to modify database table.   
def add_storage_data(x, y, z, slot, item, amount):
    storage_con = lite.connect('storage_database.db')
    storage_cur = storage_con.cursor()
    storage_cur.execute("CREATE TABLE IF NOT EXISTS storage(x FLOAT, y FLOAT, z FLOAT, slot INTEGER, item TEXT, amount INTEGER)")
    storage_cur.execute("DELETE FROM storage WHERE x = (?) AND y = (?) AND z = (?) AND slot = (?)", (x, y, z, slot))
    storage_cur.execute("INSERT INTO storage VALUES (?, ?, ?, ?, ?, ?)",(x, y, z, slot, item, amount))
    storage_cur.close()
    storage_con.commit()
    storage_con.close()

#Called by app.route function to modify database table.    
def add_conduit_data(x, y, z, conduit_range):
    conduit_con = lite.connect('conduit_database.db')
    conduit_cur = conduit_con.cursor()
    conduit_cur.execute("CREATE TABLE IF NOT EXISTS conduits(x FLOAT, y FLOAT, z FLOAT, range INTEGER)")
    conduit_cur.execute("DELETE FROM conduits WHERE x = (?) AND y = (?) AND z = (?)", (x,y,z))
    conduit_cur.execute("INSERT INTO conduits VALUES (?, ?, ?, ?)",(x, y, z, conduit_range))
    conduit_cur.close()
    conduit_con.commit()
    conduit_con.close()

#Called by app.route function to modify database table.    
def add_power_data(x, y, z, power_range, dual_output):
    power_con = lite.connect('power_database.db')
    power_cur = power_con.cursor()
    power_cur.execute("CREATE TABLE IF NOT EXISTS power(x FLOAT, y FLOAT, z FLOAT, range INTEGER, dual TEXT)")
    power_cur.execute("DELETE FROM power WHERE x = (?) AND y = (?) AND z = (?)", (x,y,z))
    power_cur.execute("INSERT INTO power VALUES (?, ?, ?, ?, ?)",(x, y, z, power_range, dual_output))
    power_cur.close()
    power_con.commit()
    power_con.close()

#Called by app.route function to modify database table.    
def add_machine_data(x, y, z, machine_speed):
    machine_con = lite.connect('machine_database.db')
    machine_cur = machine_con.cursor()
    machine_cur.execute("CREATE TABLE IF NOT EXISTS machines(x FLOAT, y FLOAT, z FLOAT, speed INTEGER)")
    machine_cur.execute("DELETE FROM machines WHERE x = (?) AND y = (?) AND z = (?)", (x, y, z))
    machine_cur.execute("INSERT INTO machines VALUES (?, ?, ?, ?)",(x, y, z, machine_speed))
    machine_cur.close()
    machine_con.commit()
    machine_con.close()

#Called by app.route function to modify database table.    
def add_hub_data(x, y, z, hub_circuit, hub_range, hub_stop, hub_time):
    hub_con = lite.connect('hub_database.db')
    hub_cur = hub_con.cursor()
    hub_cur.execute("CREATE TABLE IF NOT EXISTS hubs(x FLOAT, y FLOAT, z FLOAT, circuit INTEGER, range INTEGER, stop INTEGER, time INTEGER)")
    hub_cur.execute("DELETE FROM hubs WHERE x = (?) AND y = (?) AND z = (?)", (x, y, z))
    hub_cur.execute("INSERT INTO hubs VALUES (?, ?, ?, ?, ?, ?, ?)",(x, y, z, hub_circuit, hub_range, hub_stop, hub_time))
    hub_cur.close()
    hub_con.commit()
    hub_con.close()

#Called by app.route function to modify database table. 
def add_paint_data(block, red, green, blue):
    paint_con = lite.connect('paint_database.db')
    paint_cur = paint_con.cursor()
    paint_cur.execute("CREATE TABLE IF NOT EXISTS paint(block TEXT, red FLOAT, green FLOAT, blue FLOAT)")
    paint_cur.execute("DELETE FROM paint WHERE block = (?)",(block,))
    paint_cur.execute("INSERT INTO paint VALUES (?, ?, ?, ?)",(block, red, green, blue))
    paint_cur.close()
    paint_con.commit()
    paint_con.close()

#Called by app.route function to modify database table. 
def delete_block_data():
    if server_var.block_thread_1_busy == False:
        server_var.block_thread_2_busy = True
        server_var.block_time = 0
        block_con = lite.connect('block_database.db')
        block_cur = block_con.cursor()
        block_cur.execute("CREATE TABLE IF NOT EXISTS blocks(destroy INTEGER, block TEXT, x FLOAT, y FLOAT, z FLOAT, rx FLOAT, ry FLOAT, rz FLOAT, rw FLOAT)")
        block_cur.execute("DELETE FROM blocks")
        block_cur.close()
        block_con.commit()
        block_con.close()
        server_var.block_thread_2_busy = False
        

#Database resource.             
class Chat(Resource):
    def get(self):
        chat_engine = create_engine('sqlite:///chat_database.db', connect_args={'timeout': 15})
        conn = chat_engine.connect()
        query = conn.execute("SELECT * FROM chat")
        return {'chat': query.cursor.fetchall()}

#Database resource.    
class Players(Resource):
    def get(self):
        player_engine = create_engine('sqlite:///player_database.db', connect_args={'timeout': 15})
        conn = player_engine.connect()
        query = conn.execute("SELECT * FROM players")
        return {'players': query.cursor.fetchall()}

#Database resource.   
class Blocks(Resource):
    def get(self):
        block_engine = create_engine('sqlite:///block_database.db', connect_args={'timeout': 15})
        conn = block_engine.connect()
        query = conn.execute("SELECT * FROM blocks")
        return {'blocks': query.cursor.fetchall()}

#Database resource.    
class Storage(Resource):
    def get(self):
        storage_engine = create_engine('sqlite:///storage_database.db', connect_args={'timeout': 15})
        conn = storage_engine.connect()
        query = conn.execute("SELECT * FROM storage")
        return {'storage': query.cursor.fetchall()}

#Database resource.   
class Conduits(Resource):
    def get(self):
        conduit_engine = create_engine('sqlite:///conduit_database.db', connect_args={'timeout': 15})
        conn = conduit_engine.connect()
        query = conn.execute("SELECT * FROM conduits")
        return {'conduits': query.cursor.fetchall()}
 
#Database resource.   
class Power(Resource):
    def get(self):
        power_engine = create_engine('sqlite:///power_database.db', connect_args={'timeout': 15})
        conn = power_engine.connect()
        query = conn.execute("SELECT * FROM power")
        return {'power': query.cursor.fetchall()}

#Database resource.
class Machines(Resource):
    def get(self):
        machine_engine = create_engine('sqlite:///machine_database.db', connect_args={'timeout': 15})
        conn = machine_engine.connect()
        query = conn.execute("SELECT * FROM machines")
        return {'machines': query.cursor.fetchall()}

#Database resource.    
class Hubs(Resource):
    def get(self):
        hub_engine = create_engine('sqlite:///hub_database.db', connect_args={'timeout': 15})
        conn = hub_engine.connect()
        query = conn.execute("SELECT * FROM hubs")
        return {'hubs': query.cursor.fetchall()}

#Database resource.
class Paint(Resource):
    def get(self):
        paint_engine = create_engine('sqlite:///paint_database.db', connect_args={'timeout': 15})
        conn = paint_engine.connect()
        query = conn.execute("SELECT * FROM paint")
        return {'paint': query.cursor.fetchall()}

#Gets the LAN address.
def get_local_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

#Gets the external IP address.
def get_external_address():
    return requests.get('https://api.ipify.org').text

#Checks whether or not the server is running.
def check_status():
    server_log("Checking status...")
    time.sleep(3)
    url = "http://localhost:5000/players"
    try:
        response = urllib.urlopen(url).read()
        if response != None:     
            server_log("Server is running...")
    except:
        server_log("Server failed to start!")

#If no blocks are placed for 30 seconds, the block database is cleared.
def await_blocks():
    while True:
        server_var.block_time = server_var.block_time + 1
        if server_var.block_time > 30:
            delete_block_data()
        time.sleep(1) 
    

#Adds resources and starts the server.
def start_server(): 
    global app
    global api
    api.add_resource(Players, '/players')
    api.add_resource(Blocks, '/blocks')
    api.add_resource(Storage, '/storage')
    api.add_resource(Conduits, '/conduits')
    api.add_resource(Power, '/power')
    api.add_resource(Machines, '/machines')
    api.add_resource(Hubs, '/hubs')
    api.add_resource(Chat, '/chat')
    api.add_resource(Paint, '/paint')
    server_log("LAN: "+str(server_var.local))
    server_log("Headless: "+str(server_var.headless))
    server_log("Development: "+str(server_var.devel))
    server_log("Starting server...")
    check_status_thread = threading.Thread(target = check_status)
    block_thread = threading.Thread(target = await_blocks)
    check_status_thread.daemon = False
    block_thread.daemon = False
    check_status_thread.start()   
    block_thread.start()
    serve(app, host='0.0.0.0', port=5000, threads=512)

#Creates the database tables and calls the start server function.
def setup_server():
    create_database()
    start_server()

#Starts the server thread.
def start():
    server = threading.Thread(target=setup_server)
    server.daemon = not server_var.headless
    server.start()

#Prints log messages to the scrolled text window.
def server_log(text):
    global window
    if window != None:
        if window.winfo_exists():
            logtxt.insert(INSERT,"\n"+text)
            logtxt.see("end")
    print (text)

#Starts the program.
def init():
    global window
    global logtxt
    
    for i in sys.argv[1:]:
        if str(i) == "headless":
            server_var.headless = True
        if str(i) == "local":
            server_var.local = True
        if str(i) == "devel":
            server_var.devel = True
            
    if server_var.headless == False:
        window = Tkinter.Tk()
        window.config(background="black")
        window.title("QE Server")
        window.geometry('%dx%d' % (640,480))
        logtxt = ScrolledText.ScrolledText(window, width=88, height=32)
        logtxt.configure(font=("Arial Bold", 8), fg="white")
        logtxt.configure(background='black')
        logtxt.place(bordermode=INSIDE, rely=0, relx=0)    
        stop_btn = Button(window, text="STOP", font=("Arial Bold", 10), bg="gray", fg="black", highlightbackground = "black", command=stop)
        stop_btn.pack()
        stop_btn.place(relx=0.4,rely=0.9)
        start()
        window.mainloop()
    else:
        start()
    
if __name__ == "__main__":
    init()
    