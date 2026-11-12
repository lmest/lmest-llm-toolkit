---
name: transcricao-markdown
description: Transcreve PDFs de documentos técnicos e científicos para Markdown fiel, com equações em LaTeX, tabelas em Markdown e todas as figuras recortadas em imagens, preservando a estrutura e sinalizando trechos incertos. Use sempre que o usuário pedir para transcrever, converter, extrair ou passar para Markdown um PDF de artigo, paper, tese, dissertação, relatório técnico, livro, capítulo, apostila, manual ou outro documento técnico ou científico, mesmo sem citar a skill, e também quando pedir para recortar as figuras de um desses documentos junto com o texto. Não use para resumir, traduzir ou revisar documentos, para documentos administrativos ou financeiros (contratos, notas fiscais, formulários) nem para transcrever áudio.
---

# Transcrição de documentos para Markdown

## Objetivo
Converter PDFs de documentos técnicos e científicos em uma transcrição Markdown fiel e verificável. Preserve conteúdo e estrutura; não resuma, traduza, corrija nem complete silenciosamente trechos ilegíveis.

## O que é figura
São figuras: gráficos, diagramas, esquemas, fotos experimentais, mapas, ilustrações técnicas e qualquer elemento visual numerado ou com legenda no corpo do documento.

**Não são figuras** (não recorte nem referencie no Markdown): logotipos da revista, da editora ou de instituições, fotos dos autores, ícones (ORCID, acesso aberto, licença Creative Commons etc.) e ilustrações decorativas.

**Tabelas e equações não são figuras:** são sempre transcritas em Markdown (tabelas) e em LaTeX (equações), nunca recortadas como imagem. Veja "Tabelas, equações e notas".

## Regra obrigatória: recorte de todas as figuras
Em toda execução desta skill, **todas as figuras do documento devem ser recortadas** e salvas em `images/`, com um arquivo por figura. Não há exceção: isso vale também para figuras que pareçam simples e independe de o usuário pedir ou não. Só é permitido entregar sem recortes quando o documento não tiver nenhuma figura, e isso deve ser declarado no relatório final. Antes de concluir que não há figuras, avalie todas as páginas.

**Subfiguras:** subfiguras como 3(a) e 3(b) recebem recortes separados quando puderem ser separadas por uma caixa retangular sem cortar partes de outra subfigura. Quando forem inseparáveis (eixos, legendas ou rótulos compartilhados, sobreposição), faça um recorte único da figura inteira e registre o motivo no relatório final.

## Ferramentas e dependências
Os scripts que acompanham a skill usam Python 3, PyMuPDF (`pymupdf`, versão 1.24.3 ou superior) e Pillow (`PIL`). Em ambiente compatível, instale com `python -m pip install -r requirements.txt`. Se o sistema recusar a instalação com o erro `externally-managed-environment` (PEP 668, comum em Ubuntu/Debian), use um ambiente virtual: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, e rode os scripts com `.venv/bin/python`. Não tente instalar dependências se o ambiente não permitir. Confirme que as ferramentas e arquivos estão acessíveis antes de afirmar que o PDF foi processado ou que artefatos foram criados. Se não puder executar os scripts, explique a limitação e forneça os comandos.

## Títulos (headings) em caixa de título
Todos os títulos da transcrição (`#`, `##`, `###` etc.) devem estar em caixa de título, mesmo quando o PDF os apresenta em maiúsculas. Não copie a caixa alta do original: "INTRODUCTION" vira "Introduction" e "RESULTS AND DISCUSSION" vira "Results and Discussion".

- **Português:** maiúscula na primeira palavra e nas palavras de conteúdo; artigos, preposições e conjunções ficam em minúsculas, exceto quando forem a primeira palavra (ex.: "Sobre a Estrutura do Robô", "Controle e Estabilidade do Sistema").
- **Inglês:** maiúscula na primeira palavra e nas palavras de conteúdo; artigos, preposições curtas e conjunções ficam em minúsculas, exceto quando forem a primeira palavra (ex.: "Results and Discussion", "Time-Domain Response"). Em termos compostos com hífen, maiúscula em cada parte.
- Siglas, unidades e códigos mantêm a grafia original (PI, PD, FFT, dB SPL, MPU9250).
- Só a caixa muda. Mantenha a língua original, o texto e a ordem das palavras; não traduza nem reformule o título.
- **Numeração:** quando o título tiver numeração no original, mantenha-a exatamente como aparece ("1. INTRODUCTION" vira "1. Introduction"; "2.3 SENSOR CALIBRATION" vira "2.3 Sensor Calibration"). Não crie numeração onde não existe.
- Mantenha os níveis de título do original. Isso vale também para títulos de seções como Acknowledgments, References e Responsibility Notice.

