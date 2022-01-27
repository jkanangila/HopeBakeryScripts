#############
## IMPORTS ##
#############
##########################################################################
import json
import webbrowser as wb

from orm import MyORM
##########################################################################


#########################
## DEFAULT INFORMATION ##
#########################
##########################################################################
SALES_SITE_ID = {
    1: "Bikanga-1",
    2: "Bikanga-1-Gateaux",
    4: "De-la-paix",
    5: "Rifflard"
}

ID = int(input("Enter sales site id: \nBikanga-1 = 1, \nGateaux = 2, \nDe la paix = 4, \nRueflar = 5: ").strip())

SALES_SITE = SALES_SITE_ID[ID]
# Default pay period i.e. last day of period
# Used if user doesn't specify a pay_period
# format MM
MONTH = '01'
if SALES_SITE == "Bikanga-1-Gateaux":
    DAY = 15
else:
    DAY = 25
DEFAULT_PAY_PERIOD = f"2022-{MONTH}-{DAY}"
BASE_URL = "https://be.kanangila.com/backend/hr/salesagent/"
##########################################################################


#######################
## CLIENTS DATA FILE ##
#######################
##########################################################################
for i in range(500):
    # Open file containing customer's names and IDs
    try:
        with open(f"{ID}.json", 'r') as f:
            _dict = json.load(f)
    except:
        orm = MyORM()
        _dict = orm.retrieve_sales_agents(
            ID
        )
        with open(f"{ID}.json", 'w') as f:
            json.dump(_dict, f)
    ##########################################################################

    #################
    ## USER INPUTS ##
    #################
    ##########################################################################
    PAYMENT_MONTH = input(
        """
        Enter the payment month number (e.g. 01 for January)
        Or enter a list of numbers separated by a comma """ +
        """i.e. (08,07)\n    : """
    )
    CARD_NBR = input("\nEnter sales agent's card number: ")
    ##########################################################################

    ##################
    ## URL FUNCTION ##
    ##################
    ##########################################################################

    def open_url(pay_period, client_id):
        if pay_period == "":
            wb.open_new_tab(
                BASE_URL + f"{client_id}/view/?period={DEFAULT_PAY_PERIOD}"
            )
            return

        # instance where user specifies multiple pay periods
        last_day = DEFAULT_PAY_PERIOD.split('-')[-1]
        ls_periods = pay_period.split(',')

        if len(ls_periods) >= 2:
            links = []

            for period in ls_periods:
                if MONTH == '01' and period in ["12", "11", "10", "09"]:
                    np = f"2021-{period}-{last_day}"
                else:
                    np = f"2022-{period}-{last_day}"
                links.append(
                    BASE_URL + f"{client_id}/view/?period={np}"
                )

            for link in links:
                wb.open_new_tab(link)
        # instance where user specifies signle pay period
        else:
            if MONTH == '01' and period in ["12", "11", "10", "09"]:
                np = f"2021-{pay_period}-{last_day}"
            else:
                np = f"2022-{pay_period}-{last_day}"
            wb.open_new_tab(
                BASE_URL + f"{client_id}/view/?period={np}"
            )
    ##########################################################################

    ##########
    ## MAIN ##
    ##########
    ##########################################################################
    # Open url if user provided a valid card number
    if CARD_NBR.isnumeric() and CARD_NBR in _dict.keys():
        open_url(
            client_id=_dict[CARD_NBR]['id'],
            pay_period=PAYMENT_MONTH
        )
    elif CARD_NBR.isnumeric() and CARD_NBR not in _dict.keys():
        print("Le numero de la carte que vous avez saisis ne correponds a" +
              " aucun client")
    else:
        print("Le numero de la carte ne pas un nombre valide")
    print("Exiting...")
##########################################################################
