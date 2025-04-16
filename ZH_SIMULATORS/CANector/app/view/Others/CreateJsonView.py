import tkinter as tk
from tkinter import messagebox
from app.Model.Load import Load


# Função para exibir os valores preenchidos
def create_json():
    try:
        name = entry_nome.get()
        id_carga = entry_id_carga.get()
        modelo_carga = entry_modelo_carga.get()
        identificacao = {
            "nome" : name,
            "id_carga" : id_carga,
            "modelo_carga" : modelo_carga
        }
        load = Load(name= name, identification=identificacao)
        load.create()
        messagebox.showinfo("Json", f"Json foi criado com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao criar o arquivo JSON: {e}")
        return


# Criar a janela principal
root = tk.Tk()
root.title("Cadastro de Carga")
root.geometry("300x250")  # Tamanho da janela

# Label e Entry para "nome"
label_nome = tk.Label(root, text="Nome:")
label_nome.pack(pady=5)
entry_nome = tk.Entry(root, width=30)
entry_nome.pack(pady=5)

# Label e Entry para "id_carga"
label_id_carga = tk.Label(root, text="ID Carga:")
label_id_carga.pack(pady=5)
entry_id_carga = tk.Entry(root, width=30)
entry_id_carga.pack(pady=5)

# Label e Entry para "modelo_carga"
label_modelo_carga = tk.Label(root, text="Modelo Carga:")
label_modelo_carga.pack(pady=5)
entry_modelo_carga = tk.Entry(root, width=30)
entry_modelo_carga.pack(pady=5)

# Botão para exibir os dados inseridos
botao_exibir = tk.Button(root, text="Criar Json", command=create_json)
botao_exibir.pack(pady=20)

# Iniciar o loop da interface gráfica
root.mainloop()
