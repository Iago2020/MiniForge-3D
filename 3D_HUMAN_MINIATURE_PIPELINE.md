# MiniForge 3D — Pipeline Local para Miniaturas 3D de Pessoas

> Documento de continuidade e planejamento. Este projeto ainda não possui implementação.
>
> **Estado atual:** Fase 0 — planejamento inicial  
> **Próxima fase:** pesquisa técnica comparativa  
> **Regra:** não iniciar o MVP antes de revisar e aprovar os resultados da pesquisa.
> **Limite desta etapa:** revisar documentação não autoriza instalar ferramentas, criar módulos ou executar reconstruções.

## 1. Visão do projeto

Construir um pipeline gratuito, local e modular capaz de transformar vídeos e/ou fotos de uma pessoa real em uma miniatura 3D reconhecível e preparada para impressão em uma Bambu Lab A1.

O fluxo pretendido é:

```text
captura da pessoa
    → preparação do dataset
    → reconstrução 3D
    → tratamento da malha
    → preparação para impressão
    → Bambu Studio
    → impressão FDM e pintura manual
```

O projeto será inicialmente pessoal, operado por linha de comando e sem serviços em nuvem. Tempo de processamento longo é aceitável quando resultar em melhor qualidade.

### Ordem de prioridade

1. Fidelidade à pessoa.
2. Qualidade da geometria.
3. Imprimibilidade.
4. Estabilidade e reprodutibilidade.
5. Automação.
6. Velocidade.
7. Facilidade de uso.

## 2. Escopo

### Dentro do escopo inicial

- Captura feita com celular, usando um ou mais vídeos/fotos.
- Execução 100% local.
- Seleção inteligente e preparação de frames.
- Reconstrução de corpo, rosto, roupas e acessórios.
- Preservação de textura quando disponível.
- Conversão da reconstrução em malha fechada e imprimível.
- Exportação mínima em STL e, quando possível, OBJ + MTL + texturas.
- Configuração por arquivo, preferencialmente YAML.
- Componentes independentes coordenados por um orquestrador.
- Execução retomável, parcial e observável.
- Documentação de captura e operação.
- Benchmark de alternativas com casos reais.

### Fora do MVP

- SaaS, aplicação web ou mobile.
- Interface gráfica.
- Autenticação e multiusuário.
- Processamento distribuído ou em nuvem.
- Automação completa do Bambu Studio.
- Slicing e envio automático para a impressora.
- Suportes automáticos avançados.
- Separação automática sofisticada em várias peças.
- Impressão multicolorida.
- Estilos LEGO-like, Funko-like, chibi, bobblehead ou caricatura.
- Uso comercial.

### Definição das atividades

- **Pesquisa documental:** levantamento de ferramentas, requisitos, licenças, limitações e evidências publicadas.
- **Validação experimental:** instalação e execução controlada de candidatos selecionados para confirmar afirmações da pesquisa.
- **Implementação do pipeline:** criação dos módulos, contratos executáveis e orquestrador definitivos.

A pesquisa documental acontece primeiro. Validações experimentais só devem começar após a seleção justificada dos candidatos e não representam autorização para implementar o pipeline completo.

## 3. Critério central de fidelidade

O resultado não deve ser apenas uma pessoa 3D plausível: deve representar a pessoa capturada. Devem ser preservados, na maior medida possível:

- formato do rosto e da cabeça;
- nariz, boca, olhos e orelhas;
- cabelo;
- proporções corporais;
- roupas;
- acessórios relevantes.

IA generativa só deverá ser usada quando houver evidência de que melhora regiões incompletas sem descaracterizar a identidade. Um resultado visualmente bonito, mas inventado, é falha para este projeto.

## 4. Ambiente-alvo

### Máquina principal

**Acer Nitro V15 — Windows**

- Intel Core i5-13420H;
- NVIDIA RTX 3050 Laptop;
- 6 GB de VRAM;
- 16 GB de RAM DDR5;
- CUDA disponível.

O Nitro será a referência para compatibilidade, instalação, desempenho e testes.

### Máquinas disponíveis, mas não integradas inicialmente

