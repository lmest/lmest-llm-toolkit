# Componentes do conteudo.html

O `conteudo.html` contém só o corpo do relatório. Capa, índice lateral, fontes e scripts são acrescentados por `montar_relatorio.py`. `exemplo-conteudo.html` mostra todos os componentes em uso, em um relatório aprovado. Ele é referência de estrutura e tom: os caminhos de figura dele usam os nomes originais, então em um relatório novo use sempre os caminhos de `manifesto.json`.

## Marcações processadas pelo script

### Capa (obrigatória, no início)
```html
<relatorio titulo="Processamento dos dados coletados pelo robô"
  sobretitulo="Relatório · 29 de outubro de 2026"
  subtitulo="Frase curta que descreve o escopo"
  logos="ufu,lmest"></relatorio>
```
O atributo opcional `rodape` substitui o rodapé padrão. Use a data do material, nunca a de hoje, e omita-a se o material não trouxer nenhuma.

### Seção
```html
<section id="deteccao" data-nav="Detecção e recorte">
<div class="section-label">Detecção dos picos e recorte dos eventos</div>
<h2>O limiar de detecção define quantos impactos recortamos</h2>
<p class="lead">Frase de contexto.</p>
...
</section>
```
`data-nav` é o nome curto no índice lateral. A primeira seção é a síntese, com `class="section-label red"` no rótulo.

### Figura
```html
<fig src="figuras/nome.png" cap="Legenda curta que diz o que a figura mostra." id="sinal" classe="narrow" largura="3000"></fig>
```
- `cap` é obrigatório; a numeração é automática. `id` permite citar com `[[fig:sinal]]`, que vira o número.
- Classes de tamanho, para figura sozinha:
  - `classe="compacta"` limita a 620 px, para diagramas de blocos, esquemas simples e gráficos de baixa resolução, que ficariam grandes demais;
  - `classe="narrow"` limita a 900 px, para um gráfico simples;
  - `classe="retrato"` limita a 440 px, só para foto ou imagem vertical sem texto pequeno;
  - sem classe, a figura ocupa a largura total: use para painéis com vários subplots, mesmo quadrados ou verticais, para o texto continuar legível.
- `largura` é a resolução embutida: 2400 por padrão, 3000 para painéis com muitos gráficos.
- Em `cap`, escreva aspas como `&quot;` ou use aspas curvas.

### Duas figuras lado a lado
```html
<div class="g2">
<fig src="..." cap="..."></fig>
<fig src="..." cap="..."></fig>
</div>
```
Use para figuras que se comparam e que tenham proporções parecidas, para ficarem com a mesma altura (diferença de proporção altura/largura de no máximo cerca de 25%). Uma figura quadrada ao lado de uma larga fica desigual: nesse caso, coloque uma abaixo da outra, cada uma com sua classe de tamanho. Painéis grandes vão sozinhos, na largura total.

### Cartões lado a lado
Dois `.lm-card` em `.g2` ficam sempre com a mesma altura, porque o CSS os estica até a altura do vizinho. Não misture cartão e figura, ou cartão e texto solto, na mesma grade.

### Grade de fotos
```html
<div class="fotos">
<fig src="figuras/lab-1.jpg" cap="Bancada de ensaios acústicos."></fig>
<fig src="figuras/lab-2.jpg" cap="Câmara de testes."></fig>
</div>
```
Use para três ou mais fotos, inclusive verticais. As miniaturas são recortadas em 4:3 e a imagem inteira aparece ao ampliar, então não use para gráficos e diagramas, que perderiam parte do conteúdo.

### Abas de figura
```html
<abas-fig rotulo="Valor de τ" cap="O que comparar entre as variantes.">
<aba rotulo="τ = 0,02" src="figuras/a.png" alt="Descrição"></aba>
<aba rotulo="τ = 0,5" src="figuras/b.png" alt="Descrição"></aba>
</abas-fig>
```
Use quando o mesmo gráfico varia com um parâmetro e o valor está em alternar no mesmo enquadramento. As variantes aparecem todas na impressão.

### Barras de comparação
```html
<div class="g2 metrics">
<div class="lm-card"><h3>Média dos picos</h3>
<barras unidade="Pa" casas="4" destaque="Parado · bem solta">
<barra rotulo="Parado · bem presa" valor="0.3138"></barra>
<barra rotulo="Parado · bem solta" valor="0.8359"></barra>
</barras></div>
</div>
```
Use para uma métrica comparada entre até cerca de 8 categorias, com valores numéricos reais do material. `valor` usa ponto; a exibição sai com vírgula. Para mostrar o número como no material (“1,1 mil”), use `texto="1,1 mil"` na barra; o comprimento continua vindo de `valor`. Grandezas diferentes ficam em cartões separados, nunca no mesmo eixo. `destaque` deixa a barra em vermelho.

