from django.http import HttpResponseServerError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.contrib.auth.models import User
from rockapi.models import Rock, Type, RockImage


class RockView(ViewSet):
    """Rock view set"""

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single item

        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            rock = Rock.objects.get(pk=pk)

            if rock.user.id == request.auth.user.id:
                rock.delete()
                return Response(None, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'message': 'You do not own that rock'}, status=status.HTTP_403_FORBIDDEN)

        except Rock.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def create(self, request):
        """Handle POST requests for rocks

        Returns:
            Response: JSON serialized representation of newly created rock
        """
        try:
            # Get an object instance of a rock type
            chosen_type = Type.objects.get(pk=request.data['typeId'])

            # Create a rock object and assign it property values
            rock = Rock()
            rock.user = request.auth.user
            rock.weight = request.data['weight']
            rock.name = request.data['name']
            rock.type = chosen_type
            rock.save()

            serialized = RockSerializer(rock, many=False)

            return Response(serialized.data, status=status.HTTP_201_CREATED)
    
        except Exception as ex:
            return HttpResponseServerError(ex)

    def list(self, request):
        """Handle GET requests for all items

        Returns:
            Response -- JSON serialized array
        """
        owner_only = request.query_params.get("owner", None)

        try:
            rocks = Rock.objects.all()

            if owner_only is not None and owner_only == "current":
                rocks = rocks.filter(user=request.auth.user)

            serializer = RockSerializer(rocks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            return HttpResponseServerError(ex)


class RockOwnerSerializer(serializers.ModelSerializer):
    """JSON serializer"""

    class Meta:
        model = User
        fields = ( 'first_name', 'last_name' )

class RockTypeSerializer(serializers.ModelSerializer):
    """JSON serializer"""

    class Meta:
        model = Type
        fields = ( 'label', )

class RockImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RockImage
        fields = ('id', 'original_url', 'thumbnail_small_url', 
                  'thumbnail_medium_url', 'thumbnail_large_url', 
                  'status', 'uploaded_at', 'file_size')

class RockSerializer(serializers.ModelSerializer):
    """JSON serializer"""
    type = RockTypeSerializer(many=False)
    user = RockOwnerSerializer(many=False)
    images = RockImageSerializer(many=True, read_only=True)

    class Meta:
        model = Rock
        fields = ( 'id', 'name', 'weight', 'type', 'user', 'images')

