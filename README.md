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

## Segurança do estado atual

Sem `--dry-run`, o comando `run` encerra antes das etapas externas. Isso impede que a fundação incompleta seja confundida com um pipeline funcional.

Consulte também:

- `3D_HUMAN_MINIATURE_PIPELINE.md`;
- `PHASE_1_RESEARCH_PLAN.md`;
- `TECHNOLOGY_RESEARCH.md`;
- `TECHNOLOGY_MATRIX.md`.
