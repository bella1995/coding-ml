"""
The view classes below define the API endpoints.

+-----------------------------------------------------------------+-----------------+-------------------------------------------------+
| Endpoint                                                        | Url             | Purpose                                         |
+=================================================================+=================+=================================================+
| :class:`Get Data Table <DataTableView>`                         | /api/table      | Get table of counts based on dimensions/filters |
+-----------------------------------------------------------------+-----------------+-------------------------------------------------+
| :class:`Get Example Messages <ExampleMessagesView>`             | /api/messages   | Get example messages for slice of data          |
+-----------------------------------------------------------------+-----------------+-------------------------------------------------+
| :class:`Get Research Questions <ResearchQuestionsView>`         | /api/questions  | Get RQs related to dimensions/filters           |
+-----------------------------------------------------------------+-----------------+-------------------------------------------------+
| Message Context                                                 | /api/context    | Get context for a message                       |
+-----------------------------------------------------------------+-----------------+-------------------------------------------------+
| Snapshots                                                       | /api/snapshots  | Save a visualization snapshot                   |
+-----------------------------------------------------------------+-----------------+-------------------------------------------------+
"""
import types
from django.db import transaction

from rest_framework import status
from rest_framework.views import APIView, Response
from django.core.urlresolvers import NoReverseMatch
from rest_framework.reverse import reverse
from rest_framework.compat import get_resolver_match, OrderedDict
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.contrib.auth.models import User

from msgvis.apps.api import serializers
from msgvis.apps.corpus import models as corpus_models
from msgvis.apps.enhance import models as enhance_models
from msgvis.apps.experiment import models as experiment_models
from msgvis.apps.coding import models as coding_models
import json
import logging

logger = logging.getLogger(__name__)


class DatasetView(APIView):
    """
    Get details of a dataset

    **Request:** ``GET /api/dataset/1``
    """


    def get(self, request, format=None):
        if request.query_params.get('id'):
            dataset_id = int(request.query_params.get('id'))
            try:
                dataset = corpus_models.Dataset.objects.get(id=dataset_id)
                output = serializers.DatasetSerializer(dataset)
                return Response(output.data, status=status.HTTP_200_OK)
            except:
                return Response("Dataset not exist", status=status.HTTP_400_BAD_REQUEST)

        return Response("Please specify dataset id", status=status.HTTP_400_BAD_REQUEST)

class DictionaryView(APIView):
    """
    Get details of a dataset

    **Request:** ``GET /api/dictionary?id=1``
    """


    def get(self, request, format=None):
        if request.query_params.get('id'):
            dictionary_id = int(request.query_params.get('id'))
            try:
                dictionary = enhance_models.Dictionary.objects.get(id=dictionary_id)
                output = serializers.DictionarySerializer(dictionary)
                final_output = dict(output.data)
                if self.request.user is not None:
                    user = self.request.user
                    participant = None
                    if user.id is not None and User.objects.filter(id=self.request.user.id).count() != 0:
                        participant = User.objects.get(id=self.request.user.id)
                    user_feature_count = dictionary.get_user_feature_count(user=participant)
                    final_output['feature_count'] += user_feature_count

                return Response(final_output, status=status.HTTP_200_OK)
            except:
                return Response("Dictionary not exist", status=status.HTTP_400_BAD_REQUEST)

        return Response("Please specify dictionary id", status=status.HTTP_400_BAD_REQUEST)



class SVMResultView(APIView):
    """
    Get svm result of a dictionary

    **Request:** ``GET /api/svm?dictionary_id=1``
    """


    def get(self, request, format=None):
        if request.query_params.get('dictionary_id'):
            dictionary_id = int(request.query_params.get('dictionary_id'))
            participant = None
            if self.request.user is not None:
                user = self.request.user
                if user.id is not None and User.objects.filter(id=self.request.user.id).count() != 0:
                    participant = User.objects.get(id=self.request.user.id)
            try:
                dictionary = enhance_models.Dictionary.objects.get(id=dictionary_id)
                results = dictionary.do_training()
                all_messages = corpus_models.Message.objects.all()
                messages = []

                for message in all_messages:

                    feature_vector = message.get_feature_vector(dictionary=dictionary)
                    tweet_words = map(lambda x: x.tweet_word.original_text, message.tweetword_connections.all()) # get the token list and extract only original text
                    output = {'message': message, 'tokens': tweet_words, 'feature_vector': feature_vector}
                    messages.append(output)

                output = serializers.SVMResultSerializer({'results': results, 'messages': messages})

                return Response(output.data, status=status.HTTP_200_OK)
            except:
                import traceback
                traceback.print_exc()
                import pdb
                pdb.set_trace()

                return Response("Dictionary not exist", status=status.HTTP_400_BAD_REQUEST)

        return Response("Please specify dictionary id", status=status.HTTP_400_BAD_REQUEST)