- Desktop: Ryzen 7 5700X, 16 GB RAM, RX 6600M 8 GB.
- MacBook Pro: Apple M4, 16 GB de memória unificada.

Não distribuir processamento entre máquinas na primeira versão. Elas poderão ser avaliadas posteriormente como alternativas por etapa.

### Impressora e preparação final

- Impressora: Bambu Lab A1.
- Preparação e slicing: manualmente no Bambu Studio durante o MVP.
- Saídas prioritárias: STL e OBJ texturizado.
- Saída futura: 3MF.

## 5. Requisitos confirmados, hipóteses e decisões abertas

### Requisitos confirmados

- O pipeline deve funcionar localmente e sem custos de serviços.
- A qualidade tem prioridade sobre o tempo.
- A arquitetura deve ser modular e permitir troca de engines.
- Cada etapa deve expor entrada, saída e status por arquivos e CLI.
- Falhas não podem obrigar a repetir etapas concluídas.
- Erros e saídas de ferramentas externas devem ser preservados nos logs.
- Processamentos anteriores não podem ser sobrescritos automaticamente.
- A textura deve ser preservada, ainda que a impressão inicial seja monocromática.
- Licenças de código e pesos de modelos devem ser registradas.
- O MVP só começará depois da fase de pesquisa e de sua aprovação.

### Hipóteses a validar

- Vídeo 360° de celular fornecerá cobertura suficiente para uma miniatura reconhecível.
- Fotogrametria clássica pode superar abordagens generativas na preservação da identidade.
- Uma abordagem híbrida de corpo + rosto pode melhorar a fidelidade global.
- Segmentação prévia da pessoa pode ajudar a reconstrução em alguns engines.
- Gaussian Splatting pode servir como etapa intermediária útil para geração de mesh.
- 6 GB de VRAM serão suficientes com resolução reduzida, processamento em blocos ou offload.
- O Windows será adequado; WSL2 ou Linux podem ser necessários para engines específicas.
- Uma malha fiel poderá ser tornada imprimível sem destruir detalhes faciais.

### Decisões em aberto

- Tipo e quantidade ideal de capturas: um vídeo, vários vídeos, fotos ou combinação.
- Regras de seleção de frames e quantidade ideal por reconstrução.
- Necessidade de fundo neutro, marcadores, máscara ou turntable.
- Engine principal de reconstrução.
- Papel de SfM/MVS, reconstrução neural e Gaussian Splatting.
- Estratégia específica para rosto e eventual fusão rosto/corpo.
- Windows nativo, WSL2, Docker com GPU ou Linux.
- Ferramentas de processamento de mesh.
- Formato canônico entre módulos: OBJ, PLY, GLB, outro ou combinação.
- Forma de medir fidelidade e qualidade de maneira repetível.
- Limites mínimos de espessura e detalhes adequados à Bambu Lab A1.

## 6. Arquitetura modular proposta

A estrutura abaixo é uma proposta para orientar a pesquisa; ainda não é definitiva.

```text
MiniForge 3D/
├── orchestrator/
├── modules/
│   ├── 01-frame-preparation/
│   ├── 02-reconstruction/
│   ├── 03-mesh-processing/
│   └── 04-print-preparation/
├── configs/
├── contracts/
├── docs/
├── benchmarks/
├── scripts/
├── tests/
└── workspaces/
```

### Princípios

- Um módulo não conhece detalhes internos de outro.
- A integração ocorre por CLI, arquivos, diretórios e manifests versionados.
- Dependências podem ficar isoladas por módulo.
- Engines são implementadas como adaptadores substituíveis.
- O orquestrador controla a sequência, mas não implementa algoritmos das etapas.
- Resultados intermediários devem ser preservados para inspeção e comparação.

### Módulo 01 — Frame Preparation

**Entrada:** um ou mais vídeos/fotos.  
**Saída:** dataset selecionado, máscaras opcionais, metadados e manifest.

Responsabilidades candidatas:

- extrair frames e metadados;
- medir blur, exposição e variação entre imagens;
- eliminar frames ruins e quase duplicados;
- selecionar imagens com boa cobertura e diversidade de ângulos;
- gerar máscaras quando isso beneficiar a engine escolhida;
- registrar estatísticas e motivos de descarte.

