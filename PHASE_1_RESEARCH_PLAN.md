# MiniForge 3D — Plano da Fase 1: Pesquisa Comparativa

> **Status:** iniciado — planejamento da pesquisa  
> **Data de início:** 2026-08-08  
> **Implementação autorizada:** não  
> **Instalação e execução de engines:** somente depois da shortlist e da aprovação do plano de validação

## 1. Objetivo

Descobrir qual combinação de ferramentas open source e locais oferece a melhor chance de transformar capturas de celular de uma pessoa real em uma miniatura reconhecível e imprimível na Bambu Lab A1, usando prioritariamente o Acer Nitro V15 com RTX 3050 Laptop de 6 GB e 16 GB de RAM.

Ao fim desta fase, deve existir uma recomendação clara de **Pipeline V1**, com alternativas e limitações. Esta fase não cria o pipeline.

## 2. Perguntas que a pesquisa precisa responder

1. Qual protocolo de captura reduz problemas causados pelo movimento da pessoa?
2. Fotos, um vídeo ou vários vídeos oferecem o melhor equilíbrio entre cobertura e consistência?
3. Qual estratégia seleciona frames úteis sem manter imagens borradas ou redundantes?
4. Qual engine preserva melhor corpo, roupa, cabelo e identidade facial?
5. Fotogrametria clássica, reconstrução neural ou uma abordagem híbrida é mais adequada?
6. É necessário reconstruir o rosto separadamente e fundi-lo ao corpo?
7. Qual rota produz uma mesh utilizável, não apenas uma visualização ou Gaussian Splat?
8. Quais ferramentas executam de forma estável com 6 GB de VRAM e 16 GB de RAM?
9. Windows nativo é suficiente ou WSL2/Linux traz vantagem necessária?
10. Como tornar a mesh watertight sem destruir rosto, mãos e acessórios?
11. Qual nível de detalhe sobrevive à impressão FDM em 100, 150 e 200 mm?
12. Quais licenças permitem uso pessoal hoje e não bloqueiam uma possível evolução comercial?

## 3. Entregas da fase

- `TECHNOLOGY_RESEARCH.md`: levantamento com fontes e data de verificação.
- `TECHNOLOGY_MATRIX.md`: comparação normalizada dos candidatos.
- `CAPTURE_RESEARCH.md`: protocolo de captura proposto e variações a testar.
- `VALIDATION_PLAN.md`: instalações e experimentos controlados sugeridos.
- `PIPELINE_V1_RECOMMENDATION.md`: rota recomendada, alternativas e justificativas.

Esses arquivos serão criados progressivamente. A existência da lista não significa que todas as entregas já estejam prontas.

## 4. Ordem da pesquisa

### R1 — Reconstrução de referência

Investigar primeiro rotas de reconstrução multi-view que preservem observações reais:

- COLMAP;
- OpenMVS;
- AliceVision/Meshroom;
- outras alternativas atuais encontradas durante a pesquisa.

Objetivo: estabelecer uma baseline de fotogrametria antes de avaliar métodos que possam inventar geometria.

### R2 — Reconstrução neural e geometria visual

Investigar:

- VGGT e sua evolução atual;
- DUSt3R;
- MASt3R;
- outros métodos multi-view atuais com código e pesos disponíveis.

Objetivo: descobrir se melhoram poses, profundidade, regiões difíceis ou velocidade sem reduzir a fidelidade.

### R3 — Gaussian Splatting e extração de mesh

Investigar:

- implementações de 3D Gaussian Splatting;
- SuGaR;
- métodos atuais de Gaussian/NeRF para mesh;
- qualidade e custo da conversão para superfície imprimível.

Objetivo: separar qualidade de renderização de qualidade geométrica. Uma cena visualmente boa não é suficiente se não produzir mesh adequada.

### R4 — Reconstrução humana e facial

Investigar:

- reconstrução humana multi-view;
- modelos paramétricos de corpo e cabeça;
- reconstrução facial dedicada;
- alinhamento e fusão de rosto/corpo;
- tratamento de cabelo, mãos, roupas e acessórios.

Objetivo: avaliar ganho de identidade sem substituir a pessoa por um humano genérico.

### R5 — Geração 3D como ferramenta auxiliar

Investigar, sem assumir adoção:

- Hunyuan3D;
- TRELLIS;
- InstantMesh;
- alternativas atuais.

Objetivo: avaliar preenchimento ou reparo de regiões incompletas. Candidatos que alterem a identidade devem ser rejeitados para a rota principal.

### R6 — Mesh e preparação para impressão

Investigar:

- Blender e Blender Python API;
- Open3D;
- Trimesh;
- MeshLab;
- ferramentas de validação e reparo atuais.

Objetivo: definir a menor sequência destrutiva capaz de produzir um STL válido.

## 5. Matriz de candidatos inicial

Esta tabela é apenas a fila da pesquisa. Nenhuma tecnologia está aprovada.

