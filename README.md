## Klasa: Vozilo

**Entiteti:**
- id (primarni ključ) (tip: integer)
- broj_sasije (string, UNIQUE)
- marka (tip: string)
- model (tip: string)
- tip (tip: string) – npr. osobno, dostavno, hatchback, SUV, itd.
- godiste (tip: integer) – godina proizvodnje vozila
- boja (tip: string) – boja vozila
- tip_goriva (tip: string) – npr. benzin, dizel, električno
- cijena_dnevnog_najma (tip: decimal) – cijena najma vozila po danu


## Klasa: Termin_najma

**Entiteti:**
- id (primarni ključ) (tip: integer)
- vozilo_id (strani ključ) (tip: integer)
- datum_od (datetime) - pocetni datum
- datum_do (datetime) - krajnji datum
- status (tip: string) – npr. rezerviran, u tijeku, otkazan
- ukupna_cijena_najma (tip: decimal) – ukupna cijena najma izračunata na temelju cijene dnevnog najma vozila i trajanja najma

## Use case dijagam
![Use case dijagram](Use-case.jpg)

## Funkcionalnost
Rent a car je web aplikacija osmišljena za jednostavno upravljanje voznim parkom i terminima najma vozila. Namijenjena je agencijama za najam, tvrtkama s flotama vozila i svima koji žele imati potpunu kontrolu nad svojim vozilima i rezervacijama na jednom mjestu.

Aplikacija omogućuje unos i upravljanje detaljnim informacijama o svakom vozilu — uključujući broj šasije, marku, model, tip, boju, vrstu goriva i cijenu dnevnog najma. Pomoću intuitivnog sučelja korisnici mogu pregledavati, dodavati, uređivati ili brisati vozila unutar baze podataka.

Osim upravljanja vozilima, aplikacija nudi upravljanje terminima najma. Svakom najmu moguće je dodijeliti određeno vozilo, unijeti početni i krajnji datum, status rezervacije (rezerviran, u tijeku, otkazan), kao i izračunati ukupnu cijenu najma na temelju trajanja i cijene po danu. Sve rezervacije su jasno prikazane, što omogućuje uvid u trenutačnu zauzetost i dostupnost voznog parka.

Za dodatnu analizu, aplikacija uključuje vizualne prikaze i grafikone koji omogućuju praćenje godina proizvodnje vozila i njihovu raspodjelu. To pomaže u planiranju obnove voznog parka i optimizaciji poslovanja.

## Instalacija

```
git clone https://github.com/tmikulcic/InfoSus-projekt.git
cd InfoSus-projekt
docker build -t rentacar .
docker run -p 5001:8080 rentacar
```