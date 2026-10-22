# Entrada: formatos, pacote e convenções do Markdown

## Formatos aceitos

| Entrada | Qualidade | Como chega |
|---|---|---|
| **Markdown + diretório de imagens** | **preferida** | ZIP, pasta, `.md` solto, ou `.md` + `--imagens DIR_OU_ZIP` |
| **PPTX fora do padrão LMEst** | reconstrução a partir do conteúdo visível | arquivo `.pptx`; siga [`entrada_pptx.md`](entrada_pptx.md) |
| **PDF** | alternativa, resultado inferior | `.pdf`, ou ZIP/pasta contendo só um PDF |

Sempre que a entrada for PDF, avise o usuário **antes de processar**: enviar
o conteúdo em Markdown com um diretório de imagens é mais efetivo e gera
resultados melhores. Explique em uma ou duas frases o motivo: equações,
figuras vetoriais, ordem do texto e dados da capa não são recuperados de forma
confiável de um PDF. Depois siga com o PDF, a menos que o usuário prefira
mandar o Markdown.

## Markdown + imagens

```text
apresentacao.zip
├── apresentacao.md
└── imagens/
    ├── foto_bancada.jpg
    └── resposta_frequencia.png
```

```bash
python3 scripts/prepare_input_bundle.py apresentacao.zip work
python3 scripts/prepare_input_bundle.py pasta_do_conteudo/ work
python3 scripts/prepare_input_bundle.py apresentacao.md work                      # imagens ao lado do .md
python3 scripts/prepare_input_bundle.py apresentacao.md work --imagens imagens/   # imagens em diretório/ZIP separado
```

- O Markdown principal deve se chamar `apresentacao.md`, `slides.md`,
  `presentation.md` ou `deck.md`, ou ser o único `.md` do pacote.
- Caminhos de imagem são relativos ao `.md`. Espaços e `%20` funcionam,
  assim como `![](<minha foto.png>)`.
- **Imagens enviadas separadamente** (diretório com `--imagens`, ou arquivos
  soltos em `/mnt/user-data/uploads/`, já que o chat não aceita pastas): se o
  caminho relativo não existir, a imagem é localizada pelo **nome do arquivo**
  em qualquer lugar do pacote, e o manifesto registra
  `"aviso": "localizada pelo nome do arquivo"`. Nomes repetidos em pastas
  diferentes são tratados como ambíguos e reportados como ausentes. Com
  uploads soltos, passe a pasta de uploads como `--imagens`.
- Formatos de imagem: PNG, JPG, WEBP, SVG, GIF, BMP e TIFF. SVG/WEBP/GIF são
  convertidos para PNG na inserção (`lmest_pptx.ensure_raster`).
- Imagens remotas (`http...`) e `data:` não são aceitas: inclua o arquivo.
- `__MACOSX/`, `._*`, `.DS_Store` e `Thumbs.db` são ignorados.
- ZIPs com caminhos absolutos, `..`, links simbólicos ou mais de 1 GB
  descompactado são recusados.
- Use sempre o `path` resolvido de `imagens_referenciadas` (ou de
  `slides[].imagens[].path`), não a referência original.

A entrada original nunca é modificada. Tudo é copiado para `work/extracted/`.

## PDF

```bash
python3 scripts/prepare_input_bundle.py conteudo.pdf work      # sai com código 5
```

O PDF não vira deck direto: ele vira um **rascunho de Markdown** que você
revisa e depois processa como entrada Markdown.

1. **Conversão** (`scripts/pdf_to_markdown.py`, chamada automaticamente):
   - `work/pdf_rascunho/apresentacao.md`: um bloco por página, separado por
     `---`. Cada bloco traz `<!-- origem: pagina N (tipo provável) -->`, o
     título provável (faixa de cabeçalho ou maior corpo de fonte), o texto na
     ordem do fluxo do PDF e as imagens raster recortadas;
   - `work/pdf_rascunho/imagens/pNNN_imgK.png`: imagens raster da página;
   - `work/pdf_paginas/pagina-NNN.png`: render de cada página;
   - `input_manifest.json` com `origem: "pdf"`, `capa_sugerida`,
     `paginas_com_equacoes`, `paginas_sem_texto` e o tipo provável de cada
     página (`possivel_capa`, `possivel_divisor`, `possivel_agradecimentos`,
     `conteudo`).
2. **Revisão** do rascunho. Abra cada `pdf_paginas/pagina-NNN.png` ao lado do
   bloco correspondente e:
   - corrija títulos, junte ou separe blocos e reordene o texto de colunas;
   - transforme a página de capa no **front matter**. `capa_sugerida` é só uma
     pista: confirme título, autores, cargos e contatos com o usuário. Remova o
     bloco da capa e o dos agradecimentos do corpo, porque esses slides vêm do
     template;
   - converta páginas de divisor em `#` e as de conteúdo em `##`;
   - **transcreva as equações em LaTeX** (`$$ … $$`) a partir do render. O
     texto extraído delas sai quebrado. Liste as equações transcritas para o
     usuário conferir;
   - figuras vetoriais (gráficos de matplotlib/Excel exportados como vetor)
     não são extraídas. Recorte-as do render da página em resolução maior
     (`pdftoppm -r 220 -f N -l N -png`) e salve em `pdf_rascunho/imagens/`.
     Melhor ainda: peça o arquivo original ao usuário;
   - páginas sem camada de texto (PDF escaneado) devem ser transcritas a
     partir do render;
   - resolva e **apague** cada `<!-- conferir: … -->`. Mantenha a linha
     `<!-- RASCUNHO … -->` do topo: ela identifica a origem.
