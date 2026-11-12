# Catálogo de layouts

Cada layout traz o HTML do conteúdo (a moldura do cabeçalho está em `regras-de-slide.md` §3 e vem antes destes elementos) e as regras para o PPTX. As coordenadas estão no palco de 1920×1080 e são um ponto de partida: recalcule alturas e posições pelo texto real (≈0,49 × `font-size` por caractere) para que nada estoure nem se sobreponha, e respeite o alinhamento de colunas (`regras-de-slide.md` §4).

**Regras gerais para o PPTX.** O gerador converte cada filho fixado: `div` pintada → retângulo (arredondado se tiver `border-radius`); texto → caixa de texto com quebra automática e sem autoajuste; `img` → imagem; `table` → tabela nativa; `svg` → imagem (precisa de `rsvg-convert` ou `inkscape`, ou de um `.png` de mesmo nome); `hr` → linha. A sombra dos cartões (`box-shadow`) vira sombra externa no PPTX; cantos arredondados de imagens não passam.

---

## 1. Texto e imagem (figura com explicação)

Use quando houver uma figura do material e de 2 a 4 pontos a destacar. A imagem fica à direita (ou à esquerda), sem painel atrás, centralizada na área útil. A coluna de texto tem o mesmo topo e a mesma base da imagem, e os cartões empilhados nela ficam a 22 px uns dos outros (nunca colados).

```html
  <!-- imagem: 820 × 560, centralizada entre y 151 e 1000 → top = 151 + (849 − 560 − 40) / 2 (40 = legenda) -->
  <img src="imagens/ensaio-bancada.jpg" alt="Bancada de ensaio com o rotor" style="position:absolute; top:276px; left:1011px; width:820px; height:560px; object-fit:contain">
  <p style="position:absolute; top:846px; left:1011px; width:820px; font-family:Carlito, Calibri, sans-serif; font-size:24px; line-height:1.3; color:#5b6b7c">Bancada de rotor do LMEst-UFU, com mancais de rolamento</p>
  <!-- coluna de texto: de 276 a 836 -->
  <p style="position:absolute; top:276px; left:89px; width:860px; font-family:Carlito, Calibri, sans-serif; font-size:24px; font-weight:700; line-height:1.2; letter-spacing:4px; text-transform:uppercase; color:#5b6b7c">O que observamos</p>
  <div style="position:absolute; top:330px; left:89px; width:860px; height:150px; background:#ffffff; border:1px solid #d6dee6; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.07)"></div>
  <p style="position:absolute; top:356px; left:121px; width:796px; font-family:Carlito, Calibri, sans-serif; font-size:32px; font-weight:700; line-height:1.2; color:#152536">Pico na rotação crítica</p>
  <p style="position:absolute; top:402px; left:121px; width:796px; font-family:Carlito, Calibri, sans-serif; font-size:26px; line-height:1.4; color:#5b6b7c">A amplitude cresce 8 vezes perto de 3.200 rpm</p>
  <!-- … mais cartões a cada 172 px (150 de altura + 22 de espaço); recalcule a altura para que o último termine em y 836 … -->
```

PPTX: fiel. Para a imagem, só `object-fit:contain` ou `cover`.

## 2. Grade de cartões (3 ou 4 colunas)

Para listas de 3 a 6 itens paralelos (conceitos, etapas independentes, resultados). Três colunas: largura 554, `left` 89, 683 e 1277 (espaço de 40). Quatro colunas: largura 405, `left` 89, 534, 979 e 1424 (espaço de 40).

```html
  <div style="position:absolute; top:300px; left:89px; width:554px; height:420px; background:#ffffff; border:1px solid #d6dee6; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.07)"></div>
  <p style="position:absolute; top:340px; left:129px; width:474px; font-family:Carlito, Calibri, sans-serif; font-size:44px; font-weight:700; line-height:1.1; color:#1e88c7">01</p>
  <h3 style="position:absolute; top:410px; left:129px; width:474px; font-family:Carlito, Calibri, sans-serif; font-size:34px; font-weight:700; line-height:1.2; color:#152536">Modelo</h3>
  <p style="position:absolute; top:462px; left:129px; width:474px; font-family:Carlito, Calibri, sans-serif; font-size:26px; line-height:1.4; color:#5b6b7c">Equações de movimento do rotor com disco central</p>
  <!-- repita em left 683 (número em #2f6690) e 1277 (#1e88c7); destaque, se houver, em #c41e2a -->
```

Variante com ícone: disco de 88 px (`border-radius:50%`, fundo blue ou steel) em `top` do cartão + 40, com o ícone PNG branco de 50 px centrado (`lmest/icones/<nome>.png`), no lugar do número.

