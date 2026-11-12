"""Funções e constantes comuns aos scripts da skill lmest-apresentacao."""
import json
import os
import re
import site
import sys

# Permite rodar com python3 -I e ainda achar pacotes instalados com pip --user.
site.addsitedir(site.getusersitepackages())

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL, 'assets')

W, H = 1920, 1080

COR = {
    'navy': '#152536', 'ink': '#1b2b3a', 'muted': '#5b6b7c', 'red': '#c41e2a', 'blue': '#1e88c7',
    'blue-deep': '#17689b', 'steel': '#2f6690', 'sky': '#49a9e1', 'mist': '#b4d0dc', 'line': '#d6dee6',
    'surface': '#f3f5f8', 'surface-blue': '#f3f6fa', 'tint-blue': '#eaf4fb', 'tint-red': '#fbecee',
    'white': '#ffffff',
}
FONTE = 'Carlito, Calibri, sans-serif'

# Ids que nunca levam número de página nem barra de progresso.
SEM_NUMERO_FIXOS = {'capa', 'agradecimento', 'resumo'}
PREFIXO_DIVISORIA = 'sec-'


def ler_json(caminho, padrao=None):
    if not os.path.exists(caminho):
        if padrao is not None:
            return padrao
        sys.exit(f'Arquivo não encontrado: {caminho}')
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)


def gravar_json(caminho, dados):
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write('\n')


def ler(caminho):
    with open(caminho, encoding='utf-8') as f:
        return f.read()


def gravar(caminho, texto):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(texto)


class Projeto:
    """Pasta de uma apresentação: deck.json, projeto.json, slides/, lmest/, imagens/, saida/."""

    def __init__(self, pasta):
        self.pasta = os.path.abspath(pasta)
        self.deck_path = os.path.join(self.pasta, 'deck.json')
        self.proj_path = os.path.join(self.pasta, 'projeto.json')
        self.deck = ler_json(self.deck_path)
        self.proj = ler_json(self.proj_path, {})
        self.slides_dir = os.path.join(self.pasta, 'slides')

    def ordem(self):
        return list(self.deck.get('order', []))

    def arquivo(self, sid):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', sid):
            sys.exit(f'Id de slide inválido: {sid!r}')
        return os.path.join(self.slides_dir, f'{sid}.html')

    def tem_numero(self, sid):
        extras = set(self.proj.get('sem_numero', []))
        return not (sid in SEM_NUMERO_FIXOS or sid in extras or sid.startswith(PREFIXO_DIVISORIA))

    def salvar_deck(self):
        gravar_json(self.deck_path, self.deck)

    def salvar_proj(self):
        gravar_json(self.proj_path, self.proj)


def estilo(s):
    """'a:1px; b:c' -> {'a': '1px', 'b': 'c'}"""
    d = {}
    for parte in (s or '').split(';'):
        if ':' in parte:
            k, v = parte.split(':', 1)
            d[k.strip().lower()] = v.strip()
    return d


def px(v, base=None, padrao=None):
    """Converte '12px', '12', '50%' (com base) e 'calc(50% - 10px)' em número."""
    if v is None:
        return padrao
    v = str(v).strip()
    m = re.fullmatch(r'calc\(\s*([\d.]+)%\s*([+-])\s*([\d.]+)(px)?\s*\)', v)
    if m and base:
        a = float(m.group(1)) * base / 100
        b = float(m.group(3))
        return a + b if m.group(2) == '+' else a - b
    m = re.fullmatch(r'(-?[\d.]+)\s*(px|pt)?', v)
    if m:
        n = float(m.group(1))
        return n * 4 / 3 if m.group(2) == 'pt' else n
    m = re.fullmatch(r'(-?[\d.]+)%', v)
    if m and base:
        return float(m.group(1)) * base / 100
    return padrao


_FONTES = {}


def _fonte(fs, negrito):
    """Carlito real (assets/fontes) para medir texto; None se o Pillow não estiver disponível."""
    chave = (round(fs), negrito)
    if chave not in _FONTES:
        try:
            from PIL import ImageFont
            arq = os.path.join(ASSETS, 'fontes', 'Carlito-Bold.ttf' if negrito else 'Carlito-Regular.ttf')
            _FONTES[chave] = ImageFont.truetype(arq, max(1, round(fs)))
        except Exception:
            _FONTES[chave] = None
    return _FONTES[chave]


def largura_texto(texto, fs, negrito=False, caixa_alta=False, espacamento=0):
    """Largura de uma linha em Carlito, medida com a fonte real (ou estimada, sem Pillow)."""
    if caixa_alta:
        texto = texto.upper()
    f = _fonte(fs, negrito)
    if f is not None:
        return f.getlength(texto) + len(texto) * espacamento
    fator = 0.62 if caixa_alta else (0.53 if negrito else 0.49)
    return len(texto) * (fs * fator + espacamento)


def linhas_texto(texto, largura, fs, negrito=False, caixa_alta=False, espacamento=0):
    """Número estimado de linhas com quebra em espaços."""
    total = 0
    for paragrafo in texto.split('\n'):
        palavras = paragrafo.split()
        if not palavras:
            total += 1
            continue
        linhas, atual = 1, 0.0
        espaco = largura_texto(' ', fs, negrito, caixa_alta, espacamento)
        for p in palavras:
            w = largura_texto(p, fs, negrito, caixa_alta, espacamento)
            if atual and atual + espaco + w > largura:
                linhas += 1
                atual = w
            else:
                atual += (espaco if atual else 0) + w
        total += linhas
    return total


def slug_arquivo(t):
    """Nome de arquivo sem espaços nem acentos: 'Vibrações em rotores' -> 'vibracoes-em-rotores'."""
    import unicodedata
    t = unicodedata.normalize('NFKD', t or 'apresentacao').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-') or 'apresentacao'


def esc(t):
    return (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
