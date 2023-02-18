from rest_framework.views import APIView, Request, Response, status
from .models import Pet
from rest_framework.pagination import PageNumberPagination
from .serializers import PetSerializer
from groups.models import Group
from traits.models import Trait
from django.shortcuts import get_object_or_404


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        traits = request.query_params.get("trait")
        pets = Pet.objects.all()

        if traits:
            filtered_traits = Pet.objects.filter(traits__name=traits).all()
            result_pag = self.paginate_queryset(filtered_traits, request)
            serializer = PetSerializer(result_pag, many=True)

            return self.get_paginated_response(serializer.data)
        
        result_pag = self.paginate_queryset(pets, request)
        serializer = PetSerializer(result_pag, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:

        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group = serializer.validated_data.pop("group")
        traits = serializer.validated_data.pop("traits")

        group_obj = Group.objects.get(
            scientific_name__iexact=group["scientific_name"]
        )

        if not group_obj:
            group_obj = Group.objects.create(**group)

        new_pet = Pet.objects.create(
            **serializer.validated_data, group=group_obj
        )
        for trait in traits:
            traits_obj = Trait.objects.filter(
                name__iexact=trait["name"]
            ).first()
            if not traits_obj:
                traits_obj = Trait.objects.create(**trait)
            new_pet.traits.add(traits_obj)

        serializer_res = PetSerializer(new_pet)

        return Response(serializer_res.data, status.HTTP_201_CREATED)


class PetDetailView(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        serializer = PetSerializer(pet)
        return Response(serializer.data, status.HTTP_200_OK)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(data=request.data, partial=True)
        
        serializer.is_valid(raise_exception=True)
        group = serializer.validated_data.pop("group", None)
        traits = serializer.validated_data.pop("traits", None)

        if group:
            group_obj = Group.objects.filter(
                scientific_name__iexact=group["scientific_name"]
            ).first()
            if not group_obj:
                group_obj = Group.objects.create(**group)      
            pet.group = group_obj

        if traits:
            pet.traits.set([])
            for trait in traits:
                traits_obj = Trait.objects.filter(
                    name__iexact=trait["name"]
                ).first()
                if not traits_obj:
                    traits_obj = Trait.objects.create(**trait)
                pet.traits.add(traits_obj)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)      
        pet.save() 

        serializer = PetSerializer(pet)     
        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        pet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)