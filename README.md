# 🖥️ Library Management System — Controle de Acesso às Máquinas

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

- [ ] API que recebe os registros de entrada e saída enviados pelos clientes
- [ ] Banco de dados com usuários, máquinas e sessões
- [ ] Painel web acessado pelos administradores da biblioteca pela rede interna
- [ ] Login dos administradores (acesso restrito)
- [ ] Sessões ativas (quem está usando cada máquina agora)
- [ ] Cadastro das máquinas gerenciadas
- [ ] Histórico de acessos com filtros (data, curso, prontuário, máquina)
- [ ] Relatório com nome, curso, prontuário, máquina, entrada e saída
- [ ] Exportar relatório em PDF / CSV / Excel
- [ ] Backup do banco de dados

### 2. Cliente (máquina gerenciada — biblioteca)

Programa instalado em cada computador de uso da biblioteca. É responsável por:

- [ ] Abrir automaticamente ao iniciar a sessão do computador
- [ ] Tela de login em que o usuário informa nome, curso e prontuário
- [ ] Bloquear o uso da máquina até o login ser feito
- [ ] Enviar ao servidor da CTI o login (prontuário + identificação da máquina + horário de entrada)
- [ ] Botão de logout que envia o horário de saída
- [ ] Registrar a saída também ao desligar/reiniciar ou encerrar a sessão do Windows/Linux
- [ ] Guardar os registros localmente se o servidor estiver fora do ar e enviar depois

### Administradores (biblioteca)

Não precisam instalar nada: acessam o painel do gerenciador pelo navegador (ex.: `http://<servidor-cti>:5000`) a partir de um computador da biblioteca.

## Dados registrados

| Campo | Descrição |
|---|---|
| Nome | Nome completo do usuário |
| Curso | Curso do usuário |
| Prontuário | Número de prontuário (identificação no IFSP) |
| Máquina | Identificação do computador utilizado |
| Entrada | Data e hora do login |
| Saída | Data e hora do logout |

## Tecnologias

| Parte | Tecnologias |
|---|---|
| Gerenciador | Python 3, Flask, SQL (SQLite / MySQL), HTML, CSS, Jinja2 |
| Cliente | Python 3 (interface com Tkinter), requests |

## Banco de dados (previsto)

```sql
CREATE TABLE usuarios (
    prontuario  VARCHAR(20) PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    curso       VARCHAR(100) NOT NULL
);

CREATE TABLE maquinas (
    id          VARCHAR(50) PRIMARY KEY,   -- ex.: hostname
    descricao   VARCHAR(100)
);

CREATE TABLE administradores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario     VARCHAR(50) UNIQUE NOT NULL,
    senha_hash  VARCHAR(255) NOT NULL
);

CREATE TABLE sessoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prontuario  VARCHAR(20) NOT NULL REFERENCES usuarios(prontuario),
    maquina_id  VARCHAR(50) NOT NULL REFERENCES maquinas(id),
    entrada     DATETIME NOT NULL,
    saida       DATETIME
);
```

## Estrutura (prevista)

```
library-management-system/
├── gerenciador/            # servidor principal (CTI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── api.py          # rotas que recebem dados dos clientes
│   │   ├── painel.py       # rotas do painel dos administradores
│   │   ├── relatorios.py
│   │   ├── templates/
│   │   └── static/
│   ├── database/
│   │   └── schema.sql
│   ├── requirements.txt
│   └── run.py
├── cliente/                # programa das máquinas da biblioteca
│   ├── cliente.py          # tela de login e comunicação com a API
│   ├── config.ini          # endereço do servidor da CTI e ID da máquina
│   └── requirements.txt
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
python run.py
```

### Cliente (em cada máquina da biblioteca)

```bash
cd library-management-system/cliente
pip install -r requirements.txt
# configure o endereço do servidor da CTI em config.ini
python cliente.py
```

### Painel dos administradores (biblioteca)

Abra no navegador: `http://<ip-do-servidor-cti>:5000`

## Autora

**Maria Clara Pastor** — Análise e Desenvolvimento de Sistemas, IFSP Campus Jacareí
