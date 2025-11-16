# .github/workflows/update-readme.py
import os
import re
from datetime import datetime
import pytz
from PIL import Image # NECESSÁRIO INSTALAR: pip install Pillow

# Caminho base: raiz do repositório
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# ===== Configuração do destino =====
README_DIR = os.getenv("README_OUTPUT_DIR", BASE_DIR)
os.makedirs(README_DIR, exist_ok=True)

README_FILE = os.path.join(README_DIR, "README.md")
VERSAO_FILE = os.path.join(README_DIR, "versao.txt")

DOCS_DIR = os.path.join(BASE_DIR, "documentos")
os.makedirs(DOCS_DIR, exist_ok=True)

IMAGENS_DIR = os.path.join(BASE_DIR, "imagens")
IMAGEM_EXTENSOES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp", ".tiff"}

DOCS_REPOS_FILE = os.path.join(DOCS_DIR, "repositorios.md")

# LIMITE MÁXIMO DE LARGURA PARA REDIMENSIONAMENTO (800px)
MAX_LARGURA = 800

# Extensões e diretórios que devem ser ocultados na árvore
OCULTA_EXT = {".yml", ".py", ".git", ".webp"}
OCULTA_DIR = {
    ".git",
    ".github",
    ".gitignore",
    ".env",
    ".env.local",
    "Facebook",
    "Instagram",
    "Linkedin",
    "Twitter",
    "cache",
}

FUSO_HORARIO_BRASIL = pytz.timezone("America/Sao_Paulo")

