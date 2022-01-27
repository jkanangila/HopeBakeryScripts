import webbrowser
from datetime import datetime


for i in range(10):
    date = input("Enter date in format (YYYY-MM-DD): \n")
    if not date:
        date = datetime.strftime(datetime.today(), "%Y-%m-%d")
    site_de_vente = input("Enter Site de Vente ID: \n")

    webbrowser.open(
        "https://be.kanangila.com/backend/sales/order/?" +
        f"all=&q={date}&site_de_vente__id__exact={site_de_vente}",
        new=2)

print("Exiting...")
