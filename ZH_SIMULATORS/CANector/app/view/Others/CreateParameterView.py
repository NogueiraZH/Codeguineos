import tkinter as tk
from tkinter import messagebox

# Função para exibir os dados inseridos
def exibir_dados():
    # Coletar os dados da interface
    calculo = entry_calculo.get()
    slope = entry_slope.get()
    offset = entry_offset.get()
    valor_maximo = entry_valor_maximo.get()
    valor_minimo = entry_valor_minimo.get()
    casas_decimais = entry_casas_decimais.get()
    grandeza = entry_grandeza.get()
    id_parametro = entry_id_parametro.get()
    descricao = entry_descricao.get()
    tx_id = entry_tx_id.get()
    rx_id = entry_rx_id.get()
    tx_frame = entry_tx_frame.get()
    bytes_leitura = entry_bytes_leitura.get()

    # Exibir os dados inseridos em uma caixa de mensagem
    messagebox.showinfo("Dados Inseridos",
                        f"Cálculo: {calculo}\nSlope: {slope}\nOffset: {offset}\n"
                        f"Valor Máximo Exibição: {valor_maximo}\nValor Mínimo Exibição: {valor_minimo}\n"
                        f"Casas Decimais: {casas_decimais}\nGrandeza: {grandeza}\n"
                        f"ID Parâmetro: {id_parametro}\nDescrição: {descricao}\n"
                        f"TX ID: {tx_id}\nRX ID: {rx_id}\nTX Frame: {tx_frame}\nBytes Leitura: {bytes_leitura}")

# Criar a janela principal
root = tk.Tk()
root.title("Configuração Nível Reservatório Arla")
root.geometry("600x600")  # Tamanho da janela

# Frame para organizar os campos em 2 colunas
frame_esquerda = tk.Frame(root)
frame_esquerda.grid(row=0, column=0, padx=20, pady=20)

frame_direita = tk.Frame(root)
frame_direita.grid(row=0, column=1, padx=20, pady=20)

# Labels e Entrys para os dados principais (lado esquerdo)
label_calculo = tk.Label(frame_esquerda, text="Cálculo:")
label_calculo.grid(row=0, column=0, sticky="w", pady=5)
entry_calculo = tk.Entry(frame_esquerda, width=40)
entry_calculo.insert(0, "(byte_D * 256 + byte_R) * slope - offset")
entry_calculo.grid(row=0, column=1, pady=5)

label_slope = tk.Label(frame_esquerda, text="Slope:")
label_slope.grid(row=1, column=0, sticky="w", pady=5)
entry_slope = tk.Entry(frame_esquerda, width=40)
entry_slope.insert(0, "0.01")
entry_slope.grid(row=1, column=1, pady=5)

label_offset = tk.Label(frame_esquerda, text="Offset:")
label_offset.grid(row=2, column=0, sticky="w", pady=5)
entry_offset = tk.Entry(frame_esquerda, width=40)
entry_offset.insert(0, "0")
entry_offset.grid(row=2, column=1, pady=5)

label_valor_maximo = tk.Label(frame_esquerda, text="Valor Máximo Exibição:")
label_valor_maximo.grid(row=3, column=0, sticky="w", pady=5)
entry_valor_maximo = tk.Entry(frame_esquerda, width=40)
entry_valor_maximo.insert(0, "100")
entry_valor_maximo.grid(row=3, column=1, pady=5)

label_valor_minimo = tk.Label(frame_esquerda, text="Valor Mínimo Exibição:")
label_valor_minimo.grid(row=4, column=0, sticky="w", pady=5)
entry_valor_minimo = tk.Entry(frame_esquerda, width=40)
entry_valor_minimo.insert(0, "0")
entry_valor_minimo.grid(row=4, column=1, pady=5)

label_casas_decimais = tk.Label(frame_esquerda, text="Casas Decimais:")
label_casas_decimais.grid(row=5, column=0, sticky="w", pady=5)
entry_casas_decimais = tk.Entry(frame_esquerda, width=40)
entry_casas_decimais.insert(0, "0")
entry_casas_decimais.grid(row=5, column=1, pady=5)

label_grandeza = tk.Label(frame_esquerda, text="Grandeza:")
label_grandeza.grid(row=6, column=0, sticky="w", pady=5)
entry_grandeza = tk.Entry(frame_esquerda, width=40)
entry_grandeza.insert(0, "%")
entry_grandeza.grid(row=6, column=1, pady=5)

# Labels e Entrys para os dados secundários (lado direito)
label_id_parametro = tk.Label(frame_direita, text="ID Parâmetro:")
label_id_parametro.grid(row=0, column=0, sticky="w", pady=5)
entry_id_parametro = tk.Entry(frame_direita, width=40)
entry_id_parametro.insert(0, "6")
entry_id_parametro.grid(row=0, column=1, pady=5)

label_descricao = tk.Label(frame_direita, text="Descrição:")
label_descricao.grid(row=1, column=0, sticky="w", pady=5)
entry_descricao = tk.Entry(frame_direita, width=40)
entry_descricao.insert(0, "Nível Arla:")
entry_descricao.grid(row=1, column=1, pady=5)

label_tx_id = tk.Label(frame_direita, text="TX ID:")
label_tx_id.grid(row=2, column=0, sticky="w", pady=5)
entry_tx_id = tk.Entry(frame_direita, width=40)
entry_tx_id.insert(0, "0x18DA3DFA")
entry_tx_id.grid(row=2, column=1, pady=5)

label_rx_id = tk.Label(frame_direita, text="RX ID:")
label_rx_id.grid(row=3, column=0, sticky="w", pady=5)
entry_rx_id = tk.Entry(frame_direita, width=40)
entry_rx_id.insert(0, "0x18DAFA3D")
entry_rx_id.grid(row=3, column=1, pady=5)

label_tx_frame = tk.Label(frame_direita, text="TX Frame:")
label_tx_frame.grid(row=4, column=0, sticky="w", pady=5)
entry_tx_frame = tk.Entry(frame_direita, width=40)
entry_tx_frame.insert(0, "0x03,0x30,0x1C,0x01,0xFF,0xFF,0xFF,0xFF")
entry_tx_frame.grid(row=4, column=1, pady=5)

label_bytes_leitura = tk.Label(frame_direita, text="Bytes Leitura:")
label_bytes_leitura.grid(row=5, column=0, sticky="w", pady=5)
entry_bytes_leitura = tk.Entry(frame_direita, width=40)
entry_bytes_leitura.insert(0, "4,5")
entry_bytes_leitura.grid(row=5, column=1, pady=5)

# Botão para exibir os dados inseridos
botao_exibir = tk.Button(root, text="Exibir Dados", command=exibir_dados)
botao_exibir.grid(row=1, column=0, columnspan=2, pady=20)

# Iniciar o loop da interface gráfica
root.mainloop()
