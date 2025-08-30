Installatiehandleiding voor de Gedeelde Boodschappenlijst
Deze handleiding leidt je door de volledige installatie van de webapplicatie. We beginnen met het opzetten van een LXC-container en eindigen met de volledig functionele applicatie.

Stap 1: LXC-container aanmaken
Voor deze handleiding gebruiken we Proxmox. De stappen kunnen iets afwijken als je een andere containeromgeving gebruikt.

Log in op je Proxmox-webinterface.

Klik op de knop "Create CT" (Container maken) in de rechterbovenhoek.

Algemeen Tabblad:

Hostname: Kies een hostnaam, bijvoorbeeld boodschappenlijst-app.

Password: Kies een sterk wachtwoord voor de root-gebruiker.

Template Tabblad:

Kies een Linux-template. De aanbevolen keuze is Debian 12 "Bookworm" of Ubuntu 22.04 LTS "Jammy Jellyfish".

Storage & CPU Tabbladen:

Root Disk: Geef minstens 4 GB schijfruimte.

CPU Cores: Wijs minstens 1 core toe.

Memory & Network Tabbladen:

Memory (RAM): Geef minstens 512 MB RAM. 1 GB is aanbevolen.

Network: Stel een statisch IP-adres in voor je container, zodat je er gemakkelijk verbinding mee kunt maken.

Klik op "Finish" om de container te maken.

Stap 2: Basisconfiguratie van de Container
Nadat de container is aangemaakt, moet je er de benodigde software op installeren.

Start de container als deze niet automatisch is gestart.

Open een shell naar de container. Dit kan via de Proxmox-console of via SSH.

ssh root@<jouw-container-ip>

Werk de pakketlijst bij en installeer de benodigde tools.

apt update && apt upgrade -y
apt install -y git python3-pip python3-venv

Stap 3: De Applicatie downloaden en configureren
Nu is het tijd om de code te downloaden en de Python-omgeving op te zetten.

Navigeer naar de /opt map of een andere geschikte locatie.

cd /opt

Kloon de applicatiecode vanaf een repository (als je die hebt geüpload). Let op: Als je de code nog niet hebt geüpload, moet je de inhoud van de index.html en app.py bestanden kopiëren en lokaal opslaan in een map.

git clone [https://github.com/jouw-gebruikersnaam/jouw-project.git](https://github.com/jouw-gebruikersnaam/jouw-project.git)
cd jouw-project

Maak een virtuele Python-omgeving aan en activeer deze.

python3 -m venv venv
source venv/bin/activate

Installeer de Python-afhankelijkheden.

pip install Flask requests beautifulsoup4 apscheduler

Stap 4: Firebase/Firestore configureren
De applicatie heeft een werkende verbinding met een Firestore-database nodig.

Maak een Firebase-project aan:

Ga naar de Firebase Console.

Maak een nieuw project aan.

Web-app toevoegen:

Voeg een web-app toe aan je project.

Kopieer de firebaseConfig-variabele die je krijgt. Het ziet er zo uit:

const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  storageBucket: "...",
  messagingSenderId: "...",
  appId: "...",
  measurementId: "..."
};

Firestore-database instellen:

Navigeer naar Firestore Database in de Firebase Console.

Klik op "Create database" en kies "Start in production mode".

Stel je locatie in en klik op "Done".

Firestore Beveiligingsregels:

Ga naar het tabblad "Rules" in de Firestore-database.

Vervang de regels door het volgende, zodat de gedeelde lijsten toegankelijk zijn voor alle gebruikers. Dit is essentieel voor de samenwerkingsfunctie.

rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /artifacts/{appId}/public/data/shared_lists/{listId}/{documents=**} {
      allow read, write: if true;
    }

    match /artifacts/{appId}/users/{userId}/{documents=**} {
        allow read, write: if request.auth.uid == userId;
    }
  }
}

Klik op "Publish".

Applicatievariabelen toevoegen:

Open het index.html bestand.

Vind de regels voor firebaseConfig en appId en vervang ze met jouw eigen waarden.

const firebaseConfig = JSON.parse(typeof __firebase_config !== 'undefined' ? __firebase_config : '{"apiKey": "JOUW-API-KEY", "authDomain": "JOUW-AUTH-DOMAIN", "projectId": "JOUW-PROJECT-ID", "storageBucket": "JOUW-STORAGE-BUCKET", "messagingSenderId": "JOUW-MESSAGING-SENDER-ID", "appId": "JOUW-APP-ID"}');
const appId = typeof __app_id !== 'undefined' ? __app_id : 'JOUW-APP-ID';

Stap 5: De Applicatie lokaal uitvoeren
Je bent bijna klaar! Nu kun je de webserver starten.

Zorg ervoor dat je nog steeds in de geactiveerde Python-omgeving zit.

Start de Flask-server.

python3 app.py

De webserver zal nu luisteren op poort 5000 van het lokale IP-adres van je container. Je zou een melding moeten zien zoals Running on http://0.0.0.0:5000.

Open in je webbrowser het IP-adres van je LXC-container, gevolgd door poort 5000.

http://<jouw-container-ip>:5000

Je zou nu de applicatie moeten zien en kunnen gebruiken!

Mocht je tegen problemen aanlopen of bepaalde stappen onduidelijk vinden, laat het me dan weten!
