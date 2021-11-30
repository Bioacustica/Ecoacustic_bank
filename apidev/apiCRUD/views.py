"""
Este modulo se encarga manejar todas las peticiones mediantes las vistas (views)
Creadas y gestionadas desde django rest framework
"""

__author__ = "Victor Torres"
__license__ = "GPL"  # Pendiente por definir
__status__ = "Development"
__maintainer__ = "Victor Torres"

import os
import csv
import json
import logging


import jwt
import zipfile
from zipfile import ZipFile
from io import BytesIO

import psycopg2
from django.contrib.auth import get_user_model, authenticate
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, viewsets
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from rest_framework import response, decorators, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from dry_rest_permissions.generics import DRYPermissions
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework_simplejwt.tokens import RefreshToken
from cryptography.fernet import Fernet
from django.http import HttpResponse, JsonResponse

from .fnt import (
    choose_role,
    change_password,
    delete_user,
    consulta_filtros,
    base_64_encoding, consulta_filtros_publicos,
)
from .serializers import *
from .custom_permissions import IsAdmin
from .forms import ContactForm

# Vistas hechas con el model view set para hacer el CRUD
"""La Clase ModelViewSet incluye implementaciones para
hacer varias acciones como .list() , .create() , .update() , etc
de forma automatica sin necesidad de crear las funciones, esta
clase es muy util para un paronama general que no requiere personalización
"""
User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def my_obtain_token_view(request):
    """clase encargada de login con  Users de la DB"""
    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer
    """
    obtenemos el username(email) y contraseña con el que
    se hará la uatenticación
    """
    username = request.POST.get("email")
    password = request.POST.get("password")
    # Verificamos las credenciales y creamos el objeto usuario
    user = authenticate(username=username, password=password)

    if user is not None and user.roles != "etiquetado":
        """si el usuario no es nulo se crea un key que servirá
        posteriormente para desencriptar la contraseña del usuario
        en el response
        """
        key = Fernet.generate_key()
        fernet = Fernet(key)
        encMessage = fernet.encrypt(request.data["password"].encode())
        llave = key.decode()
        # Creamos un cursor principal
        credenciales_db = {
            "user": "animalesitm",
            "password": "animalesitm",
            "host": "postgres",
            "port": 5432,
            "database": "animalesitm",
        }
        conexion1 = psycopg2.connect(**credenciales_db)
        conexion1.autocommit = True
        # ejecutamos una verifación para saber si el usuario existe
        verificacion = (
            "SELECT  username FROM bioacustica.keys WHERE username='{}';".format(
                user.username
            )
        )
        with conexion1.cursor() as cursor1:
            cursor1.execute(verificacion)
            name = cursor1.fetchone()

            if name is None:
                with conexion1.cursor() as cursor2:
                    payload2 = "INSERT INTO bioacustica.keys (username, key) VALUES ('{}', '{}') ;".format(
                        user.username, llave
                    )
                    cursor2.execute(payload2)
            cursor1.execute(verificacion)
            nombre = cursor1.fetchone()

            if user.username == nombre[0]:
                payload = "UPDATE bioacustica.keys SET key = '{}' WHERE username ='{}' ;".format(
                    llave, user.username
                )
                cursor1.execute(payload)
            else:
                payload2 = "INSERT INTO bioacustica.keys (username, key) VALUES ('{}', '{}') ;".format(
                    user.username, llave
                )
                cursor1.execute(payload2)

        diccio = {"username": user.username, "key": llave}
        with open("keys.json", "w") as f:
            json.dump(diccio, f)

        refreshToken = RefreshToken.for_user(user)
        accessToken = refreshToken.access_token

        decodeJTW = jwt.decode(
            str(accessToken), settings.SECRET_KEY, algorithms=["HS256"]
        )

        # add payload here!!
        decodeJTW["user"] = user.username
        decodeJTW["password"] = encMessage.decode()

        # encode
        encoded = jwt.encode(decodeJTW, settings.SECRET_KEY, algorithm="HS256")

        return JsonResponse(
            {
                "status": "Logeado con exito",
                "refresh": str(refreshToken),
                "access": str(encoded),
                "username": str(user.username),
                "roles": str(user.roles),
            }
        )

    else:
        return Response(
            {"status": "Sus credenciales no son correctas"},
            status=status.HTTP_400_BAD_REQUEST,
        )


