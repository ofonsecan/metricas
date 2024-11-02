import json
import hashlib
from unittest import TestCase

from faker import Faker
from modelos import db, Usuario, Chef, Restaurante, Administrador

from app import app


class TestChef(TestCase):
    def setUp(self):
        self.data_factory = Faker()
        self.client = app.test_client()

        nombre_usuario = "test_" + self.data_factory.name()
        contrasena = "T1$" + self.data_factory.word()
        contrasena_encriptada = hashlib.md5(contrasena.encode("utf-8")).hexdigest()

        # Crear el usuario para identificarse en la aplicación
        usuario_nuevo = Administrador(
            usuario=nombre_usuario, contrasena=contrasena_encriptada
        )
        db.session.add(usuario_nuevo)
        db.session.commit()

        usuario_login = {"usuario": nombre_usuario, "contrasena": contrasena}

        solicitud_login = self.client.post(
            "/login",
            data=json.dumps(usuario_login),
            headers={"Content-Type": "application/json"},
        )

        respuesta_login = json.loads(solicitud_login.get_data())

        self.token = respuesta_login["token"]
        self.usuario_id = respuesta_login["id"]

        self.chefs_creados = []

        restaurante = Restaurante(
            nombre="Restaurante Ejemplo",
            direccion="Ejemplo Calle 123",
            telefono="1234567890",
            administrador_id=self.usuario_id,
        )

        db.session.add(restaurante)
        db.session.commit()

        self.restaurante_creado = restaurante

    def tearDown(self):
        for chef_creado in self.chefs_creados:
            chef = Chef.query.get(chef_creado.id)
            db.session.delete(chef)
            db.session.commit()

        if self.restaurante_creado:
            restaurante = Restaurante.query.get(self.restaurante_creado.id)
            db.session.delete(restaurante)
            db.session.commit()

        usuario_login = Administrador.query.get(self.usuario_id)
        db.session.delete(usuario_login)
        db.session.commit()

    def test_crear_chef(self):
        nuevo_chef = {
            "nombre": "Chef 1",
            "usuario": "chef_1",
            "contrasena": hashlib.md5("contrasena".encode("utf-8")).hexdigest(),
            "restaurante_id": self.restaurante_creado.id,
        }

        endpoint_chefs = "/chefs"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.token),
        }

        resultado_nuevo_chef = self.client.post(
            endpoint_chefs, data=json.dumps(nuevo_chef), headers=headers
        )

        self.assertEqual(resultado_nuevo_chef.status_code, 201)
        datos_respuesta = json.loads(resultado_nuevo_chef.get_data())
        self.assertEqual(datos_respuesta, {"message": "Chef creado exitosamente"})

        chef_creado = Chef.query.filter_by(usuario="chef_1").first()
        self.chefs_creados.append(chef_creado)

    def test_crear_chef_Longitud_Incorrecta(self):
 
        nombre_usuario_largo = "a" * 51

        nuevo_chef = {
            "nombre": "Chef 1",
            "usuario": nombre_usuario_largo,
            "contrasena": hashlib.md5("contrasena".encode("utf-8")).hexdigest(),
            "restaurante_id": self.restaurante_creado.id,
        }

        endpoint_chefs = "/chefs"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.token),
        }

        resultado_nuevo_chef = self.client.post(
            endpoint_chefs, data=json.dumps(nuevo_chef), headers=headers
        )

        self.assertEqual(resultado_nuevo_chef.status_code, 400)

    def test_usuario_existente(self):
        chef_existente = Chef(
            nombre="Chef Existente",
            usuario="chef_Existente",
            contrasena=hashlib.md5("contrasena".encode("utf-8")).hexdigest(),
            restaurante=self.restaurante_creado,
        )

        db.session.add(chef_existente)
        db.session.commit()
        self.chefs_creados.append(chef_existente)

        nuevo_chef = {
            "nombre": "Nuevo Chef",
            "usuario": "chef_Existente",
            "contrasena": hashlib.md5("contrasena".encode("utf-8")).hexdigest(),
            "restaurante_id": self.restaurante_creado.id,
        }

        endpoint_chefs = "/chefs"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.token),
        }

        resultado_nuevo_chef = self.client.post(
            endpoint_chefs, data=json.dumps(nuevo_chef), headers=headers
        )

        self.assertEqual(resultado_nuevo_chef.status_code, 400)
        datos_respuesta = json.loads(resultado_nuevo_chef.get_data())
        self.assertEqual(datos_respuesta, {"message": "El usuario ya existe"})


    def test_listar_chefs(self):
        #Generar 10 chefs con datos aleatorios
        for i in range(0,10):
            #Crear los datos del chef
            nombre_nuevo_chef = self.data_factory.name()
            if len(nombre_nuevo_chef) > 50:
                nombre_nuevo_chef = nombre_nuevo_chef[:47] + "..."
            usuario_nuevo_chef = self.data_factory.user_name()
            if len(usuario_nuevo_chef) > 50:
                usuario_nuevo_chef = usuario_nuevo_chef[:47] + "..."

            #Crear el chef con los datos originales para obtener su id
            chef = Chef(
                nombre = nombre_nuevo_chef,
                usuario = usuario_nuevo_chef,
                contrasena = hashlib.md5(self.data_factory.password().encode('utf-8')).hexdigest(),
                restaurante = self.restaurante_creado
            )

            db.session.add(chef)
            db.session.commit()
            self.chefs_creados.append(chef)

        #Definir endpoint, encabezados y hacer el llamado
        endpoint_chefs = "/chefs/" + str(self.restaurante_creado.id)
        headers = {'Content-Type': 'application/json', "Authorization": "Bearer {}".format(self.token)}

        resultado_consulta_chef = self.client.get(endpoint_chefs, headers=headers)

        #Obtener los datos de respuesta y dejarlos un objeto json
        datos_respuesta = json.loads(resultado_consulta_chef.get_data())

        #Verificar que el llamado fue exitoso
        self.assertEqual(resultado_consulta_chef.status_code, 200)

        #Verificar los chefs creados con sus datos
        for chef in datos_respuesta:
            for chef_creado in self.chefs_creados:
                if chef['id'] == str(chef_creado.id):
                    self.assertEqual(chef['nombre'], chef_creado.nombre)
                    self.assertEqual(chef['restaurante_id'], chef_creado.restaurante.id)
                    self.assertEqual(chef['id'], chef_creado.id)