### Equações
`<eq>LaTeX</eq>` em bloco e `<eqi>LaTeX</eqi>` na linha. Saem em LaTeX renderizado pelo KaTeX, na fonte Computer Modern, como no componente Equation do design system. O script embute o KaTeX só quando há equações. Escreva a vírgula decimal como `0{,}8913`.

**Cor das grandezas.** `\azul{…}` pinta em `blue` o que vem do sensor ou da medição. `\vermelho{…}` pinta em `red` o termo que muda ou que é o ponto da seção. O resto fica na cor do texto. Use no máximo as duas cores numa equação, e só quando o texto ao redor fala dessas grandezas; a mesma cor deve marcar a grandeza também nas `<eqi>` do texto. Lembre que o vermelho aponta para uma coisa só em cada seção.

Equação em destaque, centralizada num painel `surface`, logo depois do `lead` (uma por seção, no máximo):
```html
<div class="lm-eq"><eq>F = k_i\,\azul{i(x_s)} + k_s\,\vermelho{x_a}</eq></div>
<p><eqi>k_s</eqi> multiplica <eqi>\vermelho{x_a}</eqi>, o deslocamento no atuador.</p>
```

Conjunto de equações em cartão, com uma célula para cada equação, o que as mantém centralizadas:
```html
<div class="lm-card math"><h3>Título</h3>
<div class="eqs">
<div><eq>f_c = \sqrt{f_1 f_2}</eq></div>
<div><eq>E \approx \sum |P[k]|^2 \Delta f</eq></div>
</div></div>
```
Cartões de características, com a equação centralizada no espaço abaixo do título:
```html
<div class="g2 feats">
<div class="lm-card"><h4>Fator de forma</h4><div class="fm"><eq>...</eq><eq>...</eq></div></div>
<div class="lm-card"><h4>Centroide espectral</h4><div class="fm"><eq>...</eq></div></div>
</div>
```

## HTML direto

### Números de destaque
```html
<div class="stats">
<div class="lm-card stat"><div class="num red">0,8359 Pa</div><p>O que o número significa, com a comparação.</p></div>
<div class="lm-card stat"><div class="num">30 → 35</div><p>...</p></div>
</div>
```
Use quatro na síntese (grade `.stats`) e dois dentro de seções (`.stats.two`). Só um `num red` por seção. Mantenha o número curto, porque ele não quebra linha.

### Tabela
```html
<div class="tw"><table class="lm-table"><thead><tr><th>Estudo</th><th class="num">Resultado</th></tr></thead>
<tbody><tr><td>Xie et al. (2022)</td><td class="num">98,33%</td></tr></tbody></table></div>
```
O `.tw` dá rolagem horizontal às tabelas largas. `.num` alinha à direita, em bold. Marque nomes de arquivo com `<span class="fn">`.

### Avisos
```html
<div class="lm-callout note"><span><b>Nota de leitura.</b> Discrepância ou ressalva que o leitor precisa conhecer.</span></div>
<div class="lm-callout lm-callout--line"><span><b>Alcance destes resultados:</b> limite das conclusões.</span></div>
```

### Campos ou etapas em sequência
```html
<div class="parts"><div class="part"><div class="section-label">Status do robô</div><div>em-movimento, parado</div></div>...</div>
```
Grade de até seis células, que se ajusta à quantidade de itens, para decompor um padrão ou listar etapas curtas.

### Pills
`<span class="lm-pill">30 impactos</span>`, ou agrupadas em `<div class="pills">`. Para rotular uma figura com uma equação, use `<div class="eq-head"><eqi>L = 3\,\sigma</eqi><span class="lm-pill">35 impactos</span></div>` antes dela.

### Outros
- `<h3>` para subtítulos dentro da seção e `<p>` para texto corrido.
- `<p class="after">` para um parágrafo entre um bloco e figuras.
- `<ol class="refs">` para referências, com `<i>` no título e `<b>` no veículo.

## Se faltar um componente

Reaproveite cartões (`.lm-card`), a grade `.g2` e os estilos existentes. Só acrescente CSS em um `<style>` no conteúdo se nada servir, usando as cores de `design-system.md`.
