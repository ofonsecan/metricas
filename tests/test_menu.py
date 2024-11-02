import json
import hashlib
from unittest import TestCase
from faker import Faker
from faker.generator import random
from datetime import datetime, timedelta
from sqlalchemy import and_

from modelos import db, Usuario, Administrador, Restaurante, Ingrediente, Receta, RecetaIngrediente, Chef, Menu, MenuReceta
from app import app
from vistas import VistaMenu


class TestMenu(TestCase):
    def setUp(self):
        self.data_factory = Faker()
        self.client = app.test_client()

        nombre_usuario = "admin_" + self.data_factory.name()
        contrasena = "admin_" + self.data_factory.word()
        contrasena_encriptada = hashlib.md5(contrasena.encode("utf-8")).hexdigest()
        admin = Administrador(usuario=nombre_usuario, contrasena=contrasena_encriptada)
        db.session.add(admin)
        db.session.commit()

        usuario_login = {"usuario": nombre_usuario, "contrasena": contrasena}
        solicitud_login = self.client.post(
            "/login",
            data=json.dumps(usuario_login),
            headers={"Content-Type": "application/json"},
        )

        respuesta_login = json.loads(solicitud_login.get_data())
        self.token_admin = respuesta_login["token"]
        self.admin_id = respuesta_login["id"]

        restaurante = Restaurante(
            nombre = self.data_factory.name(),
            direccion= self.data_factory.address(),
            telefono=self.data_factory.phone_number(),
            redes_sociales=self.data_factory.url(),
            horarios_abre=self.data_factory.sentence(),
            tipo_comida=self.data_factory.word(),
            aplicaciones_asociadas=self.data_factory.sentence(),
            opciones_servicio=self.data_factory.word(),
            administrador_id= admin.id
        )
        
        db.session.add(restaurante)
        db.session.commit()
        
        self.nombre_ingrediente = self.data_factory.word()

        ingrediente = Ingrediente(
            nombre=self.nombre_ingrediente,
            unidad=self.data_factory.word(),
            costo=100,
            calorias=random.randint(1, 1000),
            sitio=self.data_factory.word(),
            administrador_id=admin.id
        )
        db.session.add(ingrediente)
        db.session.commit()

        receta = Receta(
            nombre=self.data_factory.sentence(nb_words=3),
            duracion=random.randint(1, 1000),
            porcion= 5,
            preparacion=self.data_factory.paragraph(nb_sentences=3),
            usuario=admin.id,
            ingredientes = [RecetaIngrediente(cantidad=1,ingrediente=ingrediente.id)]
        )
        db.session.add(receta)
        db.session.commit()
        
        self.restaurantes_creados = [restaurante]
        self.ingredientes_creados = [ingrediente]
        self.recetas_creadas = [receta]
        self.menus_creadas = []
        self.menu_receta_creadas = []

        nombre_chef = "chef_" + self.data_factory.name()
        contrasena_chef = "chef_" + self.data_factory.word()
        contrasena_encriptada_chef = hashlib.md5(contrasena_chef.encode("utf-8")).hexdigest()
        chef = Chef(usuario=nombre_chef, contrasena=contrasena_encriptada_chef, nombre="chef", restaurante_id= restaurante.id)
        db.session.add(chef)
        db.session.commit()

        chef_login = {"usuario": nombre_chef, "contrasena": contrasena_chef}

        solicitud_login = self.client.post(
            "/login",
            data=json.dumps(chef_login),
            headers={"Content-Type": "application/json"},
        )

        respuesta_login = json.loads(solicitud_login.get_data())

        self.token_chef = respuesta_login["token"]
        self.chef_id = respuesta_login["id"]

    def test_validacion_menu_fechas_viejas(self):
        data = {
            "nombre": "Test Menu",
            "descripcion": "Test Description",
            "fecha_inicio": "2023-09-13 10:00",
            "fecha_fin": "2023-09-14 12:00",
            "recetas": [
                {"numero_personas": 2, "receta": 1},
                {"numero_personas": 4, "receta": 2},
            ],
            "restaurante": 1
        }
        
        vista_menu = VistaMenu()

        response = vista_menu._validacion_fechas(data, data["restaurante"])
        response_status_code = response[1]
        response_data = response[0]  # Get the response data directly

        self.assertEqual(response_status_code, 400)
        self.assertEqual(response_data["mensaje"], "Las fechas deben ser mayores que la fecha actual")
        

    def test_validacion_menu_fechas_mayor(self):
        data = {
            "nombre": "Test Menu",
            "descripcion": "Test Description",
            "fecha_inicio": "2023-09-20 10:00",
            "fecha_fin": "2023-09-14 12:00",
            "recetas": [
                {"numero_personas": 2, "receta": 1},
                {"numero_personas": 4, "receta": 2},
            ],
            "restaurante": 1
        }
        
        vista_menu = VistaMenu()

        response = vista_menu._validacion_fechas(data, data["restaurante"])
        response_status_code = response[1]
        response_data = response[0]  # Get the response data directly

        self.assertEqual(response_status_code, 400)
        self.assertEqual(response_data["mensaje"], "La fecha de inicio no puede ser mayor que la fecha de fin")

    def test_validacion_menu_nombre_inválido(self):
        data = {
            "nombre": "T",
            "descripcion": "Test Description",
            "fecha_inicio": "2023-09-20 10:00",
            "fecha_fin": "2023-09-14 12:00",
            "recetas": [
                {"numero_personas": 2, "receta": 1},
                {"numero_personas": 4, "receta": 2},
            ],
            "restaurante": 1
        }
        
        vista_menu = VistaMenu()

        response = vista_menu._validacion_menu(data)
        response_status_code = response[1]
        response_data = response[0]  # Get the response data directly

        self.assertEqual(response_status_code, 400)
        self.assertEqual(response_data["mensaje"], "Nombre inválido, debe tener entre 2 y 200 caracteres")

    def test_validacion_menu_descripcion_inválido(self):
        data = {
            "nombre": "Test",
            "descripcion": "",
            "fecha_inicio": "2023-09-20 10:00",
            "fecha_fin": "2023-09-14 12:00",
            "recetas": [
                {"numero_personas": 2, "receta": 1},
                {"numero_personas": 4, "receta": 2},
            ],
            "restaurante": 1
        }
        
        vista_menu = VistaMenu()

        response = vista_menu._validacion_menu(data)
        response_status_code = response[1]
        response_data = response[0]  # Get the response data directly

        self.assertEqual(response_status_code, 400)
        self.assertEqual(response_data["mensaje"], "Datos inválidos")

    def test_crear_menu(self):

        current_datetime = datetime.now()
        fecha_inicio = current_datetime + timedelta(days=2)
        fecha_fin = current_datetime + timedelta(days=5)

        # Format the dates as strings
        fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d %H:%M")
        fecha_fin_str = fecha_fin.strftime("%Y-%m-%d %H:%M")

        data = {
            "nombre": "Test Menu 1",
            "descripcion": "Test Description",
            "fecha_inicio": fecha_inicio_str,
            "fecha_fin": fecha_fin_str,
            "recetas": [
                {"numero_personas": 2, "receta": self.recetas_creadas[0].id},
            ],
            "restaurante": self.restaurantes_creados[0].id
        }

        endpoint_chefs = "/menu"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.token_admin),
        }

        resultado_nuevo_menu = self.client.post(endpoint_chefs, data=json.dumps(data), headers=headers)

        menu = Menu.query.filter_by(nombre="Test Menu 1").first()
        self.menus_creadas.append(menu)

        menu_receta = MenuReceta.query.filter(and_(MenuReceta.receta == self.recetas_creadas[0].id, MenuReceta.receta == self.menus_creadas[0].id)).first()
        self.menu_receta_creadas.append(menu_receta)

        self.assertEqual(resultado_nuevo_menu.status_code, 201)



    def test_listar_menus_por_restaurante(self):
        #Generar 10 menus con datos aleatorios
        for i in range(0,10):
            #Crear los datos del menu
            nombre_nuevo_menu = self.data_factory.name()
            if len(nombre_nuevo_menu) > 200:
                nombre_nuevo_menu = nombre_nuevo_menu[:197] + "..."
            nombre_nuevo_menu = self.data_factory.user_name()
            if len(nombre_nuevo_menu) > 200:
                nombre_nuevo_menu = nombre_nuevo_menu[:197] + "..."

            descripcion_nuevo_menu = self.data_factory.text(max_nb_chars=2000)
            fecha_inicio_nuevo_menu = self.data_factory.date_time()
            fecha_fin_nuevo_menu = self.data_factory.date_time()

            #Crear el menu con los datos originales para obtener su id
            menu = Menu(
                nombre = nombre_nuevo_menu,
                fecha_inicio = fecha_inicio_nuevo_menu,
                fecha_fin = fecha_fin_nuevo_menu,
                descripcion = descripcion_nuevo_menu,
                usuario_id = self.admin_id,
                restaurante_id = self.restaurantes_creados[0].id,
                recetas = []
            )

            db.session.add(menu)
            db.session.commit()
            self.menus_creadas.append(menu)

        #Definir endpoint, encabezados y hacer el llamado
        endpoint_menus = "/menus/" + str(self.restaurantes_creados[0].id)
        headers = {'Content-Type': 'application/json', "Authorization": "Bearer {}".format(self.token_admin)}

        resultado_consulta_menu = self.client.get(endpoint_menus, headers=headers)

        #Obtener los datos de respuesta y dejarlos un objeto json
        datos_respuesta = json.loads(resultado_consulta_menu.get_data())

        #Verificar que el llamado fue exitoso
        self.assertEqual(resultado_consulta_menu.status_code, 200)

        #Verificar los menus creados con sus datos
        for menu in datos_respuesta:
            for menu_creado in self.menus_creadas:
                if menu['id'] == str(menu_creado.id):
                    self.assertEqual(menu['nombre'], menu_creado.nombre)
                    self.assertEqual(menu['fecha_inicio'], menu_creado.fecha_inicio.strftime('%d/%m/%Y %H:%M'))
                    self.assertEqual(menu['fecha_fin'], menu_creado.fecha_fin.strftime('%d/%m/%Y %H:%M'))
                    self.assertEqual(menu['restaurante_id'], menu_creado.restaurante_id)


    def test_listar_menus_chefs(self):
        #Generar 10 menus con datos aleatorios
        for i in range(0,10):
            #Crear los datos del menu
            nombre_nuevo_menu = self.data_factory.name()
            if len(nombre_nuevo_menu) > 200:
                nombre_nuevo_menu = nombre_nuevo_menu[:197] + "..."
            nombre_nuevo_menu = self.data_factory.user_name()
            if len(nombre_nuevo_menu) > 200:
                nombre_nuevo_menu = nombre_nuevo_menu[:197] + "..."

            descripcion_nuevo_menu = self.data_factory.text(max_nb_chars=2000)
            fecha_inicio_nuevo_menu = self.data_factory.date_time()
            fecha_fin_nuevo_menu = self.data_factory.date_time()

            #Crear el menu con los datos originales para obtener su id
            menu = Menu(
                nombre = nombre_nuevo_menu,
                fecha_inicio = fecha_inicio_nuevo_menu,
                fecha_fin = fecha_fin_nuevo_menu,
                descripcion = descripcion_nuevo_menu,
                usuario_id = self.chef_id,
                restaurante_id = self.restaurantes_creados[0].id,
                recetas = []
            )

            db.session.add(menu)
            db.session.commit()
            self.menus_creadas.append(menu)

        #Definir endpoint, encabezados y hacer el llamado
        endpoint_menus = "/menus"
        headers = {'Content-Type': 'application/json', "Authorization": "Bearer {}".format(self.token_chef)}

        resultado_consulta_menu = self.client.get(endpoint_menus, headers=headers)

        #Obtener los datos de respuesta y dejarlos un objeto json
        datos_respuesta = json.loads(resultado_consulta_menu.get_data())

        #Verificar que el llamado fue exitoso
        self.assertEqual(resultado_consulta_menu.status_code, 200)

        #Verificar los menus creados con sus datos
        for menu in datos_respuesta:
            for menu_creado in self.menus_creadas:
                if menu['id'] == str(menu_creado.id):
                    self.assertEqual(menu['nombre'], menu_creado.nombre)
                    self.assertEqual(menu['fecha_inicio'], menu_creado.fecha_inicio.strftime('%d/%m/%Y %H:%M'))
                    self.assertEqual(menu['fecha_fin'], menu_creado.fecha_fin.strftime('%d/%m/%Y %H:%M'))
                    self.assertEqual(menu['restaurante_id'], menu_creado.restaurante_id)
   
    def test_reporte_compra(self):
        data = {
            "recetas": [
                {"numero_personas": 20, "receta": self.recetas_creadas[0].id}
            ]
        }

        endpoint_chefs = "/reporte"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.token_admin),
        }

        resultado_reporte = self.client.post(endpoint_chefs, data=json.dumps(data), headers=headers)
        resultado_json = json.loads(resultado_reporte.get_data())
        ingredientes_receta = resultado_json["ingredientes_receta"]

        ingredientes_resultado = resultado_json["mensaje"]
        self.assertEqual(ingredientes_resultado, "Cálculo correcto")
        self.assertEqual(ingredientes_receta[self.nombre_ingrediente]["cantidad"], 4)

    def test_reporte_compra_receta_inexistente(self):
        data = {
            "recetas": [
                {"numero_personas": 20, "receta": 500000}
            ]
        }

        endpoint_chefs = "/reporte"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.token_admin),
        }

        resultado_reporte = self.client.post(endpoint_chefs, data=json.dumps(data), headers=headers)
        self.assertEqual(resultado_reporte.status_code, 400)

    
    def tearDown(self):

        for receta_creada in self.recetas_creadas:
            receta = Receta.query.get(receta_creada.id)
            db.session.delete(receta)
            db.session.commit()

        for menu_receta_creadas in self.menu_receta_creadas:
            menu_receta = MenuReceta.query.get(menu_receta_creadas.id)
            db.session.delete(menu_receta)
            db.session.commit()

        for menu_creado in self.menus_creadas:
            menu = Menu.query.get(menu_creado.id)
            db.session.delete(menu)
            db.session.commit()
       
        for restaurante_creado in self.restaurantes_creados:
            restaurante = Restaurante.query.get(restaurante_creado.id)
            db.session.delete(restaurante)
            db.session.commit()
    
        admin = Administrador.query.get(self.admin_id)
        db.session.delete(admin)
        db.session.commit()
        
        chef = Chef.query.get(self.chef_id)
        db.session.delete(chef)
        db.session.commit()