#  Función  encargada de registrar usuarios
@decorators.api_view(["POST"])
@authentication_classes([JWTAuthentication])
@decorators.permission_classes(
    [
        IsAdmin,
    ]
)
def registration(request):
    """
    Esta clase es la encargada de registrar usuarios nuevos
    unicamente se puede registrar usuarios
    :return: si  fue exitoso devuelve un creado de forma exitosa
    :rtype: Http status
    """
    username = request.data["username"]
    email = request.data["email"]
    password = request.data["password"]
    roles = request.data["roles"]

    credenciales_db = {
        "user": "animalesitm",
        "password": "animalesitm",
        "host": "postgres",
        "port": 5432,
        "database": "animalesitm",
    }

    conexion = psycopg2.connect(**credenciales_db)
    conexion.autocommit = True
    payload = choose_role(username, password, roles)

    with conexion.cursor() as cursor:
        cursor.execute(payload)
        bioacustica = cursor.fetchall()

    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return response.Response(
            "Creado de forma exitosa", status=status.HTTP_201_CREATED
        )
    else:
        return response.Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)


@authentication_classes([JWTAuthentication])
# la clase logginMixin  se encarga de hacer logs en la base de datos
class FundingsView(LoggingMixin, viewsets.ModelViewSet):
    """
    Esta vista se encarga del CRUD de la tabla fundings,hereda de models viewsets
    y la clase logginMixin se ecarga de registrar los logs en la db
    """

    queryset = Funding.objects.all()
    # permission_classes = (IsAdmin,)
    serializer_class = FundingSerializer


@decorators.api_view(["GET"])
@authentication_classes([JWTAuthentication])
def filtered_record_view(request):
    """
    vista encargada de filtrar los audios a los que tiene acceso el usuario
    Pide token de autenticación
    solo se permite peticiones de tipo get

    :argument autentication_classes: es un decorador encargado de la
    protección de la vista el cual pide un token de autenticación
    el cual solo se genera en el login.

    :param request: peticion de tipo Get
    :return: retorna un json
    """
    catalogo = request.data["catalogo"].upper()
    habitat = request.data["habitat"].upper()
    municipio = request.data["municipio"].upper()
    evento = request.data["evento"].upper()
    tipo_case = request.data["tipo de case"].upper()
    tipo_micro = request.data["tipo de micro"].upper()
    metodo_etiquetado = request.data["metodo etiquetado"].upper()
    software = request.data["software"].upper()
    tipo_grabadora = request.data["tipo de grabadora"].upper()
    # fecha = request.data["fecha"]
    # fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
    # elevation = request.data["elevation"]

    token = request.META.get("HTTP_AUTHORIZATION", "access")
    paginator = PageNumberPagination()
    paginator.page_size = 10
    context = paginator.paginate_queryset(
        consulta_filtros(
            token,
            catalogo,
            habitat,
            municipio,
            evento,
            tipo_case,
            tipo_micro,
            metodo_etiquetado,
            software,
            tipo_grabadora,
        ),
        request,
    )
    return paginator.get_paginated_response(context)


@decorators.api_view(["GET"])
def public_record_view(request):
    """
    vista encargada de retornar los audios a los que tiene acceso
    el público general
    """
    catalogo = request.data["catalogo"].upper()
    habitat = request.data["habitat"].upper()
    municipio = request.data["municipio"].upper()
    evento = request.data["evento"].upper()
    tipo_case = request.data["tipo de case"].upper()
    tipo_micro = request.data["tipo de micro"].upper()
    metodo_etiquetado = request.data["metodo etiquetado"].upper()
    software = request.data["software"].upper()
    tipo_grabadora = request.data["tipo de grabadora"].upper()
    # fecha = request.data["fecha"]
    # fecha_dt = datetime.strptime(fecha, '%d/%m/%Y')
    # elevation = request.data["elevation"]

    paginator = PageNumberPagination()
    paginator.page_size = 2
    context = paginator.paginate_queryset(consulta_filtros_publicos(
        catalogo,
        habitat,
        municipio,
        evento,
        tipo_case,
        tipo_micro,
        metodo_etiquetado,
        software,
        tipo_grabadora,
        ),
        request
    )
    return paginator.get_paginated_response(context)


