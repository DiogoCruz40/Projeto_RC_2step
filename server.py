import socket
import threading
import os
import psycopg2.extras
from passlib.handlers.sha2_crypt import sha256_crypt
import re
import time
from datetime import datetime
import datetime

HEADER = 64
SERVER = socket.gethostbyname(socket.gethostname())
#SERVER = '192.168.1.70'
FORMAT = 'utf-8' 
DISCONNECT_MSG = '!DISCONNECT'



def send(msg, conn):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length)) #PADDING
    conn.send(send_length)
    conn.send(message)   


def read(conn, addr):      
    msg_length = conn.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)
    
        return msg
 
#===================================================HEALTH PROFESSIONAL========================================================#


def handle_professional(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True
    send('Health Professional CONNECTED', conn)
    while connected:

        try:
            opt = read(conn, addr)
            if opt == '1':
                mail = loginverifyprofessional(conn, addr)
                if mail == 'notlogin':
                    continue
                onloginprofessional(conn,addr,mail)
            elif opt == '2':
                signupverifyprofessional(conn, addr)
            elif opt == '3':
                connected = False      

        except Exception as e:
            print(e)
   
    conn.close()

#======================For Login==========================================================#
def loginverifyprofessional(conn, addr):
   
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    while 1:
        mail = read(conn, addr) #1
        cur.execute("SELECT pass FROM profissional_de_saude WHERE email_p=%s and validated=TRUE",(mail,))
        if cur.rowcount == 1:
            send('Mail True',conn) #2
            password = cur.fetchone()[0]
            password_login = read(conn,addr) #3
            verifypass=sha256_crypt.verify(password_login, password)
            if verifypass:
                send('True', conn) #4

                cur.execute("SELECT nome_p FROM profissional_de_saude WHERE email_p=%s and validated=TRUE",(mail,))
                send(cur.fetchone()[0],conn) #5
                break
            else:
                send('False', conn) #4
                if read(conn,addr) == 'Try again Pass True':
                    continue
                else:
                    connDB.close()
                    cur.close()
                    return 'notlogin'
        else:
            send('Mail False', conn) #2
            if read(conn,addr) == 'Try again Mail True':
                continue
            else:
                connDB.close()
                cur.close()
                return 'notlogin'
    
    connDB.close()
    cur.close()
    return mail

def onloginprofessional(conn,addr,mail):
    login = True
    while login:
        try:
            opt = read(conn, addr)
            if opt == '1':
                opt2 = read(conn, addr)
                if opt2 == '1':
                    occurencemenu(conn, addr, mail)
                elif opt2 == '2': 
                    login = True
            elif opt == '2':
                mail = changeprofileprofessional(conn,addr,mail)
            elif opt == '3':
                delete = eraseaccountprofessional(conn,addr,mail)
                if delete == True:
                    login = False
            elif opt == '4':
                login = False      

        except Exception as e:
            print(e)      
    return

#======================Occurence Register==========================================================#

def occurencemenu(conn,addr,mail):
    occurence = True
    sendoccurence = False
    while occurence:   
        try:
            opt = read(conn, addr)
            if opt == '1':
                date = read(conn,addr)
            elif opt == '2':
                time_string = read(conn,addr)
            elif opt == '3':
                local = read(conn,addr)
            elif opt == '4':

                opt2 = read(conn,addr)
                if opt2 == '1':
                    description = read(conn,addr)
                elif opt2 == '2':
                    description = read(conn,addr) 
            elif opt == '5':
                opt2 = read(conn, addr)
                if opt2 == '1':
                    send('True', conn)
                    email = 'anonymous@anonymous.pt'                 
                elif opt2 == '2':
                    send('True', conn) 
                    email = mail  
                try:
                    if read(conn,addr) == 'True': 
                        opt2 = read(conn, addr)
                        if opt2 == '1':
                            sendoccurence = read(conn,addr)
                            if sendoccurence == 'True':
                                state = occurenceregister(conn,addr,email,date,time_string,local,description)
                                if state == True:
                                    occurence = False
                                    break
                                else:
                                    occurence = False
                                    continue
                            else:
                                continue            
                        elif opt2 == '2':            
                            continue                 
                    else: 
                        continue
                except:
                    print("Erro :(")                    
            elif opt == '6':
                occurence = False
        except Exception as e:
            print(e)

def occurenceregister(conn,addr,mail,date,time_string,local,description):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    occurence = True
    while occurence:
        cur.execute("SELECT id FROM profissional_de_saude WHERE email_p=%s",(mail,)) 
        id_p = cur.fetchone()[0]
        if id_p == None:
            state = False
        else:
            try:
                cur.execute("INSERT INTO ocorrencias(data,hora,localidade,descricao,profissional_de_saude_id) VALUES (%s,%s,%s,%s,%s)",(date,time_string,local,description,id_p)) 
                connDB.commit()
                state = True
                occurence = False
            except Exception as e:
                print(e)
                state = False
                occurence = False
                connDB.rollback()    
            break

    return state

#======================Change Profile==========================================================#

def changeprofileprofessional(conn,addr,mail):
    changeprofile = True
    while changeprofile:
        try:
            opt = read(conn, addr)
            if opt == '1':
                mail = changemailprofessional(conn,addr,mail)
            elif opt == '2':
                changepasswordprofessional(conn,addr,mail)
            elif opt == '3':
                changenameprofessional(conn,addr,mail)
            elif opt == '4':
                changeprofile = False      

        except Exception as e:
            print(e)
    return mail

def changemailprofessional(conn,addr,mail):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    changeemailprofessional = True
    while changeemailprofessional:
        password_login=read(conn,addr)
        cur.execute("SELECT pass FROM profissional_de_saude WHERE email_p=%s",(mail,))
        password = cur.fetchone()[0]
        verifypass=sha256_crypt.verify(password_login, password)
        if verifypass:
            send('True Password', conn)
            while 1:
                newmail = read(conn, addr)
                cur.execute("SELECT * FROM profissional_de_saude WHERE email_p=%s",(newmail,))
                if cur.rowcount != 0:
                    send('already exists',conn)
                    if read(conn, addr) == 'Try again Mail True':
                        continue
                    else:
                        connDB.close()
                        cur.close()
                        return mail
                else:
                    send('Mail Change',conn)
                    if read(conn, addr) == 'Mail Change True':
                        cur.execute("Update profissional_de_saude set email_p=%s where email_p=%s",(newmail,mail))
                        connDB.commit()
                        changeemailprofessional = False
                        break
                    else:
                        connDB.close()
                        cur.close()
                        return mail
        else:
            send('False Password', conn)
            if read(conn, addr) == 'Try again Pass True':
                continue
            else:
                connDB.close()
                cur.close()
                return mail
    
    connDB.close()
    cur.close()
    return newmail

def changepasswordprofessional(conn,addr,mail):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)

    while 1:
        password_login=read(conn,addr)
        cur.execute("SELECT pass FROM profissional_de_saude WHERE email_p=%s",(mail,))
        password = cur.fetchone()[0]
        verifypass=sha256_crypt.verify(password_login, password)
        if verifypass:
            send('True Password', conn)
            newpassword=read(conn, addr)
            if read(conn, addr) == 'Pass Change True':
                cur.execute("Update profissional_de_saude set pass=%s where email_p=%s",(newpassword,mail))
                connDB.commit()
            break
        else:
            send('False Password', conn)
            if read(conn, addr) == 'Try again Pass True':
                continue
            else:
                break
            
    connDB.close()
    cur.close()
    return

