# Componentes do Design System LMEst-UFU

Guias copiados de project/components/*/README.md do Design System (escala de 960×540: multiplique as medidas por 2 no palco de 1920×1080).

## BudgetBars

### BudgetBars

Linhas de orçamento, ordenadas da maior para a menor, com a barra proporcional ao valor.

**O consumidor fornece** rótulo, valor e percentual de cada linha.

Rótulo e valor a 14px; trilho `surface` de 21 de altura; barra em `navy`, `steel`, `blue` e `red`, nessa ordem de peso. Termine com o total em bold `red`.

**Não** use para séries temporais nem mais de oito linhas.

## Callout

### Callout

A frase que o público deve levar, separada do resto do slide.

**O consumidor fornece** o texto, com a abertura em bold, e opcionalmente um ícone.

- Padrão `tint-blue`: observação. `--line`: objetivo ou proposta. `--alert`: desafio, risco ou diferencial, em `tint-red`. `--dark`: fechamento do slide, em `navy`.
- No máximo um por slide, em geral na base.

**Não** use filete lateral colorido: a variante é dada pelo fundo.

## Chips

### Chips

Abas de fase, pills de contexto e etiquetas de campanha.

**O consumidor fornece** os rótulos e qual aba está ativa.

- `.lm-tab`: fase do projeto; a ativa em `navy`, as demais em branco com texto `subtle` (par da fonte, 2,4:1: é de propósito pouco visível, mas não ponha informação nova só ali).
- `.lm-pill`: período (`tint-blue`), maturidade (`--dark`), meta (`--red`) ou proposta (`--outline`). Em CAIXA ALTA, com intervalos em meia-risca.
- `.lm-tag`: código curto como C1 a C5. Sobre `blue` o texto `white` fica a 3,9:1.

## DataTable

### DataTable

Tabela densa com cabeçalho escuro e linhas alternadas.

**O consumidor fornece** as colunas e as linhas; a coluna de valor recebe a classe `.num`.

Cabeçalho `navy` com texto `white` bold de 12px, linhas de 26,2 de altura, alternância com `surface`, filete `table-rule`. Valores à direita em bold `steel`; o valor mais importante em `red`. Em matrizes de verificação, use `✓` em `blue` e `–` em `subtle`.

## Equation

### Equation

Equação em LaTeX, renderizada com KaTeX na fonte Computer Modern, como nos slides do LMEst.

### Quando usar

- **`lm-eq`** — equação em destaque, centralizada num painel `surface` com `radius-md`, ocupando a largura do conteúdo. Use uma por slide, logo abaixo do `lead`.
- **`lm-math`** — símbolo ou expressão curta dentro do texto (`k_s`, `x_a`), no tamanho da linha.

### Cor das variáveis

Destaque só as grandezas que o slide discute, com as mesmas cores do texto ao redor:

- `\htmlClass{lm-eq-blue}{…}` — `blue`, para o que vem do sensor ou da medição.
- `\htmlClass{lm-eq-red}{…}` — `red`, para o termo que muda ou que é o ponto do slide.

O resto da equação fica em `ink`. No máximo duas cores por equação.

### O que o consumidor fornece

Carregue os dois arquivos do KaTeX 0.16.22 que vêm no próprio design system, sem CDN: `components/Equation/katex.css` (com as fontes Computer Modern embutidas) e `components/Equation/katex.min.js`. Depois renderize cada elemento com `data-tex`:

```html
<link rel="stylesheet" href="components/Equation/katex.css">
<script src="components/Equation/katex.min.js"></script>

<div class="lm-eq" data-tex="F = k_i\,\htmlClass{lm-eq-blue}{i(x_s)} + k_s\,\htmlClass{lm-eq-red}{x_a}"></div>

<script>
document.querySelectorAll('[data-tex]').forEach(function (el) {
  katex.render(el.getAttribute('data-tex'), el, {
    displayMode: el.classList.contains('lm-eq'),
    trust: function (c) { return c.command === '\\htmlClass'; },
    strict: false, throwOnError: false
  });
});
</script>
```

`trust` libera apenas `\htmlClass`, necessário para as cores. Para PowerPoint, insira a equação pelo editor de equações nativo (Inserir › Equação, modo LaTeX) com as mesmas cores.

## GanttChart

### GanttChart

O cronograma por fase, em barras dentro de trilhos.

**O consumidor fornece** as fases, a posição de cada barra em percentual da duração total e o intervalo em meses.

Rótulo em `heading-sm`; trilho `surface` de 33,5 de altura; barra de 27,5 com 3 de folga, `radius-sm`, texto `white` de 12,5 bold com o intervalo (`M13–48`, com meia-risca). `red` marca a fase que é ampliação proposta ou a mais crítica.

## InfoCard

### InfoCard

O cartão básico: disco com ícone, título e uma frase. Versão simples sem texto: `.lm-tile`, com altura de 66,2.

**O consumidor fornece** o ícone, o título e o texto.

Fundo `white`, contorno `line` de 0,8, `radius-md`, `shadow-card`. Em grades, alterne discos `blue` e `steel`. Reserve `navy` e `red` para quem deve se destacar. Espaço entre cartões: `space-sm`.

**Não** use filete colorido na borda do cartão; a cor do cartão vem do disco.

## LogoWall

### LogoWall

As marcas parceiras, agrupadas sob um título.

**O consumidor fornece** o título do grupo e a lista de logos do grupo de assets `Parceiros`.

Painel branco com contorno `line`; logos sem alterar cor, com até 40 de altura. Separe empresas, academia no Brasil e academia no exterior.

**Não** coloque logos de terceiros sobre fundo colorido, nem cite parceria que não possa ser confirmada.

## ProcessFlow

### ProcessFlow

Uma cadeia horizontal, da entrada à decisão.

**O consumidor fornece** de quatro a seis etapas de até duas linhas.

Caixas de 119,9 × 44,6, `radius-flow`, contorno de 1,5, texto de 11 bold na cor do contorno. Início e fim em `navy` preenchido; o meio usa a cor da linha de pesquisa envolvida. Setas em `subtle`.

## SlideClosing

### SlideClosing

O slide final: agradecimento, contato e, à direita, a parede de marcas numa placa branca.

**O consumidor fornece** o nome, a função, o contato e as marcas pertinentes ao público.

Contatos com ícones de 18,7px, texto a 14,5px em `white`. Redes sociais em ícones de 15px, com `@lmest.ufu` em `caption` `mist`.

## SlideCover

### SlideCover

A capa: fundo institucional, identificação do laboratório e os três logos numa placa branca.

**O consumidor fornece** o sobretítulo, o título, o nome e o contato do apresentador.

- Sobretítulo em `eyebrow`, `sky`, sempre começando por “LMEst-UFU ·”.
- Título em `cover-title`, `white`. Identificação completa do laboratório em `mist`, com o nome “Prof. José Eduardo Tannús Reis” entre aspas curvas.
- A placa traz UFU, LMEst e INCT, nessa ordem.

**Não** troque o fundo por cor chapada nem coloque logos diretamente sobre o escuro.

## SlideFrame

### SlideFrame

O slide de conteúdo: a faixa `navy`, o filete `red`, o título e a placa de logos à direita.

**Use em** todo slide de conteúdo. O título afirma a mensagem do slide, em uma linha.

**O consumidor fornece** o título, o conteúdo dentro de `.lm-body` e o número da página.

- Geometria: faixa `navy` de 72, filete em y = 70,6 com 3,6 de altura, margens de 44,6, título em `slide-title`, número da página em y ≈ 512, 10px bold `blue`.
- Variante `- Comece o conteúdo com uma frase em `lead`, depois os blocos.

**Não** mude a altura da faixa entre slides, não mova a placa, não use logos sem a placa branca.

## SlideSection

### SlideSection

A divisória entre partes de um deck longo.

**O consumidor fornece** o número em romanos, o título e uma linha de subtítulo.

**Use** só em decks longos: a versão curta das apresentações dispensa divisórias. Texto alinhado à esquerda e centrado na altura; placa pequena no canto inferior direito.

## StatBand

### StatBand

A faixa escura que encerra um slide com o argumento mais forte.

**O consumidor fornece** um rótulo e de dois a três pares de número e frase.

Fundo `navy`, rótulo e números em `sky`, frases em `white`. Use no máximo uma por slide, na parte de baixo.

Variante de número único: fundo `surface`, número em `stat-xl` `red`, frase em `heading-sm` regular.

## StatCard

### StatCard

Um número grande e o que ele conta, em uma linha de legenda.

**O consumidor fornece** o número e a legenda.

- Número em `stat-sm`. Legenda em `body`, `muted`.
- Na mesma grade, a primeira fileira pode ir em `red` (produção) e a segunda em `ink` (estrutura): é o que as fontes fazem. Nunca mais que duas cores.
- Quantifique como as fontes: `200+`, `R$ 70 mi+`, `≈80`.

**Não** arredonde um número só para caber, nem use número sem legenda.

## StepCard

### StepCard

Etapa numerada com cadência ou prazo em pill.

**O consumidor fornece** o número, o título, o texto da pill e uma frase.

Disco de 30,2 com número em 15 bold; pill de 19,4 em `tint-blue`; descrição em `caption`. O passo que mais importa vai no modo escuro (`.lm-card--dark`, disco e pill `red`). Só um por grupo.

## Timeline

### Timeline

A trajetória por ano, com marcos alternados acima e abaixo de um eixo.

**O consumidor fornece** o ano e uma ou duas frases por marco.

Eixo `navy` de 2; círculos de 18,7 em branco com contorno de 2,5; cartões de 151,2 de largura. Marcos acima em `blue`, abaixo em `red`, ano em 15 bold e texto em `body-sm`. Passo de 80,7 entre marcos.

## ToolCard

### ToolCard

Item leve, sem contorno, para listas de ferramentas e referências.

**O consumidor fornece** o ícone, o nome e uma linha de descrição.

Fundo `surface`, `radius-md`, disco de 33,1. Use quando o conteúdo é secundário e precisa pesar menos que um InfoCard.

## TrlRamp

### TrlRamp

A escada de maturidade tecnológica, na escala TRL da API, com a meta em destaque.

**O consumidor fornece** a meta (por padrão TRL 6) e, se quiser, o painel da esquerda.

Oito colunas de 75,6 de largura, subindo 11,75 a cada degrau, de `trl-0` a `trl-7`. A meta fica em `red` com a pill “META” acima e a legenda em bold `red`. Se a meta mudar, mova o vermelho e a pill juntos.

Nas fontes, os rótulos brancos sobre TRL 2 e TRL 3 ficam abaixo de 4,5:1. Em materiais novos, prefira `navy` nesses degraus.
