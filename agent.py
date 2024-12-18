import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import socket
import json
import threading

from base64 import b64decode


class Agent:
    def __init__(self, name, gateway_url):
        self.name = name
        self.gateway_url = gateway_url
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.signed_certificate = None

    def register(self):
        public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        response = requests.post(
            f"{self.gateway_url}/register",
            json={'name': self.name, 'public_key': public_key_pem.decode()}
        )
        if response.status_code == 200:
            self.signed_certificate = response.json()['signed_certificate']
            print(f"Agente {self.name} registado com sucesso!")
            print(self.signed_certificate)
        else:
            print("Registration failed:", response)

    def exchange_key(self, other_agent_name):
        requests.post(
            f"{self.gateway_url}/exchange_key",
            json={'name': self.name, 'other_agents': [other_agent_name]}
        )

    def send_message(self, recipient_name, message):
        response = requests.post(
            f"{self.gateway_url}/send_message",
            json={
                'sender': self.name,
                'recipient': recipient_name,
                'message': message
            }
        )
        if response.status_code == 200:
            print(f"Mensagem enviada para {recipient_name}: {message}")
        else:
            print("Falha ao enviar mensagem:", response.json())



    def menu(self):
        while True:
            print("Ações:")
            print("1. Registar na Gateway")
            print("2. Trocar chave com outro agente")
            print("3. Enviar mensagem para outro agente")
            print("4. Exit")
            choice = input("Selecionar ação: ")

            if choice == "1":
                self.register()
            elif choice == "2":
                other_agent = input("Insere o nome do outro agente: ")
                self.exchange_key(other_agent)
            elif choice == "3":
                recipient = input("Insere o nome do destinatário: ")
                message = input("Insere a mensagem: ")
                self.send_message(recipient, message)    
            elif choice == "4":
                print("A sair...")
                break
            else:
                print("Escolha inválida, tenta outra vez.")



def listen():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("localhost", 5001))  
    client_socket.send(agent_name.encode())  

    while True:
        data = client_socket.recv(1024)
        """key_received = data.decode()
        print(f"Chave recebida: {key_received}")"""
        if data:
            message = json.loads(data.decode())
            if 'message' in message:
                print(f"Mensagem recebida de {message['from']}: {message['message']}")
                continue
            elif 'encrypted_key' in message and 'iv' in message:
                encrypted_key = b64decode(message['encrypted_key'])
                iv = b64decode(message['iv'])

                # Decifra a chave de sessão
                session_key = agent.private_key.decrypt(
                    encrypted_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

            print(f"Chave de sessão decifrada: {session_key.hex()}")
            print(f"IV recebido: {iv.hex()}")
        else:
            print("Mensagem recebida num formmato desconhecido.")
        

if __name__ == "__main__":
    gateway_url = "http://localhost:5000"
    agent_name = input("Insere o nome deste agente: ")
    agent = Agent(agent_name, gateway_url)
    listener_thread = threading.Thread(target=listen, daemon=True)
    listener_thread.start()
    agent.menu()
    