PPTX: o disco vira elipse; o ícone, imagem.

## 3. Comparação em duas colunas

Para antes/depois, abordagem A × B, vantagens × limitações. Painéis de 851 px, em `left` 89 e 980.

```html
  <div style="position:absolute; top:290px; left:89px; width:851px; height:560px; background:#f3f6fa; border:1px solid #d6dee6; border-radius:14px"></div>
  <p style="position:absolute; top:330px; left:129px; width:771px; font-family:Carlito, Calibri, sans-serif; font-size:24px; font-weight:700; line-height:1.2; letter-spacing:4px; text-transform:uppercase; color:#2f6690">Modelo analítico</p>
  <ul style="position:absolute; top:385px; left:129px; width:771px; font-family:Carlito, Calibri, sans-serif; font-size:28px; line-height:1.45; color:#1b2b3a">
    <li>Rápido e explica o fenômeno</li>
    <li>Supõe eixo sem massa</li>
  </ul>
  <div style="position:absolute; top:290px; left:980px; width:851px; height:560px; background:#ffffff; border:1px solid #d6dee6; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.07)"></div>
  <p style="position:absolute; top:330px; left:1020px; width:771px; font-family:Carlito, Calibri, sans-serif; font-size:24px; font-weight:700; line-height:1.2; letter-spacing:4px; text-transform:uppercase; color:#c41e2a">Elementos finitos</p>
  <ul style="position:absolute; top:385px; left:1020px; width:771px; font-family:Carlito, Calibri, sans-serif; font-size:28px; line-height:1.45; color:#1b2b3a">
    <li>Representa a geometria real</li>
    <li>Exige mais dados e validação</li>
  </ul>
```

## 4. Linha do tempo

Para histórico e cronogramas. Eixo horizontal; marcos com círculo, ano acima e texto abaixo. Com N marcos, o espaço entre centros é `1742 / N`.

```html
  <div style="position:absolute; top:560px; left:89px; width:1742px; height:5px; background:#d6dee6"></div>
  <!-- marco: centro x = 89 + (k + 0,5) × 1742 / N -->
  <div style="position:absolute; top:548px; left:249px; width:28px; height:28px; background:#2f6690; border-radius:50%"></div>
  <p style="position:absolute; top:470px; left:113px; width:300px; font-family:Carlito, Calibri, sans-serif; font-size:40px; font-weight:700; line-height:1.1; text-align:center; color:#2f6690">1950</p>
  <p style="position:absolute; top:600px; left:113px; width:300px; font-family:Carlito, Calibri, sans-serif; font-size:26px; line-height:1.35; text-align:center; color:#1b2b3a">Teste de Turing</p>
  <!-- o marco atual ou de destaque em #c41e2a -->
```

## 5. Fluxo de processo

Para etapas encadeadas (método, *pipeline*). Até 4 cartões por linha, de 350 px, em `left` 89, 553, 1017 e 1481 (114 px entre eles); com 3 cartões, de 480 px, em `left` 89, 720 e 1351 (151 px entre eles). No meio de cada intervalo vai a **seta cheia padrão**: 80 × 32 px, cor `#9aa8b6`, centrada na altura dos cartões (`left` = fim do cartão + (intervalo − 80) / 2). Nunca use seta de traço fino nem o caractere →. Os cartões são os cartões padrão (branco, contorno fino, sombra suave): **nunca contorno grosso ou colorido**. A etapa final ou de destaque pode ser um cartão `navy` cheio, com número em sky e texto branco/mist.

```html
  <div style="position:absolute; top:400px; left:89px; width:350px; height:240px; background:#ffffff; border:1px solid #d6dee6; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.07)"></div>
  <p style="position:absolute; top:440px; left:125px; width:278px; font-family:Carlito, Calibri, sans-serif; font-size:44px; font-weight:700; line-height:1.1; color:#1e88c7">01</p>
  <h3 style="position:absolute; top:506px; left:125px; width:278px; font-family:Carlito, Calibri, sans-serif; font-size:32px; font-weight:700; line-height:1.2; color:#152536">Aquisição dos sinais</h3>
  <p style="position:absolute; top:556px; left:125px; width:278px; font-family:Carlito, Calibri, sans-serif; font-size:26px; line-height:1.35; color:#5b6b7c">Acelerômetros nos mancais</p>
  <svg width="80" height="32" viewBox="0 0 80 32" style="position:absolute; top:504px; left:456px; width:80px; height:32px"><path d="M0 10 H52 V0 L80 16 L52 32 V22 H0 Z" fill="#9aa8b6"/></svg>
  <!-- etapa de destaque: -->
  <div style="position:absolute; top:400px; left:1481px; width:350px; height:240px; background:#152536; border-radius:14px; box-shadow:0 2px 8px rgba(27,43,58,0.10)"></div>
  <p style="position:absolute; top:440px; left:1517px; width:278px; font-family:Carlito, Calibri, sans-serif; font-size:44px; font-weight:700; line-height:1.1; color:#49a9e1">04</p>
  <h3 style="position:absolute; top:506px; left:1517px; width:278px; font-family:Carlito, Calibri, sans-serif; font-size:32px; font-weight:700; line-height:1.2; color:#ffffff">Diagnóstico</h3>
  <p style="position:absolute; top:556px; left:1517px; width:278px; font-family:Carlito, Calibri, sans-serif; font-size:26px; line-height:1.35; color:#b4d0dc">Falha identificada e classificada</p>
```

