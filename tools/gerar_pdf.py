"""Gera o PDF de entrega do mini-projeto a partir de docs/MINI_PROJETO.md.

Uso:  python tools/gerar_pdf.py
Converte o Markdown para HTML (conversor próprio, sem dependências) e imprime
em PDF A4 com o Chrome/Edge em modo headless.

Os dados pessoais da capa (aluno, RA, professora) ficam só na máquina, em
entrega/dados_capa.json, e o PDF é salvo em entrega/. A pasta inteira é
ignorada pelo git: nada com dados pessoais vai para o repositório.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
ORIGEM = DOCS / "MINI_PROJETO.md"
ENTREGA = RAIZ / "entrega"
DADOS_CAPA = ENTREGA / "dados_capa.json"
HTML_SAIDA = RAIZ / "build" / "MINI_PROJETO.html"
PDF_SAIDA = ENTREGA / "MiniProjeto_BladesOfSparta.pdf"

NAVEGADORES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# ----------------------------------------------------------------------------- Markdown -> HTML


def _imagem(alt, src):
    caminho = (DOCS / src).resolve().as_uri()
    return f'<img src="{caminho}" alt="{html.escape(alt)}">'


def inline(texto):
    """Converte a marcação de linha: `código`, **negrito**, *itálico* e imagens."""
    guardados = []

    def guardar(conteudo):
        guardados.append(conteudo)
        return f"\x00{len(guardados) - 1}\x00"

    # código e imagens são protegidos antes, para o negrito poder envolver código
    texto = re.sub(r"`([^`]+)`", lambda m: guardar(f"<code>{html.escape(m.group(1))}</code>"), texto)
    texto = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: guardar(_imagem(m.group(1), m.group(2))), texto)
    texto = html.escape(texto, quote=False)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", texto)
    return re.sub(r"\x00(\d+)\x00", lambda m: guardados[int(m.group(1))], texto)

def _celulas(linha):
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def markdown_para_html(texto):
    linhas = texto.splitlines()
    blocos = []
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if not linha.strip():
            i += 1
            continue
        if linha.startswith("```"):
            fim = i + 1
            while fim < len(linhas) and not linhas[fim].startswith("```"):
                fim += 1
            codigo = "\n".join(linhas[i + 1:fim])
            if "┌" in codigo:  # esboço: cada caractere numa célula de largura fixa, para a moldura alinhar
                grade = "\n".join("".join(f"<i>{html.escape(c)}</i>" for c in l) for l in codigo.splitlines())
                blocos.append(f'<pre class="esboco">{grade}</pre>')
            else:
                blocos.append(f"<pre><code>{html.escape(codigo)}</code></pre>")
            i = fim + 1
            continue
        if linha.startswith("#"):
            nivel = len(linha) - len(linha.lstrip("#"))
            blocos.append(f"<h{nivel}>{inline(linha[nivel:].strip())}</h{nivel}>")
            i += 1
            continue
        if linha.strip() == "---":
            blocos.append("<hr>")
            i += 1
            continue
        if linha.startswith("|"):
            tabela = []
            while i < len(linhas) and linhas[i].startswith("|"):
                tabela.append(linhas[i])
                i += 1
            cabecalho = _celulas(tabela[0])
            corpo = [_celulas(l) for l in tabela[2:]]
            com_imagens = any("![" in c for c in cabecalho + sum(corpo, []))
            classe = ' class="galeria"' if com_imagens else ""
            partes = [f"<table{classe}><thead><tr>"]
            partes += [f"<th>{inline(c)}</th>" for c in cabecalho]
            partes.append("</tr></thead><tbody>")
            for linha_tabela in corpo:
                partes.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in linha_tabela) + "</tr>")
            partes.append("</tbody></table>")
            blocos.append("".join(partes))
            continue
        if linha.startswith(">"):
            citacao = []
            while i < len(linhas) and linhas[i].startswith(">"):
                citacao.append(linhas[i][1:].strip())
                i += 1
            blocos.append(f"<blockquote>{inline(' '.join(citacao))}</blockquote>")
            continue
        if re.match(r"^(\d+\.|-) ", linha):
            ordenada = linha[0].isdigit()
            itens = []
            while i < len(linhas) and linhas[i].strip():
                atual = linhas[i]
                if re.match(r"^(\d+\.|-) ", atual):
                    itens.append(re.sub(r"^(\d+\.|-) ", "", atual))
                else:  # continuação do item anterior
                    itens[-1] += " " + atual.strip()
                i += 1
            tag = "ol" if ordenada else "ul"
            blocos.append(f"<{tag}>" + "".join(f"<li>{inline(item)}</li>" for item in itens) + f"</{tag}>")
            continue
        if re.fullmatch(r"!\[[^\]]*\]\([^)]+\)", linha.strip()):
            m = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", linha.strip())
            blocos.append(f'<figure>{_imagem(m.group(1), m.group(2))}</figure>')
            i += 1
            continue
        paragrafo = []
        while i < len(linhas) and linhas[i].strip() and not re.match(r"^(#|\||>|```|---$|(\d+\.|-) )", linhas[i]):
            paragrafo.append(linhas[i].strip())
            i += 1
        blocos.append(f"<p>{inline(' '.join(paragrafo))}</p>")
    return "\n".join(blocos)


# ----------------------------------------------------------------------------- documento

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm;
        @bottom-right { content: counter(page); font: 9pt 'Segoe UI', sans-serif; color: #777; }
        @bottom-left { content: "Blades of Sparta — Mini-projeto"; font: 9pt 'Segoe UI', sans-serif; color: #999; } }
@page capa { margin: 0; @bottom-right { content: none; } @bottom-left { content: none; } }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1d1b1a; margin: 0; }
.capa { page: capa; height: 297mm; padding: 26mm 22mm; display: flex; flex-direction: column;
        background: linear-gradient(180deg, #1a1012 0%, #3a1414 55%, #7a2a14 100%); color: #f2e6cf; }
.capa .instituicao { letter-spacing: .25em; font-size: 11pt; color: #d9b467; text-transform: uppercase; }
.capa .uc { margin-top: 4mm; font-size: 12pt; color: #e8d9bd; }
.capa h1 { font-family: Georgia, 'Times New Roman', serif; font-size: 40pt; line-height: 1.1; margin: 34mm 0 4mm;
           color: #e8c372; border: none; letter-spacing: .02em; }
.capa .subtitulo { font-size: 14pt; color: #f2e6cf; margin-bottom: 12mm; }
.capa img { width: 100%; border: 2px solid #b8893a; border-radius: 4px; }
.capa .dados { margin-top: auto; font-size: 11.5pt; line-height: 1.8; border-top: 1px solid #b8893a; padding-top: 6mm; }
.capa .dados b { color: #e8c372; font-weight: 600; }
h2 { font-family: Georgia, serif; color: #7a1c14; font-size: 16pt; margin: 9mm 0 3mm; padding-bottom: 1.5mm;
     border-bottom: 2px solid #c9a24e; break-after: avoid; }
h3 { color: #7a1c14; break-after: avoid; }
p { margin: 0 0 3mm; }
code { font-family: Consolas, 'Cascadia Mono', monospace; font-size: 9pt; background: #f4efe6; padding: 0 3px; border-radius: 3px; }
pre { background: #f7f3ec; border: 1px solid #e2d8c6; border-left: 4px solid #c9a24e; border-radius: 4px;
      padding: 3mm 4mm; font-size: 8.6pt; line-height: 1.35; overflow: hidden; break-inside: avoid; white-space: pre; }
pre code { background: none; padding: 0; font-size: inherit; }
pre.esboco { font-size: 7.6pt; line-height: 1.3; font-family: Consolas, 'Segoe UI Symbol', monospace; }
pre.esboco i { font-style: normal; display: inline-block; width: 1ch; text-align: center; overflow: visible; }
th code { background: rgba(255, 255, 255, .16); color: #f2e6cf; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm; font-size: 9pt; line-height: 1.38; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th { background: #3a1414; color: #f2e6cf; text-align: left; font-weight: 600; padding: 1.6mm 2.2mm; }
td { border-bottom: 1px solid #e6dccb; padding: 1.5mm 2.2mm; vertical-align: top; }
tbody tr:nth-child(even) td { background: #faf6ef; }
table.galeria td { background: none !important; padding: 1mm; border: none; }
table.galeria th { text-align: center; }
table.galeria img { width: 100%; border-radius: 3px; border: 1px solid #ccc; display: block; }
blockquote { margin: 2mm 0 4mm; padding: 2.5mm 4mm; background: #fbf1e3; border-left: 4px solid #b8893a; color: #4a3f36; font-size: 9.6pt; }
figure { margin: 0 0 4mm; } figure img { width: 100%; border-radius: 4px; }
ol, ul { margin: 0 0 3mm 5mm; padding-left: 4mm; } li { margin-bottom: 1mm; }
hr { display: none; }
"""


