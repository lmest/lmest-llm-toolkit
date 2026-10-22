---
name: apresentacoes-lmest
description: >-
  Gera e revisa apresentações PowerPoint (.pptx) e HTML no padrão visual do
  LMEst-UFU a partir de Markdown com imagens, de PDF ou reconstruindo uma
  apresentação PPTX fora do padrão. Seleciona automaticamente os
  slides mais adequados da apresentação editável de referência, preserva capa e
  agradecimentos e inspeciona visualmente cada slide renderizado. Use também
  para ajustar um .pptx existente ao padrão LMEst.
---

# Apresentações LMEst-UFU

Esta skill usa `assets/references/referencia_base.pptx` como fonte visual e
editável. O catálogo interno de `manifest.json` identifica os 19 slides por
índice e descrição. Leia as prévias renderizadas do deck e escolha, para cada
bloco de conteúdo, a referência que melhor corresponde ao assunto e à forma
dos dados. A escolha é do agente: não peça ao usuário que selecione uma
composição. O usuário pode acrescentar uma descrição visual opcional em um
blockquote logo após o heading do slide. Use-a para escolher e compor a
referência, sem inserir o texto do blockquote no slide. Sem descrição, decida
a composição pelo conteúdo. Blockquotes são reservados exclusivamente para
essas descrições; se algum não descrever visualmente o slide, interrompa a
geração e explique o problema ao usuário.

Nos slides de conteúdo, priorize explicar visualmente: procure oportunidades
para usar formas, gráficos, diagramas, fluxogramas, linhas do tempo e outros
elementos gráficos nativos e editáveis do PowerPoint. Use-os quando ajudarem a
compreender os dados, relações, etapas ou conceitos; não invente dados nem
force elementos decorativos. Preserve a estrutura fixa da capa e dos
agradecimentos.

Leia a skill pública de PowerPoint (`/mnt/skills/public/pptx/SKILL.md`) para
orientações de manipulação e validação do arquivo. Em caso de conflito visual,
prevalecem a apresentação de referência e este design system.

## Mapa da skill

| Arquivo | Quando ler |
|---|---|
| `docs/entrada_markdown.md` | sempre: entradas, estrutura Markdown e front matter |
| `docs/entrada_pptx.md` | quando a fonte for um PPTX fora do padrão LMEst |
| `docs/saida_html.md` | quando a entrega escolhida for HTML |
| `docs/design_system.md` | antes de compor: identidade visual, catálogo numerado e densidade |
| `docs/slides_rigidos.md` | capa, agradecimentos e transições |
| `docs/equacoes.md` | se houver matemática |
| `docs/qa.md` | durante a revisão visual e estrutural |
| `assets/references/refs_description.md` | ao escolher referências entre os slides |
| `examples/gerar_exemplo.py` | exemplo da API de montagem e composição |

## Entradas aceitas

- **Markdown + imagens** (preferida): ZIP, pasta, `.md` com imagens ao lado,
  ou `.md` + `--imagens DIR_OU_ZIP`.
- **PDF** (alternativa). Ao receber PDF, explique na primeira resposta que
  Markdown com imagens preserva melhor equações, figuras vetoriais, ordem e
  dados da capa; em seguida, processe o PDF, salvo se o usuário preferir enviar
  Markdown.
- **PPTX fora do padrão LMEst**: use o fluxo de reconstrução de
  `docs/entrada_pptx.md`; preserve o conteúdo visível e sua ordem, mas use o
  tema e a identidade visual LMEst no deck final.
- Se Markdown e PDF forem enviados juntos, use o Markdown.

## Escolha do formato de saída

Antes de construir a apresentação, confirme se o usuário quer PPTX ou HTML
quando ele ainda não tiver dito. Faça uma pergunta curta e aguarde a resposta.
Se o formato já estiver explícito, siga-o sem perguntar novamente. Se pedir os
dois, gere ambos independentemente a partir do mesmo conteúdo e plano.

