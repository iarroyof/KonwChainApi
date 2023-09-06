import os
from flask import Flask, request, render_template, send_file
from elasticsearch import Elasticsearch

import stanza

app = Flask(__name__)

# Descarga e instala los modelos de idioma en inglés
stanza.download('en')

# Inicializa el modelo de idioma en inglés
nlp = stanza.Pipeline('en')

# Inicializa la conexión a Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200,'scheme':'http' }])  # Reemplaza con la dirección de tu servidor Elasticsearch


# Ruta donde se guardarán los archivos subidos
UPLOAD_FOLDER = 'static'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        archivo = request.files['file']
        if not archivo:
            return "Por favor, seleccione un archivo para subir."

        # Verifica la extensión del archivo
        if archivo.filename.endswith('.txt'):
            # Guarda el archivo en el directorio de carga
            filename = os.path.join(UPLOAD_FOLDER, archivo.filename)
            archivo.save(filename)

            # Procesa el texto del archivo
            with open(filename, "r", encoding="utf-8") as file:
                texto = file.read()

            # Realiza el análisis de POS y agrupa las palabras
            doc = nlp(texto)

            palabras_por_etiqueta = {}
            etiquetas_a_excluir = {"AUX", "ADP", "PRON", "NUM", "X", "PART", "SYM", "SCONJ", "CCONJ", "DET", "PUNCT"}

            for sentence in doc.sentences:
                for word in sentence.words:
                    etiqueta_pos = word.pos
                    if etiqueta_pos not in etiquetas_a_excluir:
                        if etiqueta_pos not in palabras_por_etiqueta:
                            palabras_por_etiqueta[etiqueta_pos] = []
                        palabras_por_etiqueta[etiqueta_pos].append(word.text)
                        palabras_por_etiqueta['FILE'] = archivo.filename

            print(palabras_por_etiqueta)


            # Elimina el archivo cargado
            os.remove(filename)

            # Envía los datos a Elasticsearch
            #index_name = 'pos_analysis'  
            #es.index(index=index_name,  body=palabras_por_etiqueta)


            # Retorna las palabras agrupadas por etiqueta POS
            return render_template('result.html', palabras_por_etiqueta=palabras_por_etiqueta)
        else:
            return "El archivo debe tener la extensión .txt."

    return render_template('index.html')

@app.route('/descargar/<nombre_archivo>')
def descargar_archivo(nombre_archivo):

    try:
        # Especifica la ruta completa del archivo dentro de la carpeta 'static'
        ruta_archivo = f'static/{nombre_archivo}'
        print(f'Ruta del archivo: {ruta_archivo}')

        # Usa la función send_file para enviar el archivo al cliente
        return send_file(ruta_archivo, as_attachment=True)

    except FileNotFoundError:
        # Manejo de errores si el archivo no se encuentra
        return "El archivo no se encontró", 404

if __name__ == '__main__':
    app.run(debug=True)
