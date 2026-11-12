# Regras de slide

Estas regras valem para todo deck da skill, em qualquer saída. Elas vêm do Design System e das correções que o usuário fez nos decks aprovados ("Introdução à IA Generativa" e "Skills para Agentes de IA Generativa").

## 1. Formato-fonte

Cada slide é um arquivo `slides/<id>.html` com **uma única `<section>`**, no subconjunto do tipo Slides do claude.ai, com uma restrição a mais: **tudo é fixado**. Assim, o mesmo arquivo vira HTML, PPTX e artefato sem mudar de aparência.

```html
<section id="<id>" data-transition="fade" style="background:#ffffff">
  ... filhos diretos, todos com position:absolute ...
  <aside>Notas do apresentador.</aside>
</section>
```

- **Todo elemento visível é filho direto da `<section>`** e tem `position:absolute; top; left; width` em px. Caixas (`div`), imagens e `x-embed` também têm `height`. Nada de layout em fluxo (`display:flex`, `grid`, `gap`, `padding` da seção). Um cartão é uma `<div>` pintada **seguida** dos textos e imagens fixados sobre ela (a ordem no arquivo é a ordem de pintura).
- Tags aceitas: `h1`, `h2`, `h3`, `p`, `ul`/`ol` com `li`, `div`, `img`, `table`, `svg`, `hr`, `x-embed`, `aside`. Dentro de texto: `<b>`, `<i>`, `<u>`, `<a href>`, `<span style="color:…">`, `<br>`. Não existem `<sub>` nem `<sup>`: use Unicode quando houver o caractere (ωₙ, xᵢ, x², 10⁻⁴); índice de palavra inteira (t_escrita) não tem Unicode: escreva "t de escrita" no texto e deixe a forma indexada na equação (`equacao.py`).
- CSS aceito: o subconjunto do tipo Slides. Proibidos: `margin`, `z-index`, `float`, unidades `em`/`rem`/`vw`/`vh`, `var()`, `<style>` (fora das minipáginas), `class`.
- Imagens: `src` relativo à pasta do projeto (`lmest/...` ou `imagens/...`). Nunca URL externa nem `data:`. Para SVG, gere também um `.png` de mesmo nome (o PPTX usa o PNG).
- Texto: sempre `font-family:Carlito, Calibri, sans-serif`, `font-size` em px (mínimo 24), `line-height` sem unidade e `color`.
- Notas: um `<aside>` não vazio, **último filho** da `<section>`, em texto simples.
- **Transição: `data-transition="fade"` em todos os slides.** Nunca deslizar nem outra. `numerar.py` garante isso.
- **Não usar `data-build-in`/`data-build-out`.** Animações só por `<x-embed>` (ver `animacoes.md`).
- Estimativa de largura de texto em Carlito: ~0,49 × `font-size` por caractere (0,53 em negrito, 0,62 em caixa alta). Dimensione cada caixa pela palavra e pela linha mais longas.

## 2. Ids e slides fixos

| Id | Slide | Número e barra |
|---|---|---|
| `capa` | Capa (gerada por `montar_fixos.py`) | Não |
| `sec-<nome>` | Divisória de parte | Não |
| `resumo` | "O que vimos hoje", só se pedido | Não |
| `agradecimento` | Agradecimento (gerado por `montar_fixos.py`) | Não |
| demais | Conteúdo | Número sempre; barra só se pedida |

Ids em minúsculas, com hífen, curtos e estáveis (`modelo-jeffcott`, `resultados-ensaio`). Ids extras sem número vão em `projeto.json > sem_numero`.

## 3. Moldura do slide de conteúdo (SlideFrame)

