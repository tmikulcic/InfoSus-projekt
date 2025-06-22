from flask import Flask, request, jsonify, abort, render_template, redirect, url_for, flash
from datetime import datetime
from pony import orm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tvoj_tajni_ključ_ovdje'

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

DB.bind(provider='sqlite', filename='db.sqlite', create_db=True)
DB.generate_mapping(create_tables=True)

# ====== ROUTES ======

@app.route('/')
def home():
    with orm.db_session:
        vozila = orm.select(v for v in Vozilo)[:]
        termini = orm.select(t for t in TerminNajma)[:]
        data_termini = []
        for t in termini:
            data_termini.append({
                'id': t.id,
                'vozilo_id': t.vozilo.id,
                'datum_od': t.datum_od.strftime('%Y-%m-%d'),
                'datum_do': t.datum_do.strftime('%Y-%m-%d'),
                'status': t.status,
                'ukupna_cijena_najma': t.ukupna_cijena_najma
            })
    return render_template('index.html', vozila=vozila, termini=data_termini)

# --- Vozilo CRUD preko REST ---
@app.route('/vozilo', methods=['POST'])
def dodaj_vozilo_api():
    data = request.json
    try:
        with orm.db_session:
            Vozilo(
                broj_sasije=data['broj_sasije'],
                marka=data['marka'],
                model=data['model'],
                tip=data['tip'],
                godiste=int(data['godiste']),
                boja=data['boja'],
                tip_goriva=data['tip_goriva'],
                cijena_dnevnog_najma=float(data['cijena_dnevnog_najma'])
            )
        return jsonify({'message': 'Vozilo dodano'}), 201
    except orm.ConstraintError:
        abort(400, description="Broj šasije već postoji")

@app.route('/vozilo', methods=['GET'])
def dohvati_vozila_api():
    with orm.db_session:
        vozila = orm.select(v for v in Vozilo)[:]
        return jsonify([v.to_dict() for v in vozila])

@app.route('/vozilo/<int:vozilo_id>', methods=['PATCH'])
def azuriraj_vozilo_api(vozilo_id):
    data = request.json
    with orm.db_session:
        vozilo = Vozilo.get(id=vozilo_id)
        if not vozilo:
            abort(404, description="Vozilo nije pronađeno")
        for key in ['broj_sasije','marka','model','tip','godiste','boja','tip_goriva','cijena_dnevnog_najma']:
            if key in data:
                setattr(vozilo, key, data[key])
        return jsonify({'message': 'Vozilo ažurirano'})

@app.route('/vozilo/<int:vozilo_id>', methods=['DELETE'])
def obrisi_vozilo_api(vozilo_id):
    with orm.db_session:
        vozilo = Vozilo.get(id=vozilo_id)
        if not vozilo:
            abort(404, description="Vozilo nije pronađeno")
        vozilo.delete()
        return jsonify({'message': 'Vozilo obrisano'})

# --- Termin CRUD preko REST ---
@app.route('/termin', methods=['POST'])
def dodaj_termin_api():
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
            ukupna_cijena_najma=round(ukupna_cijena,2)
        )
    return jsonify({'message': 'Termin najma dodan'}), 201

@app.route('/termin', methods=['GET'])
def dohvati_termine_api():
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
def azuriraj_termin_api(termin_id):
    data = request.json
    with orm.db_session:
        termin = TerminNajma.get(id=termin_id)
        if not termin:
            abort(404, description="Termin nije pronađen")
        if 'status' in data:
            termin.status = data['status']
        return jsonify({'message': 'Status termina ažuriran'})

@app.route('/termin/<int:termin_id>', methods=['DELETE'])
def obrisi_termin_api(termin_id):
    with orm.db_session:
        termin = TerminNajma.get(id=termin_id)
        if not termin:
            abort(404, description="Termin nije pronađen")
        termin.delete()
        return jsonify({'message': 'Termin obrisan'})

# --- Vozilo CRUD preko web forme ---
@app.route('/vozilo/novo', methods=['GET','POST'])
def nova_vozilo():
    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            with orm.db_session:
                Vozilo(
                    broj_sasije=data['broj_sasije'],
                    marka=data['marka'],
                    model=data['model'],
                    tip=data['tip'],
                    godiste=int(data['godiste']),
                    boja=data['boja'],
                    tip_goriva=data['tip_goriva'],
                    cijena_dnevnog_najma=float(data['cijena_dnevnog_najma'])
                )
            flash('Vozilo je dodano.', 'success')
            return redirect(url_for('home'))
        except orm.ConstraintError:
            flash('Broj šasije već postoji.', 'danger')
    return render_template('vozilo_form.html', vozilo=None)