3. **Segunda passada** sobre o rascunho revisado:
   `python3 scripts/prepare_input_bundle.py work/pdf_rascunho work`.
   O manifesto sai com `origem: "pdf_revisado"` e avisa se ainda houver
   marcações `conferir` ou slides sem título.

Não rode a primeira passada de novo depois de editar o rascunho: ela recria
`pdf_rascunho/` e apaga as edições.

Na entrega de um deck feito a partir de PDF, diga ao usuário quais equações
foram transcritas e quais figuras foram recortadas do render, e repita que,
com o Markdown e as imagens originais, o resultado seria mais fiel.

## Front matter (obrigatório)

Os dados da capa e dos agradecimentos vêm **somente** do front matter YAML,
no topo do arquivo:

```yaml
---
titulo: Efeitos de não colocação em mancais magnéticos ativos
autores:
  - nome: Ana Ribeiro
    cargo: Mestranda · LMEst-UFU          # opcional
    contatos: [ana.ribeiro@ufu.br, (34) 99999-0000]
    apresentador: true                    # contatos da capa e agradecimentos
  - nome: Prof. Dr. Carlos Lima
agradecimentos:                           # opcional; omita para herdar do apresentador
  cargo: Mestranda · PPGEM-UFU            # sobrescreve campos do apresentador
  # contatos: [...]                       # até 3 (telefones e e-mails)
---
```

- `titulo` e `autores` são obrigatórios. Sem eles o script sai com código 3.
- Sem `apresentador: true`, o primeiro autor é usado (e um aviso é emitido).
- O slide de agradecimentos é sempre incluído; este bloco apenas personaliza
  nome, cargo e contatos mostrados nele.
- Para forçar uma quebra no título da capa, use um bloco literal
  (`titulo: |`) com as duas linhas.

Se o usuário não tiver front matter, mostre este bloco e peça os dados. Não
preencha com informações da conversa sem confirmação explícita.

## Divisão em slides

Duas convenções, detectadas automaticamente:

1. **Com separadores**: uma linha `---` (com linha em branco antes, senão o
   Markdown a interpreta como título setext) separa slides.
2. **Sem separadores**: cada `#` abre um **divisor de seção** e cada `##` abre
   um **slide de conteúdo**.

Em ambas, o primeiro título do bloco define o tipo: `#` vira divisor e `##`
vira conteúdo. No divisor, a primeira linha de texto após o título vira o
subtítulo.

## Descrição visual opcional

Depois do heading que inicia cada slide (`#` ou `##`), o usuário pode inserir
um blockquote Markdown para orientar a estrutura visual. Linhas em branco
entre o heading e o blockquote são permitidas; para descrições com várias
linhas, coloque `>` no início de cada linha:

```markdown
## Tempo por método

> Esse slide deve conter um gráfico de barras mostrando os valores 5, 10, 12 e 100.
> No eixo x temos o nome de cada método "Newmark", "Analítico", "Redução modal", "Original"
> e no eixo y o tempo em minutos.

O conteúdo textual do slide fica fora do blockquote.
```

O blockquote é uma instrução para o agente, não texto a ser copiado para o
slide. Seus valores, rótulos e outras especificações podem orientar objetos
visuais, como gráficos. Aspas retas ou tipográficas em texto normal não são
blockquotes.

Blockquotes são reservados exclusivamente para descrições visuais. Só é válido
um blockquote não vazio logo após o heading; qualquer blockquote no corpo,
antes de um heading ou usado como citação/conteúdo interrompe a geração. O
agente também deve conferir se a descrição realmente explica como o slide deve
ser apresentado. O erro informa a linha para correção. Sem blockquote, o agente
escolhe a estrutura visual de acordo com o conteúdo.

## Anotações (comentários HTML)

| Anotação | Efeito |
|---|---|
| `<!-- literal -->` | proíbe condensar o texto do slide |
| `<!-- notas: texto -->` | notas do apresentador do slide |

## Conteúdo

O Markdown é a fonte do **conteúdo**, não do layout. O agente escolhe, sem
anotações ou seleções manuais, qual slide da apresentação editável de referência
melhor atende a cada bloco. O slide de capa abre a apresentação e o de
agradecimentos encerra; os demais seguem a ordem do Markdown.

Preserve sempre: títulos, números, unidades, nomes próprios, tabelas (como
dados), equações e referências a figuras.

**Condensar é permitido** (regra de densidade em `design_system.md`), exceto
em slides `<!-- literal -->`. Ao condensar:

- reescreva frases, mas nunca mude números, unidades, nomes ou equações;
- o texto retirado do slide vai para as notas do apresentador;
- se o corte mudar o sentido, pergunte ao usuário.

## Inventário (`work/input_manifest.json`)

Para entradas Markdown e PDF, o arquivo traz `origem` (`markdown`, `pdf` ou
`pdf_revisado`), `capa` (dados normalizados), `slides` (tipo, título, linhas,
`description`, literal, notas, imagens, número de equações), `imagens_*`,
`equacoes` (com slide e linha), `erros`, `avisos` e um `resumo`.
Para entrada PPTX, `origem` é `pptx` e o formato do inventário está descrito
em [`entrada_pptx.md`](entrada_pptx.md).

| Código de saída | Significado |
|---|---|
| 0 | ok (podem existir avisos) |
| 2 | imagem referenciada ausente |
| 3 | front matter ausente/incompleto |
| 4 | pacote inválido/inseguro, PPTX inválido ou não renderizável, ou Markdown principal ambíguo |
| 5 | entrada em PDF convertida em rascunho: revisar e rodar a segunda passada |
| 6 | blockquote vazio ou fora da posição reservada para descrição |