def changenameprofessional(conn,addr,mail):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)

    while 1:
        password_login=read(conn,addr)
        cur.execute("SELECT pass FROM profissional_de_saude WHERE email_p=%s",(mail,))
        password = cur.fetchone()[0]
        verifypass=sha256_crypt.verify(password_login, password)
        if verifypass:
            send('True Password', conn)
            newname=read(conn, addr)
            if read(conn, addr) == 'Name Change True':
                cur.execute("Update profissional_de_saude set nome_p=%s where email_p=%s",(newname,mail))
                connDB.commit()
            break
        else:
            send('False Password', conn)
            if read(conn, addr) == 'Try again Pass True':
                continue
            else:
                break

    connDB.close()
    cur.close()
    return 

def eraseaccountprofessional(conn,addr,mail):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    delete = False

    while 1:
        password_login=read(conn,addr)
        cur.execute("SELECT pass FROM profissional_de_saude WHERE email_p=%s",(mail,))
        password = cur.fetchone()[0]
        verifypass=sha256_crypt.verify(password_login, password)
        if verifypass:
            send('True Password', conn)
            deleteconfirm=read(conn, addr)
            if deleteconfirm == 'y':
                cur.execute('SELECT id FROM profissional_de_saude where email_p=%s',(mail,))
                id_profissional = cur.fetchone()[0]
                cur.execute("DELETE FROM ocorrencias where profissional_de_saude_id=%s",(id_profissional,))
                connDB.commit()
                cur.execute("DELETE FROM profissional_de_saude where email_p=%s",(mail,))
                connDB.commit()
                delete = True
            break
                
        else:
            send('False Password', conn) 
            if read(conn, addr) == 'Try again Pass True':
                continue
            else:
                break
       
    connDB.close()
    cur.close()

    if delete == True:
        return True
    else:
        return False