Não adotar como regra simples “um frame a cada X segundos” antes de comparar estratégias melhores.

### Módulo 02 — Reconstruction

**Entrada:** dataset preparado e parâmetros da engine.  
**Saída:** reconstrução bruta, câmeras, nuvem de pontos, textura e/ou mesh, conforme a engine.

Responsabilidades:

- executar uma engine por meio de adaptador;
- validar requisitos de hardware antes da execução;
- preservar artefatos intermediários relevantes;
- normalizar a saída para um contrato comum;
- documentar limitações e parâmetros efetivos.

Configuração conceitual:

```yaml
reconstruction:
  engine: auto
  quality: maximum
  cuda: true
```

O valor `auto` só deverá existir quando houver critérios explícitos e previsíveis de seleção.

### Módulo 03 — Mesh Processing

**Entrada:** reconstrução bruta normalizada.  
**Saída:** mesh limpa, fechada e detalhada.

Responsabilidades candidatas:

- remover cenário e componentes isolados;
- corrigir normais e geometria non-manifold;
- fechar buracos;
- remesh e decimar com preservação de detalhes;
- engrossar regiões frágeis;
- tratar mãos, dedos, cabelo, óculos, orelhas, nariz e acessórios;
- garantir malha watertight;
- criar uma superfície inferior adequada.

Operações agressivas devem ser condicionais e comparadas com a malha de entrada, especialmente na face.

### Módulo 04 — Print Preparation

**Entrada:** mesh tratada e parâmetros físicos.  
**Saída:** STL e demais arquivos preparados para o Bambu Studio.

MVP:

- escala proporcional;
- altura final configurável;
- validação básica;
- exportação STL.

Evoluções:

- base opcional e texto;
- orientação;
- análise de overhang;
- separação em partes;
- encaixes;
- preparação multicolorida;
- exportação 3MF.

### Orquestrador

Responsável por:

- validar configuração e hardware;
- criar workspace exclusivo;
- executar módulos na ordem;
- impedir avanço quando uma etapa falhar;
- implementar `--resume`, `--start-from` e `--only`;
- consolidar status, logs e métricas;
- nunca apagar ou sobrescrever uma execução sem ação explícita.

Exemplo conceitual:

```text
run_pipeline --config configs/maria.yaml
run_pipeline --workspace maria-formatura --resume
run_pipeline --workspace maria-formatura --start-from reconstruction
run_pipeline --workspace maria-formatura --only reconstruction
```

## 7. Contratos entre módulos

Os contratos deverão ser versionados antes do MVP. Cada etapa recebe:

- caminho do workspace;
- arquivo de configuração resolvido;
- manifest da etapa anterior;
- diretório de saída exclusivo;
- identificador da execução.

Cada etapa deve devolver exit code coerente e um `manifest.json`.

O contrato de qualquer artefato 3D também deverá declarar explicitamente:

- formato e versão do arquivo;
- unidade física ou indicação de que o modelo ainda está sem escala;
- orientação dos eixos e definição de “cima” e “frente”;
- sistema de coordenadas e transformação aplicada;
- quantidade de vértices, faces, componentes e materiais;
- vínculo entre mesh, MTL e texturas;
- codificação de cores e espaço de cor, quando relevante.

Isso evita inversões, mudanças silenciosas de escala e perda de textura ao trocar de engine ou ferramenta.

### Manifest mínimo proposto

```json
{
  "schema_version": "1.0",
  "run_id": "maria-formatura-2026-08-08-001",
  "step": "frame_preparation",
  "status": "completed",
  "tool_versions": {},
  "effective_config": {},
  "inputs": [],
  "outputs": [],
  "input_fingerprint": "",
  "config_fingerprint": "",
  "statistics": {},
  "warnings": [],
  "error": null,
  "started_at": "",
  "finished_at": "",
  "duration_seconds": 0
}
```

### Estados permitidos

```text
pending | running | completed | failed | skipped | cancelled
```

