from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from clientes.models import Cliente
from envios.models import Encomienda
from rutas.models import Ruta

from .serializers import (
    ClienteSerializer,
    EncomiendaDetailSerializer,
    EncomiendaSerializer,
    RutaSerializer,
)
from .tokens import CustomTokenObtainPairSerializer
from .throttles import LoginRateThrottle
from .utils import get_empleado_for_user


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]


@extend_schema(methods=['GET'], responses=EncomiendaSerializer(many=True))
@extend_schema(methods=['POST'], request=EncomiendaSerializer, responses=EncomiendaSerializer)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def encomienda_list_fbv(request):
    if request.method == 'GET':
        qs = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    serializer = EncomiendaSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save(empleado_registro=get_empleado_for_user(request.user))
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(methods=['GET'], responses=EncomiendaDetailSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def encomienda_detail_fbv(request, pk):
    encomienda = get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)
    serializer = EncomiendaDetailSerializer(encomienda, context={'request': request})
    return Response(serializer.data)


class EncomiendaListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EncomiendaSerializer

    @extend_schema(responses=EncomiendaSerializer(many=True))
    def get(self, request):
        qs = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(request=EncomiendaSerializer, responses=EncomiendaSerializer)
    def post(self, request):
        serializer = EncomiendaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(empleado_registro=get_empleado_for_user(request.user))
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EncomiendaDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EncomiendaDetailSerializer

    def get_object(self, pk):
        return get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)

    @extend_schema(responses=EncomiendaDetailSerializer)
    def get(self, request, pk):
        serializer = EncomiendaDetailSerializer(self.get_object(pk), context={'request': request})
        return Response(serializer.data)

    @extend_schema(request=EncomiendaSerializer, responses=EncomiendaSerializer)
    def put(self, request, pk):
        serializer = EncomiendaSerializer(
            self.get_object(pk), data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(request=EncomiendaSerializer, responses=EncomiendaSerializer)
    def patch(self, request, pk):
        serializer = EncomiendaSerializer(
            self.get_object(pk), data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(responses=None)
    def delete(self, request, pk):
        self.get_object(pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EncomiendaMixinListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView,
):
    queryset = Encomienda.objects.con_relaciones()
    serializer_class = EncomiendaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(empleado_registro=get_empleado_for_user(self.request.user))


class EncomiendaMixinDetailView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    queryset = Encomienda.objects.con_relaciones()
    serializer_class = EncomiendaSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class EncomiendaListCreateView(generics.ListCreateAPIView):
    queryset = Encomienda.objects.con_relaciones()
    serializer_class = EncomiendaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(empleado_registro=get_empleado_for_user(self.request.user))


class EncomiendaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Encomienda.objects.con_relaciones()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EncomiendaDetailSerializer
        return EncomiendaSerializer


class ClienteListView(generics.ListAPIView):
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.activos()


class RutaListView(generics.ListAPIView):
    serializer_class = RutaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ruta.objects.activas()
