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
        """
        Inicializa uma instância da classe Request.

        :param channel: Objeto do tipo `Channel` que representa o canal CAN utilizado para comunicação.
        :param nrc: Código de resposta negativa (Negative Response Code) padrão. Valor padrão: 0x7f.
        :param parameter: Dicionário contendo os parâmetros necessários para a configuração da requisição.
                  Espera-se que contenha as seguintes chaves:
                  - "tx_id": ID de transmissão (em formato hexadecimal ou "broadcast").
                  - "rx_id": ID de recepção (em formato hexadecimal).
                  - "tx_frame": Lista de bytes representando o quadro de transmissão.
        """
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
        """
        Envia um quadro CAN para o canal configurado e aguarda uma resposta por até 100 ms.

        O método cria um quadro CAN com os dados configurados (`tx_id`, `dlc`, `tx_data`) e o envia
        pelo canal. Em seguida, entra em um loop que verifica se uma resposta foi recebida dentro
        do intervalo de 100 ms. Caso uma resposta válida seja recebida, o método retorna `True`.

        :return: `True` se uma resposta válida for recebida, caso contrário, nenhuma resposta é processada.
        :raises Exception: Caso ocorra algum erro durante o envio ou recebimento do quadro.
        """
        try:
            frame = Frame(id_=self.tx_id,dlc=self.dlc,data=self.tx_data,flags=canlib.MessageFlag.EXT)
            self.channel.write(frame)
            print(f"Enviando frame: {frame}")
            # Captura o tempo inicial
            start_time = time.time()
            # Espera um resposta por 100 ms
            print("Aguardando resposta por 100ms")
            while (time.time() - start_time) < 0.1:
                if self.receive():
                    print("Resposta recebida")
                    return True
        except Exception as e:
            print(f"Erro in Request invite: {e}")

    def validate(self):
        """
        Valida se os dados recebidos no canal correspondem aos dados transmitidos.

        O método compara os dados recebidos (`rx_data`) com os dados transmitidos (`tx_data`) para verificar
        se a resposta recebida é válida. A validação é feita com base no comprimento do código e na comparação
        byte a byte dos dados.

        :return: `True` se os dados recebidos forem válidos, caso contrário, `False`.
        :raises Exception: Caso ocorra algum erro durante a validação.
        """
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
        """
        Lê uma mensagem do canal CAN e processa o frame recebido.

        Este método tenta ler uma mensagem do canal configurado. Caso uma mensagem seja recebida,
        verifica se o ID da mensagem corresponde ao ID de recepção configurado (`rx_id`). Em seguida,
        processa o frame recebido para identificar se é um cabeçalho de fluxo, uma resposta válida
        ou um erro.

        :return:
            - `True` se o frame recebido for processado com sucesso.
            - `False` se ocorrer algum erro ou o frame não for válido.
        :raises Exception: Caso ocorra algum erro durante a leitura ou processamento da mensagem.
        """
        try:
            message = self.channel.read(timeout=2000)
            if message is not None:
                if message.id == self.rx_id:
                    self.rx_data = [byte for byte in message.data]

                    # Verifica se o frame recebido é um frame de cabeçalho de fluxo
                    if message.data[0] in [0x10]:
                        print("Frame de cabeçalho de fluxo recebido")
                        print(f"Dados recebidos: {message.data}")
                        flow_control(
                            ch=self.channel,
                            can_id=self.tx_id,
                            flow_status=0x30,
                            size=0x00,
                            time=0x00,
                            padding=0xFF
                        )
                        print(f"Enviando frame de controle de fluxo: {message.data}")

                        if self.flowcontrol(message):
                            return True
                        else:
                            return False

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
                return None
            else:
                print("Nenhuma mensagem recebida no canal.")
                return False

        except Exception as e:
            print(f"Erro in Request receive: {e}")
            return False

    def calculator(self, parameter:Dict[str,any], flow_data:any = None):
        """
        Método responsável por calcular o resultado com base nos parâmetros fornecidos.

        Este método utiliza os parâmetros fornecidos para realizar cálculos baseados em uma fórmula
        definida no parâmetro `calculo`. Ele também considera dados recebidos (`rx_data`) ou dados
        de fluxo (`flow_data`) para realizar o cálculo.

        :param parameter: Dicionário contendo os parâmetros necessários para o cálculo. Espera-se que contenha:
                          - "slope": Inclinação utilizada no cálculo.
                          - "offset": Deslocamento utilizado no cálculo.
                          - "calculo": Fórmula de cálculo como string, que será avaliada com `eval`.
                          - "casas_decimais": Número de casas decimais para arredondamento do resultado.
                          - "bytes_leitura": Dicionário indicando os bytes a serem lidos para o cálculo.
        :param flow_data: Dados de fluxo opcionais que podem ser utilizados no cálculo. Valor padrão: `None`.
        :return: O resultado do cálculo arredondado de acordo com o número de casas decimais especificado.
        :raises Exception: Caso ocorra algum erro durante o cálculo.
        """
        try:
            print("Calculando resultado...")
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
                if len(read_bytes.values()) > 1:
                    read_bytes:List[int] = [byte[0] for byte in read_bytes.values()]
                else:
                    read_bytes:List[int] = [byte for byte in list(read_bytes.values())[0]]
                byte_D = 0 if len(read_bytes) == 1 else flow_data[read_bytes[0]]
                byte_R = flow_data[read_bytes[-1]]
                self.result = eval(calc)
            print(f"Resultado Calculado: {self.result}")
            if self.result is None: self.result = 0
            if decimal > 0 :
                return round(self.result, decimal)
            else:
                return round(self.result)
        except Exception as e:
            print(f"Erro in Request Calculator: {e}")

    def flowcontrol(self, message:Frame):
        """
        Processa o controle de fluxo para mensagens CAN.

        Este método recebe uma mensagem CAN e utiliza os dados recebidos para calcular o resultado
        com base nos parâmetros configurados. Ele processa os bytes de leitura especificados no
        parâmetro `bytes_leitura` e utiliza o método `calculator` para realizar os cálculos.

        :param message: Objeto do tipo `Frame` que representa a mensagem CAN recebida.
        :return: `True` se o processamento do controle de fluxo for bem-sucedido, caso contrário, `False`.
        :raises Exception: Caso ocorra algum erro durante o processamento do controle de fluxo.
        """
        try:
            print("Aguardando resposta do controle de fluxo")
            received_data = receive_flow_data(self.channel, self.rx_id, message)
            if received_data != False and received_data is not None:
                print(f"Resposta recebido{received_data}")
                flow_read_bytes:Dict[str, any] = self.parameter["bytes_leitura"]
                flow_keys = list(flow_read_bytes.keys())
                flow_data = [0x00] * 8
                if len(flow_keys) > 1:
                    for key in flow_keys:
                        flow_data[flow_read_bytes[key][0]] = received_data[key][flow_read_bytes[key][0]]
                elif len(flow_keys) == 1:
                    for valor in flow_read_bytes[flow_keys[0]]:
                        flow_data[valor] = received_data[flow_keys[0]][valor]
                print(f"Dados de fluxo: {flow_data}")
                print("Calculando resultado com dados de fluxo")
                if self.parameter.get("status"):
                    print("Verificando status")
                    read_bytes: Dict[str, any] = flow_read_bytes
                    read_bytes: List[int] = list(read_bytes.values())[0]
                    status_data = received_data[flow_keys[0]][read_bytes[0]]
                    print(status_data)
                    status = self.parameter["status"]
                    for key, value in status.items():
                        if key == str(status_data):
                            self.result = value
                            return True
                else:
                    self.result = self.calculator(self.parameter, flow_data)
                    print("Controle de fluxo finalizado True")
                    return True
            else:
                print("Controle de fluxo finalizado False")
                return False

        except Exception as e:
            print(f"Erro in Request flowcontrol: {e}")
            return False

    def monitor(self):
        """
        Monitora mensagens no canal CAN até que um evento específico seja acionado.

        Este método lê mensagens do canal CAN em um loop contínuo até que a condição de parada
        seja atendida. Quando uma mensagem com o ID de recepção configurado (`rx_id`) é recebida,
        os dados da mensagem são processados e o resultado é calculado utilizando o método `calculator`.
        O loop é encerrado após o processamento bem-sucedido da mensagem.

        :raises AttributeError: Caso ocorra um erro ao acessar atributos do objeto.
        :raises Exception: Caso ocorra qualquer outro erro inesperado durante a execução.
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
        """
        Inicia uma thread para monitorar mensagens no canal CAN.

        Este método cria e inicia uma thread que executa o método `monitor` para monitorar mensagens
        no canal CAN. A thread é configurada como daemon para garantir que ela não bloqueie a execução
        principal do programa.

        :raises Exception: Caso ocorra algum erro ao iniciar a thread de monitoramento.
        """
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



















