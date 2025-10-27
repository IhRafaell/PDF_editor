
import os
import uuid 
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
from pypdf import PdfWriter
from PIL import Image


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def juntar_pdfs(caminhos_dos_arquivos, caminho_do_arquivo_saida):
    """Junta múltiplos arquivos PDF."""
    merger = PdfWriter()
    for caminho in caminhos_dos_arquivos:
        merger.append(caminho)
    merger.write(caminho_do_arquivo_saida)
    merger.close()

def converter_imagens_para_pdf(caminhos_das_imagens, caminho_do_arquivo_saida):

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



@app.route('/')
def index():
    return render_template('index.html', pdf_url='')

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath) and filename.endswith('.pdf'):
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
    nome_saida_unico = f'{uuid.uuid4()}.pdf'
    caminho_saida = os.path.join(app.config['UPLOAD_FOLDER'], nome_saida_unico)

    try:
        for f in arquivos_enviados:
            if f and f.filename:
                nome_upload = f"{uuid.uuid4()}_{f.filename}"
                caminho_salvo = os.path.join(app.config['UPLOAD_FOLDER'], nome_upload)
                f.save(caminho_salvo)
                caminhos_uploads.append(caminho_salvo)
        
        if not caminhos_uploads:
             return jsonify({'error': 'Nenhum arquivo válido enviado.'}), 400

        if acao == 'juntar_pdfs':
            juntar_pdfs(caminhos_uploads, caminho_saida)
        elif acao == 'converter_imagens':
            converter_imagens_para_pdf(caminhos_uploads, caminho_saida)
        else:
            return jsonify({'error': 'Ação inválida.'}), 400
        
        return jsonify({'filename': nome_saida_unico})

    except Exception as e:
        return jsonify({'error': f'Ocorreu um erro no processamento: {str(e)}'}), 500
    
    finally:

        for caminho in caminhos_uploads:
            if os.path.exists(caminho):
                os.remove(caminho)

if __name__ == '__main__':
    app.run(debug=True)
