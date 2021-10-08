import collections
import csv
import json
import logging
import jwt

from django.http import HttpResponse
import psycopg2
from django.contrib.auth import get_user_model, authenticate
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
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


from .fnt import choose_role, change_password, delete_user, consulta_filtros
from .serializers import *
from .custom_permissions import IsAdmin
from django.conf import settings

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
        verificacion = """SELECT  username FROM bioacustica."apiCRUD_keys"  WHERE username='{}';""".format(
            user.username
        )
        with conexion1.cursor() as cursor1:
            cursor1.execute(verificacion)
            name = cursor1.fetchone()
            if name is None:
                with conexion1.cursor() as cursor2:

                    payload2 = """INSERT INTO bioacustica."apiCRUD_keys" (username, key) VALUES ('{}', '{}') ;""".format(
                        user.username, llave
                    )
                    cursor2.execute(payload2)
            cursor1.execute(verificacion)
            nombre = cursor1.fetchone()
            if user.username == nombre[0]:

                payload = """UPDATE bioacustica."apiCRUD_keys" SET key = '{}' WHERE username ='{}' ;""".format(
                    llave, user.username
                )
                cursor1.execute(payload)
            else:
                payload2 = """INSERT INTO bioacustica."apiCRUD_keys" (username, key) VALUES ('{}', '{}') ;""".format(
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

        return Response(
            {
                "status": " Logeado con exito",
                "refresh": str(refreshToken),
                "access": str(encoded),
                "username": str(user.username),
                "roles": str(user.roles),
            }
        )

    else:
        return Response({"status": "Sus credenciales no son correctas"})


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
    :return: si todo fue exitoso devuelve un creado de forma exitosa
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
    queryset = Funding.objects.all()
    # permission_classes = (IsAdmin,)
    serializer_class = FundingSerializer


@decorators.api_view(["GET"])
@authentication_classes([JWTAuthentication])
def filtered_record_view(request):
    """
    vista encargada de filtrar los audios a los que tiene acceso el usuario
    """
    token = request.META.get("HTTP_AUTHORIZATION", "access")
    paginator = PageNumberPagination()
    paginator.page_size = 2
    context = paginator.paginate_queryset(consulta_filtros(token), request)
    serializer = UserSerializer(context, many=True)
    return paginator.get_paginated_response(serializer.data)


@decorators.api_view(["GET"])
@authentication_classes([JWTAuthentication])
def downolad_record_views(request):
    """
    Función encargada de la descarga de los datos de los audios

    :param request:
    :return:
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
        responses = HttpResponse(content_type="text/excel")
        keys = objects_list[0].keys()
        dict_writer = csv.DictWriter(responses, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(objects_list)
        responses["Content-Disposition"] = 'attachment; filename="users.xslx"'
        return responses


@authentication_classes([JWTAuthentication])
class CaseView(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = CaseSerializer


@permission_classes([DRYPermissions])
@authentication_classes([JWTAuthentication])
class CatalogueView(viewsets.ModelViewSet):
    queryset = Catalogue.objects.all()
    serializer_class = CatalogueSerializer


@authentication_classes([JWTAuthentication])
class CatalogueObsView(viewsets.ModelViewSet):
    queryset = CatalogueObs.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = CatalogueObsSerializer


@authentication_classes([JWTAuthentication])
class CountryView(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = CountrySerializer


@authentication_classes([JWTAuthentication])
class DatumView(viewsets.ModelViewSet):
    queryset = Datum.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = DatumSerializer


@authentication_classes([JWTAuthentication])
class MicrophoneView(viewsets.ModelViewSet):
    queryset = Microphone.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = MicrophoneSerializer


@authentication_classes([JWTAuthentication])
class DepartmentView(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = DepartmentSerializer


@authentication_classes([JWTAuthentication])
class EvidenceView(viewsets.ModelViewSet):
    queryset = Evidence.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = EvidenceSerializer


@authentication_classes([JWTAuthentication])
class FrequencyDetailView(viewsets.ModelViewSet):
    queryset = FrequencyDetail.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = FrequencyDetailSerializer


@authentication_classes([JWTAuthentication])
class FormatView(viewsets.ModelViewSet):
    queryset = Format.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = FormatSerializer


@authentication_classes([JWTAuthentication])
class HSerialView(viewsets.ModelViewSet):
    queryset = HSerial.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = HSerialSerializer


@authentication_classes([JWTAuthentication])
class HabitatView(viewsets.ModelViewSet):
    queryset = Habitat.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = HabitatSerializer


@authentication_classes([JWTAuthentication])
class HardwareView(viewsets.ModelViewSet):
    queryset = Hardware.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = HardwareSerializer


@authentication_classes([JWTAuthentication])
class LabelView(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = LabelSerializer


@authentication_classes([JWTAuthentication])
class LabeledView(viewsets.ModelViewSet):
    queryset = Labeled.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = LabeledSerializer


@authentication_classes([JWTAuthentication])
class LocalityView(viewsets.ModelViewSet):
    queryset = Locality.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = LocalitySerializer


@authentication_classes([JWTAuthentication])
class GainView(viewsets.ModelViewSet):
    queryset = Gain.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = GainSerializer


@authentication_classes([JWTAuthentication])
class FilterView(viewsets.ModelViewSet):
    queryset = Filter.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = FilterSerializer


@authentication_classes([JWTAuthentication])
class MeasureView(viewsets.ModelViewSet):
    queryset = Measure.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = MeasureSerializer


@authentication_classes([JWTAuthentication])
class MemoryView(viewsets.ModelViewSet):
    queryset = Memory.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = MemorySerializer


@authentication_classes([JWTAuthentication])
class MunicipalityView(viewsets.ModelViewSet):
    queryset = Municipality.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = MunicipalitySerializer


@authentication_classes([JWTAuthentication])
class PhotoPathView(viewsets.ModelViewSet):
    queryset = PhotoPath.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = PhotoPathSerializer


@authentication_classes([JWTAuthentication])
class PrecisionView(viewsets.ModelViewSet):
    queryset = Precision.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = PrecisionSerializer


@authentication_classes([JWTAuthentication])
class ProjectView(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = ProjectSerializer


@authentication_classes([JWTAuthentication])
class PulseTypeView(viewsets.ModelViewSet):
    queryset = PulseType.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = PulseTypeSerializer


@authentication_classes([JWTAuthentication])
class RecordView(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = RecordSerializer


@authentication_classes([JWTAuthentication])
class RecordObsView(viewsets.ModelViewSet):
    queryset = RecordObs.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = RecordObsSerializer


@authentication_classes([JWTAuthentication])
class RecordPathView(viewsets.ModelViewSet):
    queryset = RecordPath.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = RecordPathSerializer


@authentication_classes([JWTAuthentication])
class SamplingView(viewsets.ModelViewSet):
    queryset = Sampling.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = SamplingSerializer


@authentication_classes([JWTAuthentication])
class SeasonView(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    permission_classes = (DRYPermissions,)
    serializer_class = SeasonSerializer


@authentication_classes([JWTAuthentication])
class SoftwareView(viewsets.ModelViewSet):
    queryset = Software.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = SoftwareSerializer


@authentication_classes([JWTAuthentication])
class SupplyView(viewsets.ModelViewSet):
    permission_classes = (DRYPermissions,)
    queryset = Supply.objects.all()
    serializer_class = SupplySerializer


@authentication_classes([JWTAuthentication])
class TimeDetailView(viewsets.ModelViewSet):
    queryset = TimeDetail.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = TimeDetailSerializer


@authentication_classes([JWTAuthentication])
class TypeView(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = TypeSerializer


@authentication_classes([JWTAuthentication])
class VeredaView(viewsets.ModelViewSet):
    queryset = Vereda.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = VeredaSerializer


@authentication_classes([JWTAuthentication])
class VoucherView(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    permission_classes = (IsAdmin,)
    serializer_class = VoucherSerializer


@authentication_classes([JWTAuthentication])
class UserView(viewsets.ModelViewSet):
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