| Família | Candidato inicial | Papel possível | Estado |
|---|---|---|---|
| SfM/MVS | COLMAP | poses, nuvem densa e baseline | a pesquisar |
| MVS | OpenMVS | densificação, mesh e textura | a pesquisar |
| Fotogrametria | AliceVision/Meshroom | pipeline de referência alternativo | a pesquisar |
| Neural multi-view | VGGT/família atual | câmeras, profundidade e pontos | a pesquisar |
| Neural multi-view | DUSt3R | geometria e correspondências | a pesquisar |
| Neural multi-view | MASt3R | correspondências e reconstrução | a pesquisar |
| Gaussian → mesh | SuGaR/família atual | superfície a partir de splats | a pesquisar |
| Generativo | Hunyuan3D | reparo/alternativa experimental | a pesquisar |
| Generativo | TRELLIS | reparo/alternativa experimental | a pesquisar |
| Generativo | InstantMesh | reparo/alternativa experimental | a pesquisar |
| Mesh | Blender | limpeza e automação | a pesquisar |
| Mesh | Open3D | análise e operações geométricas | a pesquisar |
| Mesh | Trimesh | validação e conversão | a pesquisar |
| Mesh | MeshLab | reparo e inspeção | a pesquisar |

Novos candidatos podem entrar se apresentarem evidência melhor. Popularidade isolada não será critério de inclusão.

## 6. Ficha obrigatória por tecnologia

Cada candidato deverá registrar:

- nome, versão/release e data da verificação;
- repositório e documentação oficiais;
- finalidade real da ferramenta;
- entradas e saídas;
- geração de mesh e textura;
- suporte a CLI/automação;
- sistema operacional suportado;
- GPU, CUDA, VRAM, RAM e disco;
- possibilidade oficial de low-VRAM, offload, tiling ou precisão reduzida;
- qualidade demonstrada com pessoas reais;
- comportamento esperado diante de movimento;
- riscos de alteração da identidade;
- maturidade, atividade e problemas conhecidos;
- licença do código;
- licença dos pesos/modelos;
- restrições de uso e redistribuição;
- evidências contrárias ou limitações encontradas;
- decisão provisória: manter, manter como alternativa ou eliminar.

## 7. Regras de evidência

Prioridade das fontes:

1. documentação e repositório oficial;
2. artigo científico e material dos autores;
3. releases e issues reproduzíveis;
4. benchmarks independentes com configuração declarada;
5. relatos da comunidade apenas como indício a confirmar.

Toda afirmação instável deve ter fonte e data. Demonstrações escolhidas pelos autores não bastam para concluir qualidade com pessoas ou adequação para impressão.

## 8. Critérios de eliminação precoce

Um candidato pode ser eliminado da rota principal quando:

- não produz nem permite converter para uma mesh com qualidade verificável;
- exige nuvem ou serviço pago;
- não possui código/pesos disponíveis para execução local;
- a licença é incompatível com o uso pretendido;
- depende de hardware muito superior sem opção estável de redução/offload;
- gera uma pessoa plausível, mas não preserva a identidade observada;
- está abandonado e não possui instalação reproduzível ou alternativa mantida;
- a integração exige fragilidade desproporcional ao ganho esperado.

Uma tecnologia eliminada da rota principal ainda pode permanecer registrada como referência ou alternativa futura.

## 9. Pontuação comparativa

Escala inicial: 1 a 5, sempre acompanhada por evidência e nível de confiança.

| Critério | Peso provisório |
|---|---:|
| Identidade facial | 5 |
| Fidelidade corporal/roupas | 5 |
| Qualidade geométrica | 5 |
| Conversão para mesh imprimível | 5 |
| Estabilidade/reprodutibilidade | 4 |
| Compatibilidade com o Nitro | 4 |
| Preservação de textura | 3 |
| Integração modular/CLI | 3 |
| Licença | 3 |
| Tempo de processamento | 1 |
| Facilidade de instalação | 1 |

Os pesos são provisórios. Uma pontuação total não deve esconder um bloqueio: candidato incapaz de preservar identidade ou gerar mesh não pode vencer apenas por ser rápido.

## 10. Gate antes de qualquer instalação

Antes de baixar pesos, compilar ou instalar engines, apresentar:

- shortlist de no máximo três rotas principais;
- justificativa de cada rota;
- espaço em disco estimado;
- requisitos de VRAM/RAM;
- ambiente proposto: Windows, WSL2 ou Linux;
- arquivos que serão baixados;
- licenças relevantes;
- experimento mínimo e critério de parada;
- estratégia para desfazer/remover o ambiente experimental.

Somente depois da aprovação desse gate começa a validação experimental.

## 11. Plano preliminar de validação

Ainda não autorizado para execução:

1. Inventariar o hardware e software do Nitro.
2. Definir um pequeno dataset de captura sem informação sensível desnecessária.
3. Preservar os arquivos originais e seus checksums.
4. Rodar cada rota com a mesma entrada e registrar parâmetros.
5. Gerar vistas padronizadas da reconstrução.
6. Medir VRAM, RAM, tempo, disco e falhas.
7. Inspecionar face, silhueta, mãos, cabelo, roupa e regiões ausentes.
8. Converter para mesh sem reparo e preservar esse original.
9. Aplicar reparo mínimo e comparar a perda de detalhes.
10. Abrir o STL no Bambu Studio e registrar alertas.

## 12. Gate para iniciar o MVP

O MVP só poderá começar quando existirem:

- protocolo de captura provisório;
- engine principal e fallback escolhidos;
- evidência de que a rota cabe no hardware ou possui adaptação estável;
- formato de intercâmbio definido;
- riscos e licenças registrados;
- critérios de sucesso aprovados;
- plano de ambiente e dependências;
- autorização explícita para implementar.

## 13. Próxima ação da pesquisa

Criar `TECHNOLOGY_RESEARCH.md` e iniciar R1 pelas rotas de fotogrametria/SfM/MVS. Para cada uma, verificar primeiro documentação oficial, suporte atual ao Windows/CUDA, formatos de saída, requisitos de hardware e licença. Nenhuma instalação faz parte dessa próxima ação.
