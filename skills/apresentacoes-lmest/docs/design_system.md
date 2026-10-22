# Design system LMEst-UFU

Os valores foram extraídos da apresentação de referência editável
`assets/references/referencia_base.pptx`. `scripts/lmest_pptx.py` disponibiliza
tokens e medidas como `L.COR`, `L.MARGEM_X` e `L.TOPO_CONTEUDO`. Se este
documento e o arquivo divergem, siga a referência visual.

## Tela e identidade

- Proporção 16:9, 13,333 × 7,5 in (12 192 000 × 6 858 000 EMU), render lógico
  de 1920 × 1080 px.
- Use a faixa de cabeçalho, o traço vermelho, logos e rodapé existentes na
  referência selecionada. Ao compor sobre um corpo limpo, preserve esses
  elementos e a área livre abaixo do cabeçalho.
- Fundos navy, cartões claros, diagonais discretas e logotipos vêm da
  apresentação editável. Não redesenhe nem rasterize elementos existentes.

## Cores

| Token (`L.COR`) | Hex | Uso |
|---|---|---|
| `navy` | `152536` | cabeçalho e blocos de destaque |
| `texto` | `1B2B3A` | texto principal sobre fundo claro |
| `texto_suave` | `5B6B7C` | descrições e legendas |
| `azul` | `1E88C7` | números, valores e marcadores |
| `azul_medio` | `2F6690` | ícones e títulos secundários |
| `ciano_kicker` | `49A9E1` | rótulos sobre fundo escuro |
| `vermelho` | `C41E2A` | linha de cabeçalho e um destaque por slide |
| `laranja` | `E08A1E` | ressalva pontual |
| `borda` | `D6DEE6` | bordas de cards e tabelas |
| `superficie` | `F3F5F8` | cartões claros e áreas de equação |
| `superficie_azul` | `EAF4FB` | caixas informativas e painéis técnicos |
| `branco` | `FFFFFF` | fundos e texto sobre navy |

## Tipografia e densidade

Use Calibri em toda forma nova. O pacote Carlito ajuda a manter as quebras de
linha durante o render no LibreOffice.

| Elemento | Tamanho aproximado |
|---|---:|
| Título de conteúdo | 28 pt, negrito, branco |
| Introdução | 15–16 pt |
| Corpo e bullets | 12,5–16 pt |
| Título de card | 13–15 pt, negrito |
| Legenda | 9–11 pt |
| Número de destaque | 28 pt, negrito |

Prefira uma linha de introdução, até 5–6 bullets por área e parágrafos de até
três linhas. Legendas podem chegar a 9 pt; corpo deve ter pelo menos 12,5 pt.
Antes de reduzir fonte, condense sem alterar números, unidades, nomes ou
equações, distribua informação em blocos ou divida o slide. Texto removido vai
para notas do apresentador; respeite `<!-- literal -->`.

## Escolha automática da referência

O catálogo de `manifest.json` e as prévias produzidas a partir do PPTX são
referências internas numeradas. Para cada bloco do Markdown ou slide de
conteúdo PPTX de origem, compare assunto, quantidade e tipo de informação com
os 19 slides descritos em
`assets/references/refs_description.md`, e selecione a composição visual mais
próxima. O usuário fornece conteúdo, não uma escolha de layout. Não leia
comentários de layout nem peça que o usuário memorize nomes de composição.

Para entrada PPTX, use o inventário e as prévias de origem para determinar o
conteúdo semântico; preserve sua ordem no plano por `input_slide`, repetindo o
índice quando um slide denso for dividido. O tema e a decoração do PPTX de
origem não determinam a referência LMEst escolhida.

Considere, entre as opções, itens com ícones, cards empilhados, diagramas,
tabelas, galerias, cronogramas e gráficos. Reutilize uma referência quando
blocos diferentes pedirem estrutura semelhante. Mantenha a ordem da fonte;
posicione a capa primeiro, transições onde a estrutura de seções pedir e
agradecimentos por último. A descrição atual do slide 15 é “Gráfico de barras
verticais”.

Se nenhuma estrutura se adequar, use `clear_body` sobre um slide de conteúdo
para compor um corpo limpo, mantendo cabeçalho, identidade e rodapé. Construa o
conteúdo com texto, imagens, equações, tabelas, gráficos e conectores nativos
conforme o caso. O novo corpo deve parecer parte da mesma apresentação.

## Prioridade gráfica

