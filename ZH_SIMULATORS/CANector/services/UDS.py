import json
from inspect import Parameter
from mmap import error
from time import sleep
from typing import List, Dict, Any

from canlib.canlib import Channel
from services.Util import *

def ieee_convert(pacote):
    pacote_convertido = bytes(pacote)
    b = pacote_convertido[4:8]
    float_final = struct.unpack('>f', b)
    f = float_final[0]
    return f

def get_message(ch: Channel):
    msg = ch.read(timeout=-1)
    if msg:  # Verifica se nenhuma mensagem foi encontrada
        return msg
    return False


#---Recebe CAN ID de solicitação e retorna CAN ID de resposta
def convert_id(msg):
    can_id = msg.id
    byte0, byte1, byte2, byte3 = can_id.to_bytes(4, byteorder='big')
    if byte1 == 0xEC:
        byte1 -= 0x01
        break_id = [byte0, byte1, byte3, byte2]
        return group_bytes(break_id)
    elif byte1 == 0xEB:
        byte1 += 0x01
        break_id = [byte0, byte1, byte3, byte2]
        return group_bytes(break_id)
    elif byte1 == 0xDA:
        break_id = [byte0, byte1, byte3, byte2]
        return group_bytes(break_id)


#---Cria frame de pergunta para simulador
def response_frame(ch, can_id: int, sid, did, data, padding):
    try:
        frame_data=[]
        if sid is not None: frame_data: List[int] = [sid]
        if did is not None:frame_data = group_list(frame_data, did)
        if data is not None:frame_data = group_list(frame_data, data)
        create_frame(channel=ch, can_id=can_id, dlc=8, data=frame_data, padding=padding)
    except error:
        print(f"Error:{error} --- response_frame")


#---Cria frames de requisição para o tester
def request_frame(ch,can_id, sid:int, did, padding):
    try:
        frame_data: List[int] = [sid]
        frame_data = group_list(frame_data, did)
        create_frame(channel=ch, can_id=can_id, dlc=8, data=frame_data, padding=padding)
    except error:
        print(error)


def flow_timeout(ch:Channel, size:int):
    for i in range(size):
        ch.read(timeout=-1)
    return True


#---Cria o frame de tester presente
def tester_present(ch, can_id, padding):
    response_frame(
        ch=ch,
        can_id=can_id,
        sid=0x7E,
        did=None,
        data=None,
        padding=padding
    )