# -------------------- Versão --------------------
def ler_versao():
    if not os.path.exists(VERSAO_FILE):
        return None
    try:
        with open(VERSAO_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        return None

def salvar_versao(valor: int) -> int:
    with open(VERSAO_FILE, "w", encoding="utf-8") as f:
        f.write(str(valor))
    return valor

def obter_data_hora_brasilia() -> str:
    agora = datetime.now(FUSO_HORARIO_BRASIL)
    return agora.strftime("%d/%m/%Y %H:%M:%S")

# -------------------- Processamento de Imagens --------------------
def redimensionar_imagem_se_necessario(caminho_imagem: str, max_largura: int):
    """
    Redimensiona a imagem se sua largura for maior que max_largura, 
    mantendo a proporção original. Substitui o arquivo original.
    """
    try:
        with Image.open(caminho_imagem) as img:
            largura, altura = img.size
            
            if largura > max_largura:
                nova_altura = int((max_largura / largura) * altura)
                nova_dimensao = (max_largura, nova_altura)
                
                img = img.resize(nova_dimensao, Image.Resampling.LANCZOS)
                
                img.save(caminho_imagem, quality=90, optimize=True)

                print(f"Redimensionado: {os.path.basename(caminho_imagem)} de {largura}px para {max_largura}px.")
                return True
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {caminho_imagem}")
    except Exception as e:
        print(f"Erro ao processar a imagem {os.path.basename(caminho_imagem)}: {e}")
    return False

def coletar_imagens(path_dir: str) -> list[str]:
    """
    Lista todos os arquivos de imagem na pasta 'imagens/', ignorando arquivos ocultos,
    e redimensiona-os se necessário.
    """
    if not os.path.exists(path_dir) or not os.path.isdir(path_dir):
        return []

    imagens = []
    try:
        for item in os.listdir(path_dir):
            # Filtro: Ignora arquivos ocultos ou de cache do sistema (começam com '.')
            if item.startswith('.'):
                continue
            
            caminho_item = os.path.join(path_dir, item)
            
            if os.path.isfile(caminho_item):
                ext = os.path.splitext(item)[1].lower()
                
                if ext in IMAGEM_EXTENSOES:
                    redimensionar_imagem_se_necessario(caminho_item, MAX_LARGURA)
                    imagens.append(item)
                    
    except (FileNotFoundError, PermissionError):
        pass

    return sorted(imagens)

def montar_tabela_imagens(imagens: list[str]) -> str:
    """
    Gera a seção de demonstração em formato de tabela (2 colunas) para o README.md.
    Cada imagem é exibida UMA ÚNICA VEZ com largura de 400px.
    A numeração da tela é embutida na célula para estabilidade da formatação.
    """
    if not imagens:
        return ""

    linhas = []
    num_imagens = len(imagens)
    
    linhas.append("## 🖼️ Imagens do Projeto\n")
    linhas.append(f"Aqui estão **{num_imagens}** telas do **Porto Seguro da Sorte** contidas na pasta `imagens/`:\n")

    colunas = 2
    
    # 1. CABEÇALHO DA TABELA (Texto descritivo)
    cabecalho_descritivo = ["Demonstração"] * colunas
    linhas.append(f"| {' | '.join(cabecalho_descritivo)} |")
    
    # 2. SEPARADOR DO CABEÇALHO
    linhas.append(f"|{'---|' * colunas}")

    # Itera sobre a lista de 2 em 2
    for i in range(0, num_imagens, colunas):
        row_imagens = imagens[i : i + colunas]
        
        # --- LINHA ÚNICA: IMAGENS + NUMERAÇÃO (Tags <img>) ---
        img_tags = []
        for j, nome_imagem in enumerate(row_imagens):
            indice = i + j + 1
            caminho_relativo = f"./imagens/{nome_imagem}"
            
            # Formato Estável: Numeração e imagem na mesma célula
            img_tags.append(f'**Tela {indice}**<br><img src="{caminho_relativo}" alt="Tela {indice}" width="400"/>')
            
        # Preenche com colunas vazias se a última linha não for completa
        while len(img_tags) < colunas:
            img_tags.append(" ") 
            
        # Adiciona a linha ao conteúdo da tabela
        linhas.append(f"| {' | '.join(img_tags)} |")
        
    linhas.append("\n---\n") # Separador após a seção
    return "\n".join(linhas)

# -------------------- Utilitários --------------------
URL_LINE_RE = re.compile(r"^\s*URL\s*=\s*(?P<url>.+?)\s*$", re.IGNORECASE)

def gerar_arvore(path, ignorar=None, prefixo="", is_root=True, nome_raiz=None):
    ignorar = set(ignorar) if ignorar else set()
    linhas = []

    if is_root:
        if nome_raiz is None:
            nome_raiz = os.path.basename(os.path.normpath(path)) or "."
        linhas.append(f"📂 {nome_raiz}")

    try:
        itens = sorted(os.listdir(path))
    except (FileNotFoundError, PermissionError) as e:
        return f"{prefixo}[Erro ao acessar {path}: {e}]"

    itens_filtrados = []
    for item in itens:
        if item in ignorar:
            continue
        caminho_item = os.path.join(path, item)
        if os.path.isdir(caminho_item):
            itens_filtrados.append(item)
        else:
            ext = os.path.splitext(item)[1].lower()
            if ext not in OCULTA_EXT:
                itens_filtrados.append(item)

    total = len(itens_filtrados)
    for i, item in enumerate(itens_filtrados):
        caminho_item = os.path.join(path, item)
        ultimo = i == total - 1
        ponteiro = "└── " if ultimo else "├── "

        if os.path.isdir(caminho_item):
            try:
                conteudo_dir = [
                    f
                    for f in os.listdir(caminho_item)
                    if f not in ignorar
                    and (
                        os.path.isdir(os.path.join(caminho_item, f))
                        or os.path.splitext(f)[1].lower() not in OCULTA_EXT
                    )
                ]
            except (FileNotFoundError, PermissionError):
                conteudo_dir = []

            emoji = "📂" if conteudo_dir else "🗂️"
            linhas.append(f"{prefixo}{ponteiro}{emoji} {item}")

            if conteudo_dir:
                novo_prefixo = prefixo + ("    " if ultimo else "│   ")
                subarvore = gerar_arvore(
                    caminho_item, ignorar, novo_prefixo, is_root=False
                )
                linhas.append(subarvore)
        else:
            linhas.append(f"{prefixo}{ponteiro}📄 {item}")

    return "\n".join(linhas)


def ler_url_de_arquivo(path_url: str) -> str | None:
    """Lê o conteúdo de um .url (formato InternetShortcut) e retorna o valor após 'URL='."""
    try:
        with open(path_url, "r", encoding="utf-8") as f:
            for line in f:
                m = URL_LINE_RE.match(line)
                if m:
                    return m.group("url").strip()
    except OSError:
        return None
    return None

def ler_descricao_sidecar(stem: str) -> str:
    """
    Busca descrição em arquivos 'stem.desc.md' ou 'stem.desc.txt' dentro de documentos/.
    """
    candidatos = [
        os.path.join(DOCS_DIR, f"{stem}.desc.md"),
        os.path.join(DOCS_DIR, f"{stem}.desc.txt"),
    ]
    for arq in candidatos:
        if os.path.exists(arq):
            try:
                with open(arq, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except OSError:
                pass
    return ""

def extrair_equipe_projeto_do_nome(stem: str) -> tuple[str, str]:
    """
    Extrai Equipe e Projeto do nome do arquivo.
    """
    m = re.match(r"^\s*(Equipe\s+\d+)\s*[-—]\s*(.+)\s*$", stem, flags=re.IGNORECASE)
    if m:
        equipe = m.group(1).strip().title()
        projeto = m.group(2).strip()
        return (equipe, projeto)
    return ("", stem.strip())

def coletar_repositorios_de_documentos() -> list[dict]:
    """
    Vasculha 'documentos/' por arquivos .url e monta a lista de repositórios.
    """
    repos = []
    try:
        for item in sorted(os.listdir(DOCS_DIR)):
            path = os.path.join(DOCS_DIR, item)
            if not os.path.isfile(path):
                continue
            name, ext = os.path.splitext(item)
            if ext.lower() != ".url":
                continue

            url = ler_url_de_arquivo(path)
            if not url:
                continue

            equipe, projeto = extrair_equipe_projeto_do_nome(name)
            descricao = ler_descricao_sidecar(name)

            repos.append(
                {
                    "equipe": equipe,
                    "projeto": projeto,
                    "descricao": descricao,
                    "url": url,
                    "slug": name,
                }
            )
    except FileNotFoundError:
        pass

    repos.sort(key=lambda r: (r["equipe"] or "ZZZ", r["projeto"].lower()))
    return repos

# -------------------- Sumário (README) e página em documentos --------------------
def montar_tabela_repositorios(repos: list[dict]) -> str:
    """
    Gera markdown da seção de sumário de repositórios.
    """
    linhas = []
    linhas.append("## 📚 Sumário dos Repositórios Técnicos\n")
    linhas.append("> *Gerado automaticamente a partir de arquivos `.url` em `./documentos/`. ")
    linhas.append("Cada `.url` deve conter uma linha `URL=...`. ")
    linhas.append("O nome do arquivo define as colunas, ex.: `Equipe 0X - Campo Inteligente – Back-End.url`.*\n")
    linhas.append("")
    linhas.append("| Equipe | Projeto | Descrição | Repositório |")
    linhas.append("|:-------|:--------|:----------|:------------|")

    if not repos:
        linhas.append("| — | — | — | — |")
        return "\n".join(linhas) + "\n"

    for r in repos:
        equipe = f"**{r['equipe']}**" if r["equipe"] else "—"
        projeto = r["projeto"] if r["projeto"] else r["slug"]
        desc = (r["descricao"] or "—").replace("\n", " ").strip()
        linhas.append(f"| {equipe} | {projeto} | {desc} | [{r['slug']}]({r['url']}) |")

    linhas.append("")
    return "\n".join(linhas)

def salvar_repositorios_em_documentos(repos: list[dict], destino_md: str):
    """
    Gera 'documentos/repositorios.md' com a mesma lógica.
    """
    linhas = []
    linhas.append("# 📚 Repositórios Técnicos — Links Externos\n")
    linhas.append("_Fonte: arquivos `.url` dentro de `./documentos/`._\n")
    if not repos:
        linhas.append("> Nenhum arquivo `.url` encontrado em `./documentos/`.\n")
    else:
        for r in repos:
            equipe = (r["equipe"] + " — ") if r["equipe"] else ""
            titulo = f"{equipe}{r['projeto'] or r['slug']}"
            linhas.append(f"- **{titulo}**")
            if r["descricao"]:
                linhas.append(f"  - {r['descricao'].strip()}")
            linhas.append(f"  - Repositório: <{r['url']}>")
            linhas.append("")

    with open(destino_md, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas).rstrip() + "\n")

# -------------------- README --------------------
def atualizar_readme():
    """
    Incrementa a versão e coordena a geração do README e repositorios.md.
    """
    versao_atual = ler_versao()
    if versao_atual is None:
        nova_versao = salvar_versao(1)
    else:
        nova_versao = salvar_versao(versao_atual + 1)

    data_hora = obter_data_hora_brasilia()

    # 1) Coleta repositórios
    repos = coletar_repositorios_de_documentos()
    
    # 2) Coleta e REDIMENSIONA imagens
    imagens = coletar_imagens(IMAGENS_DIR) 

    # 3) Gera/atualiza documentos/repositorios.md
    salvar_repositorios_em_documentos(repos, DOCS_REPOS_FILE)

    # 4) Atualiza README
    gerar_readme(nova_versao, data_hora, repos, imagens)

def gerar_readme(versao, data_hora, repos_from_docs, imagens_from_dir):
    with open(README_FILE, "w", encoding="utf-8") as readme:
        # Seção 1: Cabeçalho e Informações Básicas
        readme.write("# Bem-vindo ao 🍀**Porto Seguro da Sorte**\n\n")
        readme.write(
            "O Porto Seguro da Sorte é uma plataforma digital voltada para a organização e participação em rifas online,"
            " oferecendo uma experiência prática e segura tanto para quem cria quanto para quem participa. "
            "Com integração via WhatsApp, o sistema permite o gerenciamento completo das rifas, "
            "desde a criação até o sorteio, com notificações automáticas, controle de pagamentos e emissão de comprovantes."
            " A navegação é intuitiva, com foco na acessibilidade e na transparência dos processos.\n\n"
        )

        readme.write("## ℹ️ Importante \n\n")
        readme.write("ESTE README É ATUALIZADO AUTOMATICAMENTE A CADA COMMIT NA MAIN \n\n")
        readme.write("```\n")
        readme.write(f"Repositório..........: Portifólio\n")
        readme.write(f"Sistema..............: Porto Seguro da Sorte\n")
        readme.write(f"Versão...............: {versao} (AUTO-INCREMENTO)\n")
        readme.write(f"Data de Atualização..: {data_hora}\n")
        readme.write(f"Responsável..........: Marcos Morais\n")
        readme.write("```\n")

        # Seção 2: Participantes
        readme.write("## 👥 Participantes\n\n")
        readme.write("<table style='width:100%'>\n")
        readme.write("<thead><tr>")
        readme.write("<th style='text-align:left'>Nome</th>")
        readme.write("<th style='text-align:left'>Função</th>")
        readme.write("<th style='text-align:left'>Contato</th>")
        readme.write("</tr></thead>\n")
        readme.write("<tbody>\n")
        readme.write(
            "<tr><td>MARCOS MORAIS DE SOUSA            </td><td>Gerente de Projetos      </td><td><a href='https://www.linkedin.com/in/marcosmoraisjr/'    >LinkedIn</a> | <a href='mailto:mmstec@gmail.com'>Email</a></td></tr>\n"
        )
        readme.write(
            "<tr><td>VINICIUS ANDRADE                </td><td>Scrum Master             </td><td><a href='https://www.linkedin.com/in/andrade/'           >LinkedIn</a> | <a href='mailto:vinigta30@gmail.com'>Email</a></td></tr>\n"
        )
        readme.write(
            "<tr><td>DIMITRI M. REIS DE SOUSA          </td><td>Full Stack Web Developer </td><td><a href='https://www.linkedin.com/in/dimitrimrs/'        >LinkedIn</a> | <a href='mailto:dimitrimrs@gmail.com'>Email</a></td></tr>\n"
        )
        readme.write("</tbody>\n</table>\n\n")

        # Seção 3: Tecnologias
        readme.write("## 🧩 Tecnologias Utilizadas\n\n")
        readme.write("<p align='left'>\n")
        readme.write("  <img src='https://img.shields.io/badge/Figma-F24E1E?logo=figma&logoColor=white' alt='Figma' />\n")
        readme.write("  <img src='https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white&style=flat' alt='GitHub' />\n")
        readme.write("  <img src='https://img.shields.io/badge/PostgreSQL-13+-4169E1?logo=postgresql&logoColor=white' alt='PostgreSQL' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white' alt='Python' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Uvicorn-ASGI-121212?logo=fastapi&logoColor=white' alt='Uvicorn' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Daphne-ASGI-11B5AF?logoColor=white' alt='Daphne' />\n")
        readme.write("  <img src='https://img.shields.io/badge/drf--yasg-Swagger_Integration-6DB33F?logo=swagger&logoColor=white' alt='drf-yasg' />\n")
        readme.write("</p>\n\n")

        # Seção 4: Sumário dos Repositórios
        readme.write(montar_tabela_repositorios(repos_from_docs))
        readme.write("\n")
        readme.write(
            f"🔗 Consulte também: [`documentos/{os.path.basename(DOCS_REPOS_FILE)}`](./documentos/{os.path.basename(DOCS_REPOS_FILE)}) para a lista de links externos.\n\n"
        )

        # Seção 5: Documentos
        readme.write("## 📂 Documentos\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore(DOCS_DIR, OCULTA_DIR))
        readme.write("\n```\n")

        # Seção 6: Estrutura do Repositório
        readme.write("## 🌳 Estrutura do Repositório\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore(BASE_DIR, OCULTA_DIR))
        readme.write("\n```\n")

        # Seção 7: IMAGENS DO PROJETO (Tabela Corrigida e Estável)
        readme.write(montar_tabela_imagens(imagens_from_dir))

        # Seção 8: Licença
        readme.write("## 📜 Licença\n\n")
        readme.write("Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).\n\n")

        # Seção 9: Agradecimentos
        readme.write("## 🤝 Agradecimentos\n\n")
        readme.write("Contribuições, sugestões e feedbacks são muito bem-vindos! Caso tenha algum comentário ou queira contribuir com o projeto, sinta-se à vontade para abrir uma issue ou enviar um pull request.\n\n")
        readme.write("--- \n\n")
        readme.write("Desenvolvido com ❤️ pela de [Marcos Morais](https://www.linkedin.com/in/marcosmoraisjr/) \n\n")

# -------------------- Main --------------------
if __name__ == "__main__":
    try:
        atualizar_readme()
    except ImportError:
        # Este erro será capturado se a instalação no YAML falhar
        print("Erro: A biblioteca Pillow (PIL) não está instalada. Execute 'pip install Pillow' para habilitar o redimensionamento de imagens.")
    except Exception as e:
        print(f"Ocorreu um erro durante a atualização do README: {e}")