@app.route('/vozilo/<int:vozilo_id>/uredi', methods=['GET','POST'])
def uredi_vozilo(vozilo_id):
    if request.method == 'POST':
        data = request.form.to_dict()
        with orm.db_session:
            vozilo = Vozilo.get(id=vozilo_id)
            if not vozilo:
                abort(404)
            for k,v in data.items():
                if k=='cijena_dnevnog_najma':
                    setattr(vozilo,k,float(v))
                elif k=='godiste':
                    setattr(vozilo,k,int(v))
                else:
                    setattr(vozilo,k,v)
        flash('Vozilo ažurirano.', 'success')
        return redirect(url_for('home'))

    with orm.db_session:
        vozilo = Vozilo.get(id=vozilo_id)
        if not vozilo:
            abort(404)
        vozilo_data = {
            'id': vozilo.id,
            'broj_sasije': vozilo.broj_sasije,
            'marka': vozilo.marka,
            'model': vozilo.model,
            'tip': vozilo.tip,
            'godiste': vozilo.godiste,
            'boja': vozilo.boja,
            'tip_goriva': vozilo.tip_goriva,
            'cijena_dnevnog_najma': vozilo.cijena_dnevnog_najma
        }
    return render_template('vozilo_form.html', vozilo=vozilo_data)

# --- Termin CRUD preko web forme ---
@app.route('/termin/novi', methods=['GET','POST'])
def novi_termin():
    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            datum_od = datetime.strptime(data['datum_od'], '%Y-%m-%d')
            datum_do = datetime.strptime(data['datum_do'], '%Y-%m-%d')
            if datum_do < datum_od:
                raise ValueError('Krajnji datum prije početnog')
            with orm.db_session:
                vozilo = Vozilo.get(id=int(data['vozilo_id']))
                if not vozilo:
                    raise ValueError('Vozilo nije pronađeno')
                for t in vozilo.termini:
                    if datum_od <= t.datum_do and datum_do >= t.datum_od:
                        raise ValueError('Preklapajući termin')
                broj_dana = (datum_do - datum_od).days + 1
                cijena = broj_dana * vozilo.cijena_dnevnog_najma
                TerminNajma(
                    vozilo=vozilo,
                    datum_od=datum_od,
                    datum_do=datum_do,
                    status=data['status'],
                    ukupna_cijena_najma=round(cijena,2)
                )
            flash('Termin je dodan.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(str(e), 'danger')

    with orm.db_session:
        vozila = orm.select(v for v in Vozilo)[:]
    return render_template('termin_form.html', termin=None, vozila=vozila)

@app.route('/termin/<int:termin_id>/uredi', methods=['GET','POST'])
def uredi_termin(termin_id):
    if request.method == 'POST':
        data = request.form.to_dict()
        with orm.db_session:
            termin = TerminNajma.get(id=termin_id)
            if not termin:
                abort(404)
            if 'status' in data:
                termin.status = data['status']
        flash('Termin ažuriran.', 'success')
        return redirect(url_for('home'))

    with orm.db_session:
        termin = TerminNajma.get(id=termin_id)
        if not termin:
            abort(404)
        termin_data = {
            'id': termin.id,
            'vozilo_id': termin.vozilo.id,
            'datum_od': termin.datum_od.strftime('%Y-%m-%d'),
            'datum_do': termin.datum_do.strftime('%Y-%m-%d'),
            'status': termin.status
        }
        vozila = orm.select(v for v in Vozilo)[:]
    return render_template('termin_form.html', termin=termin_data, vozila=vozila)

# --- Dohvat zauzetih termina za odabrano vozilo ---
@app.route('/termini_vozila/<int:vozilo_id>')
def termini_vozila(vozilo_id):
    with orm.db_session:
        terms = orm.select(t for t in TerminNajma if t.vozilo.id == vozilo_id)[:]
        data = [{
            'datum_od': t.datum_od.strftime('%Y-%m-%d'),
            'datum_do': t.datum_do.strftime('%Y-%m-%d')
        } for t in terms]
    return jsonify(data)

# --- Chart.js routes ---
@app.route('/charts/pie')
def charts_pie():
    with orm.db_session:
        fuel_counts = {}
        type_counts = {}
        for v in orm.select(v for v in Vozilo)[:]:
            fuel_counts[v.tip_goriva] = fuel_counts.get(v.tip_goriva, 0) + 1
            type_counts[v.tip]         = type_counts.get(v.tip, 0) + 1

    return render_template(
        'charts_pie.html',
        labelsFuel=list(fuel_counts.keys()), dataFuel=list(fuel_counts.values()),
        labelsType=list(type_counts.keys()),   dataType=list(type_counts.values())
    )

@app.route('/charts/years')
def charts_years():
    with orm.db_session:
        vozila = orm.select(v for v in Vozilo)[:]
    years = list(range(2000, 2026))
    counts = [0]*len(years)
    for v in vozila:
        if 2000 <= v.godiste <= 2025:
            counts[years.index(v.godiste)] += 1

    return render_template(
        'charts_years.html',
        labelsYears=years, dataYears=counts
    )

@app.route('/charts/earnings')
def charts_earnings():
    with orm.db_session:
        sums = {}
        for t in orm.select(t for t in TerminNajma)[:]:
            lbl = f"{t.vozilo.id} - {t.vozilo.marka} {t.vozilo.model}"
            sums[lbl] = sums.get(lbl, 0) + t.ukupna_cijena_najma
    items = sorted(sums.items(), key=lambda x: x[1], reverse=True)
    return render_template(
        'charts_earnings.html',
        labelsE=[i[0] for i in items], dataE=[i[1] for i in items]
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)