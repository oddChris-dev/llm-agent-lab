"""
Factory classes for generating test data.
"""

import factory
from django.contrib.auth.models import User
from faker import Faker

from apps.workflows.models import Workflow, Node, Connection, WorkflowStatus
from apps.providers.models import Provider, ProviderType
from apps.executions.models import Execution, ExecutionStatus

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')


class WorkflowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workflow

    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('paragraph')
    status = WorkflowStatus.DRAFT
    user = factory.SubFactory(UserFactory)
    icon = factory.LazyFunction(lambda: fake.random_element(['🤖', '📻', '🎨', '🔍']))
    color = factory.Faker('hex_color')


class NodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Node

    workflow = factory.SubFactory(WorkflowFactory)
    type = factory.LazyFunction(
        lambda: fake.random_element([
            'llm.claude', 'llm.openai', 'voice.tts', 'web.search', 'queue.fifo'
        ])
    )
    name = factory.Faker('word')
    position_x = factory.Faker('pyfloat', min_value=0, max_value=1000)
    position_y = factory.Faker('pyfloat', min_value=0, max_value=1000)
    config = factory.LazyFunction(lambda: {'model': 'test-model'})


class ConnectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Connection

    workflow = factory.SubFactory(WorkflowFactory)
    source_node = factory.SubFactory(NodeFactory)
    target_node = factory.SubFactory(NodeFactory)
    source_port = 'output'
    target_port = 'input'


class ProviderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Provider

    name = factory.Faker('company')
    slug = factory.Sequence(lambda n: f'provider-{n}')
    type = ProviderType.LLM
    config = factory.LazyFunction(lambda: {'api_key': 'test-key'})
    user = factory.SubFactory(UserFactory)


class ExecutionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Execution

    workflow = factory.SubFactory(WorkflowFactory)
    status = ExecutionStatus.PENDING
    trigger_type = 'api'
    trigger_data = factory.LazyFunction(lambda: {})
