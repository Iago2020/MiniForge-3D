# MiniForge 3D — Pesquisa de Tecnologias

> **Status:** em andamento  
> **Última verificação:** 2026-08-08  
> **Escopo desta versão:** R1 — fotogrametria, SfM e MVS  
> **Instalações realizadas:** nenhuma

## 1. Conclusão preliminar de R1

A melhor baseline inicial para o projeto é **COLMAP 4.0.4**, executado por CLI no Windows, usando primeiro seu próprio pipeline de SfM/MVS, meshing e texturização.

Duas rotas devem permanecer na shortlist para comparação posterior:

1. **COLMAP 4.0.4 completo** — baseline principal e menor quantidade de componentes.
2. **COLMAP 4.0.4 + OpenMVS 2.4.0** — alternativa para densificação, refinamento, mesh e textura.
3. **Meshroom 2025.1.0 / AliceVision 3.3.0** — baseline independente e pacote mais integrado.

Essa conclusão não afirma que COLMAP produzirá a melhor pessoa final. Ela apenas identifica a rota mais apropriada para estabelecer uma referência observacional, reproduzível e sem geração de identidade. Métodos neurais ainda precisam ser pesquisados antes da recomendação definitiva.

## 2. Por que começar por fotogrametria

O projeto exige reconstruir a pessoa capturada, não gerar uma pessoa plausível. Uma baseline baseada em correspondências entre imagens permite:

- medir se a captura possui cobertura e nitidez suficientes;
- inspecionar câmeras registradas e regiões sem observação;
- separar falha de captura de falha de geração de mesh;
- preservar imagens, câmeras, pontos, depth maps e textura;
- comparar posteriormente qualquer método neural contra uma referência comum.

O risco principal é o movimento. O próprio material do Meshroom recomenda evitar objetos em movimento. Uma pessoa respirando, piscando ou alterando mãos, roupa e cabelo viola a hipótese de cena estática da fotogrametria. Portanto, sucesso da baseline dependerá tanto do protocolo de captura quanto da engine.

