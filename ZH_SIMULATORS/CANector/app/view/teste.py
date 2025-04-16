import json, threading, time, random
import tkinter as tk
from pkgutil import get_loader
from tkinter import filedialog, messagebox
from typing import Dict
from canlib import canlib
from app.controller.RequestController import RequestController

load:Dict[str, any]
label_valores = {}
callback:RequestController
route = ""

obrigatorio = {
    "NOx PRÉ":2, "NOx PÓS":0, "O2 PRÉ":800, "O2 PÓS":1,
    "rpm motor":51, "Carga":11, "Nível arla":6, "Temp. Arla":7,
    "Temp. PRÉ":3, "Pressão Turbo":12
}
adicionais = {
    "Temp. Motor":44, "Qualidade Arla":34, "Arla Injetado":33,
    "Ativação Bomba":17,"Temp. PÓS":29
}
eficiencia = {
    "Status SCR":900, "Média NOx pós":300, "Progresso":400,
    "NOx PÓS - Total":500, "N.Amostras":600
}
def view_parameters():
    try:
        lista_parametros = {}
        global load
        for parameter, attributes in load.items():
            if parameter == "identificacao": continue
            elif parameter == "configuracao": continue
            elif attributes["id_parametro"] in obrigatorio.values(): continue
            else:
                key = attributes["descricao"]
                value = attributes["id_parametro"]
                if value in adicionais.values(): continue
                else:
                    lista_parametros.update({key:value})
                    adicionais.update(lista_parametros)
        for chave, valor in lista_parametros.items():
            criar_linha(frame_adicionais, chave, valor)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar parametros adicionais {e}")


def open_can_channel():
    global load
    try:
        config = load["configuracao"]
        ch = canlib.openChannel(channel=0, flags=canlib.canOPEN_ACCEPT_VIRTUAL)
        if config["bitrate"] == "250K":
            ch.setBusParams(canlib.canBITRATE_250K)
        elif config["bitrate"] == "500K":
            ch.setBusParams(canlib.canBITRATE_500K)
        else:
            ch.setBusParams(canlib.canBITRATE_1M)
        ch.busOn()
        return ch
    except Exception as e:
        print(f"Erro ao abrir o canal: {e}")
        return None

def carregar_json():
    global load, route
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo JSON",
        filetypes=[("Arquivos JSON", "*.json")]
    )
    route = caminho_arquivo

    if caminho_arquivo:
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as file:
                load = json.load(file)
            print("Conteúdo do JSON:", load)
            # view_parameters()
            show_status.config(text="Json Carregado", background="yellow")
            messagebox.showinfo("Arquivo carregado", "Arquivo carregado com sucesso!")
        except Exception as e:
            print("Erro ao carregar o arquivo JSON:", e)
            messagebox.showerror("Erro ao carregar o arquivo JSON", f"Erro ao carregar o arquivo JSON: {e}")

def iniciar():
    try:
        global load, callback
        channel = open_can_channel()
        callback = RequestController(channel, load)
        callback.start()
        atualizar_dados_thread()
        show_status.config(text="Tester Rodando", background="green")
        messagebox.showinfo(title="sucesso", message="Execução em andamento" )
    except Exception as e:
        messagebox.showerror("Erro ao iniciar", f"Erro ao iniciar: {e}")

def parar():
    try:
        global callback
        callback.stop()
        show_status.config(text="Tester Parado", background="red")
        messagebox.showinfo("Execução", "Execução encerrada com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro ao parar", f"Erro ao parar: {e}")

