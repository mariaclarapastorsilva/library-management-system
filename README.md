# 🖥️ Library Management System - Controle de Acesso às Máquinas

Sistema para registrar o login dos usuários nos computadores da biblioteca e gerar relatórios de uso para os administradores.

Desenvolvido com **Python**, **Flask** e **SQL**.

## Sobre o projeto

Ao usar uma máquina da biblioteca, o usuário faz login informando seus dados. O sistema registra automaticamente o **horário de entrada** e, ao encerrar a sessão, o **horário de saída**. Os dados ficam no **servidor central da CTI**, e os **administradores da biblioteca** acessam um painel para consultar e exportar relatórios.

## Arquitetura

O projeto é dividido em **duas partes** — o **gerenciador** (servidor) e o **cliente** (máquina gerenciada) — distribuídas em dois locais:

```
              BIBLIOTECA                                       CTI
┌──────────────────────────────────┐            ┌──────────────────────────────┐
│  CLIENTE (máquina 01)            │──┐         │   GERENCIADOR                │
│  CLIENTE (máquina 02)            │──┤  HTTP   │   (servidor principal)       │
│  CLIENTE (máquina N)             │──┼───────▶ │   - API Flask                │
│                                  │  │  rede   │   - Banco de dados SQL       │
│  ADMINISTRADOR (navegador) ──────│──┘         │   - Painel web + relatórios  │
└──────────────────────────────────┘            └──────────────────────────────┘
```

| Onde | O que roda | Quem usa |
|---|---|---|
| **CTI** | Servidor principal (gerenciador): API, banco de dados e painel web | Equipe da CTI (manutenção) |
| **Biblioteca** | Cliente em cada máquina de uso | Usuários (alunos/servidores) |
| **Biblioteca** | Painel web acessado pelo navegador | Administradores da biblioteca |

### 1. Gerenciador (servidor — CTI)

Instalado no servidor principal da CTI. É responsável por:

- [x] API que recebe os registros de entrada e saída enviados pelos clientes
- [x] Banco de dados com usuários, máquinas e sessões
- [x] Painel web acessado pelos administradores da biblioteca pela rede interna
- [x] Login dos administradores (acesso restrito, senha com hash)
- [x] Sessões ativas (quem está usando cada máquina agora), com opção de encerrar
- [x] Cadastro das máquinas gerenciadas (com opção de desativar)
- [x] Histórico de acessos com filtros (data, curso, prontuário/nome, máquina)
- [x] Relatório com nome, curso, prontuário, máquina, entrada, saída e duração
- [x] Exportar relatório em PDF / CSV / Excel
- [x] Backup do banco de dados

### 2. Cliente (máquina gerenciada — biblioteca)

Programa instalado em cada computador de uso da biblioteca (Windows). É responsável por:

