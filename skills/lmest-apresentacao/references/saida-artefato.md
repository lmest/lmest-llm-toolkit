# Saída como artefato Slides do claude.ai

Só quando o usuário escolher essa saída **e** as ferramentas de artefato existirem nesta sessão (`list_types`, `describe_type`, `create_from_type`, `publish_files`, `upload_asset`, `list_files`, `read_file`). Se faltarem, diga que esta sessão não publica artefatos e ofereça HTML ou PPTX.

O formato-fonte da skill já é o do tipo Slides (uma `<section>` por arquivo, `deck.json` com `order`). Por isso, publicar é subir as imagens, trocar os `src` e enviar os arquivos.

## Criar o artefato

1. Rode `validar.py` (sem erros) e `numerar.py`.
2. `list_types` e ache o tipo **Slides** ("Presentation decks: 16:9 slides…"; em 2026-11 o slug era `3e9dc3d6-8a10-4143-ac0b-5af4f2b03a61`). Chame `describe_type` e leia as instruções e os arquivos de referência que ele indicar (`format.md`, `deck-files.md`). **Se as instruções do tipo divergirem desta página em mecânica de envio, siga as do tipo.**
3. Liste as imagens a subir:
   ```bash
   python3 -I <skill>/scripts/preparar_artefato.py PASTA listar
   ```
   Suba cada caminho impresso com `upload_asset` e registre o `/_blob/<id>` devolvido em `PASTA/saida/artefato/blobs.json`, com a chave igual ao `src` usado nos slides: `{"lmest/logos/ufu.png": "/_blob/…", "imagens/grafico.svg": "/_blob/…"}`. Grave esse arquivo com a ferramenta de escrita, não com o shell.
4. Monte a pasta de envio:
   ```bash
   python3 -I <skill>/scripts/preparar_artefato.py PASTA montar
   ```
   Ela cria `PASTA/saida/artefato/project/deck.json` e `project/slides/<id>.html`, com os `src` trocados.
5. `create_from_type` uma vez, com o título do deck.
6. **Design System**: instale o "Design System LMEst-UFU" (`https://claude.ai/artifact/c21d9ee2-8534-40e3-875d-c958d06472ab`, namespace `lmest-ufu`) no deck, como manda a seção "A design system in the deck" do `deck-files.md` do tipo: a entrada de `project/ds/lmest-ufu/tokens.json` e o registro em `designSystems` do `deck.json`, no mesmo envio dos slides.
7. `publish_files` com `mode:"patch"`, enviando `project/deck.json` e todos os `project/slides/<id>.html` (no máximo 15 arquivos por chamada quando a ferramenta pedir; o `deck.json` vai na última). Nunca envie `index.html`, `SKILL.md` nem nada em `artifact-type/`.
8. Informe o link e a versão publicada. **Não abra, não renderize e não confira o artefato depois de publicar**: o usuário confere.

## Editar um artefato existente

1. `list_files` no artefato e `read_file` em `project/deck.json` e em cada slide que vai mudar. O usuário edita no editor do artefato também: parta sempre da versão que acabou de ler.
2. Para mudanças pequenas (texto, um slide), edite o arquivo lido e envie com `publish_files` (`mode:"patch"`), ou com `edit_version` usando `path`. Confirme que o trecho a trocar existe exatamente, com maiúsculas e espaços (alguns arquivos usam `#1E88C7` ou `width:N px;height` sem espaço).
3. Para mudanças de estrutura (inserir, remover ou mover slides, renumerar, barra de progresso), traga o deck para uma pasta local:
   - Grave `deck.json` e `slides/<id>.html` lidos numa pasta `PASTA/` (com a ferramenta de escrita).
   - Crie `PASTA/projeto.json` com `"origem_artefato": "<slug>"`, `"barra_progresso"` conforme o deck tem hoje, `"saidas": ["artefato"]` e, em `"sem_numero"`, os ids que não levam número (capa, divisórias, resumo, agradecimento e outros que o usuário definiu).
   - Edite, rode `numerar.py` e `validar.py`. Em projetos de artefato, `/_blob/` é aceito e slides antigos em layout de fluxo geram só aviso. Slides **novos** seguem o formato fixado.
   - Envie só os arquivos alterados com `publish_files` (`mode:"patch"`); para remover um slide, `"project/slides/<id>.html": null` e o `deck.json` sem o id.
4. **Não assuma que número e barra seguem a regra**: decks antigos têm casos fora do padrão. `numerar.py` apaga os existentes (pelo estilo: `top:1000px; left:1631px` e `top:1073px`) e escreve os corretos.
5. Imagens novas: `upload_asset` e `src="/_blob/<id>"`.
6. Um conflito (alguém salvou nesse meio-tempo): releia os arquivos, refaça a edição sobre eles e envie de novo, uma vez.
