from email.policy import default
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from decouple import config
from modelos import db
from vistas import (
    VistaIngrediente,
    VistaIngredientes,
    VistaReceta,
    VistaRecetas,
    VistaSignIn,
    VistaLogIn,
    VistaChef,
    VistaChefs,
    VistaRestaurantes,
    VistaRestaurante,
    VistaMenu,
    VistaMenus,
    VistaMenusChef,
    VistaReporteCompra,
    VistaUsuario,
)
from vistas.vistas import VistaRestauranteEspecifico

app = Flask(__name__)

FLASK_ENV = config("FLASK_ENV", default="development")

# if FLASK_ENV == "testing":
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
# else:
#     app.config["SQLALCHEMY_DATABASE_URI"] = config("DATABASE_URL")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = config("JWT_SECRET_KEY", default="frase-secreta")
app.config["PROPAGATE_EXCEPTIONS"] = True

app_context = app.app_context()
app_context.push()

db.init_app(app)
#db.drop_all()
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(VistaSignIn, "/signin")
api.add_resource(VistaLogIn, "/login")
api.add_resource(VistaUsuario, "/usuario")
api.add_resource(VistaIngredientes, "/ingredientes")
api.add_resource(VistaIngrediente, "/ingrediente/<int:id_ingrediente>")
api.add_resource(VistaRecetas, "/recetas/<int:id_usuario>")
api.add_resource(VistaReceta, "/receta/<int:id_receta>")
api.add_resource(VistaChef, "/chefs")
api.add_resource(VistaChefs, "/chefs/<int:id_restaurante>")
api.add_resource(VistaRestaurante, "/restaurante")
api.add_resource(VistaRestauranteEspecifico, "/restaurante/<int:id_restaurante>")
api.add_resource(VistaRestaurantes, "/restaurantes/<int:id_usuario>")
api.add_resource(VistaMenu, "/menu")
api.add_resource(VistaMenus, "/menus/<int:id_restaurante>")
api.add_resource(VistaMenusChef, "/menus")
api.add_resource(VistaReporteCompra, "/reporte")

jwt = JWTManager(app)
