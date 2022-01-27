from orm import MyORM
import json


def underline_str_print(_str):
    return (f"{_str}\n{'-'*len(_str)}")


def frame_str_print(_str):
    return (f"\n{'-'*(len(_str) + 4)}\n| {_str} |\n{'-'*(len(_str) + 4)}\n")


##############################################################################
print(underline_str_print("Importing modules.".upper()))
print("     Modules import complete!\n\n")
##############################################################################


##############################################################################
print(underline_str_print("Creating ORM.".upper()))
orm = MyORM()
print("     ORM Created!\n\n")
##############################################################################


##############################################################################
print(underline_str_print("Opening data files.".upper()))
with open('orders.json', 'r') as f:
    orders = json.load(f)

with open('processed_orders.json', 'r') as f:
    processed_orders = json.load(f)
print("     Files Opened!\n\n")
##############################################################################


##############################################################################
print(underline_str_print("Begining iteration over data".upper()))
for data in orders:
    print(frame_str_print(f"{data['date']}"))
    const = {}
    const['is_delivery'] = False
    for key in data.keys():
        if key == "orders":
            continue
        if key == "description":
            const[key] = orm.sales_type[data[key]]
        else:
            const[key] = data[key]

    i = 1
    count = len(data["orders"])
    for order in data["orders"]:
        print(f"{round(i/count, 2)*100} %")
        kwargs = const.copy()

        kwargs['vendeur_id'] = order[0]

        # COMMAND NORMAL
        if kwargs['description'] == 1:
            if len(order) == 2:

                # Command a credit total
                if order[1] < 0:

                    kwargs['command'] = kwargs['credit'] = \
                        float(order[1]*(-1))
                    kwargs['debit'] = float(0)
                # Command en espece
                else:
                    kwargs['command'] = kwargs['debit'] = float(order[1])
                    kwargs['credit'] = float(0)

            # Command a credit partiel
            elif len(order) == 3:
                kwargs['command'] = float(order[2])
                kwargs['debit'] = float(order[1])
                kwargs['credit'] = kwargs['command'] - kwargs['debit']

        # VENSTE SANS COMMISSION
        elif kwargs['description'] == 2:

            kwargs['debit'] = float(order[1])
            kwargs['command'] = round(
                kwargs['debit']*(1 + (1/3)), 1
            )
            kwargs['credit'] = float(0)

        # PAIMENT DE CREDIT
        elif kwargs['description'] == 3:
            kwargs['credit'] = kwargs['command'] = float(0)
            kwargs['debit'] = float(order[1])
        else:
            # TODO else
            pass

        # CONTINUE IF ORDER WAS ALREADY SAVED
        if kwargs in processed_orders:
            continue

        try:
            print(f"    Placing order {kwargs['command']:,.0f}" +
                  f" for customer {kwargs['vendeur_id']}")
            orm.place_order(**kwargs)
            processed_orders.append(kwargs)
            print("     Sucess\n")
        except Exception as e:
            print(e)

        i += 1
##############################################################################


##############################################################################
with open('processed_orders.json', 'w') as f:
    json.dump(processed_orders, f)
##############################################################################
