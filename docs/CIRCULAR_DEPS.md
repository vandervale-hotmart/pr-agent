# Circular Dependency Checker

Esta ferramenta detecta automaticamente dependências circulares em configurações `application.yml` quando um PR é criado.

## Como Funciona

1. **Detecta mudanças** em arquivos `application.yml`/`application.yaml`
2. **Extrai URLs** de serviços externos (ex: `https://api-club-settings.buildstaging.com`)
3. **Verifica** se os serviços referenciados já dependem do repositório atual
4. **Comenta** no PR alertando sobre possíveis dependências circulares

## Exemplo de Uso

### Cenário
- Repositório: `api-club-content`
- PR adiciona configuração:
```yaml
services:
  clubsettings:
    url: https://api-club-settings.buildstaging.com
```

### Verificação
A ferramenta:
1. Identifica que `api-club-settings` está sendo referenciado
2. Verifica se `api-club-settings` já tem dependência para `api-club-content`
3. Se encontrar, posta comentário de aviso no PR

### Comentário Gerado
```markdown
## ⚠️ Circular Dependency Warning

This PR introduces dependencies to services that already depend on `api-club-content`:

**Potential circular dependencies detected:**
- `api-club-settings`

**Impact:**
- This may create circular dependencies between services
- Could cause deployment issues or runtime problems
- May affect service startup order

**Recommendation:**
Please review the architecture and consider:
1. Breaking the circular dependency through an intermediary service
2. Using event-driven communication instead of direct API calls
3. Refactoring to remove the bidirectional dependency
```

## Comandos CLI

```bash
# Verificar dependências circulares manualmente
python cli.py --pr_url=<PR_URL> circular_deps

# Ou usar o comando alternativo
python cli.py --pr_url=<PR_URL> check_circular_deps
```

## Configuração

Configure via variáveis de ambiente:

- `GITHUB_TOKEN`: Token para acessar API do GitHub

## Integração com GitHub Actions

### Opção 1: Workflow Reutilizável (Recomendado)

```yaml
name: PR Analysis with Circular Dependency Check

on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]

permissions:
  issues: write
  pull-requests: write
  contents: read

jobs:
  pr-analysis:
    if: github.event_name == 'pull_request' || (github.event_name == 'issue_comment' && contains(github.event.comment.body, '/review'))
    uses: vandervale-hotmart/pr-agent/.github/workflows/hotmart-pr-review.yaml@main
    with:
      pr_url: ${{ github.event.pull_request.html_url || github.event.issue.pull_request.html_url }}
    secrets:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
```

### Opção 2: Workflow Standalone

```yaml
name: PR Circular Dependency Check
on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - '**/application.yml'
      - '**/application.yaml'

jobs:
  circular-deps:
    runs-on: buildstaging
    steps:
    - uses: actions/checkout@v4
      with:
        repository: vandervale-hotmart/pr-agent
        ref: main
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - name: Check Circular Dependencies
      run: |
        python pr_agent/cli.py --pr_url=${{ github.event.pull_request.html_url }} circular_deps
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```