# Roteiro

O roteiro é o único ponto de aprovação antes de montar o deck. Salve-o em `roteiro.md` na pasta do projeto e mostre o mesmo conteúdo na conversa. Monte o deck inteiro de uma vez só depois da aprovação.

## Como planejar

- **Duração e tamanho**: cerca de 1 slide de conteúdo a cada 1 a 1,5 minuto **de fala sobre slides**. Desconte o tempo de demonstrações ao vivo, exercícios e perguntas previstos no material. A conta é um teto: se o material não tem conteúdo para tantos slides, faça menos, nunca invente para completar. Sem duração informada, estime pelo tamanho do material e diga qual duração supôs (por exemplo: "material para ~30 min, 18 slides de conteúdo").
- **Reescreva como aula**, sem inventar conteúdo: um slide, uma ideia; o título é uma frase que afirma a mensagem; o que não couber no slide vai para as notas do apresentador.
- **Partes e divisórias**: proponha divisórias (`sec-…`) quando o material tiver partes claras ou o deck passar de ~15 slides. O usuário aprova ou retira.
- **Layout**: escolha um do catálogo (`layouts.md`) para cada slide e varie ao longo do deck. Não repita o mesmo layout em mais de três slides seguidos.
- **Figura que falta** (o material cita uma captura ou foto que não veio): no slide, ponha um retângulo de borda tracejada `2px dashed #9aa8b6`, sem fundo, do tamanho previsto, com o texto "Figura a inserir: <descrição>" em 24 px `#5b6b7c`. É a única exceção à regra de "sem painel atrás de imagens", e sai quando a figura chegar. Liste essas figuras nas lacunas.
- **Figuras**: use as do material (`figuras/` da extração, ou um recorte da página com `recortar_pagina.py`). Gráficos de dados simples podem ser redesenhados (layout 7). Não gere imagens nem busque na web sem pedido.
- **Lacunas**: se faltar algo importante para a aula (um exemplo, um dado, uma definição), aponte no roteiro. Só pesquise com a aprovação do usuário, e cite a fonte.
- **Animações**: não proponha nenhuma se o usuário não tiver pedido. Se pediu, indique na coluna "Animação" o padrão de `animacoes.md` de cada slide.

## Modelo

```markdown
# Roteiro: <título>

**Material:** <arquivo(s)> · **Duração:** <informada ou "suposta: ~N min"> · **Slides:** <total> (<N> de conteúdo)

| Nº | Id | Título (frase) | Mensagem central | Layout | Figura | Animação |
|---|---|---|---|---|---|---|
| 1 | capa | <título da apresentação> | — | Capa | — | — |
| 2 | sec-<parte> | <nome da parte 1> | <subtítulo> | Divisória | — | — |
| 3 | <id> | <título que afirma a mensagem> | <a ideia do slide em uma frase> | 2. Grade de cartões | figuras/<arquivo> | — |
| … | | | | | | |
| N | agradecimento | Obrigado | — | Agradecimento | — | — |

## Lacunas do material
- <o que falta e por que importa; proposta de como resolver>

## Para confirmar
1. **Saída**: HTML offline, PPTX editável e/ou artefato Slides do claude.ai? (Animações só no HTML e no artefato.)
2. **Palestrante**: nome, cargo, telefone (opcional) e e-mail(s) para o agradecimento. Sem resposta, ficam genéricos.
3. **Capa**: sobretítulo ("LMEst-UFU · <evento>"), subtítulo, data e local.
4. **Duração**: confirma <N> min?
5. **Barra de progresso**: incluir? (Padrão: não.)
6. **Animações**: quer alguma? (Padrão: não.)
7. **Resumo "O que vimos hoje"** antes do agradecimento? (Padrão: não.)
8. **Divisórias** propostas: mantém?
9. **Lacunas**: posso pesquisar <item>, com a fonte citada?
```

Pergunte só o que estiver em aberto. Se o usuário já informou algo (a saída, a duração, o palestrante), registre no roteiro e não pergunte de novo.