class FeatureVectorView(APIView):
    """
    Get svm result of a dictionary

    **Request:** ``GET /api/vector?dictionary_id=1&message_id=1``
    """


    def get(self, request, format=None):
        if request.query_params.get('dictionary_id') and request.query_params.get('message_id'):
            dictionary_id = int(request.query_params.get('dictionary_id'))
            message_id = int(request.query_params.get('message_id'))

            try:
                dictionary = enhance_models.Dictionary.objects.get(id=dictionary_id)
                message = corpus_models.Message.objects.get(id=message_id)
                feature_vector = message.get_feature_vector(dictionary=dictionary)
                tweet_words = map(lambda x: x.tweet_word.original_text, message.tweetword_connections.all()) # get the token list and extract only original text
                # TODO: make sure to better communicate the fact we lemmatize words
                output = serializers.FeatureVectorSerializer({'message': message, 'tokens': tweet_words, 'feature_vector': feature_vector})

                return Response(output.data, status=status.HTTP_200_OK)
            except:
                import traceback
                traceback.print_exc()
                import pdb
                pdb.set_trace()

                return Response("Dictionary not exist", status=status.HTTP_400_BAD_REQUEST)

        return Response("Please specify dictionary id", status=status.HTTP_400_BAD_REQUEST)



class UserFeatureView(APIView):
    """
    Get or set user features

    **Request:** ``GET /api/feature``
    """


    def get(self, request, format=None):

        if self.request.user is not None:
            user = self.request.user
            if user.id is not None and User.objects.filter(id=self.request.user.id).count() != 0:
                participant = User.objects.get(id=self.request.user.id)

            features = map(lambda x: x.feature, participant.feature_assignments.filter(valid=True).all())

            output = serializers.FeatureSerializer(features, many=True)

            return Response(output.data, status=status.HTTP_200_OK)
        return Response("Please log in first", status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):

        input = serializers.FeatureSerializer(data=request.data)
        if input.is_valid():
            data = input.validated_data

            dictionary = data["dictionary"]
            token_list = data["token_list"]
            feature = dictionary.add_feature(token_list, source='U')

            if self.request.user is not None:
                user = self.request.user
                if user.id is not None and User.objects.filter(id=self.request.user.id).count() != 0:
                    participant = User.objects.get(id=self.request.user.id)

                    assignment, created = coding_models.FeatureAssignment.objects.get_or_create(user=participant, feature=feature, valid=True)


            output = serializers.FeatureSerializer(feature)
            return Response(output.data, status=status.HTTP_200_OK)

        return Response(input.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, feature_id, format=None):
        if self.request.user is not None:
            user = self.request.user
            if user.id is not None and User.objects.filter(id=self.request.user.id).count() != 0:
                participant = User.objects.get(id=self.request.user.id)

                feature = enhance_models.Feature.objects.get(id=feature_id)
                assignment = experiment_models.FeatureAssignment.objects.get(user=participant, feature=feature, valid=True)
                assignment.valid = False
                assignment.save()
                return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class CodeDefinitionView(APIView):
    """
    Get the definition of a code

    **Request:** ``GET /definition/code_id?source=master``
    """


    def get(self, request, code_id, format=None):


        code = corpus_models.Code.objects.get(id=code_id)
        sources = request.query_params.get('source', "master").split(" ")

        try:
            code_definitions = []
            for source in sources:
                source_user = User.objects.get(username=source)
                code_definition = code.get_definition(source_user)
                code_definitions.append(code_definition)

            output = serializers.CodeDefinitionSerializer(code_definitions, many=True)

            return Response(output.data, status=status.HTTP_200_OK)
        except:
            import traceback
            traceback.print_exc()
            import pdb
            pdb.set_trace()

            return Response("Code definition not exist", status=status.HTTP_400_BAD_REQUEST)

        return Response("Please specify code id", status=status.HTTP_400_BAD_REQUEST)




class APIRoot(APIView):
    """
    The Text Visualization DRG Root API View.
    """
    root_urls = {}

    def get(self, request, *args, **kwargs):
        ret = OrderedDict()
        namespace = get_resolver_match(request).namespace
        for key, urlconf in self.root_urls.iteritems():
            url_name = urlconf.name
            if namespace:
                url_name = namespace + ':' + url_name
            try:
                ret[key] = reverse(
                    url_name,
                    request=request,
                    format=kwargs.get('format', None)
                )
                print ret[key]
            except NoReverseMatch:
                # Don't bail out if eg. no list routes exist, only detail routes.
                continue

        return Response(ret)