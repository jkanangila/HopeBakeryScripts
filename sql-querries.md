# Retrieve undelivered orders
```sql
select s.date, s.id as "No. Commande", sa.card_number as "No. Carte", 
	   f.first_name as "Vendeur", s.command, s.debit, s.credit, s.is_delivery
from sales_order s
	join hr_abstractbaseaccount f on s.vendeur_id = f.id
	join hr_salesagent sa on s.vendeur_id = sa.abstractbaseaccount_ptr_id
where site_de_vente_id=1  -- change accordingly
	AND is_delivery=false 
	AND date = '2021-05-26' -- change accordingly
```

# Retrieve all orders from a specific sales agent
```sql
select s.date, s.id as "No. Commande", sa.card_number as "No. Carte", 
	   f.first_name as "Vendeur", s.command, s.debit, s.credit, 
	   s.is_delivery
from sales_order s
	join hr_abstractbaseaccount f on s.vendeur_id = f.id
	join hr_salesagent sa on s.vendeur_id = sa.abstractbaseaccount_ptr_id
where site_de_vente_id=2 --change accordingly
    AND sa.card_number = '364' --change accordingly
order by s.date
```

# Retrieve list of agents, number of orders, and sum of orders during a given period
```sql
select vendeur, count(nbr_commande) as nombre_command, sum(nbr_commande) as total_command
from (  
	select concat(sa.card_number, '  -  ', f.first_name, ' ', f.last_name) as vendeur, s.command as nbr_commande
	from hr_abstractbaseaccount f 
		join sales_order s on s.vendeur_id = f.id
		join hr_salesagent sa on s.vendeur_id = sa.abstractbaseaccount_ptr_id
	where site_de_vente_id=2  -- change accordingly
		  AND date >= '2021-06-15' -- change accordingly
	 ) x
group by (vendeur)
order by 3 desc
```

# Retrieve list of agents who have not placed an order after a certain date
```sql
select x.id, x.carte, x.vendeur 
from (
	select f.id, sa.card_number as carte, concat(f.first_name, ' ', f.last_name) as vendeur
	from hr_abstractbaseaccount f 
		join hr_salesagent sa on f.id = sa.abstractbaseaccount_ptr_id
	where sales_site_id=1  -- change accordingly
	) x
	
where x.vendeur not in (
						select x.vendeur
						from (  
							select
								sa.card_number as carte,
								concat(f.first_name, ' ', 
									   f.last_name) as vendeur, s.command as nbr_commande
							from hr_abstractbaseaccount f 
								join sales_order s on s.vendeur_id = f.id
								join hr_salesagent sa on s.vendeur_id = sa.abstractbaseaccount_ptr_id
							where site_de_vente_id=1  -- change accordingly
								  AND date >= '2021-06-25' -- change accordingly
							 ) x
						group by (vendeur)
					)
order by 2  
```

# Update sales agent card_number
```sql
UPDATE hr_salesagent
SET card_number = Null
    
WHERE sales_site_id=1 AND abstractbaseaccount_ptr_id=816
```
