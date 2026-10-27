# Roteiro de implantação

Passo a passo para colocar o controle de acesso em uso: o servidor na CTI e o cliente nas máquinas da biblioteca.

O sistema já está pronto e testado. Os testes cobriram servidor fora do ar, queda de energia, 40 máquinas acessando ao mesmo tempo, bloqueio de tela e relatórios. Falta só instalar no ambiente real.

---

## 1. Decisões antes de começar

| # | Decisão | Quem decide | Sugestão / situação |
|---|---|---|---|
| 1 | Qual máquina da CTI será o servidor | CTI | ✅ **Decidido:** servidor na CTI com **IP fixo**. Falta saber qual é o IP, que vai no `config.ini` dos clientes |
| 2 | Faixas de IPs das máquinas da biblioteca **e dos administradores** | CTI | Necessárias para liberar o firewall só para quem usa o sistema (seção 2.6) |
| 3 | Usar token na API (`API_TOKEN`) | CTI | ✅ **Decidido: sim.** Impede que qualquer computador da rede registre sessões falsas. A CTI gera o token na instalação (seção 2.2) |
| 4 | Quem serão os administradores do painel | Biblioteca | ✅ **Decidido:** vários administradores, **cada um com login próprio**, acessando de máquinas diferentes. Falta a lista de nomes para criar os usuários (seção 2.3) |
| 5 | Senha de manutenção dos clientes | CTI | ✅ **Decidido: sim.** Conhecida só pela equipe da CTI, escolhida e configurada na instalação (seção 3.2) |
| 6 | Ligar o bloqueio de tela | CTI + Biblioteca | ✅ **Decidido: sim, a identificação é obrigatória.** `bloqueio = sim` em todas as máquinas, junto com a GPO na conta dos alunos (seção 5) |
| 7 | Por quanto tempo guardar os registros | Biblioteca | ⏳ **Prazo para a reunião com a biblioteca.** ✅ Já decidido: cada registro é mantido **completo** (nome, curso e prontuário) ou **apagado por inteiro**, sem guarda parcial. Sugestão de prazo: 1 ano (LGPD, seção 6). Na dúvida, consultar o Encarregado de Dados do IFSP. A limpeza já está pronta (seção 6.2) |
| 8 | Aviso aos usuários sobre o registro dos dados | Biblioteca | ⏳ **Para a reunião com a biblioteca.** Sugestão: texto curto na tela de login e/ou cartaz na biblioteca (LGPD). O aviso na tela já está pronto (seção 6.1) |
| 9 | Licença e visibilidade do repositório no GitHub | Supervisão | ✅ **Decidido:** licença **MIT**. O repositório está público |

---

## 2. Servidor (máquina da CTI)

Requisitos: Windows com **Python 3.10 ou mais novo**. No instalador, escolha **Customize installation** e marque **Install Python for all users** e **Add Python to environment variables**. Sem isso, as tarefas agendadas (que rodam como sistema) não encontram o Python.

Anote o caminho completo do Python, que vai ser usado nas tarefas agendadas:

```bat
where python
```

Normalmente é `C:\Program Files\Python312\python.exe`.

### 2.1 Instalar

```bat
cd C:\
git clone https://github.com/mariaclarapastorsilva/library-management-system.git controle-biblioteca
cd controle-biblioteca\gerenciador
python -m pip install -r requirements.txt
```

Sem git, baixe o ZIP pelo GitHub (**Code → Download ZIP**) e extraia em `C:\controle-biblioteca`.

### 2.2 Configurar (como administrador)

Gere um token aleatório e grave como variável do sistema:

```bat
python -c "import secrets; print(secrets.token_urlsafe(24))"
setx /M API_TOKEN "COLE_O_TOKEN_AQUI"
```

Guarde o token: ele vai no `config.ini` de cada máquina da biblioteca. Para valer, feche e abra o terminal de novo.

A chave secreta do painel (`SECRET_KEY`) é gerada sozinha na primeira execução, em `gerenciador\instance\secret.key`.

