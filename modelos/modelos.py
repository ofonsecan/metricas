from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from marshmallow import fields, Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import ValidationError

db = SQLAlchemy()

def not_empty(value):
    if not value.strip():
        raise ValidationError("Field cannot be empty.")
    
def not_empty_str(value):
    if not str(value).strip():
        raise ValidationError("Field cannot be empty.")

class Ingrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(128))
    unidad = db.Column(db.String(128))
    costo = db.Column(db.Numeric)
    calorias = db.Column(db.Numeric)
    sitio = db.Column(db.String(128))
    administrador_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))


class RecetaIngrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Numeric)
    ingrediente = db.Column(db.Integer, db.ForeignKey("ingrediente.id"))
    receta = db.Column(db.Integer, db.ForeignKey("receta.id"))


class Receta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(128))
    duracion = db.Column(db.Numeric)
    porcion = db.Column(db.Numeric)
    preparacion = db.Column(db.String)
    ingredientes = db.relationship(
        "RecetaIngrediente", cascade="all, delete, delete-orphan"
    )
    usuario = db.Column(db.Integer, db.ForeignKey("usuario.id"))


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    contrasena = db.Column(db.String(50))


class Administrador(Usuario):
    id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    recetas = db.relationship("Receta", cascade="all, delete, delete-orphan")
    restaurantes = db.relationship(
        "Restaurante",
        foreign_keys="Restaurante.administrador_id",
        cascade="all, delete, delete-orphan",
        single_parent=True,
    )
    ingredientes = db.relationship(
        "Ingrediente",
        foreign_keys="Ingrediente.administrador_id",
        cascade="all, delete, delete-orphan",
        single_parent=True,
    )


class Chef(Usuario):
    id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    nombre = db.Column(db.String(200))
    restaurante_id = db.Column(db.Integer, db.ForeignKey("restaurante.id"))


class Restaurante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, unique=True)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    redes_sociales = db.Column(db.String(500))
    horarios_abre = db.Column(db.String(500))
    tipo_comida = db.Column(db.String(500))
    aplicaciones_asociadas = db.Column(db.String(500))
    opciones_servicio = db.Column(db.String(50))
    administrador_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    chefs = db.relationship(
        "Chef",
        foreign_keys="Chef.restaurante_id",
        backref="restaurante",
        lazy="dynamic",
    )
    menus = db.relationship(
        "Menu",
        foreign_keys="Menu.restaurante_id",
        backref="restaurante",
        lazy="dynamic",
    )

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    fecha_inicio = db.Column(DateTime, nullable=False)
    fecha_fin = db.Column(DateTime, nullable=False)
    descripcion = db.Column(db.String(2000), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    restaurante_id = db.Column(db.Integer, db.ForeignKey("restaurante.id"))   
    recetas = db.relationship("MenuReceta", cascade="all, delete, delete-orphan")

class MenuReceta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_personas = db.Column(db.Integer, nullable=False)
    menu = db.Column(db.Integer, db.ForeignKey("menu.id"))
    receta = db.Column(db.Integer, db.ForeignKey("receta.id"))
    
class ChefSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Chef
        include_relationships = True
        include_fk = True
        load_instance = True
        fields = ("id", "nombre", "restaurante_id")


class AdministradorSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Administrador
        include_relationships = True
        load_instance = True


class RestauranteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Restaurante
        include_relationships = True
        load_instance = True

    nombre = fields.String(required=True, validate=not_empty)
    direccion = fields.String(required=True, validate=not_empty)
    telefono = fields.String(required=True, validate=not_empty)
    redes_sociales = fields.String()
    horarios_abre = fields.String()
    tipo_comida = fields.String()
    aplicaciones_asociadas = fields.String()
    opciones_servicio = fields.String()


class IngredienteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Ingrediente
        load_instance = True

    id = fields.String()
    nombre = fields.String(required=True, validate=not_empty)
    unidad = fields.String(required=True, validate=not_empty)
    costo = fields.Float(required=True, validate=not_empty_str)
    calorias = fields.Float(required=True, validate=not_empty_str)
    sitio = fields.String(required=True, validate=not_empty)


class RecetaIngredienteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RecetaIngrediente
        include_relationships = True
        include_fk = True
        load_instance = True

    id = fields.String()
    cantidad = fields.String()
    ingrediente = fields.String()


class RecetaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Receta
        include_relationships = True
        include_fk = True
        load_instance = True

    id = fields.String()
    duracion = fields.String()
    porcion = fields.String()
    ingredientes = fields.List(fields.Nested(RecetaIngredienteSchema()))


class MenuRecetaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MenuReceta
        include_relationships = True
        include_fk = True
        load_instance = True

    numero_personas = fields.String()
    receta = fields.String()


class MenuSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Menu
        include_relationships = True
        load_instance = True
        fields = ("id", "nombre", "fecha_inicio", "fecha_fin", "restaurante_id")

    id = fields.String()
    nombre = fields.String(required=True)
    fecha_inicio = fields.DateTime(required=True, format="%d/%m/%Y %H:%M")
    fecha_fin = fields.DateTime(required=True, format="%d/%m/%Y %H:%M")
    descripcion = fields.String(required=True)
    recetas = fields.List(fields.Nested(MenuRecetaSchema()))


class UsuarioSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Usuario
        load_instance = True

    id = fields.String()
