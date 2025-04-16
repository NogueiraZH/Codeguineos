import json, os
from typing import Dict

class Load:
    root:str = "../json/"
    name:str = None
    identification:Dict[str, any]
    configuration:Dict[str, any]
    parameters:Dict[str, any]
    
    def __init__(self, name, identification):
        self.name = name
        self.identification = identification

    def route(self):
        newroute = {self.identification["id_carga"] : self.root}
        route = "../json/routes.json"
        if os.path.exists(route):
            with open(route, 'r') as file:
                rotas = json.load(file)
        else:
            rotas = {}
        rotas.update(newroute)
        with open(route, 'w') as file:
            json.dump(rotas, file, indent=4)

        print(f"Rotas atualizadas com sucesso em '{route}'!")


    def create(self):
        try:
            self.root = self.root + self.name + "_" + self.identification["id_carga"]  + ".json"
            load = {
                "identificacao": self.identification,
            }
            with open(self.root, 'w') as f:
                json.dump(load, f, indent=2)
            self.route()
            return True
        except Exception as e:
            print(f"Erro ao criar o arquivo: {e} -- Class Load")
            return False

    def open(self, route:str = None):
        try:
            if route is None: route = self.root
            with open(route, 'r') as file:
                load = json.load(file)
            return load
        except Exception as e:
            print(f"Erro ao abrir o arquivo: {e} -- Class Load")

    def update(self, update:Dict[str, any]):
        if os.path.exists(self.root):
            with open(self.root, 'r') as file:
                deprecated = json.load(file)
        else:
            updated = {}
        deprecated.update(update)
        with open(self.root, 'w') as file:
            json.dump(deprecated, file, indent=4)
        print(f"Rotas atualizadas com sucesso em '{self.root}'!")
        pass


if __name__ == "__main__":
    load = {
        "identificacao" : {
            "nome" : "Mercedez",
            "id_carga" : "5165",
            "modelo_carga" : "M2"
        },
        "configuracao" : {
            "amostras" : 2000,
            "valor_maximo_coleta_02" : 10,
            "valor_minimo_coleta_02" : 2,
            "valor_minimo_coleta_carga" : 70,
            "valor_maximo_coleta_carga" : 100
        }
    }



    load = Load("Sania", load["identificacao"])
    print(load.create())
    print(load.open())


def open_json(route:str = None):
    try:
        with open(route, 'r') as file:
            load = json.load(file)
        return load
    except Exception as e:
        print(f"Erro ao abrir o arquivo: {e} -- Class Load")