## Fluxo: criar apresentação

Trabalhe em `work/` e mantenha a entrada original intacta. `$SKILL` é a pasta
desta skill.

1. **Preparar a entrada**: rode
   `python3 $SKILL/scripts/prepare_input_bundle.py ENTRADA work [--imagens DIR_OU_ZIP]`.
   Para um PPTX, o comando extrai textos, tabelas, dados de gráficos, formas,
   conectores, imagens e candidatos a equação para `input_manifest.json`,
   extrai as mídias e renderiza todos os slides em `work/source_render/`.
   Siga `docs/entrada_pptx.md`: confira todas as renderizações contra o
   inventário antes de montar. Se texto, equação, gráfico ou relação estiver
   ambíguo, pergunte ao usuário pelo trecho exato e espere resolver as dúvidas
   antes de gerar o deck. Para capa e agradecimentos, use somente os dados
   claros na fonte; pergunte se faltarem campos ou se o conteúdo for ambíguo.
   Código 5 indica rascunho de PDF para revisão conforme `docs/entrada_markdown.md`;
   código 2 indica imagens ausentes; código 3 indica dados de capa incompletos;
   código 4 indica pacote/PPTX inválido ou PPTX não renderizável; código 6 indica blockquote vazio ou fora da
   posição reservada para descrição; informe o diagnóstico e pare se ocorrer.
   Para Markdown, depois de preparar, leia `slides[].description`:
   se algum blockquote não for uma descrição visual do slide, interrompa antes
   de montar o deck e informe o usuário.
2. **Renderizar equações** se `resumo.equacoes_*` for maior que zero, usando
   `scripts/render_equations.py`.
   Para entrada PPTX, transcreva os candidatos e fórmulas identificados na
   inspeção visual para LaTeX, confirme símbolos e índices com o usuário
   quando houver dúvida e renderize cada expressão antes de inserir.
3. **Criar prévias visuais da referência** em diretório temporário de trabalho:
   `python3 $SKILL/scripts/render_deck.py $SKILL/assets/references/referencia_base.pptx work/reference_render`.
   Use essas imagens e `refs_description.md` para escolher, por conteúdo, o
   slide de referência mais adequado a cada bloco Markdown ou slide PPTX de
   origem. Não solicite que o usuário selecione ou memorize layouts.
4. **Planejar a ordem**: capa do slide 1 sempre primeiro; agradecimentos do
   slide 19 sempre por último. Preserve a ordem dos blocos Markdown ou dos
   slides de conteúdo PPTX. Em Markdown, use `description` para orientar a
   escolha da referência e trate somente o texto fora do blockquote como
   conteúdo. Em PPTX, registre `input_slide` nas entradas que vêm da fonte,
   incluindo capa e agradecimentos quando mapeados. Índices repetidos são
   permitidos para dividir um slide denso, desde que permaneçam em ordem não
   decrescente. Para Markdown, use `md_slide`. Insira a transição do slide 5
   quando a estrutura de seções pedir. Slides de referência podem ser
   reutilizados e duplicados. Quando nenhum slide se adequar, marque uma
   composição limpa baseada no cabeçalho e rodapé de um slide de conteúdo;
   componha o corpo com os elementos nativos da API.
   Se a saída escolhida for HTML, siga `docs/saida_html.md` para compor e
   renderizar o pacote; os passos 5–10 abaixo são específicos para PPTX.
5. **Montar a estrutura** com `scripts/assemble_deck.py`. O plano usa
   `source_slide` (índice 1–19), opcionalmente `md_slide` ou `input_slide` e `clean: true` para
   limpar o corpo preservando o cabeçalho, a marca e o rodapé.
