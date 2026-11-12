# Animações

**Só quando o usuário pedir, e só nas saídas HTML e artefato Slides.** Se a saída PPTX também for pedida, avise que o PPTX não leva animações e pergunte se as quer mesmo assim. Nesse caso, gere o PPTX a partir de uma cópia do projeto com cada `<x-embed>` trocada pelo desenho estático, ou não gere o PPTX. `gerar_pptx.py` para com erro se encontrar uma `<x-embed>`.

Os slides de referência são da "Introdução à IA Generativa": 21 (`l-tokens`), 18 (`l-def`), 24 (`l-lento`), 8 (`h-linha`), 23 (`l-autoreg`), 25 (`l-contexto`), 26 (`modelos-esforco`), 22 (`l-numeros`) e 15 (`t-venn`).

## O que o usuário quer

- **Roda sozinha, de uma vez, ao entrar no slide.** Sem cliques, sem passos. Ao voltar ao slide, recomeça do início, inteira.
- **Ao sair do slide, a animação é zerada**, não congelada no meio.
- **Segue a ordem de leitura**: da esquerda para a direita, ou a ordem lógica do conteúdo.
- **Nunca usar `data-build-in`.** Ele faz cada pedaço aparecer separado ao voltar o slide, e o usuário rejeitou esse resultado.

## Como implementar

1. **Uma única `<x-embed>` por animação**, filha direta da `<section>`, fixada (`position:absolute` com `top`, `left`, `width`, `height`) sobre a área que a animação ocupa. Até 8 por slide e 16 KB cada. Os elementos que não se animam (título, rodapé, número, textos de outros blocos) ficam fora dela, como elementos normais do slide.
2. **Minipágina**: `<style>` com `html,body{margin:0;padding:0;overflow:hidden;background:transparent}` e `p{margin:0}` (sem esse reset o parágrafo desce), um contêiner `<div id="c">` com posição absoluta e o tamanho da `<x-embed>`, e o `<script>` no fim. Sem dependências externas.
3. **Nada de layout em fluxo na minipágina**: todo elemento é `position:absolute` com `top` e `left` fixos.
4. **Gatilho**: `IntersectionObserver` com `threshold:[0,0.5,1]` sobre `#c`. Quando `isIntersecting && intersectionRatio>=0.5`, adiciona a classe `on` (ou chama `play()`); quando sai, remove a classe (ou chama `reset()`).
5. **Estado inicial oculto** (`opacity:0`, `scale(0)`, `scaleX(0)`); a classe `on` dispara as animações CSS com `animation-delay` em sequência. Alternativa: Web Animations API (`el.animate(keyframes,{duration,delay,easing,fill:'both'})`), guardando as animações num array para cancelá-las no `reset()`.
6. **Impressão do HTML offline**: o gerador manda a mensagem `lm-final` para cada minipágina, que então adiciona `on` a `#c` e leva todas as animações ao fim. Se a animação usa `play()`, defina também `window.lmFinal = function(){ play(); }` para o estado final aparecer no PDF.
7. **Fontes**: a minipágina não herda as fontes do slide. Use `font-family:Carlito,Calibri,sans-serif`. Textos com no mínimo 24 px.
8. **Imagens dentro da minipágina**: ela não carrega arquivos (`lmest/…`, `imagens/…`, `/_blob/…`). Use SVG inline ou `data:` WebP reduzido ao tamanho exibido (até ~88 px). Confira se o total continua abaixo de 16 KB.
9. **Cores**: as do slide. Azul `#2f6690` para elementos normais, vermelho `#c41e2a` para o destaque, cinza `#d6dee6` para eixos e grade.

### Modelo de minipágina