## Tabelas, equações e notas
- **Tabelas:** transcreva em tabela Markdown, preservando cabeçalhos, ordem de linhas e colunas, unidades e notas da tabela. Se houver células mescladas ou estrutura que a tabela Markdown não represente, use uma tabela HTML (`<table>` com `rowspan`/`colspan`) no próprio Markdown. A legenda da tabela é transcrita no idioma original, como parágrafo, antes ou depois da tabela conforme o PDF.
- **Equações:** escreva em LaTeX, com `$...$` inline e `$$...$$` destacadas. Preserve a numeração com `\tag{n}` dentro do bloco (ex.: `$$ E = mc^2 \tag{3} $$`).
- **Notas de rodapé do documento:** use notas Markdown (`[^1]` no ponto de chamada e `[^1]: texto da nota` ao final da seção ou do documento), preservando a numeração ou os símbolos do original.

## Elementos omitidos
Omita da transcrição os cabeçalhos e rodapés corridos (nome da revista, título abreviado, nomes dos autores repetidos em cada página, DOI repetido) e os números de página. Essa é a única omissão permitida sem pedido do usuário; todo o restante do conteúdo deve ser transcrito. Notas de rodapé do documento não são rodapés corridos e devem ser mantidas.

## Fluxo de trabalho
A transcrição é feita **página por página**: o `.md` é montado aos poucos, e cada página é avaliada e transcrita antes de passar à seguinte. Não abra todas as páginas de uma vez; isso esgota o contexto em artigos longos.

**Recortes de leitura são opcionais.** Se a imagem inteira da página permitir transcrever com confiança, transcreva direto dela, sem recortes de leitura (`regions`). Recorte apenas quando necessário: texto pequeno ou comprimido, equações ou tabelas densas, ordem de leitura ambígua. Já os **recortes de figuras** (`image_regions`) continuam obrigatórios para toda figura.

### Preparação
1. **Crie o diretório de trabalho com nome genérico.** Na mesma pasta do PDF (salvo instrução contrária do usuário), crie `_transcricao_em_andamento/`; se já existir, use `_transcricao_em_andamento_2/`, `_3/` e assim por diante. Esse é o `DIRETORIO` usado em todo o processo. Ele só recebe o nome do artigo no passo 7.
2. **Prepare o PDF** com `scripts/prepare_pdf.py PDF DIRETORIO [--dpi 200]`. O script renderiza todas as páginas em `DIRETORIO/pages/`, extrai o texto incorporado em ordem de leitura para `extracted_text.txt` e grava em `metadata.json`, para cada página, o campo `layout`, com caixas em coordenadas normalizadas (o mesmo formato de `bbox` de `crops.json`):
   - `captions`: legendas detectadas ("Figure 3", "Fig. 3", "Tabela 2" etc.), com tipo, rótulo e caixa;
   - `image_blocks`: imagens raster incorporadas;
   - `drawing_clusters`: agrupamentos de desenhos vetoriais (gráficos e diagramas costumam aparecer aqui);
   - `text_blocks`: blocos de texto com as primeiras palavras.
   Verifique o número de páginas e se há texto selecionável (`extracted_text_characters`). A extração e as caixas são auxiliares, não garantia de fidelidade: PDFs digitalizados podem não ter nenhuma.