### 2.3 Criar os administradores do painel

```bat
python criar_admin.py nome.do.usuario
```

O comando pede a senha, com pelo menos 8 caracteres. Repita para cada administrador. Rodar de novo com o mesmo usuário troca a senha.

### 2.4 Testar

```bat
python servir.py
```

Abra `http://localhost:5000/painel/` no navegador do servidor e entre com um administrador. Depois pare o servidor com **Ctrl+C**.

### 2.5 Iniciar junto com o Windows

No **Agendador de Tarefas → Criar Tarefa**:

- **Geral:** "Executar estando o usuário conectado ou não" e "Executar com privilégios mais altos".
- **Disparadores:** "Ao iniciar o sistema".
- **Ações:** programa = caminho completo do Python (ex.: `C:\Program Files\Python312\python.exe`), argumentos `servir.py`, **Iniciar em** `C:\controle-biblioteca\gerenciador`.
- **Configurações:** desmarcar "Interromper a tarefa se ela for executada por mais de...".

Reinicie a máquina e confira se o painel abre sem ninguém fazer login.

### 2.6 Liberar o firewall

Ajuste `remoteip` para as faixas da biblioteca **e das máquinas dos administradores** (decisão 2). Várias faixas vão separadas por vírgula:

```bat
netsh advfirewall firewall add rule name="Controle biblioteca" dir=in action=allow protocol=TCP localport=5000 remoteip=10.120.30.0/24,10.120.40.0/24
```

Os IPs acima são só exemplo. Se as faixas ainda não estiverem definidas, `remoteip=10.0.0.0/8` libera toda a rede interna.

**Teste:** abra `http://IP_DO_SERVIDOR:5000/painel/` num computador da biblioteca **e** na máquina de cada administrador. Se a tela de login aparecer, a rede está ok.

### 2.7 Backup diário

```bat
mkdir D:\backups\biblioteca
schtasks /Create /SC DAILY /ST 22:00 /RU SYSTEM /TN "Backup controle biblioteca" ^
  /TR "\"C:\Program Files\Python312\python.exe\" C:\controle-biblioteca\gerenciador\backup.py D:\backups\biblioteca 30"
```

O backup mantém as 30 cópias mais recentes e pode rodar com o servidor ligado. De vez em quando, copie a pasta para outra máquina ou para o drive institucional.

**Para restaurar um backup:** pare o servidor, copie o arquivo escolhido por cima de `gerenciador\database\biblioteca.db`, apague `biblioteca.db-wal` e `biblioteca.db-shm` se existirem, e inicie o servidor de novo.

---

## 3. Cliente (cada máquina da biblioteca)

Requisitos: **Python 3.10 ou mais novo**, instalado **para todos os usuários** e com **Add Python to environment variables** marcado (mesmas opções da seção 2). Assim a conta dos alunos encontra o Python no logon. O cliente não precisa de `pip install`.

### 3.1 Copiar e configurar

1. Copie a pasta `cliente` para `C:\controle-biblioteca\cliente`.
2. Dentro dela, copie `config.example.ini` para `config.ini` e preencha:

```ini
[servidor]
url = http://IP_DO_SERVIDOR:5000
token = O_MESMO_TOKEN_DO_SERVIDOR

[maquina]
; vazio = usa o nome do computador
id =

[cliente]
bloqueio = sim
senha_manutencao = (ver 3.2)
aviso = (texto decidido com a biblioteca, ver seção 6)
```

### 3.2 Senha de manutenção

```bat
cd C:\controle-biblioteca\cliente
python cliente.py --gerar-senha
```

Cole a linha gerada no `config.ini`. Ela pode ser **a mesma linha em todas as máquinas**: gere uma vez e copie. Com a senha configurada, **Ctrl+Shift+F12** fecha o cliente em qualquer tela.

### 3.3 Testar

```bat
python cliente.py
```

