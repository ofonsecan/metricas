from flask import request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_restful import Resource
from marshmallow import ValidationError
from collections import Counter
import hashlib
import json
from datetime import datetime
import math

from modelos import (
    db,
    Ingrediente,
    IngredienteSchema,
    RecetaIngrediente,
    RecetaIngredienteSchema,
    Receta,
    RecetaSchema,
    Chef,
    ChefSchema,
    Restaurante,
    RestauranteSchema,
    Usuario,
    UsuarioSchema,
    Administrador,
    AdministradorSchema,
    Menu,
    MenuSchema,
    MenuReceta,
    MenuRecetaSchema,
)


administrador_schema= AdministradorSchema()
chef_schema = ChefSchema()
ingrediente_schema = IngredienteSchema()
menu_schema = MenuSchema()
menu_receta_schema = MenuRecetaSchema()
receta_ingrediente_schema = RecetaIngredienteSchema()
receta_schema = RecetaSchema()
restaurante_schema = RestauranteSchema()
usuario_schema = UsuarioSchema()
restaurante_schema = RestauranteSchema()

class VistaSignIn(Resource):
    def post(self):
        usuario = Usuario.query.filter(
            Usuario.usuario == request.json["usuario"]
        ).first()
        if usuario is None:
            contrasena_encriptada = hashlib.md5(
                request.json["contrasena"].encode("utf-8")
            ).hexdigest()
            nuevo_usuario = Administrador(
                usuario=request.json["usuario"], contrasena=contrasena_encriptada
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            token_de_acceso = create_access_token(identity=nuevo_usuario.id)
            return {"mensaje": "usuario creado exitosamente", "id": nuevo_usuario.id}
        else:
            return "El usuario ya existe", 404

    def put(self, id_usuario):
        usuario = Usuario.query.get_or_404(id_usuario)
        usuario.contrasena = request.json.get("contrasena", usuario.contrasena)
        db.session.commit()
        return usuario_schema.dump(usuario)

    def delete(self, id_usuario):
        usuario = Administrador.query.get_or_404(id_usuario)
        db.session.delete(usuario)
        db.session.commit()
        return "", 204

class VistaLogIn(Resource):
    def post(self):
        contrasena_encriptada = hashlib.md5(
            request.json["contrasena"].encode("utf-8")
        ).hexdigest()
        usuario = Usuario.query.filter(
            Usuario.usuario == request.json["usuario"],
            Usuario.contrasena == contrasena_encriptada,
        ).first()
        db.session.commit()
        print(str(hashlib.md5("admin".encode("utf-8")).hexdigest()))
        if usuario is None:
            return "El usuario no existe", 404
        else:
            administrador = Administrador.query.get(usuario.id)
            rol = "admin" if administrador else "chef"

            token_de_acceso = create_access_token(identity=usuario.id)
            return {
                "mensaje": "Inicio de sesión exitoso",
                "token": token_de_acceso,
                "id": usuario.id,
                "rol": rol,
            }

class VistaUsuario(Resource):
    @jwt_required()
    def get(self):
        id_usuario = get_jwt_identity()
        administrador = Administrador.query.get(id_usuario)
        if administrador:
            return {"nombre": administrador.usuario}
        else:
            chef = Chef.query.get(id_usuario)
            if chef:
                return {"nombre": chef.nombre}
            else:
                return {"mensaje": "Acceso denegado"}, 403

class VistaIngredientes(Resource):
    def _get_administrador(self, id_usuario):
        administrador = None
        if not Administrador.query.get(id_usuario):
            chef = Chef.query.get(id_usuario)
            if not chef:
                return None
            else:
                id_usuario = chef.restaurante.administrador_id
                
        administrador = Administrador.query.get(id_usuario)
        return administrador
    
    def _create_ingrediente(self, data, administrador):
        nuevo_ingrediente = Ingrediente(
            nombre=data["nombre"],
            unidad=data["unidad"],
            costo=float(data["costo"]),
            calorias=float(data["calorias"]),
            sitio=data["sitio"],
            administrador_id=administrador.id,
        )

        db.session.add(nuevo_ingrediente)
        db.session.commit()
        return nuevo_ingrediente
    
    def _validate_data(self, data, id_usuario):
        try:
            ingrediente_schema.load(data, session=db.session)
        except ValidationError as err:
            return {"mensaje": "Datos inválidos", "errores": err.messages}, 400

        ingrediente_existente = (
            Ingrediente.query.filter_by(administrador_id=id_usuario)
            .filter_by(nombre=data["nombre"])
            .first()
        )

        if ingrediente_existente:
            return {"message": "El ingrediente ya existe con ese nombre."}, 400

    @jwt_required()
    def get(self):
        id_usuario = get_jwt_identity()

        if not Administrador.query.get(id_usuario):
            chef = Chef.query.get(id_usuario)
            if not chef:
                return {"mensaje": "Acceso denegado"}, 403
            else:
                id_usuario = chef.restaurante.administrador_id

        ingredientes = Ingrediente.query.filter_by(
            administrador_id=str(id_usuario)
        ).all()
        return [ingrediente_schema.dump(ingrediente) for ingrediente in ingredientes]

    @jwt_required()
    def post(self):
        id_usuario = get_jwt_identity()
        administrador = self._get_administrador(id_usuario)

        if not administrador:
            return {"mensaje": "Acceso denegado"}, 403

        data = request.get_json()
        validation_result = self._validate_data(data, id_usuario)
        
        if validation_result:
            return validation_result

        nuevo_ingrediente = self._create_ingrediente(data, administrador)
        return ingrediente_schema.dump(nuevo_ingrediente)


class VistaIngrediente(Resource):
    @jwt_required()
    def get(self, id_ingrediente):
        return ingrediente_schema.dump(Ingrediente.query.get_or_404(id_ingrediente))

    @jwt_required()
    def put(self, id_ingrediente):
        ingrediente = Ingrediente.query.get_or_404(id_ingrediente)
        ingrediente.nombre = request.json["nombre"]
        ingrediente.unidad = request.json["unidad"]
        ingrediente.costo = float(request.json["costo"])
        ingrediente.calorias = float(request.json["calorias"])
        ingrediente.sitio = request.json["sitio"]
        db.session.commit()
        return ingrediente_schema.dump(ingrediente)

    @jwt_required()
    def delete(self, id_ingrediente):
        ingrediente = Ingrediente.query.get_or_404(id_ingrediente)
        recetas_ingrediente = RecetaIngrediente.query.filter_by(
            ingrediente=id_ingrediente
        ).all()
        if not recetas_ingrediente:
            db.session.delete(ingrediente)
            db.session.commit()
            return "", 204
        else:
            return "El ingrediente se está usando en diferentes recetas", 409


class VistaRecetas(Resource):
    @jwt_required()
    def get(self, id_usuario):
        if not Administrador.query.get(id_usuario):
            chef = Chef.query.get(id_usuario)
            if not chef:
                return {"mensaje": "Acceso denegado"}, 403
            else:
                id_usuario = chef.restaurante.administrador_id

        recetas = Receta.query.filter_by(usuario=str(id_usuario)).all()
        resultados = [receta_schema.dump(receta) for receta in recetas]
        ingredientes = Ingrediente.query.all()
        for receta in resultados:
            for receta_ingrediente in receta["ingredientes"]:
                self.actualizar_ingredientes_util(receta_ingrediente, ingredientes)

        return resultados

    @jwt_required()
    def post(self, id_usuario):
        nueva_receta = Receta(
            nombre=request.json["nombre"],
            preparacion=request.json["preparacion"],
            ingredientes=[],
            usuario=id_usuario,
            duracion=float(request.json["duracion"]),
            porcion=float(request.json["porcion"]),
        )
        for receta_ingrediente in request.json["ingredientes"]:
            nueva_receta_ingrediente = RecetaIngrediente(
                cantidad=receta_ingrediente["cantidad"],
                ingrediente=int(receta_ingrediente["idIngrediente"]),
            )
            nueva_receta.ingredientes.append(nueva_receta_ingrediente)
        db.session.add(nueva_receta)
        db.session.commit()
        return ingrediente_schema.dump(nueva_receta)

    def actualizar_ingredientes_util(self, receta_ingrediente, ingredientes):
        for ingrediente in ingredientes:
            if str(ingrediente.id) == receta_ingrediente["ingrediente"]:
                receta_ingrediente["ingrediente"] = ingrediente_schema.dump(ingrediente)
                receta_ingrediente["ingrediente"]["costo"] = float(
                    receta_ingrediente["ingrediente"]["costo"]
                )


class VistaReceta(Resource):
    @jwt_required()
    def get(self, id_receta):
        receta = Receta.query.get_or_404(id_receta)
        ingredientes = Ingrediente.query.all()
        resultados = receta_schema.dump(Receta.query.get_or_404(id_receta))
        receta_ingredientes = resultados["ingredientes"]
        for receta_ingrediente in receta_ingredientes:
            for ingrediente in ingredientes:
                if str(ingrediente.id) == receta_ingrediente["ingrediente"]:
                    receta_ingrediente["ingrediente"] = ingrediente_schema.dump(
                        ingrediente
                    )
                    receta_ingrediente["ingrediente"]["costo"] = float(
                        receta_ingrediente["ingrediente"]["costo"]
                    )

        return resultados

    @jwt_required()
    def put(self, id_receta):
        receta = Receta.query.get_or_404(id_receta)
        receta.nombre = request.json["nombre"]
        receta.preparacion = request.json["preparacion"]
        receta.duracion = float(request.json["duracion"])
        receta.porcion = float(request.json["porcion"])

        # Verificar los ingredientes que se borraron
        for receta_ingrediente in receta.ingredientes:
            borrar = self.borrar_ingrediente_util(
                request.json["ingredientes"], receta_ingrediente
            )

            if borrar == True:
                db.session.delete(receta_ingrediente)

        db.session.commit()

        for receta_ingrediente_editar in request.json["ingredientes"]:
            if receta_ingrediente_editar["id"] == "":
                # Es un nuevo ingrediente de la receta porque no tiene código
                nueva_receta_ingrediente = RecetaIngrediente(
                    cantidad=receta_ingrediente_editar["cantidad"],
                    ingrediente=int(receta_ingrediente_editar["idIngrediente"]),
                )
                receta.ingredientes.append(nueva_receta_ingrediente)
            else:
                # Se actualiza el ingrediente de la receta
                receta_ingrediente = self.actualizar_ingrediente_util(
                    receta.ingredientes, receta_ingrediente_editar
                )
                db.session.add(receta_ingrediente)

        db.session.add(receta)
        db.session.commit()
        return ingrediente_schema.dump(receta)

    @jwt_required()
    def delete(self, id_receta):
        receta = Receta.query.get_or_404(id_receta)
        db.session.delete(receta)
        db.session.commit()
        return "", 204

    def borrar_ingrediente_util(self, receta_ingredientes, receta_ingrediente):
        borrar = True
        for receta_ingrediente_editar in receta_ingredientes:
            if receta_ingrediente_editar["id"] != "":
                if int(receta_ingrediente_editar["id"]) == receta_ingrediente.id:
                    borrar = False

        return borrar

    def actualizar_ingrediente_util(
        self, receta_ingredientes, receta_ingrediente_editar
    ):
        receta_ingrediente_retornar = None
        for receta_ingrediente in receta_ingredientes:
            if int(receta_ingrediente_editar["id"]) == receta_ingrediente.id:
                receta_ingrediente.cantidad = receta_ingrediente_editar["cantidad"]
                receta_ingrediente.ingrediente = receta_ingrediente_editar[
                    "idIngrediente"
                ]
                receta_ingrediente_retornar = receta_ingrediente

        return receta_ingrediente_retornar


class VistaChef(Resource):
    @jwt_required()
    def post(self):
        administrador_id = get_jwt_identity()

        administrador = Administrador.query.get(administrador_id)
        if not administrador:
            return {"mensaje": "Acceso denegado"}, 403

        data = request.get_json()

        restaurante_id = data.get("restaurante_id")
        nombre = data.get("nombre")
        usuario = data.get("usuario")
        contrasena = data.get("contrasena")

        # Validación de longitud y no estar vacío
        if not nombre or len(nombre) > 200:
            return {"message": "El nombre es inválido"}, 400

        if not usuario or len(usuario) > 50:
            return {"message": "El usuario es inválido"}, 400

        if not contrasena or len(contrasena) > 50:
            return {"message": "La contraseña es inválida"}, 400

        restaurante = Restaurante.query.get(restaurante_id)
        if not restaurante:
            return {"message": "Restaurante no encontrado"}, 404

        usuario_existente = Usuario.query.filter_by(usuario=usuario).first()
        if usuario_existente:
            return {"message": "El usuario ya existe"}, 400

        nuevo_chef = Chef(
            nombre=nombre,
            usuario=usuario,
            contrasena=hashlib.md5(contrasena.encode("utf-8")).hexdigest(),
            restaurante=restaurante,
        )

        db.session.add(nuevo_chef)
        db.session.commit()

        return {"message": "Chef creado exitosamente"}, 201


class VistaRestaurante(Resource):
    @jwt_required()
    def post(self):
        administrador_id = get_jwt_identity()

        administrador = Administrador.query.get(administrador_id)
        if not administrador:
            return {"mensaje": "Acceso denegado"}, 403

        data = request.get_json()

        try:
            restaurante_schema.load(data, session=db.session)
        except ValidationError as err:
            return {"mensaje": "Datos inválidos", "errores": err.messages}, 400

        restaurante_existente = Restaurante.query.filter_by(
            nombre=data["nombre"]
        ).first()
        if restaurante_existente:
            return {"message": "El restaurante ya existe con ese nombre."}, 400

        nuevo_restaurante = Restaurante(
            nombre=data["nombre"],
            direccion=data["direccion"],
            telefono=data["telefono"],
            redes_sociales=data.get("redes_sociales", ""),
            horarios_abre=data.get("horarios_abre", ""),
            tipo_comida=data.get("tipo_comida", ""),
            aplicaciones_asociadas=data.get("aplicaciones_asociadas", ""),
            opciones_servicio=data.get("opciones_servicio", ""),
            administrador_id=administrador_id,
        )

        db.session.add(nuevo_restaurante)
        db.session.commit()

        return {
            "message": "Restaurante creado exitosamente",
            "id": nuevo_restaurante.id,
        }, 201


class VistaRestauranteEspecifico(Resource):
    @jwt_required()
    def put(self, id_restaurante):
        administrador_id = get_jwt_identity()

        administrador = Administrador.query.get(administrador_id)
        if not administrador:
            return {"mensaje": "Acceso denegado"}, 403

        restaurante = Restaurante.query.get_or_404(id_restaurante)

        data = request.get_json()

        restaurante_existente = Restaurante.query.filter(
            Restaurante.nombre == data["nombre"], Restaurante.id != id_restaurante
        ).first()

        if restaurante_existente:
            return {"message": "Ya existe un restaurante con ese nombre."}, 400

        try:
            restaurante_schema.load(data, session=db.session, instance=restaurante)
        except ValidationError as err:
            return {"mensaje": "Datos inválidos", "errores": err.messages}, 400

        db.session.commit()
        return {
            "mensaje": "Restaurante actualizado exitosamente",
            "id": restaurante.id,
        }, 200

    @jwt_required()
    def get(self, id_restaurante):
        restaurante = Restaurante.query.filter_by(id=id_restaurante).first()
        if restaurante:
            return restaurante_schema.dump(restaurante), 200
        else:
            return {"mensaje": "Restaurante no encontrado"}, 404


class VistaRestaurantes(Resource):
    @jwt_required()
    def get(self, id_usuario):
        administrador_id = get_jwt_identity()

        administrador = Administrador.query.get(administrador_id)
        if not administrador:
            return {"mensaje": "Acceso denegado"}, 403

        restaurantes = (
            Restaurante.query.filter_by(administrador_id=str(id_usuario))
            .order_by(Restaurante.nombre)
            .all()
        )

        return [restaurante_schema.dump(restaurante) for restaurante in restaurantes]
    
class VistaChefs(Resource):
    @jwt_required()
    def get(self, id_restaurante):
        administrador_id = get_jwt_identity()

        administrador = Administrador.query.get(administrador_id)
        if not administrador:
            return {"mensaje": "Acceso denegado"}, 403

        chefs = (
            Chef.query.filter_by(restaurante_id=str(id_restaurante))
            .order_by(Chef.nombre)
            .all()
        )
        resultados = [chef_schema.dump(chef) for chef in chefs]
        return resultados
    
class VistaMenu(Resource):   
    def _validacion_fechas(self, data, restaurante_id):     
        fecha_actual = datetime.now()
        fecha_inicio_str = data.get("fecha_inicio")
        fecha_fin_str = data.get("fecha_fin")

        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d %H:%M")
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d %H:%M")

        if fecha_inicio > fecha_fin:
            return {"mensaje": "La fecha de inicio no puede ser mayor que la fecha de fin"}, 400
    
        if fecha_inicio < fecha_actual or fecha_fin < fecha_actual:
         return {"mensaje": "Las fechas deben ser mayores que la fecha actual"}, 400    

        menus_superpuestos = Menu.query.filter(
            Menu.restaurante_id == restaurante_id,
            Menu.fecha_fin >= fecha_inicio,
            Menu.fecha_inicio <= fecha_fin
        ).all()

        if menus_superpuestos:
            return {"mensaje": "Ya existe un menú con fechas superpuestas en este restaurante"}, 400  

    def _validacion_menu(self, data):

        if not data.get("nombre").strip() \
            or not data.get("descripcion").strip() \
            or not data.get("fecha_inicio").strip() \
            or not data.get("fecha_fin").strip():
            return {"mensaje": "Datos inválidos"}, 400
        
        if not 2 <= len(data.get("nombre")) <= 200:
            return {"mensaje": "Nombre inválido, debe tener entre 2 y 200 caracteres"}, 400
        
        if not 2 <= len(data.get("descripcion")) <= 2000:
            return {"mensaje": "Descripcion inválido, debe tener entre 2 y 2000 caracteres"}, 400

        if len(data.get("recetas")) <= 0:
            return {"mensaje": "El menú debe contener al menos una receta."}, 400
        
        id_recetas = [int(receta["receta"]) for receta in data.get("recetas")]
        recetas_duplicadas = [id for id, count in Counter(id_recetas).items() if count > 1]
        
        numero_personas = [int(receta["numero_personas"]) for receta in data.get("recetas")]
        if recetas_duplicadas:
            return {"mensaje": "No deben haber recetas duplicadas."}, 400
        self._validar_numero_personas(numero_personas)
            
        for personas in numero_personas:
            error = self._validar_numero_personas(personas)    
            if error:
                return error
        
    def _validar_numero_personas(self, num_personas):
        if not str(num_personas).isdigit():
             return {"mensaje": "El menú debe contener al menos una dígito."}, 400
        if len(str(num_personas)) < 1 or len(str(num_personas)) > 5:
            return {"mensaje": "El menú debe contener debe tener entre 1 y 5 dígitos."}, 400

    @jwt_required()
    def post(self):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return {"mensaje": "Acceso denegado"}, 403
        
        data = request.get_json()
        error = self._validacion_menu(data)
        if error:
            return error

        fecha_inicio = datetime.strptime(data.get("fecha_inicio"), "%Y-%m-%d %H:%M")
        fecha_fin = datetime.strptime(data.get("fecha_fin"), "%Y-%m-%d %H:%M")

        restaurante_id = data.get("restaurante")
        chef = Chef.query.get(usuario_id)
        if chef:
            restaurante_id = chef.restaurante_id
        
        if not restaurante_id:
            return {"mensaje": "El restaurante no se seleccionó"}, 400
              
        menu_existente = Menu.query.filter(
            Menu.nombre == data["nombre"],
            Menu.restaurante_id == restaurante_id
        ).first()
        if menu_existente:
            return {"mensaje": "El menú ya existe con ese nombre."}, 400

        error = self._validacion_fechas(data, restaurante_id)
        if error:
            return error

        nuevo_menu = Menu(
            nombre = data.get("nombre"),
            fecha_inicio = fecha_inicio,
            fecha_fin = fecha_fin,
            descripcion = data.get("descripcion"),
            usuario_id = usuario.id,
            restaurante_id = restaurante_id
        )
        
        for menu_receta in data.get("recetas"):
            nuevo_menu_receta = MenuReceta(
                numero_personas=menu_receta["numero_personas"],
                receta=int(menu_receta["receta"]),
            )
            nuevo_menu.recetas.append(nuevo_menu_receta)

        db.session.add(nuevo_menu)
        db.session.commit()
        return {"mensaje": "Menu creado exitosamente"}, 201
               

class VistaMenus(Resource):
    @jwt_required()
    def get(self, id_restaurante):
        id_usuario = get_jwt_identity()

        if not Administrador.query.get(id_usuario):
            return {"mensaje": "Acceso denegado"}, 403

        restaurante = Restaurante.query.get(id_restaurante)
        if not restaurante:
            return {"mensaje": "El restaurante no existe"}, 404
        elif restaurante.administrador_id != id_usuario:
            return {"mensaje": "Acceso denegado al restaurante"}, 403

        menus = (
            Menu.query.filter_by(restaurante_id=str(id_restaurante))
            .order_by(Menu.fecha_inicio)
            .all()
        )
        resultados = [menu_schema.dump(menu) for menu in menus]
        return resultados
    

class VistaMenusChef(Resource):
    @jwt_required()
    def get(self):
        id_usuario = get_jwt_identity()

        chef = Chef.query.get(id_usuario)
        if not chef:
            return {"mensaje": "Acceso denegado"}, 403

        menus = (
            Menu.query.filter_by(restaurante_id=str(chef.restaurante_id))
            .order_by(Menu.fecha_inicio)
            .all()
        )
        resultados = [menu_schema.dump(menu) for menu in menus]
        return resultados

class VistaReporteCompra(Resource):
    @jwt_required()
    def post(self):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return {"mensaje": "Acceso denegado"}, 403

        data = request.get_json()

        ingredientes_receta = {}
        for receta_respuesta in data["recetas"]:
            receta_id = receta_respuesta.get("receta")
            receta = Receta.query.filter_by(id=receta_id).first()

            if not receta:
                return {"mensaje": "Al menos una receta seleccionada no existe"}, 400

            numero_personas = receta_respuesta.get("numero_personas")

            for receta_ingrediente in receta.ingredientes:
                ingrediente = Ingrediente.query.get(receta_ingrediente.ingrediente)
                ingrediente_nombre = ingrediente.nombre
                porcion_float = float(receta.porcion)
                unidades = math.ceil((float(receta_ingrediente.cantidad) * numero_personas) / porcion_float)
                
                if ingrediente_nombre not in ingredientes_receta:
                    ingredientes_receta[ingrediente_nombre] = {
                    "sitio": ingrediente.sitio,
                    "cantidad": unidades,
                    "recetas": [receta.nombre],
                    "costo": float(ingrediente.costo) * unidades
                    }
                else:
                    ingredientes_receta[ingrediente_nombre]["recetas"].append(receta.nombre)   
                    ingredientes_receta[ingrediente_nombre]["cantidad"] += int(unidades)
                    costo =  float(ingrediente.costo) * unidades
                    ingredientes_receta[ingrediente_nombre]["costo"] += costo

        return {"mensaje": "Cálculo correcto", "ingredientes_receta": ingredientes_receta}, 200