Um arquivo de conclusão só deve ser gravado depois que todas as saídas obrigatórias forem validadas. A existência de um arquivo isolado não basta para o `--resume` considerar a etapa concluída. Se entradas, configuração relevante, versão da engine ou contrato mudarem, o resultado anterior deve ser considerado incompatível e a etapa precisa ser reexecutada ou explicitamente reutilizada pelo usuário.

### Proveniência e reprodutibilidade

Registrar por execução:

- versões de ferramentas, modelos, drivers e CUDA;
- comando executado e parâmetros efetivos;
- hashes ou identificação inequívoca dos arquivos de entrada;
- fingerprints da configuração e das dependências que afetam o resultado;
- hardware detectado;
- data e duração;
- aleatoriedade/seeds, quando aplicável;
- licença e origem dos componentes relevantes.

## 8. Workspaces, logs e métricas

```text
workspaces/
└── maria-formatura-2026-08-08-001/
    ├── input/
    ├── 01-frames/
    │   ├── frames_all/
    │   ├── frames_selected/
    │   ├── masks/
    │   └── manifest.json
    ├── 02-reconstruction/
    │   └── manifest.json
    ├── 03-mesh/
    │   └── manifest.json
    ├── 04-print/
    │   └── manifest.json
    ├── logs/
    │   ├── pipeline.log
    │   ├── frame-preparation.log
    │   ├── reconstruction.log
    │   ├── mesh-processing.log
    │   └── print-preparation.log
    ├── resolved-config.yaml
    └── pipeline.json
```

Logs de ferramentas externas devem manter comando, exit code, stdout, stderr e duração. Segredos e informações pessoais eventualmente presentes em caminhos ou metadados devem ser tratados antes de compartilhar logs.

Métricas desejáveis durante etapas pesadas:

- CPU e RAM;
- GPU, VRAM e temperatura, quando disponíveis;
- espaço em disco;
- tempo por subetapa;
- tamanho dos artefatos.

## 9. Configuração conceitual

```yaml
project:
  id: maria-formatura

input:
  videos:
    - input/maria.mp4

frames:
  quality: maximum

reconstruction:
  engine: auto
  quality: maximum
  cuda: true

mesh:
  preserve_face_detail: true

model:
  height_mm: 150

base:
  enabled: true
  type: circular
  text: Maria
  height_mm: null

output:
  stl: true
  obj: true
  three_mf: false
```

Esse arquivo é ilustrativo. O schema real só deverá ser definido depois da pesquisa e dos primeiros experimentos.

## 10. Estratégia de captura a documentar

A pesquisa deverá resultar em um guia prático cobrindo:

- iluminação uniforme e ausência de sombras móveis;
- foco, exposição, resolução e FPS;
- distância e enquadramento;
- velocidade do movimento;
- motion blur;
- pose da pessoa e posição dos braços;
- fundo, piso e objetos de escala;
- número de voltas e alturas;
- captura do topo da cabeça e áreas ocultas;
- cabelo, tecidos reflexivos, transparentes ou sem textura;
- quando usar vídeos separados, fotos ou close específico do rosto.

Também deve ser testado se a pessoa permanece imóvel enquanto a câmera circula ou se outra estratégia de captura oferece resultado superior.

## 11. Fase de pesquisa

### Pergunta principal

Qual combinação open source, local e estável produz a miniatura mais fiel e imprimível no hardware-alvo, aceitando processamento demorado?

### Famílias e tecnologias a investigar

A lista é ponto de partida, não decisão:

- **SfM/MVS:** COLMAP, OpenMVS, AliceVision/Meshroom e alternativas atuais.
- **Reconstrução multi-view/neural:** DUSt3R, MASt3R, VGGT e projetos atuais relacionados.
- **Gaussian Splatting e mesh:** implementações de 3DGS, SuGaR e conversores atuais.
- **Reconstrução generativa:** Hunyuan3D, InstantMesh, TRELLIS e alternativas atuais.
- **Reconstrução humana/facial:** modelos paramétricos, multi-view human reconstruction, fitting corporal/facial e métodos de fusão.
- **Segmentação e preparação:** FFmpeg, OpenCV e segmentadores locais adequados.
- **Mesh:** Blender/Python API, Open3D, Trimesh, MeshLab e alternativas.
- **Validação para impressão:** ferramentas de análise/manifold, Blender, MeshLab e recursos do Bambu Studio.

