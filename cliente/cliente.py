"""Cliente das máquinas: identifica quem está usando e avisa o gerenciador.

Todo evento (login/logout) é gravado primeiro na fila local (fila.json) e só sai
dela quando o servidor responde. Assim nada se perde se a rede ou o servidor
caírem. Enquanto há sessão aberta, sessao.json guarda o último "sinal de vida";
se a máquina for desligada sem logout, a saída é registrada com esse horário
na próxima vez que o cliente abrir.
"""
import configparser
import json
import os
import socket
import threading
import tkinter as tk
import urllib.error
import urllib.request
from datetime import datetime
from tkinter import messagebox

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_CONFIG = os.path.join(PASTA, 'config.ini')
ARQ_CONFIG_EXEMPLO = os.path.join(PASTA, 'config.example.ini')
ARQ_FILA = os.path.join(PASTA, 'fila.json')
ARQ_SESSAO = os.path.join(PASTA, 'sessao.json')
ARQ_LOG = os.path.join(PASTA, 'cliente.log')
FORMATO_DATA = '%Y-%m-%d %H:%M:%S'
INTERVALO_SINAL_MS = 60_000


def agora():
    return datetime.now().strftime(FORMATO_DATA)


def log(mensagem):
    with open(ARQ_LOG, 'a', encoding='utf-8') as f:
        f.write(f'{agora()} {mensagem}\n')