Itens dentro de um cartão (pastas, opções, parâmetros) vão em *pills*: `background:#eaf4fb; border:1px solid #c6e0f2; border-radius:999px`, texto 26 a 28 px bold `#152536`, centralizado. Uma conclusão geral do fluxo pode ir numa faixa na base (Callout): `background:#f3f5f8; border-radius:14px`, sem contorno, texto 28 px com o rótulo em negrito.

PPTX: a seta SVG precisa de `rsvg-convert` ou `inkscape`. Sem eles, troque a seta por uma imagem PNG.

## 6. Tabela

Para dados comparáveis em linhas e colunas (até ~8 linhas a 26 px). Cabeçalho navy com texto branco; linhas alternadas em surface.

```html
  <table style="position:absolute; top:290px; left:89px; width:1742px; font-family:Carlito, Calibri, sans-serif; font-size:26px; color:#1b2b3a">
    <tr style="background:#152536"><th style="width:40%; color:#ffffff">Parâmetro</th><th style="width:30%; color:#ffffff; text-align:right">Ensaio</th><th style="width:30%; color:#ffffff; text-align:right">Modelo</th></tr>
    <tr><td>1ª velocidade crítica</td><td style="text-align:right">3.180 rpm</td><td style="text-align:right">3.240 rpm</td></tr>
    <tr style="background:#f3f5f8"><td>Amortecimento</td><td style="text-align:right">2,1%</td><td style="text-align:right">2,0%</td></tr>
  </table>
```

Uma linha ocupa ≈ 2,1 × `font-size`. Sem `colspan`/`rowspan`. PPTX: tabela nativa editável.

## 7. Gráfico

- **Barras**: desenhe com `div` (vira forma nativa no PPTX). Barra horizontal: rótulo de 170 px à esquerda, barra a partir de `left` do rótulo + 190, altura 40, `border-radius:4px`, valor 20 px depois do fim da barra; passo de 62 px entre linhas. Comprimento proporcional ao valor. Destaque em `#c41e2a`, demais em `#1e88c7` e `#2f6690`. Colunas verticais crescem da base comum.
- **Curvas e dispersões**: um `<svg>` com eixos em `#d6dee6`, curva em `#2f6690` (destaque em `#c41e2a`), **sem `<text>`**: rótulos e valores dos eixos são `<p>` de 24 px fixados por cima. Para dados reais com muitos pontos, gere o SVG por script (matplotlib com `svg.fonttype='path'`, sem textos) e salve também o `.png`.
- Um gráfico do material que já seja imagem: use a imagem (layout 1), sem redesenhar.

## 8. Equação

Gere a imagem com `equacao.py` (SVG para HTML e artefato, PNG para PPTX) e posicione com a largura e a altura que o script imprime.

```html
  <div style="position:absolute; top:300px; left:89px; width:1742px; height:200px; background:#f3f6fa; border:1px solid #d6dee6; border-radius:14px"></div>
  <img src="imagens/eq-movimento.svg" alt="m x'' + c x' + k x = F(t)" style="position:absolute; top:352px; left:665px; width:590px; height:96px; object-fit:contain">
  <ul style="position:absolute; top:550px; left:89px; width:1742px; font-family:Carlito, Calibri, sans-serif; font-size:28px; line-height:1.45; color:#1b2b3a">
    <li><b>m</b>: massa do disco</li>
    <li><b>c</b>: amortecimento viscoso</li>
  </ul>
```

## 9. Destaque numérico (StatBand)

Para 2 a 4 números que sustentam a mensagem. Número grande (72 px, bold), legenda abaixo (26 px).

