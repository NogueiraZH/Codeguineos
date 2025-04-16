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
        self.channel = channel
        self.identification =load["identificacao"]
        self.configuration = load["configuracao"]
        self.load = load
        self.computenox = Computenox(self.load)

    def start(self):
        try:
            self.event.clear()
            self.thread = threading.Thread(target=self.run, args=(self.load,))
            self.thread.start()
        except Exception as e:
            print("ERRO IN START")
            return e

    def run(self, load):
        while not self.event.is_set():
            for key, parameter in load.items():
                if key == "identificacao": continue
                elif key == "configuracao": continue
                else:

                    # print(f"Nome do parametro:{key}")
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
                        time.sleep(0.050)
                        self.response.update({parameter["id_parametro"]:[request.result,parameter["grandeza"]]})
                    self.computenox.colect(self.response)
                    self.response.update(self.computenox.getresult())


    def stop(self):
        self.event.set()
        self.thread.join()

if __name__ == "__main__":
    ch = canlib.openChannel(channel=0, flags=canlib.canOPEN_ACCEPT_VIRTUAL)
    ch.setBusParams(canlib.canBITRATE_250K)
    ch.busOn()

    load = road.open_json("../json/SCANIA_EURO_0028.json")
    requestController = RequestController(ch,  load)
    requestController.run(load)
