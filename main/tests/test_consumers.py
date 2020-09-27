import asyncio

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import Group
from django.test import TestCase

from main import consumers
from main.tests import factories


class TestConsumers(TestCase):
    def test_chat_between_two_user_works(self):
        def init_db():
            user = factories.UserFactory(
                email="john@bestemails.com",
                first_name="John",
                last_name="Smith",
            )
            order = factories.OrderFactory(user=user)
            cs_user = factories.UserFactory(
                email="cs@intensive-galaxy.in",
                first_name="Adam",
                last_name="Johnson",
                is_staff=True,
            )
            employees, _ = Group.objects.get_or_create(name="Employees")
            cs_user.groups.add(employees)
            return user, order, cs_user

        async def test_body():
            user, order, cs_user = await database_sync_to_async(init_db)()

            communicator = WebsocketCommunicator(
                consumers.ChatConsumer, f"/ws/customer-service/{order.id}/"
            )
            communicator.scope["user"] = user
            communicator.scope["url_route"] = {"kwargs": {"order_id": order.id}}
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            cs_communicator = WebsocketCommunicator(
                consumers.ChatConsumer, f"/ws/customer-service/{order.id}/"
            )

            cs_communicator.scope["user"] = cs_user
            cs_communicator.scope["url_route"] = {"kwargs": {"order_id", order.id}}
            connected, _ = await cs_communicator.connect()
            self.assertTrue(connected)

            await communicator.send_json_to(
                {
                    "type": "message",
                    "message": "hello customer service",
                }
            )

            await asyncio.sleep(1)

            await cs_communicator.send_json_to(
                {"type": "message", "message": "hello user"}
            )

            self.assertEqual(
                await communicator.receive_json_from(),
                {"type": "chat_join", "username": "John Smith"},
            )

            self.assertEqual(
                await communicator.receive_json_from(),
                {"type": "chat_join", "username": "Adam Johnson"},
            )

            self.assertEqual(
                await communicator.receive_json_from(),
                {
                    "type": "chat_message",
                    "username": "John Smith",
                    "message": "hello customer service",
                },
            )

            self.assertEqual(
                await communicator.receive_json_from(),
                {
                    "type": "chat_message",
                    "username": "Adam Johnson",
                    "message": "hello user",
                },
            )
            await communicator.disconnect()
            await cs_communicator.disconnect()
            order.refresh_from_db()
            self.assertEquals(order.last_spoken_to, cs_user)
