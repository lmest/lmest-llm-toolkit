# Saída HTML

## Escolha do formato

Antes de começar a compor, confirme se a entrega deve ser **PPTX ou HTML** caso
o usuário ainda não tenha escolhido. Pergunte uma vez e aguarde a resposta antes
de construir os slides. Se o formato já estiver explícito, siga essa escolha.

## Estratégia: construir HTML diretamente

Para uma apresentação HTML, recrie diretamente em HTML, CSS e SVG usando o
mesmo conteúdo, a mesma ordem e as mesmas decisões de composição do fluxo
LMEst. **Não converta o PPTX pronto em HTML como caminho padrão.** A conversão
costuma carregar as limitações do renderizador, dificulta controlar layouts
responsivos e acessíveis e não oferece uma base confiável para interação e
animação. A construção direta permite aplicar os tokens LMEst de forma
explícita e decidir quais interações ajudam a explicar o conteúdo.

Se o usuário pedir PPTX e HTML, produza os dois a partir da mesma fonte de
conteúdo, inventário e plano de slides, mas componha cada formato diretamente.
Não use um arquivo exportado do outro como fonte. Assim, ordem, títulos, dados,
equações, legendas e sentido permanecem alinhados.

## Pacote do HTML

Entregue um diretório autônomo — ou um ZIP desse diretório — com:

```text
apresentacao-html/
  index.html
  assets/
    lmest_presentation.css
    lmest_presentation.js
    imagens/       # logos, fotos e figuras locais
    equacoes/      # equações renderizadas, se houver
```

Comece copiando os recursos comuns:

```bash
mkdir -p work/html/assets/imagens work/html/assets/equacoes
cp "$SKILL/assets/html/lmest_presentation.css" work/html/assets/
cp "$SKILL/assets/html/lmest_presentation.js" work/html/assets/
```

Escreva `work/html/index.html` com um elemento `<main class="lmest-player">`,
um `div#lmest-stage` e um `<section class="lmest-slide">` por slide. Carregue
os dois recursos locais. Marque cada slide como `lmest-slide--cover`,
`lmest-slide--content`, `lmest-slide--divider` ou `lmest-slide--thanks` e use
os componentes CSS abaixo para manter a identidade. O primeiro e o último
slides seguem as mesmas regras de conteúdo e estrutura fixa definidas em
`slides_rigidos.md`; capa abre a apresentação e agradecimentos encerram.

Estrutura mínima de navegação e um slide de conteúdo:

```html
<main class="lmest-player">
  <div id="lmest-stage" class="lmest-stage">
    <section class="lmest-slide lmest-slide--content is-active"
             role="group" aria-roledescription="slide" aria-label="2: Resultados">
      <header class="lmest-header">
        <h1 class="lmest-header__title">Resultados</h1>
        <img class="lmest-header__brand" src="assets/imagens/logo-lmest.png" alt="LMEst-UFU">
      </header>
      <div class="lmest-body">
        <div class="lmest-grid lmest-grid--2">
          <article class="lmest-card"><h2 class="lmest-card__title">Método A</h2><p>Resultado.</p></article>
          <article class="lmest-card lmest-card--blue"><strong class="lmest-kpi">10 min</strong></article>
        </div>
      </div>
      <footer class="lmest-footer"><span>LMEst-UFU</span><span class="lmest-footer__number">2</span></footer>
    </section>
  </div>
  <nav class="lmest-controls" aria-label="Navegação da apresentação">
    <button type="button" data-lmest-action="previous" aria-label="Slide anterior">‹</button>
    <span class="lmest-controls__count" data-lmest-count></span>
    <button type="button" data-lmest-action="next" aria-label="Próximo slide">›</button>
    <span class="lmest-controls__track" role="progressbar" aria-label="Progresso">
      <span class="lmest-controls__progress" data-lmest-progress></span>
    </span>
    <button type="button" data-lmest-action="fullscreen" aria-label="Tela cheia">⛶</button>
  </nav>
</main>
<script src="assets/lmest_presentation.js" defer></script>
```

Repita a seção para cada slide e inclua um heading principal acessível em cada
uma. O runtime ativa o primeiro slide por padrão.

## Identidade visual e conteúdo

- Use exatamente os valores de cor `--lmest-*` definidos no CSS, que espelham
  `manifest.json`; não crie uma paleta alternativa.