#======================For Signup==========================================================#
def signupverifyprofessional(conn, addr):
    
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)

    name=read(conn,addr)

    while 1:
        mail = read(conn, addr) #1
        cur.execute("SELECT email_p FROM profissional_de_saude WHERE email_p=%s",(mail,))
        if cur.rowcount != 0:
            send('already exists',conn) #2
            if read(conn, addr) == 'Try again Mail True':
                continue
            else:
                break
        else:
            cur.execute("SELECT email_a FROM agente_seguranca WHERE email_a=%s",(mail,))
            if cur.rowcount != 0:
                send('already exists',conn)
                if read(conn, addr) == 'Try again Mail True':
                    continue
                else:
                    break
            else:
                cur.execute("Select email_g FROM gestor_sistema WHERE email_g=%s",(mail,))
                if cur.rowcount != 0:
                    send('already exists',conn)
                    if read(conn, addr) == 'Try again Mail True':
                        continue
                    else:
                        break
                else:
                    send('doesnt exist',conn) #2
                    password = read(conn,addr) #3
                    if read(conn,addr) == 'Confirm True':
                        cur.execute("INSERT INTO profissional_de_saude(nome_p,email_p,pass) VALUES (%s,%s,%s)",(name,mail,password))
                        connDB.commit()
                    break

    connDB.close()
    cur.close()
    return

#=======================================================SYSTEM MANAGER===========================================================#