1. Faça login com dados de teste e confira a sessão no painel ("Sessões ativas").
2. Clique em **Sair** e confira no "Histórico".
3. Aperte **Ctrl+Shift+F12**, digite a senha e confira se o cliente fecha.

### 3.4 Abrir sozinho no logon (como administrador)

```bat
instalar_inicio_automatico.bat todos
```

Faça logoff e login na conta dos alunos: a tela de identificação deve aparecer sozinha.

### 3.5 Proteger a pasta

O aluno não deve conseguir alterar o `config.ini` nem o `cliente.py`. Mas o cliente, que roda na conta do aluno, precisa **criar e substituir arquivos** na pasta: `fila.json`, `sessao.json`, `cliente.log` e arquivos temporários `.tmp`.

Uma forma de fazer isso nas permissões NTFS da pasta (**Propriedades → Segurança → Avançado**, desativando a herança):

- **Administradores e SYSTEM:** Controle total.
- **Grupo dos alunos**, duas entradas:
  - "Ler e executar", aplicado a **esta pasta, subpastas e arquivos**.
  - "Criar arquivos / gravar dados", aplicado a **somente esta pasta**. Se valer para os arquivos, essa mesma permissão vira "alterar conteúdo" e o aluno poderia editar o `config.ini`.
- **Não** dê "Excluir subpastas e arquivos" aos alunos: essa permissão deixaria apagar qualquer arquivo da pasta, inclusive o `config.ini`.
- **PROPRIETÁRIO CRIADOR:** "Modificar", aplicado a **somente arquivos**. Assim, os arquivos que o próprio cliente cria (fila, sessão, log) podem ser atualizados e substituídos por ele, e os arquivos copiados pela CTI continuam só para leitura.

Copie o `config.ini` e o `cliente.py` usando uma conta de administrador, para que o dono deles seja a CTI.

Depois de ajustar, **teste na conta de um aluno**: login, logout e o caso do servidor fora do ar, que precisa gravar a fila. Se várias contas de aluno diferentes usarem a mesma máquina, teste também a troca de conta.

---

## 4. Checklist de validação

- [ ] Painel abre a partir de um computador da biblioteca e da máquina de cada administrador
- [ ] Cada administrador entra com o próprio usuário e senha
- [ ] Login no cliente aparece em "Sessões ativas"
- [ ] Logout aparece no "Histórico" com o horário certo
- [ ] **Servidor fora do ar:** pare o servidor, faça login e logout no cliente, ligue o servidor de novo. Em até 1 minuto a sessão aparece no histórico com os horários reais
- [ ] **Queda de energia:** com sessão aberta, desligue a máquina no botão. Ao religar, a sessão é fechada sozinha
- [ ] Tela de bloqueio não fecha com Alt+F4 e volta se minimizada (Windows+D)
- [ ] Ctrl+Shift+F12 com a senha fecha o cliente
- [ ] Relatórios CSV, Excel e PDF baixam e abrem corretamente
- [ ] Backup gerado na pasta configurada no dia seguinte

---

## 5. Política de Grupo (GPO) para a conta dos alunos

A identificação é **obrigatória** (decisão 6). O bloqueio do cliente impede fechar a tela com Alt+F4 ou minimizá-la, mas não impede Ctrl+Alt+Del, a tecla Windows nem o Gerenciador de Tarefas: isso só é possível pelo Windows. Sem as regras abaixo, um aluno que conheça esses atalhos consegue fechar o cliente à força. Para a conta dos alunos:

- Remover o Gerenciador de Tarefas (*Configuração do Usuário → Modelos Administrativos → Sistema → Opções Ctrl+Alt+Del*).
- Impedir acesso ao Prompt de Comando e ao Editor do Registro.
- Restringir a pasta `C:\controle-biblioteca` (ver 3.5).

---

## 6. Dados pessoais (LGPD)

O sistema guarda **nome, curso e prontuário** dos usuários, com horários de uso.