- Use `Calibri, Carlito, Arial, sans-serif`. Calibri corresponde ao arquivo
  PowerPoint; Carlito é a alternativa métrica próxima. Não dependa de fontes
  remotas nem incorpore fontes sem licença.
- Mantenha tela 16:9 e o cabeçalho navy, filete vermelho, logos e rodapé nas
  posições da referência LMEst escolhida. As capas e os agradecimentos usam o
  fundo navy e os campos editáveis definidos em `slides_rigidos.md`.
- Copie para o pacote as logos institucionais que aparecem nas referências
  escolhidas e que são necessárias ao deck. Se precisar extraí-las, rode
  `extract_pptx_content.py` sobre o PPTX de referência e selecione as mídias
  corretas pelo inventário e pelas prévias; inclua somente as imagens usadas.
- Faça o palco adaptar-se ao viewport sem alterar a proporção. Use a imagem da
  referência apenas como guia visual; construa o conteúdo com HTML/SVG/CSS, sem
  colocar uma captura do slide de referência como fundo.
- Preserve todos os textos, números, unidades, relações, dados e figuras da
  fonte. Gráficos devem usar SVG ou elementos HTML com os dados fornecidos;
  tabelas devem ser `<table>`; diagramas e conectores devem ser vetores SVG ou
  formas HTML. Use imagens fornecidas/extraídas quando não houver base para
  reconstruir uma figura fielmente. Equações devem ser transcritas em LaTeX,
  conferidas e renderizadas antes de inserir, como no fluxo PPTX.
- Marque imagens com texto alternativo e gráficos/diagramas com título,
  descrição e rótulos acessíveis. Elementos SVG interativos devem ser
  focalizáveis por teclado e informar valores/rótulos sem depender apenas da
  cor.

## Animação e interação

O runtime fornece navegação por setas, Page Up/Down, Home/End, toque, botões,
contador, barra de progresso e tela cheia. Mantenha esses controles. Use
transições discretas entre slides; `prefers-reduced-motion` deve ser
respeitado. Revele etapas em sequência, adicione tooltips ou permita expandir
detalhes somente quando a interação facilitar a compreensão. Não esconda
informação essencial atrás de uma interação, não anime números de maneira que
altere seu sentido e não adicione movimento decorativo sem propósito.

Elementos HTML nativos como `<details>` são preferíveis para expansões simples.
Para um botão de revelação controlado pelo runtime, use
`data-lmest-reveal="#id-do-conteudo"` e mantenha `aria-expanded` atualizado.
Para sequências animadas que aparecem ao entrar no slide, aplique
`class="lmest-animate"` aos elementos. Use `data-transition="none"` ou
`data-transition="fade"` quando o deslocamento padrão não servir.

## Navegação e estrutura semântica

Cada slide deve ter `role="group"`, `aria-roledescription="slide"` e um
`aria-label` que inclua número e título. Use um único heading principal por
slide. Use botões com rótulos acessíveis, ordem de tabulação natural e foco
visível. Não intercepte teclas enquanto o foco estiver em campos editáveis.
Não inclua bibliotecas, fontes ou conteúdo carregados por CDN: o pacote deve
funcionar sem rede ao abrir `index.html` localmente.

## Renderização e inspeção

Renderize todos os slides HTML em PNG de 1920 × 1080, sem transições em curso:

```bash
NODE=/caminho/fornecido/pelo/runtime/node
NODE_MODULES=/caminho/fornecido/pelo/runtime/node_modules
NODE_PATH="$NODE_MODULES" "$NODE" "$SKILL/scripts/render_html_deck.cjs" \
  work/html/index.html work/html_render
```

Se o Chromium estiver instalado fora do cache de Playwright, indique seu
executável com `LMEST_CHROMIUM=/caminho/para/chromium`.

No Codex desktop, obtenha os caminhos usando `load_workspace_dependencies`.
Playwright e Chromium precisam estar instalados no runtime. Se o Chromium não
iniciar, use uma ferramenta de prévia visual aprovada no ambiente; se não
houver uma, informe que a inspeção visual está pendente em vez de alegar que
foi feita. Não baixe nem instale um navegador automaticamente. Inspecione todos os PNGs contra a
referência LMEst correspondente e, se a fonte for PPTX, contra cada slide de
origem mapeado por `input_slide`. Confira composição, legibilidade, proporção,
elementos cortados, gráficos, navegação, imagens, equações e comportamento de
interações. Consulte `qa.md` e faça até três ciclos de correção. Os PNGs servem
para inspeção e não substituem `index.html` como entrega.
