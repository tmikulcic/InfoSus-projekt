from flask import Flask, request, jsonify, abort
from datetime import datetime, timedelta
from pony import orm

app = Flask(__name__)

# ====== DB SETUP ======
DB = orm.Database()

class Vozilo(DB.Entity):
    id = orm.PrimaryKey(int, auto=True)
    broj_sasije = orm.Required(str, unique=True)
    marka = orm.Required(str)
    model = orm.Required(str)
    tip = orm.Required(str)
    godiste = orm.Required(int)
    boja = orm.Required(str)
    tip_goriva = orm.Required(str)
    cijena_dnevnog_najma = orm.Required(float)
    termini = orm.Set("TerminNajma")

class TerminNajma(DB.Entity):
    id = orm.PrimaryKey(int, auto=True)
    vozilo = orm.Required(Vozilo)
    datum_od = orm.Required(datetime)
    datum_do = orm.Required(datetime)
    status = orm.Required(str)
    ukupna_cijena_najma = orm.Required(float)

DB.bind(provider='sqlite', filename='najam.db', create_db=True)
DB.generate_mapping(create_tables=True)

# ===== ENDPOINTI =====
@app.route('/vozilo', methods=['POST'])
def dodaj_vozilo():
    data = request.json
    try:
        with orm.db_session:
            Vozilo(
                broj_sasije=data['broj_sasije'],
                marka=data['marka'],
                model=data['model'],
                tip=data['tip'],
                godiste=data['godiste'],
                boja=data['boja'],
                tip_goriva=data['tip_goriva'],
                cijena_dnevnog_najma=float(data['cijena_dnevnog_najma'])
            )
        return jsonify({'message': 'Vozilo dodano'}), 201
    except orm.ConstraintError:
        abort(400, description="Broj šasije već postoji")

@app.route('/vozilo', methods=['GET'])
def dohvati_vozila():
    with orm.db_session:
        vozila = orm.select(v for v in Vozilo)[:]
        return jsonify([v.to_dict() for v in vozila])

@app.route('/vozilo/<int:vozilo_id>', methods=['PATCH'])
def azuriraj_vozilo(vozilo_id):
    data = request.json
    with orm.db_session:
        vozilo = Vozilo.get(id=vozilo_id)
        if not vozilo:
            abort(404, description="Vozilo nije pronađeno")
        for key in ['broj_sasije', 'marka', 'model', 'tip', 'godiste', 'boja', 'tip_goriva', 'cijena_dnevnog_najma']:
            if key in data:
                setattr(vozilo, key, data[key])
        return jsonify({'message': 'Vozilo ažurirano'})

@app.route('/vozilo/<int:vozilo_id>', methods=['DELETE'])
def obrisi_vozilo(vozilo_id):
    with orm.db_session:
        vozilo = Vozilo.get(id=vozilo_id)
        if not vozilo:
            abort(404, description="Vozilo nije pronađeno")
        vozilo.delete()
        return jsonify({'message': 'Vozilo obrisano'})

@app.route('/termin', methods=['POST'])
def dodaj_termin():
    data = request.json
    try:
        datum_od = datetime.strptime(data['datum_od'], '%d-%m-%Y')
        datum_do = datetime.strptime(data['datum_do'], '%d-%m-%Y')
    except ValueError:
        abort(400, description='Neispravan format datuma (dd-mm-yyyy)')

    if datum_do < datum_od:
        abort(400, description='Krajnji datum ne može biti prije početnog')

    with orm.db_session:
        vozilo = Vozilo.get(id=data['vozilo_id'])
        if not vozilo:
            abort(400, description='Vozilo nije pronađeno')

        # Provjera preklapanja termina za to vozilo
        for termin in vozilo.termini:
            if datum_od <= termin.datum_do and datum_do >= termin.datum_od:
                abort(409, description='Vozilo je već rezervirano u traženom terminu')

        broj_dana = (datum_do - datum_od).days + 1
        ukupna_cijena = broj_dana * vozilo.cijena_dnevnog_najma

        TerminNajma(
            vozilo=vozilo,
            datum_od=datum_od,
            datum_do=datum_do,
            status=data['status'],
            ukupna_cijena_najma=round(ukupna_cijena, 2)
        )
    return jsonify({'message': 'Termin najma dodan'}), 201

@app.route('/termin', methods=['GET'])
def dohvati_termine():
    with orm.db_session:
        termini = orm.select(t for t in TerminNajma)[:]
        data = []
        for t in termini:
            d = t.to_dict()
            d['datum_od'] = t.datum_od.strftime('%d-%m-%Y')
            d['datum_do'] = t.datum_do.strftime('%d-%m-%Y')
            d['vozilo_id'] = t.vozilo.id
            data.append(d)
        return jsonify(data)

@app.route('/termin/<int:termin_id>', methods=['PATCH'])
def azuriraj_termin(termin_id):
    data = request.json
    with orm.db_session:
        termin = TerminNajma.get(id=termin_id)
        if not termin:
            abort(404, description="Termin nije pronađen")
        if 'status' in data:
            termin.status = data['status']
        return jsonify({'message': 'Status termina ažuriran'})

@app.route('/termin/<int:termin_id>', methods=['DELETE'])
def obrisi_termin(termin_id):
    with orm.db_session:
        termin = TerminNajma.get(id=termin_id)
        if not termin:
            abort(404, description="Termin nije pronađen")
        termin.delete()
        return jsonify({'message': 'Termin obrisan'})

if __name__ == '__main__':
    app.run(port=8080)