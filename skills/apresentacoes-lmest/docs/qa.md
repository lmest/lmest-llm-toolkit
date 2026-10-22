# QA de apresentações LMEst

A revisão tem uma camada estrutural automática e uma inspeção visual obrigatória
de cada slide. A aparência é comparada com a prévia do slide de referência que
foi usado na montagem. As prévias são renderizadas sob demanda e ficam em
`work/reference_render/`; não há PNGs ou JPGs de referência persistentes em
`assets/`.

Quando a entrada for um PPTX, `work/source_render/` contém também uma prévia de
cada slide de origem. Reconcilie o inventário e essas imagens com o plano final
por meio de `input_slide`; um slide de origem pode estar ligado a vários slides
finais quando foi dividido.

## Checagens automáticas

1. Rode `L.audit(prs)` antes de salvar: sem objetos fora do canvas, estouros de
   texto conhecidos ou numeração inconsistente.
2. Rode `L.leftovers(prs)`: nenhum texto de exemplo da apresentação de
   referência pode permanecer sem intenção.
3. Valide o PPTX com a ferramenta pública de PowerPoint.
4. Renderize todas as páginas com `render_deck.py` e rode:

   ```bash
   python3 scripts/evaluate_render.py work/render --plano work/deck_plan.json \
     --referencias work/reference_render
   ```

   Para reconstrução de PPTX, acrescente
   `--entrada-pptx-render work/source_render`. O relatório cria também pares
   com o slide da fonte para cada slide final que contém `input_slide`; índices
   repetidos são válidos desde que estejam em ordem não decrescente.

   A ferramenta confirma contagem e proporção 16:9, verifica os limites de
   posição da capa e dos agradecimentos e salva imagens lado a lado em
   `work/render/comparacoes/slide-NNN.png`. Ela não aprova composição por
   diferença de pixels: o agente deve examinar os pares.

## Inspeção visual

Abra toda imagem `work/render/slide-NNN.png` junto à referência indicada pelo
`source_slide` no `deck_plan.json`. Inspecione cada página, inclusive capa,
transições e agradecimentos. Confira:

- composição e hierarquia visual adequadas ao conteúdo e à referência;
- slides de conteúdo não excessivamente textuais: quando dados, etapas,
  relações ou conceitos puderem ser explicados melhor visualmente, verificar
  se foram usados gráficos, diagramas, fluxogramas ou formas apropriadas;
- títulos, textos e legendas legíveis, sem corte, sobreposição ou excesso;
- alinhamento, margens, intervalos, contraste e consistência de cores;
- tabelas, gráficos e conectores compreensíveis e editáveis quando nativos;
- fidelidade dos elementos gráficos à fonte: sem valores, etapas ou relações
  inventados; imagens mantidas quando não houver base suficiente para
  reconstrução fiel;
- figuras técnicas sem corte, equações corretas e com corpo uniforme;
- logos, ícones fixos e numeração preservados;
- ausência de conteúdo de exemplo que veio da apresentação-base;
- fidelidade de números, unidades, nomes, equações e sentido à fonte.

Para entrada PPTX, confira cada `source_render/slide-NNN.png` contra o
inventário e os slides finais correspondentes por `input_slide`. Verifique que
todo conteúdo visível da fonte aparece no deck, inclusive o que não foi
extraído automaticamente. Preserve a sequência original, mesmo quando um
slide denso gerar várias páginas. Equações devem corresponder à fonte e ser
renderizadas a partir de LaTeX; tabelas, gráficos e diagramas devem preservar
seus dados e relações. Antes de montar, resolva com o usuário qualquer
conteúdo ambíguo e confirme os dados de capa e agradecimentos que não estejam
claros na apresentação de origem.

Uma composição sem correspondência exata ainda deve manter a identidade LMEst
e ser equilibrada. Se nenhum layout de referência servir, compare o slide limpo
com a referência visual de origem usada para preservar cabeçalho e marca.

## Ciclos de correção

Faça até três ciclos de edição, renderização e inspeção. Em cada ciclo,
renderize todas as páginas novamente e revise todas; se o deck for longo,
priorize as imagens alteradas, mas não omita a checagem final completa. Se
restar algum desvio após o terceiro ciclo, informe-o na entrega.

## Limitação do render

O render usa LibreOffice. Calibri/Carlito mantém métricas próximas, mas o
antialiasing e algumas sombras podem diferir do PowerPoint. Confirme fontes
disponíveis com `fc-list | grep -i -E 'carlito|calibri'` quando as quebras de
linha forem críticas.

## QA da saída HTML

Renderize todas as páginas com `scripts/render_html_deck.cjs` usando o Node,
Playwright e Chromium fornecidos pelo runtime do Codex. O script falha se o
runtime não carregar, houver erro de JavaScript ou alguma imagem local estiver
ausente, e grava `slide-NNN.png` em 1920 × 1080. Inspecione todos os PNGs e
confira títulos, proporção, cores, tipografia, cortes, tabelas, gráficos,
diagramas, imagens, equações e correspondência com a referência LMEst. Se a
entrada foi PPTX, compare também com os renders de origem por `input_slide`.

Teste a navegação com teclado, botões, toque e tela cheia, e acione todas as
interações deliberadas. Verifique que a apresentação funciona abrindo o HTML
localmente sem rede, que os controles têm rótulos e foco acessíveis e que a
opção de movimento reduzido continua legível. As animações devem apoiar a
compreensão; o conteúdo essencial precisa permanecer disponível sem interação.