```html
  <div style="position:absolute; top:0; left:0; width:1920px; height:144px; background:#152536"></div>
  <div style="position:absolute; top:141px; left:0; width:1920px; height:7px; background:#c41e2a"></div>
  <h2 style="position:absolute; top:40px; left:89px; width:1480px; font-family:Carlito, Calibri, sans-serif; font-size:56px; font-weight:700; line-height:1.2; color:#ffffff">Título que afirma a mensagem</h2>
  <div style="position:absolute; top:20px; left:1613px; width:218px; height:104px; background:#ffffff; border-radius:17px"></div>
  <img src="lmest/logos/ufu.png" alt="UFU" style="position:absolute; top:34px; left:1631px; width:76px; height:76px; object-fit:contain">
  <img src="lmest/logos/lmest.png" alt="LMEst" style="position:absolute; top:34px; left:1723px; width:90px; height:76px; object-fit:contain">
```

- **Título numa linha só**: até ~50 caracteres a 56 px. Se não couber, reescreva a frase; não reduza a fonte abaixo de 48 px.
- Frase de contexto (lead), quando houver: `top:188px; left:89px; width:1742px`, 30 px, `line-height:1.4`, ink.
- **Área útil**: de y 151 (fim do cabeçalho) a y 1000 (base do conteúdo), de x 89 a 1831.
- **Número de página e barra de progresso**: nunca escreva à mão. `numerar.py` insere o número (`top:1000px; left:1631px`, 24 px, bold, `#1e88c7`, alinhado à direita) e, só se `projeto.json > barra_progresso` for `true`, a barra (`top:1073px`, 7 px, largura `round(posição × 1920 / total)`, sobre trilho `#d6dee6`).

## 4. Regras de edição aprovadas pelo usuário

- **Legenda de figura**: logo abaixo da imagem, alinhada à esquerda da imagem, texto regular de 24 px, cor `#5b6b7c`, sem negrito, sem caixa ou faixa. Não vai para o rodapé.
- **Nota de rodapé (fonte, link)**: numa única linha, texto **em negrito**, 24 px, cor `#1b2b3a`, `position:absolute; top:1000px; left:89px; width:1400px`, na altura do número de página. Links em `#17689b`, sublinhados. Sem caixa, faixa ou fundo colorido. Exemplo: `Fonte: Genta, <i>Dynamics of Rotating Systems</i>, 2005 · <a href="https://…">doi.org/…</a>`.
- **Sem painel atrás de imagens** (exceção única: o retângulo tracejado de "Figura a inserir", ver `roteiro.md`): capturas e figuras ficam diretas no slide, sem quadrado, painel, faixa ou borda de fundo colorido ao redor. Para preencher a área, aumente a própria imagem (mantendo a proporção, `object-fit:contain`) e ajuste a coluna ao lado.
- **Imagem centralizada na área útil**: quando a imagem ocupa a altura entre o cabeçalho e o rodapé, os espaços acima e abaixo são iguais: `top = 151 + (849 − altura) / 2`. Com legenda, centralize o conjunto imagem + legenda.
- **Alinhamento de colunas**: blocos lado a lado com uma imagem têm o mesmo topo e a mesma base dela. O último bloco da coluna termina exatamente na base da imagem.
- **Respiro entre cartões: nunca colados.** Cartões, caixas e blocos vizinhos (empilhados ou lado a lado) têm de 22 a 40 px entre si. Para N cartões empilhados numa coluna de altura A, com espaço g = 22: altura de cada um = (A − (N − 1) × g) / N, e o topo do k-ésimo = topo da coluna + k × (altura + g). Uma caixa só encosta em outra se estiver inteira dentro dela (sub-bloco num painel). O `validar.py` dá ERRO em caixas coladas ou sobrepostas.
- **Não preencha o slide por preencher**: espaço vazio é aceitável. Só amplie elementos para ocupar a área se o usuário pedir.
- **Cartões** (aprovado no deck de *Skills*): fundo `#ffffff`, contorno **fino** de 1 px `#d6dee6`, `border-radius:14px` e a sombra suave do Design System, `box-shadow:0 2px 10px rgba(0,0,0,0.07)` (`shadow-card`). Para um cartão que precisa se destacar levemente: `box-shadow:0 2px 8px rgba(27,43,58,0.10)` (`shadow-card-strong`). Destaque forte: cartão `navy` cheio, sem contorno. Blocos secundários: `#f3f5f8` ou `#f3f6fa`, sem sombra. Padding interno de 28 a 40 px.
- **Nunca contorno grosso nem colorido em cartões** (2 px ou mais, em azul, steel ou vermelho): o usuário rejeitou o resultado "chapado". Também não há filete lateral colorido. Setas entre cartões são cheias (seta de bloco de 80 × 32 px, `#9aa8b6`, `layouts.md` §5), nunca de traço fino nem o caractere →.
- **Um destaque por slide em vermelho** `#c41e2a`. Elementos normais em `#2f6690` (steel) ou `#1e88c7` (blue); eixos e grades em `#d6dee6`.
- **Fatos e números novos** (fora do material) só com a aprovação do usuário e com fonte verificada, citada no rodapé ou nas notas.
- **Nunca deixe dois números de página nem duas barras no mesmo slide**: depois de inserir, remover ou mover slides, rode `numerar.py`, que apaga os antigos e escreve os novos.
- Quantidade de texto: um slide carrega uma ideia. Frases curtas; o detalhe vai para as notas do apresentador.

