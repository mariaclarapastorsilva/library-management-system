import json

import pytest

import cliente as C


@pytest.fixture(autouse=True)
def arquivos_temporarios(tmp_path, monkeypatch):
    """Cada teste usa fila, sessão, log e configuração próprios, longe da pasta real."""
    for nome, arquivo in [('ARQ_FILA', 'fila.json'), ('ARQ_SESSAO', 'sessao.json'), ('ARQ_LOG', 'cliente.log'),
                          ('ARQ_CONFIG', 'config.ini'), ('ARQ_CONFIG_EXEMPLO', 'config.example.ini')]:
        monkeypatch.setattr(C, nome, str(tmp_path / arquivo))
    return tmp_path


class ApiFalsa:
    """Responde com os status da lista, em ordem; None simula servidor fora do ar."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.enviados = []

    def enviar(self, caminho, dados):
        status = self.respostas.pop(0)
        if status is None:
            raise C.ErroRede('fora do ar')
        self.enviados.append(caminho)
        return status, {'erro': 'recusado'} if status >= 400 else {}


def fila_com(api, *caminhos):
    fila = C.Fila(api)
    for caminho in caminhos:
        fila.adicionar(caminho, {'maquina': 'PC'})
    return fila


def test_fila_envia_em_ordem_e_esvazia():
    api = ApiFalsa(201, 200)
    fila = fila_com(api, '/api/login', '/api/logout')
    assert fila.enviar() == 0
    assert api.enviados == ['/api/login', '/api/logout']
    assert fila.pendentes() == 0


def test_fila_guarda_tudo_com_servidor_fora_do_ar():
    fila = fila_com(ApiFalsa(None), '/api/login', '/api/logout')
    assert fila.enviar() == 2


def test_fila_para_no_meio_e_continua_depois():
    api = ApiFalsa(201, None, 200)
    fila = fila_com(api, '/api/login', '/api/logout')
    assert fila.enviar() == 1
    assert fila.enviar() == 0
    assert api.enviados == ['/api/login', '/api/logout']


def test_fila_descarta_evento_recusado_e_anota_no_log():
    fila = fila_com(ApiFalsa(404), '/api/logout')
    assert fila.enviar() == 0
    with open(C.ARQ_LOG, encoding='utf-8') as f:
        assert 'evento descartado (404' in f.read()


def test_fila_mantem_eventos_quando_o_token_esta_errado():
    fila = fila_com(ApiFalsa(401), '/api/login', '/api/logout')
    assert fila.enviar() == 2


def test_arquivo_da_fila_corrompido_nao_derruba_o_cliente():
    with open(C.ARQ_FILA, 'w') as f:
        f.write('{ meio arquivo')
    assert C.Fila(ApiFalsa()).pendentes() == 0


def test_gravar_json_nao_deixa_arquivo_temporario(arquivos_temporarios):
    C.gravar_json(C.ARQ_FILA, [{'a': 'ç'}])
    assert json.load(open(C.ARQ_FILA, encoding='utf-8')) == [{'a': 'ç'}]
    assert not list(arquivos_temporarios.glob('*.tmp'))


def test_config_padrao_sem_arquivos(monkeypatch):
    monkeypatch.setattr(C.socket, 'gethostname', lambda: 'MAQUINA-X')
    cfg = C.carregar_config()
    assert cfg['url'] == 'http://127.0.0.1:5000'
    assert cfg['maquina'] == 'MAQUINA-X'
    assert cfg['bloqueio'] is False
    assert cfg['aviso'] == '' and cfg['senha_manutencao'] == ''


def test_config_ini_sobrescreve_o_exemplo():
    with open(C.ARQ_CONFIG_EXEMPLO, 'w', encoding='utf-8') as f:
        f.write('[servidor]\nurl = http://exemplo:5000\ntoken = t1\n[cliente]\nbloqueio = nao\n')
    with open(C.ARQ_CONFIG, 'w', encoding='utf-8') as f:
        f.write('[servidor]\nurl = http://10.0.0.5:5000/\n[maquina]\nid = BIB-01\n'
                '[cliente]\nbloqueio = sim\naviso = 100% registrado\n    segunda linha\n')
    cfg = C.carregar_config()
    assert cfg['url'] == 'http://10.0.0.5:5000'  # barra final removida
    assert cfg['token'] == 't1'                   # veio do exemplo
    assert cfg['maquina'] == 'BIB-01'
    assert cfg['bloqueio'] is True
    assert cfg['aviso'] == '100% registrado\nsegunda linha'


def test_senha_de_manutencao():
    guardado = C.gerar_hash_senha('manutencao123')
    assert 'manutencao123' not in guardado
    assert C.conferir_senha('manutencao123', guardado)
    assert not C.conferir_senha('outra', guardado)
    assert not C.conferir_senha('manutencao123', 'formato-invalido')
    assert C.gerar_hash_senha('manutencao123') != guardado  # sal aleatório


def test_api_sem_servidor_vira_erro_de_rede():
    with pytest.raises(C.ErroRede):
        C.Api('http://127.0.0.1:9', '', 1).enviar('/api/login', {})