@decorators.api_view(["GET"])
def lista_filtros(request):
    """
    Vista encargada de entregar la listas de los datos existentes
    para posteriormente hacer un filtrado mas efectivo con datos existentes
    :param request: Petición de tipo GET
    :return: retornar un diccionario con la lista de opciones por las cual
    se puede filtrar
    """

    ciudad = Country.objects.values_list("description")
    habitat = Habitat.objects.values_list("description")
    municipio = Municipality.objects.values_list("description")
    evento = Type.objects.values_list("description")
    case = Case.objects.values_list("description")
    micro = Microphone.objects.values_list("description")
    evidence = Evidence.objects.values_list("description")
    software = Software.objects.values_list("description")
    hardware = Hardware.objects.values_list("description")

    # TODO  cambiar estructura del diccionario,  agregar departamentos.
    diccionario_filtros = {
        "ciudad":ciudad,
        "habitat":habitat,
        "municipio":municipio,
        "evento":evento,
        "tipo_de_case":case,
        "tipo_de_micro":micro,
        "Metodo_etiquetado":evidence,
        "software_etiquetado":software,
        "Tipo_de_grabadora":hardware,
    }
    return Response(diccionario_filtros)


@decorators.api_view(["GET"])
@authentication_classes([JWTAuthentication])
def downolad_record_views_csv(request):
    """
    Función encargada de la descarga de los datos de los audios, es decir
    descarga los datos como: donde fue grabado, duración, fecha

    :argument autentication_classes: es un decorador encargado de la
    protección de la vista el cual pide un token de autenticación
    el cual solo se genera en el login.

    :param request: Petición de tipo GET
    :return: Información de los audios
    """

    token = request.META.get("HTTP_AUTHORIZATION", "access")
    tipo_archivo = request.data["archivo"]
    objects_list = consulta_filtros(token)
    if tipo_archivo == "csv":
        responses = HttpResponse(content_type="text/csv")
        keys = objects_list[0].keys()
        dict_writer = csv.DictWriter(responses, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(objects_list)
        responses["Content-Disposition"] = 'attachment; filename="users.csv"'
        return responses
    if tipo_archivo == "excel":
        responses = HttpResponse(content_type="application/vnd.ms-excel")
        keys = objects_list[0].keys()
        dict_writer = csv.DictWriter(responses, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(objects_list)
        responses["Content-Disposition"] = 'attachment; filename="users.xlsx"'
        return responses


@authentication_classes([JWTAuthentication])
@decorators.api_view(["GET"])
def download_records_files(request) -> dict:
    """Vista encargada de extraer los paths de records
    y generar los base 64
    de forma adcional se crea un diccionario


    :param request: Petición de tipo GET
    :return: retorna un diccionario con el base 64, su nombre y su tipo de compresión
    """
    filenames = [
        "/code/apiCRUD/sample_audios/audio1.zip",
        "/code/apiCRUD/sample_audios/audio2.zip",
        "/code/apiCRUD/sample_audios/audio3.zip",
    ]
    # Creamos el base 64
    lista = []
    for fname in filenames:
        lista.append(base_64_encoding(fname))

    # Extraemos su tipo compresión y su nombre
    tipo_compresion = []
    audio_name = []
    for zipname in filenames:
        zf = zipfile.ZipFile(zipname, "r")
        for f in zf.namelist():
            audio_name.append(zf.namelist())
            zf1 = zf.getinfo(f)
            tipo_compresion.append(zf1.compress_type)

    # Creamos el diccionario
    diccionario_base64_tipocompresion = {
        str(x): {"base 64": y, "tipo compresion": z}
        for x, y, z in zip(audio_name, lista, tipo_compresion)
    }

    return Response(diccionario_base64_tipocompresion)


@authentication_classes([JWTAuthentication])
class CaseView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Case
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Case.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = CaseSerializer


@permission_classes([DRYPermissions])
@authentication_classes([JWTAuthentication])
class CatalogueView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Catalogue
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Catalogue.objects.all()
    serializer_class = CatalogueSerializer


@authentication_classes([JWTAuthentication])
class CatalogueObsView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Catalogue Obs
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = CatalogueObs.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = CatalogueObsSerializer


@authentication_classes([JWTAuthentication])
class CountryView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Country
     Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Country.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = CountrySerializer


@authentication_classes([JWTAuthentication])
class DatumView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Datum
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Datum.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = DatumSerializer


@authentication_classes([JWTAuthentication])
class DepartmentView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Departmen
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Department.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = DepartmentSerializer


@authentication_classes([JWTAuthentication])
class EvidenceView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Evidence
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Evidence.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = EvidenceSerializer


@authentication_classes([JWTAuthentication])
class FrequencyDetailView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Frecuency Detail
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = FrequencyDetail.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = FrequencyDetailSerializer


@authentication_classes([JWTAuthentication])
class FormatView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Format view
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Format.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = FormatSerializer


@authentication_classes([JWTAuthentication])
class HSerialView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Hserial
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = HSerial.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = HSerialSerializer


@authentication_classes([JWTAuthentication])
class HabitatView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla habitat
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Habitat.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = HabitatSerializer


@authentication_classes([JWTAuthentication])
class HardwareView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Hardware
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Hardware.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = HardwareSerializer


@authentication_classes([JWTAuthentication])
class LabelView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Label
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Label.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = LabelSerializer


@authentication_classes([JWTAuthentication])
class LabeledView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Labeled
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Labeled.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = LabeledSerializer


@authentication_classes([JWTAuthentication])
class LocalityView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Locality
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Locality.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = LocalitySerializer


@authentication_classes([JWTAuthentication])
class MeasureView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Measure
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Measure.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = MeasureSerializer


@authentication_classes([JWTAuthentication])
class MemoryView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Memory
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)

    """

    queryset = Memory.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = MemorySerializer


@authentication_classes([JWTAuthentication])
class MunicipalityView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Municipality
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Municipality.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = MunicipalitySerializer


@authentication_classes([JWTAuthentication])
class PhotoPathView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla PhotoPath
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = PhotoPath.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = PhotoPathSerializer


@authentication_classes([JWTAuthentication])
class PrecisionView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Precision
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Precision.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = PrecisionSerializer


@authentication_classes([JWTAuthentication])
class ProjectView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Project
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Project.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = ProjectSerializer


@authentication_classes([JWTAuthentication])
class PulseTypeView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Pulse Type
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = PulseType.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = PulseTypeSerializer


@authentication_classes([JWTAuthentication])
class RecordView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Record
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Record.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = RecordSerializer


@authentication_classes([JWTAuthentication])
class RecordObsView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Record Obs
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = RecordObs.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = RecordObsSerializer


@authentication_classes([JWTAuthentication])
class RecordPathView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Record Path
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = RecordPath.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = RecordPathSerializer


@authentication_classes([JWTAuthentication])
class SamplingView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Sampling
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Sampling.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = SamplingSerializer


@authentication_classes([JWTAuthentication])
class SeasonView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Season
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    queryset = Season.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = SeasonSerializer


@authentication_classes([JWTAuthentication])
class SoftwareView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Software
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Software.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = SoftwareSerializer


@authentication_classes([JWTAuthentication])
class SupplyView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Supply
    Se usa la clase DRYPermissions para tener mas control de los roles que tienen acceso
    Estos permisos se gestionan con funciones declaradas en los modelos( revisar models.py)
    """

    permission_classes = (DRYPermissions,)
    queryset = Supply.objects.all()
    serializer_class = SupplySerializer


@authentication_classes([JWTAuthentication])
class TimeDetailView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla  Time Detail
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = TimeDetail.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = TimeDetailSerializer


@authentication_classes([JWTAuthentication])
class TypeView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Type
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Type.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = TypeSerializer


@authentication_classes([JWTAuthentication])
class VeredaView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Vereda
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Vereda.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = VeredaSerializer


@authentication_classes([JWTAuthentication])
class VoucherView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla Voucher
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    """

    queryset = Voucher.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = VoucherSerializer


@authentication_classes([JWTAuthentication])
class UserView(viewsets.ModelViewSet):
    """
    Vista encargada del CRUD de la tabla User
    Solo se puede acceder si tienes el rol de admin( consultar modulo custom_permissions.py)
    Solo está permitido hacer peticiones get y put
    """

    queryset = User.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = UserSerializer
    http_method_names = ["get", "put"]


@decorators.api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@decorators.permission_classes(
    [
        IsAdmin,
    ]
)
def user_delete_view(request, id_user):
    """
    Función encargada de eliminar
    usuarios, recibe como parametro su
    id_user, tambien borra el rol del
    pgadmin
    :param id_user: recibe el id_user
    :type id_user: string
    """

    try:
        user = User.objects.get(id_user=id_user)
        user_name = user.username
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        credentials_db = {
            "user": "animalesitm",
            "password": "animalesitm",
            "host": "postgres",
            "port": 5432,
            "database": "animalesitm",
        }

        serializer = UserSerializer(data=request.data)
        connexion = psycopg2.connect(**credentials_db)
        connexion.autocommit = True
        print(type(user_name))
        if serializer.is_valid():
            payload = delete_user(user_name)
            with connexion.cursor() as cursor:
                cursor.execute(payload)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


@authentication_classes([JWTAuthentication])
class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """

    permission_classes = (IsAdmin,)
    serializer_class = ChangePasswordSerializer
    model = User

    def get_object(self, queryset=None):
        """obtiene el objeto de usuario
        :param queryset: , defaults to None
        :type queryset: queryset, optional
        :return: retorna el objeto usuario
        :rtype: AsbtractBaseUser
        """
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        """con este metodo hacemos directamente la
        actualización de la contraseña
        :param request: recibe los parametros del usuario para
        hacer la actualización
        :type request: json
        :return:  retorna la actualización de la constraseña
        :rtype: response
        """
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if serializer.data.get("new_password") == serializer.data.get(
                "confirm_password"
            ):
                # set_password also hashes the password that the user will get
                password = request.data["new_password"]
                username = request.data["username"]
                credenciales_db = {
                    "user": "animalesitm",
                    "password": "animalesitm",
                    "host": "postgres",
                    "port": 5432,
                    "database": "animalesitm",
                }

                conexion = psycopg2.connect(**credenciales_db)
                conexion.autocommit = True
                payload = change_password(username, password)
                with conexion.cursor() as cursor:
                    cursor.execute(payload)
                self.object.set_password(serializer.data.get("new_password"))
                self.object.save()
                response = {
                    "status": "success",
                    "code": status.HTTP_200_OK,
                    "message": "Password updated successfully",
                    "data": [],
                }
                return Response(response)
            else:
                return Response(
                    {"confirm_password": ["must be equal to new_password"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@decorators.api_view(["POST"])
def contactanos_view(request):
    """
    Vista encargada de enviar un email,
    a los admins de bioacustica,
    usa un formulario, todos los
    campos son obligatarios.
    :param request:
    :return:
    """
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            asunto = form.cleaned_data["subject"]
            email = form.cleaned_data["from_email"]
            message = form.cleaned_data["message"]
            # FIXME Lograr que aparezca el email de quien hizo el formulario.
            send_mail(
                asunto,
                "Este es mi correo electronico:" + "\n" + email + "\n" + message,
                email,
                ["animalesitm@gmail.com","piedrahita2001@gmail.com"],
            )  # se pueden agregar mas emails.
            return Response("Enviado con exito")
        return Response("ALGO salio mal ", status=status.HTTP_400_BAD_REQUEST)
