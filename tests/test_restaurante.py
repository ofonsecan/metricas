import json
import hashlib
from unittest import TestCase

from faker import Faker
from modelos import db, Usuario, Administrador, Restaurante
from app import app


class TestRestaurante(TestCase):
    def setUp(self):
        self.data_factory = Faker()
        self.client = app.test_client()

        nombre_usuario = "test_" + self.data_factory.name()
        contrasena = "T1$" + self.data_factory.word()
        contrasena_encriptada = hashlib.md5(contrasena.encode("utf-8")).hexdigest()

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

        self.restaurantes_creados = []

    def tearDown(self):
        for restaurante_creado in self.restaurantes_creados:
            restaurante = Restaurante.query.get(restaurante_creado.id)
            db.session.delete(restaurante)
            db.session.commit()

        usuario_login = Administrador.query.get(self.usuario_id)
        db.session.delete(usuario_login)
        db.session.commit()

    def _get_auth_headers(self, without_token=False):
        headers = {
            "Content-Type": "application/json",
        }
        if not without_token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def test_crear_restaurante(self):
        nuevo_restaurante = {
            "nombre": "Restaurante Ejemplo",
            "direccion": "Direccion Ejemplo",
            "telefono": "1234567890",
            "redes_sociales": "Facebook: Ejemplo",
            "horarios_abre": "Lunes a Viernes 9am a 9pm",
            "tipo_comida": "Comida rápida",
            "aplicaciones_asociadas": "UberEats, Rappi",
            "opciones_servicio": "Delivery",
        }

        endpoint_restaurantes = "/restaurante"

        resultado_nuevo_restaurante = self.client.post(
            endpoint_restaurantes,
            data=json.dumps(nuevo_restaurante),
            headers=self._get_auth_headers(),
        )

        self.assertEqual(resultado_nuevo_restaurante.status_code, 201)
        datos_respuesta = json.loads(resultado_nuevo_restaurante.get_data())
        self.assertEqual(datos_respuesta["message"], "Restaurante creado exitosamente")

        restaurante_creado = Restaurante.query.filter_by(
            nombre="Restaurante Ejemplo"
        ).first()
        self.restaurantes_creados.append(restaurante_creado)

    def test_restaurante_existente(self):
        restaurante_existente = Restaurante(
            nombre="Restaurante Duplicado",
            direccion="Direccion Ejemplo",
            telefono="1234567890",
            administrador_id=self.usuario_id,
        )

        db.session.add(restaurante_existente)
        db.session.commit()
        self.restaurantes_creados.append(restaurante_existente)

        nuevo_restaurante = {
            "nombre": "Restaurante Duplicado",
            "direccion": "Direccion Ejemplo",
            "telefono": "1234567890",
        }

        endpoint_restaurantes = "/restaurante"

        resultado_nuevo_restaurante = self.client.post(
            endpoint_restaurantes,
            data=json.dumps(nuevo_restaurante),
            headers=self._get_auth_headers(),
        )

        self.assertEqual(resultado_nuevo_restaurante.status_code, 400)
        datos_respuesta = json.loads(resultado_nuevo_restaurante.get_data())
        self.assertEqual(
            datos_respuesta, {"message": "El restaurante ya existe con ese nombre."}
        )

    def test_listar_restaurantes(self):
        for i in range(10):
            restaurante = Restaurante(
                nombre=self.data_factory.name(),
                direccion="Direccion Ejemplo",
                telefono="1234567890",
                administrador_id=self.usuario_id,
            )

            db.session.add(restaurante)
            db.session.commit()
            self.restaurantes_creados.append(restaurante)

        endpoint_restaurantes = f"/restaurantes/{self.usuario_id}"

        resultados_restaurantes = self.client.get(
            endpoint_restaurantes, headers=self._get_auth_headers()
        )
        print(len(json.loads(resultados_restaurantes.get_data())))
        self.assertEqual(10, len(json.loads(resultados_restaurantes.get_data())))

    def test_listar_restaurantes_alfabeticamente(self):
        restaurantes_prueba = []
        for i in range(5):
            restaurante = Restaurante(
                nombre=self.data_factory.name(),
                direccion="Direccion Ejemplo",
                telefono="1234567890",
                administrador_id=self.usuario_id,
            )

            db.session.add(restaurante)
            db.session.commit()
            restaurantes_prueba.append(restaurante)
            self.restaurantes_creados.append(restaurante)

        restaurantes_prueba.sort(key=lambda restaurante: restaurante.nombre)

        endpoint_restaurantes = f"/restaurantes/{self.usuario_id}"

        resultados_restaurantes = self.client.get(
            endpoint_restaurantes, headers=self._get_auth_headers()
        )
        restaurantes_listados = json.loads(resultados_restaurantes.get_data())

        print(restaurantes_listados[0])
        for i in range(5):
            self.assertEqual(
                restaurantes_prueba[i].nombre, restaurantes_listados[i]["nombre"]
            )

    def test_editar_restaurante(self):
        # 1. Crear un restaurante de prueba.
        restaurante_prueba = Restaurante(
            nombre="Restaurante Original",
            direccion="Direccion Original",
            telefono="1234567890",
            redes_sociales="Facebook: Original",
            horarios_abre="Lunes a Viernes 9am a 9pm",
            tipo_comida="Comida original",
            aplicaciones_asociadas="OriginalEats",
            opciones_servicio="OriginalDelivery",
            administrador_id=self.usuario_id,
        )
        db.session.add(restaurante_prueba)
        db.session.commit()
        self.restaurantes_creados.append(restaurante_prueba)

        # 2. Modificar todos los campos del restaurante.
        datos_actualizados = {
            "nombre": "Restaurante Modificado",
            "direccion": "Direccion Modificada",
            "telefono": "0987654321",
            "redes_sociales": "Facebook: Modificado",
            "horarios_abre": "Lunes a Viernes 10am a 8pm",
            "tipo_comida": "Comida modificada",
            "aplicaciones_asociadas": "ModificadoEats",
            "opciones_servicio": "ModificadoDelivery",
        }

        # 3. Enviar una solicitud PUT para actualizar el restaurante.
        endpoint_restaurante_especifico = f"/restaurante/{restaurante_prueba.id}"

        resultado_editar_restaurante = self.client.put(
            endpoint_restaurante_especifico,
            data=json.dumps(datos_actualizados),
            headers=self._get_auth_headers(),
        )

        # 4. Verificar que la actualización fue exitosa.
        self.assertEqual(resultado_editar_restaurante.status_code, 200)
        datos_respuesta = json.loads(resultado_editar_restaurante.get_data())
        self.assertEqual(
            datos_respuesta["mensaje"], "Restaurante actualizado exitosamente"
        )

        # 5. Verificar que los campos del restaurante en la base de datos ahora coinciden con los valores actualizados.
        restaurante_actualizado = Restaurante.query.get(restaurante_prueba.id)
        self.assertEqual(restaurante_actualizado.nombre, datos_actualizados["nombre"])
        self.assertEqual(
            restaurante_actualizado.direccion, datos_actualizados["direccion"]
        )
        self.assertEqual(
            restaurante_actualizado.telefono, datos_actualizados["telefono"]
        )
        self.assertEqual(
            restaurante_actualizado.redes_sociales, datos_actualizados["redes_sociales"]
        )
        self.assertEqual(
            restaurante_actualizado.horarios_abre, datos_actualizados["horarios_abre"]
        )
        self.assertEqual(
            restaurante_actualizado.tipo_comida, datos_actualizados["tipo_comida"]
        )
        self.assertEqual(
            restaurante_actualizado.aplicaciones_asociadas,
            datos_actualizados["aplicaciones_asociadas"],
        )
        self.assertEqual(
            restaurante_actualizado.opciones_servicio,
            datos_actualizados["opciones_servicio"],
        )

    def test_obtener_restaurante_no_existente(self):
        response = self.client.get(
            "/restaurante/99999", headers=self._get_auth_headers()
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data["mensaje"], "Restaurante no encontrado")

    def test_obtener_restaurante_exitoso(self):
        # Creación de un restaurante de prueba
        nuevo_restaurante = {
            "nombre": "Restaurante Prueba",
            "direccion": "Direccion Prueba",
            "telefono": "1234567890",
            "redes_sociales": "Facebook: Prueba",
            "horarios_abre": "Lunes a Viernes 9am a 9pm",
            "tipo_comida": "Comida rápida",
            "aplicaciones_asociadas": "UberEats, Rappi",
            "opciones_servicio": "Delivery",
        }

        # Crear el restaurante y guardar el ID del restaurante creado
        resultado = self.client.post(
            "/restaurante",
            data=json.dumps(nuevo_restaurante),
            headers=self._get_auth_headers(),
        )
        self.assertEqual(resultado.status_code, 201)
        datos_respuesta = json.loads(resultado.data)
        id_restaurante = datos_respuesta["id"]

        # Obtener el restaurante previamente creado
        response = self.client.get(
            f"/restaurante/{id_restaurante}", headers=self._get_auth_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verificación de los datos del restaurante obtenido con los datos originales
        self.assertEqual(data["nombre"], nuevo_restaurante["nombre"])
        self.assertEqual(data["direccion"], nuevo_restaurante["direccion"])
        self.assertEqual(data["telefono"], nuevo_restaurante["telefono"])
        self.assertEqual(data["redes_sociales"], nuevo_restaurante["redes_sociales"])
        self.assertEqual(data["horarios_abre"], nuevo_restaurante["horarios_abre"])
        self.assertEqual(data["tipo_comida"], nuevo_restaurante["tipo_comida"])
        self.assertEqual(
            data["aplicaciones_asociadas"], nuevo_restaurante["aplicaciones_asociadas"]
        )
        self.assertEqual(
            data["opciones_servicio"], nuevo_restaurante["opciones_servicio"]
        )
