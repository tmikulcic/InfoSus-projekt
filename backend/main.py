from flask import Flask, request, jsonify, abort
from datetime import datetime, timedelta

app = Flask(__name__)

vozila = []
termini_najma = []

# ===== VOZILO =====
@app.route('/vozilo', methods=['POST'])
def dodaj_vozilo():
    data = request.json
    # Provjera unikatnog broja šasije
    if any(v['broj_sasije'] == data['broj_sasije'] for v in vozila):
        abort(400, description='Broj šasije već postoji')
    vozila.append(data)
    return jsonify({'message': 'Vozilo dodano'}), 201

@app.route('/vozilo', methods=['GET'])
def dohvati_vozila():
    return jsonify(vozila)

@app.route('/vozilo/<int:vozilo_id>', methods=['PUT'])
def zamijeni_vozilo(vozilo_id):
    novi_podaci = request.json
    for i, vozilo in enumerate(vozila):
        if vozilo['id'] == vozilo_id:
            vozila[i] = novi_podaci
            return jsonify({'message': 'Vozilo zamijenjeno'}), 200
    abort(404, description="Vozilo nije pronađeno")

@app.route('/vozilo/<int:vozilo_id>', methods=['DELETE'])
def obrisi_vozilo(vozilo_id):
    for i, vozilo in enumerate(vozila):
        if vozilo['id'] == vozilo_id:
            del vozila[i]
            return jsonify({'message': 'Vozilo obrisano'}), 200
    abort(404, description="Vozilo nije pronađeno")

# ===== TERMIN NAJMA =====
@app.route('/termin', methods=['POST'])
def dodaj_termin():
    data = request.json
    vozilo = next((v for v in vozila if v['id'] == data['vozilo_id']), None)
    if not vozilo:
        abort(400, description='Vozilo nije pronađeno')

    try:
        datum_od = datetime.strptime(data['datum_od'], '%d-%m-%Y')
        datum_do = datetime.strptime(data['datum_do'], '%d-%m-%Y')
    except ValueError:
        abort(400, description='Neispravan format datuma (dd-mm-yyyy)')

    if datum_do < datum_od:
        abort(400, description='Krajnji datum ne može biti prije početnog')

    # Provjera preklapanja termina za to vozilo
    for termin in termini_najma:
        if termin['vozilo_id'] == data['vozilo_id']:
            postojeci_od = datetime.strptime(termin['datum_od'], '%d-%m-%Y')
            postojeci_do = datetime.strptime(termin['datum_do'], '%d-%m-%Y')
            if datum_od <= postojeci_do and datum_do >= postojeci_od:
                abort(409, description='Vozilo je već rezervirano u traženom terminu')

    broj_dana = (datum_do - datum_od).days + 1
    ukupna_cijena = broj_dana * float(vozilo['cijena_dnevnog_najma'])

    data['ukupna_cijena_najma'] = round(ukupna_cijena, 2)
    data['datumi_rezervacije'] = [
        (datum_od + timedelta(days=i)).strftime('%d-%m-%Y') for i in range(broj_dana)
    ]
    termini_najma.append(data)
    return jsonify({'message': 'Termin najma dodan'}), 201

@app.route('/termin', methods=['GET'])
def dohvati_termine():
    return jsonify(termini_najma)

@app.route('/termin/<int:termin_id>', methods=['DELETE'])
def obrisi_termin(termin_id):
    for i, termin in enumerate(termini_najma):
        if termin['id'] == termin_id:
            del termini_najma[i]
            return jsonify({'message': 'Termin obrisan'}), 200
    abort(404, description="Termin nije pronađen")

@app.route('/termin/<int:termin_id>', methods=['PATCH'])
def azuriraj_status_termina(termin_id):
    novi_status = request.json.get('status')
    for termin in termini_najma:
        if termin['id'] == termin_id:
            termin['status'] = novi_status
            return jsonify({'message': 'Status ažuriran'}), 200
    abort(404, description="Termin nije pronađen")

if __name__ == '__main__':
    app.run(port=8080)