### Ciclo por página
3. Para cada página, em ordem, faça os passos 3.1 a 3.6 e só então passe à próxima.
   1. **Avalie a página** (`pages/page_NNN.png`): legibilidade, colunas, ordem de leitura, cabeçalhos/rodapés corridos (a omitir), figuras, tabelas e regiões relevantes. Não presuma layout idêntico ao de outras páginas nem divida automaticamente em duas colunas. Respeite o espaço real entre colunas. Tente ler a página inteira; se conseguir transcrevê-la com confiança, não faça recortes de leitura. Se o texto estiver pequeno, comprimido, ambíguo ou a ordem de leitura não estiver clara, gere recortes menores. Não há limite universal de pixels: use a capacidade de transcrever com confiança como critério e subdivida o recorte se ainda houver dúvida.
   2. **Planeje os recortes de leitura, só se necessários** (ver 3.1), acrescentando a página a `DIRETORIO/crops.json`, seguindo `examples/crops.example.json`. Toda região precisa de um `id` explícito e único na página (o script aborta se faltar `id` ou se houver repetição). `bbox` usa coordenadas normalizadas de 0 a 1 no formato `[x0,y0,x1,y1]`. Use as caixas de `metadata.json` (`layout`) como ponto de partida e ajuste-as visualmente. Cada região de leitura aceita `horizontal_parts` e `overlap` (fração da altura nominal compartilhada entre faixas, por exemplo 0.12). Para duas colunas, defina regiões separadas na ordem de leitura. Na primeira página, pode haver um recorte de título e resumo, mas transcreva também o restante da página.
   3. **Recorte obrigatório de figuras.** Na mesma página do manifesto, defina `image_regions` para cada figura (ver "O que é figura"), sem exceção. Use `id` no formato `figure_N` (ou `figure_Na`, `figure_Nb` para subfiguras). A caixa deve conter somente a figura, sem a legenda nem texto ao redor; rótulos que façam parte do desenho devem ser mantidos. Para estimá-la, parta de `drawing_clusters` ou `image_blocks` próximos da legenda correspondente em `captions` e pare antes da caixa da legenda. Subfiguras seguem a regra de "Regra obrigatória: recorte de todas as figuras".
   4. **Gere e inspecione** com `scripts/crop_images.py --manifest DIRETORIO/crops.json --pages-dir DIRETORIO/pages --output-dir DIRETORIO/crops`. Os recortes de leitura vão para `DIRETORIO/crops`. As figuras vão para `DIRETORIO/images` e são renderizadas **direto do PDF a 300 DPI** (o caminho do PDF vem de `metadata.json`), com qualidade superior a um recorte da página renderizada; ajuste com `--figure-dpi` se necessário, e use `--figures-from-pages` só se o PDF não puder ser aberto. O script grava `DIRETORIO/generated_files.json` com os arquivos gerados e avisa sobre PNGs antigos de execuções anteriores (campo `stale_files`); apague-os. Se a página não tiver figuras nem precisar de recortes de leitura, pule este passo. Inspecione apenas os recortes da página atual: cada figura deve estar inteira, sem cortes em eixos, rótulos, símbolos ou margens, e sem a legenda. Ajuste o manifesto e regenere até estarem corretos.
   5. **Transcreva a página e acrescente-a imediatamente ao `.md`** (ver "Regras de transcrição"). Na primeira página, leia o título do documento, defina o `<Nome Final>` (ver "Organização obrigatória") e crie `DIRETORIO/<Nome Final>.md`. Use a imagem da página (e os recortes de leitura, se houver) como fonte visual primária; use o texto extraído da página para conferir caracteres, nomes e continuidade. Em páginas com duas colunas, normalmente leia a coluna esquerda inteira e depois a direita, confirmando a ordem visualmente.
   6. **Registre a continuidade** antes de seguir: se a página termina no meio de um parágrafo, tabela, equação ou lista, anote isso (mentalmente ou em uma linha de trabalho) para emendar corretamente na página seguinte, sem quebra de parágrafo nem duplicação. Não reabra imagens de páginas anteriores, a não ser para resolver uma junção.

### Fechamento
4. **Revise o `.md` completo:** ordem de páginas e colunas, continuidade nas junções entre páginas, duplicações nas sobreposições, tabelas, figuras, equações, referências e apêndices. Confirme que cabeçalhos/rodapés corridos e números de página foram omitidos e que nenhum outro conteúdo foi descartado.
5. **Rode o verificador:** `scripts/check_transcription.py DIRETORIO`. Ele confere:
   - que cada recorte de `images/` é referenciado no Markdown e cada referência aponta para um arquivo existente, gerado pelo último `crop_images.py`, sem `stale_files`;
   - o formato das figuras: imagem sozinha na linha, linha em branco, legenda inteira em negrito, sem `>` nem descrição entre colchetes, e texto alternativo com o mesmo rótulo e número da legenda;
   - títulos em caixa alta, tabelas inseridas como imagem, blocos `$$` não fechados e notas de rodapé sem definição;
   - o nome do diretório e do `.md` (ainda provisório, longo demais, caracteres proibidos).
   Corrija todos os **erros** e avalie os **avisos**; o aviso de nome provisório é esperado até o passo 7. O verificador não substitui a revisão do passo 4: ele não confirma se todas as figuras do documento foram recortadas nem se o texto está fiel. Se faltar alguma figura, volte ao passo 3.3 da página correspondente.
6. Confirme que cada figura do documento tem um recorte em `images/` e uma referência no Markdown, comparando com as legendas de `captions` em `metadata.json` e com a avaliação visual das páginas.
7. **Renomeie o diretório** de `_transcricao_em_andamento` (ou da variante numerada) para `<Nome Final>`, conforme "Organização obrigatória". Se já existir um diretório com esse nome, não sobrescreva: pergunte ao usuário como proceder. Os caminhos no Markdown e em `generated_files.json` são relativos e continuam válidos após a renomeação. Rode `check_transcription.py` de novo no diretório renomeado; ele deve terminar sem erros.
8. **Relatório final:** liste cada figura com o caminho completo do recorte gerado (já com o diretório renomeado), informe qualquer figura não recortada ou com subfiguras em recorte único, com o motivo, e informe se o título foi truncado ou teve caracteres trocados. Sem essa lista, a execução não está concluída.