```html
  <x-embed style="position:absolute; top:270px; left:89px; width:847px; height:690px">
<style>
html,body{margin:0;padding:0;background:transparent;overflow:hidden;font-family:Carlito,Calibri,sans-serif}
p{margin:0}
#c{position:absolute;left:0;top:0;width:847px;height:690px}
.a{position:absolute;white-space:nowrap;line-height:1.2}
.item{opacity:0;transform:translateY(20px)}
.on .item{animation:entra .5s cubic-bezier(.2,.8,.2,1) forwards}
.on .i1{animation-delay:.2s}.on .i2{animation-delay:.45s}.on .i3{animation-delay:.7s}
@keyframes entra{to{opacity:1;transform:none}}
</style>
<div id="c">
  <p class="a item i1" style="left:40px;top:40px;font-size:30px;color:#1b2b3a">Primeiro</p>
  <p class="a item i2" style="left:40px;top:100px;font-size:30px;color:#1b2b3a">Segundo</p>
  <p class="a item i3" style="left:40px;top:160px;font-size:30px;font-weight:700;color:#c41e2a">Destaque</p>
</div>
<script>
(function(){
  var c=document.getElementById('c');
  if(!('IntersectionObserver' in window)){ c.classList.add('on'); return; }
  new IntersectionObserver(function(es){
    es.forEach(function(e){ c.classList.toggle('on', e.isIntersecting && e.intersectionRatio>=0.5); });
  },{threshold:[0,0.5,1]}).observe(c);
})();
</script>
  </x-embed>
```

Remover a classe `on` volta tudo ao estado inicial, e por isso a animação recomeça ao voltar.

## Tempos típicos (medidos nos slides de referência)

- Entrada de texto ou caixa: 0,4 a 0,7 s, `cubic-bezier(.2,.8,.2,1)`, deslocamento de 8 a 40 px.
- Ponto ou marcador com "pulo": 0,26 a 0,45 s, `cubic-bezier(.34,1.56,.64,1)` ou `(.3,1.4,.5,1)`.
- Linha de eixo ou gráfico: 0,7 a 1,3 s, `scaleX` ou `scaleY` a partir da origem.
- Intervalo entre itens sequenciais: 0,14 a 0,32 s. Em linhas do tempo, o atraso de cada item pode ser proporcional à posição horizontal.
- Legenda final: 0,4 a 0,5 s, por último.

## Padrões aprovados

### Gráficos com eixos (slide 24, `l-lento`)

Ordem obrigatória:
1. **Eixo Y** cresce de baixo para cima (`scaleY`, `transform-origin:bottom`), em 0 s.
2. **Eixo X** cresce da esquerda para a direita (`scaleX`, `transform-origin:left`), ~0,6 s depois.
3. **Linhas de grade**, depois os **rótulos dos eixos** (valores e unidades), em ordem crescente de valor.
4. **Linha ou curva** revelada da esquerda para a direita, por `clip-path` com largura crescendo de 0 até a largura total, ou por `stroke-dasharray`. Começa depois dos eixos e da grade.
5. **Pontos** um a um, da esquerda para a direita, com "pulo", espaçados por 0,25 a 0,3 s.
6. **Rótulos de destaque** (valores nos pontos, anotações em vermelho) por último, cada um logo após o seu ponto.

Nunca desenhar pontos ou linha antes dos eixos, nem revelar fora da ordem do eixo X.

### Barras horizontais (slide 23, `l-autoreg`)

1. O cartão das barras vai inteiro para dentro da `<x-embed>`, com fundo, borda e título.
2. Posições no cartão (origem no canto superior esquerdo): título em `top:40px; left:40px`; subtítulo ~50 px abaixo; linhas de barra 22 px abaixo do subtítulo, altura 40, passo de 62 px; rótulo de categoria em `left:40px`, largura 170, `top` da linha + 2; barra em `left:230px`, `border-radius:4px`; valor em `left` = 230 + largura da barra + 20; nota 22 px abaixo da última linha.
3. Estado inicial `transform:scaleX(0); transform-origin:0 50%`. Cada barra cresce em 0,9 s, `cubic-bezier(.2,.8,.2,1)`, `forwards`, de cima para baixo, começando em 0,3 s, com 0,35 s entre barras.
4. Valor: fade de 0,4 s, 0,3 s depois do fim do crescimento da sua barra.
5. Destaque (maior valor ou o escolhido) em vermelho; demais em azul e cinza-azulado.
6. Comprimento proporcional ao valor (referência: 488, 144, 88 e 48 px para 61%, 18%, 11% e 6%).

