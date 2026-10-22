# Equações

## Política única

Toda equação do Markdown é renderizada em LaTeX por `scripts/render_equations.py`
e entra no slide como **imagem PNG no tamanho nativo**. Não use equação nativa
do PowerPoint, caixa de texto com símbolos, SVG ou outro renderizador.

A aparência de referência está em `assets/equations/eq_1.png`, `eq_2.png` e
`eq_3.png`. As fontes LaTeX delas estão em `assets/equations/fontes.md`.

## O que é detectado

| Sintaxe | Tipo |
|---|---|
| `$$ … $$`, `\[ … \]` | display |
| `\begin{equation|align|gather|multline|alignat|flalign}` (com ou sem `*`) | display |
| blocos ` ```math `, ` ```latex `, ` ```tex ` | display |
| `$ … $` | inline |

Ignorados: blocos de código, código inline, comentários HTML e valores
monetários. O `$` de abertura não pode vir colado a letra ou número, então
"R$ 70 mi" e "US$ 5" não são equações. Também não pode haver espaço logo
depois da abertura nem antes do fechamento, e o fechamento não pode vir colado
a número ("$5 e $10" não é equação). Para um cifrão literal ambíguo, escreva `\$`.

## Renderização

```bash
python3 scripts/render_equations.py work/extracted/apresentacao.md work/equacoes
#   --pt-display 20   corpo das equações display (padrão)
#   --pt-inline 16    corpo das fórmulas inline (padrão)
#   --sem-inline      não renderiza $...$
```

- Cada equação é compilada já no corpo final (Latin Modern, ou Computer
  Modern se o `lmodern` não estiver instalado; o desenho matemático é o mesmo),
  em 300 dpi, com fundo transparente.
- `equations_manifest.json` traz, por equação: `latex`, `kind`, `line`,
  `slide` (índice no `input_manifest.json`), `image`, `largura_in` e `altura_in`.
- Falhas não interrompem as demais: ficam com `image: null` e `erro`, o `.tex`
  vai para `work/equacoes/falhas/` e o script sai com código 1. Corrija o
  LaTeX (ou instale o pacote ausente) e rode de novo. **Nunca** substitua a
  equação por texto comum.
- Para mudar o tamanho, mude `--pt-display` para **o deck inteiro** e
  renderize de novo. Não reescale imagens individualmente.

## Inserção

```python
L.add_equation(slide, entrada, "work/equacoes", x_centro, y, max_w=L.LARGURA_UTIL)
```

- Insere no tamanho nativo (`largura_in` × `altura_in`), o que mantém o mesmo
  corpo de letra em todas as equações.
- Grava o LaTeX no texto alternativo (`descr`), o que preserva uma cópia
  editável e serve de acessibilidade.
- Levanta `LayoutError` se a equação não couber em `max_w`. Nesse caso, quebre
  em linhas (`gathered`/`aligned`), dedique um slide inteiro ou reduza
  `--pt-display` no deck todo.

**Matemática inline no meio de uma frase** não deve virar imagem. Escreva a
variável como runs de texto: `("k", {"italic": True}), ("s", {"baseline": "sub"})`.
PNGs de fórmulas inline servem apenas quando a fórmula aparece sozinha, como
rótulo ou célula de tabela.

## Composição

- Preto sobre fundo branco ou `superficie` (`F3F5F8`). Nunca sobre fundo escuro.
- Equações centralizadas horizontalmente, com bastante respiro:
  ≥ 0,3 in até qualquer texto ou borda.
- Grupos de equações relacionadas ficam em um único bloco `gathered` ou
  `aligned`, ou empilhados com espaçamento uniforme.
- Frases de ligação entre equações em 15 pt `texto_suave`, centralizadas.
- A equação não deve dominar o slide, salvo quando ela for o assunto principal.
- Sem cor, caixa, sombra ou negrito decorativo dentro da equação. Destaques
  de cor só se o usuário pedir.

## Convenções de escrita (LMEst)

- Vetores e matrizes em `\mathbf{}`; escalares em itálico padrão.
- Derivadas temporais com `\dot{}` / `\ddot{}`.
- Matrizes com `bmatrix`; reticências com `\cdots`, `\vdots`, `\ddots`, `\cdot`.
- Transposta com `^T`.

## Verificação

Antes de aprovar: compare cada equação com o Markdown (símbolos, índices,
sinais, transpostas) e confira no render do slide que o corpo de letra está
uniforme e próximo de `assets/equations/`.