Para cada candidato, verificar documentação, releases, issues recentes, requisitos reais, licença do código e dos pesos, exemplos com pessoas, exportação de mesh e relatos em GPUs de 6 GB. Não confiar apenas no README ou em demonstrações promocionais.

### Critérios objetivos de comparação

| Dimensão | Evidência esperada |
|---|---|
| Identidade facial | avaliação cega e comparação visual padronizada |
| Fidelidade corporal | silhueta, proporções e detalhes das roupas |
| Cobertura | regiões ausentes, buracos e partes inventadas |
| Geometria | ruído, detalhes úteis, topologia e consistência |
| Textura | nitidez, costuras, cobertura e correspondência |
| Imprimibilidade | watertight, non-manifold, espessura e elementos frágeis |
| Hardware | pico de VRAM/RAM, disco e compatibilidade com 6 GB |
| Desempenho | tempo total e por etapa, sem priorizá-lo sobre qualidade |
| Estabilidade | falhas, repetibilidade e clareza de diagnóstico |
| Integração | CLI, formatos, automação e isolamento de dependências |
| Plataforma | Windows nativo, WSL2, Linux e restrições conhecidas |
| Maturidade | manutenção, releases, comunidade e documentação |
| Licença | código, pesos, datasets e possível uso comercial futuro |

### Escala de avaliação sugerida

Usar notas de 1 a 5 acompanhadas por evidências, artefatos e observações. Não produzir uma nota agregada sem pesos aprovados. Identidade facial, fidelidade corporal e imprimibilidade devem ter peso maior que velocidade e facilidade.

## 12. Experimentos necessários

### E0 — Validação do ambiente

Objetivo: mapear GPU, VRAM, CUDA, driver, RAM, disco e opções de execução.  
Sucesso: relatório reproduzível do ambiente e matriz de compatibilidade inicial.

### E1 — Protocolo de captura

Comparar, com a mesma pessoa:

- um vídeo contínuo;
- vários vídeos em alturas diferentes;
- conjunto de fotos;
- vídeo corporal + close específico do rosto.

Sucesso: protocolo que maximize cobertura e nitidez sem exigir app próprio.

### E2 — Seleção de frames

Comparar amostragem temporal, filtros de blur/duplicação e seleção por diversidade/cobertura.  
Sucesso: reduzir redundância sem degradar reconstrução e documentar quantidade recomendada.

### E3 — Engines de reconstrução

Executar candidatos viáveis sobre o mesmo dataset e preservar todas as configurações.  
Sucesso: ranking fundamentado e pelo menos uma rota executável no hardware-alvo.

### E4 — Fidelidade facial

Comparar reconstrução global com possíveis rotas de rosto dedicado e fusão.  
Sucesso: ganho visível e repetível sem alterar a identidade nem criar costuras inaceitáveis.

### E5 — Mesh para impressão

Comparar limpeza, fechamento, remesh, decimação e espessamento.  
Sucesso: STL watertight que preserve detalhes essenciais e abra corretamente no Bambu Studio.

### E6 — Impressão física

Imprimir pelo menos um modelo em alturas representativas, por exemplo 100, 150 e 200 mm.  
Sucesso: identificar o limite real de detalhes, fragilidade, orientação e acabamento da A1.

### Dataset e registro dos testes

```text
tests/
├── person-001/
└── person-002/

benchmarks/
└── runs.csv ou runs.jsonl
```

Cada execução deve registrar pessoa/dataset, engine, configuração, frames, duração, VRAM máxima, resultado, falhas, avaliação e caminhos dos artefatos. Dados pessoais não devem ser publicados sem consentimento.

Antes dos testes, deve existir uma cópia preservada dos arquivos de captura originais. Workspaces são derivados e podem ter política de retenção; as capturas originais não devem depender deles como única cópia.

## 13. Riscos técnicos