- Esses dados ficam **só no servidor da CTI** e nos backups, e nunca vão para o GitHub (estão no `.gitignore`).
- Os relatórios exportados também têm dados pessoais: guarde-os em local com acesso restrito.
- Defina por quanto tempo os registros serão mantidos (decisão 7) e informe os usuários (decisão 8).

As duas funções já estão prontas no sistema. Depois da reunião com a biblioteca, basta configurar.

### 6.1 Aviso aos usuários (decisão 8)

No `config.ini` de cada máquina, seção `[cliente]`:

```ini
aviso = Seus dados (nome, curso, prontuário e horários de uso) são registrados
    pela biblioteca para controle de uso dos computadores.
```

O texto aparece embaixo do formulário de login. Para continuar numa nova linha, comece a linha seguinte com espaços. Vazio = nenhum aviso.

### 6.2 Limpeza dos registros antigos (decisão 7)

O script `limpar_registros.py` **apaga por completo** as sessões mais antigas que o prazo decidido. Enquanto um registro é mantido, ele fica inteiro (nome, curso, prontuário, máquina e horários). Não há guarda parcial nem anonimização.

Os alunos que ficarem sem nenhuma sessão saem do cadastro, e o arquivo do banco é reescrito para que os dados apagados não fiquem no disco.

**Primeiro, veja o que seria feito** (nada é alterado sem `--confirmar`):

```bat
cd C:\controle-biblioteca\gerenciador
python limpar_registros.py --meses 12
```

**Depois, faça um backup e rode de verdade:**

```bat
python backup.py D:\backups\biblioteca 30
python limpar_registros.py --meses 12 --confirmar
```

**Agende para todo dia 1º do mês**, às 23h, depois do backup diário:

```bat
schtasks /Create /SC MONTHLY /D 1 /ST 23:00 /RU SYSTEM /TN "Limpeza controle biblioteca" ^
  /TR "\"C:\Program Files\Python312\python.exe\" C:\controle-biblioteca\gerenciador\limpar_registros.py --meses 12 --confirmar"
```

Troque `12` pelo prazo decidido, em meses.

Se o script avisar que há **sessões abertas desde antes do prazo**, são sessões de máquinas que sumiram sem fechar a sessão. Encerre-as no painel (**Sessões ativas → Encerrar**): na próxima limpeza elas serão apagadas.

Os backups também contêm dados pessoais, mas se renovam sozinhos: só os 30 mais recentes são mantidos.

---

## 7. Uso no dia a dia

| Situação | O que fazer |
|---|---|
| Aluno esqueceu de sair | Painel → **Sessões ativas** → **Encerrar** |
| Máquina nova na biblioteca | Instalar o cliente (seção 3). Ela aparece sozinha no painel no primeiro login |
| Máquina com defeito ou fora de uso | Painel → **Máquinas** → **Desativar**. Ela passa a recusar logins |
| Relatório do mês | Painel → **Histórico** → filtrar as datas → **CSV**, **XLSX** ou **PDF** |
| Administrador quer trocar a senha | No painel: **Trocar senha**, no canto superior direito |
| Administrador esqueceu a senha | A CTI, no servidor: `python criar_admin.py usuario` |
| Cliente mostra "configuração incorreta" | O token do `config.ini` não bate com o do servidor. Os registros ficam guardados na máquina até a correção |

---

## 8. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| Cliente mostra "N registro(s) aguardando o servidor" | Servidor desligado ou rede fora. Os registros são enviados sozinhos quando voltar |
| Painel não abre de outro computador | Firewall (2.6) ou servidor rodando com `run.py` em vez de `servir.py` |
| Sessão ficou "em uso" depois de a máquina desligar | Normal: ela é fechada quando o cliente abrir de novo naquela máquina |
| "O controle de uso já está aberto neste computador" | Já existe um cliente rodando. Procure "Controle de uso" na barra de tarefas |
| O que aconteceu numa máquina | Ver `cliente.log` na pasta do cliente |