Fonte: [manual Meshroom — captura e objetos em movimento](https://meshroom-manual.readthedocs.io/_/downloads/en/v19.01.45/pdf/).

## 3. COLMAP 4.0.4

### Papel possível

- extração e correspondência de features;
- estimativa de câmeras e reconstrução esparsa;
- reconstrução densa;
- fusão de depth maps;
- meshing Poisson ou Delaunay;
- texturização;
- exportação de dados intermediários para outros módulos.

### Evidências confirmadas

- É um pipeline geral de Structure-from-Motion e Multi-View Stereo.
- Possui GUI e CLI.
- A release estável encontrada é 4.0.4, publicada em 27 de abril de 2026.
- Há binários para Windows.
- O projeto documenta compilação CUDA no Windows por VCPKG.
- O pipeline denso produz depth/normal maps, nuvem fusionada e meshes Poisson/Delaunay.
- O `mesh_texturer` produz atlas de textura e coordenadas UV.
- Suporta máscaras durante a extração de features.
- Permite reduzir resolução máxima e quantidade de imagens vizinhas para diminuir consumo.
- A licença do COLMAP é New BSD; dependências de terceiros precisam ser auditadas separadamente.

Fontes:

- [repositório e release do COLMAP](https://github.com/colmap/colmap);
- [instalação oficial](https://colmap.github.io/install.html);
- [tutorial e pipeline denso](https://colmap.github.io/tutorial.html);
- [CLI oficial](https://github.com/colmap/colmap/blob/main/doc/cli.rst);
- [formatos de saída](https://colmap.github.io/format.html);
- [FAQ: máscaras, memória e resolução](https://colmap.github.io/faq.html);
- [licença oficial](https://colmap.github.io/license.html).

### Compatibilidade com o Nitro

**Provisoriamente compatível**, pois há suporte oficial a Windows/CUDA e mecanismos documentados para reduzir resolução/carga. A documentação consultada não estabelece um mínimo universal de VRAM para todos os datasets. Portanto, não é correto afirmar que 6 GB bastarão em qualidade máxima sem teste.

Adaptações previstas se houver falta de memória:

- limitar resolução na extração e na reconstrução densa;
- reduzir número de source images por imagem de referência;
- controlar cache e threads conforme a RAM disponível;
- testar primeiro um dataset pequeno e bem selecionado;
- executar feature extraction em CPU apenas como fallback, reconhecendo o custo de RAM e tempo.

### Pontos fortes para este projeto

- menor risco de inventar identidade;
- excelente observabilidade dos passos intermediários;
- CLI adequada a adaptador modular;
- saídas compatíveis com processamento posterior;
- máscaras podem impedir features no fundo;
- licença permissiva do componente principal;
- Windows é plataforma oficialmente suportada.

### Riscos e lacunas

- sujeito precisa permanecer praticamente estático;
- pele, cabelo e tecidos lisos podem fornecer poucas correspondências;
- rosto pode ocupar poucos pixels nos frames de corpo inteiro;
- reconstrução não possui escala métrica automática para este caso;
- mesh resultante ainda poderá exigir reparo cuidadoso;
- GPU usada também dirige a tela do notebook, e cargas densas podem causar timeout no Windows;
- requisitos reais de VRAM/RAM precisam ser medidos com o dataset humano.

### Decisão provisória

**Manter como baseline principal.** Não instalar ainda neste computador, pois o ambiente-alvo é o Nitro com Windows. A instalação deve ocorrer somente no gate experimental e diretamente na máquina-alvo.

## 4. OpenMVS 2.4.0

### Papel possível

Receber câmeras e nuvem esparsa do COLMAP e executar:

- densificação;
- reconstrução de mesh;
- refinamento da superfície;
- limpeza;
- texturização.

### Evidências confirmadas

- A release 2.4.0 foi publicada em 20 de janeiro de 2026.
- A entrada conceitual é um conjunto de poses/câmeras e nuvem esparsa; a saída é mesh texturizada.
- O projeto possui interface oficial para saída densa do COLMAP.
- A release 2.4 acrescentou melhorias em ROI, máscaras/segmentação, estruturas finas e limpeza de mesh.
- Existem builds estáveis para Windows x64, inclusive CUDA, conforme a documentação de build.
- Possui aplicativos CLI separados e API Python opcional.
- A licença é AGPL-3.0.

Fontes:

- [repositório oficial OpenMVS](https://github.com/cdcseacave/openMVS);
- [release 2.4.0](https://github.com/cdcseacave/openMVS/releases);
- [interface com COLMAP](https://github-wiki-see.page/m/cdcseacave/openMVS/wiki/Interface);
- [uso do pipeline COLMAP + OpenMVS](https://github-wiki-see.page/m/cdcseacave/openMVS/wiki/Usage);
- [builds e dependências](https://github-wiki-see.page/m/cdcseacave/openMVS/wiki/Building);
- [licença AGPL-3.0](https://raw.githubusercontent.com/cdcseacave/openMVS/master/LICENSE).

### Compatibilidade com o Nitro

**Possível, mas não comprovada em 6 GB.** O projeto oferece CUDA opcional e mecanismos como nível de resolução, ROI e divisão de cenas. A documentação não fornece um mínimo universal de VRAM. O uso real dependerá de quantidade de imagens, resolução, vizinhança e tamanho da mesh.

### Pontos fortes para este projeto

- especialização na metade final da fotogrametria;
- saída direta em mesh texturizada;
- integração documentada com COLMAP;
- refinamento e texturização separados, úteis para benchmarks;
- suporte atual a Windows/CUDA;
- mecanismos recentes de máscaras, ROI e estruturas finas.

### Riscos e lacunas

- adiciona conversão e outro ambiente ao pipeline;
- aumenta a superfície de falhas e incompatibilidades;
- licença AGPL exige revisão cuidadosa caso o projeto evolua para distribuição/serviço comercial;
- ainda herda todas as limitações da captura estática;
- ganho sobre o MVS interno do COLMAP precisa ser demonstrado, não presumido.

### Decisão provisória

**Manter como segunda rota técnica.** Comparar somente após obter uma reconstrução válida com COLMAP. Se não houver ganho em face, completude ou mesh, evitar a complexidade adicional.

## 5. Meshroom 2025.1.0 / AliceVision 3.3.0

### Papel possível

- baseline completa alternativa;
- exploração visual e diagnóstico do dataset;
- pipeline integrado de photogrammetry;
- possível uso futuro de segmentação e plugins.

### Evidências confirmadas

- Meshroom 2025.1.0 foi publicado em 18 de agosto de 2025.
- A release possui download oficial para Windows e Linux.
- Os binários são construídos com CUDA 12 e requerem compute capability mínima 5.0.
- A release usa AliceVision 3.3.0.
- Existe `meshroom_batch` para execução por CLI, com input, output, cache e overrides.
- O grafo invalida nós downstream quando parâmetros mudam e reaproveita cache intermediário.
- O projeto é licenciado sob MPL-2.0.

Fontes:

- [release oficial Meshroom 2025.1.0](https://github.com/alicevision/meshroom/releases);
- [repositório oficial Meshroom](https://github.com/alicevision/meshroom);
- [repositório oficial AliceVision](https://github.com/alicevision/AliceVision);
- [CLI `meshroom_batch`](https://meshroom-manual.readthedocs.io/en/latest/feature-documentation/cmd/photogrammetry.html);
- [instalação e binários](https://meshroom-manual.readthedocs.io/en/latest/first-steps/install/getting-meshroom/).

### Compatibilidade com o Nitro

**Provável, ainda não validada.** A GPU indicada pelo projeto possui CUDA e a release oferece Windows/CUDA. Precisamos confirmar compute capability, driver compatível e comportamento do DepthMap com 6 GB antes de aprovar.

### Pontos fortes para este projeto

- pacote integrado e visualmente inspecionável;
- binário Windows pronto;
- pipeline em lote disponível;
- cache e invalidação por grafo;
- logs e resultados por nó;
- alternativa independente para distinguir problema de captura de problema específico do COLMAP.

### Riscos e lacunas

- facilidade de uso não implica melhor fidelidade;
- abstração em grafo pode dificultar normalização fina no início;
- pipeline completo ainda sofre com movimento humano;
- requisitos reais para máxima resolução precisam ser medidos;
- plugins experimentais não devem entrar na baseline sem pesquisa própria.

### Decisão provisória

**Manter como baseline de controle.** É a primeira alternativa completa a comparar contra COLMAP, mas não a primeira escolha para o adaptador principal.

## 6. Comparação preliminar

| Critério | COLMAP 4.0.4 | COLMAP + OpenMVS 2.4 | Meshroom 2025.1 |
|---|---|---|---|
| Windows oficial | sim | sim | sim |
| CUDA | sim | opcional/sim | sim, binário CUDA 12 |
| CLI | sim | sim | sim |
| SfM | sim | fornecido pelo COLMAP | sim |
| Dense/MVS | sim | OpenMVS | sim |
| Mesh | sim | sim, foco central | sim |
| Textura | sim | sim | sim |
| Máscaras | features | densificação/segmentação atual | recursos de segmentação/pipeline |
| Licença principal | New BSD | BSD + AGPL-3.0 | MPL-2.0 |
| Complexidade inicial | média | alta | baixa/média |
| VRAM mínima comprovada para nosso caso | não | não | não |
| Decisão | baseline principal | segunda rota | controle independente |

## 7. Rota recomendada para a primeira validação futura

```text
frames selecionados e máscaras opcionais
    → COLMAP 4.0.4: features + matching + SfM
    → inspeção de câmeras registradas e nuvem esparsa
    → COLMAP 4.0.4: dense stereo + fusion
    → Poisson e Delaunay como duas saídas preservadas
    → mesh_texturer
    → PLY texturizado + atlas + dados de câmera
    → avaliação antes de qualquer reparo
```

Se essa rota registrar as câmeras, mas a etapa densa/mesh for insuficiente, testar a mesma reconstrução de câmeras com OpenMVS. Meshroom deverá executar o mesmo conjunto de frames como controle independente.

## 8. Critérios de sucesso da baseline

A baseline não precisa produzir uma miniatura perfeita. Ela precisa responder objetivamente:

- qual porcentagem dos frames foi registrada;
- se existe cobertura 360° coerente;
- se face, cabeça, tronco, braços e pernas aparecem na nuvem/mesh;
- quais regiões falharam;
- se movimento criou duplicação ou borramento geométrico;
- se a mesh possui detalhe facial utilizável;
- se a textura preserva identidade visual;
- qual o pico de VRAM, RAM, disco e duração;
- se a saída abre em ferramentas de mesh sem corrupção.

## 9. Pendências antes do gate experimental

- Pesquisar VGGT, DUSt3R, MASt3R e alternativas atuais.
- Pesquisar métodos específicos de reconstrução humana/facial.
- Definir protocolo provisório de captura.
- Confirmar modelo do celular e resolução/FPS disponíveis.
- Confirmar corpo inteiro ou busto no primeiro teste.
- Confirmar tamanho prioritário da miniatura.
- Inventariar driver/CUDA/espaço em disco do Nitro.
- Definir dataset mínimo e regras de privacidade.
- Estimar tamanho dos downloads e ambientes.

## 10. Decisão atual

Continuar a pesquisa. **Não instalar ainda.** O candidato principal de R1 é COLMAP 4.0.4, mas o Pipeline V1 só será decidido depois de avaliar reconstrução neural e abordagens específicas para pessoas.
