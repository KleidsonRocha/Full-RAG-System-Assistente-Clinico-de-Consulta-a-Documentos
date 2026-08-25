# Regressao de configuracao RAG

- Status: aprovado
- Perguntas: 30
- Aprovacao automatica: 14/30 (46.7%)
- Recuperacao: 11/24 (45.8%)
- Geracao: 19/30 (63.3%)
- Recusa fora do acervo: 6/6 (100.0%)
- Context Recall@2: 56.2%
- Context Precision@2: 34.4%
- Hit Rate@2: 62.5%
- Hit Rate@5: 87.5%
- Hit Rate@10: 87.5%
- MRR@10: 0.646
- Latencia media: 14672 ms

## Como usar

Execute este arquivo em toda alteracao de configuracao do RAG:

```bash
python eval/regression.py
```

O comando roda o mesmo golden set versionado e falha com codigo 1 se alguma metrica cair abaixo do limite configurado.