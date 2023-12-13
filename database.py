from neo4j import GraphDatabase
from neo4j.time import Date
from dateutil.parser import parse
class Database:
	def __init__(self, uri, user, password):
		self.driver = GraphDatabase.driver(uri, auth=(user, password))

	def close(self):
		self.driver.close()

	def run_query(self, query, single = False, **parameters):
		with self.driver.session() as session:
			if not single:
				return session.run(query, **parameters).value()
			else:
				return session.run(query, **parameters).single()

	def get_people_all(self):
		return self.run_query('MATCH (p:Person) RETURN p')

	def get_people_by_gender(self, gender):
		query = f'MATCH (p:Person {{gender: "{gender}"}}) RETURN p'
		return self.run_query(query)

	def get_people_alive(self):
		query = 'MATCH (p:Person) WHERE p.birthDate < date() AND (p.deathDate IS NULL OR p.deathDate > date()) RETURN p'
		return self.run_query(query)

	def get_people_dead(self):
		query = 'MATCH (p:Person) WHERE p.deathDate < date() RETURN p'
		return self.run_query(query)

	def get_people_alone(self):
		query = 'MATCH (p:Person) OPTIONAL MATCH (p)-[m:MARRIED]->() WITH p, m WHERE m IS NULL OR m.marriageEndDate < date() RETURN p'
		return self.run_query(query)

	def get_people_except(self, person_id):
		query = 'MATCH (p:Person) WHERE p.personID <> $id RETURN p'
		return self.run_query(query, id=person_id)
	
	def get_people_by_gender_except(self, gender, person_id):
		query = f'MATCH (p:Person {{gender: "{gender}"}}) where p.personID <> $id RETURN p'
		return self.run_query(query, id=person_id)

	def get_person(self, person_id):
		query = 'MATCH (p:Person) WHERE p.personID = $id RETURN p'
		return self.run_query(query, id=person_id)[0]

	def add_person(self, first_name, last_name, gender, birth_date, death_date):
		query = 'CREATE (p:Person {personID: apoc.create.uuid()})'
		query_set = 'SET'
		parameters = {'firstName': first_name, 'lastName': last_name, 'gender': gender}

		for key, value in [('firstName', first_name), ('lastName', last_name), ('gender', gender)]:
			if value.strip():
				query_set += f' p.{key} = ${key},'
				parameters[key] = value

		for key, date_str in [('birthDate', birth_date), ('deathDate', death_date)]:
			if date_str.strip():
				try:
					date_value = Date.from_native(parse(date_str))
					query_set += f' p.{key} = ${key},'
					parameters[key] = date_value
				except:
					pass

		if query_set != 'SET':
			query += query_set[:-1]

		query += ' RETURN p.personID'
		
		return self.run_query(query, single=True, **parameters)['p.personID']

	def edit_person(self, person_id, first_name, last_name, gender, birth_date, death_date):
		query_set, query_remove = '', ''
		parameters = {'id': person_id, 'firstName': first_name, 'lastName': last_name, 'gender': gender}

		for key, value in [('firstName', first_name), ('lastName', last_name), ('gender', gender)]:
			if value.strip():
				query_set += f' p.{key} = ${key},'
			else:
				query_remove += f' p.{key},'

		for key, date_str in [('birthDate', birth_date), ('deathDate', death_date)]:
			if date_str.strip():
				try:
					date_value = Date.from_native(parse(date_str))
					query_set += f' p.{key} = ${key},'
					parameters[key] = date_value
				except:
					pass
			else:
				query_remove += f' p.{key},'

		if query_set:
			self.run_query(f'MATCH (p:Person {{personID: $id}}) SET {query_set[:-1]}', **parameters)
		if query_remove:
			self.run_query(f'MATCH (p:Person {{personID: $id}}) REMOVE {query_remove[:-1]}', **parameters)

	def delete_person(self, person_id):
		query = 'MATCH (p:Person {personID: $id}) DELETE p'
		self.run_query(query, id=person_id)

	def marry_person(self, person_id, marriage_date, marriage_end_date, other_id):
		query1 = 'MATCH (a:Person {personID: $id}), (b:Person {personID: $otherID}) CREATE (a)-[m:MARRIED {marriageID: apoc.create.uuid()}]->(b)'
		query2 = 'MATCH (a:Person {personID: $id}), (b:Person {personID: $otherID}) CREATE (a)<-[m:MARRIED {marriageID: $marriageID}]-(b)'
		query_set = 'SET'
		parameters = {'id': person_id, 'marriageDate': marriage_date, 'marriageEndDate': marriage_end_date, 'otherID': other_id}

		for key, date_str in [('marriageDate', marriage_date), ('marriageEndDate', marriage_end_date)]:
			if date_str.strip():
				try:
					date_value = Date.from_native(parse(date_str))
					query_set += f' m.{key} = ${key},'
					parameters[key] = date_value
				except:
						pass

		if query_set != 'SET':
			query1 += query_set[:-1] + ' RETURN m.marriageID'
			query2 += query_set[:-1]

		marriage_id = self.run_query(query1, **parameters).single()['m.marriageID']
		self.run_query(query2, marriageID=marriage_id, **parameters)

	def get_marriages(self, person_id):
		query = 'MATCH (:Person {personID: $id})-[m:MARRIED]->(o:Person) RETURN m, o'
		return self.run_query(query, id=person_id)

	def delete_marriage(self, marriage_id):
		query = 'MATCH ()-[m:MARRIED {marriageID: $id}]->() DELETE m'
		self.run_query(query, id=marriage_id)

	def add_relative(self, relationship_type, person_id, other_id):
		query = f'MATCH (a:Person {{personID: $id}}), (b:Person {{personID: $otherID}}) CREATE (a)-[:{relationship_type}]->(b)'
		parameters = {'id': person_id, 'otherID': other_id}

		if not other_id.strip():
			return

		self.run_query(query, **parameters)

	def get_relative(self, relationship_type, person_id):
		query = f'MATCH (:Person {{personID: $id}})-[:{relationship_type}]->(r:Person) RETURN r'

		result = self.run_query(query, id=person_id)
		return result[0] if len(result) > 0 else None

	def delete_relative(self, relationship_type, person_id):
		query = f'MATCH (:Person {{personID: $id}})-[r:{relationship_type}]-() DELETE r'
		self.run_query(query, id=person_id)

	def add_mother(self, person_id, mother_id):
		self.add_relative('MOTHER', person_id, mother_id)

	def get_mother(self, person_id):
		return self.get_relative('MOTHER', person_id)

	def delete_mother(self, person_id):
		self.delete_relative('MOTHER', person_id)

	def add_father(self, person_id, father_id):
		self.add_relative('FATHER', person_id, father_id)

	def get_father(self, person_id):
		return self.get_relative('FATHER', person_id)

	def delete_father(self, person_id):
		self.delete_relative('FATHER', person_id)