## Regras de transcrição
- Produza Markdown fiel. Preserve títulos, numeração e níveis de seção (com a caixa de título definida em "Títulos (headings) em caixa de título"), parágrafos, listas, citações, notas, legendas, tabelas e referências, seguindo "Tabelas, equações e notas". Mantenha a língua original.
- Trate sobreposições entre faixas como contexto repetido, mas transcreva o trecho sobreposto uma única vez. Revise as junções para não duplicar nem omitir palavras, linhas de tabela ou equações.
- Não adivinhe texto, números, símbolos, nomes ou equações. Use `[ilegível]` ou `[incerto: ...]`, indicando página/região quando útil. Diferencie falha de leitura de lacuna existente no PDF.
- Cada figura aparece no Markdown exatamente neste formato, com uma linha em branco entre a imagem e a legenda:

```
![Figure 1](images/p002_figure_1.png)

**Figure 1 – Design of the wall-climbing robot. (Pereira *et al.* (2026b))**
```

  - O texto alternativo (`![...]`) e a legenda usam sempre o idioma original do documento: `![Figure 1](...)` em documentos em inglês, `![Figura 1](...)` em documentos em português, e assim por diante, com o mesmo rótulo usado na legenda.
  - A legenda é transcrita integralmente, como parágrafo normal (sem `>`), no idioma original.
  - Subfiguras recortadas separadamente (ex.: 3a e 3b) ficam na mesma linha, separadas por espaço, e compartilham uma única legenda. Subfiguras com recorte único aparecem como uma imagem só.
  - Não escreva descrição do conteúdo visual: nada de `[Figura 1] ...`, `> ...` ou texto entre a imagem e a legenda. O conteúdo visual fica no recorte, não é repetido no texto.

## Organização obrigatória
O diretório de saída recebe, ao final do processo (passo 7), o nome do documento: o `<Nome Final>`. Ele é o título completo do documento, como aparece no PDF, na caixa de título definida em "Títulos (headings) em caixa de título", sem alterar as palavras. Se o título estiver em caixa alta no PDF, aplique a caixa de título também ao nome. A transcrição final fica dentro dele com o mesmo nome, seguido de `.md` (ex.: `Título do Documento/Título do Documento.md`). O nome do arquivo é o nome do diretório, não `transcricao.md` nem outro nome genérico.

Ajustes no `<Nome Final>`, nesta ordem:
1. **Caracteres proibidos:** troque `/ \ : * ? " < > |` por hífen ou remova-os.
2. **Títulos muito longos:** se o nome passar de 200 bytes em UTF-8 (acentos ocupam mais de um byte), mostre somente o início do título, cortando na última palavra inteira que caiba, e complete com reticências (`…`, caractere único U+2026). Ex.: `Experimental Analysis of the Dynamic Behavior of a Wall-Climbing Robot With…`.
3. **Final do nome:** remova espaços e pontos no fim do nome antes das reticências (e do nome inteiro, se não houver truncamento).

Informe no relatório final qualquer troca de caracteres ou truncamento.

```text
Título do Documento/
├── pages/                 # imagens integrais, uma por página
├── crops/                 # recortes de leitura, só se necessários
├── images/                # recortes das figuras, sem legendas/texto ao redor
├── extracted_text.txt     # texto incorporado, se disponível
├── metadata.json          # metadados de renderização e extração
├── crops.json             # plano reproduzível de recortes
├── generated_files.json   # lista dos arquivos gerados pelo último recorte
└── Título do Documento.md    # transcrição final (mesmo nome do diretório, com .md)
```
Use nomes estáveis, como `page_001.png`, `p001_body_left_part01.png` e `p001_figure_1.png`. A pasta `images/` é obrigatória sempre que o documento tiver figuras e deve conter um recorte por figura (ou por subfigura separável). Se o ambiente não permitir criar, renomear arquivos ou diretórios, não alegue que o fez: informe a limitação.

## Scripts incluídos
- `scripts/prepare_pdf.py PDF DIRETORIO [--dpi 200]`: renderiza as páginas, extrai o texto em ordem de leitura e grava em `metadata.json` as caixas de legendas, imagens, desenhos e blocos de texto (campo `layout`).
- `scripts/crop_images.py --manifest DIRETORIO/crops.json --pages-dir DIRETORIO/pages --output-dir DIRETORIO/crops [--figure-dpi 300] [--pdf PDF] [--figures-from-pages] [--images-output-dir DIRETORIO/images] [--generated-list DIRETORIO/generated_files.json]`: gera os recortes de leitura e as figuras (renderizadas do PDF em alta resolução). Exige `id` único por região, valida o manifesto inteiro antes de gravar e registra os arquivos gerados e os antigos.
- `scripts/check_transcription.py DIRETORIO`: verificação automática da transcrição; sai com código 1 se houver erros.
- `examples/crops.example.json`: exemplo de manifesto.
