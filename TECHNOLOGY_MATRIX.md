# MiniForge 3D — Matriz de Tecnologias

> **Status:** parcial — R1 preenchida  
> **Escala:** 1 (fraco/desfavorável) a 5 (forte/favorável)  
> **Regra:** `?` significa ausência de evidência suficiente; não significa nota baixa.

## 1. Matriz R1 — fotogrametria

As notas são provisórias e avaliam adequação arquitetural/documental. Qualidade com pessoas e consumo no Nitro só podem ser pontuados depois de validação controlada.

| Critério | Peso | COLMAP 4.0.4 | COLMAP + OpenMVS 2.4 | Meshroom 2025.1 |
|---|---:|---:|---:|---:|
| Preservação observacional da identidade | 5 | 4 | 4 | 4 |
| Fidelidade facial real | 5 | ? | ? | ? |
| Fidelidade corporal/roupas | 5 | ? | ? | ? |
| Qualidade geométrica humana | 5 | ? | ? | ? |
| Caminho até mesh | 5 | 4 | 5 | 4 |
| Textura | 3 | 4 | 5 | 4 |
| Windows | 4 | 5 | 4 | 5 |
| RTX 3050 6 GB | 4 | ? | ? | ? |
| 16 GB RAM | 4 | ? | ? | ? |
| CLI e automação | 3 | 5 | 5 | 4 |
| Artefatos intermediários | 3 | 5 | 5 | 5 |
| Modularidade | 3 | 5 | 5 | 4 |
| Maturidade/atividade | 4 | 5 | 4 | 4 |
| Licença favorável a evolução comercial | 3 | 5 | 2 | 4 |
| Facilidade de instalação | 1 | 4 | 3 | 5 |
| Complexidade operacional | 1 | 4 | 2 | 4 |

Não há total ponderado enquanto os critérios essenciais estiverem sem evidência.

## 2. Ficha resumida

| Tecnologia | Versão verificada | Plataforma | GPU | Saída relevante | Licença | Estado |
|---|---|---|---|---|---|---|
| COLMAP | 4.0.4 | Windows/Linux/macOS | CUDA suportado | câmeras, pontos, depth maps, mesh, textura | New BSD | baseline principal |
| OpenMVS | 2.4.0 | Windows/Linux/macOS | CUDA opcional | nuvem densa, mesh refinada e textura | AGPL-3.0 | segunda rota |
| Meshroom/AliceVision | 2025.1.0 / 3.3.0 | Windows/Linux | binário CUDA 12 | pipeline fotogramétrico e mesh texturizada | MPL-2.0 | controle independente |

## 3. Hipóteses que precisam de teste

| ID | Hipótese | Experimento futuro |
|---|---|---|
| H-R1-01 | COLMAP registra cobertura corporal completa com frames de vídeo bem selecionados | executar SfM e medir frames registrados/cobertura |
| H-R1-02 | 6 GB suportam dense stereo em resolução útil | escada de resolução com medição de VRAM |
| H-R1-03 | OpenMVS melhora completude/detalhe sobre o MVS do COLMAP | usar exatamente as mesmas câmeras e imagens |
| H-R1-04 | Meshroom produz baseline comparável com menos configuração | executar o mesmo dataset e comparar artefatos |
| H-R1-05 | Máscaras do fundo melhoram a pessoa sem remover features úteis | comparar com e sem máscaras |
| H-R1-06 | Close facial separado é necessário | comparar corpo apenas contra corpo + captura facial |
| H-R1-07 | Movimento da pessoa é o gargalo dominante | correlacionar artefatos com frames/movimentos observados |

## 4. Bloqueios atuais

- Nenhum dataset humano aprovado.
- Hardware do Nitro ainda não inventariado diretamente.
- Protocolo de captura ainda não definido.
- Famílias neural, Gaussian e humana/facial ainda não pesquisadas.
- Portanto, nenhuma engine está autorizada como escolha definitiva.

## 5. Próxima atualização

Adicionar R2: VGGT, DUSt3R, MASt3R e alternativas atuais. Depois, comparar se algum candidato neural deve substituir, complementar ou apenas diagnosticar a baseline de fotogrametria.