## 5. Divisória de parte (SlideSection)

```html
<section id="sec-historico" data-transition="fade" style="background:#152536">
  <img src="lmest/fundos/fundo-institucional.jpg" alt="" style="position:absolute; top:0; left:0; width:1920px; height:1080px; object-fit:cover">
  <p style="position:absolute; top:400px; left:89px; width:1400px; font-family:Carlito, Calibri, sans-serif; font-size:26px; font-weight:700; line-height:1.2; letter-spacing:6px; text-transform:uppercase; color:#49a9e1">Parte 1 · Histórico</p>
  <h2 style="position:absolute; top:452px; left:89px; width:1500px; font-family:Carlito, Calibri, sans-serif; font-size:80px; font-weight:700; line-height:1.15; color:#ffffff">De Turing ao ChatGPT</h2>
  <p style="position:absolute; top:568px; left:89px; width:1400px; font-family:Carlito, Calibri, sans-serif; font-size:32px; line-height:1.4; color:#b4d0dc">Setenta anos de inteligência artificial em poucos minutos</p>
  <aside>Transição para a parte 1: o que ela mostra e por quê.</aside>
</section>
```

O rótulo diz o número da parte ("Parte 1 · Histórico"); o `<h2>` é o **nome da parte**, o mesmo usado no cartão do resumo e em `deck.json > sections`. Se o título tiver duas linhas, desça o subtítulo em 92 px. As divisórias não têm placa de logos, número nem barra.

## 6. Capa e agradecimento

São fixos e gerados por `montar_fixos.py` a partir de `projeto.json`. Não os edite à mão: mude `projeto.json` e rode o script de novo (as notas do apresentador são preservadas).

- **Capa**: fundo institucional; placa branca de 380×152 px em `top:72px`, margem direita de 89 px (`left:1451px`), `border-radius:17px`, com UFU 92×92, LMEst 113×88 e INCT 76×112; sobretítulo "LMEst-UFU · <evento>" em sky; título de 88 px; subtítulo em mist; palestrante; afiliação; data e local. **Sem barra na base**, nem vermelha nem azul.
- **Agradecimento**: fundo institucional; à esquerda, "AGRADECIMENTOS" em sky, "Obrigado" (96 px), nome (38 px, bold), cargo (28 px, mist), contatos com ícones (WhatsApp para telefone, envelope para e-mail; 29 px) e "@lmest.ufu" com Instagram e LinkedIn (24 px, ícones de 34 px); à direita, a placa branca de 1002×720 com as 19 logos fixas (empresas parceiras, fomento, UFU, FEMEC, pós-graduação e LMEst). Dados ausentes do palestrante ficam genéricos ("Nome do apresentador", "e-mail do apresentador").