```html
  <div style="position:absolute; top:330px; left:89px; width:554px; height:300px; background:#ffffff; border:1px solid #d6dee6; border-radius:14px; box-shadow:0 2px 10px rgba(0,0,0,0.07)"></div>
  <p style="position:absolute; top:380px; left:129px; width:474px; font-family:Carlito, Calibri, sans-serif; font-size:72px; font-weight:700; line-height:1.1; color:#c41e2a">≈80</p>
  <p style="position:absolute; top:480px; left:129px; width:474px; font-family:Carlito, Calibri, sans-serif; font-size:26px; line-height:1.4; color:#5b6b7c">projetos de PD&amp;I concluídos desde 2006</p>
  <!-- só um número em vermelho; os demais em #2f6690 ou #1e88c7 -->
```

## 10. Citação

Para uma frase-chave de um autor. Texto grande, aspas vermelhas, autor em muted.

```html
  <p style="position:absolute; top:300px; left:89px; width:120px; font-family:Carlito, Calibri, sans-serif; font-size:160px; font-weight:700; line-height:1; color:#c41e2a">“</p>
  <p style="position:absolute; top:340px; left:220px; width:1500px; font-family:Carlito, Calibri, sans-serif; font-size:48px; font-weight:700; line-height:1.3; color:#152536">A frase-chave, curta, com no máximo três linhas</p>
  <p style="position:absolute; top:560px; left:220px; width:1500px; font-family:Carlito, Calibri, sans-serif; font-size:28px; line-height:1.3; color:#5b6b7c">Autor · obra, ano</p>
```

## 11. Imagem em destaque

Uma figura grande que fala sozinha (captura de tela, foto do ensaio). Centralizada na área útil, com legenda logo abaixo e alinhada à esquerda da imagem, sem painel atrás.

```html
  <!-- imagem 1400 × 740; conjunto de 740 + 10 + 32 = 782 → top = 151 + (849 − 782) / 2 = 184 -->
  <img src="imagens/captura.png" alt="…" style="position:absolute; top:184px; left:260px; width:1400px; height:740px; object-fit:contain">
  <p style="position:absolute; top:934px; left:260px; width:1400px; font-family:Carlito, Calibri, sans-serif; font-size:24px; line-height:1.3; color:#5b6b7c">Legenda curta da figura</p>
```

Com `object-fit:contain`, a largura desenhada pode ser menor que a caixa. Para a legenda ficar alinhada à borda real da imagem, ajuste a caixa à proporção da imagem (largura = altura × proporção).

## 12. Resumo "O que vimos hoje" (só se o usuário pedir)

Slide `resumo`, antes do agradecimento, sem número e sem barra. Um cartão por parte do deck, com o nome igual ao da divisória e na ordem das divisórias em `order`.

```html
<section id="resumo" data-transition="fade" style="background:#152536">
  <img src="lmest/fundos/fundo-institucional.jpg" alt="" style="position:absolute; top:0; left:0; width:1920px; height:1080px; object-fit:cover">
  <div style="position:absolute; top:0; left:0; width:1920px; height:1080px; background:#152536; opacity:0.6"></div>
  <p style="position:absolute; top:230px; left:200px; width:1520px; font-family:Carlito, Calibri, sans-serif; font-size:24px; font-weight:700; line-height:1.2; letter-spacing:6px; text-transform:uppercase; text-align:center; color:#49a9e1">O que vimos hoje</p>
  <!-- 6 cartões em 3 × 2: left 200, 716, 1232 (width 488); top 300 e 554 (height 230) -->
  <div style="position:absolute; top:300px; left:200px; width:488px; height:230px; background:#1c2b3e; border:1px solid #34495e; border-radius:14px"></div>
  <p style="position:absolute; top:328px; left:232px; width:424px; font-family:Carlito, Calibri, sans-serif; font-size:40px; font-weight:700; line-height:1.1; color:#49a9e1">01</p>
  <p style="position:absolute; top:380px; left:232px; width:424px; font-family:Carlito, Calibri, sans-serif; font-size:34px; font-weight:700; line-height:1.2; color:#ffffff">Nome da parte 1</p>
  <p style="position:absolute; top:426px; left:232px; width:424px; font-family:Carlito, Calibri, sans-serif; font-size:24px; line-height:1.35; color:#b4d0dc">Descrição em até duas linhas, cerca de 70 caracteres</p>
  <!-- … -->
  <aside>Uma frase de recapitulação.</aside>
</section>
```

O título do cartão é o `<h2>` da divisória correspondente; o número é a ordem da parte (01, 02…). Com 4 partes, use 2 × 2 (`left` 444 e 976). Com 3 partes, uma linha só: rótulo em `top:380px` e cartões em `top:450px`. Com 5, uma linha de 3 e outra de 2 centralizada (`left` 458 e 974). Sem divisórias, use de 3 a 6 cartões com as ideias principais. Se mudar as partes do deck, atualize os cartões.
