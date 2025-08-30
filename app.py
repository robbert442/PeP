import os
import requests
import re
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time

app = Flask(__name__)

# Een eenvoudige webscraper die naar productprijzen zoekt op basis van de websites.
# LET OP: Dit is een vereenvoudigde implementatie. De selectors kunnen veranderen
# en sommige websites kunnen geavanceerde technieken gebruiken die dit voorkomen.
def get_offers_from_websites(products):

    # Tijdelijke opslag voor de beste deal per product
    best_deals = {}

    # Initialiseer de beste deals met "niet gevonden" status
    for product in products:
        best_deals[product['name'].lower()] = {
            "productName": product['name'],
            "store": "n.v.t.",
            "price": "Niet gevonden",
            "details": "Niet gevonden",
            "numericPrice": float('inf')
        }

    # Zoektermen voor elke winkel en hun corresponderende URL's
    search_urls = {
        "ah.nl": "https://www.ah.nl/zoeken?query=",
        "jumbo.com": "https://www.jumbo.com/zoeken?search=",
        "kruidvat.nl": "https://www.kruidvat.nl/search?q=",
        "lidl.nl": "https://www.lidl.nl/s?q="
    }

    for product in products:
        product_name = product['name'].lower()

        for store, base_url in search_urls.items():
            try:
                # Bouw de volledige URL voor het product
                search_query = product_name.replace(" ", "+")
                url = f"{base_url}{search_query}"

                # Voer het verzoek uit
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()  # Gooi een uitzondering voor slechte antwoorden (4xx of 5xx)

                # Parse de HTML-inhoud
                soup = BeautifulSoup(response.text, 'html.parser')

                if store == "ah.nl":
                    # AH: Zoek naar productkaarten met de class 'product-card'
                    products_found = soup.find_all('article', class_=lambda c: c and 'product-card' in c.split())
                    for product_element in products_found:
                        found_name_element = product_element.find(class_=lambda c: c and 'product-name' in c.split())
                        found_name = found_name_element.get_text(strip=True) if found_name_element else ""
                        price_element = product_element.find(class_=lambda c: c and 'price' in c.split())
                        price = price_element.get_text(strip=True) if price_element else "Onbekend"

                        if product_name in found_name.lower():
                            is_one_plus_one = False
                            if "1+1 gratis" in product_element.get_text().lower():
                                is_one_plus_one = True

                            numeric_price = parse_price_to_float(price)

                            if is_one_plus_one and numeric_price != float('inf'):
                                numeric_price /= 2
                                deal_details = "1+1 Gratis"
                            else:
                                deal_details = "Actuele prijs"

                            current_offer = {
                                "productName": found_name,
                                "store": "AH",
                                "price": price,
                                "details": deal_details,
                                "numericPrice": numeric_price
                            }

                            if product_name in best_deals and numeric_price < best_deals[product_name]["numericPrice"]:
                                best_deals[product_name] = current_offer

                elif store == "jumbo.com":
                    # Jumbo: Zoek naar productkaarten met de class 'product-card'
                    products_found = soup.find_all('div', class_=lambda c: c and 'jumbo-product-card' in c.split())
                    for product_element in products_found:
                        found_name_element = product_element.find(class_=lambda c: c and 'jumbo-product-name' in c.split())
                        found_name = found_name_element.get_text(strip=True) if found_name_element else ""
                        price_element = product_element.find(class_=lambda c: c and 'jumbo-price' in c.split())
                        price = price_element.get_text(strip=True) if price_element else "Onbekend"

                        if product_name in found_name.lower():
                            is_one_plus_one = False
                            if "1+1 gratis" in product_element.get_text().lower():
                                is_one_plus_one = True

                            numeric_price = parse_price_to_float(price)

                            if is_one_plus_one and numeric_price != float('inf'):
                                numeric_price /= 2
                                deal_details = "1+1 Gratis"
                            else:
                                deal_details = "Actuele prijs"

                            current_offer = {
                                "productName": found_name,
                                "store": "JUMBO",
                                "price": price,
                                "details": deal_details,
                                "numericPrice": numeric_price
                            }

                            if product_name in best_deals and numeric_price < best_deals[product_name]["numericPrice"]:
                                best_deals[product_name] = current_offer

                elif store == "kruidvat.nl":
                    # Kruidvat: Zoek naar productkaarten en prijzen
                    products_found = soup.find_all('div', class_='product-list-item')
                    for product_element in products_found:
                        found_name_element = product_element.find('div', class_='product-name')
                        found_name = found_name_element.get_text(strip=True) if found_name_element else ""
                        price_element = product_element.find('span', class_='price')
                        price = price_element.get_text(strip=True) if price_element else "Onbekend"

                        if product_name in found_name.lower():
                            numeric_price = parse_price_to_float(price)

                            current_offer = {
                                "productName": found_name,
                                "store": "KRUIDVAT",
                                "price": price,
                                "details": "Actuele prijs",
                                "numericPrice": numeric_price
                            }

                            if product_name in best_deals and numeric_price < best_deals[product_name]["numericPrice"]:
                                best_deals[product_name] = current_offer

                elif store == "lidl.nl":
                    # Lidl: Zoek naar productkaarten en prijzen
                    products_found = soup.find_all('div', class_='s-grid__item')
                    for product_element in products_found:
                        found_name_element = product_element.find('h3', class_='s-title')
                        found_name = found_name_element.get_text(strip=True) if found_name_element else ""
                        price_element = product_element.find('span', class_='price__label')
                        price = price_element.get_text(strip=True) if price_element else "Onbekend"

                        if product_name in found_name.lower():
                            numeric_price = parse_price_to_float(price)

                            current_offer = {
                                "productName": found_name,
                                "store": "LIDL",
                                "price": price,
                                "details": "Actuele prijs",
                                "numericPrice": numeric_price
                            }

                            if product_name in best_deals and numeric_price < best_deals[product_name]["numericPrice"]:
                                best_deals[product_name] = current_offer

            except requests.exceptions.RequestException as e:
                print(f"Kon geen data ophalen van {store}: {e}")
                continue

    # Converteer de beste deals terug naar een lijst
    return list(best_deals.values())

