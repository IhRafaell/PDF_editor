# app.py
import os
import uuid # Importar para gerar IDs únicos
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
from pypdf import PdfWriter
from PIL import Image

# Configuração do Flask
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Funções de Manipulação de Arquivos (Mesmas do exemplo anterior) ---
# ... (Manter as funções juntar_pdfs e converter_imagens_para_pdf)

def juntar_pdfs(caminhos_dos_arquivos, caminho_do_arquivo_saida):
    """Junta múltiplos arquivos PDF."""
    merger = PdfWriter()
    for caminho in caminhos_dos_arquivos:
        merger.append(caminho)
    merger.write(caminho_do_arquivo_saida)
    merger.close()

def converter_imagens_para_pdf(caminhos_das_imagens, caminho_do_arquivo_saida):
    """Converte múltiplas imagens para um único PDF."""
    imagens_pil = []
    for caminho in caminhos_das_imagens:
        try:
            imagens_pil.append(Image.open(caminho).convert('RGB'))
        except Exception as e:
            print(f"Erro ao processar imagem {caminho}: {e}")
            
    if not imagens_pil:
        raise ValueError("Nenhuma imagem válida encontrada para conversão.")

    imagens_pil[0].save(
        caminho_do_arquivo_saida,
        save_all=True,
        append_images=imagens_pil[1:]
    )
# ... (Fim das Funções)

# Rota para a página inicial
@app.route('/')
def index():
    # Adicionamos uma variável para o template para a URL de download
    return render_template('index.html', pdf_url='')

# Nova rota para servir o PDF gerado (vai ser chamada via JS/iframe)
@app.route('/pdf/<filename>')
def serve_pdf(filename):
    # Garante que o arquivo está na pasta de uploads e é um PDF
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath) and filename.endswith('.pdf'):
        # Retorna o arquivo com o Content-Type correto para renderizar no navegador
        return send_file(filepath, mimetype='application/pdf')
    
    return "Arquivo não encontrado.", 404

@app.route('/processar', methods=['POST'])
def processar():
    """Recebe os arquivos, processa e retorna o nome do PDF gerado."""
    
    acao = request.form.get('acao')
    arquivos_enviados = request.files.getlist('arquivos')
    
    if not arquivos_enviados or not acao:
        return jsonify({'error': 'Nenhum arquivo ou ação selecionada.'}), 400

    caminhos_uploads = []
    # Gera um nome de arquivo de saída único para evitar cache e conflitos
    nome_saida_unico = f'{uuid.uuid4()}.pdf'
    caminho_saida = os.path.join(app.config['UPLOAD_FOLDER'], nome_saida_unico)

    try:
        # 1. Salva temporariamente os arquivos de entrada
        for f in arquivos_enviados:
            if f and f.filename:
                # Usa um nome único para o arquivo de upload temporário
                nome_upload = f"{uuid.uuid4()}_{f.filename}"
                caminho_salvo = os.path.join(app.config['UPLOAD_FOLDER'], nome_upload)
                f.save(caminho_salvo)
                caminhos_uploads.append(caminho_salvo)
        
        if not caminhos_uploads:
             return jsonify({'error': 'Nenhum arquivo válido enviado.'}), 400

        # 2. Processa
        if acao == 'juntar_pdfs':
            juntar_pdfs(caminhos_uploads, caminho_saida)
        elif acao == 'converter_imagens':
            converter_imagens_para_pdf(caminhos_uploads, caminho_saida)
        else:
            return jsonify({'error': 'Ação inválida.'}), 400
        
        # 3. Retorna o NOME do arquivo gerado (o Front-end vai carregar este arquivo)
        return jsonify({'filename': nome_saida_unico})

    except Exception as e:
        return jsonify({'error': f'Ocorreu um erro no processamento: {str(e)}'}), 500
    
    finally:
        # 4. Limpa os arquivos de entrada temporários (O ARQUIVO DE SAÍDA DEVE PERMANECER)
        # O arquivo de saída (resultado.pdf) será limpo por um sistema externo 
        # ou após um certo tempo, para que o /pdf/<filename> funcione.
        for caminho in caminhos_uploads:
            if os.path.exists(caminho):
                os.remove(caminho)

if __name__ == '__main__':
    app.run(debug=True)