- [x] Abrir automaticamente ao iniciar a sessão do computador
- [x] Tela de login em que o usuário informa nome, curso e prontuário
- [x] Bloquear o uso da máquina até o login ser feito (ver [limites](#limites-do-bloqueio-de-tela))
- [x] Enviar ao servidor da CTI o login (prontuário + identificação da máquina + horário de entrada)
- [x] Botão de logout que envia o horário de saída
- [x] Registrar a saída também ao desligar/reiniciar ou encerrar a sessão do Windows
- [x] Guardar os registros localmente se o servidor estiver fora do ar e enviar depois
- [x] Impedir que duas cópias do cliente rodem na mesma máquina

### Administradores (biblioteca)

Não precisam instalar nada: acessam o painel do gerenciador pelo navegador (`http://<servidor-cti>:5000/painel/`) a partir de um computador da biblioteca.

## Dados registrados

| Campo | Descrição |
|---|---|
| Nome | Nome completo do usuário |
| Curso | Curso do usuário |
| Prontuário | Número de prontuário (identificação no IFSP) |
| Máquina | Identificação do computador utilizado (hostname) |
| Entrada | Data e hora do login |
| Saída | Data e hora do logout |

## Tecnologias

| Parte | Tecnologias |
|---|---|
| Gerenciador | Python 3, Flask, SQLite, HTML, CSS, Jinja2, openpyxl (Excel), reportlab (PDF), waitress (produção) |
| Cliente | Python 3, Tkinter, só biblioteca padrão (não precisa de `pip install`) |

## Banco de dados

Definido em [`gerenciador/database/schema.sql`](gerenciador/database/schema.sql):

```sql
CREATE TABLE usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prontuario  TEXT NOT NULL UNIQUE,
    nome        TEXT NOT NULL,
    curso       TEXT NOT NULL,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE maquinas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    identificador  TEXT NOT NULL UNIQUE,      -- hostname enviado pelo cliente
    descricao      TEXT NOT NULL DEFAULT '',
    ativa          INTEGER NOT NULL DEFAULT 1,
    criado_em      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE sessoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    maquina_id  INTEGER NOT NULL REFERENCES maquinas(id),
    entrada     TEXT NOT NULL,                -- 'AAAA-MM-DD HH:MM:SS'
    saida       TEXT                          -- NULL enquanto a sessão está aberta
);

CREATE TABLE administradores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario     TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
```

## Estrutura

```
library-management-system/
├── gerenciador/                 # servidor principal (CTI)
│   ├── app/
│   │   ├── __init__.py          # cria o app Flask
│   │   ├── db.py                # conexão com o SQLite
│   │   ├── api.py               # rotas que recebem dados dos clientes
│   │   ├── painel.py            # rotas do painel dos administradores
│   │   ├── relatorios.py        # exportação CSV / Excel / PDF
│   │   └── templates/
│   ├── database/
│   │   ├── schema.sql
│   │   └── criar_banco.py
│   ├── criar_admin.py           # cria administrador / troca senha
│   ├── backup.py                # cópia do banco
│   ├── run.py                   # servidor de desenvolvimento
│   ├── servir.py                # servidor de produção (waitress)
│   └── requirements.txt
├── cliente/                     # programa das máquinas da biblioteca
│   ├── cliente.py               # tela de login e comunicação com a API
│   ├── config.example.ini       # modelo do config.ini (endereço do servidor e ID da máquina)
│   └── instalar_inicio_automatico.bat
└── README.md
```

## Como executar

### Gerenciador (no servidor da CTI)

```bash
git clone https://github.com/mariaclarapastorsilva/library-management-system.git
cd library-management-system/gerenciador
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python criar_admin.py admin   # cria o primeiro administrador (pede a senha)
python run.py                 # desenvolvimento: só acessível em http://127.0.0.1:5000
```

O banco (`database/biblioteca.db`) é criado automaticamente na primeira execução.

### Cliente (em cada máquina da biblioteca)

```bash
cd library-management-system/cliente
copy config.example.ini config.ini   # e ajuste o endereço do servidor da CTI
python cliente.py
```

Opções do `config.ini`:

| Seção / chave | Para que serve |
|---|---|
| `[servidor] url` | Endereço do gerenciador, ex.: `http://10.0.0.5:5000` |
| `[servidor] token` | Igual à variável `API_TOKEN` do servidor (vazio se não usar) |
| `[maquina] id` | Identificação da máquina no painel; vazio = hostname do Windows |
| `[cliente] bloqueio` | `sim` = tela de login em tela cheia que não fecha até alguém entrar |

Para o cliente abrir sozinho no logon do Windows, rode `instalar_inicio_automatico.bat` (ou `instalar_inicio_automatico.bat todos`, como administrador, para todas as contas).

### Painel dos administradores (biblioteca)

Abra no navegador: `http://<ip-do-servidor-cti>:5000/painel/`

## API

| Rota | Corpo JSON | Respostas |
|---|---|---|
| `POST /api/login` | `prontuario`, `nome`, `curso`, `maquina`, `horario` (opcional) | 201 sessão aberta · 400 campos faltando · 403 máquina desativada |
| `POST /api/logout` | `maquina`, `horario` (opcional) | 200 sessão fechada · 404 nenhuma sessão aberta |

```bash
curl -X POST http://127.0.0.1:5000/api/login -H "Content-Type: application/json" \
     -d '{"prontuario":"SP123456","nome":"Ana","curso":"Informática","maquina":"LAB-01"}'

curl -X POST http://127.0.0.1:5000/api/logout -H "Content-Type: application/json" \
     -d '{"maquina":"LAB-01"}'
```

- `horario` (`AAAA-MM-DD HH:MM:SS`) só é enviado pelo cliente para eventos que ficaram na fila offline. Assim o registro guarda a hora real, e não a hora do reenvio.
- O usuário é criado no primeiro login. Se nome ou curso mudarem, o cadastro é atualizado.
- Uma máquina desconhecida é cadastrada sozinha no primeiro login.
- Se a máquina já tem uma sessão aberta, ela é fechada antes de abrir a nova.
- Se a variável `API_TOKEN` estiver definida no servidor, os clientes precisam enviar o cabeçalho `X-Token`.

## Robustez do cliente

- **Fila local (`fila.json`)**: login e logout são gravados primeiro no disco e só saem da fila quando o servidor responde. Com o servidor fora do ar, a máquina continua utilizável e os eventos são reenviados a cada minuto.
- **Desligamento**: o cliente registra o logout quando o Windows avisa que vai desligar. Enquanto há sessão aberta, ele também grava um "sinal de vida" por minuto em `sessao.json`. Se a máquina cair sem logout (ex.: queda de energia), a saída é registrada com o horário do último sinal na próxima vez que o cliente abrir.
- **Eventos recusados** pelo servidor (ex.: máquina desativada) são descartados e anotados em `cliente.log`.

### Limites do bloqueio de tela

`bloqueio = sim` deixa a tela de login em tela cheia, sempre por cima, e a janela não pode ser fechada. Mas um programa Tkinter não consegue bloquear Ctrl+Alt+Del, a tecla Windows nem o Gerenciador de Tarefas. Para um bloqueio de verdade, combine com Política de Grupo (GPO) na conta dos alunos, desabilitando o Gerenciador de Tarefas e restringindo o que pode ser executado.

## Implantação na CTI

1. **Servidor de produção**: `python servir.py` (waitress, porta 5000). Variáveis opcionais: `HOST`, `PORT`, `DATABASE`, `SECRET_KEY`, `API_TOKEN`. Sem `SECRET_KEY`, uma chave é gerada e guardada em `gerenciador/instance/secret.key`.
2. **Iniciar com o Windows**: crie uma tarefa no Agendador de Tarefas com o gatilho "Ao iniciar o sistema", a ação `python servir.py` e "Iniciar em" apontando para a pasta `gerenciador`. Outra opção é registrar como serviço com o [NSSM](https://nssm.cc).
3. **Firewall**: libere a porta só para a rede interna (ajuste a faixa de IPs):
   ```
   netsh advfirewall firewall add rule name="Controle biblioteca" dir=in action=allow protocol=TCP localport=5000 remoteip=10.0.0.0/8
   ```
4. **Backup diário** às 22h, mantendo os 30 mais recentes:
   ```
   schtasks /Create /SC DAILY /ST 22:00 /TN "Backup controle biblioteca" ^
     /TR "python C:\caminho\gerenciador\backup.py D:\backups\biblioteca 30"
   ```
   O backup pode rodar com o servidor ligado. De vez em quando, copie a pasta de backups para outra máquina.

> ⚠️ O banco, os backups, os relatórios exportados e os arquivos `fila.json`/`sessao.json` do cliente contêm nome, curso e prontuário (LGPD) e estão no `.gitignore`. Não versione esses arquivos.

## Autora

**Maria Clara Pastor** — Estagiária da CTI, IFSP Campus Jacareí