def centralize(window, width, height):
    view_width = window.winfo_screenwidth()
    view_height = window.winfo_screenheight()
    position_x = (view_width // 2) - (width // 2)
    position_y = (view_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{position_x}+{position_y}")

def atualizar_valores_na_tela(dados):
    for id_parametro, valor in dados.items():
        id_str = str(id_parametro)
        if id_str in label_valores:
            if valor is not None:
                if type(valor) == list:
                    if len(valor) > 1:
                        label_valores[id_str].config(text=f"{valor[0]} " + valor[1])
                    else:
                        if valor[0] is None:
                            label_valores[id_str].config(text="--")
                        else:
                            label_valores[id_str].config(text=f"{valor[0]}")
                else:
                    label_valores[id_str].config(text=f"{valor}")
            else:
                label_valores[id_str].config(text="--")


def atualizar_dados_thread():
    def atualizar():
        while True:
            time.sleep(.050)
            if callback and hasattr(callback, "response"):
                dados = callback.response
                root.after(50, atualizar_valores_na_tela, dados)

    thread = threading.Thread(target=atualizar, daemon=True)
    thread.start()

def atualizar_json():
    global route, load
    if route != "":
        try:
            with open(route, 'r', encoding='utf-8') as file:
                load = json.load(file)
            print("Conteúdo do JSON:", load)
            messagebox.showinfo("Arquivo atualizado", "Arquivo atualizado com sucesso!")
        except Exception as e:
            print("Erro ao carregar o arquivo JSON:", e)
            messagebox.showerror("Erro ao atualizar o arquivo JSON", f"Erro ao atualizar o arquivo JSON: {e}")

def criar_linha(frame_pai, chave, valor, largura=20):
    row = tk.Frame(frame_pai, bg="#ADD8E6")
    row.pack(fill="x", pady=5)

    tk.Label(row, text=chave, bg="#ADD8E6", width=15, anchor="center",
             font=("Arial", 10, "bold")).pack(side="top", padx=(5, 5))

    label_result = tk.Label(row, text="--", bg="white", width=largura, anchor="center",
                            relief="sunken", font=("Arial", 12))
    label_result.pack(side="top", padx=(5, 5))

    label_valores[str(valor)] = label_result

def new_teste():
    try:
        global load, callback, label_valores
        channel = open_can_channel()
        callback = RequestController(channel, load)
        callback.start()
        label_valores = {}
        atualizar_dados_thread()
        show_status.config(text="Tester Rodando", background="green")
        messagebox.showinfo(title="sucesso", message="Execução em andamento" )
    except Exception as e:
        messagebox.showerror("Erro ao iniciar", f"Erro ao iniciar: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Interface Gráfica")
    centralize(root, 900, 600)

    # Frame principal com grid
    main_frame = tk.Frame(root, bg="#ADD8E6")
    main_frame.pack(fill="both", expand=True)

    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.columnconfigure(2, weight=1)

    # Coluna 1 - Dados obrigatórios
    frame_obrigatorio = tk.Frame(main_frame, bg="#ADD8E6", padx=10, pady=10)
    frame_obrigatorio.grid(row=0, column=0, sticky="nsew")

    # Coluna 2 - Dados adicionais
    frame_adicionais = tk.Frame(main_frame, bg="#ADD8E6", padx=10, pady=10)
    frame_adicionais.grid(row=0, column=1, sticky="nsew")

    # Coluna 3 - Eficiência + botões
    frame_direito = tk.Frame(main_frame, bg="#ADD8E6", padx=10, pady=10)
    frame_direito.grid(row=0, column=2, sticky="nsew")

    frame_eficiencia = tk.Frame(frame_direito, bg="#ADD8E6")
    frame_eficiencia.pack(fill="both", expand=True)

    frame_botoes = tk.Frame(frame_direito, bg="#ADD8E6")
    frame_botoes.pack(pady=20)

    # Labels dos dados


    for chave, valor in obrigatorio.items():
        criar_linha(frame_obrigatorio, chave, valor)

    for chave, valor in adicionais.items():
        criar_linha(frame_adicionais, chave, valor)

    for chave, valor in eficiencia.items():
        criar_linha(frame_eficiencia, chave, valor, largura=20)

    # Status e botões
    tk.Label(frame_botoes, text="Status:", bg="#ADD8E6",
             font=("Arial", 10, "bold")).pack(pady=(10, 2))

    show_status = tk.Label(frame_botoes, text="--", bg="white", width=20, anchor="center",
                           relief="sunken", font=("Arial", 12))
    show_status.pack(pady=(0, 15))

    botoes = [
        ("Carregar JSON", carregar_json),
        ("Atualizar JSON", atualizar_json),
        ("Iniciar Teste", iniciar),
        ("Parar Teste", parar),
        # ("Novo teste", new_teste)
    ]

    for texto, comando in botoes:
        tk.Button(frame_botoes, text=texto, command=comando, width=20,
                  font=("Arial", 10)).pack(pady=5)

    root.mainloop()

