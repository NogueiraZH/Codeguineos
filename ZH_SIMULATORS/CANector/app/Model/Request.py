import threading
import time

from ZH_SIMULATORS.CANector.services.UDS import *
from canlib.canlib import Channel

class Request:
    channel:Channel = None
    tx_id:any = None
    rx_id:int = None
    tx_data:List[int] = None
    rx_data:List[int] = None
    result = None
    dlc:int = 8
    nrc:int = None
    parameter:Dict[str,any] = None
    event = threading.Event()

    def __init__(self, channel, nrc = 0x7f, parameter:Dict[str,any] = None):
        try:
            self.channel = channel
            if parameter.get("tx_id") == "broadcast":
                self.tx_id = parameter["tx_id"]
            else:
                self.tx_id = int(parameter["tx_id"], 16)
            for key, value in parameter.items():
                if key == "rx_id": self.rx_id = int(parameter["rx_id"], 16)
                elif key == "tx_frame":
                    self.dlc = len(parameter["tx_frame"])
                    self.tx_data = [int(byte, 16) for byte in parameter["tx_frame"]]
                self.nrc = nrc
                self.parameter = parameter
        except Exception as e:
            print(f"Erro in Request construct: {e}")


    def invite(self):
        try:
            frame = Frame(id_=self.tx_id,dlc=self.dlc,data=self.tx_data,flags=canlib.MessageFlag.EXT)
            self.channel.write(frame)
            # Captura o tempo inicial
            start_time = time.time()
            # Espera um resposta por 100 ms
            while (time.time() - start_time) < 0.1:
                if self.receive():
                    return True
        except Exception as e:
            print(f"Erro in Request invite: {e}")

    def validate(self):
        """Realiza a validação do frame recebido com o frame enviado."""
        try:
            code_len = self.tx_data[0]
            validate = False

            if (self.tx_data[1] + 0x40) != self.rx_data[1]:
                return validate

            for i in range(2, code_len):
                if self.rx_data[i] == self.tx_data[i]:
                    validate = True
                else:
                    validate = False
                    break
            return validate
        except Exception as e:
            print(f"Erro in Request validate: {e}")
            return False

    def receive(self):
        try:
            message = self.channel.read(timeout=2000)
            if message is not None:
                if message.id == self.rx_id:
                    self.rx_data = [byte for byte in message.data]

                    # Verifica se o frame recebido é um frame de cabeçalho de fluxo
                    if message.data[0] in [0x10]:
                        flow_control(
                            ch=self.channel,
                            can_id=self.tx_id,
                            flow_status=0x30,
                            size=0x00,
                            time=0x00,
                            padding=0xFF
                        )

                        if self.flowcontrol(message): return True
                        else: return False

                    # Verifica se o frame recebido é um frame de resposta válida
                    elif message.data[1] != self.nrc:
                        if self.validate():
                            # if self.parameter is not None:
                            # Verifica se o parâmetro deve ser lido como status
                            if self.parameter.get("status"):
                                read_bytes: Dict[str, any] = self.parameter["bytes_leitura"]
                                read_bytes: List[int] = list(read_bytes.values())[0]
                                status_data = self.rx_data[read_bytes[0]]
                                status = self.parameter["status"]
                                for key, value in status.items():
                                    if key == str(status_data):
                                        self.result = value
                                        return True
                            else:
                                self.result = self.calculator(self.parameter)
                                return True
                        else:
                            return False
                    else:
                        print(f"Erro: NRC {hex(message.data[1])}")
                        self.result = f"Erro: NRC ( {hex(self.nrc)}, {hex(self.rx_data[2])}, {hex(self.rx_data[3])} )"
                        return True
            else:
                print("Nenhuma mensagem recebida no canal.")
                return False

        except Exception as e:
            print(f"Erro in Request receive: {e}")
            return False

    def calculator(self, parameter:Dict[str,any], flow_data:any = None):
        """
        Método responsável por calcular o resultado com base nos parâmetros fornecidos.
        :return:
        """
        try:
            slope = parameter["slope"]
            offset = parameter["offset"]
            calc = parameter["calculo"]
            decimal = parameter["casas_decimais"]
            read_bytes:Dict[str, any] = parameter["bytes_leitura"]
            if flow_data is None:
                read_bytes:List[int] = list(read_bytes.values())[0]
                byte_D = 0 if len(read_bytes) == 1 else self.rx_data[read_bytes[0]]
                byte_R = self.rx_data[read_bytes[-1]]
                self.result = eval(calc)
            else:
                read_bytes:List[int] = [byte[0] for byte in read_bytes.values()]
                byte_D = 0 if len(read_bytes) == 1 else flow_data[read_bytes[0]]
                byte_R = flow_data[read_bytes[-1]]
                self.result = eval(calc)
            if self.result is None: self.result = 0
            if decimal > 0 :
                return round(self.result, decimal)
            else:
                return round(self.result)
        except Exception as e:
            print(f"Erro in Request Calculator: {e}")

    def flowcontrol(self, message:Frame):
        try:
            received_data:Dict[str, any] = receive_flow_data(self.channel, self.rx_id, message)
            flow_read_bytes:Dict[str, any] = self.parameter["bytes_leitura"]
            flow_keys = list(flow_read_bytes.keys())#[0]
            flow_data = [0x00] * 8
            for key in flow_keys:
                flow_data[flow_read_bytes[key][0]] = received_data[key][flow_read_bytes[key][0]]

            self.result = self.calculator(self.parameter, flow_data)
            return True
        except Exception as e:
            print(f"Erro in Request flowcontrol: {e}")
            return False

    def monitor(self):
        """
        Método responsável por monitorar mensagens no canal. Lê as mensagens até que um
        evento específico seja acionado (`self.event.set()`).
        """
        try:
            stop_thread = False
            while not stop_thread:
                print("Thread de braodcast executando")
                msg = self.channel.read(timeout=2000)  # Timeout especificado
                if msg.id == self.rx_id:
                    self.rx_data = msg.data
                    self.result = self.calculator(self.parameter)
                    stop_thread = True
        except AttributeError as err:
            print(f"Atributo incorreto ao acessar o objeto: {err}")
        except Exception as err:
            print(f"Erro inesperado no monitor: {err}")
            return False


    def broadcast(self):
        try:
            # Thread iniciada para executar o método monitor
            receive_monitor = threading.Thread(target=self.monitor)
            receive_monitor.daemon = True  # Define como daemon para não bloquear a execução principal
            receive_monitor.start()
        except Exception as err:
            print(f"Erro ao iniciar a thread de monitoramento: {err}")




if __name__ == "__main__":
    ch = canlib.openChannel(channel=0, flags=canlib.canOPEN_ACCEPT_VIRTUAL)
    ch.setBusParams(canlib.canBITRATE_250K)
    ch.busOn()

    valor_teste = open("../../json/data.json", "r")
    valor = json.load(valor_teste)["data"]

    json_data = open("../../json/SCANIA_EURO_0028.json", "r")
    data = json.load(json_data)
    nivel_arala = data["nivel_reservatorio_arla"]
    tx_id = int(nivel_arala["tx_id"], 16)
    rx_id = int(nivel_arala["rx_id"], 16)
    tx_frame = nivel_arala["tx_frame"]

    # nox = Request(ch, tx_id, rx_id, tx_data = tx_frame, parameter=nivel_arala)
    # print(nox.tx_data)
    # print(nox.invite())



















