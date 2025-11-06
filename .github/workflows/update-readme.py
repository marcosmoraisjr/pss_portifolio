
# .github/workflows/update-readme.py
import os
from datetime import datetime
import pytz

# Caminho base: raiz do repositório (2 níveis acima, pois o script está em .github/workflows)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# ===== Configuração do destino =====
# Pasta onde README.md e versao.txt serão gravados.
# - Padrão: raiz do repositório (BASE_DIR).
# - Para customizar (ex.: no GitHub Actions), defina a env README_OUTPUT_DIR.
README_DIR = os.getenv("README_OUTPUT_DIR", BASE_DIR)

# Garante que o diretório de saída exista
os.makedirs(README_DIR, exist_ok=True)

# Caminhos do README e do arquivo de versão (sempre na MESMA pasta)
README_FILE = os.path.join(README_DIR, "README.md")
VERSAO_FILE = os.path.join(README_DIR, "versao.txt")

# Diretório de documentos (opcional; usado para listar arquivos na seção "Documentos")
DOCS_DIR = os.path.join(BASE_DIR, "documentos")
os.makedirs(DOCS_DIR, exist_ok=True)

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

# Fuso horário para data/hora
FUSO_HORARIO_BRASIL = pytz.timezone("America/Sao_Paulo")


# -------------------- Versão --------------------


def ler_versao():
    """Lê a versão atual do versao.txt. Retorna int ou None se não existir/for inválido."""
    if not os.path.exists(VERSAO_FILE):
        return None
    try:
        with open(VERSAO_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        return None


def salvar_versao(valor: int) -> int:
    """Persiste a versão informada e retorna o valor salvo."""
    with open(VERSAO_FILE, "w", encoding="utf-8") as f:
        f.write(str(valor))
    return valor


def obter_data_hora_brasilia() -> str:
    agora = datetime.now(FUSO_HORARIO_BRASIL)
    return agora.strftime("%d/%m/%Y %H:%M:%S")


# -------------------- Árvore de diretórios --------------------


def gerar_arvore(path, ignorar=None, prefixo="", is_root=True, nome_raiz=None):
    """Gera uma árvore de diretórios/arquivos com emojis, ocultando extensões e pastas especificadas."""
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
                novo_prefixo = prefixo + ("    " if ultimo else "│   ")
                subarvore = gerar_arvore(
                    caminho_item, ignorar, novo_prefixo, is_root=False
                )
                linhas.append(subarvore)
        else:
            linhas.append(f"{prefixo}{ponteiro}📄 {item}")

    return "\n".join(linhas)


# -------------------- README --------------------


def atualizar_readme():
    """
    Regras de versão:
    - Se não existir versao.txt -> salva 1 (primeira execução, sem auto-incremento).
    - Se existir -> incrementa +1.
    """
    versao_atual = ler_versao()
    if versao_atual is None:
        nova_versao = salvar_versao(1)  # primeira execução -> 1
    else:
        nova_versao = salvar_versao(versao_atual + 1)  # execuções seguintes -> +1

    data_hora = obter_data_hora_brasilia()
    gerar_readme(nova_versao, data_hora)


def gerar_readme(versao, data_hora):
    """Gera o README.md diretamente no destino (README_DIR)."""
    with open(README_FILE, "w", encoding="utf-8") as readme:
        readme.write("# Bem-vindo ao 🍀**Porto Seguro da Sorte**\n\n")
        readme.write(
            "O Porto Seguro da Sorte é uma plataforma digital voltada para a organização e participação em rifas online,"
            " oferecendo uma experiência prática e segura tanto para quem cria quanto para quem participa. "
            "Com integração via WhatsApp, o sistema permite o gerenciamento completo das rifas, "
            "desde a criação até o sorteio, com notificações automáticas, controle de pagamentos e emissão de comprovantes."
            " A navegação é intuitiva, com foco na acessibilidade e na transparência dos processos.\n\n"
        )

        readme.write("## ℹ️ Importante \n\n")
        readme.write(
            "ESTE README É ATUALIZADO AUTOMATICAMENTE A CADA COMMIT NA MAIN \n\n"
        )
        readme.write("```\n")
        readme.write(f"Repositório..........: BACK-END\n")
        readme.write(f"Sistema..............: Porto Seguro da Sorte\n")
        readme.write(f"Versão...............: {versao} (AUTO-INCREMENTO)\n")
        readme.write(f"Data de Atualização..: {data_hora}\n")
        readme.write(f"Responsável..........: Marcos Morais\n")
        readme.write("```\n")

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
            "<tr><td>VINICIUS ANDRADE                  </td><td>Scrum Master             </td><td><a href='https://www.linkedin.com/in/andrade/'           >LinkedIn</a> | <a href='mailto:vinigta30@gmail.com'>Email</a></td></tr>\n"
        )
        readme.write(
            "<tr><td>DIMITRI M. REIS DE SOUSA          </td><td>Full Stack Web Developer </td><td><a href='https://www.linkedin.com/in/dimitrimrs/'        >LinkedIn</a> | <a href='mailto:dimitrimrs@gmail.com'>Email</a></td></tr>\n"
        )
        readme.write("</tbody>\n</table>\n\n")

        readme.write("## 🧩 Tecnologias Utilizadas\n\n")
        readme.write("<p align='left'>\n")
        readme.write(
            "  <img src='https://img.shields.io/badge/Figma-F24E1E?logo=figma&logoColor=white' alt='Figma' />\n"
        )
        readme.write(
            "  <img src='https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white&style=flat' alt='GitHub' />\n"
        )
        readme.write(
            "  <img src='https://img.shields.io/badge/PostgreSQL-13+-4169E1?logo=postgresql&logoColor=white' alt='PostgreSQL' />\n"
        )
        readme.write(
            "  <img src='https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white' alt='Python' />\n"
        )
        readme.write(
            "  <img src='https://img.shields.io/badge/Uvicorn-ASGI-121212?logo=fastapi&logoColor=white' alt='Uvicorn' />\n"
        )
        readme.write(
            "  <img src='https://img.shields.io/badge/Daphne-ASGI-11B5AF?logoColor=white' alt='Daphne' />\n"
        )
        readme.write(
            "  <img src='https://img.shields.io/badge/drf--yasg-Swagger_Integration-6DB33F?logo=swagger&logoColor=white' alt='drf-yasg' />\n"
        )
        readme.write("</p>\n\n")

        readme.write("## 📂 Documentos\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore(DOCS_DIR, OCULTA_DIR))
        readme.write("\n```\n")

        readme.write("## 🌳 Estrutura do Repositório\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore(BASE_DIR, OCULTA_DIR))
        readme.write("\n```\n")

        readme.write("## 📜 Licença\n\n")
        readme.write(
            "Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).\n\n"
        )

        readme.write("## 🤝 Agradecimentos\n\n")
        readme.write(
            "Contribuições, sugestões e feedbacks são muito bem-vindos! Caso tenha algum comentário ou queira contribuir com o projeto, sinta-se à vontade para abrir uma issue ou enviar um pull request.\n\n"
        )
        readme.write("--- \n\n")
        readme.write(
            "Desenvolvido com ❤️ pela equipe de [Marcos Morais](https://www.linkedin.com/in/marcosmoraisjr/) \n\n"
        )


if __name__ == "__main__":
    atualizar_readme()
