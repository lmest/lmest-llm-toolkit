# Design system LMEst-UFU aplicado ao relatório HTML

Cópia condensada do design system cadastrado em https://claude.ai/artifact/QyGsUH1VCCj4CqknL22zyY, atualizada em 5 de novembro de 2026, depois da inclusão do componente Equation e da troca dos assets por versões em alta resolução. Mudanças no design system não chegam aqui sozinhas.

`assets/report.css` já aplica tudo o que está abaixo. Consulte este arquivo para escolher componentes e escrever o texto, não para redefinir estilos.

O design system foi feito para slides de 960 × 540. No relatório, os tamanhos de texto foram ampliados para leitura em tela (corpo de 17 px, frase de contexto de 19 px, títulos de seção de 30 px). Cores, raios, cartões e gestos de marca são os mesmos.

## Identidade

Laboratório de engenharia que presta contas a empresas: sóbrio, denso em dados e organizado em cartões, com um único gesto de marca, a faixa azul-marinho cortada por um filete vermelho.

Nome completo: Laboratório de Mecânica de Estruturas “Prof. José Eduardo Tannús Reis”, Faculdade de Engenharia Mecânica, Universidade Federal de Uberlândia. Escreva sempre “LMEst-UFU” e “LMEst”.

## Voz

- Português do Brasil, na primeira pessoa do plural.
- O título afirma a mensagem, em caixa de frase e sem ponto final: “O limiar de detecção define quantos impactos recortamos”.
- Cada seção começa com uma frase de contexto (`lead`), seguida dos blocos.
- Prove com números concretos. Vírgula decimal e ponto de milhar.
- Explique a sigla na primeira menção, sem subestimar o leitor.
- Use ponto médio ` · ` entre itens de uma linha, meia-risca em intervalos (`2.000–4.000 Hz`) e aspas curvas “ ”.
- CAIXA ALTA só em rótulos curtos (já aplicada pelo CSS, então escreva em caixa normal).
- Itálico em termos estrangeiros não incorporados: *autoencoder*, *edge*.
- Sem emoji e sem pontos de exclamação.

## Cores

| Token | Valor | Uso |
| --- | --- | --- |
| `navy` | `#152536` | Superfícies escuras, cabeçalho de tabela, aba ativa |
| `ink` | `#1B2B3A` | Texto principal |
| `muted` | `#5B6B7C` | Texto secundário e legendas |
| `subtle` | `#9AA8B6` | Conectores; não use em texto informativo |
| `red` | `#C41E2A` | Filete, número principal, meta, alerta |
| `blue` | `#1E88C7` | Barras e discos; em texto só de 19 px para cima |
| `blue-deep` | `#17689B` | Texto azul pequeno e links |
| `steel` | `#2F6690` | Segundo azul, texto de pill |
| `sky` | `#49A9E1` | Rótulos sobre escuro; nunca sobre claro |
| `mist` | `#B4D0DC` | Texto secundário sobre escuro |
| `surface` | `#F3F5F8` | Blocos sem borda, trilho de barras, linha alternada |
| `tint-blue` | `#EAF4FB` | Destaques e pills |
| `tint-red` | `#FBECEE` | Alerta |
| `line` | `#D6DEE6` | Contorno de cartões |

**O vermelho aponta para uma coisa só.** Em cada seção, use-o em no máximo um número ou barra, sempre o mais importante. Ele não é decoração. Por isso as notas de leitura são azuis, a menos que haja um alerta real para o leitor.

## Tipografia

Uma família só para texto: Carlito, equivalente livre da Calibri, embutida no HTML. A hierarquia vem do tamanho e do bold. Títulos e números sempre em bold. Alinhe à esquerda.

Equações são a exceção: saem em LaTeX, na fonte Computer Modern do KaTeX (componente Equation). A equação principal de uma seção fica centralizada num painel `surface` com `radius-md`. As grandezas em discussão podem ganhar `blue` (sensor, medição) ou `red` (o termo que é o ponto), no máximo duas cores por equação; o resto fica em `ink`.

## Formas

- Cartões com contorno fino e sombra quase imperceptível.
- Sem filetes laterais coloridos e sem gradientes além do fundo institucional da capa.
- Pills com cantos totalmente arredondados. Barras com cantos de 4 px.

## Imagens e logos

- Use imagens reais do material, com legenda curta. Sem banco de imagens.
- O fundo institucional da capa é o mesmo dos slides: degradê azul-marinho com linhas diagonais finas, sem outros grafismos.
- Logos sempre sobre placa branca, na ordem UFU, LMEst e, quando couber, INCT. A capa do relatório padrão usa UFU e LMEst. Use `logos="ufu,lmest,inct"` só quando o material se apresentar como projeto ou produto do INCT, para não sugerir vínculo que não existe. Se a dúvida persistir, use `ufu,lmest` e cite a escolha na entrega.