Em cada slide de conteúdo, procure oportunidades para explicar a informação
visualmente antes de recorrer a blocos longos de texto. Use gráficos para
representar dados fornecidos; diagramas e fluxogramas para processos, relações
ou estruturas descritas; e formas nativas para agrupar, comparar ou destacar
conceitos. Linhas do tempo, sequências e layouts com cards também são opções
quando correspondem ao conteúdo.

Prefira objetos editáveis do PowerPoint. Use `L.add_chart` para gráficos com
dados, `L.add_table` para tabelas, `L.add_card` para cards e `L.add_connector`
para ligações; use as formas nativas de `python-pptx` quando precisar de outras
geometrias. Use imagens para figuras fornecidas pelo usuário ou quando não
houver dados suficientes para reconstruir fielmente o gráfico. Não invente
valores, etapas ou relações para preencher um visual. Elementos gráficos
devem esclarecer a hierarquia ou o conteúdo, sem competir com a leitura nem
ser adicionados apenas como decoração.

## Formas, imagens e elementos de dados

- Cards: retângulos arredondados de raio visual aproximado de 10 px, preenchidos
  com `superficie` ou branco e borda `borda` de 1 pt.
- Destaques: navy com texto branco e rótulo ciano; vermelho apenas para um
  ponto focal por slide.
- Fotos: grade com alturas e espaços consistentes. Use `cover` para fotos e
  `contain` para gráficos e figuras técnicas, que nunca devem ser cortados.
- Ícones existentes podem ser reaproveitados da referência escolhida. Mantenha
  ícones sociais institucionais em seus lugares fixos.
- Conectores retos ou ortogonais: navy/azul, 1,5 pt. Use
  `L.add_connector`; conecte aos objetos quando isso melhorar a leitura.
  A conexão a formas é mais confiável com cards retangulares ou arredondados;
  confira visualmente conectores ligados a formas livres ou complexas.
- Tabelas: use `L.add_table` para conteúdo editável. Cabeçalho navy e texto
  branco; linhas claras alternadas; números alinhados à direita e destacados
  em azul.
- Gráficos de dados editáveis: use `L.add_chart` com barras horizontais,
  colunas, linhas ou dispersão e a paleta LMEst. Gráficos enviados como imagem
  podem ser inseridos sem reconstrução, preferindo `contain`.
- Não use SmartArt nem tema de gráfico pronto do Office.

### API de objetos editáveis

As coordenadas e dimensões são EMU. Tabelas recebem cabeçalhos e linhas; as
larguras de coluna opcionais também são EMU e precisam somar a largura total.
Gráficos categóricos recebem séries no formato `[{"name": ..., "values": [...] }]`
e rótulos; dispersão recebe séries no formato
`[{"name": ..., "x": [...], "values": [...]}]`. Conectores aceitam
coordenadas e, opcionalmente, objetos de forma com os índices de conexão.

```python
L.add_table(slide, x, y, w, h, headers, rows,
            column_widths=widths, numeric_columns=[1])
L.add_chart(slide, x, y, w, h, "column", series, categories=labels)
L.add_chart(slide, x, y, w, h, "scatter", series_xy)
L.add_connector(slide, (x1, y1), (x2, y2), kind="elbow",
                begin_shape=shape_a, end_shape=shape_b)
```

Tipos de gráfico aceitos: `bar` (barras horizontais), `column`, `line` e
`scatter`. Conectores aceitos: `straight` e `elbow` (também reconhecido como
`orthogonal`).

## Aplicação em HTML

Se a saída for HTML, mantenha os mesmos valores de cor, hierarquia tipográfica,
proporção 16:9, cabeçalho, filete vermelho, marcas e composição selecionada.
Use `assets/html/lmest_presentation.css` e
`assets/html/lmest_presentation.js` como base. Recrie componentes com HTML e
SVG nativos (tabelas em `<table>`, gráficos e diagramas em SVG); use os mesmos
dados e rótulos da fonte. Consulte `docs/saida_html.md` para navegação,
interações, animação e renderização de QA. O HTML é composto diretamente e
não é uma exportação do arquivo PPTX.

## Composição

- Alinhe objetos a margens e colunas comuns; não centralize texto corrido.
- Mantenha o espaço vazio intencional e distribua os intervalos de forma
  consistente (aproximadamente 0,2–0,3 in entre cards).
- Escolha um ponto focal por slide e preserve a hierarquia da referência.
- Priorize uma representação visual quando ela explicar melhor dados,
  processos, relações ou conceitos; mantenha slides sem elementos gráficos
  quando a informação não se beneficiar deles.
- Substitua ou remova textos, imagens e dados de exemplo. Não deixe conteúdo
  específico do PPTX original no deck final.