def ler_json(caminho, padrao):
    try:
        with open(caminho, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return padrao


def gravar_json(caminho, dados):
    # Grava em arquivo temporário e troca, para não corromper se a energia cair no meio.
    temporario = caminho + '.tmp'
    with open(temporario, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False)
    os.replace(temporario, caminho)


def carregar_config():
    cfg = configparser.ConfigParser()
    # O exemplo (versionado) dá os padrões; o config.ini da máquina (fora do git) sobrescreve.
    cfg.read([ARQ_CONFIG_EXEMPLO, ARQ_CONFIG], encoding='utf-8')
    return {
        'url': cfg.get('servidor', 'url', fallback='http://127.0.0.1:5000').rstrip('/'),
        'token': cfg.get('servidor', 'token', fallback='').strip(),
        'timeout': cfg.getfloat('servidor', 'timeout', fallback=5),
        'maquina': cfg.get('maquina', 'id', fallback='').strip() or socket.gethostname(),
        'bloqueio': cfg.get('cliente', 'bloqueio', fallback='nao').strip().lower()
                    in ('sim', 's', 'yes', 'true', '1'),
    }


class ErroRede(Exception):
    """Servidor inalcançável ou com erro interno: o evento deve ficar na fila."""


class Api:
    def __init__(self, url, token, timeout):
        self.url, self.token, self.timeout = url, token, timeout

    def enviar(self, caminho, dados):
        """Retorna (status, corpo) para respostas 2xx/4xx; levanta ErroRede no resto."""
        cabecalhos = {'Content-Type': 'application/json'}
        if self.token:
            cabecalhos['X-Token'] = self.token
        req = urllib.request.Request(self.url + caminho, data=json.dumps(dados).encode(),
                                     headers=cabecalhos, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, json.loads(resp.read() or b'{}')
        except urllib.error.HTTPError as e:
            if e.code >= 500:
                raise ErroRede(f'servidor respondeu {e.code}') from e
            try:
                corpo = json.loads(e.read() or b'{}')
            except ValueError:
                corpo = {}
            return e.code, corpo
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise ErroRede(str(e)) from e


class Fila:
    def __init__(self, api):
        self.api = api
        self.trava = threading.Lock()

    def adicionar(self, caminho, dados):
        with self.trava:
            eventos = ler_json(ARQ_FILA, [])
            eventos.append({'caminho': caminho, 'dados': dados})
            gravar_json(ARQ_FILA, eventos)

    def pendentes(self):
        return len(ler_json(ARQ_FILA, []))

    def enviar(self):
        """Envia os eventos em ordem e para no primeiro erro de rede.

        Eventos recusados pelo servidor (4xx) são descartados e anotados no log,
        porque reenviar não mudaria a resposta. Retorna quantos ficaram na fila.
        """
        with self.trava:
            eventos = ler_json(ARQ_FILA, [])
            while eventos:
                evento = eventos[0]
                try:
                    status, corpo = self.api.enviar(evento['caminho'], evento['dados'])
                except ErroRede:
                    break
                if status == 401:
                    # Token errado é problema de configuração, não do evento: mantém na fila
                    # para ser enviado quando o config.ini for corrigido.
                    log('servidor recusou o token; eventos mantidos na fila')
                    break
                if status >= 400:
                    log(f'evento descartado ({status} {corpo.get("erro", "")}): {evento}')
                eventos.pop(0)
                gravar_json(ARQ_FILA, eventos)
            return len(eventos)


class Cliente:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.fila = Fila(Api(config['url'], config['token'], config['timeout']))
        self.sessao = None
        self.envio = None

        root.title('Controle de uso')
        root.protocol('WM_DELETE_WINDOW', self.ao_fechar)
        # O Tk no Windows dispara este protocolo quando o sistema vai desligar ou fazer logoff.
        root.protocol('WM_SAVE_YOURSELF', self.ao_desligar)

        self.recuperar_sessao_perdida()
        self.tela_login()
        self.enviar_fila_em_segundo_plano()
        root.after(INTERVALO_SINAL_MS, self.sinal_de_vida)

    # ---- sessão e fila ----

    def recuperar_sessao_perdida(self):
        anterior = ler_json(ARQ_SESSAO, None)
        if anterior:
            log(f'sessão sem logout encontrada; saída registrada em {anterior["ultimo_sinal"]}')
            self.fila.adicionar('/api/logout', {'maquina': self.config['maquina'],
                                                'horario': anterior['ultimo_sinal']})
            os.remove(ARQ_SESSAO)

    def enviar_fila_em_segundo_plano(self):
        # A thread só recebe a fila: nada do Tk pode ser usado fora da thread principal.
        if self.envio is None or not self.envio.is_alive():
            self.envio = threading.Thread(target=self.fila.enviar, daemon=True)
            self.envio.start()

    def sinal_de_vida(self):
        if self.sessao:
            self.sessao['ultimo_sinal'] = agora()
            gravar_json(ARQ_SESSAO, self.sessao)
        self.enviar_fila_em_segundo_plano()
        self.atualizar_status()
        self.root.after(INTERVALO_SINAL_MS, self.sinal_de_vida)

    def registrar_logout(self):
        if not self.sessao:
            return
        self.fila.adicionar('/api/logout', {'maquina': self.config['maquina'], 'horario': agora()})
        self.sessao = None
        if os.path.exists(ARQ_SESSAO):
            os.remove(ARQ_SESSAO)

    # ---- eventos da janela ----

    def entrar(self):
        nome = self.campos['nome'].get().strip()
        curso = self.campos['curso'].get().strip()
        prontuario = self.campos['prontuario'].get().strip().upper()
        if not (nome and curso and prontuario):
            messagebox.showwarning('Controle de uso', 'Preencha nome, curso e prontuário.', parent=self.root)
            return

        dados = {'prontuario': prontuario, 'nome': nome, 'curso': curso,
                 'maquina': self.config['maquina'], 'horario': agora()}
        self.root.config(cursor='watch')
        self.root.update_idletasks()
        try:
            # Eventos antigos precisam chegar antes deste, então só envia direto se a fila esvaziou.
            if self.fila.enviar() == 0:
                try:
                    status, corpo = self.fila.api.enviar('/api/login', dados)
                except ErroRede:
                    self.fila.adicionar('/api/login', dados)
                else:
                    if status >= 400:
                        if status == 401:
                            mensagem = ('Este computador está com a configuração incorreta '
                                        '(token do servidor). Avise a equipe da CTI.')
                        else:
                            mensagem = corpo.get('erro', f'Erro {status}')
                        messagebox.showerror('Controle de uso', mensagem, parent=self.root)
                        return
            else:
                self.fila.adicionar('/api/login', dados)
        finally:
            self.root.config(cursor='')

        self.sessao = {'nome': nome, 'prontuario': prontuario, 'curso': curso,
                       'entrada': dados['horario'], 'ultimo_sinal': dados['horario']}
        gravar_json(ARQ_SESSAO, self.sessao)
        self.tela_sessao()

    def sair(self):
        self.registrar_logout()
        if self.config['bloqueio']:
            self.enviar_fila_em_segundo_plano()
            self.tela_login()
        else:
            self.fila.enviar()  # se falhar, o logout fica na fila para a próxima abertura
            self.root.destroy()

    def ao_fechar(self):
        if self.sessao:
            if messagebox.askyesno('Controle de uso', 'Encerrar sua sessão?', parent=self.root):
                self.sair()
        elif not self.config['bloqueio']:
            self.root.destroy()
        # Com bloqueio ativo, a tela de login não fecha.

    def ao_desligar(self):
        self.registrar_logout()
        self.fila.enviar()  # tentativa rápida; se falhar, o evento já está salvo na fila
        self.root.destroy()

    # ---- telas ----

    def limpar(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def atualizar_status(self):
        if getattr(self, 'status', None) and self.status.winfo_exists():
            n = self.fila.pendentes()
            self.status.config(text=f'{n} registro(s) aguardando o servidor' if n else '')

    def tela_login(self):
        self.limpar()
        self.root.deiconify()
        bloqueio = self.config['bloqueio']
        self.root.attributes('-fullscreen', bloqueio)
        self.root.attributes('-topmost', bloqueio)
        if not bloqueio:
            self.root.geometry('')
            self.root.resizable(False, False)

        quadro = tk.Frame(self.root, padx=30, pady=30)
        if bloqueio:
            quadro.place(relx=0.5, rely=0.5, anchor='center')
        else:
            quadro.pack()

        tk.Label(quadro, text='Identifique-se para usar este computador',
                 font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        self.campos = {}
        for linha, (chave, rotulo) in enumerate([('nome', 'Nome'), ('curso', 'Curso'),
                                                 ('prontuario', 'Prontuário')], start=1):
            tk.Label(quadro, text=rotulo, font=('Segoe UI', 11)).grid(row=linha, column=0, sticky='e', pady=4)
            entrada = tk.Entry(quadro, width=32, font=('Segoe UI', 11))
            entrada.grid(row=linha, column=1, pady=4, padx=(8, 0))
            self.campos[chave] = entrada
        tk.Button(quadro, text='Entrar', width=14, font=('Segoe UI', 11),
                  command=self.entrar).grid(row=4, column=0, columnspan=2, pady=(15, 5))
        tk.Label(quadro, text=f'Máquina: {self.config["maquina"]}', fg='gray').grid(row=5, column=0, columnspan=2)
        self.status = tk.Label(quadro, fg='#b26b00')
        self.status.grid(row=6, column=0, columnspan=2)
        self.atualizar_status()

        self.root.bind('<Return>', lambda _e: self.entrar())
        self.campos['nome'].focus_set()
        if bloqueio:
            self.manter_em_primeiro_plano()

    def manter_em_primeiro_plano(self):
        if self.sessao is None and self.root.winfo_exists():
            self.root.lift()
            self.root.after(1000, self.manter_em_primeiro_plano)

    def tela_sessao(self):
        self.limpar()
        self.root.unbind('<Return>')
        self.root.attributes('-fullscreen', False)
        self.root.attributes('-topmost', False)
        self.root.resizable(False, False)

        quadro = tk.Frame(self.root, padx=20, pady=15)
        quadro.pack()
        tk.Label(quadro, text=f'{self.sessao["nome"]} ({self.sessao["prontuario"]})',
                 font=('Segoe UI', 11, 'bold')).pack()
        tk.Label(quadro, text=f'Em uso desde {self.sessao["entrada"][11:16]}').pack()
        tk.Button(quadro, text='Sair (encerrar sessão)', command=self.sair).pack(pady=(10, 0))
        self.status = tk.Label(quadro, fg='#b26b00')
        self.status.pack()
        self.atualizar_status()
        self.root.geometry('')
        self.root.iconify()


def ja_esta_aberto():
    """Impede duas cópias do cliente na mesma máquina, que registrariam sessões duplicadas."""
    if os.name != 'nt':
        return False
    import ctypes
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    # O handle precisa continuar aberto enquanto o programa roda.
    global _TRAVA_INSTANCIA
    _TRAVA_INSTANCIA = kernel32.CreateMutexW(None, False, 'Global\\ControleDeUsoBiblioteca')
    # 183 = já existe; 5 = existe, criado por outra conta do Windows.
    return ctypes.get_last_error() in (183, 5)


if __name__ == '__main__':
    raiz = tk.Tk()
    if ja_esta_aberto():
        raiz.withdraw()
        messagebox.showinfo('Controle de uso', 'O controle de uso já está aberto neste computador.\n'
                            'Procure a janela "Controle de uso" na barra de tarefas.')
        raiz.destroy()
    else:
        Cliente(raiz, carregar_config())
        raiz.mainloop()
