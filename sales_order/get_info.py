from orm import MyORM


orm = MyORM()

SALES_SITE_ID = {
    1: "Bikanga-1",
    2: "Bikanga-1-Gateaux",
    4: "De-la-paix",
    5: "Rifflard"
}

sales_site_id = input("""
Selectionner un site de vente:
    1: "Bikanga-1",
    2: "Bikanga-1-Gateaux",
    4: "De-la-paix",
    5: "Rifflard": 
""")
agents = orm.retrieve_sales_agents(int(sales_site_id))

# agents = orm.retrieve_sales_agents(
#     SALES_SITE_ID["Bikanga-1-Gateaux"]
# )
while True:
    card_number = input("Enter le numero du client: ")
    if card_number in ("quit", "q"):
        orm.close()
        raise StopIteration
    try:
        print(f"\n{agents[int(card_number)]['id']}")
        print((
            f"{agents[int(card_number)]['first_name']}" +
            f" {agents[int(card_number)]['last_name']}"
        ))
        print()
    except KeyError:
        print("\nCe numero n'existe pas")
    except:
        break