def receive_flow_data(channel:Channel, rx_id, message:Frame):
    try:
        flow_byte_len = message.data[1]
        flow_frame_len = (flow_byte_len // 7)
        flow_received_data = {"0x10":[byte for byte in message.data]}
        frame_counter = 0
        while frame_counter < flow_frame_len:
            msg = channel.read(timeout=2000)
            if msg.id == rx_id:
                if frame_counter < flow_frame_len:
                    flow_received_data.update({hex(msg.data[0]):[byte for byte in msg.data]})
                    frame_counter += 1
        return flow_received_data
    except Exception as e:
        print(f"Error:{e} --- receive_flow_data")
        return False

#---Manda o primeiro frame de um bloco de frames
def first_frame(ch,can_id, sid:int, did, message:List[int], consecutive_block:List[list[int]]):
    """ Realiza montagem do Primeiro frame de um multframe e faz o envio do
        mesmo na rede CAN passada pelo parametro ch"""
    try:
        pack_len = (len(consecutive_block) * 7) + (len(message) - 2)
        message[1] = pack_len
        message[2] = (sid+0x40)
        message[3] = did[0]
        if len(did) > 1: message[4] = did[1]
        response_frame(ch=ch,can_id=can_id,sid=None,did=None,data= message,padding=None)
        print(f'Enviando primeiro frame SID:{hex(sid)}  DID:{hex(did[0]), hex(did[1])}')
    except Exception as e:
        print(f"Error: {e}")

#---Escreve os frames consecutivos ao primeiro frame
def consecutive_frame(ch:Channel, can_id, msg, data:List[list[int]]):
    block_size = msg.data[1]
    st_min = msg.data[2]
    if st_min > 0x00: st_min = st_min*0.01
    if data is not None:
        if block_size == 0x00:
            for frame in data:
                sleep(st_min)
                response_frame(
                    ch=ch,
                    can_id=can_id,
                    sid=None,
                    did=None,
                    data=[frame[0], frame[1], frame[2], frame[3], frame[4], frame[5], frame[6], frame[7]],
                    padding=None)
        else:
            x = 0
            while True:
                if x == len(data):
                    break
                else:
                    for i in range(block_size):

                        response_frame(
                            ch=ch,
                            can_id=can_id,
                            sid=None,
                            did=None,
                            data=[data[x][0], data[x][1], data[x][2], data[x][3], data[x][4], data[x][5], data[x][6], data[x][7]],
                            padding=None
                        )
                        sleep(st_min)
                        i += 1
    else: return error

#---Envia controle de fluxo
def flow_control(ch:Channel, can_id:int, flow_status:int, size:int, time:int, padding):
    if padding is None: padding = 0xFF
    response_frame(
        ch=ch,
        can_id=can_id,
        sid=None,
        did=None,
        data=[flow_status, size, time, padding, padding, padding, padding, padding],
        padding=None
    )

def multi_frame(ch:Channel, tx_id:int, rx_id:int, sid:int, did:List[int], carga:Dict[str, any]):
    filter = message_filter(rx_id,0xFFFFFFFF)
    txHeader = carga["HEAD"]
    txLoad = carga["DATA"]
    first_frame(ch=ch, can_id=tx_id, sid=sid, did=did, message=txHeader, consecutive_block=txLoad)
    while True:
        msg = ch.read(timeout=-1)
        if filter(msg.id):
            if msg.data[0] in [0x30, 0x31, 0x32, 0x33]:
                consecutive_frame(ch=ch, can_id=tx_id, msg=msg, data=txLoad)
                break

#--Monta dicionario
def construct_load(frames_size: int):
    """ Retorna duas listas a primeira sendo ela uma Lista de inteiro
        E a segunda uma lista de listas de inteiro """
    try:
        load:Dict[str, any] = {
            "HEAD":[0x10]+[0x00] * 7,
            "DATA":[[((0x21 + i) - 0x10) % 0x10 + 0x20] + [0x00] * 7 for i in range(frames_size)]
        }
        return load["HEAD"], load["DATA"]
    except Exception as  e:
        print(f'Erro:{e} \nLocal: contruct_load()')

# def frame_update(frame:List[int], index:List[int], values):
#     try:
#         i = 0
#         for position in index:
#             frame[position] = values[i]
#             i+=1
#         return frame
#     except Exception as e:
#         print(f"Erro:{e} --- frame_update on UDS.py")


def frame_update(frame:List[int], values:Dict[str, any]):
    try:
        for key, value in values.items():
            index = int(key)
            frame[index] = value
    except Exception as e:
        print(f"Erro:{e} --- in function teste on UDS.py")


#---Envia ou confirma controle de sessão
def session_control(ch, can_id,  session, padding):
    response_frame(ch, can_id, sid= 0x50, did=[session], data=None, padding=padding)



import threading

# Variáveis globais
frame_data = None
stop_thread = False

# Função para monitorar o barramento CAN e buscar um frame específico
def broadcast_monitor(channel:Channel, tx_id):
    try:
        stop_thread = False
        while not stop_thread:
            try:
                # Receber frame do barramento
                frame = channel.read(timeout=2000)  # -- Verifica se existem mensagens na rede CAN
                if frame.id == tx_id:               # -- Verifica se a mensagem recebida corresponde a esperada
                    rx_data = frame.data            # -- Armazena os dados do frame no objeto request
                    stop_thread = True              # -- Para a execução da thread
                    return rx_data                  # -- Retorna os dados do frame
            except canlib.canNoMsg:                 # -- Nenhuma mensagem recebida no tempo de espera
                continue
            except canlib.canError as e:
                print(f"Erro no barramento CAN: {e}")
    except Exception as e:
        print(f"Erro in UDS : {e}")





# Inicializa a thread para monitorar o barramento CAN


#---Envia ou confirma controle de sessão
def ecu_reset(frame):
    print("")

def routine_control(frame):
    print("")

def clear_diagnostic_information(frame):
    print("")

def write_data_by_identifier(frame):
    print("")

def write_memory_by_address(frame):
    print("")

def request_download(frame):
    print("")

def request_upload(frame):
    print("")

def transfer_data(frame):
    print("")

def read_dtc_information(frame):
    print("")

def ReadDataByPeriodicIdentifier(frame):
    print("")

def security_acesses(seed, acesses, truck_model):
    print("")


def authentication(frame):
    print("")

#---Envia resposta negativa com codigo de erro
def negative_response(ch, can_id, did):
    response_frame(ch=ch, can_id=can_id,sid=0x7F, did=did, data=None, padding=0xFF)
    #print("negative_code, sid, NRC")

def extended_frame_response(ch):
    print('')