def handle_manager(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True
    send('System Manager CONNECTED', conn)
    while connected:

        try:
            opt = read(conn, addr)
            if opt == '1':
                if not loginverifymanager(conn, addr):
                     continue
                onloginmanager(conn, addr)
            elif opt == '2':
                connected = False      

        except Exception as e:
            print(e)
   
    conn.close()

def VerifyPassLogin(cur, passe, email):
    cur.execute("SELECT * FROM gestor_sistema WHERE pass=crypt(%s,pass) and email_g=%s",
                (passe, email))
    if cur.rowcount == 0:
        return False
    else:
        return True

def loginverifymanager(conn, addr):
   
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    while 1:
        mail = read(conn, addr) #1
        cur.execute("SELECT * FROM gestor_sistema WHERE email_g=%s",(mail,))
        if cur.rowcount == 1:
            send('Mail True',conn) #2
            password_login = read(conn,addr) #3
            if VerifyPassLogin(cur, password_login, mail):
                send('True', conn) #4
                cur.execute("SELECT nome_g FROM gestor_sistema WHERE email_g=%s",(mail,))
                send(cur.fetchone()[0],conn) #5
                break
            else:
                send('False', conn) #4
                if read(conn,addr) == 'Try again Pass True':
                    continue
                else:
                    connDB.close()
                    cur.close()
                    return False
        else:
            send('Mail False', conn) #2
            if read(conn,addr) == 'Try again Mail True':
                continue
            else:
                connDB.close()
                cur.close()
                return False
    
    connDB.close()
    cur.close()
    return True

def onloginmanager(conn,addr):
    login = True
    while login:
        try:
            opt = read(conn, addr)
            if opt == '1':
                validateanaccountmanager(conn,addr)
            elif opt == '2':
                deleteanaccountmanager(conn,addr)
            elif opt == '3':
                login = False      

        except Exception as e:
            print(e)
    return

def validateanaccountmanager(conn,addr):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    while 1:
        cur.execute("Select nome_p,email_p,validated FROM profissional_de_saude where email_p!='anonymous@anonymous.pt'")
        send(str(cur.fetchall()),conn)
        cur.execute("Select nome_a,email_a,validated FROM agente_seguranca")
        send(str(cur.fetchall()),conn)
        mail = read(conn, addr) #1
        if mail == '0':
            connDB.close()
            cur.close()
            return
        cur.execute("SELECT * FROM profissional_de_saude WHERE email_p=%s and validated=FALSE",(mail,))
        if cur.rowcount != 0:
            send('Mail validate', conn)
            if read(conn, addr) == 'Mail Confirm True':
                cur.execute("UPDATE profissional_de_saude set validated=TRUE where email_p=%s",(mail,))
                connDB.commit()
            break
        else:
            cur.execute("SELECT * FROM agente_seguranca WHERE email_a=%s and validated=FALSE",(mail,))
            if cur.rowcount !=0:
                send('Mail validate', conn)
                if read(conn, addr) == 'Mail Confirm True':
                    cur.execute("UPDATE agente_seguranca set validated=TRUE where email_a=%s",(mail,))
                    connDB.commit()
                break
            else:
                send('Mail False',conn)
                continue
    connDB.close()
    cur.close()
    return


def deleteanaccountmanager(conn,addr):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    while 1:
        cur.execute("Select nome_p,email_p,validated FROM profissional_de_saude where email_p!='anonymous@anonymous.pt'")
        send(str(cur.fetchall()),conn)
        cur.execute("Select nome_a,email_a,validated FROM agente_seguranca")
        send(str(cur.fetchall()),conn)
        mail = read(conn, addr) #1
        if mail == '0':
            connDB.close()
            cur.close()
            return
        
        cur.execute("SELECT * FROM profissional_de_saude WHERE email_p=%s and email_p!='anonymous@anonymous.pt'",(mail,))
        if cur.rowcount != 0: 
            send('Mail delete', conn)
            if read(conn, addr) == 'Mail Confirm True':
                cur.execute("DELETE FROM ocorrencias where profissional_de_saude_id=%s",(cur.fetchone()[0],))
                connDB.commit()
                cur.execute("Delete from profissional_de_saude where email_p=%s",(mail,))
                connDB.commit()
            break
        else:
            cur.execute("SELECT * FROM agente_seguranca WHERE email_a=%s",(mail,))
            if cur.rowcount !=0:
                send('Mail delete', conn)
                if read(conn, addr) == 'Mail Confirm True':
                    
                    cur.execute("Delete from agente_seguranca where email_a=%s",(mail,))
                    connDB.commit()
                break
            else:
                send('Mail False',conn)
                continue
    connDB.close()
    cur.close()
    return            
#===========================================================SECURITY OFFICER======================================================#


def handle_security(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True
    send('Security Officer CONNECTED', conn)
    while connected:

        try:
            opt = read(conn, addr)
            if opt == '1':
                mail = loginverifysecurity(conn, addr)
                if mail == 'notlogin':
                    continue
                onloginsecurity(conn,addr,mail)
            elif opt == '2':
                signupverifysecurity(conn, addr)
            elif opt == '3':
                connected = False      

        except Exception as e:
            print(e)
   
    conn.close()

#======================For Login==========================================================#
def loginverifysecurity(conn, addr):
   
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    while 1:
        mail = read(conn, addr) #1
        cur.execute("SELECT pass FROM agente_seguranca WHERE email_a=%s and validated=TRUE",(mail,))
        if cur.rowcount == 1:
            send('Mail True',conn) #2
            password = cur.fetchone()[0]
            password_login = read(conn,addr) #3
            verifypass=sha256_crypt.verify(password_login, password)
            if verifypass:
                send('True', conn) #4

                cur.execute("SELECT nome_a FROM agente_seguranca WHERE email_a=%s and validated=TRUE",(mail,))
                send(cur.fetchone()[0],conn) #5
                break
            else:
                send('False', conn) #4
                if read(conn,addr) == 'Try again Pass True':
                    continue
                else:
                    connDB.close()
                    cur.close()
                    return 'notlogin'
        else:
            send('Mail False', conn) #2
            if read(conn,addr) == 'Try again Mail True':
                continue
            else:
                connDB.close()
                cur.close()
                return 'notlogin'
    
    connDB.close()
    cur.close()
    return mail

def onloginsecurity(conn,addr,mail):
    login = True
    while login:
        try:
            opt = read(conn, addr) #1
            if opt == '1':    
                occurenceview(conn,addr,mail,True,False,False,False,False)
                while 1:
                    opt2 = read(conn,addr)
                    if opt2 == '1':
                        occurenceview(conn,addr,mail,False,True,False,False,False)
                        break
                    elif opt2 == '2':
                        occurenceview(conn,addr,mail,False,False,True,False,False)
                        break
                    elif opt2 == '3':
                        occurenceview(conn,addr,mail,False,False,False,True,False)
                        break
                    elif opt2 == '4':
                        occurenceview(conn,addr,mail,False,False,False,False,True)
                        break
                    elif opt2 == '5':
                        break
            elif opt == '2':
                mail = changeprofilesecurity(conn,addr,mail)
            elif opt == '3':
                delete = eraseaccountsecurity(conn,addr,mail)
                if delete == True:
                    login = False
            elif opt == '4':
                login = False      

        except Exception as e:
            print(e)
    return

def occurenceview(conn,addr,mail, all_selected, word,date, location,id_cl):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    datatoview = True   

    title=['Id_ocorrencia', 'Data', 'Hora', 'Localidade', 'Descrição', 'Id_utilizador', 'Nome de Utilizador']
    
    try:
        if word == True:
            count = 0
            client_word = read(conn, addr)  #2
            cur.execute("SELECT descricao FROM ocorrencias")
            for row in cur.fetchall():
                descricao, = row
                if re.search(client_word.lower(), descricao.lower()):
                    count = count + 1
            nrofoccurences = count
        
        elif all_selected == True:
            cur.execute("SELECT COUNT(*) FROM ocorrencias ")
            nrofoccurences, = cur.fetchone()  

        elif date == True:
            client_date = read(conn, addr)
            datetime.datetime.strptime(client_date, "%Y-%m-%d")
            cur.execute("SELECT COUNT(*) FROM ocorrencias WHERE data = %s",[client_date])
            nrofoccurences, = cur.fetchone()        
        
        elif location == True:
            count = 0
            client_location = read(conn, addr)
            cur.execute("SELECT localidade FROM ocorrencias")
            for row in cur.fetchall():
                localidade, = row
                if re.search(client_location.lower(), localidade.lower()):
                    count = count + 1
            nrofoccurences = count
    
        elif id_cl == True:
            client_id = read(conn, addr)
            cur.execute("SELECT COUNT(*) FROM ocorrencias WHERE profissional_de_saude_id = %s",[client_id])
            nrofoccurences, = cur.fetchone()

        send(str(nrofoccurences), conn)   #1   --  #3
        read(conn, addr)    #2
       

    except Exception as e:
        print(e)

    if nrofoccurences == 0:
        return
    
    else:
        send('TitleStart', conn)   #3
        while read(conn, addr) != 'Ready': #4
            continue
        for x in title:
            send(x, conn)   #5
            read(conn, addr)  #6
        send('Stop',conn)    #7
       
        while read(conn, addr) != 'Ready':   #8
            continue
        send('Start', conn)   #9
    
        if word == True:    
            cur.execute("SELECT * FROM ocorrencias")
            for row in cur.fetchall():
                Id,Data,Hora,Local,descricao,Id_ut = row
                if re.search(client_word.lower(), descricao.lower()):
                    cur.execute("SELECT nome_p FROM profissional_de_saude WHERE id = %s",str(Id_ut),)
                    user_name, = cur.fetchone()
                    elements = str(str(Id) + ',' + str(Data)+ ',' + str(Hora)+ ',' 
                    + str(Local)+ ',' + str(descricao)+ ',' + str(Id_ut)+ ',' + str(user_name))
                    send(elements,conn)
                    read(conn, addr)
            send('True', conn)

        if location == True:   
            cur.execute("SELECT * FROM ocorrencias")
            for row in cur.fetchall():
                Id,Data,Hora,Local,descricao,Id_ut = row
                if re.search(client_location.lower(), Local.lower()):
                    cur.execute("SELECT nome_p FROM profissional_de_saude WHERE id = %s",str(Id_ut),)
                    user_name, = cur.fetchone()
                    elements = str(str(Id) + ',' + str(Data)+ ',' + str(Hora)+ ',' 
                    + str(Local)+ ',' + str(descricao)+ ',' + str(Id_ut)+ ',' + str(user_name))
                    send(elements,conn)
                    read(conn, addr)
            send('True', conn)


        else:
            if all_selected == True:
                cur.execute("SELECT * FROM ocorrencias ")

            elif date == True:
                cur.execute("SELECT * FROM ocorrencias WHERE data = %s",[client_date])

            #elif location == True:
            #    cur.execute("SELECT * FROM ocorrencias WHERE localidade = %s",[client_location])
            
            elif id_cl == True:
                cur.execute("SELECT * FROM ocorrencias WHERE profissional_de_saude_id = %s",[client_id])
            
            for row in cur.fetchall():
                Id,Data,Hora,Local,descricao,Id_ut = row
                cur.execute("SELECT nome_p FROM profissional_de_saude WHERE id = %s",str(Id_ut),)
                user_name, = cur.fetchone()
                elements = str(str(Id) + ',' + str(Data)+ ',' + str(Hora)+ ',' 
                + str(Local)+ ',' + str(descricao)+ ',' + str(Id_ut)+ ',' + str(user_name))
                send(elements,conn)
                read(conn, addr)
            send('True', conn)  

def changeprofilesecurity(conn,addr,mail):
    changeprofile = True
    while changeprofile:
        try:
            opt = read(conn, addr)
            if opt == '1':
                mail = changemailsecurity(conn,addr,mail)
            elif opt == '2':
                changepasswordsecurity(conn,addr,mail)
            elif opt == '3':
                changenamesecurity(conn,addr,mail)
            elif opt == '4':
                changeprofile = False      

        except Exception as e:
            print(e)
    return mail

def changemailsecurity(conn,addr,mail):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    changeemailsecurity = True
    while changeemailsecurity:
        password_login=read(conn,addr)
        cur.execute("SELECT pass FROM agente_seguranca WHERE email_a=%s",(mail,))
        password = cur.fetchone()[0]
        verifypass=sha256_crypt.verify(password_login, password)
        if verifypass:
            send('True Password', conn)
            while 1:
                newmail = read(conn, addr)
                cur.execute("SELECT * FROM agente_seguranca WHERE email_a=%s",(newmail,))
                if cur.rowcount != 0:
                    send('already exists',conn)
                    if read(conn, addr) == 'Try again Mail True':
                        continue
                    else:
                        connDB.close()
                        cur.close()
                        return mail
                else:
                    send('Mail Change',conn)
                    if read(conn, addr) == 'Mail Change True':
                        cur.execute("Update agente_seguranca set email_a=%s where email_a=%s",(newmail,mail))
                        connDB.commit()
                        changeemailsecurity = False
                        break
                    else:
                        connDB.close()
                        cur.close()
                        return mail
        else:
            send('False Password', conn)
            if read(conn, addr) == 'Try again Pass True':
                continue
            else:
                connDB.close()
                cur.close()
                return mail
    
    connDB.close()
    cur.close()
    return newmail

def changepasswordsecurity(conn,addr,mail):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)

    while 1:
        password_login=read(conn,addr)
        cur.execute("SELECT pass FROM agente_seguranca WHERE email_a=%s",(mail,))
        password = cur.fetchone()[0]
        verifypass=sha256_crypt.verify(password_login, password)
        if verifypass:
            send('True Password', conn)
            newpassword=read(conn, addr)
            if read(conn, addr) == 'Pass Change True':
                cur.execute("Update agente_seguranca set pass=%s where email_a=%s",(newpassword,mail))
                connDB.commit()
            break
        else:
            send('False Password', conn)
            if read(conn, addr) == 'Try again Pass True':
                continue
            else:
                break
            
    connDB.close()
    cur.close()
    return

def changenamesecurity(conn,addr,mail):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)

    while 1:
        password_login=read(conn,addr)
        cur.execute("SELECT pass FROM agente_seguranca WHERE email_a=%s",(mail,))
        password = cur.fetchone()[0]
        verifypass=sha256_crypt.verify(password_login, password)
        if verifypass:
            send('True Password', conn)
            newname=read(conn, addr)
            if read(conn, addr) == 'Name Change True':
                cur.execute("Update agente_seguranca set nome_a=%s where email_a=%s",(newname,mail))
                connDB.commit()
            break
        else:
            send('False Password', conn)
            if read(conn, addr) == 'Try again Pass True':
                continue
            else:
                break

    connDB.close()
    cur.close()
    return 