def parse_price_to_float(price_string):
    """
    Converteert een prijsstring (bijv. '€ 1,23') naar een float (bijv. 1.23).
    """
    if not isinstance(price_string, str):
        return float('inf')  # Retourneer oneindigheid voor niet-vergelijkbare prijzen

    # Verwijder valuta symbolen, spaties en vervang de komma door een punt
    clean_price = re.sub(r'[^\d,]+', '', price_string).replace(',', '.')

    try:
        return float(clean_price)
    except ValueError:
        return float('inf') # Retourneer oneindigheid als de conversie mislukt

# Globale variabelen om de aanbiedingen op te slaan
latest_offers = []
last_update_timestamp = ""

def update_offers():
    """Update de globale lijst van aanbiedingen en de tijdstempel."""
    global latest_offers, last_update_timestamp
    print("Bezig met het updaten van aanbiedingen...")
    # Hier kun je de productenlijst uit de database halen
    # Voor nu gebruiken we de hardgecodeerde lijst
    # user_products = [haal_op_uit_database]
    user_products = [{'name': 'Nivea deodorant'}, {'name': 'Lays chips'}]
    latest_offers = get_offers_from_websites(user_products)
    last_update_timestamp = time.strftime("%d-%m-%Y %H:%M:%S")
    print(f"Aanbiedingen zijn bijgewerkt op {last_update_timestamp}.")

# Initialiseer de scheduler
scheduler = BackgroundScheduler()
# Voeg een taak toe die elke dag om 06:00 uur de offers bijwerkt
scheduler.add_job(func=update_offers, trigger='cron', hour=6, minute=0)
# Start de scheduler
scheduler.start()
# Zorg ervoor dat de scheduler netjes afsluit wanneer de app stopt
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def home():
    """Geeft de hoofd index.html template terug."""
    return render_template('index.html')

@app.route('/api/get-offers', methods=['POST'])
def get_offers():
    """
    Retourneert de laatst bijgewerkte aanbiedingen inclusief tijdstempel.
    """
    global latest_offers, last_update_timestamp
    try:
        # data = request.get_json()
        # user_products = data.get('products', [])

        return jsonify({"offers": latest_offers, "timestamp": last_update_timestamp})
    except Exception as e:
        print(f"Fout bij het verwerken van het verzoek: {e}")
        return jsonify({"error": "Ongeldige aanvraag body"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
