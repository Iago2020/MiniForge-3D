# MiniForge 3D

Fundação do pipeline local e modular para transformar capturas de uma pessoa em uma miniatura 3D imprimível.

## Estado atual

O projeto implementa somente a camada de controle:

- leitura e validação de configuração;
- detecção básica de hardware e ferramentas externas;
- criação de workspaces sem sobrescrita;
- fingerprints de entradas e configuração;
- plano de execução parcial;
- logs e contratos iniciais de manifest;
- detecção do adaptador COLMAP.
- preparação de frames com FFmpeg e seleção por qualidade/diversidade.
- segmentação local da pessoa, com frames de fundo uniforme e máscaras COLMAP.
- planejamento e execução protegida de reconstrução COLMAP.
- geração de STL imprimível a partir de uma única foto (`from-photo`).

A reconstrução, o tratamento de mesh e a preparação para impressão ainda não são executados.

## Preparação futura no Nitro com Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Comandos atuais

```powershell
miniforge3d preflight
miniforge3d run --config configs/example.yaml --dry-run
miniforge3d run --config configs/example.yaml --dry-run --only reconstruction
miniforge3d run --config configs/example.yaml --dry-run --start-from reconstruction
miniforge3d run --config configs/example.yaml --dry-run --resume --workspace workspaces/EXECUCAO
miniforge3d prepare-frames --video input/person-001.mp4 --output workspaces/teste/01-frames
miniforge3d segment-person --frames workspaces/teste/01-frames/frames_selected --output workspaces/teste/02-segmentation
miniforge3d reconstruct --frames workspaces/person-001/01-frames/frames_selected --output workspaces/person-001/02-reconstruction --dry-run
```

Para instalar a segmentação local:

```bash
python -m pip install -e '.[segmentation]'
```

As máscaras geradas seguem o padrão exigido pelo COLMAP (`<imagem>.png`) e podem
ser usadas assim:

```bash
miniforge3d reconstruct \
  --frames workspaces/person-002/02-segmentation/frames_masked \
  --masks workspaces/person-002/02-segmentation/masks \
  --output workspaces/person-002/03-reconstruction-masked-sparse \
  --mode sparse \
  --cpu
```

O módulo de frames cria:

```text
01-frames/
├── frames_all/
├── frames_selected/
├── logs/
├── metadata.json
└── manifest.json
```

Os valores iniciais são conservadores e deverão ser calibrados com vídeos reais. O algoritmo extrai candidatos em cadência alta e seleciona usando nitidez, brilho, contraste, diversidade visual e distribuição temporal; não trata a amostragem temporal como seleção final.

## Reconstrução

No Mac, gere e revise o plano sem executar o COLMAP:

```bash
miniforge3d reconstruct \
  --frames workspaces/person-001/01-frames/frames_selected \
  --output workspaces/person-001/02-reconstruction \
  --dry-run
```

Se o COLMAP estiver instalado no Mac, somente a reconstrução esparsa pode ser testada sem CUDA:

```bash
miniforge3d reconstruct \
  --frames workspaces/person-001/01-frames/frames_selected \
  --output workspaces/person-001/02-reconstruction-sparse \
  --mode sparse \
  --cpu
```

No Windows/Nitro com COLMAP CUDA disponível, a reconstrução completa será:

```powershell
miniforge3d reconstruct `
  --frames workspaces/person-001/01-frames/frames_selected `
  --output workspaces/person-001/02-reconstruction `
  --mode full
```

O modo completo executa extração de features, matching, SfM, dense stereo, fusão, meshes Poisson/Delaunay e texturização. A saída existente nunca é sobrescrita. Por padrão, usa matching exaustivo porque nossos datasets iniciais têm menos de algumas centenas de imagens e a prioridade é qualidade. Para conjuntos maiores, use `--matcher sequential`.

Todos os caminhos relativos da configuração são resolvidos a partir da pasta em que o comando é executado.

## Miniatura a partir de uma única foto

Rota alternativa ao vídeo: uma foto de corpo inteiro vira um STL pronto para o
Bambu Studio. A geração 3D roda de graça nos Spaces públicos do Hugging Face
(Hunyuan3D 2.1 por padrão, TRELLIS como alternativa), então não depende da GPU local.

```bash
python -m pip install -e '.[photo]'
miniforge3d from-photo --image input/foto.jpg --output workspaces/foto-001
```

Opções úteis: `--height-mm 150`, `--base round|none`, `--engine hunyuan3d|trellis`,
`--seed 42` (gera outra variação) e `--no-local-segmentation`.

Saída:

```text
foto-001/
├── 01-input/prepared.png      # pessoa recortada, fundo transparente
├── 02-generation/raw_mesh.glb # malha bruta devolvida pelo serviço
├── 03-print/model.stl         # Z para cima, frente em -Y, altura em mm, com base
└── manifest.json
```

O processamento local remove fragmentos soltos, fecha a malha, coloca a figura em pé,
escala para a altura pedida, aplaina os pés e une uma base redonda.

**Cota gratuita:** sem login, a cota de GPU do Hugging Face acaba depois de poucas
gerações por dia. Crie um token gratuito em https://huggingface.co/settings/tokens
(permissão *read*) e exporte antes de rodar:

```bash
export HF_TOKEN=hf_xxx
```

**Privacidade:** a foto é enviada para um serviço público de terceiros (Hugging Face e
o autor do Space). Use apenas fotos de pessoas que autorizaram isso.

**Dicas de foto:** corpo inteiro, de frente, boa luz, braços levemente afastados do
corpo, rosto nítido e nada na frente da pessoa. O fundo pode ser qualquer um.

Antes de gastar cota, o comando recusa fotos em que a pessoa está cortada pelo topo
ou pelas laterais, ou ocupa quase a imagem inteira (selfie muito próxima). Nesses casos
a IA costuma gerar uma placa achatada. Use `--allow-cropped` para tentar mesmo assim.

## Segurança do estado atual

Sem `--dry-run`, o comando `run` encerra antes das etapas externas. Isso impede que a fundação incompleta seja confundida com um pipeline funcional.

Consulte também:

- `3D_HUMAN_MINIATURE_PIPELINE.md`;
- `PHASE_1_RESEARCH_PLAN.md`;
- `TECHNOLOGY_RESEARCH.md`;
- `TECHNOLOGY_MATRIX.md`.
