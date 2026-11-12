# Design System LMEst-UFU no palco de 1920×1080

Fonte: artefato "Design System LMEst-UFU" (https://claude.ai/artifact/c21d9ee2-8534-40e3-875d-c958d06472ab). O Design System mede tudo no palco de 960×540. Os decks usam **1920×1080: multiplique por 2** as medidas do Design System. Quando uma regra dos decks aprovados (`regras-de-slide.md`) divergir do dobro do Design System, vale a regra dos decks.

Guias de cada componente (SlideFrame, Callout, StatCard, Timeline, ProcessFlow, LogoWall…): `componentes-ds.md`.

## Voz e conteúdo

- Português do Brasil, na primeira pessoa do plural ("O que já dominamos", "Como vamos aprender").
- **O título afirma a mensagem do slide**, em caixa de frase e sem ponto final ("Ensaio, eletrônica e computação numa única cadeia"). Evite títulos genéricos ("Infraestrutura", "Resultados").
- Comece o slide com uma frase de contexto (estilo `lead`), depois os blocos.
- Prove com números concretos, com vírgula decimal e ponto de milhar (`R$ 70 mi+`, `≈80`, `2,5 kg`).
- Explique a sigla na hora: "taxa de erro de bit (BER)". Use analogias simples para o que é difícil.
- Separe itens da mesma linha com ponto médio `·`. Use meia-risca em intervalos (`M13–48`) e aspas curvas “ ”.
- CAIXA ALTA só em rótulos e sobretítulos curtos (`eyebrow`, `section-label`, `pill-label`).
- **Termos estrangeiros em itálico**, inclusive nos títulos: *skill*, *token*, *Machine Learning*, *whirl*.
- Sem emoji e sem ponto de exclamação. Escreva "LMEst-UFU" e "LMEst", nunca "LMEST" em texto corrido.

## Cores (tokens)

| Token | Hex | Uso |
|---|---|---|
| navy | `#152536` | Toda superfície escura: cabeçalho, painéis, cabeçalho de tabela. Sobre ela: white, mist, sky |
| ink | `#1B2B3A` | Texto principal sobre white, surface e tint-blue |
| muted | `#5B6B7C` | Texto secundário, legendas (5,4:1 em white) |
| subtle | `#9AA8B6` | Só conectores e abas inativas; nunca texto informativo (2,4:1) |
| red | `#C41E2A` | Assinatura: filete do cabeçalho, número principal, meta, alerta, destaque. Um só destaque por slide |
| blue | `#1E88C7` | Discos de ícone, barras, número de página. Texto só em bold ≥ 38 px |
| blue-deep | `#17689B` | Texto azul pequeno; links |
| steel | `#2F6690` | Segundo azul: alterna com blue em discos e barras; elementos normais de gráficos |
| steel-soft | `#3F6F92` | Variação de steel |
| sky | `#49A9E1` | Rótulos e números sobre navy e o fundo institucional. Nunca sobre claro |
| blue-soft | `#8CC3E6` | Só contorno de sub-blocos |
| mist | `#B4D0DC` | Texto secundário sobre navy e o fundo institucional |
| gold | `#D6A300` | Só projeção futura em número grande. Raro |
| orange | `#E08A1E` | Evite |
| white | `#FFFFFF` | Fundo, cartões, placa de logos |
| surface | `#F3F5F8` | Blocos sem borda, trilho de barras, linha alternada de tabela |
| surface-blue | `#F3F6FA` | Painel de diagrama e coluna de contexto com borda line |
| tint-blue | `#EAF4FB` | Destaque azul (callout). Texto ink ou steel |
| tint-blue-2 | `#DDEDF8` | Sub-bloco dentro de tint-blue |
| tint-blue-line | `#C6E0F2` | Contorno de painéis tint-blue |
| tint-steel | `#E6EEF5` | Célula de matriz, com contorno e texto steel |
| tint-red | `#FBECEE` | Destaque vermelho: alerta. Texto ink ou red |
| tint-red-2 | `#FBEFF0` | Coluna de destaque vermelho claro |
| tint-red-line | `#F0CDD0` | Contorno de tint-red-2 |
| red-soft | `#F2A7AD` | Contorno de tint-red |
| line | `#D6DEE6` | Contorno de cartões (1 px), eixos e grade de gráficos |
| line-soft | `#DCE6EE` | Separador interno em tabelas e listas |
| table-rule | `#CBCBCB` | Filete entre linhas de tabela |
| table-rule-alt | `#C2C4C6` | Filete entre colunas |
| table-rule-strong | `#192631` | Filete do cabeçalho de tabela |
| trl-0 … trl-5 | `#C9DCE7` `#A9C8DB` `#86B0CC` `#5F93B8` `#3F77A2` `#2A5C86` | Rampa TRL (degrau 6 = red, 7 = navy) |

## Tipografia

Uma família só: **Carlito** (`font-family:Carlito, Calibri, sans-serif`) no HTML e no artefato; **Calibri** no PPTX (o gerador troca). A hierarquia vem do tamanho e do bold. Alinhe à esquerda; centralize só caixas de fluxo, pills e rótulos de barras.

Escala dos decks aprovados, em px do palco de 1920×1080 (**mínimo absoluto: 24 px**, inclusive rodapés, rótulos, células e minipáginas):

| Estilo | Tamanho | Peso | Altura de linha | Cor |
|---|---|---|---|---|
| Título da capa | 88 | 700 | 1,1 | white |
| Sobretítulo (eyebrow) | 26 | 700, caixa alta, `letter-spacing:6px` | 1,2 | sky |
| Título de divisória | 80 | 700 | 1,15 | white |
| "Obrigado" | 96 | 700 | 1,2 | white |
| Título do slide (cabeçalho) | 56 | 700 | 1,2 | white, uma linha |
| Frase de contexto (lead) | 30 | 400 | 1,4 | ink |
| Título de bloco | 32–34 | 700 | 1,2 | navy ou ink |
| Texto de cartão | 26–28 | 400 | 1,4 | muted ou ink |
| Número de destaque | 40–44 | 700 | 1,1 | blue, steel ou red |
| Rótulo de grupo (section-label) | 24 | 700, caixa alta, `letter-spacing:4px` | 1,2 | muted, red ou blue |
| Legenda de figura | 24 | 400 | 1,3 | muted `#5B6B7C` |
| Nota de rodapé e fonte | 24 | 700 | 1,2 | ink `#1B2B3A` |
| Número de página | 24 | 700 | 1,2 | blue `#1E88C7` |

## Espaços, raios, sombras e traços (×2)

- Margem lateral: **89 px** (conteúdo de 89 a 1831, largura útil 1742).
- Cabeçalho: faixa navy de 0 a 144 px e filete red de 7 px em `top:141px`. Área de conteúdo entre y 151 e 1000.
- Espaços: xs 14, sm 22, md 29, lg 43 px. Entre cartões de uma grade: 22 a 40 px; entre blocos: 40 a 48 px.
- Raios: barra 4 (8), cartão 12–14, placa de logos 17, pill 999 px.
- Sombras (tokens do Design System, ×2):
  - `shadow-card` = `0 1.2px 5px rgba(0,0,0,0.07)` → **`box-shadow:0 2px 10px rgba(0,0,0,0.07)`**: cartões brancos com contorno `line`. Quase imperceptível.
  - `shadow-card-strong` = `0 1px 4px rgba(27,43,58,0.10)` → **`box-shadow:0 2px 8px rgba(27,43,58,0.10)`**: cartões que precisam se destacar levemente.
  - O PPTX recebe a mesma sombra como sombra externa.
- Traços: contorno de cartão 1 px `line` (também nas caixas de fluxo); conector 4 px `subtle`; marco de linha do tempo 5 px.

## Assets (cópia local em `assets/`, e em `lmest/` dentro de cada projeto)

- **logos/**: `lmest.png` (principal), `lmest-grade.png` (agradecimento), `ufu.png` (roxo), `ufu-preto.png` (paredes de logos), `inct.png`, `femec.png`, `pos-graduacao.png`, `cnpq.png`, `fapemig.png`, `capes.png`.
- **parceiros/**: `petrobras`, `baesa`, `ceran`, `cpfl`, `foz-do-chapeco`, `enercan`, `bayer`, `aneel`, `csc`, `dynamic`, `embraer`; `academicos-brasil` (grupo de universidades brasileiras); exterior: `villanova`, `dtu`, `cleveland`, `aberdeen`, `insa`, `isae`, `tum`, `politecnico`, `technion`. Só para relações reais; não amplie além de ~240 px de largura (baixa resolução em `bayer`, `ceran`, `csc`).
- **icones/** (PNG, traço arredondado). A maioria é **branca**: ponha sempre num disco `blue`, `steel`, `navy` ou `red`, com o ícone a 56% do diâmetro. Coloridos para fundo claro: `chip-azul`, `binario-azul`, `hierarquia-navy`, `bandeira-navy`, `check-navy`. Contato sobre escuro: `email-nevoa`. Redes: `linkedin`, `instagram`, `whatsapp`.
  - Temas: `engrenagem`, `chip`, `placa-circuito`, `sinal`, `ondas`, `ia`, `funcao`, `binario-azul`, `cubo-3d`, `monitor-config`, `servidor`, `codigo`, `github`, `ramificacao`.
  - Gestão: `checklist`, `calendario`, `pasta`, `video`, `mensagens`, `equipe`, `usuario-check`, `usuario-estrela`, `bandeira`, `alvo`, `rota`, `atualizar`, `prancheta-custo`, `arquivo-check`.
  - Institucional: `instituicao`, `formatura`, `certificado`, `escudo-check`, `escudo-check-2`, `armazem`, `martelo`, `chave-inglesa`.
  - Não misture com outras famílias de ícones nem use emoji.
- **fundos/**: `fundo-institucional.jpg`, gradiente navy com diagonais sutis, em tela cheia na capa, nas divisórias, no resumo e no agradecimento.
- **fontes/** (na skill): Carlito Regular, Italic, Bold e BoldItalic, em `.woff2` (embutidas no HTML) e `.ttf`.

## Regras de logos

- **Sempre sobre placa branca**, inclusive em slide escuro. Ordem fixa: UFU e LMEst no cabeçalho; UFU, LMEst e INCT na capa.
- Marcas de terceiros só no agradecimento ou numa parede de logos (LogoWall).

## Imagens e diagramas

- Fotos reais e figuras do material, sem banco de imagens nem imagem gerada.
- Diagramas em vetores simples: `blue` e `steel` para elementos normais, `red` para o destaque ou a meta, `surface-blue` no painel, rótulos em pill.
- Decks seguem o sanduíche: capa escura, conteúdo claro, divisórias escuras, agradecimento escuro.

## No PowerPoint

Slide 16:9 (33,867 × 19,05 cm), Calibri, 1 px do palco = 0,5 pt. O gerador `gerar_pptx.py` faz a conversão.
