# Capa, transição e agradecimentos

O deck-base é `assets/references/referencia_base.pptx`. A capa e os
agradecimentos são obrigatórios, ocupam sempre a primeira e a última posição e
mantêm a estrutura original. Estas regras de conteúdo e composição se aplicam
tanto ao PPTX quanto ao HTML. Para PPTX, preencha somente os campos indicados
com as funções de `scripts/lmest_pptx.py`; para HTML, reproduza sua composição
com a mesma hierarquia e posições relativas usando os recursos locais. Os
nomes de objetos nas tabelas abaixo identificam apenas objetos do PowerPoint.
Não mova, redimensione nem substitua logos, fundos ou formas fixas.

Se o conteúdo não couber, levante `LayoutError`, explique o que precisa ser
encurtado e preserve o layout.

## Capa — slide de referência 1 (`fill_cover`)

| Campo | Objeto no PPTX-base | Regra |
|---|---|---|
| Título | `Text 1` | 44 pt, negrito branco, até duas linhas |
| Autoria | `Text 3` | um autor pode incluir cargo; múltiplos autores ficam na mesma linha |
| Contatos | `Text 4` | contatos do apresentador em uma linha |

Preserve o kicker (`Text 0`), a identificação institucional (`Text 2`), o
cartão de logos (`Shape 5`) e as imagens de logo (`Image 0` a `Image 2`). Use
somente dados do front matter. Não invente evento, data, orientador ou afiliação.

## Transição — slide de referência 5 (`fill_divider`)

| Campo | Objeto no PPTX-base | Regra |
|---|---|---|
| Rótulo | `Text 8` | “PARTE I”, “PARTE II” etc.; use algarismos romanos |
| Título | `Text 9` | 40 pt, uma linha |
| Subtítulo | `Text 10` | 16 pt, uma linha; vazio se não houver |

A transição é opcional e sua posição segue as seções do conteúdo. Preserve o
fundo e os logos. Encurte títulos que não caibam.

## Agradecimentos — slide de referência 19 (`fill_thanks`)

| Campo | Objeto no PPTX-base | Regra |
|---|---|---|
| Nome | `Text 7` | 19 pt, negrito, uma linha |
| Cargo | `Text 187` | 14 pt, uma linha; mantenha o objeto vazio quando ausente |
| Contatos | `Text 208`, `Text 227`, `Text 243` | até três linhas; telefone antes de e-mail |

Preserve “AGRADECIMENTOS”, “Obrigado”, os ícones sociais, `@lmest.ufu`, o
painel de logos e as imagens institucionais. Os ícones dos contatos acompanham
o tipo de cada contato. Contatos vêm do bloco `agradecimentos` do front matter
ou, na ausência dele, do apresentador. Remova os pares ícone/texto de linhas
sem contato sem deslocar os demais elementos.

## Elementos fixos dos slides de conteúdo

Ao adaptar uma referência, preserve cabeçalho, logos institucionais e
identidade gráfica. Títulos e numeração de página são atualizados para o novo
conteúdo e para a ordem final. Remova texto e imagens de exemplo que não
pertençam ao conteúdo do usuário.
