from flask import Flask, request, render_template, jsonify
import requests
import os

app = Flask(__name__)

def get_sequence_from_uniprot(uniprot_id):
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"
    response = requests.get(url)
    if response.status_code != 200:
        return None, "UniProt ID not found."
    lines = response.text.strip().split('\n')
    sequence = ''.join(lines[1:])
    return sequence, None

def get_structure_from_esmfold(sequence):
    url = "https://api.esmatlas.com/foldSequence/v1/pdb/"
    response = requests.post(url, data=sequence, headers={'Content-Type': 'text/plain'})
    if response.status_code != 200:
        return None, "Structure prediction failed, check sequence and try again."
    return response.text, None

def get_sequence_properties(sequence):
    amino_acid_weights = {
        'A': 89.1, 'R': 174.2, 'N': 132.1, 'D': 133.1, 'C': 121.2,
        'E': 147.1, 'Q': 146.2, 'G': 75.1, 'H': 155.2, 'I': 131.2,
        'L': 131.2, 'K': 146.2, 'M': 149.2, 'F': 165.2, 'P': 115.1,
        'S': 105.1, 'T': 119.1, 'W': 204.2, 'Y': 181.2, 'V': 117.1
    }
    length = len(sequence)
    mw = sum(amino_acid_weights.get(aa, 110) for aa in sequence.upper())
    composition = {}
    for aa in sequence.upper():
        composition[aa] = composition.get(aa, 0) + 1
    top_residues = sorted(composition.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        'length': length,
        'molecular_weight': round(mw / 1000, 2),
        'top_residues': top_residues
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    uniprot_id = request.form.get('uniprot_id', '').strip()
    sequence = request.form.get('sequence', '').strip()
    
    if len(sequence) > 400:
    return render_template('index.html', error="sequence must be under 400 amino acids")

    if uniprot_id:
        sequence, error = get_sequence_from_uniprot(uniprot_id)
        if error:
            return render_template('index.html', error=error)

    if not sequence:
        return render_template('index.html', error="Please enter AA sequence or UniProt ID.")

    pdb_data, error = get_structure_from_esmfold(sequence)
    print("PDB DATA PREVIEW:", pdb_data[:200] if pdb_data else "NONE")

    if error:
        return render_template('index.html', error=error)

    properties = get_sequence_properties(sequence)

    return render_template('index.html',
        pdb_data=pdb_data,
        sequence=sequence,
        properties=properties
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
