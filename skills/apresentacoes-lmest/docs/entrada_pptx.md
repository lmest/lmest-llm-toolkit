# Reconstruir a partir de uma apresentação PPTX

Use este fluxo quando o usuário fornecer uma apresentação pronta que ainda não
segue o padrão visual LMEst. O conteúdo visível e a ordem da fonte devem ser
preservados; tema, cores, fontes, fundos e decoração da fonte não são levados
para o deck final.

Pergunte se a entrega deve ser PPTX ou HTML quando o usuário ainda não tiver
especificado. A conferência de conteúdo e as perguntas sobre ambiguidades são
comuns aos dois formatos; para HTML, siga `saida_html.md` depois dessa etapa.

## Preparação e inventário

```bash
python3 scripts/prepare_input_bundle.py apresentacao_fonte.pptx work
```

O código 0 indica que o inventário e as prévias foram gerados. O código 4 indica
PPTX inválido, arquivo que não pode ser aberto ou falha na renderização. Em
`work/input_manifest.json`, cada slide contém:

- `index`, `titulo` e `titulo_origem`;
- `elementos`: lista em ordem de leitura/estrutura, com `kind`, nome, tipo
  PowerPoint e `posicao` em EMU;
- `texto` para texto visível; `dados` para células de tabelas ou séries,
  categorias e eixos de gráficos nativos;
- `midia.path` para cada imagem extraída e `candidato_equacao` para equações
  detectadas em OMML ou por uma heurística textual;
- `render`, caminho relativo a `work` para a prévia daquele slide;
- `avisos` sobre elementos que precisam de atenção manual.

As imagens originais ficam em `work/extracted/pptx_media/`, o PPTX copiado fica
em `work/extracted/origem.pptx` e todos os slides são renderizados em
`work/source_render/`. Os renders preservam a proporção da fonte; podem não ser
16:9. O inventário é uma ajuda para a leitura, não substitui a inspeção visual.
Caminhos de mídia e de render são relativos ao diretório `work/`. O manifesto
marca o primeiro e o último slides como candidatos para abertura e encerramento;
confirme pela imagem se realmente contêm a capa e os agradecimentos.

Esquema resumido de um slide:

```json
{
  "index": 2,
  "titulo": "Resultados por método",
  "titulo_origem": "placeholder_titulo",
  "elementos": [
    {
      "id": 3,
      "kind": "grafico",
      "posicao": {"x": 400000, "y": 800000, "largura": 5000000, "altura": 3000000, "unidade": "EMU"},
      "dados": {"tipo": "COLUMN_CLUSTERED", "categorias": ["A", "B"], "series": [{"nome": "Tempo", "valores": [5, 10]}]}
    }
  ],
  "render": "source_render/slide-002.png"
}
```

## Conferência obrigatória antes da montagem

Abra **todas** as imagens `source_render/slide-NNN.png` e confira cada uma
contra o slide correspondente no inventário. Complete o que o extrator não
conseguir ler e registre as dúvidas por slide. Verifique especialmente:

- textos em caixas, imagens, grupos e objetos incorporados;
- células e ordem de linhas e colunas das tabelas;
- categorias, unidades, valores, séries e eixos de gráficos;
- formas, setas, conectores e relações entre etapas;
- equações, símbolos, subscritos, sobrescritos e sinais;
- elementos que só aparecem no render e não foram extraídos como objeto.

O extrator pode marcar candidatos a equação, mas não garante que encontrou
todos: fórmulas em imagem, vetor ou desenho precisam ser identificadas pela
inspeção. Diagramas, SmartArt, gráficos sem dados acessíveis e objetos OLE
podem exigir interpretação da imagem. Não deduza valores ou relações ausentes.

Se houver qualquer trecho ilegível, valor de gráfico incerto, equação duvidosa,
relação de diagrama ambígua ou divergência entre inventário e render, pare e
pergunte ao usuário, identificando o slide e o ponto exato. Não comece a gerar
ou montar o deck até resolver as pendências. Mostre a transcrição proposta
(quando apropriado) para o usuário confirmar.

## Capa e agradecimentos

Inspecione os slides de abertura e encerramento da fonte para mapear os dados
claros para os campos fixos LMEst. A capa LMEst recebe título, autores,
cargos e contatos que estiverem visíveis e inequívocos. O slide final recebe
os dados de agradecimento explicitamente presentes na fonte. Se a apresentação
não tiver capa ou agradecimentos, ou faltar/for ambíguo qualquer campo
necessário, pergunte ao usuário exatamente o que deve aparecer. Não invente
autores, cargos, contatos, nomes de agradecimento nem texto institucional.

Esses slides LMEst continuam obrigatórios: `source_slide: 1` abre o deck e
`source_slide: 19` encerra. Só os campos de conteúdo documentados em
`slides_rigidos.md` podem ser alterados; preserve o layout fixo.

## Planejar e reconstruir

1. Extraia todo o conteúdo semântico visível, mantendo texto, números, unidades,
   nomes, dados, equações e sequência. Não copie os elementos de identidade da
   apresentação de origem.
2. Para cada slide de conteúdo, selecione uma referência LMEst adequada ao
   conteúdo. Recrie tabelas e gráficos como objetos PowerPoint editáveis quando
   a estrutura estiver disponível. Refaça diagramas com formas e conectores
   nativos quando as relações estiverem claras.
3. Quando não for possível reconstruir uma figura fielmente, use a mídia
   extraída ou um recorte da renderização de origem. Insira a figura recortada
   como imagem; não use uma página inteira do render como fundo do slide final.
4. Transcreva as equações para LaTeX, confira sinais e índices contra o render
   e renderize cada expressão antes de inserir. Para usar o renderizador
   existente, crie um Markdown temporário com as expressões em `$$...$$` e rode
   `scripts/render_equations.py`.
5. Preserve a ordem de origem. Um slide denso pode virar dois ou mais slides
   LMEst; repita `input_slide` no plano para cada divisão. Os índices precisam
   ser inteiros positivos em ordem não decrescente. Não omita conteúdo para
   forçar a correspondência a uma única página.
6. Registre `input_slide` em cada slide final cujo conteúdo veio da fonte,
   incluindo capa e agradecimentos quando forem mapeados de slides da origem.
   `md_slide` continua sendo usado para entradas Markdown. Exemplos:

   ```json
   {"slides": [
     {"source_slide": 1, "input_slide": 1, "papel": "capa"},
     {"source_slide": 8, "input_slide": 1},
     {"source_slide": 7, "input_slide": 2},
     {"source_slide": 3, "input_slide": 2},
     {"source_slide": 19, "input_slide": 6, "papel": "agradecimentos"}
   ]}
   ```

   O slide 2 da fonte foi dividido em dois; referências repetidas são válidas,
   mas os índices `input_slide` devem continuar não decrescentes.

Depois da montagem, renderize todas as páginas finais e rode a avaliação com os
renders da fonte:

```bash
python3 scripts/render_deck.py work/deck.pptx work/render
python3 scripts/evaluate_render.py work/render --plano work/deck_plan.json \
  --referencias work/reference_render --entrada-pptx-render work/source_render
```

Inspecione cada página final contra a referência LMEst escolhida e contra o
slide de origem indicado por `input_slide`. Confira a correspondência entre o
inventário e o deck final para garantir que nenhum conteúdo visível ficou de
fora. A avaliação cria pares para as duas comparações; ela não substitui a
revisão visual do agente. Consulte `qa.md` e corrija em até três ciclos.

Notas do apresentador e animações não fazem parte do escopo de extração.