6. **Preencher e compor** com `scripts/lmest_pptx.py`:
   - use `fill_cover`, `fill_divider` e `fill_thanks` para preencher os campos
     editáveis dos slides 1, 5 e 19 sem alterar posições ou elementos visuais;
   - nos slides de conteúdo, substitua ou remova todo texto, imagem ou dado de
     exemplo. Preserve os elementos de marca e a estrutura visual que orientou
     a escolha. Procure uma representação gráfica adequada ao conteúdo e
     prefira objetos editáveis do PowerPoint: `add_chart` para dados fornecidos,
     diagramas e conectores para relações ou processos, e formas/cards para
     organizar conceitos. Use `set_title`, `set_text`, `add_text`,
     `add_picture`, `add_equation`, `add_table`, `add_chart` e `add_connector`
     conforme necessário; não invente valores ou relações nem force adornos;
   - tabelas e gráficos devem ser objetos nativos editáveis do PowerPoint;
     figuras de gráficos enviados pelo usuário podem permanecer como imagens;
   - passe conteúdo complementar para `set_notes`. Execute `renumber`,
     `audit` e `leftovers` antes de salvar.
7. **Validar e renderizar**: valide o PPTX com a ferramenta pública de PowerPoint
   e gere todas as páginas com
   `python3 $SKILL/scripts/render_deck.py work/deck.pptx work/render`.
8. **Inspecionar visualmente** cada imagem de `work/render/slide-NNN.png`, lado
   a lado com a imagem da referência escolhida. Se a origem for PPTX, compare
   também com `work/source_render/slide-NNN.png` conforme `input_slide` e
   reconcilie todo o inventário com o deck final. Consulte `docs/qa.md`; verifique
   composição, hierarquia, dados, texto, alinhamento e elementos de marca. O
   relatório de `evaluate_render.py` verifica estrutura e cria comparações
   lado a lado, mas a aprovação visual é feita pelo agente.
9. **Corrigir** em até 3 ciclos de edição, renderização e inspeção. Se ainda
   houver desvios após o terceiro ciclo, relate-os claramente na entrega.
10. **Entregar** o PPTX (e PDF se útil) em `/mnt/user-data/outputs/`. Para
    origem PDF, liste equações transcritas e imagens recortadas para conferência.

## Fluxo: gerar HTML

Siga primeiro as etapas comuns de preparação, resolução de dúvidas, seleção de
referências e plano de slides acima. Depois use `docs/saida_html.md` e os
recursos `assets/html/lmest_presentation.css` e
`assets/html/lmest_presentation.js` para criar um pacote HTML local. Construa
HTML/CSS/SVG diretamente; não exporte o PPTX para HTML. Renderize cada slide
com `scripts/render_html_deck.cjs`, inspecione todos os PNGs e faça até três
ciclos de correção. Entregue a pasta `index.html` + recursos locais, ou um ZIP
da pasta, mantendo a apresentação funcional sem rede.

## Fluxo: ajustar apresentação existente

Renderize o PPTX, compare cada slide com as referências mais próximas e aplique
os tokens e regras de `docs/design_system.md`. Se o deck estiver distante do
padrão LMEst, reconstrua-o a partir do próprio PPTX seguindo
`docs/entrada_pptx.md`; edite no lugar quando ajustes locais forem suficientes.

## Regras essenciais

- Capa e agradecimentos são obrigatórios; use as estruturas dos slides 1 e 19
  e altere apenas seus campos de conteúdo documentados em `slides_rigidos.md`.
- As demais referências, inclusive a transição do slide 5, podem mudar de
  posição ou ser reutilizadas conforme a estrutura do conteúdo.
- Se não houver referência adequada, componha um corpo limpo com a identidade
  LMEst e objetos editáveis. Não invente conteúdo.
- Use Calibri em textos novos; não use SmartArt nem temas prontos de Office.
- Equações são PNGs produzidos por `render_equations.py`, em tamanho nativo,
  com LaTeX no texto alternativo.
- Preserve números, unidades, nomes, equações e sentido do conteúdo. Condense
  somente dentro das regras de `docs/entrada_markdown.md`; respeite `literal`.
- Não conclua sem renderizar e inspecionar visualmente todas as páginas.
