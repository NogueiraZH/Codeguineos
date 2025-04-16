import json
import struct
from typing import List

from canlib import canlib, Frame

def converteFloat(pacote):
    pacote_convertido = bytes(pacote)
    b = pacote_convertido[4:8]
    float_final = struct.unpack('>f', b)
    f = float_final[0]
    return f

def message_filter(code, mask): #Cria filtros de mensagens para que apenas mensagens específicas sejam processadas.
    msg_filter = canlib.objbuf.MessageFilter(code=code, mask=mask)
    return msg_filter

def group_list(list_origin:List[int], list_append ):
    if list_append is not None:
        for i in range(len(list_append)):
            list_origin.append(list_append[i])
        return list_origin
    else:
        return list_origin

def create_frame(channel, can_id, dlc, data:List[int], padding): #Cria um frame CAN com um ID específico, comprimento de dados (DLC), e a sequência de dados
    if len(data) == 8:
        frame = Frame(id_=can_id, dlc=dlc, data=data, flags=canlib.MessageFlag.EXT)
        channel.write(frame)
    elif len(data) < 8:
        data.insert(0, len(data))
        for i in range((8 - len(data))):
            data.append(padding)
        frame = Frame(id_=can_id, dlc=dlc, data=data, flags=canlib.MessageFlag.EXT)
        channel.write(frame)
    else:
        print("Pacote de dados não pode ultrapassar 7 bytes!!!")

def group_bytes(message:List[int]):
    resultado = 0x00
    x = (len(message) - 1)
    for i in range(len(message)):
        y = message[i]*(256**x)
        if y != 0x00:
            resultado += y
            x -= 1
        elif y == 0x00:
            resultado += message[i]
    return resultado

def convert_id(msg):
    can_id = msg.id
    byte0, byte1, byte2, byte3 = can_id.to_bytes(4, byteorder='big')
    invert_id = [byte0, byte1, byte3, byte2]
    return group_bytes(invert_id)

def montaPacoteDados(ch, pack_langth):
    pacote = [
        [], [], [], [], [], [], [], []
    ]

    i = 0
    while True:
        if i == pack_langth:
            return pacote
            break
        else:
            frame = ch.read(timeout=-1)
            data = [frame.data[0],frame.data[1],frame.data[2],frame.data[3],frame.data[4],frame.data[5],frame.data[6],frame.data[7]]
            pacote.insert(i, data)
            i += 1

def openjson(route, read):
    with open(f"{route}", 'r') as file:
        read_f = json.load(file)
        print(read_f)
    return read_f



