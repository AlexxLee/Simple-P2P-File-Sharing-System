import socket, sys, threading, json, time,optparse, os

def validate_ip(s):
    """
    Check if an input string is a valid IP address dot decimal format
    Inputs:
    - a: a string

    Output:
    - True or False
    """
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True

def validate_port(x):
    """
    Check if the port number is within range
    Inputs:
    - x: port number

    Output:
    - True or False
    """
    if not x.isdigit():
        return False
    i = int(x)
    if i < 0 or i > 65535:
            return False
    return True

class Tracker(threading.Thread):
    def __init__(self, port, host='0.0.0.0'):
        threading.Thread.__init__(self)
        self.port = port #port used by tracker
        self.host = host #tracker's IP address
        self.BUFFER_SIZE = 8192
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket to accept connections from peers

         # Track (ip, port, exp time) for each peer using a dictionary
         # You can optionally use (ip,port,stime) as key
         # {'ip':{'port':,'stime':}}
        self.users = {}

        # Track (ip, port, modified time) for each file
        # Only the most recent modified time and the respective peer are store
        # {'filename':{'ip':,'port':,'mtime':}}
        self.files = {}

        self.lock = threading.Lock()
        try:
            #YOUR CODE
            #Bind to address and port
            self.server.bind((self.host, self.port))
        except socket.error:
            print(('Bind failed %s' % (socket.error)))
            sys.exit()

        #YOUR CODE
        #listen for connections
        self.server.listen(5)

    def check_user(self):
        #Check if the peers are alive or not
        """Steps:
            1. check if a peer has expired or not
            2. if expired, remove items self.users and self.files ()
            [Pay attention to race conditions (Hint: use self.lock)]
        """
        #YOUR CODE
        self.lock.acquire()
        ct = int(time.time())
        for p in self.users:
            if ct - self.users[p]['stime'] >= 180:
                for f in self.files:
                    if self.files[f]['ip'] == p:
                        self.files.pop(f)
                self.users.pop(p)
        self.lock.release()



        #schedule the method to be called periodically
        t = threading.Timer(20, self.check_user)
        t.start()

   #Ensure sockets are closed on disconnect (This function is Not used)
    def exit(self):
        self.server.close()

    def run(self):
        # start the timer to check if peers are alive or not
        t = threading.Timer(20, self.check_user)
        t.start()

        print(('Waiting for connections on port %s' % (self.port)))
        while True:
            #accept incoming connection
            conn, addr = self.server.accept()#YOUR CODE

            #process the message from a peer
            threading.Thread(target=self.process_messages, args=(conn, addr)).start()


    def process_messages(self, conn, addr):
        conn.settimeout(180.0)
        print(('Client connected with ' + addr[0] + ':' + str(addr[1])))

        while True:
            #receiving data from a peer
            data = ''
            while True:
                part = conn.recv(self.BUFFER_SIZE).decode()
                data = data + part
                if len(part) < self.BUFFER_SIZE:
                    break

            # Check if the received data is a json string of the anticipated format. If not, ignore.
            #YOUR CODE
            #try and exception

            #deserialize
            try:
                data_dic = json.loads(data)

                """
                1) Update self.users and self.files if nessesary
                2) Send directory response message
                Steps:1. Check message type (initial or keepalive). See Table I in description.
                    2. If this is an initial message from a peer and the peer is not in self.users, create the corresponding entry in self.users
                    2. If this is a  keepalive message, update the expire time with the respective peer
                    3. For an intial message, check the list of files. Create a new entry in user.files if one does not exist,
                    or, update the last modifed time to the most recent one
                    4. Pay attention to race conditions (Hint: use self.lock)
                """
                # YOUR CODE
                # Dictionary Format
                # self.user = {'ip':{'port':,'stime':}}
                # self.files = {'filename':{'ip':,'port':,'mtime':}}
                # initial_message = {'port':, 'files':[{'name':, 'mtime':}]}
                # keep-alive_message = {'port':}
                # response_message = {'filename':{'ip':, 'port':, 'mtime':}}

                
                self.lock.acquire()
                # check if the message from a peer is an initial message (len>1 -> initial)
                if len(data_dic) > 1:
                    # The user sending the initial message is already in self.user -> error
                    if (str(addr[0]) in self.users) and (str(addr[1]) == self.users[str(addr[0])]['port']):
                        print('Initial message only need to be sent once.')
                    # initial message
                    else:
                        ct = int(time.time())
                        self.users[str(addr[0])] = {'port': data_dic['port'], 'stime': ct}
                        # run for each file in the initial message
                        for f in data_dic['files']:
                            # check if the file is already in the self.files
                            if f['name'] in self.files:
                                filename = f['name']
                                self.files[filename]['ip'] = str(addr[0])
                                self.files[filename]['port'] = data_dic['port']
                                # compare the modified times between the file in the message and the one in self.files
                                if round(f['mtime']) > round(self.files[filename]['mtime']):
                                    self.files[filename]['mtime'] = round(f['mtime'])
                            # the file in the initial message is new
                            else:
                                filename = f['name']
                                self.files[filename] = {'ip': str(addr[0]), 'port': data_dic['port'], 'mtime': round(f['mtime'])}
                        msg = json.dumps(self.files)
                        print(msg)
                        conn.send(bytes(msg, "utf-8"))
                # it is a keep-alive message
                else:
                    # check if the user is in self.users (it should be)
                    if str(addr[0]) in self.users:
                        ct = int(time.time())
                        self.users[str(addr[0])]['port'] = data_dic['port']
                        self.users[str(addr[0])]['stime'] = ct
                        msg = json.dumps(self.files)
                        print(msg)
                        conn.send(bytes(msg, "utf-8"))
                    # The user who is not in self.user is sending a keep-alive message -> error
                    else:
                        print('Error: can not find user')
                self.lock.release()


            except ValueError:
                print('The format of JSON string is expected')

        conn.close() # Close

if __name__ == '__main__':
    parser = optparse.OptionParser(usage="%prog ServerIP SezrverPort")
    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error("No ServerIP and ServerPort")
    elif len(args) < 2:
        parser.error("No  ServerIP or ServerPort")
    else:
        if validate_ip(args[0]) and validate_port(args[1]):
            server_ip = args[0]
            server_port = int(args[1])
        else:
            parser.error("Invalid ServerIP or ServerPort")
    tracker = Tracker(server_port,server_ip)
    tracker.start()
