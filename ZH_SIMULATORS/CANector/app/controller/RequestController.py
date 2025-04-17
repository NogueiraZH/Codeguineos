import threading
import time
from typing import Dict
from canlib import canlib
from canlib.canlib import Channel
from app.Model import Load as road
from app.Model.Computenox import Computenox
from app.Model.Request import Request

class RequestController:
    channel:Channel = None
    computenox:Computenox = None
    load:Dict[str, any] = None
    identification:Dict[str, any] = None
    configuration:Dict[str, any] = {}
    response:Dict[str, any] = {}
    thread:threading.Thread = None
    event = threading.Event()

    def __init__(self, channel:Channel, load:Dict[str, any]):
        """
        Inicializa uma nova instância da classe RequestController.

        Este método é responsável por configurar os atributos iniciais da classe, incluindo o canal CAN,
        os dados de identificação, configuração e carga, além de instanciar o objeto Computenox.

        :param channel: Objeto do tipo `Channel` que representa o canal CAN utilizado para comunicação.
        :param load: Dicionário contendo os dados de carga, incluindo identificação e configuração.
        """
        self.channel = channel
        self.identification =load["identificacao"]
        self.configuration = load["configuracao"]
        self.load = load
        self.computenox = Computenox(self.load)

    def start(self):
        """
        Inicia a execução de uma thread para processar a lógica principal.

        Este método limpa o evento de parada, cria uma nova thread para executar o método `run`
        com os dados de carga (`self.load`) e inicia a thread. Caso ocorra algum erro durante
        o processo, uma mensagem de erro será exibida.

        :raises Exception: Caso ocorra um erro ao iniciar a thread.
        """
        try:
            self.event.clear()
            self.thread = threading.Thread(target=self.run, args=(self.load,))
            self.thread.start()
        except Exception as e:
            print("ERRO IN START")
            return e

    def run(self, load):
        """
        Executa a lógica principal de processamento de mensagens CAN.

        Este método processa os parâmetros fornecidos no dicionário `load` e executa diferentes ações
        dependendo do tipo de mensagem (unicast ou broadcast). Para mensagens unicast, ele cria uma
        instância de `Request` e tenta enviar a mensagem, atualizando a resposta com os resultados.
        Para mensagens broadcast, ele monitora as mensagens recebidas. Os resultados são coletados e
        processados pelo objeto `Computenox`.

        :param load: Dicionário contendo os parâmetros de carga para processamento. Cada chave representa
                     um tipo de parâmetro, e os valores contêm os detalhes necessários para a comunicação.
        """
        while not self.event.is_set():
            for key, parameter in load.items():
                if key == "identificacao": continue
                elif key == "configuracao": continue
                else:
                    print(f"Requisitando parametro: {key}")
                    if parameter["tx_id"] != "broadcast":
                        request = Request(self.channel, parameter=parameter)
                        if request.invite():
                            if parameter.get("grandeza"):
                                self.response.update({parameter["id_parametro"]:[request.result, parameter["grandeza"]]})
                            else:
                                self.response.update({parameter["id_parametro"]:[request.result]})
                        else:
                            self.response.update({parameter["id_parametro"]:[None]})

                    else:
                        request = Request(self.channel, parameter=parameter)
                        request.monitor()

                        self.response.update({parameter["id_parametro"]:[request.result,parameter["grandeza"]]})
                    time.sleep(0.005)
                    self.computenox.colect(self.response)
                    self.response.update(self.computenox.getresult())


    def stop(self):
        """
        Interrompe a execução da thread principal de forma segura.

        Este método sinaliza o evento de parada para interromper o loop de execução
        no método `run` e aguarda a finalização da thread associada, garantindo que
        todos os recursos sejam liberados corretamente.
        """
        self.event.set()
        self.thread.join()

if __name__ == "__main__":
    ch = canlib.openChannel(channel=0, flags=canlib.canOPEN_ACCEPT_VIRTUAL)
    ch.setBusParams(canlib.canBITRATE_250K)
    ch.busOn()

    load = road.open_json("../json/SCANIA_EURO_0028.json")
    requestController = RequestController(ch,  load)
    requestController.run(load)