| Risco | Impacto | Mitigação a investigar |
|---|---|---|
| Pessoa se move durante a captura | artefatos e falha de correspondência | captura curta, pose estável, múltiplas tomadas |
| Pele, cabelo e roupas sem textura | baixa correspondência e buracos | iluminação, resolução, close, métodos humanos/neural |
| Face pequena nos frames corporais | perda de identidade | captura facial dedicada e eventual fusão |
| Regiões ocultas | geometria ausente ou inventada | protocolo multialtura e poses adequadas |
| 6 GB de VRAM | engine não inicia ou resolução insuficiente | offload, tiling, menor resolução, engines alternativas |
| 16 GB de RAM | swapping ou falha em datasets grandes | lotes menores, subsampling, paginação e upgrade futuro |
| Windows incompatível | instalação frágil ou baixo desempenho | WSL2, Linux nativo ou engine alternativa |
| Conversão para mesh | perda de detalhe e topologia ruim | comparar métodos e preservar artefato original |
| Correção watertight | destruição do rosto/dedos | processamento localizado e validação antes/depois |
| Partes finas em FDM | quebra ou desaparecimento | espessamento seletivo e testes físicos |
| IA alucina detalhes | descaracterização da pessoa | limitar uso, comparar com referências e exigir aprovação |
| Ecossistema muda rapidamente | obsolescência | adaptadores, contratos estáveis e benchmark reproduzível |
| Licenças restritivas | bloqueio de uso futuro | inventário desde a pesquisa e alternativas permissivas |
| Alto uso de disco | interrupção e workspaces enormes | estimativa prévia, métricas e política explícita de retenção |
| Escala, eixos ou transformações inconsistentes | modelo invertido, deformado ou com dimensão incorreta | contrato 3D explícito e validação automática de unidade/orientação |
| `--resume` reutiliza resultado obsoleto | benchmark inválido ou saída incoerente | fingerprints de entrada, configuração, engine e schema |
| Perda das capturas originais | teste irrepetível e dado pessoal perdido | cópia preservada, checksum e política de backup local |

## 14. Alternativas para limites da RTX 3050 6 GB

Não descartar automaticamente uma tecnologia que peça mais VRAM. Avaliar, nesta ordem, desde que a solução permaneça estável:

1. redução controlada de resolução;
2. processamento em blocos/tiles ou lotes;
3. precisão reduzida suportada oficialmente;
4. CPU/RAM offload;
5. quantização suportada;
6. menor quantidade de frames bem selecionados;
7. divisão do pipeline em etapas independentes;
8. WSL2 ou Linux, se houver ganho comprovado;
9. engine alternativa com perda de qualidade medida;
10. upgrade de RAM/GPU apenas após identificar o gargalo real.

Para cada adaptação, medir a perda de fidelidade. Uma execução possível, porém instável ou que descaracterize a pessoa, não é uma solução aceitável.

## 15. Fases e critérios de sucesso

### Fase 0 — Planejamento

**Entrega:** este documento revisado.  
**Sucesso:** escopo, prioridades, decisões abertas e plano de pesquisa aprovados.

### Fase 1 — Pesquisa comparativa

**Entrega:** relatório técnico, matriz comparativa e recomendação de pipeline V1 com alternativas.  
**Sucesso:** cada escolha é sustentada por fontes atuais; candidatos inviáveis são eliminados com justificativa; e qualquer validação experimental necessária é proposta separadamente antes de instalar ou executar ferramentas.

### Fase 2 — Prova de conceito

**Meta:** `video.mp4 → person.stl`.  
**Sucesso:** pessoa reconhecível, arquivo aberto no Bambu Studio e processo reproduzível ao menos manualmente. Mesmo nesta fase, comandos, versões, parâmetros, entradas e saídas devem ser registrados para que o resultado possa ser comparado.

### Fase 3 — Fidelidade

**Meta:** melhorar rosto, cabelo, corpo e roupas.  
**Sucesso:** ganho consistente em avaliações padronizadas, sem aumento inaceitável de artefatos.

### Fase 4 — Imprimibilidade

**Meta:** mesh fechada, robusta e adequada à FDM.  
**Sucesso:** impressão física concluída com detalhes essenciais preservados.