def eraseaccountsecurity(conn,addr,mail):
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)
    delete = False

    while 1:
        password_login=read(conn,addr)
        cur.execute("SELECT pass FROM agente_seguranca WHERE email_a=%s",(mail,))
        password = cur.fetchone()[0]
        verifypass=sha256_crypt.verify(password_login, password)
        if verifypass:
            send('True Password', conn)
            deleteconfirm=read(conn, addr)
            if deleteconfirm == 'y':
                cur.execute("DELETE FROM agente_seguranca where email_a=%s",(mail,))
                connDB.commit()
                delete = True
            break
                
        else:
            send('False Password', conn) 
            if read(conn, addr) == 'Try again Pass True':
                continue
            else:
                break
       
    connDB.close()
    cur.close()

    if delete == True:
        return True
    else:
        return False      

#======================For Signup==========================================================#

def signupverifysecurity(conn, addr):
    
    connDB = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = connDB.cursor(cursor_factory=psycopg2.extras.DictCursor)

    name=read(conn,addr)

    while 1:
        mail = read(conn, addr) #1
        cur.execute("SELECT email_a FROM agente_seguranca WHERE email_a=%s",(mail,))
        if cur.rowcount != 0:
            send('already exists',conn) #2
            if read(conn, addr) == 'Try again Mail True':
                continue
            else:
                break
        else:
            cur.execute("SELECT email_p FROM profissional_de_saude WHERE email_p=%s",(mail,))
            if cur.rowcount != 0:
                send('already exists',conn)
                if read(conn, addr) == 'Try again Mail True':
                    continue
                else:
                    break
            else:
                cur.execute("Select email_g FROM gestor_sistema WHERE email_g=%s",(mail,))
                if cur.rowcount != 0:
                    send('already exists',conn)
                    if read(conn, addr) == 'Try again Mail True':
                        continue
                    else:
                        break
                else:
                    send('doesnt exist',conn) #2
                    password = read(conn,addr) #3
                    if read(conn,addr) == 'Confirm True':
                        cur.execute("INSERT INTO agente_seguranca(nome_a,email_a, pass) VALUES (%s,%s,%s)",(name,mail,password))
                        connDB.commit()
                    break

    connDB.close()
    cur.close()
    return

