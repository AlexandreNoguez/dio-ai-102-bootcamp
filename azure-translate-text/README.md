# URL Page Translator (Markdown) — Azure AI Translator

Um utilitário em **Python** que recebe uma **URL**, extrai o conteúdo principal da página em **Markdown** e traduz o texto usando o **Azure AI Translator** (Text Translation v3).
Ideal para transformar artigos e documentação pública em `.md` traduzidos, prontos para ler, versionar no Git ou publicar.

## ✨ Recursos

* ✅ Extrai conteúdo “limpo” da página (remove menus/rodapés/lixo) e gera **Markdown**
* ✅ Inclui **metadados** no frontmatter (`source_url`, `target_lang`, `extracted_at_utc`)
* ✅ Tradução via **Azure AI Translator**
* ✅ Divide automaticamente em **chunks** para respeitar limites da API
* ✅ CLI simples e direta

## 📦 Requisitos

* Python **3.10+** (recomendado)
* Conta Azure com recurso **Translator** (Azure AI Translator)
* Dependências Python:

  * `requests`
  * `trafilatura`
  * `python-dotenv`

## 🚀 Instalação

### 1) Clonar o repositório

```bash
git clone http://github.com/AlexandreNoguez/azure-translate-text
cd azure-translate-text
```

### 2) Criar ambiente virtual (opcional, mas recomendado)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3) Instalar dependências

```bash
pip install -r requirements.txt
```

Se você ainda não tiver o `requirements.txt`, crie com:

```txt
requests
trafilatura
python-dotenv
```

## 🔑 Configuração (Azure)

Crie um arquivo `.env` na raiz do projeto com as variáveis abaixo:

```env
AZURE_TRANSLATOR_KEY=SEU_KEY
AZURE_TRANSLATOR_REGION=brazilsouth
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
```

**Onde encontrar:**

* `AZURE_TRANSLATOR_KEY`: chave do seu recurso Translator
* `AZURE_TRANSLATOR_REGION`: região do recurso (ex.: `brazilsouth`)
* `AZURE_TRANSLATOR_ENDPOINT`: endpoint do Translator (padrão acima ou seu custom domain)

> Dica: não versione seu `.env`. Adicione ao `.gitignore`.

## ▶️ Como usar

O script principal é `translate_page.py`.

### Tradução básica

```bash
python script.py --url "https://exemplo.com/artigo" --to pt
```

Isso vai gerar um arquivo `translated.pt.md` no diretório atual.

### Definir arquivo de saída

```bash
python translate_page.py --url "https://exemplo.com/artigo" --to pt --out artigo.pt.md
```

### Salvar também o Markdown original extraído

```bash
python translate_page.py --url "https://exemplo.com/artigo" --to pt --save-original
```