### Fase 5 — Base e escala

**Meta:** altura configurável e base opcional com texto.  
**Sucesso:** união/encaixe correto e dimensões verificadas.

### Fase 6 — Textura e referência de pintura

**Meta:** OBJ texturizado e vistas frontal, traseira, laterais e close do rosto.  
**Sucesso:** referências consistentes e úteis para pintura manual.

### Fase 7 — Automação e robustez

**Meta:** completar e endurecer orquestração, resume, execução parcial, diagnóstico e benchmarks.  
**Sucesso:** falhas recuperáveis, invalidação correta de etapas obsoletas, resultados rastreáveis e engines substituíveis. O registro mínimo necessário à reprodução começa na Fase 2; esta fase transforma esse mecanismo inicial em uma solução robusta.

### Fase 8 — Expansões futuras

- estilos artísticos;
- separação automática em peças e encaixes;
- 3MF e multicolorido;
- integração maior com o Bambu Studio;
- avaliação de uso comercial.

## 16. Pipeline V1 — ainda não decidido

O pipeline definitivo não deve ser preenchido por preferência ou suposição. A Fase 1 deverá entregar algo no formato:

```text
vídeos conforme protocolo aprovado
    → preparação com [ferramenta/estratégia escolhida]
    → reconstrução com [engine escolhida]
    → tratamento facial [se comprovadamente necessário]
    → processamento de mesh com [ferramentas escolhidas]
    → validação e escala
    → STL + OBJ/texturas
    → Bambu Studio
```

Cada escolha deverá incluir justificativa, consumo no Nitro, limitações, licença, alternativa de fallback e evidência de qualidade.

## 17. Próxima retomada

Ao voltar ao projeto:

1. Revisar este documento e corrigir escopo ou prioridades.
2. Responder às questões realmente bloqueadoras da seção 18.
3. Definir como a fidelidade será avaliada e quais dados reais poderão ser usados.
4. Iniciar pesquisa documental atualizada das tecnologias, sem instalar ferramentas nem implementar o pipeline.
5. Produzir matriz comparativa com fontes, requisitos e licenças.
6. Apresentar uma shortlist, o plano de validação e o pipeline recomendado V1 com alternativas.
7. Somente após aprovação, executar validações experimentais necessárias.
8. Aprovar os contratos iniciais e iniciar a prova de conceito.

## 18. Questões importantes para a próxima conversa

- Qual celular e quais modos de câmera estarão disponíveis?
- A pessoa poderá permanecer imóvel por quanto tempo?
- Há espaço para fundo controlado e iluminação uniforme?
- Qual tamanho de miniatura é prioritário para o primeiro teste?
- O primeiro objetivo exige corpo inteiro, busto ou ambos?
- É aceitável instalar WSL2 ou Linux se os testes indicarem vantagem clara?
- Existe disponibilidade para upgrade de RAM ou armazenamento, se comprovadamente necessário?
- Como será feita a avaliação de “reconhecível”: autor, pessoa retratada e/ou avaliadores externos?
- As imagens de teste podem permanecer apenas locais e privadas?

As quatro primeiras decisões que realmente condicionam a pesquisa são: celular/modos de captura disponíveis, corpo inteiro ou busto, tamanho prioritário da miniatura e aceitação de WSL2/Linux. As demais podem ser refinadas durante a Fase 1 sem bloquear seu início.

## 19. Resumo executivo

As únicas decisões arquiteturais assumidas neste momento são: processamento local, prioridade absoluta à fidelidade, modularidade por contratos, execução retomável e Bambu Studio manual no MVP. Engines, sistema operacional de execução, protocolo de captura e estratégia de rosto continuam deliberadamente abertos.

Os maiores riscos são movimento da pessoa, baixa qualidade facial em capturas corporais, conversão destrutiva para mesh, limites de 6 GB de VRAM/16 GB de RAM e incompatibilidade de ferramentas no Windows. A pesquisa deve medir esses riscos com os mesmos datasets e preservar todos os artefatos e parâmetros.

O próximo resultado esperado não é código: é uma recomendação técnica atualizada e testável para o pipeline V1.