#============================================================================================================================#
# IF doesn't start try:
#lsof -iTCP:8100 -sTCP:LISTEN
#lsof -iTCP:8200 -sTCP:LISTEN
#lsof -iTCP:8300 -sTCP:LISTEN

#kill -9 <Pid Number>

def start(PORT, SERVER):
    ADDR =  (SERVER, PORT)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f'[LISTENING] Server is listening on {SERVER}')
    while True:
        (conn,addr) = server.accept()
        if PORT == 8100:
            thread = threading.Thread(target=handle_professional, args=(conn, addr))
        elif PORT == 8200:
            thread = threading.Thread(target=handle_manager, args=(conn, addr))
        elif PORT == 8300:
            thread = threading.Thread(target=handle_security , args=(conn, addr))
        thread.start()
        
        if PORT==8100:
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1} of Health_Professionals")
        if PORT==8200:
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1} of System_Managers")
        if PORT==8300:
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1} of Security officers")


def main(SERVER):
    print("[STARTING] server is starting...")
    pid = os.fork()
    
    if pid == 0 :
        print('Health Professional')
        start(8100, SERVER)

    else:
        pid2 = os.fork()
        if pid2 == 0:
            print('System Manager')
            start(8200, SERVER)
    
        else:
            print('Security Officer')
            start(8300, SERVER)
       


if __name__ == "__main__":
    main(SERVER)