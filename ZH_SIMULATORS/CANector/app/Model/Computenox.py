import time
from getpass import fallback_getpass
from time import sleep
from typing import Dict

class Computenox:
    load:Dict[str, any]
    limit_amostras:int
    total_amostras = 0
    maximo_o2:int
    minimo_o2:int
    maximo_carga:int
    minimo_carga:int
    o2_pos = False
    dewpoint:Dict[str, any] = {"900":"Aguardando dewpoint"}
    media_nox:Dict[str, any] = {"300":[0, "ppm"]}
    progresso:Dict[str, any] = {"400":[0, "%"]}
    nox_total:Dict[str, any] = {"500":[0, "ppm"]}
    n_amostras:Dict[str, any] = {"600":0}
    result:Dict[str, any] = {}
    DEWPOINT = False
    DEW_COUNT = 0
    VALID_NOX = 0

    def __init__(self, load:Dict[str, any]):
        self.load = load
        self.limit_amostras = load["configuracao"]["amostras"]
        self.maximo_o2 = load["configuracao"]["valor_maximo_coleta_02"]
        self.minimo_o2 = load["configuracao"]["valor_minimo_coleta_02"]
        self.maximo_carga = load["configuracao"]["valor_maximo_coleta_carga"]
        self.minimo_carga = load["configuracao"]["valor_minimo_coleta_carga"]
        for chave, valor in self.load.items():
            if chave == "identificacao": continue
            elif chave == "configuracao":continue
            else:
                if valor["id_parametro"] == 1:
                    self.o2_pos = True

    def validate_nox_point(self, COLECTED_NOX):
        if COLECTED_NOX and not isinstance(COLECTED_NOX, str):
            if COLECTED_NOX > 0 and COLECTED_NOX < 3000:
                if self.DEW_COUNT > 5:
                    self.DEWPOINT = True
                    self.dewpoint["900"] = "Dados validos"
                if self.DEWPOINT is not True:
                    if self.VALID_NOX != COLECTED_NOX:
                        self.VALID_NOX = COLECTED_NOX
                        self.DEW_COUNT +=1




    def colect(self, dados:Dict[str, any]):
        o2, engine_load, nox_pos, nox_pre = 0, 0, 0, 0

        # Coleta de dados utilizados para computar nox
        for key, value in dados.items():
            if key == 1:
                if value[0] is not None:
                    if type(value[0]) is not str: o2 = value[0]
            elif key == 11:
                if value[0] is not None:
                    if type(value[0]) is not str: engine_load = value[0]
            elif key == 0:
                if value[0] is not None:
                    if type(value[0]) is not str: nox_pos = value[0]
            elif key == 2:
                if value[0] is not None:
                    if type(value[0]) is not str: nox_pre = value[0]

        self.validate_nox_point(nox_pos)

        if self.DEWPOINT:
            self.dewpoint["900"] = "Dados validos"
            if self.o2_pos is True:
                if (o2 >= self.minimo_o2) and (o2 <= self.maximo_o2):
                    if (engine_load >= self.minimo_carga) and (engine_load <= self.maximo_carga):
                        if self.n_amostras["600"]< self.limit_amostras:
                            if self.total_amostras > 200:
                                self.n_amostras["600"] += 1
                                self.nox_total["500"][0] += int(nox_pos)
                                self.progresso["400"][0] = int((self.n_amostras["600"] / self.limit_amostras) * 100)
                                self.media_nox["300"][0] = round(self.nox_total["500"][0] / self.n_amostras["600"])
                            else: self.total_amostras+= 1
            else:
                # Adicionar Coleta de nox pré após dados validos
                if engine_load is not None:
                    if (engine_load >= self.minimo_carga) and (engine_load <= self.maximo_carga):
                        print(f"Carga: {engine_load}")
                        if self.n_amostras["600"]< self.limit_amostras:
                            if self.total_amostras > 200:
                                self.n_amostras["600"] += 1
                                self.nox_total["500"][0] += int(nox_pos)
                                self.progresso["400"][0] = int((self.n_amostras["600"] / self.limit_amostras) * 100)
                                self.media_nox["300"][0] = round(self.nox_total["500"][0] / self.n_amostras["600"])
                            else: self.total_amostras += 1
            time.sleep(.02)

    def getresult(self):
        self.result.update(self.dewpoint)
        self.result.update(self.media_nox)
        self.result.update(self.progresso)
        self.result.update(self.nox_total)
        self.result.update(self.n_amostras)
        return self.result