### Colunas verticais (slide 26, `modelos-esforco`)

1. Cada coluna cresce de baixo para cima, a partir da base comum (`transform-origin:50% 100%`, `scaleY` de 0 a 1). Nunca de cima para baixo.
2. Da esquerda para a direita, começando em 0,2 s, com 0,2 s entre colunas; 0,7 s cada, `cubic-bezier(.2,.8,.2,1)`, `forwards`.
3. Rótulo de cada coluna: fade de 0,4 s, ~0,2 s depois do fim do crescimento dela.
4. Dimensione a minipágina para caber a coluna mais alta, o rótulo e a base.

### Barra segmentada (slide 25, `l-contexto`)

1. **Contorno primeiro**: `<rect>` SVG com `pathLength="100"`, `stroke-dasharray:100`, `stroke-dashoffset:100`, animado para 0 em 0,9 s.
2. **Seções depois, da esquerda para a direita**: `div` absoluto com `transform:scaleX(0); transform-origin:0 50%`, crescendo em 0,7 s, `cubic-bezier(.2,.8,.2,1)`, com início em 1 s, 2 s, 3 s…
3. **Texto só depois da sua seção**: começa no fim do crescimento (início + 0,7 s), letra a letra, 0,05 s por caractere (`animation-delay` calculado por JS, fade de 0,01 s).
4. As seções das pontas têm `border-radius` de 10 px nos lados externos.

### Dispersão com pontos e rótulos (slide 22, `l-numeros`)

1. Eixos com `stroke-dasharray:100` e `pathLength="100"`, para `dashoffset` 0 em 0,7 s: Y em 0 s, X em 0,6 s, Z em 1,2 s. Ponta de seta com fade logo após o eixo.
2. Pontos na ordem do eixo X, com "pulo" (0,45 s, `cubic-bezier(.34,1.56,.64,1)`), 0,3 s entre pontos, a partir de 2,2 s.
3. Cada rótulo: fade de 0,4 s, 0,25 s depois do seu ponto.

### Círculos concêntricos (slide 15, `t-venn`)

1. De fora para dentro: o círculo externo primeiro.
2. 0,6 s entre círculos, a partir de 0,2 s. Cada um cresce de `scale(.6)` e `opacity:0` até `scale(1)` e `opacity:1`, em 0,7 s, `cubic-bezier(.2,.8,.2,1)`, com `transform-box:fill-box` e `transform-origin:center`.
3. Rótulo de cada círculo: fade de 0,4 s, ~0,7 s depois do círculo. Rótulos de duas partes aparecem juntos.

### Lista ou fluxo sequencial (sem referência aprovada; use até o usuário aprovar outro)

Itens ou caixas entram na ordem de leitura, cada um de baixo para cima (0,5 s, deslocamento de 20 px, `cubic-bezier(.2,.8,.2,1)`), com 0,25 a 0,35 s entre itens. Setas entre caixas (a seta cheia de 80 × 32 px de `layouts.md` §5) crescem com `scaleX` a partir da esquerda, logo depois da caixa anterior. Detalhes de uma caixa entram depois dela.

### Texto digitado e tokens (slides 18 e 21)

O texto é digitado letra a letra (50 a 140 ms por caractere), com cursor piscando. Depois, os pedaços (tokens, palavras-chave) saem da frase e vão para a posição final, por transformação. As letras de origem ficam semitransparentes. Os IDs ou rótulos aparecem depois, e a legenda fecha a sequência.

## Checklist antes de gerar

- A animação roda sozinha ao entrar e recomeça inteira ao voltar?
- Todos os elementos começam ocultos e só aparecem pela animação?
- A ordem segue a leitura?
- A `<x-embed>` tem menos de 16 KB e não usa arquivos nem fontes externas?
- Todo texto da minipágina tem pelo menos 24 px?
- Título, rodapé, número e barra continuam fora da minipágina?