def carregar_dados_capa():
    """Lê os dados pessoais da capa; sem o arquivo, a capa sai sem eles."""
    try:
        return json.loads(DADOS_CAPA.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as erro:
        print(f"[aviso] {DADOS_CAPA} indisponível ({erro}); capa sem dados do aluno")
        return {}


def montar_html(markdown, dados):
    linhas = markdown.splitlines()
    # o cabeçalho do .md (título, UC e imagem) vira a capa; o corpo começa na seção 1
    inicio = next(i for i, l in enumerate(linhas) if l.startswith("## 1."))
    corpo = markdown_para_html("\n".join(linhas[inicio:]))
    rotulos = (("aluno", "Aluno"), ("ra", "RA"), ("professora", "Professora"), ("data", "Data"))
    linhas_dados = "".join(f"<b>{rotulo}:</b> {html.escape(dados[chave])}<br>"
                           for chave, rotulo in rotulos if dados.get(chave))
    capa = f"""
<section class="capa">
  <div class="instituicao">Centro Universitário UNA</div>
  <div class="uc">Computação Gráfica e Realidade Virtual · Jogos em Python</div>
  <h1>Blades of Sparta</h1>
  <div class="subtitulo">Mini-projeto: jogo de plataforma 2D em Python e Pygame</div>
  {_imagem("Fase 1", "img/fase1.png")}
  <div class="dados">{linhas_dados}</div>
</section>"""
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Blades of Sparta — Mini-projeto</title>
<style>{CSS}</style></head><body>{capa}
<main>{corpo}</main></body></html>"""


def main():
    navegador = next((n for n in NAVEGADORES if os.path.exists(n)), None) or shutil.which("chrome")
    if not navegador:
        print("Chrome ou Edge não encontrado; não é possível gerar o PDF.")
        return 1
    HTML_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    ENTREGA.mkdir(exist_ok=True)
    HTML_SAIDA.write_text(montar_html(ORIGEM.read_text(encoding="utf-8"), carregar_dados_capa()), encoding="utf-8")
    perfil = RAIZ / "build" / "perfil-navegador"
    comando = [navegador, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
               "--allow-file-access-from-files", f"--user-data-dir={perfil}",
               f"--print-to-pdf={PDF_SAIDA}", HTML_SAIDA.as_uri()]
    resultado = subprocess.run(comando, capture_output=True, text=True, timeout=120)
    if not PDF_SAIDA.exists():
        print(resultado.stderr)
        return 1
    print("PDF gerado:", PDF_SAIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
