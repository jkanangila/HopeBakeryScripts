# SECTION IMPORTS
import json
import psycopg2

from collections import Counter
from datetime import datetime
import sqlite3
# !SECTION

# ANCHOR DSN
with open("vars.json",'r') as f:
    var = json.load(f)


dsn = f"host={var['DB_HOST']} dbname={var['DB_NAME']} user={var['DB_USER']} password={var['DB_PASSWORD']}"


# SECTION orm
class MyORM(object):

    # ANCHOR __init__
    def __init__(self):
        # cree une connection et un curseur
        self.conn = psycopg2.connect(dsn)
        self.local_conn = sqlite3.connect('local.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        self.local_cur = self.local_conn.cursor()
        self.delivery_date = ""
        self.invalid_data = []

        self.sales_type = {
            "Normal": 1,
            "Vente Sans Commission": 2,
            "Credit Payment": 3
        }

        self.__init__local_db()

    # ANCHOR __init__local_db
    def __init__local_db(self):
        sales_order_table = """
        CREATE TABLE IF NOT EXISTS sales_order (
            id INTEGER PRIMARY KEY,
            carte_no INTEGER NOT NULL,
            client_name VARCHAR NOT NULL,
            vendeur_id INTEGER NOT NULL, 
            site_de_vente_id INTEGER NOT NULL, 
            date DATE DEFAULT CURRENT_DATE, 
            command FLOAT(53) NOT NULL, 
            credit FLOAT(53) NOT NULL,
            debit FLOAT(53) NOT NULL,
            description VARCHAR NOT NULL,
            operateur_id INTEGER NOT NULL,
            is_delivery BIT DEFAULT 0,
            saved_to_remote BIT DEFAULT 0
        );
        """

        operations_delivery = """
        CREATE TABLE IF NOT EXISTS operations_delivery (
            id integer PRIMARY KEY,
            order_id INTEGER NOT NULL,
            delivery_date DATE NOT NULL, 
            created_at DATE NOT NULL, 
            updated_at DATE NOT NULL, 
            delivered_by_id INTEGER NOT NULL,
            saved_to_remote BIT DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES sales_order (id)
        );
        """

        self.local_cur.execute(
                sales_order_table
        )
        self.local_cur.execute(
                operations_delivery
        )
        self.local_conn.commit()

    # ANCHOR data_preprocessing
    def data_preprocessing(self, text):
        """Process text input received from user
        and place data in correct structure for db query
        valid data:
            1. Date OrderId (e.g.: 2021-08-21 24589)
               No need to specify a delivery date from date picker
            2. OrderID --> delivery_date should be specified
            3. Date CardNum CommandAmount (e.g. 2021-08-21 67 4000)
               Specify delivery date
        """
        # Strip text of whitespace and split it based on line breaks
        text = text.strip()
        #   Changing data into a set then back to list removes duplicate
        list_data = list(set(text.split("\n")))
        # Remove whitespaces from each data point
        list_data = [i.strip() for i in list_data]

        # Extract list of valid dates from the list of data
        list_dates = [
            i.split(" ")[0] for i in list_data if self.is_date(i.split(" ")[0])
        ]

        try:
            # Determine delivery date
            self.delivery_date = self.my_counter(list_dates)
        except IndexError:
            pass

        data = []
        for i in list_data:
            pt = i.split(" ")
            # order date and ID
            if self.is_date(pt[0]) and len(pt) == 2:
                data.append({"created_at": pt[0], "order_id": pt[1]})

            # order date, card number, and command amount
            elif self.is_date(pt[0]) and len(pt) == 3:
                data.append(
                    {"created_at": pt[0], "card_number": pt[1], "command": pt[2]}
                )

            # only order ID
            elif len(pt) == 1 and i.isdigit():
                data.append({"order_id": i})

            # invalid data
            else:
                self.invalid_data.append({"invalid-data": i})

        return data

    # ANCHOR execute_query
    def execute_query(self, querry_string, parm=None, verbose=False, cursor="remote"):
        # Execute user querry
        if cursor == "remote":
            self.cur.execute(querry_string, parm)

            if verbose:
                cols = [desc[0] for desc in self.cur.description]  # list of columns
                rows = []
                # append querry results to list
                for row in self.cur:
                    rows.append({i: j for i, j in zip(cols, row)})
                return rows

        elif cursor == "local":
            self.local_cur.execute(querry_string)

            if verbose:
                cols = [desc[0] for desc in self.local_cur.description]  # list of columns
                rows = []
                # append querry results to list
                for row in self.local_cur:
                    rows.append({i: j for i, j in zip(cols, row)})
                return rows

        else:
            raise ValueError(
                "Invalid value for cursor. Valid options are 'remote' and 'local'")

    # ANCHOR close
    def close(self):
        self.cur.close()
        self.local_cur.close()
        self.local_conn.close()
        self.conn.close()

    # ANCHOR my_counter
    @staticmethod
    def my_counter(l):
        """Count items of a list and return the most recurring values"""
        return Counter(l).most_common(1)[0][0]

    # ANCHOR is_date
    @staticmethod
    def is_date(string):
        """
        Returns True if a string can be parsed in datetime format (YYYY-MM-DD),
        False otherwise"""
        try:
            datetime.strptime(string, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    # ANCHOR parse_date
    @staticmethod
    def parse_date(t):
        try:
            return datetime.strftime(t, "%Y-%m-%d")
        except:
            return t

    # ANCHOR qs_1
    @staticmethod
    def qs_1():
        """Create delivery object in operations_delivery table"""
        return """
                INSERT INTO operations_delivery(
                                    delivery_date, 
                                    created_at, 
                                    updated_at, 
                                    delivered_by_id, 
                                    order_id
                                    )
                VALUES (
                        CAST('%(delivery_date)s' AS DATE), 
                        CAST('%(created_at)s' AS DATE), 
                        CAST('%(delivery_date)s' AS DATE), 
                        %(delivered_by_id)s, 
                        %(order_id))
                """

    # ANCHOR qs_2
    @staticmethod
    def qs_2():
        return """
                UPDATE sales_order
                SET is_delivery = true

                WHERE id=%(order_id)s
                """

    # ANCHOR retrieve_order_id
    def retrieve_order_id(self, created_at, card_number, command):
        """retrieve order id knowing the date the order was placed and"""
        qs = f"""select s.id from sales_order s 
                    join hr_abstractbaseaccount f on s.vendeur_id = f.id
                    join hr_salesagent sa on s.vendeur_id = sa.abstractbaseaccount_ptr_id
                    where s.date='%(created_at)s' 
                    and s.command=%(command)s 
                    and sa.card_number=%(card_number)s"""
        try:
            return self.execute_query(
                querry_string=qs,
                parm={
                    'created_at':created_at, 
                    'card_number':card_number, 
                    'command':command
                },
                verbose=True)[0]["id"]
        except:
            self.conn.rollback()
            return False

    # ANCHOR retrieve_created_at
    def retrieve_created_at(self, order_id):
        qs = f"select date from sales_order where id=%(order_id)s"
        try:
            return self.execute_query(
                querry_string=qs,
                parm={'order_id':order_id},
                verbose=True)[0]["date"]
        except:
            self.conn.rollback()
            return False

    # ANCHOR retrieve_sales_agents
    def retrieve_sales_agents(self, sales_site_id):
        "Retrieve list of all sales agents for a given sales site where card numbers are used as keys"
        qs = f"""SELECT f.id, f.first_name, f.last_name, sa.card_number 
                FROM hr_abstractbaseaccount f 
                JOIN hr_salesagent sa ON sa.abstractbaseaccount_ptr_id = f.id 
                WHERE sa.sales_site_id = %(sales_site_id)s
                    AND sa.card_number IS NOT NULL
                ORDER BY sa.card_number"""
        try:
            qr = self.execute_query(
                querry_string=qs,
                parm={'sales_site_id':sales_site_id},
                verbose=True)
            d = {}
            for q in qr:
                cn = q["card_number"]
                del q["card_number"]
                d[cn] = q
            return d
        except:
            self.conn.rollback()
            return False

    # ANCHOR retrieve_daily_orders
    def retrieve_daily_orders(self, sales_site_id):
        """Retrieve all orders placed today"""
        pass

    # ANCHOR retrieve_inactive_agents
    def retrieve_inactive_agents(self, date, sales_site_id):
        "Set card number of specified agents to none"
        qs = f"""
        SELECT x.id, x.carte, x.vendeur 
        FROM (
                -- List of sales agents in a given sales site
	        SELECT f.id, sa.card_number as carte, concat(f.first_name, ' ', f.last_name) as vendeur
	        FROM hr_abstractbaseaccount f 
		        JOIN hr_salesagent sa ON f.id = sa.abstractbaseaccount_ptr_id
	        WHERE sales_site_id=%(sales_site_id)s
	    ) x
	
        WHERE x.carte IS NOT NULL AND
            x.vendeur NOT IN (
                -- List of sales agents who have placed an order after specified date
		SELECT x.vendeur
		FROM (  
		        SELECT sa.card_number as carte,concat(f.first_name, ' ', 
				f.last_name) as vendeur, s.command as nbr_commande
			FROM hr_abstractbaseaccount f 
			    JOIN sales_order s ON s.vendeur_id = f.id
			    JOIN hr_salesagent sa ON s.vendeur_id = sa.abstractbaseaccount_ptr_id
			WHERE site_de_vente_id=%(sales_site_id)s
				AND date >= '%(date)s'
		    ) x
	    GROUP BY (vendeur)
		            )
        ORDER BY 2
        """
        return self.execute_query(
            querry_string=qs,
            parm={'date':date, 'sales_site_id':sales_site_id},
            verbose=True)

    # ANCHOR archive_inactive_agents
    def archive_inactive_agents(self, date, sales_site_id):
        "Return list of sales agents who were inactive during a time period"

        print("retrieving list of inactive agents")
        data = self.retrieve_inactive_agents(date=date, sales_site_id=sales_site_id)

        print(f"{len(data)} agents retrieved. Begining archiving...")
        for agent in data:
            print(f"\nPreparing to archive {agent['vendeur']}")
            qs = f"""
            UPDATE hr_salesagent
            SET card_number = Null
    
            WHERE sales_site_id = %(sales_site_id)s 
            AND abstractbaseaccount_ptr_id = %(acc_id)s
            """
            self.execute_query(
                query_string=qs,
                parm={
                    'sales_site_id':sales_site_id,
                    'acc_id':agent['id']
                    },
                verbose=True)
            print(f"Archived {agent['vendeur']}")
            #sleep(2)
        self.conn.commit()  # <--- Don't forget to commit
        return data

    # ANCHOR retrieve_archived_agents
    def retrieve_archived_agents(self, sales_site_id):
        "Retrieve list of all sales agents for a given sales site where ids are used as keys"
        qs = f"""SELECT f.id, f.first_name, f.last_name 
                FROM hr_abstractbaseaccount f 
                JOIN hr_salesagent sa ON sa.abstractbaseaccount_ptr_id = f.id 
                WHERE sa.sales_site_id = %(sales_site_id)s
                    AND sa.card_number IS NULL
                ORDER BY f.first_name"""
        try:
            qr = self.execute_query(
                querry_string=qs,
                parm={'sales_site_id':sales_site_id},
                verbose=True)
            d = {}
            for q in qr:
                cn = q["id"]
                del q["id"]
                d[cn] = q
            return d
        except:
            self.conn.rollback()
            return False

    # ANCHOR retrieve_staff_users
    def retrieve_staff_users(self):
        qs = """SELECT CONCAT(first_name, ' ' ,last_name) as user 
                FROM auth_user 
                WHERE is_staff=true"""
        users = self.execute_query(querry_string=qs, verbose=True)
        return sorted([i['user'] for i in users if i['user'] != ' '])

    # ANCHOR retrieve_session_info
    def retrieve_session_info(self, user):
        qs = """SELECT * 
            FROM (SELECT CONCAT(u.first_name, ' ' , u.last_name) AS user, 
                         u.id AS user_id, u.is_superuser, 
                         s.default_sales_site_id AS sales_site_id, 
                        
                  FROM auth_user u
                    JOIN settings_settings s ON u.id = s.user_id
                    JOIN operations_operationsite o ON s.default_sales_site_id = o.id
                  WHERE is_staff=true) x 
            WHERE x.user=%(user)s"""

        return self.execute_query(querry_string=qs, parm={"user":user}, verbose=True)

    # ANCHOR place_order
    def place_order(
            self, vendeur_id, site_de_vente_id, date, 
            command, debit, credit,  description,
            operateur_id,is_delivery, cursor="remote",
            created_at=datetime.now().replace(microsecond=0),
            updated_at=datetime.now().replace(microsecond=0),
            carte_no=None, client_name=None
                            ):
        if cursor == "remote":
            qs = """
            INSERT INTO sales_order(
                                vendeur_id, 
                                site_de_vente_id, 
                                date, 
                                command, 
                                credit,
                                debit,
                                description,
                                operateur_id,
                                is_delivery,
                                created_at,
                                updated_at
                            )
            VALUES (
                    %(vendeur_id)s,
                    %(site_de_vente_id)s,
                    CAST(%(date)s AS DATE),
                    %(command)s,
                    %(credit)s,
                    %(debit)s,
                    %(description)s,
                    %(operateur_id)s,
                    CAST(%(is_delivery)s AS BOOLEAN),
                    %(created_at)s,
                    %(updated_at)s
                    )
            RETURNING id
            """
            try:
                self.execute_query(
                    querry_string=qs,
                    parm={
                        'vendeur_id': vendeur_id, 
                        'site_de_vente_id': site_de_vente_id, 
                        'date': date, 
                        'command': command,
                        'debit': debit, 
                        'credit': credit,
                        'description': description,
                        'operateur_id': operateur_id,
                        'is_delivery': is_delivery,
                        'created_at': created_at,
                        'updated_at': updated_at
                    },
                    cursor=cursor
                )
                self.conn.commit()
                return self.cur.fetchone()[0]
            except Exception as e:
                self.conn.rollback()
                return e

        elif cursor == "local":
            try:
                qs = f"""
                INSERT INTO sales_order(
                                    carte_no,
                                    client_name,
                                    vendeur_id, 
                                    site_de_vente_id, 
                                    date, 
                                    command, 
                                    credit,
                                    debit,
                                    description,
                                    operateur_id,
                                    is_delivery,
                                    saved_to_remote)
                VALUES ({carte_no},
                        '{client_name}',
                        {vendeur_id},
                        {site_de_vente_id},
                        {date},
                        {command},
                        {credit},
                        {debit},
                        '{description}',
                        {operateur_id},
                        {is_delivery},
                        false)
            """
                self.local_cur.execute(qs)
                self.local_conn.commit()

                return self.local_cur.lastrowid
            except Exception as e:
                self.local_conn.rollback()
                return e

    # ANCHOR data_base_schema
    def data_base_schema(self):
        qs = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        return sorted([i['table_name'] for i in self.execute_query(qs, verbose=True)])

    # ANCHOR find_duplicates
    def find_duplicates(self, sales_site_id=2):
        qs = """
            SELECT x.id, x.vendeur
            FROM (
                SELECT  f.id, concat(f.first_name, ' ', f.last_name) as vendeur
                FROM 
                    hr_abstractbaseaccount f 
                JOIN 
                    hr_salesagent sa ON f.id = sa.abstractbaseaccount_ptr_id
                WHERE 
                    sales_site_id=%(sales_site_id)s
            ) x
            JOIN (
                SELECT 
                    concat(f.first_name, ' ', f.last_name) as vendeur, COUNT(*)
                FROM 
                    hr_abstractbaseaccount f 
                JOIN 
                    hr_salesagent sa ON f.id = sa.abstractbaseaccount_ptr_id
                WHERE 
                    sales_site_id=%(sales_site_id)s 
                GROUP 
                    BY vendeur
                HAVING 
                    COUNT(*) > 1
            ) y
            ON x.vendeur = y.vendeur
            ORDER BY x.vendeur
            """
        try:
            return self.execute_query(
                querry_string=qs,
                parm={'sales_site_id':sales_site_id},
                verbose=True)
        except Exception as e:
            self.conn.rollback()
            return e

    def retrieve_order_details(self, order_id):
        # retrieve order details using orderID
        qs = "SELECT command, debit, credit FROM sales_order WHERE id=%(order_id)s"

        try:
            return self.execute_query(
                querry_string=qs,
                parm={'order_id':order_id},
                verbose=True)
        except Exception as e:
            self.conn.rollback()
            return e

    def retrieve_all_orders_placed_by_sales_agent(self, vendeur_id):
        qs = """
        SELECT  vendeur_id, site_de_vente_id, date, command, credit, debit
                description, operateur_id, is_delivery, created_at, updated_at
        FROM sales_order
        WHERE vendeur_id = vendeur_id
                """

# !SECTION

# Get IDs of all orders placed by vendor 1
qs = """
SELECT id FROM sales_order WHERE site_de_vente_id = 3
"""

qs = """
UPDATE sales_order
SET vendeur_id = 182
WHERE id = 52169
"""