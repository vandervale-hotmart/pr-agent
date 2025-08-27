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

```yaml
name: PR Circular Dependency Check
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  circular-deps:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Check Circular Dependencies
      run: |
        python cli.py --pr_url=${{ github.event.pull_request.html_url }} circular_deps
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```